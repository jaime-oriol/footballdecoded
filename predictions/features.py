"""Feature engineering pipeline for match prediction.

Builds feature vectors from ELO ratings, squad strength, and match context.
All features are computed as team_a vs team_b pairs (symmetric: a is always
the "first" team as listed in the fixture).
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ._config import (
    ALL_FEATURES,
    CONTEXT_FEATURES,
    ELO_FEATURES,
    HOST_COUNTRIES,
    QUALIFIED_TEAMS,
    SQUAD_FEATURES,
)

logger = logging.getLogger(__name__)


def build_elo_features(
    team_a: str,
    team_b: str,
    rankings_df: pd.DataFrame,
) -> Dict[str, float]:
    """Build ELO-based features for a match.

    Parameters
    ----------
    team_a, team_b : str
        Team names matching ELO rankings index.
    rankings_df : pd.DataFrame
        Output of elo_data.get_rankings(), indexed by team name.

    Returns
    -------
    Dict with elo_* feature values.
    """
    feat = {}

    ra = _get_team_elo(team_a, rankings_df)
    rb = _get_team_elo(team_b, rankings_df)

    # Direct ratings and difference (1500 = neutral ELO for unknown teams)
    feat["elo_rating_diff"] = ra.get("elo_rating", 1500) - rb.get("elo_rating", 1500)
    feat["elo_rating_avg_diff"] = ra.get("elo_rating_average", 1500) - rb.get("elo_rating_average", 1500)

    # Per-team form features
    for suffix, data in [("a", ra), ("b", rb)]:
        feat[f"elo_rating_3m_chg_{suffix}"] = data.get("elo_rating_3m_chg", 0)
        feat[f"elo_rating_6m_chg_{suffix}"] = data.get("elo_rating_6m_chg", 0)
        feat[f"elo_rating_1y_chg_{suffix}"] = data.get("elo_rating_1y_chg", 0)

        total = data.get("elo_total_matches", 0)
        wins = data.get("elo_wins", 0)
        gf = data.get("elo_goals_for", 0)

        feat[f"elo_win_pct_{suffix}"] = wins / total if total > 0 else 0.0
        feat[f"elo_goals_per_match_{suffix}"] = gf / total if total > 0 else 0.0

        chg_3m = data.get("elo_rating_3m_chg", 0)
        chg_1y = data.get("elo_rating_1y_chg", 0)
        feat[f"elo_form_momentum_{suffix}"] = chg_3m - chg_1y

    return feat


def build_squad_features_pair(
    team_a: str,
    team_b: str,
    squad_features: Dict[str, Dict[str, float]],
) -> Dict[str, float]:
    """Build squad strength features for both teams.

    Parameters
    ----------
    team_a, team_b : str
        Team names.
    squad_features : dict
        Output of squad_builder.build_all_squads().

    Returns
    -------
    Dict with squad_*_a and squad_*_b features.
    """
    feat = {}
    sa = squad_features.get(team_a, {})
    sb = squad_features.get(team_b, {})

    for key in [
        "squad_avg_rating", "squad_attack_xg", "squad_attack_xa",
        "squad_defense_tackles", "squad_defense_interceptions",
        "squad_gk_saves", "squad_gk_clean_sheet",
        "squad_total_market_value", "squad_median_market_value",
        "squad_top5_rating", "squad_big_league_pct",
        "squad_avg_age", "squad_depth_rating_std", "squad_avg_pass_accuracy",
    ]:
        feat[f"{key}_a"] = sa.get(key, 0.0)
        feat[f"{key}_b"] = sb.get(key, 0.0)

    return feat


def build_context_features(
    team_a: str,
    team_b: str,
    stage: int = 0,
    rest_days_a: int = 3,
    rest_days_b: int = 3,
    group_match_number: int = 0,
    must_win_a: bool = False,
    must_win_b: bool = False,
    h2h_record: Optional[Dict] = None,
) -> Dict[str, float]:
    """Build match context features.

    Parameters
    ----------
    stage : int
        0=group, 1=R32, 2=R16, 3=QF, 4=SF, 5=Final.
    rest_days_a, rest_days_b : int
        Days since last match.
    group_match_number : int
        1, 2, or 3 for group stage; 0 for knockout.
    must_win_a, must_win_b : bool
        Whether team must win to advance.
    h2h_record : dict
        Output of elo_data.get_h2h().

    Returns
    -------
    Dict with context feature values.
    """
    feat = {}

    feat["tournament_stage"] = stage
    feat["is_host_a"] = 1.0 if team_a in HOST_COUNTRIES else 0.0
    feat["is_host_b"] = 1.0 if team_b in HOST_COUNTRIES else 0.0
    feat["rest_days_a"] = rest_days_a
    feat["rest_days_b"] = rest_days_b
    feat["group_match_number"] = group_match_number
    feat["must_win_a"] = 1.0 if must_win_a else 0.0
    feat["must_win_b"] = 1.0 if must_win_b else 0.0

    if h2h_record:
        feat["h2h_win_pct"] = h2h_record.get("win_pct_a", 0.0)
        feat["h2h_goal_diff"] = h2h_record.get("avg_goal_diff", 0.0)
        feat["h2h_matches"] = h2h_record.get("matches", 0)
    else:
        feat["h2h_win_pct"] = 0.0
        feat["h2h_goal_diff"] = 0.0
        feat["h2h_matches"] = 0

    return feat


def build_match_features(
    team_a: str,
    team_b: str,
    rankings_df: pd.DataFrame,
    squad_features: Dict[str, Dict[str, float]],
    h2h_record: Optional[Dict] = None,
    stage: int = 0,
    rest_days_a: int = 3,
    rest_days_b: int = 3,
    group_match_number: int = 0,
    must_win_a: bool = False,
    must_win_b: bool = False,
) -> Dict[str, float]:
    """Build complete feature vector for a single match.

    Combines ELO + squad + context features into a single dict.

    Parameters
    ----------
    team_a, team_b : str
        Team names.
    rankings_df : pd.DataFrame
        ELO rankings.
    squad_features : dict
        Squad strength features for all teams.
    h2h_record : dict, optional
        Head-to-head record.
    stage, rest_days_a, rest_days_b, group_match_number, must_win_a, must_win_b:
        Context parameters.

    Returns
    -------
    Dict with all feature values (ELO + squad + context).
    """
    feat = {}
    feat.update(build_elo_features(team_a, team_b, rankings_df))
    feat.update(build_squad_features_pair(team_a, team_b, squad_features))
    feat.update(build_context_features(
        team_a, team_b,
        stage=stage,
        rest_days_a=rest_days_a,
        rest_days_b=rest_days_b,
        group_match_number=group_match_number,
        must_win_a=must_win_a,
        must_win_b=must_win_b,
        h2h_record=h2h_record,
    ))
    return feat


def build_training_matrix(
    matches_df: pd.DataFrame,
    rankings_by_year: Dict[int, pd.DataFrame],
    squad_features_by_year: Optional[Dict[int, Dict[str, Dict[str, float]]]] = None,
) -> Tuple[pd.DataFrame, pd.Series]:
    """Build feature matrix X and target y from historical matches.

    Parameters
    ----------
    matches_df : pd.DataFrame
        Historical match results with: team1, team2, team1_score, team2_score, date.
    rankings_by_year : dict
        {year: rankings_df} for ELO features at time of match.
    squad_features_by_year : dict, optional
        {year: squad_features_dict} for squad features. If None, squad features
        are set to 0 (ELO-only mode).

    Returns
    -------
    X : pd.DataFrame
        Feature matrix with ALL_FEATURES columns.
    y : pd.Series
        Target: 2=team1 win, 1=draw, 0=team2 win.
    """
    rows = []
    targets = []

    empty_squad = {}

    for _, match in matches_df.iterrows():
        team_a = match["team1"]
        team_b = match["team2"]
        score_a = int(match["team1_score"])
        score_b = int(match["team2_score"])

        # Determine year for feature lookup
        if "date" in match and pd.notna(match.get("date")):
            year = pd.to_datetime(match["date"]).year
        elif "year" in match:
            year = int(match["year"])
        else:
            continue

        # Get rankings for that year (fallback to nearest available)
        rankings = _get_nearest_rankings(year, rankings_by_year)
        if rankings is None:
            continue

        # Get squad features for that year
        if squad_features_by_year:
            squad = squad_features_by_year.get(year, empty_squad)
        else:
            squad = empty_squad

        feat = build_match_features(
            team_a, team_b,
            rankings_df=rankings,
            squad_features=squad,
            stage=0,
        )
        rows.append(feat)

        # Target: 2=win_a, 1=draw, 0=win_b
        if score_a > score_b:
            targets.append(2)
        elif score_a == score_b:
            targets.append(1)
        else:
            targets.append(0)

    X = pd.DataFrame(rows)
    y = pd.Series(targets, name="result")

    # Ensure all expected columns exist (fill missing with 0)
    for col in ALL_FEATURES:
        if col not in X.columns:
            X[col] = 0.0

    X = X[ALL_FEATURES].fillna(0.0)

    logger.info("Training matrix built: %d matches, %d features", len(X), len(ALL_FEATURES))
    return X, y


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _get_team_elo(team_name: str, rankings_df: pd.DataFrame) -> Dict:
    """Get ELO data for a team, with case-insensitive fallback."""
    if rankings_df.empty:
        return {}
    # Exact match
    if team_name in rankings_df.index:
        return rankings_df.loc[team_name].to_dict()
    # Case-insensitive
    lower_idx = rankings_df.index.str.lower()
    mask = lower_idx == team_name.lower()
    if mask.any():
        return rankings_df[mask].iloc[0].to_dict()
    return {}


def _get_nearest_rankings(
    year: int,
    rankings_by_year: Dict[int, pd.DataFrame],
) -> Optional[pd.DataFrame]:
    """Get rankings for exact year, or nearest available."""
    if year in rankings_by_year:
        return rankings_by_year[year]
    if not rankings_by_year:
        return None
    nearest = min(rankings_by_year.keys(), key=lambda y: abs(y - year))
    return rankings_by_year[nearest]
