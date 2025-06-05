# ========================================================
# FootballDecoded - FBref Data Extractor
# ====================================================================
# Clean, professional wrapper for extracting ALL FBref metrics
# Covers: players, teams, matches, events - complete tactical analysis ready
# ====================================================================

import sys
import os
import pandas as pd
import warnings
from typing import Dict, List, Optional, Union
from datetime import datetime

# Add extractors to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrappers import FBref

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=FutureWarning)


# ====================================================================
# PLAYER DATA EXTRACTION
# ====================================================================

def extract_player_season(
    player_name: str, 
    league: str, 
    season: str,
    verbose: bool = False
) -> Optional[Dict]:
    """
    Extract complete season statistics for a single player.
    
    Args:
        player_name: Player name (e.g., "Mbappé", "Vinicius Jr")
        league: League ID (e.g., "ESP-La Liga", "ENG-Premier League") 
        season: Season ID (e.g., "2024-25", "2023-24")
        verbose: Show extraction progress
        
    Returns:
        Dict with ALL available FBref statistics or None if not found
    """
    if verbose:
        print(f"🔍 Extracting {player_name} season data: {league} {season}")
    
    # All available stat types for comprehensive analysis
    stat_types = [
        'standard', 'shooting', 'passing', 'passing_types', 
        'goal_shot_creation', 'defense', 'possession', 
        'playing_time', 'misc', 'keeper', 'keeper_adv'
    ]
    
    return _extract_player_data(
        player_name=player_name,
        league=league, 
        season=season,
        stat_types=stat_types,
        match_id=None,
        verbose=verbose
    )


def extract_player_match(
    player_name: str,
    match_id: str, 
    league: str,
    season: str,
    verbose: bool = False
) -> Optional[Dict]:
    """
    Extract complete match statistics for a single player.
    
    Args:
        player_name: Player name
        match_id: FBref match ID
        league: League identifier
        season: Season identifier
        verbose: Show extraction progress
        
    Returns:
        Dict with match-specific statistics or None if not found
    """
    if verbose:
        print(f"🔍 Extracting {player_name} match data: {match_id}")
    
    # Match-specific stat types
    stat_types = [
        'summary', 'passing', 'passing_types', 'defense', 
        'possession', 'misc', 'keepers'
    ]
    
    return _extract_player_data(
        player_name=player_name,
        league=league,
        season=season, 
        stat_types=stat_types,
        match_id=match_id,
        verbose=verbose
    )


