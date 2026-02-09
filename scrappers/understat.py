"""Scraper for understat.com -- xG, xA, PPDA and advanced stats.

Extracts data from Understat's AJAX API and embedded JavaScript.
Coverage: Big 5 European leagues only.
"""

import itertools
import json
from collections.abc import Iterable
from html import unescape
from pathlib import Path
from typing import Any, Callable, Optional, Union

import pandas as pd

from ._common import BaseRequestsReader, make_game_id
from ._config import DATA_DIR, NOCACHE, NOSTORE, TEAMNAME_REPLACEMENTS

UNDERSTAT_DATADIR = DATA_DIR / "Understat"
UNDERSTAT_URL = "https://understat.com"

# Understat internal codes -> human-readable labels
SHOT_SITUATIONS = {
    "OpenPlay": "Open Play",
    "FromCorner": "From Corner",
    "SetPiece": "Set Piece",
    "DirectFreekick": "Direct Freekick",
}

SHOT_BODY_PARTS = {
    "RightFoot": "Right Foot",
    "LeftFoot": "Left Foot",
    "OtherBodyParts": "Other",
}

SHOT_RESULTS = {
    "Goal": "Goal",
    "OwnGoal": "Own Goal",
    "BlockedShot": "Blocked Shot",
    "SavedShot": "Saved Shot",
    "MissedShots": "Missed Shot",
    "ShotOnPost": "Shot On Post",
}


