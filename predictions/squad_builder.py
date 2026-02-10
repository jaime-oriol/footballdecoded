"""National team squad construction from club-level data.

Aggregates FotMob player stats + Transfermarkt profiles into 14 team-level
features representing squad strength. Uses nationality from Transfermarkt
to map club players to national teams.
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ._config import (
    MIN_MINUTES,
    POSITION_TO_CATEGORY,
    POSITIONS,
    QUALIFIED_TEAMS,
    SQUAD_SIZE,
)

logger = logging.getLogger(__name__)

# Big 5 league codes for squad_big_league_pct calculation
BIG_5_LEAGUES = {
    "ENG-Premier League",
    "ESP-La Liga",
    "ITA-Serie A",
    "GER-Bundesliga",
    "FRA-Ligue 1",
}



def build_squad(
    nationality: str,
    players_df: pd.DataFrame,
    season: str,
) -> pd.DataFrame:
    """Build a projected 26-man squad for a national team.

    Parameters
    ----------
    nationality : str
        Country name (e.g. "Spain", "Argentina") matching Transfermarkt nationality.
    players_df : pd.DataFrame
        All players from the database/wrappers with at minimum:
        - transfermarkt_nationality (str)
        - transfermarkt_position_specific (str)
        - fotmob_mins_played (numeric)
        - fotmob_rating (numeric)
    season : str
        Season code (e.g. "25-26").

    Returns
    -------
    pd.DataFrame
        Selected 26-man squad with all available metrics.
    """
    nat_lower = nationality.lower()

    # Filter by nationality
    if "transfermarkt_nationality" in players_df.columns:
        mask = players_df["transfermarkt_nationality"].str.lower().fillna("") == nat_lower
    elif "nationality" in players_df.columns:
        mask = players_df["nationality"].str.lower().fillna("") == nat_lower
    else:
        logger.error("No nationality column found in players_df")
        return pd.DataFrame()

    pool = players_df[mask].copy()
    if pool.empty:
        logger.warning("No players found for nationality: %s", nationality)
        return pd.DataFrame()

    # Filter by minimum minutes
    mins_col = _find_col(pool, ["fotmob_mins_played", "mins_played"])
    if mins_col:
        pool = pool[pool[mins_col].fillna(0) >= MIN_MINUTES].copy()

    if pool.empty:
        logger.warning("No players with %d+ minutes for %s", MIN_MINUTES, nationality)
        return pd.DataFrame()

    # Map positions to categories
    pos_col = _find_col(pool, ["transfermarkt_position_specific", "position"])
    if pos_col:
        pool["_category"] = pool[pos_col].map(POSITION_TO_CATEGORY).fillna("MID")
    else:
        pool["_category"] = "MID"

    # Sort by rating within each category, select top N per position
    rating_col = _find_col(pool, ["fotmob_rating", "rating"])
    if rating_col:
        pool = pool.sort_values(rating_col, ascending=False)

    selected = []
    for cat, count in POSITIONS.items():
        cat_pool = pool[pool["_category"] == cat]
        selected.append(cat_pool.head(count))

    squad = pd.concat(selected, ignore_index=True)

    # If under 26, fill with best remaining players
    if len(squad) < SQUAD_SIZE:
        remaining = pool[~pool.index.isin(squad.index)]
        if rating_col:
            remaining = remaining.sort_values(rating_col, ascending=False)
        extra = remaining.head(SQUAD_SIZE - len(squad))
        squad = pd.concat([squad, extra], ignore_index=True)

    logger.info("Squad built for %s: %d players", nationality, len(squad))
    return squad


def aggregate_squad_features(
    squad_df: pd.DataFrame,
    nationality: str,
) -> Dict[str, float]:
    """Aggregate individual player stats into 14 team-level features.

    Parameters
    ----------
    squad_df : pd.DataFrame
        Output of build_squad().
    nationality : str
        Country name (for logging).

    Returns
    -------
    Dict with 14 squad_* features.
    """
    if squad_df.empty:
        return _empty_squad_features()

    features = {}

    # Helper: safe mean/sum/median
    def _safe_mean(col_names, mask=None):
        col = _find_col(squad_df, col_names)
        if col is None:
            return 0.0
        s = squad_df[col] if mask is None else squad_df.loc[mask, col]
        vals = pd.to_numeric(s, errors="coerce").dropna()
        return float(vals.mean()) if len(vals) > 0 else 0.0

    def _safe_sum(col_names, mask=None):
        col = _find_col(squad_df, col_names)
        if col is None:
            return 0.0
        s = squad_df[col] if mask is None else squad_df.loc[mask, col]
        vals = pd.to_numeric(s, errors="coerce").dropna()
        return float(vals.sum()) if len(vals) > 0 else 0.0

    def _safe_median(col_names, mask=None):
        col = _find_col(squad_df, col_names)
        if col is None:
            return 0.0
        s = squad_df[col] if mask is None else squad_df.loc[mask, col]
        vals = pd.to_numeric(s, errors="coerce").dropna()
        return float(vals.median()) if len(vals) > 0 else 0.0

    def _safe_std(col_names, mask=None):
        col = _find_col(squad_df, col_names)
        if col is None:
            return 0.0
        s = squad_df[col] if mask is None else squad_df.loc[mask, col]
        vals = pd.to_numeric(s, errors="coerce").dropna()
        return float(vals.std()) if len(vals) > 1 else 0.0

    # Position masks
    cat_col = "_category" if "_category" in squad_df.columns else None
    if cat_col:
        is_gk = squad_df[cat_col] == "GK"
        is_def = squad_df[cat_col].isin(["DEF", "MID"])
        is_att = squad_df[cat_col].isin(["FWD", "MID"])
    else:
        is_gk = pd.Series(False, index=squad_df.index)
        is_def = pd.Series(True, index=squad_df.index)
        is_att = pd.Series(True, index=squad_df.index)

    # 1. Squad average rating (weighted by minutes)
    rating_col = _find_col(squad_df, ["fotmob_rating", "rating"])
    mins_col = _find_col(squad_df, ["fotmob_mins_played", "mins_played"])
    if rating_col and mins_col:
        ratings = pd.to_numeric(squad_df[rating_col], errors="coerce").fillna(0)
        mins = pd.to_numeric(squad_df[mins_col], errors="coerce").fillna(0)
        total_mins = mins.sum()
        features["squad_avg_rating"] = float((ratings * mins).sum() / total_mins) if total_mins > 0 else 0.0
    else:
        features["squad_avg_rating"] = _safe_mean(["fotmob_rating", "rating"])

    # 2-3. Attack: xG and xA per 90 (top attackers)
    features["squad_attack_xg"] = _safe_mean(
        ["fotmob_expected_goals_per_90", "fotmob_expected_goals"], mask=is_att
    )
    features["squad_attack_xa"] = _safe_mean(
        ["fotmob_expected_assists_per_90", "fotmob_expected_assists"], mask=is_att
    )

    # 4-5. Defense: tackles and interceptions
    features["squad_defense_tackles"] = _safe_mean(
        ["fotmob_total_tackle"], mask=is_def
    )
    features["squad_defense_interceptions"] = _safe_mean(
        ["fotmob_interception"], mask=is_def
    )

    # 6-7. Goalkeeping
    features["squad_gk_saves"] = _safe_mean(["fotmob_saves"], mask=is_gk)
    features["squad_gk_clean_sheet"] = _safe_mean(["fotmob_clean_sheet"], mask=is_gk)

    # 8-9. Market value
    features["squad_total_market_value"] = _safe_sum(
        ["transfermarkt_market_value_eur"]
    )
    features["squad_median_market_value"] = _safe_median(
        ["transfermarkt_market_value_eur"]
    )

    # 10. Top 5 star power
    if rating_col:
        top5 = pd.to_numeric(squad_df[rating_col], errors="coerce").nlargest(5)
        features["squad_top5_rating"] = float(top5.mean()) if len(top5) > 0 else 0.0
    else:
        features["squad_top5_rating"] = 0.0

    # 11. Big league exposure
    if "league" in squad_df.columns:
        n_big5 = squad_df["league"].isin(BIG_5_LEAGUES).sum()
        features["squad_big_league_pct"] = n_big5 / max(len(squad_df), 1)
    else:
        features["squad_big_league_pct"] = 0.0

    # 12. Average age
    if "age" in squad_df.columns:
        ages = pd.to_numeric(squad_df["age"], errors="coerce").dropna()
        features["squad_avg_age"] = float(ages.mean()) if len(ages) > 0 else 0.0
    else:
        features["squad_avg_age"] = 0.0

    # 13. Squad depth (rating std)
    features["squad_depth_rating_std"] = _safe_std(["fotmob_rating", "rating"])

    # 14. Pass accuracy
    features["squad_avg_pass_accuracy"] = _safe_mean(["fotmob_accurate_pass"])

    logger.debug("Squad features for %s: %s", nationality, features)
    return features


def build_all_squads(
    players_df: pd.DataFrame,
    season: str,
    teams: Optional[Dict[str, Dict]] = None,
) -> Dict[str, Dict[str, float]]:
    """Build squad features for all qualified teams.

    Parameters
    ----------
    players_df : pd.DataFrame
        All players across all leagues.
    season : str
        Season code.
    teams : dict, optional
        Team config dict (default: QUALIFIED_TEAMS from _config).

    Returns
    -------
    Dict mapping team name -> squad features dict.
    """
    if teams is None:
        teams = QUALIFIED_TEAMS

    all_features = {}
    for team_name in teams:
        squad = build_squad(team_name, players_df, season)
        all_features[team_name] = aggregate_squad_features(squad, team_name)

    logger.info("Squad features built for %d teams", len(all_features))
    return all_features


def _find_col(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """Return first column name from candidates that exists in df."""
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _empty_squad_features() -> Dict[str, float]:
    """Return zeroed squad features dict."""
    return {
        "squad_avg_rating": 0.0,
        "squad_attack_xg": 0.0,
        "squad_attack_xa": 0.0,
        "squad_defense_tackles": 0.0,
        "squad_defense_interceptions": 0.0,
        "squad_gk_saves": 0.0,
        "squad_gk_clean_sheet": 0.0,
        "squad_total_market_value": 0.0,
        "squad_median_market_value": 0.0,
        "squad_top5_rating": 0.0,
        "squad_big_league_pct": 0.0,
        "squad_avg_age": 0.0,
        "squad_depth_rating_std": 0.0,
        "squad_avg_pass_accuracy": 0.0,
    }
