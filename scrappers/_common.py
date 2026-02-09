"""Base classes and utilities for all scrapers.

Provides caching, rate limiting, proxy rotation, TLS fingerprinting,
Selenium automation, and season/league normalization.
"""

import io
import json
import pprint
import random
import re
import time
import warnings
from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import IO, Callable, Optional, Union

import numpy as np
import pandas as pd
import seleniumbase as sb

# Suppress tls_requests debug output on import
import sys
_original_stdout = sys.stdout
sys.stdout = io.StringIO()
import tls_requests
sys.stdout = _original_stdout

# Disable tls_requests print statements permanently
try:
    import tls_requests.models.libraries as _tls_lib
    _tls_lib.print = lambda *args, **kwargs: None
except (ImportError, AttributeError):
    pass

from dateutil.relativedelta import relativedelta
from lxml.etree import _Element
from selenium.common.exceptions import JavascriptException, WebDriverException

from ._config import DATA_DIR, LEAGUE_DICT, MAXAGE, TEAMNAME_REPLACEMENTS, logger


class SeasonCode(Enum):
    """Season code format: single year ('2021') or multi-year ('2122')."""

    SINGLE_YEAR = "single-year"
    MULTI_YEAR = "multi-year"

    @staticmethod
    def from_league(league: str) -> "SeasonCode":
        """Return the default season code format for a league."""
        if league not in LEAGUE_DICT:
            raise ValueError(f"Invalid league '{league}'")
        select_league_dict = LEAGUE_DICT[league]
        # Explicit override in config takes precedence (e.g. World Cup = single-year)
        if "season_code" in select_league_dict:
            return SeasonCode(select_league_dict["season_code"])
        # Infer from calendar: if end < start, season spans two years
        start_month = datetime.strptime(  # noqa: DTZ007
            select_league_dict.get("season_start", "Aug"),
            "%b",
        ).month
        end_month = datetime.strptime(  # noqa: DTZ007
            select_league_dict.get("season_end", "May"),
            "%b",
        ).month
        return SeasonCode.MULTI_YEAR if (end_month - start_month) < 0 else SeasonCode.SINGLE_YEAR

    @staticmethod
    def from_leagues(leagues: list[str]) -> "SeasonCode":
        """Determine season code for a set of leagues. Defaults to multi-year if mixed."""
        season_codes = {SeasonCode.from_league(league) for league in leagues}
        if len(season_codes) == 1:
            return season_codes.pop()
        warnings.warn(
            "The leagues have different default season codes. Using multi-year season codes.",
            stacklevel=2,
        )
        return SeasonCode.MULTI_YEAR

    def parse(self, season: Union[str, int]) -> str:  # noqa: C901
        """Normalize season input to standard format (e.g. '94' -> '9495' or '1994')."""
        season = str(season)
        # Order matters: 4-digit before 2-digit, full ranges before short
        patterns = [
            (
                re.compile(r"^[0-9]{4}$"),  # 1994 | 9495
                lambda s: process_four_digit_year(s),
            ),
            (
                re.compile(r"^[0-9]{2}$"),  # 94
                lambda s: process_two_digit_year(s),
            ),
            (
                re.compile(r"^[0-9]{4}-[0-9]{4}$"),  # 1994-1995
                lambda s: process_full_year_range(s),
            ),
            (
                re.compile(r"^[0-9]{4}/[0-9]{4}$"),  # 1994/1995
                lambda s: process_full_year_range(s.replace("/", "-")),
            ),
            (
                re.compile(r"^[0-9]{4}-[0-9]{2}$"),  # 1994-95
                lambda s: process_partial_year_range(s),
            ),
            (
                re.compile(r"^[0-9]{2}-[0-9]{2}$"),  # 94-95
                lambda s: process_short_year_range(s),
            ),
            (
                re.compile(r"^[0-9]{2}/[0-9]{2}$"),  # 94/95
                lambda s: process_short_year_range(s.replace("/", "-")),
            ),
        ]

        current_year = datetime.now(tz=timezone.utc).year

        def process_four_digit_year(season: str) -> str:
            """Handle '1994' or '9495' depending on season code type."""
            if self == SeasonCode.MULTI_YEAR:
                if int(season[2:]) == int(season[:2]) + 1:
                    if season == "2021":
                        msg = (
                            f'Season id "{season}" is ambiguous: '
                            f'interpreting as "{season[:2]}-{season[-2:]}"'
                        )
                        warnings.warn(msg, stacklevel=1)
                    return season
                if season[2:] == "99":
                    return "9900"
                return season[-2:] + f"{int(season[-2:]) + 1:02d}"
            if season == "1920":
                return "1919"
            if season == "2021":
                return "2020"
            if season[:2] == "19" or season[:2] == "20":
                return season
            if int(season) <= current_year:
                return "20" + season[:2]
            return "19" + season[:2]

        def process_two_digit_year(season: str) -> str:
            """Handle '94' -> '9495' (multi) or '1994'/'2094' (single)."""
            if self == SeasonCode.MULTI_YEAR:
                if season == "99":
                    return "9900"
                return season + f"{int(season) + 1:02d}"
            if int("20" + season) <= current_year:
                return "20" + season
            return "19" + season

        def process_full_year_range(season: str) -> str:
            """Handle '1994-1995' -> '9495' (multi) or '1994' (single)."""
            if self == SeasonCode.MULTI_YEAR:
                return season[2:4] + season[-2:]
            return season[:4]

        def process_partial_year_range(season: str) -> str:
            """Handle '1994-95' -> '9495' (multi) or '1994' (single)."""
            if self == SeasonCode.MULTI_YEAR:
                return season[2:4] + season[-2:]
            return season[:4]

        def process_short_year_range(season: str) -> str:
            """Handle '94-95' -> '9495' (multi) or '1994'/'2094' (single)."""
            if self == SeasonCode.MULTI_YEAR:
                return season[:2] + season[-2:]
            if int("20" + season[:2]) <= current_year:
                return "20" + season[:2]
            return "19" + season[:2]

        for pattern, action in patterns:
            if pattern.match(season):
                return action(season)

        raise ValueError(f"Unrecognized season code: '{season}'")