class Understat(BaseRequestsReader):
    """Scraper for understat.com xG data (Big 5 leagues only).

    Fetches league standings, match schedules, player/team stats, shot events,
    and advanced breakdowns (situation, formation, gameState, timing, etc.)
    via Understat's AJAX API. Raw responses are cached locally for 30 days.

    Parameters
    ----------
    leagues : str or list of str, optional
        League codes to scrape (e.g. "ESP-La Liga").
    seasons : str, int, or iterable, optional
        Seasons to scrape (e.g. "24-25" or 2024).
    proxy : str, list of str, or callable, optional
        Proxy configuration for requests.
    no_cache : bool
        If True, bypass cached data.
    no_store : bool
        If True, do not store downloaded data.
    data_dir : Path
        Directory for cached data.
    """

    def __init__(
        self,
        leagues: Optional[Union[str, list[str]]] = None,
        seasons: Optional[Union[str, int, Iterable[Union[str, int]]]] = None,
        proxy: Optional[Union[str, list[str], Callable[[], str]]] = None,
        no_cache: bool = NOCACHE,
        no_store: bool = NOSTORE,
        data_dir: Path = UNDERSTAT_DATADIR,
    ):
        """Initialize a new Understat reader."""
        super().__init__(
            leagues=leagues,
            proxy=proxy,
            no_cache=no_cache,
            no_store=no_store,
            data_dir=data_dir,
        )
        self.seasons = seasons  # type: ignore

    def read_leagues(self) -> pd.DataFrame:
        """Retrieve available leagues as a DataFrame indexed by league name."""
        data = self._read_leagues()

        leagues = {}

        league_data = data["statData"]
        for league_stat in league_data:
            league_id = league_stat["league_id"]
            if league_id not in leagues:
                league = league_stat["league"]
                league_slug = league.replace(" ", "_")
                leagues[league_id] = {
                    "league_id": league_id,
                    "league": league,
                    "url": UNDERSTAT_URL + f"/league/{league_slug}",
                }

        index = "league"
        if len(leagues) == 0:
            return pd.DataFrame(index=index)

        df = (
            pd.DataFrame.from_records(list(leagues.values()))
            .pipe(self._translate_league)
            .set_index(index)
            .sort_index()
            .convert_dtypes()
        )

        valid_leagues = [league for league in self.leagues if league in df.index]
        return df.loc[valid_leagues]

    def read_seasons(self) -> pd.DataFrame:
        """Retrieve available seasons for selected leagues."""
        data = self._read_leagues()

        seasons = {}

        league_data = data["statData"]
        for league_stat in league_data:
            league_id = league_stat["league_id"]
            year = int(league_stat["year"])
            month = int(league_stat["month"])
            # Seasons start in July/August
            season_id = year if month >= 7 else year - 1
            key = (league_id, season_id)
            if key not in seasons:
                league = league_stat["league"]
                league_slug = league.replace(" ", "_")
                season = f"{season_id}/{season_id + 1}"
                seasons[key] = {
                    "league_id": league_id,
                    "league": league,
                    "season_id": season_id,
                    "season": self._season_code.parse(season),
                    "url": UNDERSTAT_URL + f"/league/{league_slug}/{season_id}",
                }

        index = ["league", "season"]
        if len(seasons) == 0:
            return pd.DataFrame(index=index)

        df = (
            pd.DataFrame.from_records(list(seasons.values()))
            .pipe(self._translate_league)
            .set_index(index)
            .sort_index()
            .convert_dtypes()
        )

        all_seasons = itertools.product(self.leagues, self.seasons)
        valid_seasons = [season for season in all_seasons if season in df.index]
        return df.loc[valid_seasons]

    def read_schedule(
        self, include_matches_without_data: bool = True, force_cache: bool = False
    ) -> pd.DataFrame:
        """Retrieve match schedule for selected leagues and seasons.

        Parameters
        ----------
        include_matches_without_data : bool
            If False, only return matches that have xG data.
        force_cache : bool
            If True, use cached data even for the current season.
        """
        df_seasons = self.read_seasons()

        matches = []

        for (league, season), league_season in df_seasons.iterrows():
            league_id = league_season["league_id"]
            season_id = league_season["season_id"]
            url = league_season["url"]

            is_current_season = not self._is_complete(league, season)
            no_cache = is_current_season and not force_cache

            data = self._read_league_season(url, league_id, season_id, no_cache)

            matches_data = data["datesData"]
            for match in matches_data:
                match_id = _as_int(match["id"])
                # xG != 0 means Understat has processed this match
                has_home_xg = match["xG"]["h"] not in ("0", None)
                has_away_xg = match["xG"]["a"] not in ("0", None)
                has_data = has_home_xg or has_away_xg
                matches.append(
                    {
                        "league_id": league_id,
                        "league": league,
                        "season_id": season_id,
                        "season": season,
                        "game_id": match_id,
                        "date": match["datetime"],
                        "home_team_id": _as_int(match["h"]["id"]),
                        "away_team_id": _as_int(match["a"]["id"]),
                        "home_team": _as_str(match["h"]["title"]),
                        "away_team": _as_str(match["a"]["title"]),
                        "away_team_code": match["a"]["short_title"],
                        "home_team_code": match["h"]["short_title"],
                        "home_goals": _as_int(match["goals"]["h"]),
                        "away_goals": _as_int(match["goals"]["a"]),
                        "home_xg": _as_float(match["xG"]["h"]),
                        "away_xg": _as_float(match["xG"]["a"]),
                        "is_result": _as_bool(match["isResult"]),
                        "has_data": has_data,
                        "url": UNDERSTAT_URL + f"/match/{match_id}",
                    }
                )

        index = ["league", "season", "game"]
        if len(matches) == 0:
            return pd.DataFrame(index=index)

        df = (
            pd.DataFrame.from_records(matches)
            .assign(date=lambda g: pd.to_datetime(g["date"], format="%Y-%m-%d %H:%M:%S"))
            .replace(
                {
                    "home_team": TEAMNAME_REPLACEMENTS,
                    "away_team": TEAMNAME_REPLACEMENTS,
                }
            )
            .assign(game=lambda g: g.apply(make_game_id, axis=1))
            .set_index(index)
            .sort_index()
            .convert_dtypes()
        )

        if not include_matches_without_data:
            df = df[df["has_data"]]

        return df

    def read_team_match_stats(self, force_cache: bool = False) -> pd.DataFrame:
        """Retrieve per-match team stats (xG, PPDA, deep completions, etc.).

        Parameters
        ----------
        force_cache : bool
            If True, use cached data even for the current season.
        """
        df_seasons = self.read_seasons()

        stats = {}

        for (league, season), league_season in df_seasons.iterrows():
            league_id = league_season["league_id"]
            season_id = league_season["season_id"]
            url = league_season["url"]

            is_current_season = not self._is_complete(league, season)
            no_cache = is_current_season and not force_cache

            data = self._read_league_season(url, league_id, season_id, no_cache)

            schedule = {}  # match_id -> match metadata
            matches = {}   # (date, team_id) -> match_id

            matches_data = data["datesData"]
            for match in matches_data:
                match_id = _as_int(match["id"])
                match_date = match["datetime"]
                schedule[match_id] = {
                    "league_id": league_id,
                    "league": league,
                    "season_id": season_id,
                    "season": season,
                    "game_id": match_id,
                    "date": match["datetime"],
                    "home_team_id": _as_int(match["h"]["id"]),
                    "away_team_id": _as_int(match["a"]["id"]),
                    "home_team": _as_str(match["h"]["title"]),
                    "away_team": _as_str(match["a"]["title"]),
                    "away_team_code": _as_str(match["a"]["short_title"]),
                    "home_team_code": _as_str(match["h"]["short_title"]),
                }
                for side in ("h", "a"):
                    team_id = _as_int(match[side]["id"])
                    matches[(match_date, team_id)] = match_id

            teams_data = data["teamsData"]
            for team in teams_data.values():
                team_id = _as_int(team["id"])
                for match in team["history"]:
                    match_date = match["date"]
                    match_id = matches[(match_date, team_id)]
                    team_side = match["h_a"]
                    prefix = "home" if team_side == "h" else "away"

                    if match_id not in stats:
                        stats[match_id] = schedule[match_id]

                    # PPDA = Passes Allowed per Defensive Action
                    ppda = match["ppda"]
                    team_ppda = (ppda["att"] / ppda["def"]) if ppda["def"] != 0 else pd.NA

                    stats[match_id].update(
                        {
                            f"{prefix}_points": _as_int(match["pts"]),
                            f"{prefix}_expected_points": _as_float(match["xpts"]),
                            f"{prefix}_goals": _as_int(match["scored"]),
                            f"{prefix}_xg": _as_float(match["xG"]),
                            f"{prefix}_np_xg": _as_float(match["npxG"]),
                            f"{prefix}_np_xg_difference": _as_float(match["npxGD"]),
                            f"{prefix}_ppda": _as_float(team_ppda),
                            f"{prefix}_deep_completions": _as_int(match["deep"]),
                        }
                    )

        index = ["league", "season", "game"]
        if len(stats) == 0:
            return pd.DataFrame(index=index)

        return (
            pd.DataFrame.from_records(list(stats.values()))
            .assign(date=lambda g: pd.to_datetime(g["date"], format="%Y-%m-%d %H:%M:%S"))
            .replace(
                {
                    "home_team": TEAMNAME_REPLACEMENTS,
                    "away_team": TEAMNAME_REPLACEMENTS,
                }
            )
            .assign(game=lambda g: g.apply(make_game_id, axis=1))
            .set_index(index)
            .sort_index()
            .convert_dtypes()
        )

    def read_player_season_stats(self, force_cache: bool = False) -> pd.DataFrame:
        """Retrieve aggregated player stats per season (xG, xA, xGChain, etc.).

        Parameters
        ----------
        force_cache : bool
            If True, use cached data even for the current season.
        """
        df_seasons = self.read_seasons()

        stats = []
        for (league, season), league_season in df_seasons.iterrows():
            league_id = league_season["league_id"]
            season_id = league_season["season_id"]
            url = league_season["url"]

            is_current_season = not self._is_complete(league, season)
            no_cache = is_current_season and not force_cache

            data = self._read_league_season(url, league_id, season_id, no_cache)

            teams_data = data["teamsData"]
            team_mapping = {}
            for team in teams_data.values():
                team_name = _as_str(team["title"])
                team_id = _as_int(team["id"])
                team_mapping[team_name] = team_id

            players_data = data["playersData"]
            for player in players_data:
                player_team_name = player["team_title"]
                # Multi-team players: take the first (most recent) team
                if "," in player_team_name:
                    player_team_name = player_team_name.split(",")[0]
                player_team_name = _as_str(player_team_name)
                player_team_id = team_mapping[player_team_name]
                stats.append(
                    {
                        "league": league,
                        "league_id": league_id,
                        "season": season,
                        "season_id": season_id,
                        "team": player_team_name,
                        "team_id": player_team_id,
                        "player": _as_str(player["player_name"]),
                        "player_id": _as_int(player["id"]),
                        "position": _as_str(player["position"]),
                        "matches": _as_int(player["games"]),
                        "minutes": _as_int(player["time"]),
                        "goals": _as_int(player["goals"]),
                        "xg": _as_float(player["xG"]),
                        "np_goals": _as_int(player["npg"]),
                        "np_xg": _as_float(player["npxG"]),
                        "assists": _as_int(player["assists"]),
                        "xa": _as_float(player["xA"]),
                        "shots": _as_int(player["shots"]),
                        "key_passes": _as_int(player["key_passes"]),
                        "yellow_cards": _as_int(player["yellow_cards"]),
                        "red_cards": _as_int(player["red_cards"]),
                        "xg_chain": _as_float(player["xGChain"]),
                        "xg_buildup": _as_float(player["xGBuildup"]),
                    }
                )

        index = ["league", "season", "team", "player"]
        if len(stats) == 0:
            return pd.DataFrame(index=index)

        return (
            pd.DataFrame.from_records(stats)
            .replace(
                {
                    "team": TEAMNAME_REPLACEMENTS,
                }
            )
            .set_index(index)
            .sort_index()
            .convert_dtypes()
        )

    def read_player_match_stats(
        self, match_id: Optional[Union[int, list[int]]] = None
    ) -> pd.DataFrame:
        """Retrieve per-match player stats (xG, xA, xGChain, xGBuildup).

        Parameters
        ----------
        match_id : int or list of int, optional
            Filter to specific match(es). If None, all matches in selected seasons.

        Raises
        ------
        ValueError
            If match_id not found in selected seasons.
        """
        df_schedule = self.read_schedule(include_matches_without_data=False)
        df_results = self._select_matches(df_schedule, match_id)

        stats = []
        for (league, season, game), league_season_game in df_results.iterrows():
            league_id = league_season_game["league_id"]
            season_id = league_season_game["season_id"]
            game_id = league_season_game["game_id"]
            url = league_season_game["url"]

            data = self._read_match(url, game_id)
            if data is None:
                continue

            match_info = data["match_info"]
            team_id_to_name = {
                match_info[side]: _as_str(match_info[f"team_{side}"]) for side in ("h", "a")
            }

            players_data = data["rostersData"]
            for team_players in players_data.values():
                for player in team_players.values():
                    team_id = player["team_id"]
                    team = team_id_to_name[team_id]
                    stats.append(
                        {
                            "league": league,
                            "league_id": league_id,
                            "season": season,
                            "season_id": season_id,
                            "game_id": game_id,
                            "game": game,
                            "team": team,
                            "team_id": _as_int(team_id),
                            "player": _as_str(player["player"]),
                            "player_id": _as_int(player["player_id"]),
                            "position": _as_str(player["position"]),
                            "position_id": _as_int(player["positionOrder"]),
                            "minutes": _as_int(player["time"]),
                            "goals": _as_int(player["goals"]),
                            "own_goals": _as_int(player["own_goals"]),
                            "shots": _as_int(player["shots"]),
                            "xg": _as_float(player["xG"]),
                            "xg_chain": _as_float(player["xGChain"]),
                            "xg_buildup": _as_float(player["xGBuildup"]),
                            "assists": _as_int(player["assists"]),
                            "xa": _as_float(player["xA"]),
                            "key_passes": _as_int(player["key_passes"]),
                            "yellow_cards": _as_int(player["yellow_card"]),
                            "red_cards": _as_int(player["red_card"]),
                        }
                    )

        index = ["league", "season", "game", "team", "player"]
        if len(stats) == 0:
            return pd.DataFrame(index=index)

        return (
            pd.DataFrame.from_records(stats)
            .replace(
                {
                    "team": TEAMNAME_REPLACEMENTS,
                }
            )
            .set_index(index)
            .sort_index()
            .convert_dtypes()
        )

    def read_shot_events(self, match_id: Optional[Union[int, list[int]]] = None) -> pd.DataFrame:
        """Retrieve shot events with xG, coordinates, body part, situation, and result.

        Parameters
        ----------
        match_id : int or list of int, optional
            Filter to specific match(es). If None, all matches in selected seasons.

        Raises
        ------
        ValueError
            If match_id not found in selected seasons.
        """
        df_schedule = self.read_schedule(include_matches_without_data=False)
        df_results = self._select_matches(df_schedule, match_id)

        shots = []
        for (league, season, game), league_season_game in df_results.iterrows():
            league_id = league_season_game["league_id"]
            season_id = league_season_game["season_id"]
            game_id = league_season_game["game_id"]
            url = league_season_game["url"]

            data = self._read_match(url, game_id)
            if data is None:
                continue

            match_info = data["match_info"]
            team_name_to_id = {
                _as_str(match_info[f"team_{side}"]): _as_int(match_info[side])
                for side in ("h", "a")
            }

            rosters_data = data["rostersData"]
            player_name_to_id = {}
            for team_data in rosters_data.values():
                for player in team_data.values():
                    player_name = _as_str(player["player"])
                    player_id = _as_int(player["id"])
                    player_name_to_id[player_name] = player_id

            shots_data = data["shotsData"]
            for team_shots in shots_data.values():
                for shot in team_shots:
                    team_side = shot["h_a"]
                    team = _as_str(shot[f"{team_side}_team"])
                    team_id = team_name_to_id[team]
                    assist_player = _as_str(shot["player_assisted"])
                    assist_player_id = player_name_to_id.get(assist_player, pd.NA)
                    shots.append(
                        {
                            "league_id": league_id,
                            "league": league,
                            "season_id": season_id,
                            "season": season,
                            "game_id": game_id,
                            "game": game,
                            "date": shot["date"],
                            "shot_id": _as_int(shot["id"]),
                            "team_id": team_id,
                            "team": team,
                            "player_id": _as_int(shot["player_id"]),
                            "player": shot["player"],
                            "assist_player_id": assist_player_id,
                            "assist_player": assist_player,
                            "xg": _as_float(shot["xG"]),
                            "location_x": _as_float(shot["X"]),
                            "location_y": _as_float(shot["Y"]),
                            "minute": _as_int(shot["minute"]),
                            "body_part": SHOT_BODY_PARTS.get(shot["shotType"], pd.NA),
                            "situation": SHOT_SITUATIONS.get(shot["situation"], pd.NA),
                            "result": SHOT_RESULTS.get(shot["result"], pd.NA),
                        }
                    )

        index = ["league", "season", "game", "team", "player"]
        if len(shots) == 0:
            return pd.DataFrame(index=index)

        return (
            pd.DataFrame.from_records(shots)
            .assign(date=lambda g: pd.to_datetime(g["date"], format="%Y-%m-%d %H:%M:%S"))
            .replace(
                {
                    "team": TEAMNAME_REPLACEMENTS,
                }
            )
            .set_index(index)
            .sort_index()
            .convert_dtypes()
        )

    def read_team_advanced_stats(self, force_cache: bool = False) -> pd.DataFrame:
        """Retrieve advanced team stats from getTeamData endpoint.

        Fetches 7 stat categories (situation, formation, gameState, timing,
        shotZone, attackSpeed, result) per team and flattens them into ~200 columns.

        Parameters
        ----------
        force_cache : bool
            If True, use cached data even for the current season.
        """
        df_seasons = self.read_seasons()
        records = []

        for (league, season), league_season in df_seasons.iterrows():
            season_id = league_season["season_id"]
            url = league_season["url"]

            is_current_season = not self._is_complete(league, season)
            no_cache = is_current_season and not force_cache

            data = self._read_league_season(url, league_season["league_id"], season_id, no_cache)
            teams_data = data["teamsData"]

            for team in teams_data.values():
                team_name = _as_str(team["title"])
                team_id = _as_int(team["id"])
                team_slug = team_name.replace(" ", "_")

                endpoint = f"{UNDERSTAT_URL}/getTeamData/{team_slug}/{season_id}"
                filepath = self.data_dir / f"team_{team_id}_{season_id}_advanced.json"

                try:
                    team_data = self._fetch_ajax(endpoint, filepath, no_cache)
                except Exception as e:
                    from ._config import logger
                    logger.debug(f"Error fetching advanced stats for {team_name}: {e}")
                    continue

                record = {
                    "league": league,
                    "season": season,
                    "team": team_name,
                    "team_id": team_id,
                }

                # Flatten: {cat}_{for|against}_{sub_key}_{metric}
                statistics = team_data.get("statistics", {})
                stat_categories = ["situation", "formation", "gameState", "timing", "shotZone", "attackSpeed", "result"]
                for cat in stat_categories:
                    cat_data = statistics.get(cat)
                    if not cat_data:
                        continue
                    for sub_key, sub_val in cat_data.items():
                        if not isinstance(sub_val, dict):
                            continue
                        for metric in ("shots", "goals", "xG", "time"):
                            if metric in sub_val:
                                record[f"{cat}_for_{sub_key}_{metric}"] = _as_float(sub_val[metric])
                        against = sub_val.get("against")
                        if isinstance(against, dict):
                            for metric, val in against.items():
                                record[f"{cat}_against_{sub_key}_{metric}"] = _as_float(val)

                dates = team_data.get("dates")
                if dates:
                    record["forecast_matches"] = len(dates)

                records.append(record)

        index = ["league", "season", "team"]
        if not records:
            return pd.DataFrame()

        return (
            pd.DataFrame.from_records(records)
            .replace({"team": TEAMNAME_REPLACEMENTS})
            .set_index(index)
            .sort_index()
            .convert_dtypes()
        )

    def read_player_career_shots(self, player_id: int) -> dict:
        """Retrieve all career shots for a player via getPlayerData endpoint.

        Parameters
        ----------
        player_id : int
            Understat player ID (from read_player_season_stats).

        Returns
        -------
        dict
            'shots': DataFrame with xG, coords, result per shot.
            'groups': Category breakdowns (situation, shotZone, etc.).
        """
        endpoint = f"{UNDERSTAT_URL}/getPlayerData/{player_id}"
        filepath = self.data_dir / f"player_{player_id}_data.json"
        data = self._fetch_ajax(endpoint, filepath)

        shots_raw = data.get("shots", [])
        shots = []
        for shot in shots_raw:
            is_home = shot.get("h_a") == "h"
            shots.append({
                "match_id": _as_int(shot.get("match_id")),
                "season": _as_int(shot.get("season")),
                "date": shot.get("date"),
                "player_id": player_id,
                "player": _as_str(shot.get("player")),
                "team": _as_str(shot.get("h_team") if is_home else shot.get("a_team")),
                "xg": _as_float(shot.get("xG")),
                "location_x": _as_float(shot.get("X")),
                "location_y": _as_float(shot.get("Y")),
                "minute": _as_int(shot.get("minute")),
                "body_part": SHOT_BODY_PARTS.get(shot.get("shotType"), shot.get("shotType")),
                "situation": SHOT_SITUATIONS.get(shot.get("situation"), shot.get("situation")),
                "result": SHOT_RESULTS.get(shot.get("result"), shot.get("result")),
                "shot_id": _as_int(shot.get("id")),
            })

        shots_df = pd.DataFrame(shots) if shots else pd.DataFrame()

        groups = data.get("groups", {})

        return {"shots": shots_df, "groups": groups}

    def _select_matches(
        self,
        df_schedule: pd.DataFrame,
        match_id: Optional[Union[int, list[int]]] = None,
    ) -> pd.DataFrame:
        """Filter schedule to specific match IDs, or return all if None."""
        if match_id is not None:
            match_ids = [match_id] if isinstance(match_id, int) else match_id
            df = df_schedule[df_schedule["game_id"].isin(match_ids)]
            if df.empty:
                raise ValueError("No matches found with the given IDs in the selected seasons.")
        else:
            df = df_schedule

        return df

    def _fetch_ajax(self, endpoint: str, filepath: Path, no_cache: bool = False) -> dict:
        """Fetch JSON from Understat AJAX endpoint with 30-day file cache."""
        is_cached = self._is_cached(filepath, max_age=30)
        if not no_cache and not self.no_cache and is_cached:
            with filepath.open("rb") as f:
                return json.load(f)

        import time as _time
        import random as _random

        headers = self._get_random_headers()
        headers["X-Requested-With"] = "XMLHttpRequest"

        response = self._session.get(endpoint, headers=headers)
        _time.sleep(self.rate_limit + _random.random() * self.max_delay)
        response.raise_for_status()
        data = response.json()

        if not self.no_store and filepath is not None:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with filepath.open("wb") as fh:
                fh.write(json.dumps(data).encode("utf-8"))

        return data

    def _read_leagues(self, no_cache: bool = False) -> dict:
        """Fetch league metadata from getStatData endpoint."""
        filepath = self.data_dir / "leagues.json"
        data = self._fetch_ajax(f"{UNDERSTAT_URL}/getStatData", filepath, no_cache)
        return {"statData": data["stat"]}

    def _read_league_season(
        self, url: str, league_id: int, season_id: int, no_cache: bool = False
    ) -> dict:
        """Fetch matches, players, and teams for a league-season."""
        league_slug = url.split("/league/")[1].split("/")[0]
        endpoint = f"{UNDERSTAT_URL}/getLeagueData/{league_slug}/{season_id}"
        filepath = self.data_dir / f"league_{league_id}_season_{season_id}.json"
        data = self._fetch_ajax(endpoint, filepath, no_cache)
        return {
            "datesData": data["dates"],
            "playersData": data["players"],
            "teamsData": data["teams"],
        }

    def _read_match(self, url: str, match_id: int) -> Optional[dict]:
        """Fetch match data: info from HTML, rosters+shots from AJAX. Returns None on error."""
        try:
            filepath_html = self.data_dir / f"match_{match_id}_info.json"
            response = self.get(url, filepath_html, var="match_info")
            match_info_wrapper = json.load(response)
            match_info = match_info_wrapper.get("match_info", match_info_wrapper)

            filepath_data = self.data_dir / f"match_{match_id}_data.json"
            ajax_data = self._fetch_ajax(
                f"{UNDERSTAT_URL}/getMatchData/{match_id}", filepath_data
            )

            # Remap rosters from {h/a: ...} to {team_id: ...} for compatibility
            rosters_data = {}
            for side in ("h", "a"):
                team_id = str(match_info[side])
                rosters_data[team_id] = ajax_data["rosters"].get(side, {})

            shots_data = ajax_data["shots"]

            return {
                "match_info": match_info,
                "rostersData": rosters_data,
                "shotsData": shots_data,
            }
        except (ConnectionError, KeyError, json.JSONDecodeError) as e:
            from ._config import logger
            logger.debug(f"Error reading match {match_id}: {e}")
            return None


# --- Safe type conversion helpers (handle None/invalid data) ---

def _as_bool(value: Any) -> Optional[bool]:
    """Convert to bool, returning None on failure."""
    try:
        return bool(value)
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> Optional[float]:
    """Convert to float, returning None on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> Optional[int]:
    """Convert to int, returning None on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_str(value: Any) -> Optional[str]:
    """Convert to string and unescape HTML entities, returning None on failure."""
    try:
        return unescape(value)
    except (TypeError, ValueError):
        return None
