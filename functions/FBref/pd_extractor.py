# FootballDecoded - Player Data Extractor
# Robust and reusable player statistics extraction

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import warnings
from typing import Dict, List, Optional, Union
from extractors import FBref

# Suppress the pandas FutureWarning about empty DataFrame concatenation
warnings.filterwarnings('ignore', category=FutureWarning, message='.*DataFrame concatenation with empty or all-NA entries.*')


def extract_player_stats(
    player_name: str, 
    league: str, 
    season: str,
    include_keeper_stats: bool = True,
    verbose: bool = False
) -> Optional[Dict]:
    """
    Extract complete statistics for a single player.
    
    Simple interface: just pass player name, league, and season.
    
    Args:
        player_name: Name of the player (e.g., "Mbappé", "Dembélé")
        league: League identifier (e.g., "ESP-La Liga", "FRA-Ligue 1")
        season: Season identifier (e.g., "2024-25", "2023-24")
        include_keeper_stats: Whether to include goalkeeper statistics
        verbose: Whether to show extraction progress
        
    Returns:
        Dictionary with all player statistics or None if not found
        
    Example:
        >>> mbappe_stats = extract_player_stats("Mbappé", "ESP-La Liga", "2024-25")
        >>> print(f"Goals: {mbappe_stats['goals']}")
    """
    if verbose:
        print(f"Extracting data for {player_name} ({league}, {season})")
    
    # Convert to list format for FBref
    leagues = [league]
    seasons = [season]
    
    # Stat types to extract
    stat_types = [
        'standard', 'shooting', 'passing', 'passing_types', 
        'goal_shot_creation', 'defense', 'possession', 
        'playing_time', 'misc'
    ]
    
    if include_keeper_stats:
        stat_types.extend(['keeper', 'keeper_adv'])
    
    try:
        # Initialize FBref extractor
        fbref = FBref(leagues=leagues, seasons=seasons)
        
        player_data = {}
        basic_info = {}
        
        # Extract each stat type
        for i, stat_type in enumerate(stat_types, 1):
            if verbose:
                print(f"  [{i}/{len(stat_types)}] Processing {stat_type}")
            
            try:
                stats = fbref.read_player_season_stats(stat_type=stat_type)
                player_row = _find_player(stats, player_name)
                
                if player_row is not None:
                    # Capture basic info on first successful extraction
                    if not basic_info:
                        basic_info = {
                            'player_name': player_name,
                            'league': player_row.index.get_level_values('league')[0],
                            'season': player_row.index.get_level_values('season')[0],
                            'team': player_row.index.get_level_values('team')[0]
                        }
                    
                    # Process all columns
                    for col in player_row.columns:
                        clean_name = _clean_column_name(col)
                        value = player_row.iloc[0][col]
                        
                        # Avoid overwriting existing data
                        if clean_name not in player_data:
                            player_data[clean_name] = value
                            
            except Exception as e:
                if verbose:
                    print(f"    Warning: Could not extract {stat_type} - {str(e)[:50]}...")
                continue
        
        if not basic_info:
            if verbose:
                print(f"  Player '{player_name}' not found")
            return None
        
        # Combine basic info with statistics
        final_data = {**basic_info, **player_data}
        
        # Apply standardized naming
        standardized_data = _apply_stat_mapping(final_data)
        
        if verbose:
            print(f"  ✅ Extracted {len(standardized_data)} fields")
        
        return standardized_data
        
    except Exception as e:
        if verbose:
            print(f"  Error extracting data: {str(e)}")
        return None


