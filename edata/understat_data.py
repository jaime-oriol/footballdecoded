# ====================================================================
# FootballDecoded - Understat Advanced Metrics Extractor  
# ====================================================================
# Specialized xG and team performance metrics from Understat
# Designed for seamless integration with FBref data
# Focus: xGChain, xGBuildup, PPDA, Deep completions, xPoints
# ====================================================================

import sys
import os
import pandas as pd
import warnings
from typing import Dict, List, Optional, Union, Tuple

# Add scrappers to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrappers import Understat

# Suppress pandas warnings for cleaner output
warnings.filterwarnings('ignore', category=FutureWarning, 
                       message='.*DataFrame concatenation with empty or all-NA entries.*')


# ====================================================================
# MAIN EXTRACTION FUNCTIONS - Understat Specialized Metrics
# ====================================================================

def extract_understat_player_season(
    player_name: str,
    league: str,
    season: str,
    verbose: bool = False
) -> Optional[Dict]:
    """
    Extract specialized Understat metrics for a single player's season.
    
    Focus on advanced xG metrics not available in FBref:
    - xGChain (total expected goals in attacking sequences)
    - xGBuildup (expected goals from build-up play)
    - npxG + xA (non-penalty expected goals + expected assists)
    
    Args:
        player_name: Player name (e.g., "Mbappé", "Haaland")
        league: League ID (e.g., "ENG-Premier League", "ESP-La Liga") 
        season: Season ID (e.g., "2024-25", "2023-24")
        verbose: Show detailed extraction progress
        
    Returns:
        Dictionary with Understat-specific metrics or None if not found
        
    Example:
        >>> stats = extract_understat_player_season("Haaland", "ENG-Premier League", "2023-24")
        >>> print(f"xGChain: {stats['xg_chain']} | xGBuildup: {stats['xg_buildup']}")
    """
    if verbose:
        print(f"🎯 Extracting Understat advanced metrics for {player_name}")
        print(f"   League: {league} | Season: {season}")
    
    return _extract_understat_player_data(
        player_name=player_name,
        league=league, 
        season=season,
        extraction_type='season',
        match_id=None,
        verbose=verbose
    )


def extract_understat_player_match(
    player_name: str,
    match_id: int,
    league: str,
    season: str,
    verbose: bool = False
) -> Optional[Dict]:
    """
    Extract specialized Understat metrics for a single player's match.
    
    Match-specific advanced xG analysis from Understat.
    
    Args:
        player_name: Player name (e.g., "Mbappé", "Haaland")
        match_id: Understat match ID (integer)
        league: League identifier
        season: Season identifier
        verbose: Show detailed extraction progress
        
    Returns:
        Dictionary with match-specific Understat metrics
        
    Example:
        >>> stats = extract_understat_player_match("Haaland", 21059, "ENG-Premier League", "2023-24")
        >>> print(f"Match xGChain: {stats['xg_chain']}")
    """
    if verbose:
        print(f"🎯 Extracting Understat match metrics for {player_name}")
        print(f"   Match ID: {match_id} | League: {league}")
    
    return _extract_understat_player_data(
        player_name=player_name,
        league=league,
        season=season,
        extraction_type='match',
        match_id=match_id,
        verbose=verbose
    )


def extract_understat_team_season(
    team_name: str,
    league: str,
    season: str,
    verbose: bool = False
) -> Optional[Dict]:
    """
    Extract specialized Understat team metrics for the season.
    
    Focus on advanced team performance metrics:
    - PPDA (Passes Per Defensive Action)
    - Deep completions (final third entries)
    - xPoints (expected points from performance)
    - xGA (expected goals against)
    
    Args:
        team_name: Team name (e.g., "Manchester City", "Real Madrid")
        league: League identifier
        season: Season identifier
        verbose: Show extraction progress
        
    Returns:
        Dictionary with team-specific Understat metrics
        
    Example:
        >>> stats = extract_understat_team_season("Manchester City", "ENG-Premier League", "2023-24")
        >>> print(f"PPDA: {stats['ppda_avg']} | Deep completions: {stats['deep_completions_total']}")
    """
    if verbose:
        print(f"🎯 Extracting Understat team metrics for {team_name}")
        print(f"   League: {league} | Season: {season}")
    
    return _extract_understat_team_data(
        team_name=team_name,
        league=league,
        season=season,
        verbose=verbose
    )


