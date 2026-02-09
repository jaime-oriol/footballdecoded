"""FotMob scraper: player and team season stats via JSON API.

Uses the ``leagueseasondeepstats`` endpoint to fetch one stat key per request,
then merges all keys into a single DataFrame per entity type (players/teams).
All metric columns are prefixed with ``fotmob_``.
"""

import json
import random
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Callable, Optional, Union

import pandas as pd

from ._common import BaseRequestsReader
from ._config import DATA_DIR, LEAGUE_DICT, NOCACHE, NOSTORE, logger

FOTMOB_DATADIR = DATA_DIR / "FotMob"
FOTMOB_API = "https://www.fotmob.com/api"

FOTMOB_LEAGUE_IDS = {
    "ENG-Premier League": 47,
    "ESP-LaLiga": 87,
    "ITA-Serie A": 55,
    "GER-Bundesliga": 54,
    "FRA-Ligue 1": 53,
    "INT-Champions League": 42,
    "INT-World Cup": 77,
    "INT-EURO": 50,
    "INT-Women's World Cup": 76,
    "POR-Primeira Liga": 61,
    "NED-Eredivisie": 57,
    "BEL-Pro League": 40,
    "TUR-Super Lig": 71,
    "SCO-Premiership": 64,
    "SUI-Super League": 69,
    "USA-MLS": 130,
}

PLAYER_STAT_KEYS = [
    "goals",
    "goal_assist",
    "_goals_and_goal_assist",
    "rating",
    "mins_played",
    "goals_per_90",
    "expected_goals",
    "expected_goals_per_90",
    "expected_goalsontarget",
    "ontarget_scoring_att",
    "total_scoring_att",
    "accurate_pass",
    "big_chance_created",
    "total_att_assist",
    "accurate_long_balls",
    "expected_assists",
    "expected_assists_per_90",
    "_expected_goals_and_expected_assists_per_90",
    "won_contest",
    "big_chance_missed",
    "penalty_won",
    "total_tackle",
    "interception",
    "effective_clearance",
    "outfielder_block",
    "penalty_conceded",
    "poss_won_att_3rd",
    "clean_sheet",
    "_save_percentage",
    "saves",
    "_goals_prevented",
    "goals_conceded",
    "fouls",
    "yellow_card",
    "red_card",
]

TEAM_STAT_KEYS = [
    "rating_team",
    "goals_team_match",
    "goals_conceded_team_match",
    "possession_percentage_team",
    "clean_sheet_team",
    "home_attendance_team",
    "expected_goals_team",
    "_xg_diff_team",
    "ontarget_scoring_att_team",
    "big_chance_team",
    "big_chance_missed_team",
    "accurate_pass_team",
    "accurate_long_balls_team",
    "accurate_cross_team",
    "penalty_won_team",
    "touches_in_opp_box_team",
    "corner_taken_team",
    "expected_goals_conceded_team",
    "interception_team",
    "total_tackle_team",
    "effective_clearance_team",
    "poss_won_att_3rd_team",
    "penalty_conceded_team",
    "saves_team",
    "fk_foul_lost_team",
    "total_yel_card_team",
    "total_red_card_team",
]


def _fotmob_league_id(league: str) -> Optional[int]:
    """Resolve LEAGUE_DICT key to FotMob numeric league ID."""
    fotmob_key = LEAGUE_DICT.get(league, {}).get("FotMob")
    if fotmob_key is None:
        return None
    return FOTMOB_LEAGUE_IDS.get(fotmob_key)