def extract_multiple_players(
    players: List[Dict[str, str]], 
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract statistics for multiple players.
    
    Args:
        players: List of dictionaries with 'name', 'league', 'season' keys
        verbose: Whether to show extraction progress
        
    Returns:
        DataFrame with all players' statistics
        
    Example:
        >>> players = [
        ...     {'name': 'Mbappé', 'league': 'ESP-La Liga', 'season': '2024-25'},
        ...     {'name': 'Dembélé', 'league': 'FRA-Ligue 1', 'season': '2024-25'}
        ... ]
        >>> df = extract_multiple_players(players)
    """
    all_data = []
    
    for i, player_config in enumerate(players, 1):
        if verbose:
            print(f"[{i}/{len(players)}] Processing {player_config['name']}")
        
        player_data = extract_player_stats(
            player_config['name'],
            player_config['league'],
            player_config['season'],
            verbose=False  # Suppress individual verbose output
        )
        
        if player_data:
            all_data.append(player_data)
        elif verbose:
            print(f"  Failed to extract data for {player_config['name']}")
    
    return pd.DataFrame(all_data) if all_data else pd.DataFrame()


def _clean_column_name(col: Union[str, tuple]) -> str:
    """Clean and standardize column names from FBref's multi-level headers."""
    if isinstance(col, tuple):
        level0, level1 = col[0], col[1]
        
        if level1 == '' or pd.isna(level1) or level1 is None:
            return level0
        
        # For common category headers, use only the specific stat name
        common_categories = [
            'Standard', 'Performance', 'Expected', 'Total', 'Short', 
            'Medium', 'Long', 'Playing Time', 'Per 90 Minutes'
        ]
        
        if level0 in common_categories:
            return level1
        else:
            return f"{level0}_{level1}"
    
    return str(col)


def _find_player(stats: pd.DataFrame, player_name: str) -> Optional[pd.DataFrame]:
    """Search for a player using flexible name matching."""
    if stats is None or stats.empty:
        return None
    
    # Generate name variations for flexible matching
    variations = [
        player_name,
        player_name.replace('é', 'e').replace('ñ', 'n').replace('í', 'i').replace('ó', 'o'),
        player_name.split()[-1] if ' ' in player_name else player_name,
        player_name.split()[0] if ' ' in player_name else player_name,
    ]
    
    for variation in variations:
        matches = stats[
            stats.index.get_level_values('player').str.contains(
                variation, case=False, na=False
            )
        ]
        if not matches.empty:
            return matches
    
    return None


def _get_stat_mapping() -> Dict[str, str]:
    """Complete mapping from FBref technical names to descriptive names."""
    return {
        # Basic information
        'nation': 'nationality',
        'pos': 'position', 
        'age': 'age',
        'born': 'birth_year',
        
        # Playing time
        'MP': 'matches_played',
        'Starts': 'matches_started',
        'Min': 'minutes_played',
        '90s': 'full_matches_equivalent',
        'Mn/MP': 'minutes_per_match',
        'Min%': 'minutes_percentage',
        'Mn/Start': 'minutes_per_start',
        'Compl': 'complete_matches',
        'Subs': 'substitute_appearances',
        'Mn/Sub': 'minutes_per_substitution',
        'unSub': 'unused_substitute',
        
        # Performance
        'Gls': 'goals',
        'Ast': 'assists', 
        'G+A': 'goals_plus_assists',
        'G-PK': 'non_penalty_goals',
        'PK': 'penalty_goals',
        'PKatt': 'penalty_attempts',
        'CrdY': 'yellow_cards',
        'CrdR': 'red_cards',
        '2CrdY': 'second_yellow_cards',
        'G+A-PK': 'goals_assists_minus_penalties',
        
        # Shooting
        'Sh': 'shots',
        'SoT': 'shots_on_target',
        'SoT%': 'shots_on_target_pct',
        'Sh/90': 'shots_per_90',
        'SoT/90': 'shots_on_target_per_90',
        'G/Sh': 'goals_per_shot',
        'G/SoT': 'goals_per_shot_on_target',
        'Dist': 'avg_shot_distance',
        'FK': 'free_kick_shots',
        
        # Expected metrics
        'xG': 'expected_goals',
        'npxG': 'non_penalty_expected_goals',
        'npxG/Sh': 'non_penalty_xG_per_shot',
        'G-xG': 'goals_minus_expected',
        'np:G-xG': 'non_penalty_goals_minus_expected',
        'xAG': 'expected_assists',
        'xA': 'expected_assists_alt',
        'A-xAG': 'assists_minus_expected',
        'npxG+xAG': 'non_penalty_xG_plus_xAG',
        'xG+xAG': 'expected_goals_plus_assists',
        
        # Passing
        'Cmp': 'passes_completed',
        'Att': 'passes_attempted', 
        'Cmp%': 'pass_completion_pct',
        'TotDist': 'total_pass_distance',
        'PrgDist': 'progressive_pass_distance',
        'KP': 'key_passes',
        '1/3': 'passes_final_third',
        'PPA': 'passes_penalty_area',
        'CrsPA': 'crosses_penalty_area',
        'PrgP': 'progressive_passes',
        
        # Pass types
        'Live': 'live_ball_passes',
        'Dead': 'dead_ball_passes',
        'TB': 'through_balls',
        'Sw': 'switches',
        'Crs': 'crosses',
        'TI': 'throw_ins',
        'CK': 'corner_kicks',
        'In': 'inswinging_corners',
        'Out': 'outswinging_corners',
        'Str': 'straight_corners',
        'Off': 'offsides_from_passes',
        'Blocks': 'blocked_passes',
        
        # Shot/Goal creation
        'SCA': 'shot_creating_actions',
        'SCA90': 'shot_creating_actions_per_90',
        'PassLive': 'sca_live_passes',
        'PassDead': 'sca_dead_ball_passes',
        'TO': 'sca_take_ons',
        'Sh': 'sca_shots',
        'Fld': 'sca_fouls_drawn',
        'Def': 'sca_defensive_actions',
        'GCA': 'goal_creating_actions',
        'GCA90': 'goal_creating_actions_per_90',
        
        # Defense
        'Tkl': 'tackles',
        'TklW': 'tackles_won',
        'Def 3rd': 'tackles_defensive_third',
        'Mid 3rd': 'tackles_middle_third',
        'Att 3rd': 'tackles_attacking_third',
        'Tkl%': 'challenge_success_pct',
        'Lost': 'challenges_lost',
        'Int': 'interceptions',
        'Tkl+Int': 'tackles_plus_interceptions',
        'Clr': 'clearances',
        'Err': 'errors',
        
        # Possession
        'Touches': 'touches',
        'Def Pen': 'touches_defensive_penalty_area',
        'Def 3rd': 'touches_defensive_third',
        'Mid 3rd': 'touches_middle_third',
        'Att 3rd': 'touches_attacking_third',
        'Att Pen': 'touches_attacking_penalty_area',
        'Live': 'live_ball_touches',
        'Succ': 'successful_take_ons',
        'Succ%': 'take_on_success_pct',
        'Tkld': 'tackled_during_take_on',
        'Tkld%': 'tackled_during_take_on_pct',
        'Carries': 'carries',
        'PrgC': 'progressive_carries',
        'CPA': 'carries_into_penalty_area',
        'Mis': 'miscontrols',
        'Dis': 'dispossessed',
        'Rec': 'passes_received',
        'PrgR': 'progressive_passes_received',
        
        # Team success
        'PPM': 'points_per_match',
        'onG': 'goals_while_on_pitch',
        'onGA': 'goals_against_while_on_pitch',
        '+/-': 'plus_minus',
        '+/-90': 'plus_minus_per_90',
        'On-Off': 'team_performance_difference',
        'onxG': 'expected_goals_while_on_pitch',
        'onxGA': 'expected_goals_against_while_on_pitch',
        'xG+/-': 'expected_plus_minus',
        'xG+/-90': 'expected_plus_minus_per_90',
        
        # Disciplinary
        'Fls': 'fouls_committed',
        'Fld': 'fouls_drawn',
        'Off': 'offsides',
        'PKwon': 'penalties_won',
        'PKcon': 'penalties_conceded',
        'OG': 'own_goals',
        'Recov': 'ball_recoveries',
        
        # Aerial duels
        'Won': 'aerial_duels_won',
        'Lost': 'aerial_duels_lost',
        'Won%': 'aerial_duels_won_pct',
        
        # Goalkeeper specific
        'GA': 'goals_against',
        'GA90': 'goals_against_per_90',
        'SoTA': 'shots_on_target_against',
        'Saves': 'saves',
        'Save%': 'save_percentage',
        'W': 'wins',
        'D': 'draws',
        'L': 'losses',
        'CS': 'clean_sheets',
        'CS%': 'clean_sheet_percentage',
        'PKA': 'penalty_kicks_attempted_against',
        'PKsv': 'penalty_kicks_saved',
        'PKm': 'penalty_kicks_missed_against'
    }


def _apply_stat_mapping(player_data: Dict) -> Dict:
    """Apply standardized naming to player statistics."""
    stat_mapping = _get_stat_mapping()
    standardized_data = {}
    
    for original_name, value in player_data.items():
        standardized_name = stat_mapping.get(original_name, original_name)
        standardized_data[standardized_name] = value
    
    return standardized_data


# Convenience function for single player extraction
def get_player_stats(player_name: str, league: str, season: str) -> Optional[Dict]:
    """
    Simple convenience function for extracting player statistics.
    
    Args:
        player_name: Player name (e.g., "Mbappé")
        league: League (e.g., "ESP-La Liga")
        season: Season (e.g., "2024-25")
        
    Returns:
        Dictionary with player statistics or None if not found
    """
    return extract_player_stats(player_name, league, season, verbose=False)