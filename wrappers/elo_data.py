"""ELO ratings data wrapper.

Simplified API for national team ELO rankings, historical match results,
and head-to-head records. Wraps scrappers.elo.EloRatings.
"""

from typing import Dict, List, Optional, Tuple

import pandas as pd

from scrappers.elo import EloRatings
from scrappers._config import logger


def get_rankings(year: Optional[int] = None) -> pd.DataFrame:
    """Fetch ELO rankings for all national teams.

    Args:
        year: Year to fetch (default: current year).

    Returns:
        DataFrame indexed by team name with elo_* columns (33 metrics).
    """
    elo = EloRatings()
    return elo.read_rankings(year=year)


def get_latest_matches() -> pd.DataFrame:
    """Fetch recent international match results.

    Returns:
        DataFrame with one row per match (date, teams, scores, ELO, tournament).
    """
    elo = EloRatings()
    return elo.read_latest_matches()


def get_matches_for_year(year: int) -> pd.DataFrame:
    """Fetch international match results for a specific year.

    Args:
        year: Year to fetch (e.g. 2022).

    Returns:
        DataFrame with one row per match, same format as get_latest_matches().
    """
    elo = EloRatings()
    return elo.read_matches_for_year(year)


def get_matches_range(start_year: int, end_year: int) -> pd.DataFrame:
    """Fetch match results across multiple years.

    Args:
        start_year: First year (inclusive).
        end_year: Last year (inclusive).

    Returns:
        Combined DataFrame sorted by date descending, deduplicated.
    """
    elo = EloRatings()
    return elo.read_matches_range(start_year, end_year)


def get_h2h(
    team_a: str,
    team_b: str,
    matches_df: Optional[pd.DataFrame] = None,
    start_year: int = 2014,
) -> Dict:
    """Compute head-to-head record between two national teams.

    Args:
        team_a: First team name (e.g. "Brazil").
        team_b: Second team name (e.g. "Argentina").
        matches_df: Pre-loaded matches DataFrame. If None, fetches from start_year to now.
        start_year: Start year if matches_df not provided.

    Returns:
        Dict with h2h stats: matches, wins_a, wins_b, draws, goals_a, goals_b,
        avg_goal_diff, last_result, last_date.
    """
    if matches_df is None:
        from datetime import datetime
        current_year = datetime.now().year
        matches_df = get_matches_range(start_year, current_year)

    if matches_df.empty:
        return _empty_h2h()

    a_lower = team_a.lower()
    b_lower = team_b.lower()

    # Filter matches where both teams played
    mask = (
        (matches_df["team1"].str.lower() == a_lower) & (matches_df["team2"].str.lower() == b_lower)
    ) | (
        (matches_df["team1"].str.lower() == b_lower) & (matches_df["team2"].str.lower() == a_lower)
    )
    h2h = matches_df[mask].copy()

    if h2h.empty:
        return _empty_h2h()

    wins_a, wins_b, draws = 0, 0, 0
    goals_a, goals_b = 0, 0

    for _, row in h2h.iterrows():
        if row["team1"].lower() == a_lower:
            ga, gb = row["team1_score"], row["team2_score"]
        else:
            ga, gb = row["team2_score"], row["team1_score"]
        goals_a += ga
        goals_b += gb
        if ga > gb:
            wins_a += 1
        elif gb > ga:
            wins_b += 1
        else:
            draws += 1

    n = len(h2h)
    last_row = h2h.iloc[0]  # Already sorted by date desc
    if last_row["team1"].lower() == a_lower:
        last_ga, last_gb = last_row["team1_score"], last_row["team2_score"]
    else:
        last_ga, last_gb = last_row["team2_score"], last_row["team1_score"]

    if last_ga > last_gb:
        last_result = "W"
    elif last_gb > last_ga:
        last_result = "L"
    else:
        last_result = "D"

    return {
        "matches": n,
        "wins_a": wins_a,
        "wins_b": wins_b,
        "draws": draws,
        "goals_a": goals_a,
        "goals_b": goals_b,
        "avg_goal_diff": (goals_a - goals_b) / n,
        "win_pct_a": wins_a / n,
        "last_result": last_result,
        "last_date": last_row.get("date"),
    }


def get_team_rating(team_name: str, year: Optional[int] = None) -> Optional[Dict]:
    """Fetch a single team's ELO data.

    Args:
        team_name: Team name (e.g. "Spain").
        year: Year (default: current).

    Returns:
        Dict with all elo_* fields, or None if not found.
    """
    df = get_rankings(year=year)
    if df.empty:
        return None
    matches = df.index.str.lower() == team_name.lower()
    if not matches.any():
        logger.debug("Team not found in ELO rankings: %s", team_name)
        return None
    row = df[matches].iloc[0]
    return row.to_dict()


def _empty_h2h() -> Dict:
    """Return empty head-to-head record."""
    return {
        "matches": 0,
        "wins_a": 0,
        "wins_b": 0,
        "draws": 0,
        "goals_a": 0,
        "goals_b": 0,
        "avg_goal_diff": 0.0,
        "win_pct_a": 0.0,
        "last_result": None,
        "last_date": None,
    }
