# ====================================================================
# FootballDecoded - Understat Professional Advanced Metrics Extractor
# ====================================================================
# Specialized wrapper for extracting ALL advanced metrics from Understat
# that FBref doesn't provide. Maintains FBref-compatible format for easy merging.
# Focus: xGChain, xGBuildup, PPDA, OPPDA, Deep completions, Shot coordinates
# ====================================================================

import sys
import os
import pandas as pd
import numpy as np
import warnings
from typing import Dict, List, Optional, Union
from datetime import datetime

# Add extractors to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrappers import Understat

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore', category=FutureWarning)


# ====================================================================
# PLAYER METRICS EXTRACTION
# ====================================================================

def extract_player_season(
    player_name: str,
    league: str,
    season: str,
    verbose: bool = False
) -> Optional[Dict]:
    """
    Extract ALL available Understat player metrics for the season.
    
    Returns metrics NOT available in FBref:
    - xGChain, xGBuildup (build-up involvement)
    - Key passes (more detailed than FBref)
    - npxG + xA (non-penalty combined metric)
    - Position-specific analytics
    
    Args:
        player_name: Player name (e.g., "Haaland", "Mbappé")
        league: League ID ("ENG-Premier League", "ESP-La Liga", etc.)
        season: Season ID ("2023-24", "2024-25")
        verbose: Show extraction progress
        
    Returns:
        Dict with ALL Understat metrics in FBref-compatible format
    """
    if verbose:
        print(f"🎯 Extracting complete Understat metrics for {player_name}")
    
    try:
        understat = Understat(leagues=[league], seasons=[season])
        
        if verbose:
            print(f"   🔍 Searching Understat database...")
        
        stats = understat.read_player_season_stats()
        player_row = _find_player(stats, player_name)
        
        if player_row is None:
            if verbose:
                print(f"   ❌ {player_name} not found in Understat {league} {season}")
            return None
        
        # Extract basic identification
        basic_info = {
            'player_name': player_name,
            'league': league,
            'season': season,
            'team': player_row.index.get_level_values('team')[0],
            'official_player_name': player_row.index.get_level_values('player')[0]
        }
        
        # Extract ALL available Understat metrics
        understat_metrics = _extract_all_player_metrics(player_row)
        
        # Combine and standardize
        final_data = {**basic_info, **understat_metrics}
        
        if verbose:
            metrics_count = len([k for k in final_data.keys() if k.startswith('understat_')])
            print(f"   ✅ SUCCESS: Extracted {metrics_count} unique Understat metrics")
        
        return final_data
        
    except Exception as e:
        if verbose:
            print(f"   ❌ EXTRACTION FAILED: {str(e)}")
        return None