class BaseReader(ABC):
    """Abstract base for all data readers. Handles caching, proxies, and league/season config."""

    def __init__(
        self,
        leagues: Optional[Union[str, list[str]]] = None,
        proxy: Optional[Union[str, list[str], Callable[[], str]]] = None,
        no_cache: bool = False,
        no_store: bool = False,
        data_dir: Path = DATA_DIR,
    ):
        """Create a new data reader."""
        # Normalize proxy to a callable returning a proxy string
        if isinstance(proxy, str) and proxy.lower() == "tor":
            self.proxy = lambda: "socks5://127.0.0.1:9050"
        elif isinstance(proxy, str):
            self.proxy = lambda: proxy
        elif isinstance(proxy, list):
            self.proxy = lambda: random.choice(proxy)
        elif callable(proxy):
            self.proxy = proxy
        else:
            self.proxy = lambda: None  # type: ignore

        self._selected_leagues = leagues  # type: ignore
        self.no_cache = no_cache
        self.no_store = no_store
        self.data_dir = data_dir
        self.rate_limit = 0
        self.max_delay = 0
        if self.no_store:
            logger.debug("Caching disabled")
        else:
            logger.debug("Cache: %s", str(self.data_dir).replace(str(Path.home()), "~"))
            self.data_dir.mkdir(parents=True, exist_ok=True)

    def get(
        self,
        url: str,
        filepath: Optional[Path] = None,
        max_age: Optional[Union[int, timedelta]] = MAXAGE,
        no_cache: bool = False,
        var: Optional[Union[str, Iterable[str]]] = None,
    ) -> IO[bytes]:
        """Fetch url with caching. Returns cached file if fresh, otherwise downloads."""
        is_cached = self._is_cached(filepath, max_age)
        if no_cache or self.no_cache or not is_cached:
            logger.debug("Fetching %s", url)
            return self._download_and_save(url, filepath, var)
        logger.debug("Cache hit: %s", url)
        if filepath is None:
            raise ValueError("No filepath provided for cached data.")
        return filepath.open(mode="rb")

    def _is_cached(
        self,
        filepath: Optional[Path] = None,
        max_age: Optional[Union[int, timedelta]] = None,
    ) -> bool:
        """Return True if filepath exists and is younger than max_age."""
        if max_age is not None:
            if isinstance(max_age, int):
                _max_age = timedelta(days=max_age)
            elif isinstance(max_age, timedelta):
                _max_age = max_age
            else:
                raise TypeError("'max_age' must be of type int or datetime.timedelta")
        else:
            _max_age = None

        cache_invalid = False
        if _max_age is not None and filepath is not None and filepath.exists():
            last_modified = datetime.fromtimestamp(filepath.stat().st_mtime, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            if (now - last_modified) > _max_age:
                cache_invalid = True

        return not cache_invalid and filepath is not None and filepath.exists()

    @abstractmethod
    def _download_and_save(
        self,
        url: str,
        filepath: Optional[Path] = None,
        var: Optional[Union[str, Iterable[str]]] = None,
    ) -> IO[bytes]:
        """Download url and optionally save to filepath. Returns file-like object."""

    @classmethod
    def available_leagues(cls) -> list[str]:
        """Return a list of league IDs available for this source."""
        return sorted(cls._all_leagues().keys())

    @classmethod
    def _all_leagues(cls) -> dict[str, str]:
        """Return dict mapping canonical league IDs to source-specific IDs. Cached per class."""
        if not hasattr(cls, "_all_leagues_dict"):
            cls._all_leagues_dict = {  # type: ignore
                k: v[cls.__name__] for k, v in LEAGUE_DICT.items() if cls.__name__ in v
            }
        return cls._all_leagues_dict  # type: ignore

    @classmethod
    def _translate_league(cls, df: pd.DataFrame, col: str = "league") -> pd.DataFrame:
        """Map source league ID to canonical ID (e.g. 'EPL' -> 'ENG-Premier League')."""
        flip = {v: k for k, v in cls._all_leagues().items()}
        mask = ~df[col].isin(flip)
        df.loc[mask, col] = np.nan
        df[col] = df[col].replace(flip)
        return df

    @property
    def _selected_leagues(self) -> dict[str, str]:
        """Return a dict mapping selected canonical league IDs to source league IDs."""
        return self._leagues_dict

    @_selected_leagues.setter
    def _selected_leagues(self, ids: Optional[Union[str, list[str]]] = None) -> None:
        """Validate and set the selected leagues. None selects all available."""
        if ids is None:
            self._leagues_dict = self._all_leagues()
        else:
            if len(ids) == 0:
                raise ValueError("Empty iterable not allowed for 'leagues'")
            if isinstance(ids, str):
                ids = [ids]
            tmp_league_dict = {}
            for i in ids:
                if i not in self._all_leagues():
                    raise ValueError(
                        f"""
                        Invalid league '{i}'. Valid leagues are:
                        {pprint.pformat(self.available_leagues())}
                        """
                    )
                tmp_league_dict[i] = self._all_leagues()[i]
            self._leagues_dict = tmp_league_dict

    @property
    def _season_code(self) -> SeasonCode:
        """Infer season code format from selected leagues."""
        return SeasonCode.from_leagues(self.leagues)

    def _is_complete(self, league: str, season: str) -> bool:
        """Check if a season is complete (past its end date)."""
        if league in LEAGUE_DICT:
            league_dict = LEAGUE_DICT[league]
        else:
            flip = {v: k for k, v in self._all_leagues().items()}
            if league in flip:
                league_dict = LEAGUE_DICT[flip[league]]
            else:
                raise ValueError(f"Invalid league '{league}'")
        if "season_end" not in league_dict:
            season_ends = datetime(
                datetime.strptime(season[-2:], "%y").year,  # noqa: DTZ007
                7,
                1,
                tzinfo=timezone.utc,
            )
        else:
            season_ends = datetime(
                datetime.strptime(season[-2:], "%y").year,  # noqa: DTZ007
                datetime.strptime(  # noqa: DTZ007
                    league_dict["season_end"], "%b"
                ).month,
                1,
                tzinfo=timezone.utc,
            ) + relativedelta(months=1)
        return datetime.now(tz=timezone.utc) >= season_ends

    @property
    def leagues(self) -> list[str]:
        """Return a list of selected leagues."""
        return list(self._leagues_dict.keys())

    @property
    def seasons(self) -> list[str]:
        """Return a list of selected seasons."""
        return self._season_ids

    @seasons.setter
    def seasons(self, seasons: Optional[Union[str, int, Iterable[Union[str, int]]]]) -> None:
        """Set and normalize seasons. Defaults to last 5 if None."""
        if seasons is None:
            logger.debug("No seasons specified - using last 5 seasons")
            year = datetime.now(tz=timezone.utc).year
            seasons = [f"{y - 1}-{y}" for y in range(year, year - 6, -1)]
        if isinstance(seasons, (str, int)):
            seasons = [seasons]
        self._season_ids = [self._season_code.parse(s) for s in seasons]


class BaseRequestsReader(BaseReader):
    """Base class for HTTP scrapers. Uses tls_requests for TLS fingerprint evasion."""

    def __init__(
        self,
        leagues: Optional[Union[str, list[str]]] = None,
        proxy: Optional[Union[str, list[str], Callable[[], str]]] = None,
        no_cache: bool = False,
        no_store: bool = False,
        data_dir: Path = DATA_DIR,
    ):
        """Initialize the reader."""
        super().__init__(
            no_cache=no_cache,
            no_store=no_store,
            leagues=leagues,
            proxy=proxy,
            data_dir=data_dir,
        )

        self._session = self._init_session()

    def _init_session(self) -> tls_requests.Client:
        """Create a new TLS client session with current proxy."""
        return tls_requests.Client(proxy=self.proxy())

    def _get_random_headers(self) -> dict:
        """Return random browser headers to avoid bot detection."""
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
        ]

        accept_languages = [
            "en-US,en;q=0.9",
            "en-GB,en;q=0.9",
            "en-US,en;q=0.9,es;q=0.8",
            "en-GB,en;q=0.8,es;q=0.7",
            "en-US,en;q=0.9,fr;q=0.8",
        ]

        return {
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": random.choice(accept_languages),
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }

    def _download_and_save(
        self,
        url: str,
        filepath: Optional[Path] = None,
        var: Optional[Union[str, Iterable[str]]] = None,
    ) -> IO[bytes]:
        """Download url with retry (5 attempts). Resets session on failure."""
        for i in range(5):
            try:
                response = self._session.get(url, headers=self._get_random_headers())
                time.sleep(self.rate_limit + random.random() * self.max_delay)
                response.raise_for_status()
                if var is not None:
                    # Extract JS variables matching: varName = JSON.parse('...')
                    if isinstance(var, str):
                        var = [var]
                    var_names = "|".join(var)
                    template_understat = rb"(%b)+[\s\t]*=[\s\t]*JSON\.parse\('(.*)'\)"
                    pattern_understat = template_understat % bytes(var_names, encoding="utf-8")
                    results = re.findall(pattern_understat, response.content)
                    data = {
                        key.decode("unicode_escape"): json.loads(value.decode("unicode_escape"))
                        for key, value in results
                    }
                    payload = json.dumps(data).encode("utf-8")
                else:
                    payload = response.content
                if not self.no_store and filepath is not None:
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    with filepath.open(mode="wb") as fh:
                        fh.write(payload)
                return io.BytesIO(payload)
            except Exception as e:
                logger.error(
                    "Error scraping %s (attempt %d/5): %s",
                    url,
                    i + 1,
                    str(e)[:100],
                )
                self._session = self._init_session()
                continue

        raise ConnectionError(f"Could not download {url}.")