def extract_multiple_understat_players(
    players: List[str],
    league: str,
    season: str,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract Understat metrics for multiple players efficiently.
    
    Perfect for squad-level advanced analytics complementing FBref data.
    
    Args:
        players: List of player names
        league: League identifier  
        season: Season identifier
        verbose: Show extraction progress
        
    Returns:
        DataFrame with Understat metrics for all players
        
    Example:
        >>> players = ["Haaland", "De Bruyne", "Foden"]
        >>> df = extract_multiple_understat_players(players, "ENG-Premier League", "2023-24")
    """
    if verbose:
        print(f"🎯 Extracting Understat metrics for {len(players)} players")
    
    all_data = []
    successful_extractions = 0
    
    for i, player_name in enumerate(players, 1):
        if verbose:
            print(f"\n[{i}/{len(players)}] Processing {player_name}")
        
        player_data = extract_understat_player_season(
            player_name, league, season, verbose=False
        )
        
        if player_data:
            all_data.append(player_data)
            successful_extractions += 1
        elif verbose:
            print(f"   ❌ Failed to extract Understat data for {player_name}")
    
    if verbose:
        print(f"\n✅ SUMMARY: {successful_extractions}/{len(players)} players extracted")
    
    # Create DataFrame with standardized columns for FBref compatibility
    df = pd.DataFrame(all_data) if all_data else pd.DataFrame()
    return _standardize_understat_dataframe(df, 'player')


# ====================================================================
# CORE EXTRACTION ENGINE - Understat Processing Logic
# ====================================================================

def _extract_understat_player_data(
    player_name: str,
    league: str,
    season: str,
    extraction_type: str,
    match_id: Optional[int] = None,
    verbose: bool = False
) -> Optional[Dict]:
    """
    Core engine for extracting Understat player metrics.
    
    Focuses only on metrics not available in FBref for clean merging.
    """
    try:
        # Initialize Understat extractor
        understat = Understat(leagues=[league], seasons=[season])
        
        if verbose:
            print(f"   🔍 Searching Understat database...")
        
        # Choose extraction method
        if extraction_type == 'season':
            stats = understat.read_player_season_stats()
            player_row = _find_understat_player(stats, player_name)
        else:  # match
            stats = understat.read_player_match_stats(match_id=match_id)
            player_row = _find_understat_player(stats, player_name)
        
        if player_row is None:
            if verbose:
                print(f"   ❌ {player_name} not found in Understat {league} {season}")
            return None
        
        # Extract basic identification info
        basic_info = _extract_understat_basic_info(player_row, player_name, extraction_type, match_id)
        
        # Extract specialized Understat metrics only
        understat_metrics = _extract_understat_specific_metrics(player_row)
        
        # Combine and standardize
        final_data = {**basic_info, **understat_metrics}
        standardized_data = _apply_understat_stat_mapping(final_data)
        
        if verbose:
            metrics_count = len([k for k in standardized_data.keys() if k not in ['player_name', 'team', 'league', 'season']])
            print(f"   ✅ SUCCESS: Extracted {metrics_count} Understat metrics")
        
        return standardized_data
        
    except Exception as e:
        if verbose:
            print(f"   ❌ EXTRACTION FAILED: {str(e)}")
        return None


def _extract_understat_team_data(
    team_name: str,
    league: str,
    season: str,
    verbose: bool = False
) -> Optional[Dict]:
    """
    Core engine for extracting Understat team metrics.
    
    Focuses on PPDA, Deep completions, xPoints, and other team-specific metrics.
    """
    try:
        # Initialize Understat extractor
        understat = Understat(leagues=[league], seasons=[season])
        
        if verbose:
            print(f"   🔍 Searching Understat team database...")
        
        # Get team match stats to calculate aggregated metrics
        team_stats = understat.read_team_match_stats()
        team_matches = _find_understat_team(team_stats, team_name)
        
        if team_matches is None or team_matches.empty:
            if verbose:
                print(f"   ❌ {team_name} not found in Understat {league} {season}")
            return None
        
        # Calculate aggregated team metrics
        basic_info = {
            'team_name': team_name,
            'league': league,
            'season': season,
            'official_team_name': team_matches.iloc[0]['home_team']  # Use first occurrence
        }
        
        # Calculate Understat-specific team metrics
        team_metrics = _calculate_understat_team_metrics(team_matches)
        
        # Combine and standardize
        final_data = {**basic_info, **team_metrics}
        standardized_data = _apply_understat_team_stat_mapping(final_data)
        
        if verbose:
            metrics_count = len([k for k in standardized_data.keys() if k not in ['team_name', 'league', 'season']])
            print(f"   ✅ SUCCESS: Calculated {metrics_count} team metrics from {len(team_matches)} matches")
        
        return standardized_data
        
    except Exception as e:
        if verbose:
            print(f"   ❌ TEAM EXTRACTION FAILED: {str(e)}")
        return None


# ====================================================================
# SEARCH ENGINE - Understat Player/Team Matching
# ====================================================================

def _find_understat_player(stats: pd.DataFrame, player_name: str) -> Optional[pd.DataFrame]:
    """
    Search for player in Understat data with flexible name matching.
    
    Understat uses different name formats than FBref, so robust matching is essential.
    """
    if stats is None or stats.empty:
        return None
    
    # Generate name variations specific to Understat format
    variations = _generate_understat_name_variations(player_name)
    
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


def _find_understat_team(stats: pd.DataFrame, team_name: str) -> Optional[pd.DataFrame]:
    """Search for team in Understat data with flexible name matching."""
    if stats is None or stats.empty:
        return None
    
    variations = _generate_understat_team_variations(team_name)
    
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


def _generate_understat_name_variations(player_name: str) -> List[str]:
    """
    Generate name variations specific to Understat's naming conventions.
    
    Understat often uses different formats than FBref.
    """
    variations = [player_name]
    
    # Remove accents (Understat often uses ASCII versions)
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
            variations.append(f"{parts[0]} {parts[-1]}")  # First + Last
    
    # Common Understat format variations
    if player_name == "Kylian Mbappé":
        variations.extend(["Kylian Mbappe", "K. Mbappe", "Mbappe"])
    elif player_name == "Erling Haaland":
        variations.extend(["E. Haaland", "Haaland", "Erling Braut Haaland"])
    
    return list(dict.fromkeys(variations))


def _generate_understat_team_variations(team_name: str) -> List[str]:
    """Generate team name variations for Understat format."""
    variations = [team_name]
    
    # Remove common suffixes
    suffixes = [' FC', ' CF', ' United', ' City']
    for suffix in suffixes:
        if team_name.endswith(suffix):
            variations.append(team_name[:-len(suffix)])
    
    # Common Understat team name mappings
    understat_mappings = {
        'Manchester United': ['Manchester Utd', 'Man United'],
        'Manchester City': ['Man City'],
        'Tottenham': ['Tottenham Hotspur'],
        'Brighton': ['Brighton and Hove Albion'],
        'Newcastle': ['Newcastle United']
    }
    
    if team_name in understat_mappings:
        variations.extend(understat_mappings[team_name])
    
    return list(dict.fromkeys(variations))


# ====================================================================
# DATA PROCESSING - Extract Specific Metrics
# ====================================================================

def _extract_understat_basic_info(
    player_row: pd.DataFrame,
    player_name: str,
    extraction_type: str,
    match_id: Optional[int] = None
) -> Dict:
    """Extract basic info compatible with FBref format."""
    basic_info = {
        'player_name': player_name,
        'league': player_row.index.get_level_values('league')[0],
        'season': player_row.index.get_level_values('season')[0],
        'team': player_row.index.get_level_values('team')[0]
    }
    
    if extraction_type == 'match' and match_id:
        basic_info['match_id'] = match_id
    
    return basic_info


def _extract_understat_specific_metrics(player_row: pd.DataFrame) -> Dict:
    """
    Extract ONLY the metrics we want from Understat.
    
    Focus on metrics that complement FBref data:
    - xGChain, xGBuildup (not in FBref)
    - npxG + xA combined metric
    """
    understat_data = {}
    
    # Core Understat-specific metrics
    metrics_mapping = {
        'xg_chain': 'xg_chain',
        'xg_buildup': 'xg_buildup', 
        'np_xg': 'np_xg',
        'xa': 'xa',
        'xg': 'xg'  # For verification/cross-checking
    }
    
    for col in player_row.columns:
        if col in metrics_mapping:
            understat_data[metrics_mapping[col]] = player_row.iloc[0][col]
    
    # Calculate combined metric
    if 'np_xg' in understat_data and 'xa' in understat_data:
        np_xg = understat_data['np_xg'] if pd.notna(understat_data['np_xg']) else 0
        xa = understat_data['xa'] if pd.notna(understat_data['xa']) else 0
        understat_data['npxg_plus_xa'] = np_xg + xa
    
    return understat_data


def _calculate_understat_team_metrics(team_matches: pd.DataFrame) -> Dict:
    """
    Calculate aggregated team metrics from match data.
    
    Focus on PPDA, Deep completions, xPoints, xGA.
    """
    team_metrics = {}
    
    # Separate home and away matches for proper aggregation
    home_matches = team_matches[team_matches['home_team'].notna()]
    away_matches = team_matches[team_matches['away_team'].notna()]
    
    # Calculate total matches
    total_matches = len(team_matches)
    team_metrics['matches_analyzed'] = total_matches
    
    if total_matches == 0:
        return team_metrics
    
    # PPDA - Average across all matches
    ppda_values = []
    for col in ['home_ppda', 'away_ppda']:
        if col in team_matches.columns:
            values = team_matches[col].dropna()
            ppda_values.extend(values.tolist())
    
    if ppda_values:
        team_metrics['ppda_avg'] = sum(ppda_values) / len(ppda_values)
        team_metrics['ppda_total_samples'] = len(ppda_values)
    
    # Deep completions - Sum across all matches
    deep_values = []
    for col in ['home_deep_completions', 'away_deep_completions']:
        if col in team_matches.columns:
            values = team_matches[col].dropna()
            deep_values.extend(values.tolist())
    
    if deep_values:
        team_metrics['deep_completions_total'] = sum(deep_values)
        team_metrics['deep_completions_avg'] = sum(deep_values) / total_matches
    
    # Expected Points - Sum across all matches
    xpts_values = []
    for col in ['home_expected_points', 'away_expected_points']:
        if col in team_matches.columns:
            values = team_matches[col].dropna()
            xpts_values.extend(values.tolist())
    
    if xpts_values:
        team_metrics['expected_points_total'] = sum(xpts_values)
        team_metrics['expected_points_avg'] = sum(xpts_values) / total_matches
    
    return team_metrics


# ====================================================================
# STANDARDIZATION - Compatible Column Names
# ====================================================================

def _apply_understat_stat_mapping(player_data: Dict) -> Dict:
    """
    Apply standardized naming for seamless FBref integration.
    
    Ensures column names match FBref format for easy merging.
    """
    understat_mapping = {
        # Understat-specific metrics (not in FBref)
        'xg_chain': 'understat_xg_chain',
        'xg_buildup': 'understat_xg_buildup',
        'npxg_plus_xa': 'understat_npxg_plus_xa',
        
        # Cross-reference metrics (compare with FBref)
        'np_xg': 'understat_np_xg',
        'xa': 'understat_xa',
        'xg': 'understat_xg',
        
        # Basic info (keep compatible with FBref)
        'player_name': 'player_name',
        'team': 'team', 
        'league': 'league',
        'season': 'season'
    }
    
    standardized_data = {}
    for original_name, value in player_data.items():
        standardized_name = understat_mapping.get(original_name, original_name)
        standardized_data[standardized_name] = value
    
    return standardized_data


def _apply_understat_team_stat_mapping(team_data: Dict) -> Dict:
    """Apply standardized naming for team metrics."""
    team_mapping = {
        # Team identification (compatible with FBref)
        'team_name': 'team_name',
        'league': 'league', 
        'season': 'season',
        'official_team_name': 'official_team_name',
        
        # Understat-specific team metrics
        'ppda_avg': 'understat_ppda_avg',
        'ppda_total_samples': 'understat_ppda_samples',
        'deep_completions_total': 'understat_deep_completions_total',
        'deep_completions_avg': 'understat_deep_completions_per_match',
        'expected_points_total': 'understat_expected_points_total',
        'expected_points_avg': 'understat_expected_points_per_match',
        'matches_analyzed': 'understat_matches_analyzed'
    }
    
    standardized_data = {}
    for original_name, value in team_data.items():
        standardized_name = team_mapping.get(original_name, original_name)
        standardized_data[standardized_name] = value
    
    return standardized_data


def _standardize_understat_dataframe(df: pd.DataFrame, data_type: str) -> pd.DataFrame:
    """
    Ensure column ordering compatible with FBref DataFrames.
    
    Priority: basic info → Understat metrics → analysis fields
    """
    if df.empty:
        return df
    
    if data_type == 'player':
        priority_columns = [
            # Basic identification (compatible with FBref)
            'player_name', 'team', 'league', 'season',
            # Understat-specific metrics
            'understat_xg_chain', 'understat_xg_buildup', 'understat_npxg_plus_xa',
            # Cross-reference metrics
            'understat_np_xg', 'understat_xa', 'understat_xg'
        ]
    else:  # team
        priority_columns = [
            # Basic identification
            'team_name', 'league', 'season', 'official_team_name',
            # Understat team metrics
            'understat_ppda_avg', 'understat_deep_completions_total',
            'understat_expected_points_total', 'understat_matches_analyzed'
        ]
    
    # Organize columns
    available_priority = [col for col in priority_columns if col in df.columns]
    remaining_columns = sorted([col for col in df.columns if col not in priority_columns])
    
    final_order = available_priority + remaining_columns
    return df[final_order]


# ====================================================================
# CONVENIENCE FUNCTIONS - Quick Access Interface  
# ====================================================================

def get_understat_player(player_name: str, league: str, season: str) -> Optional[Dict]:
    """Quick Understat player metrics without verbose output."""
    return extract_understat_player_season(player_name, league, season, verbose=False)


def get_understat_team(team_name: str, league: str, season: str) -> Optional[Dict]:
    """Quick Understat team metrics without verbose output."""
    return extract_understat_team_season(team_name, league, season, verbose=False)


def get_understat_squad(players: List[str], league: str, season: str) -> pd.DataFrame:
    """Quick squad Understat metrics without verbose output."""
    return extract_multiple_understat_players(players, league, season, verbose=False)


# ====================================================================
# INTEGRATION FUNCTIONS - Merge with FBref Data
# ====================================================================

def merge_fbref_with_understat(
    fbref_data: Union[pd.DataFrame, Dict],
    league: str,
    season: str,
    data_type: str = 'player',
    verbose: bool = False
) -> pd.DataFrame:
    """
    Merge FBref data with Understat advanced metrics automatically.
    
    This is the key function for creating enriched datasets combining both sources.
    
    Args:
        fbref_data: DataFrame or Dict from FBref extraction
        league: League identifier
        season: Season identifier  
        data_type: 'player' or 'team'
        verbose: Show merge progress
        
    Returns:
        Combined DataFrame with both FBref and Understat metrics
        
    Example:
        >>> # Get FBref data first
        >>> fbref_df = extract_multiple_players_season(["Haaland", "De Bruyne"], "ENG-Premier League", "2023-24")
        >>> 
        >>> # Enrich with Understat
        >>> enriched_df = merge_fbref_with_understat(fbref_df, "ENG-Premier League", "2023-24")
        >>> print(enriched_df[['player_name', 'goals', 'understat_xg_chain']])
    """
    if verbose:
        print(f"🔗 Merging FBref data with Understat metrics")
    
    # Convert Dict to DataFrame if needed
    if isinstance(fbref_data, dict):
        fbref_df = pd.DataFrame([fbref_data])
    else:
        fbref_df = fbref_data.copy()
    
    if fbref_df.empty:
        if verbose:
            print("   ❌ No FBref data provided for merging")
        return fbref_df
    
    # Extract entities from FBref data
    if data_type == 'player':
        entities = fbref_df['player_name'].unique().tolist()
        extract_func = extract_multiple_understat_players
        merge_key = 'player_name'
    else:  # team
        entities = fbref_df['team_name'].unique().tolist()
        # Would need team function - for now focus on players
        if verbose:
            print("   ⚠️  Team merging not yet implemented")
        return fbref_df
    
    if verbose:
        print(f"   📊 Extracting Understat data for {len(entities)} {data_type}s")
    
    # Get Understat data
    understat_df = extract_func(entities, league, season, verbose=False)
    
    if understat_df.empty:
        if verbose:
            print("   ⚠️  No Understat data found for merging")
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
        print(f"   📋 New metrics: {', '.join(understat_cols[:3])}{'...' if len(understat_cols) > 3 else ''}")
    
    return merged_df


def export_enriched_data(
    merged_data: pd.DataFrame,
    filename: str,
    include_timestamp: bool = True
) -> str:
    """
    Export merged FBref + Understat data with proper formatting.
    
    Args:
        merged_data: Combined DataFrame from merge_fbref_with_understat
        filename: Output filename (without .csv extension)
        include_timestamp: Add timestamp to filename
        
    Returns:
        Full path of created CSV file
        
    Example:
        >>> enriched_df = merge_fbref_with_understat(fbref_data, "ENG-Premier League", "2023-24")
        >>> export_enriched_data(enriched_df, "man_city_enriched_analysis")
    """
    import datetime
    
    if include_timestamp:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"{filename}_{timestamp}.csv"
    else:
        full_filename = f"{filename}.csv"
    
    # Export with proper encoding
    merged_data.to_csv(full_filename, index=False, encoding='utf-8')
    
    fbref_cols = len([col for col in merged_data.columns if not col.startswith('understat_')])
    understat_cols = len([col for col in merged_data.columns if col.startswith('understat_')])
    
    print(f"📊 Enriched data exported to: {full_filename}")
    print(f"   Rows: {len(merged_data)} | FBref metrics: {fbref_cols} | Understat metrics: {understat_cols}")
    
    return full_filename


# ====================================================================
# QUICK ANALYSIS - One-Function Solutions
# ====================================================================

def quick_enriched_analysis(
    players: List[str],
    league: str, 
    season: str,
    export: bool = True,
    verbose: bool = False
) -> Dict:
    """
    One-function solution for complete FBref + Understat analysis.
    
    Gets comprehensive data from both sources and merges automatically.
    
    Args:
        players: List of player names for analysis
        league: League identifier
        season: Season identifier
        export: Whether to export enriched data to CSV
        verbose: Show detailed progress
        
    Returns:
        Dictionary with separate and merged datasets
        
    Example:
        >>> players = ["Haaland", "De Bruyne", "Foden"]
        >>> analysis = quick_enriched_analysis(players, "ENG-Premier League", "2023-24")
        >>> print(analysis['merged_data'][['player_name', 'goals', 'understat_xg_chain']])
    """
    if verbose:
        print(f"🚀 Complete enriched analysis for {len(players)} players")
        print(f"   Combining FBref + Understat data from {league} {season}")
    
    results = {}
    
    # Import FBref functions (assumes fbref_data.py is available)
    try:
        from .fbref_data import extract_multiple_players_season
        fbref_available = True
    except ImportError:
        if verbose:
            print("   ⚠️  FBref module not found - Understat only analysis")
        fbref_available = False
    
    # Get Understat data
    if verbose:
        print("\n   📊 Extracting Understat metrics...")
    
    understat_data = extract_multiple_understat_players(players, league, season, verbose)
    results['understat_data'] = understat_data
    
    if not understat_data.empty and verbose:
        print(f"   ✅ Understat: {len(understat_data)} players with {len(understat_data.columns)} metrics")
    
    # Get FBref data if available
    if fbref_available:
        if verbose:
            print("\n   📊 Extracting FBref comprehensive data...")
        
        try:
            fbref_data = extract_multiple_players_season(players, league, season, verbose=False)
            results['fbref_data'] = fbref_data
            
            if not fbref_data.empty:
                if verbose:
                    print(f"   ✅ FBref: {len(fbref_data)} players with {len(fbref_data.columns)} metrics")
                
                # Merge datasets
                if verbose:
                    print("\n   🔗 Merging FBref + Understat datasets...")
                
                merged_data = merge_fbref_with_understat(fbref_data, league, season, verbose=verbose)
                results['merged_data'] = merged_data
                
                # Export if requested
                if export and not merged_data.empty:
                    filename = f"enriched_analysis_{league.replace('-', '_')}_{season}"
                    export_path = export_enriched_data(merged_data, filename)
                    results['export_path'] = export_path
                    
            else:
                if verbose:
                    print("   ⚠️  No FBref data found - Understat only")
                results['merged_data'] = understat_data
                
        except Exception as e:
            if verbose:
                print(f"   ❌ FBref extraction failed: {str(e)[:50]}...")
            results['fbref_data'] = pd.DataFrame()
            results['merged_data'] = understat_data
    
    else:
        # Understat only
        results['merged_data'] = understat_data
        if export and not understat_data.empty:
            filename = f"understat_analysis_{league.replace('-', '_')}_{season}"
            export_path = export_enriched_data(understat_data, filename)
            results['export_path'] = export_path
    
    if verbose:
        print(f"\n✅ ANALYSIS COMPLETE")
        if 'merged_data' in results and not results['merged_data'].empty:
            total_metrics = len(results['merged_data'].columns)
            understat_metrics = len([col for col in results['merged_data'].columns if col.startswith('understat_')])
            print(f"   📊 Final dataset: {len(results['merged_data'])} players, {total_metrics} total metrics")
            print(f"   🎯 Understat contribution: {understat_metrics} advanced metrics")
    
    return results


# ====================================================================
# VALIDATION FUNCTIONS - Data Quality Checks
# ====================================================================

def validate_understat_data(
    data: Union[pd.DataFrame, Dict],
    verbose: bool = True
) -> Dict:
    """
    Validate Understat data quality and completeness.
    
    Useful for ensuring data integrity before analysis.
    
    Args:
        data: Extracted Understat data (DataFrame or Dict)
        verbose: Show detailed validation results
        
    Returns:
        Dictionary with validation results and recommendations
    """
    if isinstance(data, dict):
        df = pd.DataFrame([data])
    else:
        df = data.copy()
    
    validation_results = {
        'total_records': len(df),
        'missing_data': {},
        'data_quality': {},
        'recommendations': []
    }
    
    if df.empty:
        validation_results['recommendations'].append("No data found - check player names and league/season")
        return validation_results
    
    # Check for missing Understat-specific metrics
    key_metrics = ['understat_xg_chain', 'understat_xg_buildup', 'understat_npxg_plus_xa']
    
    for metric in key_metrics:
        if metric in df.columns:
            missing_count = df[metric].isna().sum()
            validation_results['missing_data'][metric] = {
                'missing_count': missing_count,
                'missing_percentage': (missing_count / len(df)) * 100
            }
        else:
            validation_results['missing_data'][metric] = {
                'missing_count': len(df),
                'missing_percentage': 100.0
            }
    
    # Data quality checks
    if 'understat_xg_chain' in df.columns and 'understat_xg_buildup' in df.columns:
        # xGChain should generally be >= xGBuildup
        valid_chain_buildup = df[
            (df['understat_xg_chain'] >= df['understat_xg_buildup']) | 
            df['understat_xg_chain'].isna() | 
            df['understat_xg_buildup'].isna()
        ]
        
        validation_results['data_quality']['valid_chain_buildup_ratio'] = len(valid_chain_buildup) / len(df)
    
    # Generate recommendations
    for metric, stats in validation_results['missing_data'].items():
        if stats['missing_percentage'] > 50:
            validation_results['recommendations'].append(
                f"High missing data for {metric} ({stats['missing_percentage']:.1f}%) - verify player names and league coverage"
            )
        elif stats['missing_percentage'] > 20:
            validation_results['recommendations'].append(
                f"Moderate missing data for {metric} ({stats['missing_percentage']:.1f}%) - some players may not have sufficient data"
            )
    
    if verbose:
        print("🔍 Understat Data Validation Results")
        print("=" * 40)
        print(f"Total records: {validation_results['total_records']}")
        
        print("\n📊 Missing Data Analysis:")
        for metric, stats in validation_results['missing_data'].items():
            status = "✅" if stats['missing_percentage'] < 20 else "⚠️" if stats['missing_percentage'] < 50 else "❌"
            print(f"   {status} {metric}: {stats['missing_percentage']:.1f}% missing")
        
        if validation_results['recommendations']:
            print("\n💡 Recommendations:")
            for rec in validation_results['recommendations']:
                print(f"   • {rec}")
        else:
            print("\n✅ Data quality looks good!")
    
    return validation_results


def compare_fbref_understat_metrics(
    merged_data: pd.DataFrame,
    verbose: bool = True
) -> Dict:
    """
    Compare overlapping metrics between FBref and Understat for validation.
    
    Useful for identifying discrepancies and ensuring data consistency.
    
    Args:
        merged_data: DataFrame from merge_fbref_with_understat
        verbose: Show detailed comparison results
        
    Returns:
        Dictionary with comparison statistics and insights
    """
    comparison_results = {
        'overlapping_metrics': [],
        'correlations': {},
        'discrepancies': {},
        'insights': []
    }
    
    # Define overlapping metrics (both sources have these)
    overlap_pairs = [
        ('expected_goals', 'understat_xg'),
        ('non_penalty_expected_goals', 'understat_np_xg'),
        ('expected_assists', 'understat_xa')
    ]
    
    for fbref_col, understat_col in overlap_pairs:
        if fbref_col in merged_data.columns and understat_col in merged_data.columns:
            comparison_results['overlapping_metrics'].append((fbref_col, understat_col))
            
            # Calculate correlation
            correlation = merged_data[fbref_col].corr(merged_data[understat_col])
            comparison_results['correlations'][(fbref_col, understat_col)] = correlation
            
            # Find large discrepancies
            diff = (merged_data[fbref_col] - merged_data[understat_col]).abs()
            large_discrepancies = diff > (diff.std() * 2)  # More than 2 standard deviations
            comparison_results['discrepancies'][(fbref_col, understat_col)] = {
                'mean_difference': diff.mean(),
                'max_difference': diff.max(),
                'large_discrepancy_count': large_discrepancies.sum()
            }
    
    # Generate insights
    for pair, correlation in comparison_results['correlations'].items():
        if correlation > 0.9:
            comparison_results['insights'].append(f"Excellent agreement between {pair[0]} and {pair[1]} (r={correlation:.3f})")
        elif correlation > 0.7:
            comparison_results['insights'].append(f"Good agreement between {pair[0]} and {pair[1]} (r={correlation:.3f})")
        else:
            comparison_results['insights'].append(f"Potential data quality issue with {pair[0]} vs {pair[1]} (r={correlation:.3f})")
    
    if verbose:
        print("🔍 FBref vs Understat Comparison")
        print("=" * 40)
        
        if comparison_results['overlapping_metrics']:
            print("📊 Metric Correlations:")
            for pair, correlation in comparison_results['correlations'].items():
                status = "✅" if correlation > 0.8 else "⚠️" if correlation > 0.6 else "❌"
                print(f"   {status} {pair[0]} vs {pair[1]}: r = {correlation:.3f}")
            
            print("\n📈 Discrepancy Analysis:")
            for pair, stats in comparison_results['discrepancies'].items():
                print(f"   {pair[0]} vs {pair[1]}:")
                print(f"      Mean difference: {stats['mean_difference']:.3f}")
                print(f"      Large discrepancies: {stats['large_discrepancy_count']} players")
        else:
            print("No overlapping metrics found for comparison")
        
        if comparison_results['insights']:
            print("\n💡 Insights:")
            for insight in comparison_results['insights']:
                print(f"   • {insight}")
    
    return comparison_results


# ====================================================================
# EXPORT UTILITIES - Advanced Export Functions
# ====================================================================

def export_understat_summary_report(
    data: pd.DataFrame,
    league: str,
    season: str,
    filename: Optional[str] = None
) -> str:
    """
    Export a comprehensive summary report of Understat metrics.
    
    Creates a detailed analysis report with key insights and statistics.
    
    Args:
        data: Understat DataFrame (from extract_multiple_understat_players)
        league: League identifier
        season: Season identifier
        filename: Optional custom filename
        
    Returns:
        Path to generated report file
    """
    import datetime
    
    if filename is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"understat_summary_{league.replace('-', '_')}_{season}_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("UNDERSTAT ADVANCED METRICS SUMMARY REPORT\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"League: {league}\n")
        f.write(f"Season: {season}\n")
        f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Players: {len(data)}\n\n")
        
        if not data.empty:
            # Top performers by key metrics
            understat_metrics = [col for col in data.columns if col.startswith('understat_')]
            
            f.write("TOP PERFORMERS BY UNDERSTAT METRICS\n")
            f.write("-" * 40 + "\n\n")
            
            for metric in understat_metrics[:5]:  # Top 5 metrics
                if metric in data.columns and data[metric].notna().any():
                    top_player = data.loc[data[metric].idxmax()]
                    f.write(f"{metric.replace('understat_', '').upper()}:\n")
                    f.write(f"  Leader: {top_player['player_name']} ({top_player['team']})\n")
                    f.write(f"  Value: {top_player[metric]:.3f}\n\n")
            
            # Summary statistics
            f.write("SUMMARY STATISTICS\n")
            f.write("-" * 20 + "\n\n")
            
            for metric in understat_metrics:
                if metric in data.columns and data[metric].notna().any():
                    f.write(f"{metric}:\n")
                    f.write(f"  Mean: {data[metric].mean():.3f}\n")
                    f.write(f"  Median: {data[metric].median():.3f}\n")
                    f.write(f"  Std Dev: {data[metric].std():.3f}\n")
                    f.write(f"  Min: {data[metric].min():.3f}\n")
                    f.write(f"  Max: {data[metric].max():.3f}\n\n")
    
    print(f"📄 Summary report exported to: {filename}")
    return filename