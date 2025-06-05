# ====================================================================
# FootballDecoded - Professional Player Data Extractor FBref
# ====================================================================
# Modular and robust player statistics extraction from FBref
# Supports both season-long and match-specific data extraction
# ====================================================================

import sys
import os
import pandas as pd
import warnings
from typing import Dict, List, Optional, Union, Tuple

# Add extractors to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrappers import FBref

# Suppress pandas warnings for cleaner output
warnings.filterwarnings('ignore', category=FutureWarning, 
                       message='.*DataFrame concatenation with empty or all-NA entries.*')


# ====================================================================
# MAIN EXTRACTION FUNCTIONS
# ====================================================================

def extract_season_stats(
    player_name: str, 
    league: str, 
    season: str,
    include_keeper_stats: bool = True,
    verbose: bool = False
) -> Optional[Dict]:
    """
    Extract complete season statistics for a single player.
    
    This is your go-to function for season-long analysis.
    
    Args:
        player_name: Player name (e.g., "Mbappé", "Vinicius Jr")
        league: League ID (e.g., "ESP-La Liga", "ENG-Premier League")
        season: Season ID (e.g., "2024-25", "2023-24")
        include_keeper_stats: Include goalkeeper metrics if available
        verbose: Show detailed extraction progress
        
    Returns:
        Dictionary with standardized player statistics or None if not found
        
    Example:
        >>> stats = extract_season_stats("Mbappé", "ESP-La Liga", "2024-25")
        >>> print(f"Goals: {stats['goals']} | Assists: {stats['assists']}")
    """
    if verbose:
        print(f"🔍 Extracting season data for {player_name}")
        print(f"   League: {league} | Season: {season}")
    
    # Configure stat types for comprehensive season analysis
    stat_types = [
        'standard',          # Core stats: goals, assists, minutes, cards
        'shooting',          # Shot metrics: attempts, accuracy, xG
        'passing',           # Pass metrics: completion, distance, key passes
        'passing_types',     # Pass types: live/dead, crosses, corners
        'goal_shot_creation', # Creation metrics: SCA, GCA
        'defense',           # Defensive actions: tackles, interceptions
        'possession',        # Ball control: touches, carries, take-ons
        'playing_time',      # Minutes distribution and team performance
        'misc'               # Additional: fouls, offsides, recoveries
    ]
    
    if include_keeper_stats:
        stat_types.extend(['keeper', 'keeper_adv'])
    
    return _extract_player_data(
        player_name=player_name,
        league=league,
        season=season,
        stat_types=stat_types,
        extraction_type='season',
        match_id=None,
        verbose=verbose
    )


def extract_match_stats(
    player_name: str,
    match_id: str,
    league: str,
    season: str,
    include_keeper_stats: bool = True,
    verbose: bool = False
) -> Optional[Dict]:
    """
    Extract complete match statistics for a single player.
    
    Perfect for match-specific analysis and tactical breakdowns.
    
    Args:
        player_name: Player name (e.g., "Mbappé", "Vinicius Jr")
        match_id: FBref match ID (e.g., "c6b7a6e0")
        league: League ID (e.g., "ESP-La Liga", "ENG-Premier League")
        season: Season ID (e.g., "2024-25", "2023-24")
        include_keeper_stats: Include goalkeeper metrics if available
        verbose: Show detailed extraction progress
        
    Returns:
        Dictionary with standardized player statistics or None if not found
        
    Example:
        >>> stats = extract_match_stats("Mbappé", "c6b7a6e0", "ESP-La Liga", "2024-25")
        >>> print(f"Minutes: {stats['minutes_played']} | Touches: {stats['touches']}")
    """
    if verbose:
        print(f"🔍 Extracting match data for {player_name}")
        print(f"   Match ID: {match_id} | League: {league} | Season: {season}")
    
    # Configure stat types for comprehensive match analysis
    stat_types = [
        'summary',           # Core match stats: goals, assists, minutes, cards
        'passing',           # Pass metrics: completion, distance, key passes
        'passing_types',     # Pass types: live/dead, crosses, corners
        'defense',           # Defensive actions: tackles, interceptions
        'possession',        # Ball control: touches, carries, take-ons
        'misc'               # Additional: fouls, offsides, recoveries
    ]
    
    if include_keeper_stats:
        stat_types.append('keepers')
    
    return _extract_player_data(
        player_name=player_name,
        league=league,
        season=season,
        stat_types=stat_types,
        extraction_type='match',
        match_id=match_id,
        verbose=verbose
    )