class BaseSeleniumReader(BaseReader):
    """Base class for browser-based scrapers. Uses SeleniumBase with UC mode for anti-bot bypass."""

    def __init__(
        self,
        leagues: Optional[Union[str, list[str]]] = None,
        proxy: Optional[Union[str, list[str], Callable[[], str]]] = None,
        no_cache: bool = False,
        no_store: bool = False,
        data_dir: Path = DATA_DIR,
        path_to_browser: Optional[Path] = None,
        headless: bool = True,
    ):
        """Initialize the reader."""
        super().__init__(
            no_cache=no_cache,
            no_store=no_store,
            leagues=leagues,
            proxy=proxy,
            data_dir=data_dir,
        )
        self.path_to_browser = path_to_browser
        self.headless = headless

        try:
            self._driver = self._init_webdriver()
        except WebDriverException as e:
            logger.error(
                "ChromeDriver failed to start: %s",
                str(e)[:100] + "..." if len(str(e)) > 100 else str(e),
            )

    def _init_webdriver(self) -> "sb.Driver":
        """Start a new Selenium driver with undetected-chromedriver mode."""
        if hasattr(self, "_driver"):
            self._driver.quit()
        proxy_str = self.proxy()
        # Force DNS through proxy to prevent DNS leaks
        resolver_rules = None
        if proxy_str is not None:
            resolver_rules = "MAP * ~NOTFOUND , EXCLUDE 127.0.0.1"
        return sb.Driver(
            uc=True,
            headless=self.headless,
            binary_location=self.path_to_browser,
            host_resolver_rules=resolver_rules,
            proxy=proxy_str,
        )

    def _download_and_save(
        self,
        url: str,
        filepath: Optional[Path] = None,
        var: Optional[Union[str, Iterable[str]]] = None,
    ) -> IO[bytes]:
        """Download url via browser with retry (5 attempts). Exponential backoff on failure."""
        for i in range(5):
            try:
                self._driver.get(url)
                time.sleep(self.rate_limit + random.random() * self.max_delay)
                # Incapsula (Imperva WAF) = IP blocked
                if "Incapsula incident ID" in self._driver.page_source:
                    raise WebDriverException(
                        "Your IP is blocked. Use tor or a proxy to continue scraping."
                    )
                if var is None:
                    response = self._driver.execute_script(
                        "return document.body.innerHTML;"
                    ).encode("utf-8")
                    if response == b"":
                        raise Exception("Empty response.")
                else:
                    if not isinstance(var, str):
                        raise NotImplementedError("Only implemented for single variables.")
                    try:
                        response = json.dumps(self._driver.execute_script("return " + var)).encode(
                            "utf-8"
                        )
                    except JavascriptException:
                        response = json.dumps(None).encode("utf-8")
                if not self.no_store and filepath is not None:
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    with filepath.open(mode="wb") as fh:
                        fh.write(response)
                return io.BytesIO(response)
            except Exception as e:
                logger.error(
                    "Error scraping %s (attempt %d/5, retry in %ds): %s",
                    url,
                    i + 1,
                    i * 10,
                    str(e)[:100],
                )
                time.sleep(i * 10)
                self._driver = self._init_webdriver()
                continue

        raise ConnectionError(f"Could not download {url}.")


