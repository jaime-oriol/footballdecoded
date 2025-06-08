# ====================================================================
# FootballDecoded - Understat Optimized Advanced Metrics Extractor
# ====================================================================
# Compacto y eficiente para extraer SOLO métricas únicas de Understat
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

warnings.filterwarnings('ignore', category=FutureWarning)

# ====================================================================
# CORE ENGINE - UNIFIED EXTRACTION
# ====================================================================

def extract_data(
    entity_name: str,
    entity_type: str,  # 'player' or 'team'
    league: str,
    season: str,
    verbose: bool = False
) -> Optional[Dict]:
    """
    Unified extraction engine for Understat advanced metrics.
    
    Args:
        entity_name: Player or team name
        entity_type: 'player' or 'team'
        league: League ID
        season: Season ID
        verbose: Show progress
        
    Returns:
        Dict with ALL unique Understat metrics (NOT in FBref)
    """
    if verbose:
        print(f"🎯 Extracting Understat metrics for {entity_name}")
    
    try:
        understat = Understat(leagues=[league], seasons=[season])
        
        if entity_type == 'player':
            stats = understat.read_player_season_stats()
            entity_row = _find_entity(stats, entity_name, 'player')
            
            if entity_row is None:
                if verbose:
                    print(f"   ❌ {entity_name} not found in Understat")
                return None
            
            # Extract basic info
            basic_info = {
                'player_name': entity_name,
                'league': league,
                'season': season,
                'team': entity_row.index.get_level_values('team')[0],
                'official_player_name': entity_row.index.get_level_values('player')[0]
            }
            
            # Extract ONLY Understat-specific metrics
            understat_metrics = _extract_player_metrics(entity_row)
            
        else:  # team
            team_stats = understat.read_team_match_stats()
            team_matches = _find_team_matches(team_stats, entity_name)
            
            if team_matches is None or team_matches.empty:
                if verbose:
                    print(f"   ❌ {entity_name} not found in Understat")
                return None
            
            # Extract basic info
            basic_info = {
                'team_name': entity_name,
                'league': league,
                'season': season,
                'official_team_name': team_matches.iloc[0]['home_team'] if 'home_team' in team_matches.columns else entity_name
            }
            
            # Calculate ONLY Understat-specific team metrics
            understat_metrics = _calculate_team_metrics(team_matches)
        
        # Combine data
        final_data = {**basic_info, **understat_metrics}
        
        if verbose:
            metrics_count = len([k for k in final_data.keys() if k.startswith('understat_')])
            print(f"   ✅ SUCCESS: Extracted {metrics_count} unique Understat metrics")
        
        return final_data
        
    except Exception as e:
        if verbose:
            print(f"   ❌ EXTRACTION FAILED: {str(e)}")
        return None


# ====================================================================
# BATCH EXTRACTION
# ====================================================================

