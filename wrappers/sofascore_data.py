"""Wrapper for SofaScore data extraction.

Provides simplified API for getting shot data with xG values from SofaScore.
This is a lightweight wrapper focused on match-level shot data.
"""

from typing import Optional
import pandas as pd
from scrappers.sofascore import SofaScore
from scrappers._config import logger


def extract_shot_events(
    event_id: Optional[int] = None,
    home_team: Optional[str] = None,
    away_team: Optional[str] = None,
    match_date: Optional[str] = None,
    verbose: bool = True
) -> pd.DataFrame:
    """Extract shot events with xG data for a match.

    Args:
        event_id: SofaScore event ID (if known)
        home_team: Home team name (for searching if event_id not provided)
        away_team: Away team name (for searching if event_id not provided)
        match_date: Match date in YYYY-MM-DD format
        verbose: Print extraction info

    Returns:
        DataFrame with shot data including xG, xgot, coordinates, and metadata

    Examples:
        # Direct extraction with event_id
        >>> shots = extract_shot_events(event_id=14924703)

        # Search-based extraction
        >>> shots = extract_shot_events(
        ...     home_team="Inter Miami CF",
        ...     away_team="Vancouver Whitecaps",
        ...     match_date="2024-12-07"
        ... )
    """
    try:
        scraper = SofaScore(no_cache=True)
        shots_df = scraper.read_shot_events(
            event_id=event_id,
            home_team=home_team,
            away_team=away_team,
            match_date=match_date
        )

        if shots_df.empty:
            if verbose:
                logger.warning("No shot data found")
            return pd.DataFrame()

        if verbose:
            total_shots = len(shots_df)
            total_xg = shots_df['xg'].sum()
            logger.info(f"Extracted {total_shots} shots (xG: {total_xg:.2f})")

        return shots_df

    except Exception as e:
        logger.error(f"Error extracting shot events: {e}")
        return pd.DataFrame()


def get_match_xg_summary(
    event_id: Optional[int] = None,
    home_team: Optional[str] = None,
    away_team: Optional[str] = None,
    match_date: Optional[str] = None
) -> dict:
    """Get xG summary for a match.

    Args:
        event_id: SofaScore event ID
        home_team: Home team name
        away_team: Away team name
        match_date: Match date in YYYY-MM-DD format

    Returns:
        Dictionary with xG statistics by team

    Examples:
        >>> summary = get_match_xg_summary(event_id=14924703)
        >>> print(f"Home xG: {summary['home']['xg']:.2f}")
    """
    shots_df = extract_shot_events(
        event_id=event_id,
        home_team=home_team,
        away_team=away_team,
        match_date=match_date,
        verbose=False
    )

    if shots_df.empty:
        return {}

    summary = {}
    for is_home in [True, False]:
        team_shots = shots_df[shots_df['is_home'] == is_home]
        if not team_shots.empty:
            team_name = team_shots.iloc[0]['team']
            summary['home' if is_home else 'away'] = {
                'team': team_name,
                'shots': len(team_shots),
                'xg': float(team_shots['xg'].sum()),
                'xgot': float(team_shots['xgot'].sum()),
                'goals': len(team_shots[team_shots['result'] == 'Goal'])
            }

    return summary