def make_game_id(row: pd.Series) -> str:
    """Return a game id based on date, home and away team."""
    if pd.isnull(row["date"]):
        game_id = "{}-{}".format(
            row["home_team"],
            row["away_team"],
        )
    else:
        game_id = "{} {}-{}".format(
            row["date"].strftime("%Y-%m-%d"),
            row["home_team"],
            row["away_team"],
        )
    return game_id


def add_alt_team_names(team: Union[str, list[str]]) -> set[str]:
    """Return set of all known alternative names for the given team(s)."""
    teams = [team] if isinstance(team, str) else team

    alt_teams = set()
    for team in teams:
        for alt_name, norm_name in TEAMNAME_REPLACEMENTS.items():
            if norm_name == team:
                alt_teams.add(alt_name)
        alt_teams.add(team)
    return alt_teams


def add_standardized_team_name(team: Union[str, list[str]]) -> set[str]:
    """Return set including the canonical name for any non-standard team name(s)."""
    teams = [team] if isinstance(team, str) else team
    std_teams = set()
    for team in teams:
        for alt_name, norm_name in TEAMNAME_REPLACEMENTS.items():
            if alt_name == team:
                std_teams.add(norm_name)
        std_teams.add(team)
    return std_teams


def standardize_colnames(df: pd.DataFrame, cols: Optional[list[str]] = None) -> pd.DataFrame:
    """Convert DataFrame column names to snake_case (e.g. 'xGChain' -> 'x_g_chain')."""

    def to_snake(name: str) -> str:
        """Convert camelCase/PascalCase to snake_case."""
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        name = re.sub("__([A-Z])", r"_\1", name)
        name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name)
        return name.lower().replace("-", "_").replace(" ", "")

    if df.columns.nlevels > 1 and cols is None:
        new_df = df.copy()
        new_cols = [to_snake(c) for c in df.columns.levels[0]]
        new_df.columns = new_df.columns.set_levels(new_cols, level=0)
        return new_df

    if cols is None:
        cols = list(df.columns)

    return df.rename(columns={c: to_snake(c) for c in cols})