def extract_multiple(
    entities: List[str],
    entity_type: str,
    league: str,
    season: str,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract multiple entities efficiently.
    
    Args:
        entities: List of entity names
        entity_type: 'player' or 'team'
        league: League identifier
        season: Season identifier
        verbose: Show progress
        
    Returns:
        DataFrame with all entities' Understat metrics
    """
    if verbose:
        print(f"🎯 Extracting Understat data for {len(entities)} {entity_type}s")
    
    all_data = []
    successful = 0
    
    for i, entity_name in enumerate(entities, 1):
        if verbose:
            print(f"[{i}/{len(entities)}] {entity_name}")
        
        entity_data = extract_data(entity_name, entity_type, league, season, verbose=False)
        
        if entity_data:
            all_data.append(entity_data)
            successful += 1
        elif verbose:
            print(f"   ❌ Failed for {entity_name}")
    
    if verbose:
        print(f"✅ Successfully extracted {successful}/{len(entities)} {entity_type}s")
    
    df = pd.DataFrame(all_data) if all_data else pd.DataFrame()
    return _standardize_dataframe(df, entity_type)


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
    Extract shot events with complete spatial and tactical information.
    
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
        print(f"🎯 Extracting shot events from match {match_id}")
    
    try:
        understat = Understat(leagues=[league], seasons=[season])
        shot_events = understat.read_shot_events(match_id=match_id)
        
        if shot_events is None or shot_events.empty:
            if verbose:
                print(f"   ❌ No shot events found")
            return pd.DataFrame()
        
        if verbose:
            print(f"   📊 Raw data: {len(shot_events)} shots extracted")
        
        # Process and enhance shot data
        enhanced_events = _process_shot_events(shot_events)
        
        # Apply filters
        filtered_events = _apply_shot_filters(enhanced_events, player_filter, team_filter, verbose)
        
        # Add match context
        if not filtered_events.empty:
            filtered_events['match_id'] = match_id
            filtered_events['data_source'] = 'understat'
        
        if verbose and not filtered_events.empty:
            total_shots = len(filtered_events)
            goals = len(filtered_events[filtered_events.get('is_goal', 0) == 1])
            avg_xg = filtered_events['shot_xg'].mean() if 'shot_xg' in filtered_events.columns else 0
            
            print(f"   ✅ SUCCESS: {total_shots} shot events with analytics")
            print(f"   📊 Goals: {goals} | Average xG: {avg_xg:.3f}")
        
        return filtered_events
        
    except Exception as e:
        if verbose:
            print(f"   ❌ SHOT EXTRACTION FAILED: {str(e)}")
        return pd.DataFrame()


# ====================================================================
# INTEGRATION WITH FBREF
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
        understat_df = extract_multiple(entities, 'player', league, season, verbose=False)
        merge_key = 'player_name'
    else:  # team
        entities = fbref_df['team_name'].unique().tolist()
        understat_df = extract_multiple(entities, 'team', league, season, verbose=False)
        merge_key = 'team_name'
    
    if understat_df.empty:
        if verbose:
            print("   ⚠️ No Understat data found")
        return fbref_df
    
    # Merge datasets
    merged_df = pd.merge(
        fbref_df, understat_df,
        on=[merge_key, 'league', 'season', 'team'],
        how='left', suffixes=('', '_understat_dup')
    )
    
    # Remove duplicate columns
    dup_cols = [col for col in merged_df.columns if col.endswith('_understat_dup')]
    merged_df = merged_df.drop(columns=dup_cols)
    
    if verbose:
        understat_cols = [col for col in merged_df.columns if col.startswith('understat_')]
        print(f"   ✅ SUCCESS: Added {len(understat_cols)} Understat metrics")
    
    return merged_df


# ====================================================================
# CORE PROCESSING FUNCTIONS
# ====================================================================

def _find_entity(stats: pd.DataFrame, entity_name: str, entity_type: str) -> Optional[pd.DataFrame]:
    """Find entity with flexible name matching."""
    if stats is None or stats.empty:
        return None
    
    variations = _generate_name_variations(entity_name)
    index_level = entity_type
    
    # Try exact matches first
    for variation in variations:
        matches = stats[stats.index.get_level_values(index_level).str.lower() == variation.lower()]
        if not matches.empty:
            return matches
    
    # Try partial matches
    for variation in variations:
        matches = stats[stats.index.get_level_values(index_level).str.contains(
            variation, case=False, na=False, regex=False)]
        if not matches.empty:
            return matches
    
    return None


def _find_team_matches(stats: pd.DataFrame, team_name: str) -> Optional[pd.DataFrame]:
    """Find team matches in Understat format."""
    if stats is None or stats.empty:
        return None
    
    variations = _generate_name_variations(team_name)
    
    # Check both home_team and away_team columns
    for variation in variations:
        home_matches = stats[stats['home_team'].str.contains(variation, case=False, na=False, regex=False)]
        away_matches = stats[stats['away_team'].str.contains(variation, case=False, na=False, regex=False)]
        
        if not home_matches.empty or not away_matches.empty:
            return pd.concat([home_matches, away_matches]).drop_duplicates()
    
    return None


def _generate_name_variations(name: str) -> List[str]:
    """Generate name variations for Understat's naming conventions."""
    variations = [name]
    
    # Remove accents (Understat uses ASCII)
    clean_name = (name.replace('é', 'e').replace('ñ', 'n').replace('í', 'i')
                  .replace('ó', 'o').replace('á', 'a').replace('ú', 'u')
                  .replace('ç', 'c').replace('ü', 'u').replace('ø', 'o'))
    if clean_name != name:
        variations.append(clean_name)
    
    # Add name components
    if ' ' in name:
        parts = name.split()
        variations.extend(parts)
        if len(parts) >= 2:
            variations.append(f"{parts[0]} {parts[-1]}")
    
    # Common variations
    mappings = {
        "Kylian Mbappé": ["Kylian Mbappe", "K. Mbappe", "Mbappe"],
        "Erling Haaland": ["E. Haaland", "Haaland"],
        "Vinicius Jr": ["Vinicius Junior", "Vinicius"],
        'Manchester United': ['Manchester Utd', 'Man United'],
        'Manchester City': ['Man City'],
        'Tottenham': ['Tottenham Hotspur'],
        'Real Madrid': ['Madrid'],
        'Barcelona': ['Barça', 'FC Barcelona']
    }
    
    if name in mappings:
        variations.extend(mappings[name])
    
    return list(dict.fromkeys(variations))


def _extract_player_metrics(player_row: pd.DataFrame) -> Dict:
    """Extract ONLY Understat-specific player metrics (NOT in FBref)."""
    understat_data = {}
    
    # Core Understat-exclusive metrics
    core_metrics = {
        'xg_chain': 'understat_xg_chain',              # Build-up involvement xG
        'xg_buildup': 'understat_xg_buildup',          # Build-up creation xG
        'key_passes': 'understat_key_passes',          # More detailed than FBref
        'np_xg': 'understat_np_xg',                    # Non-penalty xG
        'xa': 'understat_xa',                          # Expected assists
        'np_goals': 'understat_np_goals',              # Non-penalty goals
        'player_id': 'understat_player_id',            # Player ID
        'team_id': 'understat_team_id'                 # Team ID
    }
    
    # Extract metrics
    for col in player_row.columns:
        if col in core_metrics:
            value = player_row.iloc[0][col]
            understat_data[core_metrics[col]] = value if pd.notna(value) else None
    
    # Add derived metrics
    _add_derived_player_metrics(understat_data)
    
    return understat_data


def _add_derived_player_metrics(data: Dict) -> None:
    """Add calculated metrics unique to Understat analysis."""
    # Non-penalty xG + xA combined
    if data.get('understat_np_xg') and data.get('understat_xa'):
        np_xg = data['understat_np_xg'] or 0
        xa = data['understat_xa'] or 0
        data['understat_npxg_plus_xa'] = np_xg + xa
    
    # Build-up involvement percentage
    if data.get('understat_xg_chain') and data.get('understat_np_xg'):
        xg_chain = data['understat_xg_chain'] or 0
        np_xg = data['understat_np_xg'] or 0
        if np_xg > 0:
            data['understat_buildup_involvement_pct'] = (xg_chain / np_xg) * 100


def _calculate_team_metrics(team_matches: pd.DataFrame) -> Dict:
    """Calculate ONLY Understat-specific team metrics."""
    team_metrics = {}
    
    total_matches = len(team_matches)
    team_metrics['understat_matches_analyzed'] = total_matches
    
    if total_matches == 0:
        return team_metrics
    
    # PPDA Metrics - Core defensive metric
    ppda_values = _extract_column_values(team_matches, ['home_ppda', 'away_ppda'])
    if ppda_values:
        team_metrics['understat_ppda_avg'] = np.mean(ppda_values)
        team_metrics['understat_ppda_std'] = np.std(ppda_values)
    
    # Deep Completions - Final third entries
    deep_values = _extract_column_values(team_matches, ['home_deep_completions', 'away_deep_completions'])
    if deep_values:
        team_metrics['understat_deep_completions_total'] = np.sum(deep_values)
        team_metrics['understat_deep_completions_avg'] = np.mean(deep_values)
    
    # Expected Points - Performance analysis
    xpts_values = _extract_column_values(team_matches, ['home_expected_points', 'away_expected_points'])
    if xpts_values:
        team_metrics['understat_expected_points_total'] = np.sum(xpts_values)
        team_metrics['understat_expected_points_avg'] = np.mean(xpts_values)
    
    # Non-penalty xG metrics
    np_xg_values = _extract_column_values(team_matches, ['home_np_xg', 'away_np_xg'])
    if np_xg_values:
        team_metrics['understat_np_xg_total'] = np.sum(np_xg_values)
        team_metrics['understat_np_xg_avg'] = np.mean(np_xg_values)
    
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
    if 'understat_expected_points_total' in metrics:
        xpts = metrics['understat_expected_points_total']
        if xpts > 0:
            metrics['understat_points_efficiency'] = xpts / metrics.get('understat_matches_analyzed', 1)


def _process_shot_events(shot_events: pd.DataFrame) -> pd.DataFrame:
    """Process and enhance shot event data."""
    if shot_events.empty:
        return shot_events
    
    df = shot_events.copy()
    
    # Rename columns to standard format
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
        'assist_player': 'assist_player_name'
    }
    
    # Apply renaming
    rename_dict = {k: v for k, v in column_mapping.items() if k in df.columns}
    df = df.rename(columns=rename_dict)
    
    # Add analytics
    _add_shot_analytics(df)
    
    return df