class FotMob(BaseRequestsReader):
    """Scrape player and team season stats from the FotMob JSON API.

    Fetches per-stat-key data from ``leagueseasondeepstats`` and merges
    results into unified DataFrames. Cached locally in ``data/FotMob/``.

    Parameters
    ----------
    leagues : str or list of str, optional
        Leagues to read (LEAGUE_DICT keys). None = all available.
    seasons : str or int or list, optional
        Seasons to read (e.g. '2425', '2024'). None = current.
    proxy : 'tor' or str or list or callable, optional
        Proxy for requests.
    no_cache : bool
        Skip cached data.
    no_store : bool
        Do not store downloaded data.
    data_dir : Path
        Cache directory path.
    """

    def __init__(
        self,
        leagues: Optional[Union[str, list[str]]] = None,
        seasons: Optional[Union[str, int, Iterable[Union[str, int]]]] = None,
        proxy: Optional[Union[str, list[str], Callable[[], str]]] = None,
        no_cache: bool = NOCACHE,
        no_store: bool = NOSTORE,
        data_dir: Path = FOTMOB_DATADIR,
    ):
        """Initialize reader with rate_limit=3s and max_delay=2s jitter."""
        super().__init__(
            leagues=leagues,
            proxy=proxy,
            no_cache=no_cache,
            no_store=no_store,
            data_dir=data_dir,
        )
        self.seasons = seasons  # type: ignore
        self.rate_limit = 3
        self.max_delay = 2

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def read_player_season_stats(self, force_cache: bool = False) -> pd.DataFrame:
        """Retrieve player season stats for the selected leagues and seasons.

        Fetches each player stat key individually and merges into one DataFrame.
        All metric columns are prefixed with ``fotmob_``.

        Parameters
        ----------
        force_cache : bool
            If True, force use of cached data even for the current season.

        Returns
        -------
        pd.DataFrame
        """
        return self._read_season_stats("players", PLAYER_STAT_KEYS, force_cache)

    def read_team_season_stats(self, force_cache: bool = False) -> pd.DataFrame:
        """Retrieve team season stats for the selected leagues and seasons.

        Fetches each team stat key individually and merges into one DataFrame.
        All metric columns are prefixed with ``fotmob_``.

        Parameters
        ----------
        force_cache : bool
            If True, force use of cached data even for the current season.

        Returns
        -------
        pd.DataFrame
        """
        return self._read_season_stats("teams", TEAM_STAT_KEYS, force_cache)

    def read_league_stats(self, force_cache: bool = False) -> dict:
        """Retrieve both player and team season stats.

        Parameters
        ----------
        force_cache : bool
            If True, force use of cached data even for the current season.

        Returns
        -------
        dict
            Keys ``'players'`` and ``'teams'`` mapping to DataFrames.
        """
        return {
            "players": self.read_player_season_stats(force_cache=force_cache),
            "teams": self.read_team_season_stats(force_cache=force_cache),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_season_stats(
        self, entity_type: str, stat_keys: list[str], force_cache: bool
    ) -> pd.DataFrame:
        """Fetch all stat keys for entity_type across selected leagues/seasons.

        Each stat key requires a separate API call. Results are merged by
        entity ID into a single row per player/team.
        """
        all_records: dict[tuple, dict] = {}  # (league, season, eid) -> record

        for league in self.leagues:
            league_id = _fotmob_league_id(league)
            if league_id is None:
                logger.warning("No FotMob ID for league '%s', skipping", league)
                continue

            for season in self.seasons:
                season_id = self._resolve_season_id(league_id, season, force_cache)
                if season_id is None:
                    logger.warning(
                        "Could not resolve season '%s' for league '%s'", season, league
                    )
                    continue

                is_current = not self._is_complete(league, season)
                no_cache = is_current and not force_cache

                for stat_key in stat_keys:
                    data = self._fetch_stat(
                        league_id, season_id, entity_type, stat_key, no_cache
                    )
                    if data is None:
                        continue

                    col_name = f"fotmob_{stat_key.lstrip('_')}"

                    for row in data:
                        eid = row["id"]
                        key = (league, season, eid)

                        if key not in all_records:
                            rec = {
                                "league": league,
                                "season": season,
                                "fotmob_id": eid,
                                "name": row["name"],
                                "fotmob_team_id": row.get("teamId"),
                            }
                            if entity_type == "players":
                                rec["fotmob_position"] = row.get("position")
                            all_records[key] = rec

                        sv = row.get("statValue", {})
                        all_records[key][col_name] = _safe_number(sv.get("value"))

                        # substatValue is typically appearances (same for all stat keys)
                        ssv = row.get("substatValue", {})
                        sub_val = _safe_number(ssv.get("value"))
                        if sub_val is not None and f"{col_name}_sub" not in all_records[key]:
                            all_records[key][f"{col_name}_sub"] = sub_val

        if entity_type == "players":
            index = ["league", "season", "name"]
        else:
            index = ["league", "season", "name"]

        if not all_records:
            return pd.DataFrame()

        df = pd.DataFrame.from_records(list(all_records.values()))

        # All stat keys return the same appearances substat; keep one, drop duplicates
        sub_cols = [c for c in df.columns if c.endswith("_sub")]
        if sub_cols:
            first_sub = sub_cols[0]
            df = df.rename(columns={first_sub: "fotmob_appearances"})
            drop_subs = [c for c in sub_cols[1:] if c in df.columns]
            if drop_subs:
                df = df.drop(columns=drop_subs)

        return df.set_index(index).sort_index().convert_dtypes()

    def _resolve_season_id(
        self, league_id: int, season: str, force_cache: bool
    ) -> Optional[int]:
        """Map a season code (e.g. '2425') to FotMob's numeric season ID."""
        seasons_map = self._fetch_seasons_map(league_id, force_cache)
        if not seasons_map:
            return None

        # Convert our code to FotMob format: '2425' -> '2024/2025', '2024' stays '2024'
        if len(season) == 4:
            y1, y2 = int(season[:2]), int(season[2:])
            # Multi-year if y2 == y1+1 and not a full year like '2024' (century prefix)
            is_multi_year = (y2 == (y1 + 1) % 100) and season[:2] not in ("19", "20")
            if is_multi_year:
                c1 = 2000 if y1 < 80 else 1900
                c2 = 2000 if y2 < 80 else 1900
                target = f"{c1 + y1}/{c2 + y2}"
            else:
                target = season
        else:
            target = season

        for sid, name in seasons_map.items():
            if name == target or name.startswith(target):
                return sid

        logger.debug("Season '%s' (target '%s') not found in FotMob seasons", season, target)
        return None

    def _fetch_seasons_map(self, league_id: int, force_cache: bool = False) -> dict:
        """Return {season_id: season_name} for a league from cached or API data."""
        filepath = self.data_dir / f"seasons_{league_id}.json"
        max_age = 30 if force_cache else 7

        if self._is_cached(filepath, max_age):
            with filepath.open("r") as f:
                return {int(k): v for k, v in json.load(f).items()}

        # Any stat request returns the full seasons list as a side effect
        url = f"{FOTMOB_API}/leagueseasondeepstats?id={league_id}&season=0&type=players&stat=goals"
        try:
            response = self._session.get(url, headers=self._get_fotmob_headers())
            time.sleep(self.rate_limit + random.random() * self.max_delay)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.error("Failed to fetch seasons for league %d: %s", league_id, str(e)[:100])
            return {}

        seasons = data.get("seasons", [])
        result = {s["id"]: s["name"] for s in seasons}

        if not self.no_store:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with filepath.open("w") as f:
                json.dump(result, f)

        return result

    def _fetch_stat(
        self,
        league_id: int,
        season_id: int,
        entity_type: str,
        stat_key: str,
        no_cache: bool = False,
    ) -> Optional[list[dict]]:
        """Fetch a single stat key from the leagueseasondeepstats endpoint."""
        filepath = (
            self.data_dir / f"stats_{league_id}_{season_id}_{entity_type}_{stat_key}.json"
        )

        url = (
            f"{FOTMOB_API}/leagueseasondeepstats"
            f"?id={league_id}&season={season_id}&type={entity_type}&stat={stat_key}"
        )

        try:
            reader = self.get(url, filepath, max_age=30, no_cache=no_cache)
            data = json.load(reader)
        except Exception as e:
            logger.debug("Failed to fetch stat %s: %s", stat_key, str(e)[:100])
            return None

        stats_data = data.get("statsData", [])
        if not stats_data:
            return None

        return stats_data

    def _get_fotmob_headers(self) -> dict:
        """Return headers suitable for FotMob API requests."""
        headers = self._get_random_headers()
        headers.update({
            "Accept": "application/json",
            "Referer": "https://www.fotmob.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        })
        return headers

    def _download_and_save(self, url, filepath=None, var=None):
        """Override base method to use FotMob-specific headers. Retries up to 5 times."""
        for i in range(5):
            try:
                response = self._session.get(url, headers=self._get_fotmob_headers())
                time.sleep(self.rate_limit + random.random() * self.max_delay)
                response.raise_for_status()

                payload = response.content

                if not self.no_store and filepath is not None:
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    with filepath.open(mode="wb") as fh:
                        fh.write(payload)

                import io
                return io.BytesIO(payload)
            except Exception as e:
                logger.error(
                    "Error fetching %s (attempt %d/5): %s",
                    url, i + 1, str(e)[:100],
                )
                self._session = self._init_session()
                continue

        raise ConnectionError(f"Could not download {url}.")


def _safe_number(value: Any) -> Optional[float]:
    """Convert value to float, returning None on failure or None input."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
