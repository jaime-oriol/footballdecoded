"""Historical data collection for model training.

Collects international match results from ELO ratings source and organizes
them for Dixon-Coles training and backtesting.
"""

import logging
from typing import Dict, List, Optional, Tuple

import pandas as pd

from ._config import BACKTEST_TOURNAMENTS

logger = logging.getLogger(__name__)


def collect_historical_matches(
    start_year: int = 2014,
    end_year: int = 2026,
) -> pd.DataFrame:
    """Collect international match results across multiple years.

    Parameters
    ----------
    start_year : int
        First year (inclusive).
    end_year : int
        Last year (inclusive).

    Returns
    -------
    pd.DataFrame
        Combined match results sorted by date.
    """
    from wrappers.elo_data import get_matches_range
    return get_matches_range(start_year, end_year)


def collect_rankings_by_year(
    start_year: int = 2014,
    end_year: int = 2026,
) -> Dict[int, pd.DataFrame]:
    """Collect ELO rankings for each year.

    Parameters
    ----------
    start_year, end_year : int
        Year range.

    Returns
    -------
    Dict mapping year -> rankings DataFrame.
    """
    from wrappers.elo_data import get_rankings

    rankings = {}
    for year in range(start_year, end_year + 1):
        try:
            df = get_rankings(year=year)
            if not df.empty:
                rankings[year] = df
                logger.debug("Rankings for %d: %d teams", year, len(df))
        except Exception as e:
            logger.warning("Could not fetch rankings for %d: %s", year, e)

    logger.info("Collected rankings for %d years", len(rankings))
    return rankings


def filter_tournament_matches(
    matches_df: pd.DataFrame,
    tournament_name: str,
    year: int,
) -> pd.DataFrame:
    """Filter matches for a specific tournament and year.

    Parameters
    ----------
    matches_df : pd.DataFrame
        All matches with 'tournament' and 'date' columns.
    tournament_name : str
        Tournament name substring to match (e.g. "World Cup", "European").
    year : int
        Year of the tournament.

    Returns
    -------
    pd.DataFrame
        Filtered matches.
    """
    if matches_df.empty:
        return pd.DataFrame()

    mask = pd.Series(True, index=matches_df.index)

    if "tournament" in matches_df.columns:
        mask &= matches_df["tournament"].str.contains(tournament_name, case=False, na=False)

    if "date" in matches_df.columns:
        dates = pd.to_datetime(matches_df["date"], errors="coerce")
        mask &= dates.dt.year == year
    elif "year" in matches_df.columns:
        mask &= matches_df["year"] == year

    filtered = matches_df[mask].copy()
    logger.info("Filtered %d matches for %s %d", len(filtered), tournament_name, year)
    return filtered


def split_train_test(
    matches_df: pd.DataFrame,
    cutoff_date: str,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Split matches into train/test by date.

    Parameters
    ----------
    matches_df : pd.DataFrame
        All matches with 'date' column.
    cutoff_date : str
        ISO date string (e.g. "2022-01-01"). Matches before this go to train.

    Returns
    -------
    Tuple of (train_df, test_df).
    """
    dates = pd.to_datetime(matches_df["date"], errors="coerce")
    cutoff = pd.to_datetime(cutoff_date)

    train = matches_df[dates < cutoff].copy()
    test = matches_df[dates >= cutoff].copy()

    logger.info("Train/test split at %s: %d train, %d test", cutoff_date, len(train), len(test))
    return train, test


def prepare_backtest_data(
    matches_df: pd.DataFrame,
    rankings_by_year: Dict[int, pd.DataFrame],
) -> List[Dict]:
    """Prepare backtest folds for temporal cross-validation.

    Folds:
        1. Train before 2018, test on WC 2018
        2. Train before 2022, test on WC 2022
        3. Train before 2024, test on Euro 2024

    Parameters
    ----------
    matches_df : pd.DataFrame
        All historical matches.
    rankings_by_year : dict
        Rankings per year.

    Returns
    -------
    List of fold dicts with keys: name, train_df, test_df, rankings_df.
    """
    folds = []

    fold_configs = [
        {"name": "WC 2018", "cutoff": "2018-06-01", "tournament": "World Cup", "year": 2018},
        {"name": "WC 2022", "cutoff": "2022-11-01", "tournament": "World Cup", "year": 2022},
        {"name": "Euro 2024", "cutoff": "2024-06-01", "tournament": "European", "year": 2024},
    ]

    for cfg in fold_configs:
        train_df, _ = split_train_test(matches_df, cfg["cutoff"])
        test_df = filter_tournament_matches(matches_df, cfg["tournament"], cfg["year"])

        if test_df.empty:
            logger.warning("No test matches found for %s", cfg["name"])
            continue

        # Use rankings from the tournament year
        rankings = rankings_by_year.get(cfg["year"])
        if rankings is None:
            nearest = min(rankings_by_year.keys(), key=lambda y: abs(y - cfg["year"]))
            rankings = rankings_by_year[nearest]

        folds.append({
            "name": cfg["name"],
            "train_df": train_df,
            "test_df": test_df,
            "rankings_df": rankings,
        })

    logger.info("Prepared %d backtest folds", len(folds))
    return folds