def get_proxy() -> dict[str, str]:
    """Fetch a working public proxy from GeoNode API. Returns empty dict if none work."""
    list_of_proxy_content = [
        "https://proxylist.geonode.com/api/proxy-list?sort_by=lastChecked&sort_type=desc",
    ]

    full_proxy_list = []
    for proxy_url in list_of_proxy_content:
        proxy_json = json.loads(tls_requests.get(proxy_url).text)["data"]
        full_proxy_list.extend(proxy_json)

        if not full_proxy_list:
            logger.debug("No proxies available")
            return {}
        logger.debug(f"Found {len(full_proxy_list)} proxy servers, checking...")

    final_proxy_list = []
    for proxy in full_proxy_list:
        protocol = proxy["protocols"][0]
        ip_ = proxy["ip"]
        port = proxy["port"]

        proxy = {
            "https": protocol + "://" + ip_ + ":" + port,
            "http": protocol + "://" + ip_ + ":" + port,
        }

        final_proxy_list.append(proxy)

    for proxy in final_proxy_list:
        if check_proxy(proxy):
            return proxy

    logger.debug("No working proxies found")
    return {}


def check_proxy(proxy: dict) -> bool:
    """Check if proxy is working."""
    try:
        r0 = tls_requests.get("https://ipinfo.io/json", proxies=proxy, timeout=15)
        return r0.status_code == 200
    except Exception as error:
        logger.error(f"Proxy failed: {error!s}")
        return False


def safe_xpath_text(node: _Element, xpath_expr: str, warn: Optional[str] = None) -> Optional[str]:
    """Extract text via xpath, returning None (with optional warning) if not found."""
    result = node.xpath(xpath_expr)
    if not result and warn is not None:
        warnings.warn(warn, stacklevel=2)
        return None
    return result[0].strip()