def extract_multiple_players_season(
    players: List[str],
    league: str,
    season: str,
    include_keeper_stats: bool = True,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract season statistics for multiple players efficiently.
    
    Ideal for squad analysis and player comparisons.
    
    Args:
        players: List of player names
        league: League identifier
        season: Season identifier
        include_keeper_stats: Include goalkeeper statistics
        verbose: Show extraction progress
        
    Returns:
        DataFrame with all players' statistics, standardized column order
        
    Example:
        >>> players = ["Mbappé", "Vinicius Jr", "Bellingham"]
        >>> df = extract_multiple_players_season(players, "ESP-La Liga", "2024-25")
    """
    return _extract_multiple_players(
        players=players,
        league=league,
        season=season,
        extraction_type='season',
        match_id=None,
        include_keeper_stats=include_keeper_stats,
        verbose=verbose
    )


def extract_multiple_players_match(
    players: List[str],
    match_id: str,
    league: str,
    season: str,
    include_keeper_stats: bool = True,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract match statistics for multiple players efficiently.
    
    Perfect for tactical analysis of specific matches.
    
    Args:
        players: List of player names
        match_id: FBref match identifier
        league: League identifier
        season: Season identifier
        include_keeper_stats: Include goalkeeper statistics
        verbose: Show extraction progress
        
    Returns:
        DataFrame with all players' statistics, standardized column order
        
    Example:
        >>> players = ["Mbappé", "Vinicius Jr", "Bellingham"]
        >>> df = extract_multiple_players_match(players, "c6b7a6e0", "ESP-La Liga", "2024-25")
    """
    return _extract_multiple_players(
        players=players,
        league=league,
        season=season,
        extraction_type='match',
        match_id=match_id,
        include_keeper_stats=include_keeper_stats,
        verbose=verbose
    )


# ====================================================================
# CORE EXTRACTION ENGINE - Internal processing logic
# ====================================================================

def _extract_player_data(
    player_name: str,
    league: str,
    season: str,
    stat_types: List[str],
    extraction_type: str,
    match_id: Optional[str] = None,
    verbose: bool = False
) -> Optional[Dict]:
    """
    Core extraction engine that handles both season and match data.
    
    This unified approach ensures consistent data structure and processing
    across different extraction types.
    """
    try:
        # Initialize FBref extractor
        fbref = FBref(leagues=[league], seasons=[season])
        
        player_data = {}
        basic_info = {}
        stats_extracted = 0
        
        # Process each stat type systematically
        for i, stat_type in enumerate(stat_types, 1):
            if verbose:
                print(f"   [{i}/{len(stat_types)}] Processing {stat_type}...")
            
            try:
                # Choose extraction method based on type
                if extraction_type == 'season':
                    stats = fbref.read_player_season_stats(stat_type=stat_type)
                    player_row = _find_player_in_season(stats, player_name)
                else:  # match
                    stats = fbref.read_player_match_stats(stat_type=stat_type, match_id=match_id)
                    player_row = _find_player_in_match(stats, player_name)
                
                if player_row is not None:
                    # Capture basic info on first successful extraction
                    if not basic_info:
                        basic_info = _extract_basic_info(
                            player_row, player_name, extraction_type, match_id
                        )
                    
                    # Extract all statistics from this stat type
                    cols_added = _process_player_columns(player_row, player_data)
                    stats_extracted += 1
                    
                    if verbose:
                        print(f"      ✅ Extracted {cols_added} fields from {stat_type}")
                else:
                    if verbose:
                        print(f"      ⚠️  Player not found in {stat_type}")
                        
            except Exception as e:
                if verbose:
                    print(f"      ❌ Error with {stat_type}: {str(e)[:50]}...")
                continue
        
        # Validate extraction success
        if not basic_info:
            if verbose:
                target = f"match {match_id}" if extraction_type == 'match' else f"{league} {season}"
                print(f"   ❌ Player '{player_name}' not found in {target}")
            return None
        
        # Combine and standardize data
        final_data = {**basic_info, **player_data}
        standardized_data = _apply_stat_mapping(final_data)
        
        if verbose:
            print(f"   ✅ SUCCESS: Extracted {len(standardized_data)} total fields")
            print(f"   📊 Stats types processed: {stats_extracted}/{len(stat_types)}")
        
        return standardized_data
        
    except Exception as e:
        if verbose:
            print(f"   ❌ EXTRACTION FAILED: {str(e)}")
        return None


def _extract_multiple_players(
    players: List[str],
    league: str,
    season: str,
    extraction_type: str,
    match_id: Optional[str] = None,
    include_keeper_stats: bool = True,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Efficiently extract data for multiple players with consistent column ordering.
    """
    if verbose:
        target = f"match {match_id}" if extraction_type == 'match' else f"{league} {season}"
        print(f"🔍 Extracting {extraction_type} data for {len(players)} players from {target}")
    
    all_data = []
    successful_extractions = 0
    
    for i, player_name in enumerate(players, 1):
        if verbose:
            print(f"\n[{i}/{len(players)}] Processing {player_name}")
        
        # Use appropriate extraction function
        if extraction_type == 'season':
            player_data = extract_season_stats(
                player_name, league, season, include_keeper_stats, verbose=False
            )
        else:  # match
            player_data = extract_match_stats(
                player_name, match_id, league, season, include_keeper_stats, verbose=False
            )
        
        if player_data:
            all_data.append(player_data)
            successful_extractions += 1
        elif verbose:
            print(f"   ❌ Failed to extract data for {player_name}")
    
    if verbose:
        print(f"\n✅ SUMMARY: {successful_extractions}/{len(players)} players extracted successfully")
    
    # Create DataFrame with standardized column order
    df = pd.DataFrame(all_data) if all_data else pd.DataFrame()
    return _standardize_dataframe_columns(df, extraction_type)


# ====================================================================
# DATA PROCESSING UTILITIES - Column handling and standardization
# ====================================================================

def _extract_basic_info(
    player_row: pd.DataFrame,
    player_name: str,
    extraction_type: str,
    match_id: Optional[str] = None
) -> Dict:
    """Extract and standardize basic player information."""
    basic_info = {
        'player_name': player_name,
        'league': player_row.index.get_level_values('league')[0],
        'season': player_row.index.get_level_values('season')[0],
        'team': player_row.index.get_level_values('team')[0]
    }
    
    if extraction_type == 'match':
        basic_info.update({
            'match_id': match_id,
            'game': player_row.index.get_level_values('game')[0]
        })
    
    return basic_info


def _process_player_columns(player_row: pd.DataFrame, player_data: Dict) -> int:
    """Process all columns from a player row, avoiding duplicates."""
    cols_added = 0
    
    for col in player_row.columns:
        clean_name = _clean_column_name(col)
        value = player_row.iloc[0][col]
        
        # Avoid overwriting existing data (first occurrence wins)
        if clean_name not in player_data:
            player_data[clean_name] = value
            cols_added += 1
    
    return cols_added


def _clean_column_name(col: Union[str, tuple]) -> str:
    """
    Clean and standardize column names from FBref's multi-level headers.
    
    FBref uses nested column structures that need flattening while preserving
    meaningful information and avoiding redundancy.
    """
    if isinstance(col, tuple):
        level0, level1 = col[0], col[1]
        
        # Handle empty or null second level
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


def _standardize_dataframe_columns(df: pd.DataFrame, extraction_type: str) -> pd.DataFrame:
    """
    Ensure consistent column ordering across season and match DataFrames.
    
    Priority order: basic info → core stats → advanced metrics → goalkeeper stats
    This guarantees that merging/comparing DataFrames is seamless.
    """
    if df.empty:
        return df
    
    # Define standard column order for consistent DataFrames
    priority_columns = [
        # Basic identification
        'player_name', 'team', 'league', 'season',
        # Match-specific (only for match extraction)
        'match_id', 'game',
        # Core performance metrics
        'position', 'age', 'nationality', 'birth_year',
        'minutes_played', 'matches_played', 'matches_started',
        'goals', 'assists', 'goals_plus_assists',
        'non_penalty_goals', 'penalty_goals', 'penalty_attempts',
        # Advanced performance
        'expected_goals', 'non_penalty_expected_goals', 'expected_assists',
        'shots', 'shots_on_target', 'shots_on_target_pct',
        # Passing metrics
        'passes_completed', 'passes_attempted', 'pass_completion_pct',
        'total_pass_distance', 'progressive_pass_distance',
        'key_passes', 'progressive_passes',
        # Possession and movement
        'touches', 'carries', 'progressive_carries',
        'successful_take_ons', 'take_on_success_pct',
        # Defensive actions
        'tackles', 'tackles_won', 'interceptions', 'clearances',
        # Disciplinary
        'yellow_cards', 'red_cards', 'fouls_committed', 'fouls_drawn'
    ]
    
    # Remove match-specific columns for season data
    if extraction_type == 'season':
        priority_columns = [col for col in priority_columns 
                          if col not in ['match_id', 'game']]
    
    # Organize columns: priority first, then remaining alphabetically
    available_priority = [col for col in priority_columns if col in df.columns]
    remaining_columns = sorted([col for col in df.columns if col not in priority_columns])
    
    final_column_order = available_priority + remaining_columns
    
    return df[final_column_order]


# ====================================================================
# PLAYER SEARCH ENGINE - Robust name matching
# ====================================================================

def _find_player_in_season(stats: pd.DataFrame, player_name: str) -> Optional[pd.DataFrame]:
    """Search for player in season statistics with flexible name matching."""
    return _find_player_base(stats, player_name, 'season')


def _find_player_in_match(stats: pd.DataFrame, player_name: str) -> Optional[pd.DataFrame]:
    """Search for player in match statistics with flexible name matching."""
    return _find_player_base(stats, player_name, 'match')


def _find_player_base(stats: pd.DataFrame, player_name: str, context: str) -> Optional[pd.DataFrame]:
    """
    Base player search function with comprehensive name variations.
    
    Uses progressive matching strategy: exact → partial → fuzzy
    This handles international names, accents, and common variations.
    """
    if stats is None or stats.empty:
        return None
    
    # Generate comprehensive name variations
    variations = _generate_name_variations(player_name)
    
    # Try exact matches first (most reliable)
    for variation in variations:
        matches = stats[
            stats.index.get_level_values('player').str.lower() == variation.lower()
        ]
        if not matches.empty:
            return matches
    
    # Then try partial matches (broader search)
    for variation in variations:
        matches = stats[
            stats.index.get_level_values('player').str.contains(
                variation, case=False, na=False, regex=False
            )
        ]
        if not matches.empty:
            return matches
    
    return None


def _generate_name_variations(player_name: str) -> List[str]:
    """
    Generate comprehensive name variations for robust player matching.
    
    Handles international characters, common prefixes, and name ordering
    to maximize search success across different data sources.
    """
    variations = [player_name]
    
    # Remove accents and special characters
    clean_name = (player_name
                  .replace('é', 'e').replace('ñ', 'n').replace('í', 'i')
                  .replace('ó', 'o').replace('á', 'a').replace('ú', 'u')
                  .replace('ç', 'c').replace('ü', 'u').replace('ø', 'o'))
    if clean_name != player_name:
        variations.append(clean_name)
    
    # Add name components (useful for compound names)
    if ' ' in player_name:
        parts = player_name.split()
        variations.extend(parts)  # Individual name parts
        if len(parts) > 1:
            variations.append(' '.join(parts[:2]))  # First two parts
            variations.append(' '.join(parts[-2:]))  # Last two parts
    
    # Remove common prefixes that might cause mismatches
    for prefix in ['de ', 'del ', 'van ', 'von ', 'da ', 'dos ', 'el ']:
        if player_name.lower().startswith(prefix):
            variations.append(player_name[len(prefix):])
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(variations))


# ====================================================================
# STAT MAPPING SYSTEM - Standardized nomenclature
# ====================================================================

def _apply_stat_mapping(player_data: Dict) -> Dict:
    """
    Apply standardized naming convention to all statistics.
    
    This ensures consistent column names across different extraction types
    and makes data analysis more intuitive.
    """
    stat_mapping = _get_stat_mapping()
    standardized_data = {}
    
    for original_name, value in player_data.items():
        standardized_name = stat_mapping.get(original_name, original_name)
        standardized_data[standardized_name] = value
    
    return standardized_data


def _get_stat_mapping() -> Dict[str, str]:
    """
    Comprehensive mapping from FBref technical names to descriptive names.
    
    This mapping ensures consistent, intuitive column names across all extractions.
    New statistics should be added here to maintain standardization.
    """
    return {
        # ===== BASIC INFORMATION =====
        'nation': 'nationality',
        'pos': 'position',
        'age': 'age',
        'born': 'birth_year',
        
        # ===== PLAYING TIME =====
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
        
        # ===== CORE PERFORMANCE =====
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
        
        # ===== SHOOTING =====
        'Sh': 'shots',
        'SoT': 'shots_on_target',
        'SoT%': 'shots_on_target_pct',
        'Sh/90': 'shots_per_90',
        'SoT/90': 'shots_on_target_per_90',
        'G/Sh': 'goals_per_shot',
        'G/SoT': 'goals_per_shot_on_target',
        'Dist': 'avg_shot_distance',
        'FK': 'free_kick_shots',
        
        # ===== EXPECTED METRICS =====
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
        
        # ===== PASSING =====
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
        
        # ===== PASS TYPES =====
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
        
        # ===== SHOT/GOAL CREATION =====
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
        
        # ===== DEFENSE =====
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
        
        # ===== POSSESSION =====
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
        
        # ===== TEAM SUCCESS =====
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
        
        # ===== DISCIPLINARY =====
        'Fls': 'fouls_committed',
        'Fld': 'fouls_drawn',
        'Off': 'offsides',
        'PKwon': 'penalties_won',
        'PKcon': 'penalties_conceded',
        'OG': 'own_goals',
        'Recov': 'ball_recoveries',
        
        # ===== AERIAL DUELS =====
        'Won': 'aerial_duels_won',
        'Lost': 'aerial_duels_lost',
        'Won%': 'aerial_duels_won_pct',
        
        # ===== GOALKEEPER SPECIFIC =====
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


# ====================================================================
# CONVENIENCE FUNCTIONS - Quick access interface
# ====================================================================

def get_player_season(player_name: str, league: str, season: str) -> Optional[Dict]:
    """Quick season stats extraction without verbose output."""
    return extract_season_stats(player_name, league, season, verbose=False)


def get_player_match(player_name: str, match_id: str, league: str, season: str) -> Optional[Dict]:
    """Quick match stats extraction without verbose output."""
    return extract_match_stats(player_name, match_id, league, season, verbose=False)


def get_squad_season(players: List[str], league: str, season: str) -> pd.DataFrame:
    """Quick squad season analysis without verbose output."""
    return extract_multiple_players_season(players, league, season, verbose=False)


def get_squad_match(players: List[str], match_id: str, league: str, season: str) -> pd.DataFrame:
    """Quick squad match analysis without verbose output."""
    return extract_multiple_players_match(players, match_id, league, season, verbose=False)


# ====================================================================
# EXPORT UTILITIES - Data persistence helpers
# ====================================================================

def export_to_csv(data: Union[Dict, pd.DataFrame], filename: str, 
                 include_timestamp: bool = True) -> str:
    """
    Export player data to CSV with automatic formatting.
    
    Args:
        data: Player statistics (Dict or DataFrame)
        filename: Output filename (without .csv extension)
        include_timestamp: Add timestamp to filename for version control
        
    Returns:
        Full path of created CSV file
        
    Example:
        >>> stats = get_player_season("Mbappé", "ESP-La Liga", "2024-25")
        >>> export_to_csv(stats, "mbappe_season_analysis")
    """
    import datetime
    
    # Convert Dict to DataFrame if needed
    if isinstance(data, dict):
        df = pd.DataFrame([data])
    else:
        df = data
    
    # Add timestamp to filename if requested
    if include_timestamp:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"{filename}_{timestamp}.csv"
    else:
        full_filename = f"{filename}.csv"
    
    # Export with proper encoding for international names
    df.to_csv(full_filename, index=False, encoding='utf-8')
    
    print(f"📊 Data exported to: {full_filename}")
    print(f"   Rows: {len(df)} | Columns: {len(df.columns)}")
    
    return full_filename


def quick_player_analysis(player_name: str, league: str, season: str, 
                         match_id: Optional[str] = None, export: bool = False) -> Dict:
    """
    One-function solution for complete player analysis.
    
    Perfect for quick analysis - gets both season and match data if available.
    
    Args:
        player_name: Player name
        league: League identifier
        season: Season identifier
        match_id: Optional specific match analysis
        export: Whether to export results to CSV
        
    Returns:
        Dictionary with season stats and optional match stats
        
    Example:
        >>> analysis = quick_player_analysis("Mbappé", "ESP-La Liga", "2024-25", 
        ...                                  match_id="c6b7a6e0", export=True)
    """
    print(f"🔍 Complete analysis for {player_name}")
    
    results = {}
    
    # Get season statistics
    season_stats = extract_season_stats(player_name, league, season, verbose=True)
    if season_stats:
        results['season_stats'] = season_stats
        print(f"✅ Season data: {len(season_stats)} fields")
    else:
        print("❌ Season data not found")
    
    # Get match statistics if requested
    if match_id:
        match_stats = extract_match_stats(player_name, match_id, league, season, verbose=True)
        if match_stats:
            results['match_stats'] = match_stats
            print(f"✅ Match data: {len(match_stats)} fields")
        else:
            print("❌ Match data not found")
    
    # Export if requested
    if export and results:
        if 'season_stats' in results:
            export_to_csv(results['season_stats'], 
                         f"{player_name.replace(' ', '_')}_season_{league}_{season}")
        
        if 'match_stats' in results:
            export_to_csv(results['match_stats'], 
                         f"{player_name.replace(' ', '_')}_match_{match_id}")
    
    return results


# ====================================================================
# BATCH PROCESSING - Advanced multi-player operations
# ====================================================================

def extract_full_squad_analysis(
    team_name: str,
    league: str, 
    season: str,
    player_list: Optional[List[str]] = None,
    export: bool = True,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Complete squad analysis with automatic player detection.
    
    If player_list is not provided, attempts to extract all players from team.
    Perfect for comprehensive team analysis.
    
    Args:
        team_name: Team name for filtering
        league: League identifier
        season: Season identifier  
        player_list: Optional specific players list
        export: Whether to export results
        verbose: Show detailed progress
        
    Returns:
        DataFrame with complete squad statistics
    """
    if verbose:
        print(f"🔍 Full squad analysis for {team_name}")
    
    # If no player list provided, extract all team players
    if player_list is None:
        if verbose:
            print("   Getting team roster...")
        
        # Get basic team stats to find all players
        fbref = FBref(leagues=[league], seasons=[season])
        try:
            team_stats = fbref.read_player_season_stats(stat_type='standard')
            team_players = team_stats[
                team_stats.index.get_level_values('team').str.contains(
                    team_name, case=False, na=False
                )
            ]
            player_list = team_players.index.get_level_values('player').unique().tolist()
            
            if verbose:
                print(f"   Found {len(player_list)} players in {team_name}")
        except Exception as e:
            if verbose:
                print(f"   Could not auto-detect players: {str(e)}")
            return pd.DataFrame()
    
    # Extract stats for all players
    squad_df = extract_multiple_players_season(
        players=player_list,
        league=league,
        season=season,
        verbose=verbose
    )
    
    # Export if requested
    if export and not squad_df.empty:
        filename = f"{team_name.replace(' ', '_')}_squad_{league}_{season}"
        export_to_csv(squad_df, filename)
    
    return squad_df

# ====================================================================
# TEAM DATA PROCESSING
# ====================================================================

def extract_team_season_stats(
    team_name: str, 
    league: str, 
    season: str,
    include_keeper_stats: bool = True,
    include_opponent_stats: bool = False,
    verbose: bool = False
) -> Optional[Dict]:
    """
    Extract complete season statistics for a single team.
    
    This is your go-to function for comprehensive team analysis.
    
    Args:
        team_name: Team name (e.g., "Real Madrid", "Manchester City")
        league: League ID (e.g., "ESP-La Liga", "ENG-Premier League")
        season: Season ID (e.g., "2024-25", "2023-24")
        include_keeper_stats: Include goalkeeper metrics if available
        include_opponent_stats: Include opponent statistics
        verbose: Show detailed extraction progress
        
    Returns:
        Dictionary with standardized team statistics or None if not found
        
    Example:
        >>> stats = extract_team_season_stats("Real Madrid", "ESP-La Liga", "2024-25")
        >>> print(f"Goals scored: {stats['goals']} | Goals conceded: {stats['goals_against']}")
    """
    if verbose:
        print(f"🔍 Extracting season data for {team_name}")
        print(f"   League: {league} | Season: {season}")
    
    # Configure stat types for comprehensive team analysis
    stat_types = [
        'standard',          # Core stats: goals, wins, points, goal difference
        'shooting',          # Shot metrics: attempts, accuracy, xG
        'passing',           # Pass metrics: completion, distance, key passes
        'passing_types',     # Pass types: live/dead, crosses, corners
        'goal_shot_creation', # Creation metrics: SCA, GCA
        'defense',           # Defensive actions: tackles, interceptions
        'possession',        # Ball control: touches, carries, take-ons
        'playing_time',      # Squad rotation and usage patterns
        'misc'               # Additional: fouls, cards, offsides
    ]
    
    if include_keeper_stats:
        stat_types.extend(['keeper', 'keeper_adv'])
    
    return _extract_team_data(
        team_name=team_name,
        league=league,
        season=season,
        stat_types=stat_types,
        include_opponent_stats=include_opponent_stats,
        verbose=verbose
    )
    
def extract_league_players(
    league: str,
    season: str,
    team_filter: Optional[str] = None,
    position_filter: Optional[str] = None,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract all player names from a league or specific team in a season.
    
    Perfect for building player databases and squad analysis preparation.
    
    Args:
        league: League ID (e.g., "ESP-La Liga", "ENG-Premier League")
        season: Season ID (e.g., "2024-25", "2023-24")
        team_filter: Optional team name to filter players (e.g., "Real Madrid")
        position_filter: Optional position filter (e.g., "FW", "MF", "DF", "GK")
        verbose: Show detailed extraction progress
        
    Returns:
        DataFrame with player names, teams, positions, and basic info
        
    Example:
        >>> # Get all La Liga players
        >>> all_players = extract_league_players("ESP-La Liga", "2024-25")
        >>> 
        >>> # Get only Real Madrid players
        >>> rm_players = extract_league_players("ESP-La Liga", "2024-25", 
        ...                                     team_filter="Real Madrid")
        >>> 
        >>> # Get all forwards in the league
        >>> forwards = extract_league_players("ESP-La Liga", "2024-25", 
        ...                                   position_filter="FW")
    """
    if verbose:
        print(f"🔍 Extracting player list from {league} {season}")
        if team_filter:
            print(f"   Team filter: {team_filter}")
        if position_filter:
            print(f"   Position filter: {position_filter}")
    
    try:
        # Initialize FBref extractor
        fbref = FBref(leagues=[league], seasons=[season])
        
        if verbose:
            print(f"   📊 Reading player database...")
        
        # Get basic player stats to extract names and info
        player_stats = fbref.read_player_season_stats(stat_type='standard')
        
        if player_stats is None or player_stats.empty:
            if verbose:
                print(f"   ❌ No players found in {league} {season}")
            return pd.DataFrame()
        
        # Extract player information
        players_df = player_stats.reset_index()
        
        # Apply team filter if specified
        if team_filter:
            original_count = len(players_df)
            players_df = players_df[
                players_df['team'].str.contains(team_filter, case=False, na=False)
            ]
            if verbose:
                print(f"   🔍 Team filter applied: {len(players_df)}/{original_count} players")
        
        # Apply position filter if specified
        if position_filter:
            original_count = len(players_df)
            # Handle multi-position players (e.g., "FW,MF")
            players_df = players_df[
                players_df['pos'].str.contains(position_filter, case=False, na=False)
            ]
            if verbose:
                print(f"   🔍 Position filter applied: {len(players_df)}/{original_count} players")
        
        # Select and standardize columns
        result_df = players_df[['player', 'team', 'league', 'season']].copy()
        
        # Add additional info if available
        if 'pos' in players_df.columns:
            result_df['position'] = players_df['pos']
        if 'age' in players_df.columns:
            result_df['age'] = players_df['age']
        if 'nation' in players_df.columns:
            result_df['nationality'] = players_df['nation']
        
        # Sort by team and player name for easy reading
        result_df = result_df.sort_values(['team', 'player'])
        
        if verbose:
            print(f"   ✅ SUCCESS: Found {len(result_df)} players")
            if len(result_df) > 0:
                teams_count = result_df['team'].nunique()
                print(f"   📊 Across {teams_count} teams")
        
        return result_df
        
    except Exception as e:
        if verbose:
            print(f"   ❌ EXTRACTION FAILED: {str(e)}")
        return pd.DataFrame()
    
def _extract_team_data(
    team_name: str,
    league: str,
    season: str,
    stat_types: List[str],
    include_opponent_stats: bool = False,
    verbose: bool = False
) -> Optional[Dict]:
    """
    Core team extraction engine that handles comprehensive team statistics.
    
    This unified approach ensures consistent data structure and processing
    for team-level analysis across different stat categories.
    """
    try:
        # Initialize FBref extractor
        fbref = FBref(leagues=[league], seasons=[season])
        
        team_data = {}
        basic_info = {}
        stats_extracted = 0
        
        # Process each stat type systematically
        for i, stat_type in enumerate(stat_types, 1):
            if verbose:
                print(f"   [{i}/{len(stat_types)}] Processing {stat_type}...")
            
            try:
                # Extract team season stats
                team_stats = fbref.read_team_season_stats(
                    stat_type=stat_type, 
                    opponent_stats=False
                )
                team_row = _find_team_in_stats(team_stats, team_name)
                
                if team_row is not None:
                    # Capture basic info on first successful extraction
                    if not basic_info:
                        basic_info = _extract_team_basic_info(
                            team_row, team_name, league, season
                        )
                    
                    # Extract all statistics from this stat type
                    cols_added = _process_team_columns(team_row, team_data, 'for')
                    stats_extracted += 1
                    
                    if verbose:
                        print(f"      ✅ Extracted {cols_added} fields from {stat_type}")
                else:
                    if verbose:
                        print(f"      ⚠️  Team not found in {stat_type}")
                
                # Extract opponent stats if requested
                if include_opponent_stats:
                    try:
                        opponent_stats = fbref.read_team_season_stats(
                            stat_type=stat_type, 
                            opponent_stats=True
                        )
                        opponent_row = _find_team_in_stats(opponent_stats, team_name)
                        
                        if opponent_row is not None:
                            cols_added = _process_team_columns(opponent_row, team_data, 'against')
                            if verbose:
                                print(f"      ✅ Extracted {cols_added} opponent fields from {stat_type}")
                    except Exception:
                        if verbose:
                            print(f"      ⚠️  Opponent stats not available for {stat_type}")
                        
            except Exception as e:
                if verbose:
                    print(f"      ❌ Error with {stat_type}: {str(e)[:50]}...")
                continue
        
        # Validate extraction success
        if not basic_info:
            if verbose:
                print(f"   ❌ Team '{team_name}' not found in {league} {season}")
            return None
        
        # Combine and standardize data
        final_data = {**basic_info, **team_data}
        standardized_data = _apply_team_stat_mapping(final_data)
        
        if verbose:
            print(f"   ✅ SUCCESS: Extracted {len(standardized_data)} total fields")
            print(f"   📊 Stats types processed: {stats_extracted}/{len(stat_types)}")
        
        return standardized_data
        
    except Exception as e:
        if verbose:
            print(f"   ❌ EXTRACTION FAILED: {str(e)}")
        return None
    
# ====================================================================
# TEAM DATA PROCESSING UTILITIES - Team-specific helpers
# ====================================================================

def _find_team_in_stats(stats: pd.DataFrame, team_name: str) -> Optional[pd.DataFrame]:
    """Search for team in statistics with flexible name matching."""
    if stats is None or stats.empty:
        return None
    
    # Generate comprehensive team name variations
    variations = _generate_team_name_variations(team_name)
    
    # Try exact matches first (most reliable)
    for variation in variations:
        matches = stats[
            stats.index.get_level_values('team').str.lower() == variation.lower()
        ]
        if not matches.empty:
            return matches
    
    # Then try partial matches (broader search)
    for variation in variations:
        matches = stats[
            stats.index.get_level_values('team').str.contains(
                variation, case=False, na=False, regex=False
            )
        ]
        if not matches.empty:
            return matches
    
    return None


def _generate_team_name_variations(team_name: str) -> List[str]:
    """
    Generate comprehensive team name variations for robust matching.
    
    Handles common team name formats, abbreviations, and international variations.
    """
    variations = [team_name]
    
    # Remove common suffixes
    suffixes_to_remove = [' FC', ' CF', ' United', ' City', ' Real', ' Club']
    for suffix in suffixes_to_remove:
        if team_name.endswith(suffix):
            variations.append(team_name[:-len(suffix)])
    
    # Add common abbreviations
    if ' ' in team_name:
        parts = team_name.split()
        # First letters of each word
        abbreviation = ''.join([part[0] for part in parts])
        variations.append(abbreviation)
        
        # First and last word
        if len(parts) > 1:
            variations.append(f"{parts[0]} {parts[-1]}")
    
    # Handle specific common variations
    common_variations = {
        'Real Madrid': ['Madrid', 'Real Madrid CF'],
        'Barcelona': ['Barça', 'FC Barcelona', 'Barca'],
        'Manchester United': ['Man United', 'Man Utd', 'United'],
        'Manchester City': ['Man City', 'City'],
        'Tottenham': ['Spurs', 'Tottenham Hotspur'],
        'Arsenal': ['Arsenal FC', 'Gunners']
    }
    
    if team_name in common_variations:
        variations.extend(common_variations[team_name])
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(variations))


def _extract_team_basic_info(
    team_row: pd.DataFrame,
    team_name: str,
    league: str,
    season: str
) -> Dict:
    """Extract and standardize basic team information."""
    return {
        'team_name': team_name,
        'league': league,
        'season': season,
        'official_team_name': team_row.index.get_level_values('team')[0]
    }


def _process_team_columns(team_row: pd.DataFrame, team_data: Dict, prefix: str) -> int:
    """Process all columns from a team row, adding prefix for opponent stats."""
    cols_added = 0
    
    for col in team_row.columns:
        clean_name = _clean_column_name(col)
        
        # Add prefix for opponent stats
        if prefix == 'against':
            clean_name = f"opponent_{clean_name}"
        
        value = team_row.iloc[0][col]
        
        # Avoid overwriting existing data (first occurrence wins)
        if clean_name not in team_data:
            team_data[clean_name] = value
            cols_added += 1
    
    return cols_added


def _apply_team_stat_mapping(team_data: Dict) -> Dict:
    """
    Apply standardized naming convention to all team statistics.
    
    Ensures consistent column names for team-level analysis.
    """
    team_stat_mapping = _get_team_stat_mapping()
    standardized_data = {}
    
    for original_name, value in team_data.items():
        standardized_name = team_stat_mapping.get(original_name, original_name)
        standardized_data[standardized_name] = value
    
    return standardized_data


def _get_team_stat_mapping() -> Dict[str, str]:
    """
    Comprehensive mapping for team-specific statistics.
    
    Extends the player mapping with team-specific metrics.
    """
    # Start with base player mapping
    base_mapping = _get_stat_mapping()
    
    # Add team-specific mappings
    team_specific = {
        # ===== TEAM PERFORMANCE =====
        'W': 'wins',
        'D': 'draws',
        'L': 'losses',
        'Pts': 'points',
        'Pts/MP': 'points_per_match',
        'GF': 'goals_for',
        'GA': 'goals_against',
        'GD': 'goal_difference',
        'xGF': 'expected_goals_for',
        'xGA': 'expected_goals_against',
        'xGD': 'expected_goal_difference',
        'xGD/90': 'expected_goal_difference_per_90',
        
        # ===== SQUAD STATS =====
        'Squad': 'squad_size',
        'Age': 'average_age',
        'Poss': 'possession_percentage',
        '# Pl': 'players_used',
        
        # ===== OPPONENT PREFIXED STATS =====
        'opponent_goals': 'goals_conceded',
        'opponent_shots': 'shots_conceded',
        'opponent_shots_on_target': 'shots_on_target_conceded',
        'opponent_passes_completed': 'opponent_passes_completed',
        'opponent_possession_percentage': 'opponent_possession_percentage'
    }
    
    # Combine mappings
    combined_mapping = {**base_mapping, **team_specific}
    return combined_mapping


# ====================================================================
# CONVENIENCE FUNCTIONS - Team-specific quick access
# ====================================================================

def get_team_season(team_name: str, league: str, season: str) -> Optional[Dict]:
    """Quick team season stats extraction without verbose output."""
    return extract_team_season_stats(team_name, league, season, verbose=False)


def get_all_players(league: str, season: str, team_filter: Optional[str] = None) -> pd.DataFrame:
    """Quick player list extraction without verbose output."""
    return extract_league_players(league, season, team_filter=team_filter, verbose=False)


def get_team_squad(team_name: str, league: str, season: str) -> pd.DataFrame:
    """Get all players from a specific team."""
    return extract_league_players(league, season, team_filter=team_name, verbose=False)


# ====================================================================
# TEAM BATCH PROCESSING - Advanced team operations
# ====================================================================

def extract_multiple_teams_season(
    teams: List[str],
    league: str,
    season: str,
    include_opponent_stats: bool = False,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract season statistics for multiple teams efficiently.
    
    Ideal for league analysis and team comparisons.
    
    Args:
        teams: List of team names
        league: League identifier
        season: Season identifier
        include_opponent_stats: Include opponent statistics
        verbose: Show extraction progress
        
    Returns:
        DataFrame with all teams' statistics, standardized column order
        
    Example:
        >>> teams = ["Real Madrid", "Barcelona", "Atletico Madrid"]
        >>> df = extract_multiple_teams_season(teams, "ESP-La Liga", "2024-25")
    """
    if verbose:
        print(f"🔍 Extracting season data for {len(teams)} teams from {league} {season}")
    
    all_data = []
    successful_extractions = 0
    
    for i, team_name in enumerate(teams, 1):
        if verbose:
            print(f"\n[{i}/{len(teams)}] Processing {team_name}")
        
        team_data = extract_team_season_stats(
            team_name, league, season, 
            include_opponent_stats=include_opponent_stats, 
            verbose=False
        )
        
        if team_data:
            all_data.append(team_data)
            successful_extractions += 1
        elif verbose:
            print(f"   ❌ Failed to extract data for {team_name}")
    
    if verbose:
        print(f"\n✅ SUMMARY: {successful_extractions}/{len(teams)} teams extracted successfully")
    
    # Create DataFrame with standardized column order
    df = pd.DataFrame(all_data) if all_data else pd.DataFrame()
    return _standardize_team_dataframe_columns(df)


def _standardize_team_dataframe_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure consistent column ordering for team DataFrames.
    
    Priority order: basic info → performance → advanced metrics → opponent stats
    """
    if df.empty:
        return df
    
    # Define standard column order for team DataFrames
    priority_columns = [
        # Basic identification
        'team_name', 'official_team_name', 'league', 'season',
        # Core performance metrics
        'wins', 'draws', 'losses', 'points', 'points_per_match',
        'goals_for', 'goals_against', 'goal_difference',
        'matches_played', 'players_used', 'average_age',
        # Advanced performance
        'expected_goals_for', 'expected_goals_against', 'expected_goal_difference',
        'possession_percentage', 'shots', 'shots_on_target',
        # Passing and creation
        'passes_completed', 'passes_attempted', 'pass_completion_pct',
        'key_passes', 'shot_creating_actions',
        # Defensive metrics
        'tackles', 'interceptions', 'clearances',
        # Disciplinary
        'yellow_cards', 'red_cards', 'fouls_committed'
    ]
    
    # Organize columns: priority first, then remaining alphabetically
    available_priority = [col for col in priority_columns if col in df.columns]
    remaining_columns = sorted([col for col in df.columns if col not in priority_columns])
    
    final_column_order = available_priority + remaining_columns
    
    return df[final_column_order]