def extract_multiple_players(
    players: List[str],
    league: str,
    season: str,
    match_id: Optional[str] = None,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract statistics for multiple players efficiently.
    
    Args:
        players: List of player names
        league: League identifier
        season: Season identifier
        match_id: Optional match ID for match-specific data
        verbose: Show progress
        
    Returns:
        DataFrame with all players' statistics
    """
    if verbose:
        data_type = "match" if match_id else "season"
        print(f"🔍 Extracting {data_type} data for {len(players)} players")
    
    all_data = []
    successful = 0
    
    for i, player_name in enumerate(players, 1):
        if verbose:
            print(f"[{i}/{len(players)}] {player_name}")
        
        # Choose extraction method
        if match_id:
            player_data = extract_player_match(player_name, match_id, league, season, verbose=False)
        else:
            player_data = extract_player_season(player_name, league, season, verbose=False)
        
        if player_data:
            all_data.append(player_data)
            successful += 1
        elif verbose:
            print(f"   ❌ Failed: {player_name}")
    
    if verbose:
        print(f"✅ Extracted {successful}/{len(players)} players successfully")
    
    df = pd.DataFrame(all_data) if all_data else pd.DataFrame()
    return _standardize_columns(df, 'player')


# ====================================================================
# TEAM DATA EXTRACTION  
# ====================================================================

def extract_team_season(
    team_name: str,
    league: str, 
    season: str,
    include_opponent_stats: bool = False,
    verbose: bool = False
) -> Optional[Dict]:
    """
    Extract complete season statistics for a single team.
    
    Args:
        team_name: Team name (e.g., "Real Madrid", "Manchester City")
        league: League identifier
        season: Season identifier  
        include_opponent_stats: Include opponent statistics
        verbose: Show extraction progress
        
    Returns:
        Dict with comprehensive team statistics or None if not found
    """
    if verbose:
        print(f"🔍 Extracting {team_name} season data: {league} {season}")
    
    # All team stat types for complete analysis
    stat_types = [
        'standard', 'shooting', 'passing', 'passing_types',
        'goal_shot_creation', 'defense', 'possession', 
        'playing_time', 'misc', 'keeper', 'keeper_adv'
    ]
    
    return _extract_team_data(
        team_name=team_name,
        league=league,
        season=season,
        stat_types=stat_types, 
        include_opponent_stats=include_opponent_stats,
        verbose=verbose
    )


def extract_multiple_teams(
    teams: List[str],
    league: str,
    season: str, 
    include_opponent_stats: bool = False,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract season statistics for multiple teams efficiently.
    
    Args:
        teams: List of team names
        league: League identifier
        season: Season identifier
        include_opponent_stats: Include opponent statistics
        verbose: Show progress
        
    Returns:
        DataFrame with all teams' statistics
    """
    if verbose:
        print(f"🔍 Extracting season data for {len(teams)} teams")
    
    all_data = []
    successful = 0
    
    for i, team_name in enumerate(teams, 1):
        if verbose:
            print(f"[{i}/{len(teams)}] {team_name}")
        
        team_data = extract_team_season(
            team_name, league, season, include_opponent_stats, verbose=False
        )
        
        if team_data:
            all_data.append(team_data)
            successful += 1
        elif verbose:
            print(f"   ❌ Failed: {team_name}")
    
    if verbose:
        print(f"✅ Extracted {successful}/{len(teams)} teams successfully")
    
    df = pd.DataFrame(all_data) if all_data else pd.DataFrame()
    return _standardize_columns(df, 'team')


def extract_league_players(
    league: str,
    season: str,
    team_filter: Optional[str] = None,
    position_filter: Optional[str] = None,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract all players from a league with optional filtering.
    
    Args:
        league: League identifier
        season: Season identifier
        team_filter: Optional team name filter
        position_filter: Optional position filter ("FW", "MF", "DF", "GK")
        verbose: Show progress
        
    Returns:
        DataFrame with player list and basic info
    """
    if verbose:
        print(f"🔍 Extracting player list from {league} {season}")
        if team_filter:
            print(f"   Team filter: {team_filter}")
        if position_filter:
            print(f"   Position filter: {position_filter}")
    
    try:
        fbref = FBref(leagues=[league], seasons=[season])
        player_stats = fbref.read_player_season_stats(stat_type='standard')
        
        if player_stats is None or player_stats.empty:
            if verbose:
                print(f"   ❌ No players found")
            return pd.DataFrame()
        
        # Extract and filter player information
        players_df = player_stats.reset_index()
        
        # Apply filters
        if team_filter:
            original_count = len(players_df)
            players_df = players_df[
                players_df['team'].str.contains(team_filter, case=False, na=False)
            ]
            if verbose:
                print(f"   🔍 Team filter: {len(players_df)}/{original_count} players")
        
        if position_filter:
            original_count = len(players_df)
            players_df = players_df[
                players_df['pos'].str.contains(position_filter, case=False, na=False)
            ]
            if verbose:
                print(f"   🔍 Position filter: {len(players_df)}/{original_count} players")
        
        # Select and standardize columns
        result_columns = ['player', 'team', 'league', 'season']
        if 'pos' in players_df.columns:
            result_columns.append('pos')
        if 'age' in players_df.columns:
            result_columns.append('age')
        if 'nation' in players_df.columns:
            result_columns.append('nation')
        
        result_df = players_df[result_columns].copy()
        result_df = result_df.sort_values(['team', 'player'])
        
        if verbose:
            print(f"   ✅ Found {len(result_df)} players")
        
        return result_df
        
    except Exception as e:
        if verbose:
            print(f"   ❌ Extraction failed: {str(e)}")
        return pd.DataFrame()


# ====================================================================
# MATCH DATA EXTRACTION
# ====================================================================

def extract_match_events(
    match_id: str,
    league: str, 
    season: str,
    event_type: str = 'all',
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract match events (goals, cards, substitutions, shots).
    
    Args:
        match_id: FBref match identifier
        league: League identifier
        season: Season identifier
        event_type: 'all', 'events', 'shots', 'lineups'
        verbose: Show progress
        
    Returns:
        DataFrame with match events
    """
    if verbose:
        print(f"🔍 Extracting {event_type} from match {match_id}")
    
    try:
        fbref = FBref(leagues=[league], seasons=[season])
        
        if event_type in ['all', 'events']:
            events = fbref.read_events(match_id=match_id)
            if verbose and not events.empty:
                print(f"   ✅ Events: {len(events)} records")
        
        if event_type in ['all', 'shots']:
            shots = fbref.read_shot_events(match_id=match_id)
            if verbose and not shots.empty:
                print(f"   ✅ Shots: {len(shots)} records")
        
        if event_type in ['all', 'lineups']:
            lineups = fbref.read_lineup(match_id=match_id)
            if verbose and not lineups.empty:
                print(f"   ✅ Lineups: {len(lineups)} records")
        
        # Return appropriate data based on event_type
        if event_type == 'events':
            return events if 'events' in locals() else pd.DataFrame()
        elif event_type == 'shots':
            return shots if 'shots' in locals() else pd.DataFrame()
        elif event_type == 'lineups':
            return lineups if 'lineups' in locals() else pd.DataFrame()
        else:  # 'all'
            result = {}
            if 'events' in locals() and not events.empty:
                result['events'] = events
            if 'shots' in locals() and not shots.empty:
                result['shots'] = shots
            if 'lineups' in locals() and not lineups.empty:
                result['lineups'] = lineups
            return result
        
    except Exception as e:
        if verbose:
            print(f"   ❌ Match extraction failed: {str(e)}")
        return pd.DataFrame() if event_type != 'all' else {}


def extract_league_schedule(
    league: str,
    season: str,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract complete league schedule with results.
    
    Args:
        league: League identifier
        season: Season identifier
        verbose: Show progress
        
    Returns:
        DataFrame with league schedule and results
    """
    if verbose:
        print(f"🔍 Extracting schedule for {league} {season}")
    
    try:
        fbref = FBref(leagues=[league], seasons=[season])
        schedule = fbref.read_schedule()
        
        if verbose and not schedule.empty:
            total_matches = len(schedule)
            completed_matches = len(schedule[schedule['score'].notna()])
            print(f"   ✅ Schedule: {total_matches} matches ({completed_matches} completed)")
        
        return schedule
        
    except Exception as e:
        if verbose:
            print(f"   ❌ Schedule extraction failed: {str(e)}")
        return pd.DataFrame()


# ====================================================================
# CORE PROCESSING ENGINE
# ====================================================================

def _extract_player_data(
    player_name: str,
    league: str,
    season: str, 
    stat_types: List[str],
    match_id: Optional[str] = None,
    verbose: bool = False
) -> Optional[Dict]:
    """Core player extraction engine."""
    try:
        fbref = FBref(leagues=[league], seasons=[season])
        
        player_data = {}
        basic_info = {}
        stats_found = 0
        
        for i, stat_type in enumerate(stat_types, 1):
            if verbose:
                print(f"   [{i}/{len(stat_types)}] {stat_type}")
            
            try:
                # Get stats based on extraction type
                if match_id:
                    stats = fbref.read_player_match_stats(stat_type=stat_type, match_id=match_id)
                    player_row = _find_player_in_data(stats, player_name)
                else:
                    stats = fbref.read_player_season_stats(stat_type=stat_type)
                    player_row = _find_player_in_data(stats, player_name)
                
                if player_row is not None:
                    # Extract basic info on first success
                    if not basic_info:
                        basic_info = _extract_basic_info(player_row, player_name, match_id)
                    
                    # Process all columns from this stat type
                    _process_columns(player_row, player_data)
                    stats_found += 1
                    
                    if verbose:
                        print(f"      ✅ Success")
                elif verbose:
                    print(f"      ⚠️  Not found")
                    
            except Exception as e:
                if verbose:
                    print(f"      ❌ Error: {str(e)[:30]}...")
                continue
        
        if not basic_info:
            if verbose:
                print(f"   ❌ Player not found: {player_name}")
            return None
        
        # Combine and standardize
        final_data = {**basic_info, **player_data}
        standardized_data = _apply_stat_mapping(final_data)
        
        if verbose:
            print(f"   ✅ Extracted {len(standardized_data)} fields from {stats_found} stat types")
        
        return standardized_data
        
    except Exception as e:
        if verbose:
            print(f"   ❌ Extraction failed: {str(e)}")
        return None


def _extract_team_data(
    team_name: str,
    league: str,
    season: str,
    stat_types: List[str],
    include_opponent_stats: bool = False,
    verbose: bool = False
) -> Optional[Dict]:
    """Core team extraction engine."""
    try:
        fbref = FBref(leagues=[league], seasons=[season])
        
        team_data = {}
        basic_info = {}
        stats_found = 0
        
        for i, stat_type in enumerate(stat_types, 1):
            if verbose:
                print(f"   [{i}/{len(stat_types)}] {stat_type}")
            
            try:
                # Extract team stats
                stats = fbref.read_team_season_stats(stat_type=stat_type, opponent_stats=False)
                team_row = _find_team_in_data(stats, team_name)
                
                if team_row is not None:
                    if not basic_info:
                        basic_info = _extract_team_basic_info(team_row, team_name, league, season)
                    
                    _process_columns(team_row, team_data)
                    stats_found += 1
                    
                    if verbose:
                        print(f"      ✅ Success")
                else:
                    if verbose:
                        print(f"      ⚠️  Not found")
                
                # Extract opponent stats if requested
                if include_opponent_stats:
                    try:
                        opp_stats = fbref.read_team_season_stats(stat_type=stat_type, opponent_stats=True)
                        opp_row = _find_team_in_data(opp_stats, team_name)
                        if opp_row is not None:
                            _process_columns(opp_row, team_data, prefix='opponent_')
                    except Exception:
                        pass
                        
            except Exception as e:
                if verbose:
                    print(f"      ❌ Error: {str(e)[:30]}...")
                continue
        
        if not basic_info:
            if verbose:
                print(f"   ❌ Team not found: {team_name}")
            return None
        
        # Combine and standardize
        final_data = {**basic_info, **team_data}
        standardized_data = _apply_stat_mapping(final_data)
        
        if verbose:
            print(f"   ✅ Extracted {len(standardized_data)} fields from {stats_found} stat types")
        
        return standardized_data
        
    except Exception as e:
        if verbose:
            print(f"   ❌ Extraction failed: {str(e)}")
        return None


# ====================================================================
# UTILITY FUNCTIONS
# ====================================================================

def _find_player_in_data(stats: pd.DataFrame, player_name: str) -> Optional[pd.DataFrame]:
    """Find player with flexible name matching."""
    if stats is None or stats.empty:
        return None
    
    variations = _generate_name_variations(player_name)
    
    # Try exact matches first
    for variation in variations:
        matches = stats[
            stats.index.get_level_values('player').str.lower() == variation.lower()
        ]
        if not matches.empty:
            return matches
    
    # Try partial matches
    for variation in variations:
        matches = stats[
            stats.index.get_level_values('player').str.contains(
                variation, case=False, na=False, regex=False
            )
        ]
        if not matches.empty:
            return matches
    
    return None


def _find_team_in_data(stats: pd.DataFrame, team_name: str) -> Optional[pd.DataFrame]:
    """Find team with flexible name matching."""
    if stats is None or stats.empty:
        return None
    
    variations = _generate_team_variations(team_name)
    
    # Try exact matches first
    for variation in variations:
        matches = stats[
            stats.index.get_level_values('team').str.lower() == variation.lower()
        ]
        if not matches.empty:
            return matches
    
    # Try partial matches
    for variation in variations:
        matches = stats[
            stats.index.get_level_values('team').str.contains(
                variation, case=False, na=False, regex=False
            )
        ]
        if not matches.empty:
            return matches
    
    return None


def _generate_name_variations(name: str) -> List[str]:
    """Generate name variations for robust matching."""
    variations = [name]
    
    # Remove accents
    clean_name = (name
                  .replace('é', 'e').replace('ñ', 'n').replace('í', 'i')
                  .replace('ó', 'o').replace('á', 'a').replace('ú', 'u')
                  .replace('ç', 'c').replace('ü', 'u').replace('ø', 'o'))
    if clean_name != name:
        variations.append(clean_name)
    
    # Add name components
    if ' ' in name:
        parts = name.split()
        variations.extend(parts)
        if len(parts) > 1:
            variations.append(' '.join(parts[:2]))
            variations.append(' '.join(parts[-2:]))
    
    return list(dict.fromkeys(variations))


def _generate_team_variations(team_name: str) -> List[str]:
    """Generate team name variations."""
    variations = [team_name]
    
    # Remove common suffixes
    suffixes = [' FC', ' CF', ' United', ' City', ' Real', ' Club']
    for suffix in suffixes:
        if team_name.endswith(suffix):
            variations.append(team_name[:-len(suffix)])
    
    # Common variations
    mappings = {
        'Real Madrid': ['Madrid', 'Real Madrid CF'],
        'Barcelona': ['Barça', 'FC Barcelona', 'Barca'],
        'Manchester United': ['Man United', 'Man Utd', 'United'],
        'Manchester City': ['Man City', 'City'],
        'Tottenham': ['Spurs', 'Tottenham Hotspur']
    }
    
    if team_name in mappings:
        variations.extend(mappings[team_name])
    
    return list(dict.fromkeys(variations))


def _extract_basic_info(
    row: pd.DataFrame,
    name: str,
    match_id: Optional[str] = None
) -> Dict:
    """Extract basic identification info."""
    basic_info = {
        'player_name': name,
        'league': row.index.get_level_values('league')[0],
        'season': row.index.get_level_values('season')[0],
        'team': row.index.get_level_values('team')[0]
    }
    
    if match_id:
        basic_info['match_id'] = match_id
        if 'game' in row.index.names:
            basic_info['game'] = row.index.get_level_values('game')[0]
    
    return basic_info


def _extract_team_basic_info(
    row: pd.DataFrame,
    team_name: str,
    league: str,
    season: str
) -> Dict:
    """Extract basic team identification info."""
    return {
        'team_name': team_name,
        'league': league,
        'season': season,
        'official_team_name': row.index.get_level_values('team')[0]
    }


def _process_columns(row: pd.DataFrame, data_dict: Dict, prefix: str = '') -> None:
    """Process all columns from a row, avoiding duplicates."""
    for col in row.columns:
        clean_name = _clean_column_name(col)
        if prefix:
            clean_name = f"{prefix}{clean_name}"
        
        if clean_name not in data_dict:
            data_dict[clean_name] = row.iloc[0][col]


def _clean_column_name(col: Union[str, tuple]) -> str:
    """Clean and standardize column names."""
    if isinstance(col, tuple):
        level0, level1 = col[0], col[1]
        
        if level1 == '' or pd.isna(level1) or level1 is None:
            return level0
        
        common_categories = [
            'Standard', 'Performance', 'Expected', 'Total', 'Short', 
            'Medium', 'Long', 'Playing Time', 'Per 90 Minutes'
        ]
        
        if level0 in common_categories:
            return level1
        else:
            return f"{level0}_{level1}"
    
    return str(col)


def _apply_stat_mapping(data: Dict) -> Dict:
    """Apply standardized naming convention."""
    stat_mapping = _get_stat_mapping()
    standardized_data = {}
    
    for original_name, value in data.items():
        standardized_name = stat_mapping.get(original_name, original_name)
        standardized_data[standardized_name] = value
    
    return standardized_data


def _get_stat_mapping() -> Dict[str, str]:
    """Comprehensive stat mapping for consistent naming."""
    return {
        # Basic info
        'nation': 'nationality', 'pos': 'position', 'age': 'age', 'born': 'birth_year',
        
        # Playing time
        'MP': 'matches_played', 'Starts': 'matches_started', 'Min': 'minutes_played',
        '90s': 'full_matches_equivalent', 'Mn/MP': 'minutes_per_match',
        
        # Core performance
        'Gls': 'goals', 'Ast': 'assists', 'G+A': 'goals_plus_assists',
        'G-PK': 'non_penalty_goals', 'PK': 'penalty_goals', 'PKatt': 'penalty_attempts',
        'CrdY': 'yellow_cards', 'CrdR': 'red_cards',
        
        # Shooting
        'Sh': 'shots', 'SoT': 'shots_on_target', 'SoT%': 'shots_on_target_pct',
        'Sh/90': 'shots_per_90', 'G/Sh': 'goals_per_shot', 'G/SoT': 'goals_per_shot_on_target',
        'Dist': 'avg_shot_distance',
        
        # Expected metrics
        'xG': 'expected_goals', 'npxG': 'non_penalty_expected_goals',
        'xAG': 'expected_assists', 'xA': 'expected_assists_alt',
        'npxG+xAG': 'non_penalty_xG_plus_xAG',
        
        # Passing
        'Cmp': 'passes_completed', 'Att': 'passes_attempted', 'Cmp%': 'pass_completion_pct',
        'TotDist': 'total_pass_distance', 'PrgDist': 'progressive_pass_distance',
        'KP': 'key_passes', '1/3': 'passes_final_third', 'PPA': 'passes_penalty_area',
        'PrgP': 'progressive_passes',
        
        # Pass types
        'Live': 'live_ball_passes', 'Dead': 'dead_ball_passes', 'TB': 'through_balls',
        'Sw': 'switches', 'Crs': 'crosses', 'CK': 'corner_kicks',
        
        # Shot/Goal creation
        'SCA': 'shot_creating_actions', 'SCA90': 'shot_creating_actions_per_90',
        'GCA': 'goal_creating_actions', 'GCA90': 'goal_creating_actions_per_90',
        
        # Defense
        'Tkl': 'tackles', 'TklW': 'tackles_won', 'Int': 'interceptions',
        'Clr': 'clearances', 'Err': 'errors',
        
        # Possession
        'Touches': 'touches', 'Succ': 'successful_take_ons', 'Succ%': 'take_on_success_pct',
        'Carries': 'carries', 'PrgC': 'progressive_carries', 'Mis': 'miscontrols',
        'Dis': 'dispossessed',
        
        # Disciplinary
        'Fls': 'fouls_committed', 'Fld': 'fouls_drawn', 'Off': 'offsides',
        'Recov': 'ball_recoveries',
        
        # Aerial duels
        'Won': 'aerial_duels_won', 'Lost': 'aerial_duels_lost', 'Won%': 'aerial_duels_won_pct',
        
        # Goalkeeper
        'GA': 'goals_against', 'GA90': 'goals_against_per_90', 'SoTA': 'shots_on_target_against',
        'Saves': 'saves', 'Save%': 'save_percentage', 'CS': 'clean_sheets',
        'PKA': 'penalty_kicks_attempted_against', 'PKsv': 'penalty_kicks_saved',
        
        # Team performance
        'W': 'wins', 'D': 'draws', 'L': 'losses', 'Pts': 'points',
        'GF': 'goals_for', 'GA': 'goals_against', 'GD': 'goal_difference',
        'xGF': 'expected_goals_for', 'xGA': 'expected_goals_against'
    }


def _standardize_columns(df: pd.DataFrame, data_type: str) -> pd.DataFrame:
    """Ensure consistent column ordering."""
    if df.empty:
        return df
    
    if data_type == 'player':
        priority_columns = [
            'player_name', 'team', 'league', 'season', 'match_id', 'game',
            'position', 'age', 'nationality', 'birth_year',
            'minutes_played', 'matches_played', 'matches_started',
            'goals', 'assists', 'goals_plus_assists',
            'expected_goals', 'shots', 'shots_on_target',
            'passes_completed', 'pass_completion_pct', 'key_passes',
            'touches', 'tackles', 'interceptions'
        ]
    else:  # team
        priority_columns = [
            'team_name', 'league', 'season', 'official_team_name',
            'wins', 'draws', 'losses', 'points', 'goals_for', 'goals_against',
            'expected_goals_for', 'expected_goals_against', 'shots', 'passes_completed'
        ]
    
    # Organize columns: priority first, then remaining alphabetically
    available_priority = [col for col in priority_columns if col in df.columns]
    remaining_columns = sorted([col for col in df.columns if col not in priority_columns])
    
    final_order = available_priority + remaining_columns
    return df[final_order]


# ====================================================================
# EXPORT UTILITIES
# ====================================================================

def export_to_csv(
    data: Union[Dict, pd.DataFrame],
    filename: str,
    include_timestamp: bool = True
) -> str:
    """
    Export data to CSV with proper formatting.
    
    Args:
        data: Data to export (Dict or DataFrame)
        filename: Output filename (without .csv extension)
        include_timestamp: Add timestamp to filename
        
    Returns:
        Full path of created CSV file
    """
    if isinstance(data, dict):
        df = pd.DataFrame([data])
    else:
        df = data
    
    if include_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"{filename}_{timestamp}.csv"
    else:
        full_filename = f"{filename}.csv"
    
    df.to_csv(full_filename, index=False, encoding='utf-8')
    
    print(f"📊 Data exported to: {full_filename}")
    print(f"   Rows: {len(df)} | Columns: {len(df.columns)}")
    
    return full_filename


# ====================================================================
# QUICK ACCESS FUNCTIONS - Simple Interface
# ====================================================================

def get_player(player_name: str, league: str, season: str) -> Optional[Dict]:
    """Quick player season stats extraction."""
    return extract_player_season(player_name, league, season, verbose=False)


def get_team(team_name: str, league: str, season: str) -> Optional[Dict]:
    """Quick team season stats extraction."""
    return extract_team_season(team_name, league, season, verbose=False)


def get_players(players: List[str], league: str, season: str) -> pd.DataFrame:
    """Quick multiple players extraction."""
    return extract_multiple_players(players, league, season, verbose=False)


def get_teams(teams: List[str], league: str, season: str) -> pd.DataFrame:
    """Quick multiple teams extraction."""
    return extract_multiple_teams(teams, league, season, verbose=False)


def get_league_players(league: str, season: str, team: Optional[str] = None) -> pd.DataFrame:
    """Quick league players list."""
    return extract_league_players(league, season, team_filter=team, verbose=False)


def get_match_data(match_id: str, league: str, season: str, data_type: str = 'all') -> Union[pd.DataFrame, Dict]:
    """Quick match data extraction."""
    return extract_match_events(match_id, league, season, event_type=data_type, verbose=False)


def get_schedule(league: str, season: str) -> pd.DataFrame:
    """Quick league schedule extraction."""
    return extract_league_schedule(league, season, verbose=False)


# ====================================================================
# BATCH PROCESSING - Advanced Operations
# ====================================================================

def analyze_full_squad(
    team_name: str,
    league: str,
    season: str,
    export: bool = True,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Complete squad analysis with automatic player detection.
    
    Args:
        team_name: Team name for analysis
        league: League identifier
        season: Season identifier
        export: Whether to export results to CSV
        verbose: Show detailed progress
        
    Returns:
        DataFrame with complete squad statistics
    """
    if verbose:
        print(f"🔍 Full squad analysis for {team_name}")
    
    # Get team roster
    players_df = extract_league_players(league, season, team_filter=team_name, verbose=verbose)
    
    if players_df.empty:
        if verbose:
            print(f"   ❌ No players found for {team_name}")
        return pd.DataFrame()
    
    player_list = players_df['player'].unique().tolist()
    
    if verbose:
        print(f"   📊 Analyzing {len(player_list)} players")
    
    # Extract stats for all players
    squad_df = extract_multiple_players(player_list, league, season, verbose=verbose)
    
    # Export if requested
    if export and not squad_df.empty:
        filename = f"{team_name.replace(' ', '_')}_squad_{league}_{season}"
        export_to_csv(squad_df, filename)
    
    return squad_df


def compare_teams(
    teams: List[str],
    league: str,
    season: str,
    include_squad_analysis: bool = False,
    export: bool = True,
    verbose: bool = False
) -> Dict[str, pd.DataFrame]:
    """
    Complete teams comparison with optional squad analysis.
    
    Args:
        teams: List of team names to compare
        league: League identifier
        season: Season identifier
        include_squad_analysis: Whether to include individual player analysis
        export: Whether to export results
        verbose: Show progress
        
    Returns:
        Dict with team stats and optional squad data
    """
    if verbose:
        print(f"🔍 Comparing {len(teams)} teams in {league} {season}")
    
    results = {}
    
    # Team-level comparison
    teams_df = extract_multiple_teams(teams, league, season, verbose=verbose)
    results['team_comparison'] = teams_df
    
    if export and not teams_df.empty:
        export_to_csv(teams_df, f"team_comparison_{league}_{season}")
    
    # Squad-level analysis if requested
    if include_squad_analysis:
        if verbose:
            print("   📊 Including squad analysis...")
        
        squad_data = {}
        for team in teams:
            if verbose:
                print(f"   Analyzing {team} squad...")
            squad_df = analyze_full_squad(team, league, season, export=False, verbose=False)
            if not squad_df.empty:
                squad_data[team] = squad_df
        
        results['squad_analysis'] = squad_data
        
        if export and squad_data:
            # Export combined squad data
            all_squads = pd.concat(squad_data.values(), ignore_index=True)
            export_to_csv(all_squads, f"squads_comparison_{league}_{season}")
    
    if verbose:
        print(f"✅ Comparison complete")
    
    return results


def analyze_league(
    league: str,
    season: str,
    include_player_stats: bool = False,
    top_teams_only: int = 0,
    export: bool = True,
    verbose: bool = False
) -> Dict[str, pd.DataFrame]:
    """
    Complete league analysis with schedule, teams, and optional player data.
    
    Args:
        league: League identifier
        season: Season identifier
        include_player_stats: Whether to include all player statistics
        top_teams_only: If > 0, only analyze top N teams (by points)
        export: Whether to export results
        verbose: Show progress
        
    Returns:
        Dict with comprehensive league data
    """
    if verbose:
        print(f"🔍 Complete league analysis: {league} {season}")
    
    results = {}
    
    # League schedule and results
    if verbose:
        print("   📅 Extracting schedule...")
    schedule_df = extract_league_schedule(league, season, verbose=False)
    results['schedule'] = schedule_df
    
    # All teams basic stats
    if verbose:
        print("   🏟️ Extracting team statistics...")
    
    # Get all teams from schedule or player data
    if not schedule_df.empty:
        all_teams = list(set(schedule_df['home_team'].tolist() + schedule_df['away_team'].tolist()))
    else:
        players_df = extract_league_players(league, season, verbose=False)
        all_teams = players_df['team'].unique().tolist() if not players_df.empty else []
    
    if all_teams:
        teams_df = extract_multiple_teams(all_teams, league, season, verbose=False)
        results['teams'] = teams_df
        
        # Filter to top teams if requested
        if top_teams_only > 0 and not teams_df.empty and 'points' in teams_df.columns:
            top_teams = teams_df.nlargest(top_teams_only, 'points')['team_name'].tolist()
            if verbose:
                print(f"   🏆 Focusing on top {top_teams_only} teams: {', '.join(top_teams)}")
        else:
            top_teams = all_teams
    else:
        top_teams = []
        results['teams'] = pd.DataFrame()
    
    # Player statistics if requested
    if include_player_stats and top_teams:
        if verbose:
            print("   👤 Extracting player statistics...")
        
        all_players_data = []
        for team in top_teams[:min(len(top_teams), 10)]:  # Limit to avoid overload
            if verbose:
                print(f"      Analyzing {team}...")
            team_players = extract_league_players(league, season, team_filter=team, verbose=False)
            if not team_players.empty:
                players_list = team_players['player'].unique().tolist()
                players_stats = extract_multiple_players(players_list, league, season, verbose=False)
                if not players_stats.empty:
                    all_players_data.append(players_stats)
        
        if all_players_data:
            results['players'] = pd.concat(all_players_data, ignore_index=True)
        else:
            results['players'] = pd.DataFrame()
    
    # Export results
    if export:
        for data_type, data in results.items():
            if not data.empty:
                filename = f"{league}_{season}_{data_type}"
                export_to_csv(data, filename)
    
    if verbose:
        total_data_points = sum(len(df) for df in results.values() if isinstance(df, pd.DataFrame))
        print(f"✅ League analysis complete: {total_data_points} total records")
    
    return results