"""ELO ratings scraper for national football teams from eloratings.net.

Fetches current rankings, recent and historical match results via TSV endpoints.
All metric columns are prefixed with ``elo_``.

Data sources:
    - ``{year}.tsv``: Rankings with 33 columns (rating, rank, changes, match record)
    - ``latest.tsv``: Recent match results with pre/post ratings
    - ``{year}_results.tsv``: Historical match results for a specific year
    - ``en.teams.tsv``: Country code to name mapping (331 entries)
    - ``en.tournaments.tsv``: Tournament code to name mapping
"""

import io
import random
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

# Suppress tls_requests debug output on import
import sys
_original_stdout = sys.stdout
sys.stdout = io.StringIO()
import tls_requests
sys.stdout = _original_stdout

try:
    import tls_requests.models.libraries as _tls_lib
    _tls_lib.print = lambda *args, **kwargs: None
except (ImportError, AttributeError):
    pass

from ._config import DATA_DIR, logger

ELO_DATADIR = DATA_DIR / "EloRatings"
ELO_BASE_URL = "https://www.eloratings.net"

# Column definitions for {year}.tsv (33 fields per row)
RANKING_COLUMNS = [
    "local_rank",          # 0: confederation rank (or rank change indicator)
    "elo_rank",            # 1: global rank
    "code",                # 2: 2-letter team code
    "elo_rating",          # 3: current ELO rating
    "elo_rank_highest",    # 4: all-time highest rank
    "elo_rating_highest",  # 5: all-time highest rating
    "elo_rank_average",    # 6: average rank
    "elo_rating_average",  # 7: average rating
    "elo_rank_lowest",     # 8: all-time lowest rank
    "elo_rating_lowest",   # 9: all-time lowest rating
    "elo_rank_3m_chg",     # 10: 3-month rank change
    "elo_rating_3m_chg",   # 11: 3-month rating change
    "elo_rank_6m_chg",     # 12: 6-month rank change
    "elo_rating_6m_chg",   # 13: 6-month rating change
    "elo_rank_1y_chg",     # 14: 1-year rank change
    "elo_rating_1y_chg",   # 15: 1-year rating change
    "elo_rank_2y_chg",     # 16: 2-year rank change
    "elo_rating_2y_chg",   # 17: 2-year rating change
    "elo_rank_5y_chg",     # 18: 5-year rank change
    "elo_rating_5y_chg",   # 19: 5-year rating change
    "elo_rank_10y_chg",    # 20: 10-year rank change
    "elo_rating_10y_chg",  # 21: 10-year rating change
    "elo_total_matches",   # 22: total matches played
    "elo_home_matches",    # 23: home matches
    "elo_away_matches",    # 24: away matches
    "elo_neutral_matches", # 25: neutral venue matches
    "elo_wins",            # 26: total wins
    "elo_losses",          # 27: total losses
    "elo_draws",           # 28: total draws
    "elo_goals_for",       # 29: total goals scored
    "elo_goals_against",   # 30: total goals conceded
    "elo_rank_chg",        # 31: recent rank change
    "elo_rating_chg",      # 32: recent rating change
]

# Column definitions for latest.tsv (match results)
MATCH_COLUMNS = [
    "year", "month", "day",
    "team1_code", "team2_code",
    "team1_score", "team2_score",
    "tournament_code", "venue_code",
    "elo_rating_diff",
    "team1_elo_before", "team2_elo_before",
    "team1_elo_change", "team2_elo_change",
    "team1_rank", "team2_rank",
]