def _add_shot_analytics(df: pd.DataFrame) -> None:
    """Add calculated shot analytics fields."""
    # Outcome analysis
    if 'shot_result' in df.columns:
        df['is_goal'] = (df['shot_result'] == 'Goal').astype(int)
        df['is_on_target'] = df['shot_result'].isin(['Goal', 'Saved Shot']).astype(int)
        df['is_blocked'] = (df['shot_result'] == 'Blocked Shot').astype(int)
    
    # Spatial analysis
    if 'shot_location_x' in df.columns and 'shot_location_y' in df.columns:
        df['shot_distance_to_goal'] = _calculate_shot_distance(df['shot_location_x'], df['shot_location_y'])
        df['shot_zone'] = _classify_shot_zones(df['shot_location_x'], df['shot_location_y'])
    
    # Assist analysis
    if 'assist_player_name' in df.columns:
        df['is_assisted'] = (~df['assist_player_name'].isna()).astype(int)


def _calculate_shot_distance(x_coords: pd.Series, y_coords: pd.Series) -> pd.Series:
    """Calculate distance from shot location to goal center."""
    distances = []
    goal_x, goal_y = 1.0, 0.5  # Goal center in Understat coordinates
    
    for x, y in zip(x_coords, y_coords):
        if pd.isna(x) or pd.isna(y):
            distances.append(None)
            continue
        
        distance = np.sqrt((float(x) - goal_x)**2 + (float(y) - goal_y)**2) * 100
        distances.append(distance)
    
    return pd.Series(distances, index=x_coords.index)


