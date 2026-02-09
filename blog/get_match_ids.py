#!/usr/bin/env python3
"""
Match ID extractor for WhoScored and Understat.

Extracts match IDs for a given team from WhoScored and Understat,
then merges them by date into a single DataFrame. Useful for feeding
IDs into viz/match_data.py and viz/match_data_v2.py pipelines.

Usage:
    from get_match_ids import get_match_ids

    ids = get_match_ids("Atletico Madrid", "ESP-La Liga", "24-25")
    ids.to_csv("atm_matches_24-25.csv", index=False)
"""

import sys
import os
import pandas as pd
import warnings

# Allow imports from project root when running standalone
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scrappers import WhoScored, Understat
from scrappers._config import LEAGUE_DICT

warnings.filterwarnings('ignore')


def _normalize_team_name(team_name: str) -> list[str]:
    """Return name variations for fuzzy team matching (accents, aliases)."""
    variations = [team_name]

    clean_name = (team_name.replace('é', 'e').replace('ñ', 'n').replace('í', 'i')
                  .replace('ó', 'o').replace('á', 'a').replace('ú', 'u'))
    if clean_name != team_name:
        variations.append(clean_name)

    # Teams whose names differ between WhoScored and Understat
    common_mappings = {
        'Atlético Madrid': ['Atletico Madrid', 'Atlético', 'Atletico', 'ATM'],
        'Athletic Club': ['Athletic Bilbao', 'Athletic'],
        'Real Madrid': ['Madrid', 'Real'],
        'Barcelona': ['Barça', 'FC Barcelona', 'Barca'],
        'Manchester United': ['Man United', 'Manchester Utd'],
        'Manchester City': ['Man City'],
        'Tottenham': ['Tottenham Hotspur', 'Spurs'],
        'Inter Miami': ['Inter Miami CF', 'Miami', 'Inter Miami C.F.'],
    }

    for key, values in common_mappings.items():
        if team_name in [key] + values:
            variations.extend([key] + values)

    return list(dict.fromkeys(variations))  # deduplicate, preserve order


def _filter_team_matches(schedule: pd.DataFrame, team_name: str) -> pd.DataFrame:
    """Filter schedule to matches where team appears as home or away."""
    if schedule.empty:
        return schedule

    variations = _normalize_team_name(team_name)
    mask = pd.Series([False] * len(schedule))

    for variation in variations:
        if 'home_team' in schedule.columns:
            mask |= schedule['home_team'].str.contains(variation, case=False, na=False, regex=False)
        if 'away_team' in schedule.columns:
            mask |= schedule['away_team'].str.contains(variation, case=False, na=False, regex=False)

    return schedule[mask].copy()