def extract_multiple_players(
    players: List[str],
    league: str,
    season: str,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract complete Understat metrics for multiple players efficiently.
    
    Args:
        players: List of player names
        league: League identifier
        season: Season identifier
        verbose: Show progress
        
    Returns:
        DataFrame with ALL Understat metrics for all players
    """
    if verbose:
        print(f"🎯 Extracting Understat data for {len(players)} players")
    
    all_data = []
    successful_extractions = 0
    
    for i, player_name in enumerate(players, 1):
        if verbose:
            print(f"[{i}/{len(players)}] {player_name}")
        
        player_data = extract_player_season(player_name, league, season, verbose=False)
        
        if player_data:
            all_data.append(player_data)
            successful_extractions += 1
        elif verbose:
            print(f"   ❌ Failed for {player_name}")
    
    if verbose:
        print(f"✅ Successfully extracted {successful_extractions}/{len(players)} players")
    
    df = pd.DataFrame(all_data) if all_data else pd.DataFrame()
    return _standardize_dataframe(df, 'player')


# ====================================================================
# TEAM METRICS EXTRACTION
# ====================================================================

def extract_team_season(
    team_name: str,
    league: str,
    season: str,
    verbose: bool = False
) -> Optional[Dict]:
    """
    Extract ALL available Understat team metrics for the season.
    
    Focus on advanced team metrics NOT in FBref:
    - PPDA (Passes Per Defensive Action)
    - OPPDA (Opponent PPDA - defensive intensity allowed)
    - Deep completions (final third entries)
    - xPoints (expected points from performance)
    - npxG team metrics (non-penalty expected goals)
    - xG difference per match
    
    Args:
        team_name: Team name (e.g., "Manchester City", "Real Madrid")
        league: League identifier
        season: Season identifier
        verbose: Show extraction progress
        
    Returns:
        Dict with ALL team-specific Understat metrics
    """
    if verbose:
        print(f"🎯 Extracting complete Understat team metrics for {team_name}")
    
    try:
        understat = Understat(leagues=[league], seasons=[season])
        
        if verbose:
            print(f"   🔍 Searching team database...")
        
        team_stats = understat.read_team_match_stats()
        team_matches = _find_team(team_stats, team_name)
        
        if team_matches is None or team_matches.empty:
            if verbose:
                print(f"   ❌ {team_name} not found in {league} {season}")
            return None
        
        # Basic identification
        basic_info = {
            'team_name': team_name,
            'league': league,
            'season': season,
            'official_team_name': team_matches.iloc[0]['home_team'] if 'home_team' in team_matches.columns else team_name
        }
        
        # Calculate ALL team metrics from match data
        team_metrics = _calculate_all_team_metrics(team_matches)
        
        # Combine and standardize
        final_data = {**basic_info, **team_metrics}
        
        if verbose:
            metrics_count = len([k for k in final_data.keys() if k.startswith('understat_')])
            print(f"   ✅ SUCCESS: Calculated {metrics_count} team metrics from {len(team_matches)} matches")
        
        return final_data
        
    except Exception as e:
        if verbose:
            print(f"   ❌ TEAM EXTRACTION FAILED: {str(e)}")
        return None


def extract_multiple_teams(
    teams: List[str],
    league: str,
    season: str,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract complete Understat team metrics for multiple teams efficiently.
    
    Args:
        teams: List of team names
        league: League identifier
        season: Season identifier
        verbose: Show progress
        
    Returns:
        DataFrame with ALL team metrics
    """
    if verbose:
        print(f"🎯 Extracting Understat team data for {len(teams)} teams")
    
    all_data = []
    successful_extractions = 0
    
    for i, team_name in enumerate(teams, 1):
        if verbose:
            print(f"[{i}/{len(teams)}] {team_name}")
        
        team_data = extract_team_season(team_name, league, season, verbose=False)
        
        if team_data:
            all_data.append(team_data)
            successful_extractions += 1
    
    if verbose:
        print(f"✅ Successfully extracted {successful_extractions}/{len(teams)} teams")
    
    df = pd.DataFrame(all_data) if all_data else pd.DataFrame()
    return _standardize_dataframe(df, 'team')


# ====================================================================
# SHOT EVENTS EXTRACTION
# ====================================================================

def extract_shot_events(
    match_id: int,
    league: str,
    season: str,
    player_filter: Optional[str] = None,
    team_filter: Optional[str] = None,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract ALL shot event data with complete tactical information.
    
    Returns shot events with:
    - Coordinates (x, y) and calculated distance/angle
    - Assist player information
    - Detailed shot zones classification
    - Body part, situation, outcome
    - xG values per shot
    
    Args:
        match_id: Understat match ID (integer)
        league: League identifier
        season: Season identifier
        player_filter: Optional player name filter
        team_filter: Optional team name filter
        verbose: Show detailed extraction progress
        
    Returns:
        DataFrame with complete shot events and tactical analysis
    """
    if verbose:
        print(f"🎯 Extracting complete shot events from match {match_id}")
    
    try:
        understat = Understat(leagues=[league], seasons=[season])
        
        shot_events = understat.read_shot_events(match_id=match_id)
        
        if shot_events is None or shot_events.empty:
            if verbose:
                print(f"   ❌ No shot events found for match {match_id}")
            return pd.DataFrame()
        
        if verbose:
            print(f"   📊 Raw data: {len(shot_events)} shots extracted")
        
        # Process and standardize ALL shot data
        standardized_events = _process_complete_shot_events(shot_events)
        
        # Apply filters if specified
        filtered_events = _apply_shot_filters(
            standardized_events, player_filter, team_filter, verbose
        )
        
        # Add match context
        if not filtered_events.empty:
            filtered_events['match_id'] = match_id
            filtered_events['data_source'] = 'understat'
        
        if verbose and not filtered_events.empty:
            total_shots = len(filtered_events)
            goals = len(filtered_events[filtered_events.get('is_goal', 0) == 1])
            avg_xg = filtered_events['shot_xg'].mean() if 'shot_xg' in filtered_events.columns else 0
            
            print(f"   ✅ SUCCESS: {total_shots} shot events with complete analytics")
            print(f"   📊 Goals: {goals} | Average xG: {avg_xg:.3f}")
        
        return filtered_events
        
    except Exception as e:
        if verbose:
            print(f"   ❌ SHOT EXTRACTION FAILED: {str(e)}")
        return pd.DataFrame()


# ====================================================================
# INTEGRATION UTILITIES
# ====================================================================

def merge_with_fbref(
    fbref_data: Union[pd.DataFrame, Dict],
    league: str,
    season: str,
    data_type: str = 'player',
    verbose: bool = False
) -> pd.DataFrame:
    """
    Merge FBref data with Understat metrics automatically.
    
    Args:
        fbref_data: FBref DataFrame or Dict
        league: League identifier  
        season: Season identifier
        data_type: 'player' or 'team'
        verbose: Show merge progress
        
    Returns:
        DataFrame with combined FBref + Understat metrics
    """
    if verbose:
        print("🔗 Merging FBref data with Understat metrics")
    
    # Convert to DataFrame if needed
    if isinstance(fbref_data, dict):
        fbref_df = pd.DataFrame([fbref_data])
    else:
        fbref_df = fbref_data.copy()
    
    if fbref_df.empty:
        if verbose:
            print("   ❌ No FBref data provided")
        return fbref_df
    
    # Extract entities and get Understat data
    if data_type == 'player':
        entities = fbref_df['player_name'].unique().tolist()
        understat_df = extract_multiple_players(entities, league, season, verbose=False)
        merge_key = 'player_name'
    else:  # team
        entities = fbref_df['team_name'].unique().tolist()
        understat_df = extract_multiple_teams(entities, league, season, verbose=False)
        merge_key = 'team_name'
    
    if understat_df.empty:
        if verbose:
            print("   ⚠️ No Understat data found")
        return fbref_df
    
    # Merge datasets
    merged_df = pd.merge(
        fbref_df,
        understat_df,
        on=[merge_key, 'league', 'season', 'team'],
        how='left',
        suffixes=('', '_understat_dup')
    )
    
    # Remove duplicate columns
    dup_cols = [col for col in merged_df.columns if col.endswith('_understat_dup')]
    merged_df = merged_df.drop(columns=dup_cols)
    
    if verbose:
        understat_cols = [col for col in merged_df.columns if col.startswith('understat_')]
        print(f"   ✅ SUCCESS: Added {len(understat_cols)} Understat metrics")
    
    return merged_df


# ====================================================================
# CORE PROCESSING ENGINE
# ====================================================================

def _find_player(stats: pd.DataFrame, player_name: str) -> Optional[pd.DataFrame]:
    """Find player with flexible name matching for Understat format."""
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


def _find_team(stats: pd.DataFrame, team_name: str) -> Optional[pd.DataFrame]:
    """Find team with flexible name matching for Understat format."""
    if stats is None or stats.empty:
        return None
    
    variations = _generate_team_variations(team_name)
    
    # Check both home_team and away_team columns
    for variation in variations:
        home_matches = stats[
            stats['home_team'].str.contains(variation, case=False, na=False, regex=False)
        ]
        away_matches = stats[
            stats['away_team'].str.contains(variation, case=False, na=False, regex=False)
        ]
        
        if not home_matches.empty or not away_matches.empty:
            return pd.concat([home_matches, away_matches]).drop_duplicates()
    
    return None


def _generate_name_variations(player_name: str) -> List[str]:
    """Generate name variations for Understat's naming conventions."""
    variations = [player_name]
    
    # Remove accents (Understat uses ASCII)
    clean_name = (player_name
                  .replace('é', 'e').replace('ñ', 'n').replace('í', 'i')
                  .replace('ó', 'o').replace('á', 'a').replace('ú', 'u')
                  .replace('ç', 'c').replace('ü', 'u').replace('ø', 'o'))
    if clean_name != player_name:
        variations.append(clean_name)
    
    # Add name components
    if ' ' in player_name:
        parts = player_name.split()
        variations.extend(parts)
        if len(parts) >= 2:
            variations.append(f"{parts[0]} {parts[-1]}")
    
    # Common Understat variations
    mappings = {
        "Kylian Mbappé": ["Kylian Mbappe", "K. Mbappe", "Mbappe"],
        "Erling Haaland": ["E. Haaland", "Haaland", "Erling Braut Haaland"],
        "Vinicius Jr": ["Vinicius Junior", "Vinicius", "V. Junior"]
    }
    
    if player_name in mappings:
        variations.extend(mappings[player_name])
    
    return list(dict.fromkeys(variations))


def _generate_team_variations(team_name: str) -> List[str]:
    """Generate team name variations for Understat format."""
    variations = [team_name]
    
    # Remove common suffixes
    suffixes = [' FC', ' CF', ' United', ' City']
    for suffix in suffixes:
        if team_name.endswith(suffix):
            variations.append(team_name[:-len(suffix)])
    
    # Common team mappings
    mappings = {
        'Manchester United': ['Manchester Utd', 'Man United'],
        'Manchester City': ['Man City'],
        'Tottenham': ['Tottenham Hotspur'],
        'Brighton': ['Brighton and Hove Albion'],
        'Newcastle': ['Newcastle United'],
        'Real Madrid': ['Madrid'],
        'Barcelona': ['Barça', 'FC Barcelona']
    }
    
    if team_name in mappings:
        variations.extend(mappings[team_name])
    
    return list(dict.fromkeys(variations))


def _extract_all_player_metrics(player_row: pd.DataFrame) -> Dict:
    """Extract ALL available Understat player metrics."""
    understat_data = {}
    
    # Core Understat-specific metrics (NOT in FBref)
    core_metrics = {
        'xg_chain': 'understat_xg_chain',              # Build-up involvement xG
        'xg_buildup': 'understat_xg_buildup',          # Build-up creation xG
        'key_passes': 'understat_key_passes',          # More detailed than FBref
        'np_xg': 'understat_np_xg',                    # Non-penalty xG
        'xa': 'understat_xa',                          # Expected assists
        'xg': 'understat_xg',                          # Total xG
        'np_goals': 'understat_np_goals',              # Non-penalty goals
        'position_id': 'understat_position_id',        # Numerical position
        'player_id': 'understat_player_id',            # Player ID for cross-ref
        'team_id': 'understat_team_id'                 # Team ID for cross-ref
    }
    
    # Validation metrics (compare with FBref)
    validation_metrics = {
        'matches': 'understat_matches',
        'minutes': 'understat_minutes',
        'goals': 'understat_goals',
        'assists': 'understat_assists',
        'shots': 'understat_shots',
        'yellow_cards': 'understat_yellow_cards',
        'red_cards': 'understat_red_cards'
    }
    
    # Extract all available metrics
    all_metrics = {**core_metrics, **validation_metrics}
    
    for col in player_row.columns:
        if col in all_metrics:
            value = player_row.iloc[0][col]
            understat_data[all_metrics[col]] = value if pd.notna(value) else None
    
    # Calculate derived metrics unique to Understat
    _add_derived_player_metrics(understat_data)
    
    return understat_data


def _add_derived_player_metrics(data: Dict) -> None:
    """Add calculated metrics unique to Understat analysis."""
    # Non-penalty xG + xA combined
    if data.get('understat_np_xg') and data.get('understat_xa'):
        np_xg = data['understat_np_xg'] or 0
        xa = data['understat_xa'] or 0
        data['understat_npxg_plus_xa'] = np_xg + xa
    
    # Goals vs xG efficiency ratio
    if data.get('understat_goals') and data.get('understat_xg'):
        goals = data['understat_goals'] or 0
        xg = data['understat_xg'] or 0
        if xg > 0:
            data['understat_goals_vs_xg_ratio'] = goals / xg
    
    # Key passes per 90 minutes
    if data.get('understat_key_passes') and data.get('understat_minutes'):
        key_passes = data['understat_key_passes'] or 0
        minutes = data['understat_minutes'] or 0
        if minutes > 0:
            data['understat_key_passes_per_90'] = (key_passes / minutes) * 90
    
    # Build-up involvement percentage
    if data.get('understat_xg_chain') and data.get('understat_xg'):
        xg_chain = data['understat_xg_chain'] or 0
        total_xg = data['understat_xg'] or 0
        if total_xg > 0:
            data['understat_buildup_involvement_pct'] = (xg_chain / total_xg) * 100


def _calculate_all_team_metrics(team_matches: pd.DataFrame) -> Dict:
    """Calculate ALL available team metrics from Understat match data."""
    team_metrics = {}
    
    total_matches = len(team_matches)
    team_metrics['understat_matches_analyzed'] = total_matches
    
    if total_matches == 0:
        return team_metrics
    
    # PPDA Metrics - Core defensive metric
    ppda_values = _extract_column_values(team_matches, ['home_ppda', 'away_ppda'])
    if ppda_values:
        team_metrics['understat_ppda_avg'] = np.mean(ppda_values)
        team_metrics['understat_ppda_min'] = np.min(ppda_values)
        team_metrics['understat_ppda_max'] = np.max(ppda_values)
        team_metrics['understat_ppda_std'] = np.std(ppda_values)
    
    # Deep Completions - Final third entries
    deep_values = _extract_column_values(team_matches, ['home_deep_completions', 'away_deep_completions'])
    if deep_values:
        team_metrics['understat_deep_completions_total'] = np.sum(deep_values)
        team_metrics['understat_deep_completions_avg'] = np.mean(deep_values)
        team_metrics['understat_deep_completions_max'] = np.max(deep_values)
    
    # Expected Points - Performance analysis
    xpts_values = _extract_column_values(team_matches, ['home_expected_points', 'away_expected_points'])
    if xpts_values:
        team_metrics['understat_expected_points_total'] = np.sum(xpts_values)
        team_metrics['understat_expected_points_avg'] = np.mean(xpts_values)
    
    # Expected Goals For
    xgf_values = _extract_column_values(team_matches, ['home_xg', 'away_xg'])
    if xgf_values:
        team_metrics['understat_xg_for_total'] = np.sum(xgf_values)
        team_metrics['understat_xg_for_avg'] = np.mean(xgf_values)
        team_metrics['understat_xg_for_max'] = np.max(xgf_values)
    
    # Non-penalty xG metrics
    np_xg_values = _extract_column_values(team_matches, ['home_np_xg', 'away_np_xg'])
    if np_xg_values:
        team_metrics['understat_np_xg_total'] = np.sum(np_xg_values)
        team_metrics['understat_np_xg_avg'] = np.mean(np_xg_values)
    
    # Goals scored (for validation)
    goals_values = _extract_column_values(team_matches, ['home_goals', 'away_goals'])
    if goals_values:
        team_metrics['understat_goals_scored_total'] = np.sum(goals_values)
        team_metrics['understat_goals_scored_avg'] = np.mean(goals_values)
    
    # Points earned (for validation)
    points_values = _extract_column_values(team_matches, ['home_points', 'away_points'])
    if points_values:
        team_metrics['understat_points_total'] = np.sum(points_values)
        team_metrics['understat_points_avg'] = np.mean(points_values)
    
    # Add derived analytics
    _add_derived_team_metrics(team_metrics)
    
    return team_metrics


def _extract_column_values(df: pd.DataFrame, columns: List[str]) -> List[float]:
    """Extract and combine values from multiple columns."""
    values = []
    for col in columns:
        if col in df.columns:
            col_values = df[col].dropna()
            values.extend(col_values.tolist())
    return values


def _add_derived_team_metrics(metrics: Dict) -> None:
    """Add calculated team metrics unique to analysis."""
    # Points vs xPoints performance
    if 'understat_points_total' in metrics and 'understat_expected_points_total' in metrics:
        points_diff = metrics['understat_points_total'] - metrics['understat_expected_points_total']
        metrics['understat_points_vs_xpoints_difference'] = points_diff
    
    # Goals vs xG performance
    if 'understat_goals_scored_total' in metrics and 'understat_xg_for_total' in metrics:
        goals_diff = metrics['understat_goals_scored_total'] - metrics['understat_xg_for_total']
        metrics['understat_goals_vs_xg_difference'] = goals_diff


def _process_complete_shot_events(shot_events: pd.DataFrame) -> pd.DataFrame:
    """Process and standardize ALL shot event data with complete analytics."""
    if shot_events.empty:
        return shot_events
    
    df = shot_events.copy()
    
    # Comprehensive column mapping
    column_mapping = {
        'xg': 'shot_xg',
        'location_x': 'shot_location_x',
        'location_y': 'shot_location_y',
        'body_part': 'shot_body_part',
        'situation': 'shot_situation',
        'result': 'shot_result',
        'minute': 'shot_minute',
        'player': 'shot_player',
        'team': 'shot_team',
        'date': 'shot_date',
        'shot_id': 'shot_id',
        'player_id': 'shot_player_id',
        'team_id': 'shot_team_id',
        'assist_player': 'assist_player_name',
        'assist_player_id': 'assist_player_id'
    }
    
    # Apply renaming
    rename_dict = {k: v for k, v in column_mapping.items() if k in df.columns}
    df = df.rename(columns=rename_dict)
    
    # Convert numeric columns
    numeric_cols = ['shot_xg', 'shot_location_x', 'shot_location_y', 'shot_minute']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Add comprehensive analysis fields
    _add_shot_analytics(df)
    
    return df


def _add_shot_analytics(df: pd.DataFrame) -> None:
    """Add ALL calculated shot analytics fields."""
    # Outcome analysis
    if 'shot_result' in df.columns:
        df['is_goal'] = (df['shot_result'] == 'Goal').astype(int)
        df['is_on_target'] = df['shot_result'].isin(['Goal', 'Saved Shot']).astype(int)
        df['is_blocked'] = (df['shot_result'] == 'Blocked Shot').astype(int)
        df['is_missed'] = (df['shot_result'] == 'Missed Shot').astype(int)
        df['is_post'] = (df['shot_result'] == 'Shot On Post').astype(int)
    
    # Spatial analysis
    if 'shot_location_x' in df.columns and 'shot_location_y' in df.columns:
        df['shot_zone'] = _classify_shot_zones(df['shot_location_x'], df['shot_location_y'])
        df['shot_distance_to_goal'] = _calculate_shot_distance(df['shot_location_x'], df['shot_location_y'])
        df['shot_angle'] = _calculate_shot_angle(df['shot_location_x'], df['shot_location_y'])
    
    # Time analysis
    if 'shot_minute' in df.columns:
        df['shot_period'] = df['shot_minute'].apply(
            lambda x: 'First Half' if x <= 45 else 'Second Half' if x <= 90 else 'Extra Time'
        )
    
    # Assist analysis
    if 'assist_player_name' in df.columns:
        df['is_assisted'] = (~df['assist_player_name'].isna()).astype(int)
        df['is_individual_play'] = (df['assist_player_name'].isna()).astype(int)


def _classify_shot_zones(x_coords: pd.Series, y_coords: pd.Series) -> pd.Series:
    """Classify shots into detailed tactical zones."""
    zones = []
    
    for x, y in zip(x_coords, y_coords):
        if pd.isna(x) or pd.isna(y):
            zones.append('Unknown')
            continue
        
        x_pct = float(x) * 100
        y_pct = float(y) * 100
        
        # Tactical zone classification
        if x_pct >= 88:  # 6-yard box area
            zones.append('Central 6-yard Box' if 35 <= y_pct <= 65 else 'Wide 6-yard Box')
        elif x_pct >= 83:  # Penalty box close
            if 40 <= y_pct <= 60:
                zones.append('Central Penalty Box')
            elif 25 <= y_pct <= 75:
                zones.append('Wide Penalty Box')
            else:
                zones.append('Very Wide Penalty Box')
        elif x_pct >= 67:  # Full penalty area
            zones.append('Central Penalty Area Edge' if 35 <= y_pct <= 65 else 'Wide Penalty Area')
        elif x_pct >= 50:  # Outside box but attacking third
            if 40 <= y_pct <= 60:
                zones.append('Central Outside Box')
            elif 25 <= y_pct <= 75:
                zones.append('Wide Outside Box')
            else:
                zones.append('Very Wide Attacking Third')
        elif x_pct >= 33:  # Middle third
            zones.append('Middle Third')
        else:  # Long range
            zones.append('Long Range')
    
    return pd.Series(zones, index=x_coords.index)


def _calculate_shot_distance(x_coords: pd.Series, y_coords: pd.Series) -> pd.Series:
    """Calculate distance from shot location to goal center in meters."""
    distances = []
    goal_x, goal_y = 1.0, 0.5  # Goal center in Understat coordinates
    
    for x, y in zip(x_coords, y_coords):
        if pd.isna(x) or pd.isna(y):
            distances.append(None)
            continue
        
        # Euclidean distance to goal (approximate meters)
        distance = np.sqrt((float(x) - goal_x)**2 + (float(y) - goal_y)**2)
        distance_meters = distance * 100  # Convert to approximate meters
        distances.append(distance_meters)
    
    return pd.Series(distances, index=x_coords.index)


def _calculate_shot_angle(x_coords: pd.Series, y_coords: pd.Series) -> pd.Series:
    """Calculate shot angle to goal in degrees."""
    angles = []
    goal_left_y, goal_right_y = 0.45, 0.55  # Goal posts
    goal_x = 1.0
    
    for x, y in zip(x_coords, y_coords):
        if pd.isna(x) or pd.isna(y):
            angles.append(None)
            continue
        
        x_pos, y_pos = float(x), float(y)
        
        # Vectors to goal posts
        vec1 = np.array([goal_x - x_pos, goal_left_y - y_pos])
        vec2 = np.array([goal_x - x_pos, goal_right_y - y_pos])
        
        # Calculate angle between vectors
        cos_angle = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        cos_angle = np.clip(cos_angle, -1, 1)
        angle_radians = np.arccos(cos_angle)
        angle_degrees = np.degrees(angle_radians)
        
        angles.append(angle_degrees)
    
    return pd.Series(angles, index=x_coords.index)


def _apply_shot_filters(
    df: pd.DataFrame, 
    player_filter: Optional[str], 
    team_filter: Optional[str], 
    verbose: bool
) -> pd.DataFrame:
    """Apply player and team filters to shot events."""
    filtered_df = df.copy()
    
    # Player filter
    if player_filter and 'shot_player' in filtered_df.columns:
        if verbose:
            print(f"   🎯 Applying player filter: {player_filter}")
        
        player_variations = _generate_name_variations(player_filter)
        mask = pd.Series([False] * len(filtered_df))
        
        for variation in player_variations:
            exact_matches = filtered_df['shot_player'].str.lower() == variation.lower()
            partial_matches = filtered_df['shot_player'].str.contains(
                variation, case=False, na=False, regex=False
            )
            mask |= exact_matches | partial_matches
        
        filtered_df = filtered_df[mask]
        
        if verbose:
            print(f"   ✅ Player filter applied: {len(filtered_df)} shots found")
    
    # Team filter
    if team_filter and 'shot_team' in filtered_df.columns:
        if verbose:
            print(f"   🏟️ Applying team filter: {team_filter}")
        
        team_variations = _generate_team_variations(team_filter)
        mask = pd.Series([False] * len(filtered_df))
        
        for variation in team_variations:
            exact_matches = filtered_df['shot_team'].str.lower() == variation.lower()
            partial_matches = filtered_df['shot_team'].str.contains(
                variation, case=False, na=False, regex=False
            )
            mask |= exact_matches | partial_matches
        
        filtered_df = filtered_df[mask]
        
        if verbose:
            print(f"   ✅ Team filter applied: {len(filtered_df)} shots")
    
    return filtered_df


def _standardize_dataframe(df: pd.DataFrame, data_type: str) -> pd.DataFrame:
    """Ensure proper column ordering for integration with FBref."""
    if df.empty:
        return df
    
    if data_type == 'player':
        priority_columns = [
            'player_name', 'team', 'league', 'season', 'official_player_name',
            'understat_xg_chain', 'understat_xg_buildup', 'understat_npxg_plus_xa',
            'understat_key_passes', 'understat_np_xg', 'understat_xa', 'understat_xg'
        ]
    else:  # team
        priority_columns = [
            'team_name', 'league', 'season', 'official_team_name',
            'understat_ppda_avg', 'understat_deep_completions_total',
            'understat_expected_points_total', 'understat_xg_for_total'
        ]
    
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
# QUICK ACCESS FUNCTIONS
# ====================================================================

def get_player(player_name: str, league: str, season: str) -> Optional[Dict]:
    """Quick player metrics extraction."""
    return extract_player_season(player_name, league, season, verbose=False)


def get_team(team_name: str, league: str, season: str) -> Optional[Dict]:
    """Quick team metrics extraction."""
    return extract_team_season(team_name, league, season, verbose=False)


def get_squad(players: List[str], league: str, season: str) -> pd.DataFrame:
    """Quick squad metrics extraction."""
    return extract_multiple_players(players, league, season, verbose=False)


def get_shots(match_id: int, league: str, season: str, 
              player_filter: Optional[str] = None) -> pd.DataFrame:
    """Quick shot events extraction."""
    return extract_shot_events(match_id, league, season, player_filter, verbose=False)