class EloRatings:
    """Scrape national team ELO ratings from eloratings.net.

    Fetches TSV data files: rankings ({year}.tsv), recent matches (latest.tsv),
    and reference data (team names, tournament names).

    Parameters
    ----------
    proxy : str, optional
        HTTP proxy URL.
    no_cache : bool
        Skip cached data.
    data_dir : Path
        Cache directory path.
    """

    def __init__(
        self,
        proxy: Optional[str] = None,
        no_cache: bool = False,
        data_dir: Path = ELO_DATADIR,
    ):
        self.proxy = proxy
        self.no_cache = no_cache
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit = 3
        self.max_delay = 2
        self._session = tls_requests.Client(proxy=proxy)
        self._team_map: Optional[dict[str, str]] = None
        self._tournament_map: Optional[dict[str, str]] = None

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def read_rankings(self, year: Optional[int] = None) -> pd.DataFrame:
        """Fetch current ELO rankings for all national teams.

        Parameters
        ----------
        year : int, optional
            Year to fetch. Defaults to current year.

        Returns
        -------
        pd.DataFrame
            Indexed by team name, with elo_* columns.
        """
        if year is None:
            year = datetime.now(tz=timezone.utc).year

        filepath = self.data_dir / f"rankings_{year}.tsv"
        url = f"{ELO_BASE_URL}/{year}.tsv"
        raw = self._fetch(url, filepath, max_age_days=1)
        team_map = self._get_team_map()

        rows = []
        for line in raw.strip().split("\n"):
            if not line.strip():
                continue
            fields = line.split("\t")
            if len(fields) < 33:
                continue
            code = fields[2]
            team_name = team_map.get(code, code)
            row = {"team": team_name, "code": code}
            for i, col in enumerate(RANKING_COLUMNS):
                if col == "code":
                    continue
                val = fields[i].replace("\u2212", "-").strip()
                if col in ("local_rank",):
                    row[col] = val
                else:
                    try:
                        row[col] = int(val)
                    except ValueError:
                        row[col] = None
            rows.append(row)

        df = pd.DataFrame(rows)
        if df.empty:
            return df
        df = df.set_index("team").sort_values("elo_rank")
        logger.info("ELO rankings: %d teams fetched for %d", len(df), year)
        return df

    def read_latest_matches(self) -> pd.DataFrame:
        """Fetch recent international match results with ELO changes.

        Returns
        -------
        pd.DataFrame
            One row per match with team names, scores, ratings, and tournament.
        """
        filepath = self.data_dir / "latest.tsv"
        url = f"{ELO_BASE_URL}/latest.tsv"
        raw = self._fetch(url, filepath, max_age_days=1)
        return self._parse_matches(raw)

    def read_matches_for_year(self, year: int) -> pd.DataFrame:
        """Fetch international match results for a specific year.

        Parameters
        ----------
        year : int
            Year to fetch (e.g. 2022).

        Returns
        -------
        pd.DataFrame
            One row per match, same format as read_latest_matches().
        """
        filepath = self.data_dir / f"matches_{year}.tsv"
        url = f"{ELO_BASE_URL}/{year}_results.tsv"
        raw = self._fetch(url, filepath, max_age_days=30)
        df = self._parse_matches(raw)
        if not df.empty:
            logger.info("ELO matches for %d: %d results", year, len(df))
        return df

    def read_matches_range(self, start_year: int, end_year: int) -> pd.DataFrame:
        """Fetch match results across multiple years.

        Parameters
        ----------
        start_year : int
            First year (inclusive).
        end_year : int
            Last year (inclusive).

        Returns
        -------
        pd.DataFrame
            Combined match results sorted by date descending.
        """
        frames = []
        for year in range(start_year, end_year + 1):
            try:
                df = self.read_matches_for_year(year)
                if not df.empty:
                    frames.append(df)
            except ConnectionError:
                logger.warning("No match data available for year %d", year)
        if not frames:
            return pd.DataFrame()
        combined = pd.concat(frames, ignore_index=True)
        combined = combined.drop_duplicates(
            subset=["date", "team1_code", "team2_code"], keep="first"
        )
        combined = combined.sort_values("date", ascending=False).reset_index(drop=True)
        logger.info("ELO matches %d-%d: %d total results", start_year, end_year, len(combined))
        return combined

    def _parse_matches(self, raw: str) -> pd.DataFrame:
        """Parse TSV match data into DataFrame.

        Parameters
        ----------
        raw : str
            Raw TSV text with 16 fields per line (MATCH_COLUMNS format).

        Returns
        -------
        pd.DataFrame
            Parsed match results.
        """
        team_map = self._get_team_map()
        tournament_map = self._get_tournament_map()

        rows = []
        for line in raw.strip().split("\n"):
            if not line.strip():
                continue
            fields = line.split("\t")
            if len(fields) < 16:
                continue
            row = {}
            for i, col in enumerate(MATCH_COLUMNS):
                val = fields[i].replace("\u2212", "-").strip()
                try:
                    row[col] = int(val)
                except ValueError:
                    row[col] = val

            # Resolve team names
            row["team1"] = team_map.get(row["team1_code"], row["team1_code"])
            row["team2"] = team_map.get(row["team2_code"], row["team2_code"])
            # Resolve tournament
            row["tournament"] = tournament_map.get(
                row.get("tournament_code", ""), row.get("tournament_code", "")
            )
            # Build date
            try:
                row["date"] = f"{row['year']:04d}-{row['month']:02d}-{row['day']:02d}"
            except (ValueError, TypeError):
                row["date"] = None

            # Venue: empty = home/away, code = neutral ground
            venue = row.get("venue_code", "")
            if venue and venue != row["team1_code"]:
                row["venue"] = team_map.get(venue, venue) if venue else "Home/Away"
            else:
                row["venue"] = "Home"

            rows.append(row)

        df = pd.DataFrame(rows)
        if df.empty:
            return df

        # Reorder columns
        col_order = [
            "date", "team1", "team2", "team1_score", "team2_score",
            "tournament", "venue",
            "team1_elo_before", "team2_elo_before",
            "team1_elo_change", "team2_elo_change",
            "team1_rank", "team2_rank",
            "elo_rating_diff",
            "team1_code", "team2_code", "tournament_code", "venue_code",
            "year", "month", "day",
        ]
        col_order = [c for c in col_order if c in df.columns]
        df = df[col_order].sort_values("date", ascending=False).reset_index(drop=True)
        logger.info("ELO matches: %d results parsed", len(df))
        return df

    # ------------------------------------------------------------------
    # Reference data
    # ------------------------------------------------------------------

    def _get_team_map(self) -> dict[str, str]:
        """Return {code: name} dict from en.teams.tsv. Cached after first fetch."""
        if self._team_map is not None:
            return self._team_map

        filepath = self.data_dir / "en.teams.tsv"
        url = f"{ELO_BASE_URL}/en.teams.tsv"
        raw = self._fetch(url, filepath, max_age_days=30)

        team_map = {}
        for line in raw.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t")
            code = parts[0]
            if code.endswith("_loc"):
                continue
            name = parts[1] if len(parts) > 1 else code
            team_map[code] = name

        self._team_map = team_map
        logger.debug("ELO team map: %d entries", len(team_map))
        return team_map

    def _get_tournament_map(self) -> dict[str, str]:
        """Return {code: name} dict from en.tournaments.tsv. Cached after first fetch."""
        if self._tournament_map is not None:
            return self._tournament_map

        filepath = self.data_dir / "en.tournaments.tsv"
        url = f"{ELO_BASE_URL}/en.tournaments.tsv"
        raw = self._fetch(url, filepath, max_age_days=30)

        tournament_map = {}
        for line in raw.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t")
            code = parts[0]
            name = parts[1] if len(parts) > 1 else code
            tournament_map[code] = name

        self._tournament_map = tournament_map
        logger.debug("ELO tournament map: %d entries", len(tournament_map))
        return tournament_map

    # ------------------------------------------------------------------
    # Internal: fetch with cache
    # ------------------------------------------------------------------

    def _fetch(self, url: str, filepath: Path, max_age_days: int = 1) -> str:
        """Fetch URL with file-based caching.

        Parameters
        ----------
        url : str
            URL to fetch.
        filepath : Path
            Local cache file.
        max_age_days : int
            Cache expiry in days.

        Returns
        -------
        str
            Raw text content.
        """
        if not self.no_cache and filepath.exists():
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime, tz=timezone.utc)
            age = datetime.now(tz=timezone.utc) - mtime
            if age < timedelta(days=max_age_days):
                logger.debug("Cache hit: %s", filepath.name)
                return filepath.read_text(encoding="utf-8")

        # Rate limit
        delay = self.rate_limit + random.uniform(0, self.max_delay)
        time.sleep(delay)

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/plain,text/tab-separated-values,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        logger.debug("Fetching %s", url)
        response = self._session.get(url, headers=headers)
        if response.status_code != 200:
            raise ConnectionError(f"HTTP {response.status_code} for {url}")

        text = response.text
        filepath.write_text(text, encoding="utf-8")
        logger.debug("Cached: %s (%d bytes)", filepath.name, len(text))
        return text