def get_match_ids(
    team_name: str,
    league: str,
    season: str,
    verbose: bool = True
) -> pd.DataFrame:
    """Extract match IDs from WhoScored and Understat for a team.

    Args:
        team_name: Team name (e.g., "Atletico Madrid", "Barcelona").
        league: League code (e.g., "ESP-La Liga", "ENG-Premier League").
        season: Season in YY-YY format (e.g., "24-25", "23-24").
        verbose: Print progress info.

    Returns:
        DataFrame with columns: date, home_team, away_team,
        whoscored_id, understat_id, league, season.

    Raises:
        ValueError: If league is not found in LEAGUE_DICT.
    """

    if league not in LEAGUE_DICT:
        raise ValueError(f"League '{league}' not found in LEAGUE_DICT")

    if verbose:
        print(f"\nExtracting match IDs for: {team_name} | {league} | {season}\n")

    whoscored_matches = pd.DataFrame()
    understat_matches = pd.DataFrame()

    if 'WhoScored' in LEAGUE_DICT[league]:
        try:
            if verbose:
                print("Extracting from WhoScored...")

            ws = WhoScored(leagues=[league], seasons=[season])
            ws_schedule = ws.read_schedule()

            if not ws_schedule.empty:
                ws_schedule_reset = ws_schedule.reset_index()
                whoscored_matches = _filter_team_matches(ws_schedule_reset, team_name)

                if not whoscored_matches.empty:
                    whoscored_matches = whoscored_matches[['date', 'home_team', 'away_team', 'game_id']].copy()
                    whoscored_matches = whoscored_matches.rename(columns={'game_id': 'whoscored_id'})
                    whoscored_matches['date'] = pd.to_datetime(whoscored_matches['date']).dt.tz_localize(None)

                    if verbose:
                        print(f"  Found {len(whoscored_matches)} matches in WhoScored")
                else:
                    if verbose:
                        print(f"  WARN: No matches for '{team_name}' in WhoScored")
        except Exception as e:
            if verbose:
                print(f"  ERROR extracting from WhoScored: {e}")
    else:
        if verbose:
            print(f"  League '{league}' not available in WhoScored")

    if 'Understat' in LEAGUE_DICT[league]:
        try:
            if verbose:
                print("Extracting from Understat...")

            us = Understat(leagues=[league], seasons=[season])
            us_schedule = us.read_schedule()

            if not us_schedule.empty:
                us_schedule_reset = us_schedule.reset_index()
                understat_matches = _filter_team_matches(us_schedule_reset, team_name)

                if not understat_matches.empty:
                    understat_matches = understat_matches[['date', 'home_team', 'away_team', 'game_id']].copy()
                    understat_matches = understat_matches.rename(columns={'game_id': 'understat_id'})
                    understat_matches['date'] = pd.to_datetime(understat_matches['date']).dt.tz_localize(None)

                    if verbose:
                        print(f"  Found {len(understat_matches)} matches in Understat")
                else:
                    if verbose:
                        print(f"  WARN: No matches for '{team_name}' in Understat")
        except Exception as e:
            if verbose:
                print(f"  ERROR extracting from Understat: {e}")
    else:
        if verbose:
            print(f"  League '{league}' not available in Understat")

    # Outer join keeps matches found by either source
    if not whoscored_matches.empty and not understat_matches.empty:
        merged = pd.merge(
            whoscored_matches,
            understat_matches[['date', 'understat_id']],
            on='date',
            how='outer'
        )
    elif not whoscored_matches.empty:
        merged = whoscored_matches.copy()
        merged['understat_id'] = None
    elif not understat_matches.empty:
        merged = understat_matches.copy()
        merged['whoscored_id'] = None
    else:
        if verbose:
            print("\nNo matches found in any source")
        return pd.DataFrame(columns=['date', 'home_team', 'away_team', 'whoscored_id', 'understat_id', 'league', 'season'])

    merged['league'] = league
    merged['season'] = season

    merged = merged.sort_values('date').reset_index(drop=True)

    if verbose:
        ws_count = merged['whoscored_id'].notna().sum()
        us_count = merged['understat_id'].notna().sum()
        both_count = (merged['whoscored_id'].notna() & merged['understat_id'].notna()).sum()
        print(f"\nSummary: {len(merged)} matches "
              f"(WhoScored: {ws_count}, Understat: {us_count}, both: {both_count})\n")

    return merged


def main():
    """Run usage examples for Atletico Madrid and Barcelona."""

    print("\nMATCH ID EXTRACTOR - WhoScored & Understat\n")

    print("Example 1: Atletico Madrid 24-25")
    atm_ids = get_match_ids("Atletico Madrid", "ESP-La Liga", "24-25")

    if not atm_ids.empty:
        print("\nFirst 5 matches:")
        print(atm_ids.head())

        output_file = "atm_match_ids_24-25.csv"
        atm_ids.to_csv(output_file, index=False)
        print(f"\nSaved to: {output_file}")

    print("\nExample 2: Barcelona 23-24")
    barca_ids = get_match_ids("Barcelona", "ESP-La Liga", "23-24")

    if not barca_ids.empty:
        print("\nFirst 5 matches:")
        print(barca_ids.head())


if __name__ == "__main__":
    main()