def _classify_shot_zones(x_coords: pd.Series, y_coords: pd.Series) -> pd.Series:
    """Classify shots into tactical zones."""
    zones = []
    
    for x, y in zip(x_coords, y_coords):
        if pd.isna(x) or pd.isna(y):
            zones.append('Unknown')
            continue
        
        x_pct = float(x) * 100
        y_pct = float(y) * 100
        
        if x_pct >= 88:
            zones.append('Six_Yard_Box')
        elif x_pct >= 83:
            zones.append('Penalty_Box')
        elif x_pct >= 67:
            zones.append('Penalty_Area_Edge')
        else:
            zones.append('Long_Range')
    
    return pd.Series(zones, index=x_coords.index)


def _apply_shot_filters(df: pd.DataFrame, player_filter: Optional[str], team_filter: Optional[str], verbose: bool) -> pd.DataFrame:
    """Apply filters to shot events."""
    filtered_df = df.copy()
    
    if player_filter and 'shot_player' in filtered_df.columns:
        if verbose:
            print(f"   🎯 Applying player filter: {player_filter}")
        
        player_variations = _generate_name_variations(player_filter)
        mask = pd.Series([False] * len(filtered_df))
        
        for variation in player_variations:
            mask |= filtered_df['shot_player'].str.contains(variation, case=False, na=False, regex=False)
        
        filtered_df = filtered_df[mask]
    
    if team_filter and 'shot_team' in filtered_df.columns:
        if verbose:
            print(f"   🏟️ Applying team filter: {team_filter}")
        
        team_variations = _generate_name_variations(team_filter)
        mask = pd.Series([False] * len(filtered_df))
        
        for variation in team_variations:
            mask |= filtered_df['shot_team'].str.contains(variation, case=False, na=False, regex=False)
        
        filtered_df = filtered_df[mask]
    
    return filtered_df


def _standardize_dataframe(df: pd.DataFrame, entity_type: str) -> pd.DataFrame:
    """Ensure proper column ordering."""
    if df.empty:
        return df
    
    if entity_type == 'player':
        priority_columns = [
            'player_name', 'team', 'league', 'season', 'official_player_name',
            'understat_xg_chain', 'understat_xg_buildup', 'understat_npxg_plus_xa',
            'understat_key_passes', 'understat_np_xg', 'understat_xa'
        ]
    else:  # team
        priority_columns = [
            'team_name', 'league', 'season', 'official_team_name',
            'understat_ppda_avg', 'understat_deep_completions_total',
            'understat_expected_points_total', 'understat_np_xg_total'
        ]
    
    available_priority = [col for col in priority_columns if col in df.columns]
    remaining_columns = sorted([col for col in df.columns if col not in priority_columns])
    
    final_order = available_priority + remaining_columns
    return df[final_order]


# ====================================================================
# EXPORT UTILITIES
# ====================================================================

def export_to_csv(data: Union[Dict, pd.DataFrame], filename: str, include_timestamp: bool = True) -> str:
    """Export data to CSV with proper formatting."""
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
# QUICK ACCESS FUNCTIONS - SIMPLIFIED API
# ====================================================================

def get_player(player_name: str, league: str, season: str) -> Optional[Dict]:
    """Quick player advanced metrics extraction."""
    return extract_data(player_name, 'player', league, season)

def get_team(team_name: str, league: str, season: str) -> Optional[Dict]:
    """Quick team advanced metrics extraction."""
    return extract_data(team_name, 'team', league, season)

def get_players(players: List[str], league: str, season: str) -> pd.DataFrame:
    """Quick multiple players extraction."""
    return extract_multiple(players, 'player', league, season)

def get_teams(teams: List[str], league: str, season: str) -> pd.DataFrame:
    """Quick multiple teams extraction."""
    return extract_multiple(teams, 'team', league, season)

def get_shots(match_id: int, league: str, season: str, player_filter: Optional[str] = None) -> pd.DataFrame:
    """Quick shot events extraction."""
    return extract_shot_events(match_id, league, season, player_filter=player_filter)