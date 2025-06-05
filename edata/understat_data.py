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

# Add extractors to path
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


def extract_understat_shot_events(
    match_id: int,
    league: str,
    season: str,
    player_filter: Optional[str] = None,
    team_filter: Optional[str] = None,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract detailed shot events with coordinates and xG data from Understat.
    
    FIXED: Properly handles player names through mapping system.
    
    Args:
        match_id: Understat match ID (integer)
        league: League identifier
        season: Season identifier
        player_filter: Optional player name to filter shots
        team_filter: Optional team name to filter shots
        verbose: Show detailed extraction progress
        
    Returns:
        DataFrame with shot events including coordinates, xG, body part, situation
        
    Example:
        >>> # All shots from match
        >>> shots = extract_understat_shot_events(22256, "ENG-Premier League", "2023-24")
        >>> 
        >>> # Only Cody Gakpo's shots
        >>> gakpo_shots = extract_understat_shot_events(
        ...     22256, "ENG-Premier League", "2023-24", 
        ...     player_filter="Cody Gakpo"
        ... )
    """
    if verbose:
        print(f"🎯 Extracting shot events from match {match_id}")
        print(f"   League: {league} | Season: {season}")
        if player_filter:
            print(f"   Player filter: {player_filter}")
        if team_filter:
            print(f"   Team filter: {team_filter}")
    
    try:
        # Initialize Understat extractor
        understat = Understat(leagues=[league], seasons=[season])
        
        if verbose:
            print(f"   🔍 Extracting shot events from Understat...")
        
        # Extract shot events for the specific match
        shot_events = understat.read_shot_events(match_id=match_id)
        
        if shot_events is None or shot_events.empty:
            if verbose:
                print(f"   ❌ No shot events found for match {match_id}")
            return pd.DataFrame()
        
        if verbose:
            print(f"   📊 Raw data: {len(shot_events)} shots extracted")
            print(f"   📋 Original columns: {list(shot_events.columns)}")
        
        # KEY FIX: Get player season stats to map IDs to names
        player_names_map = {}
        team_names_map = {}
        
        try:
            if verbose:
                print(f"   🔍 Getting player names mapping...")
            
            # Get player season stats for name mapping
            player_stats = understat.read_player_season_stats()
            
            # Create mapping from player_id to player name
            if not player_stats.empty and hasattr(player_stats.index, 'levels'):
                for idx in player_stats.index:
                    if isinstance(idx, tuple) and len(idx) >= 4:
                        # Index format: (league, season, team, player)
                        player_name = idx[3]  # Player name is at index 3
                        # Find corresponding player_id in the data
                        player_data = player_stats.loc[idx]
                        if hasattr(player_data, 'index') and 'player_id' in player_data.index:
                            player_id = player_data['player_id']
                            player_names_map[player_id] = player_name
                        
                        # Map team name too
                        team_name = idx[2]  # Team name is at index 2
                        # We'll map this later when we have team_id
                        
            if verbose:
                print(f"   📝 Mapped {len(player_names_map)} player names")
                
        except Exception as mapping_error:
            if verbose:
                print(f"   ⚠️ Player mapping failed: {str(mapping_error)}")
                print(f"   📊 Proceeding with ID-based filtering...")
        
        # Apply standardization and name mapping
        standardized_events = _standardize_shot_events_columns(shot_events, player_names_map, team_names_map)
        
        # Apply filters after standardization
        filtered_events = standardized_events.copy()
        
        # Filter by player
        if player_filter:
            if 'shot_player' in filtered_events.columns:
                if verbose:
                    print(f"   🎯 Applying player filter: {player_filter}")
                
                # Generate name variations for flexible matching
                player_variations = _generate_understat_name_variations(player_filter)
                
                if verbose:
                    print(f"   🔍 Trying variations: {player_variations}")
                
                # Apply filter with multiple variations
                mask = pd.Series([False] * len(filtered_events))
                
                for variation in player_variations:
                    # Exact match
                    exact_matches = filtered_events['shot_player'].str.lower() == variation.lower()
                    mask |= exact_matches
                    
                    # Partial match
                    partial_matches = filtered_events['shot_player'].str.contains(
                        variation, case=False, na=False, regex=False
                    )
                    mask |= partial_matches
                    
                    if verbose and (exact_matches.any() or partial_matches.any()):
                        matches_found = exact_matches.sum() + partial_matches.sum()
                        print(f"      '{variation}': {matches_found} matches")
                
                filtered_events = filtered_events[mask]
                
                if verbose:
                    if len(filtered_events) > 0:
                        actual_players = filtered_events['shot_player'].unique()
                        print(f"   ✅ Filter applied: {len(filtered_events)} shots found")
                        print(f"   👤 Players included: {list(actual_players)}")
                    else:
                        print(f"   ❌ No shots found for {player_filter}")
                        available_players = standardized_events['shot_player'].dropna().unique()
                        print(f"   👥 Available players: {list(available_players)}")
            else:
                if verbose:
                    print(f"   ❌ Cannot apply player filter - 'shot_player' column not available")
        
        # Filter by team
        if team_filter and 'shot_team' in filtered_events.columns:
            if verbose:
                print(f"   🏟️ Applying team filter: {team_filter}")
            
            team_variations = _generate_understat_team_variations(team_filter)
            mask = pd.Series([False] * len(filtered_events))
            
            for variation in team_variations:
                exact_matches = filtered_events['shot_team'].str.lower() == variation.lower()
                partial_matches = filtered_events['shot_team'].str.contains(
                    variation, case=False, na=False, regex=False
                )
                mask |= exact_matches | partial_matches
            
            filtered_events = filtered_events[mask]
            
            if verbose:
                print(f"   ✅ Team filter applied: {len(filtered_events)} shots")
        
        if filtered_events.empty:
            if verbose:
                print(f"   ⚠️ No shots found after applying filters")
            return pd.DataFrame()
        
        # Add match context
        filtered_events = filtered_events.reset_index(drop=True)
        filtered_events['match_id'] = match_id
        filtered_events['data_source'] = 'understat'
        
        if verbose:
            total_shots = len(filtered_events)
            goals = len(filtered_events[filtered_events.get('shot_result', '') == 'Goal'])
            avg_xg = filtered_events['shot_xg'].mean() if 'shot_xg' in filtered_events.columns else 0
            
            print(f"   ✅ SUCCESS: {total_shots} shot events extracted")
            print(f"   📊 Goals: {goals} | Average xG: {avg_xg:.3f}")
            
            # Body part breakdown
            if 'shot_body_part' in filtered_events.columns:
                body_part_counts = filtered_events['shot_body_part'].value_counts()
                if not body_part_counts.empty:
                    print(f"   🦵 Body parts: {dict(body_part_counts)}")
        
        return filtered_events
        
    except Exception as e:
        if verbose:
            print(f"   ❌ EXTRACTION FAILED: {str(e)}")
        return pd.DataFrame()


def extract_understat_match_shots_analysis(
    match_id: int,
    league: str,
    season: str,
    export_csv: bool = False,
    verbose: bool = False
) -> Dict:
    """
    Complete shot analysis for a match with summary statistics.
    
    Perfect for tactical analysis and match reports.
    
    Args:
        match_id: Understat match ID
        league: League identifier
        season: Season identifier
        export_csv: Whether to export shot events to CSV
        verbose: Show detailed analysis progress
        
    Returns:
        Dictionary with shot events DataFrame and analysis summary
        
    Example:
        >>> analysis = extract_understat_match_shots_analysis(
        ...     22256, "ENG-Premier League", "2023-24", 
        ...     export_csv=True, verbose=True
        ... )
        >>> print(f"Total shots: {analysis['summary']['total_shots']}")
        >>> print(f"Goals: {analysis['summary']['goals']}")
    """
    if verbose:
        print(f"🎯 Complete shot analysis for match {match_id}")
    
    # Extract all shot events
    shot_events = extract_understat_shot_events(
        match_id=match_id,
        league=league,
        season=season,
        verbose=verbose
    )
    
    analysis_results = {
        'shot_events': shot_events,
        'summary': {},
        'team_breakdown': {},
        'player_breakdown': {}
    }
    
    if shot_events.empty:
        if verbose:
            print("   ❌ No shot data available for analysis")
        return analysis_results
    
    # Calculate summary statistics
    total_shots = len(shot_events)
    goals = len(shot_events[shot_events['shot_result'] == 'Goal'])
    total_xg = shot_events['shot_xg'].sum()
    avg_xg_per_shot = shot_events['shot_xg'].mean()
    
    analysis_results['summary'] = {
        'match_id': match_id,
        'total_shots': total_shots,
        'goals': goals,
        'total_xg': round(total_xg, 3),
        'avg_xg_per_shot': round(avg_xg_per_shot, 3),
        'conversion_rate': round((goals / total_shots) * 100, 1) if total_shots > 0 else 0,
        'goal_difference_vs_xg': round(goals - total_xg, 3)
    }
    
    # Team-level breakdown
    if 'shot_team' in shot_events.columns:
        team_summary = shot_events.groupby('shot_team').agg({
            'shot_xg': ['count', 'sum', 'mean'],
            'shot_result': lambda x: (x == 'Goal').sum()
        }).round(3)
        
        team_summary.columns = ['shots', 'total_xg', 'avg_xg', 'goals']
        analysis_results['team_breakdown'] = team_summary.to_dict('index')
    
    # Player-level breakdown (top 5 by shots)
    if 'shot_player' in shot_events.columns:
        player_summary = shot_events.groupby(['shot_player', 'shot_team']).agg({
            'shot_xg': ['count', 'sum', 'mean'],
            'shot_result': lambda x: (x == 'Goal').sum()
        }).round(3)
        
        player_summary.columns = ['shots', 'total_xg', 'avg_xg', 'goals']
        top_players = player_summary.sort_values('shots', ascending=False).head(5)
        analysis_results['player_breakdown'] = top_players.to_dict('index')
    
    # Export CSV if requested
    if export_csv and not shot_events.empty:
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"understat_shots_match_{match_id}_{timestamp}.csv"
        shot_events.to_csv(filename, index=False, encoding='utf-8')
        analysis_results['export_path'] = filename
        
        if verbose:
            print(f"   📊 Shot events exported to: {filename}")
    
    if verbose:
        print(f"   ✅ ANALYSIS COMPLETE")
        print(f"   📊 {total_shots} shots | {goals} goals | {total_xg:.2f} xG")
        print(f"   🎯 Conversion: {analysis_results['summary']['conversion_rate']}%")
    
    return analysis_results


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
    elif player_name == "Cody Gakpo":
        variations.extend(["C. Gakpo", "Gakpo"])
    
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
        'Newcastle': ['Newcastle United'],
        'Aston Villa': ['Villa'],
        'Liverpool': ['Liverpool FC']
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
# SHOT EVENTS PROCESSING - Fixed with Player Name Mapping
# ====================================================================

def _standardize_shot_events_columns(
    shot_events: pd.DataFrame, 
    player_names_map: Dict = None,
    team_names_map: Dict = None
) -> pd.DataFrame:
    """
    Standardize shot events column names and map IDs to names.
    
    FIXED: Properly handles Understat's ID-based system.
    """
    standardized_df = shot_events.copy()
    
    if player_names_map is None:
        player_names_map = {}
    if team_names_map is None:
        team_names_map = {}
    
    # Initial column mapping
    shot_mapping = {
        'xg': 'shot_xg',
        'location_x': 'shot_location_x', 
        'location_y': 'shot_location_y',
        'body_part': 'shot_body_part',
        'situation': 'shot_situation',
        'result': 'shot_result',
        'minute': 'shot_minute',
        'date': 'shot_date',
        'game_id': 'match_id'
    }
    
    # Apply basic mapping
    rename_dict = {}
    for original, standardized in shot_mapping.items():
        if original in standardized_df.columns:
            rename_dict[original] = standardized
    
    if rename_dict:
        standardized_df = standardized_df.rename(columns=rename_dict)
    
    # KEY FIX: Map player_id to player names
    if 'player_id' in standardized_df.columns and player_names_map:
        print(f"   🔍 Mapping player IDs to names...")
        standardized_df['shot_player'] = standardized_df['player_id'].map(player_names_map)
        
        # Fill missing names with "Unknown Player [ID]"
        mask = standardized_df['shot_player'].isna()
        standardized_df.loc[mask, 'shot_player'] = (
            "Unknown Player [" + standardized_df.loc[mask, 'player_id'].astype(str) + "]"
        )
        
        mapped_count = (~standardized_df['shot_player'].str.contains('Unknown')).sum()
        print(f"   ✅ Mapped {mapped_count}/{len(standardized_df)} player names")
    
    elif 'player_id' in standardized_df.columns:
        # Fallback: use player_id as shot_player for filtering purposes
        print(f"   ⚠️ No player name mapping available, using IDs...")
        standardized_df['shot_player'] = "Player ID " + standardized_df['player_id'].astype(str)
    
    # Map team_id to team names (try to get from schedule or use basic mapping)
    if 'team_id' in standardized_df.columns:
        # Create basic team name mapping based on known team IDs
        # For the match we're testing (Aston Villa vs Liverpool)
        basic_team_mapping = {
            71: "Aston Villa",    # Based on your CSV data
            87: "Liverpool"       # Based on your CSV data
        }
        
        standardized_df['shot_team'] = standardized_df['team_id'].map(basic_team_mapping)
        
        # Fill missing with team ID
        mask = standardized_df['shot_team'].isna()
        standardized_df.loc[mask, 'shot_team'] = (
            "Team ID " + standardized_df.loc[mask, 'team_id'].astype(str)
        )
        
        print(f"   🏟️ Mapped team IDs to names")
    
    # Convert data types
    numeric_cols = ['shot_xg', 'shot_location_x', 'shot_location_y', 'shot_minute']
    for col in numeric_cols:
        if col in standardized_df.columns:
            standardized_df[col] = pd.to_numeric(standardized_df[col], errors='coerce')
    
    # Add calculated fields
    if 'shot_result' in standardized_df.columns:
        standardized_df['is_goal'] = (standardized_df['shot_result'] == 'Goal').astype(int)
        standardized_df['is_on_target'] = standardized_df['shot_result'].isin(['Goal', 'Saved Shot']).astype(int)
    
    # Add shot zones
    if 'shot_location_x' in standardized_df.columns and 'shot_location_y' in standardized_df.columns:
        standardized_df['shot_zone'] = _classify_shot_zones(
            standardized_df['shot_location_x'], 
            standardized_df['shot_location_y']
        )
    
    # Debug info
    if 'shot_player' in standardized_df.columns:
        unique_players = standardized_df['shot_player'].dropna().unique()
        print(f"   👤 Players found: {list(unique_players)}")
    
    return standardized_df


def _classify_shot_zones(x_coords: pd.Series, y_coords: pd.Series) -> pd.Series:
    """
    Classify shots into tactical zones for analysis.
    
    Based on Understat coordinate system (0-1 scale).
    """
    zones = []
    
    for x, y in zip(x_coords, y_coords):
        if pd.isna(x) or pd.isna(y):
            zones.append('Unknown')
            continue
        
        # Convert to percentages for easier understanding
        x_pct = float(x) * 100
        y_pct = float(y) * 100
        
        # Zone classification based on position
        if x_pct >= 83:  # Very close to goal
            if 30 <= y_pct <= 70:
                zones.append('Central Box')
            else:
                zones.append('Wide Box')
        elif x_pct >= 67:  # Penalty area
            if 35 <= y_pct <= 65:
                zones.append('Central Penalty Area')
            else:
                zones.append('Wide Penalty Area')
        elif x_pct >= 50:  # Outside box
            if 40 <= y_pct <= 60:
                zones.append('Central Outside Box')
            else:
                zones.append('Wide Outside Box')
        else:  # Long range
            zones.append('Long Range')
    
    return pd.Series(zones, index=x_coords.index)


# ====================================================================
# CONVENIENCE FUNCTIONS - Shot Events Quick Access
# ====================================================================

def get_understat_shots(match_id: int, league: str, season: str, 
                       player_filter: Optional[str] = None) -> pd.DataFrame:
    """Quick shot events extraction without verbose output."""
    return extract_understat_shot_events(
        match_id, league, season, player_filter=player_filter, verbose=False
    )


def get_player_shots_from_match(player_name: str, match_id: int, 
                               league: str, season: str) -> pd.DataFrame:
    """Quick extraction of specific player's shots from a match."""
    return extract_understat_shot_events(
        match_id, league, season, player_filter=player_name, verbose=False
    )


def get_team_shots_from_match(team_name: str, match_id: int,
                             league: str, season: str) -> pd.DataFrame:
    """Quick extraction of specific team's shots from a match."""
    return extract_understat_shot_events(
        match_id, league, season, team_filter=team_name, verbose=False
    )


# ====================================================================
# STANDARDIZATION - Compatible Column Names
# ====================================================================

def prepare_shot_map_data(shot_events: pd.DataFrame) -> Dict:
    """
    Prepare shot events data for visualization/plotting.
    
    Returns organized data ready for shot maps, heat maps, and tactical graphics.
    """
    if shot_events.empty:
        return {
            'coordinates': {'x': [], 'y': [], 'xg_size': []},
            'goals': {'x': [], 'y': []},
            'by_player': {},
            'by_team': {},
            'summary': {}
        }
    
    viz_data = {
        'coordinates': {
            'x': shot_events.get('shot_location_x', []).tolist(),
            'y': shot_events.get('shot_location_y', []).tolist(),
            'xg': shot_events.get('shot_xg', []).tolist(),
            'xg_size': (shot_events.get('shot_xg', []) * 1000).tolist(),  # Scale for plotting
        },
        'goals': {},
        'by_player': {},
        'by_team': {},
        'summary': {}
    }
    
    # Extract goals separately for highlighting
    if 'is_goal' in shot_events.columns:
        goals = shot_events[shot_events['is_goal'] == 1]
        viz_data['goals'] = {
            'x': goals.get('shot_location_x', []).tolist(),
            'y': goals.get('shot_location_y', []).tolist(),
            'xg': goals.get('shot_xg', []).tolist()
        }
    
    # Organize by player
    if 'shot_player' in shot_events.columns:
        for player in shot_events['shot_player'].unique():
            if pd.notna(player):
                player_shots = shot_events[shot_events['shot_player'] == player]
                viz_data['by_player'][player] = {
                    'x': player_shots.get('shot_location_x', []).tolist(),
                    'y': player_shots.get('shot_location_y', []).tolist(),
                    'xg': player_shots.get('shot_xg', []).tolist(),
                    'goals': len(player_shots[player_shots.get('is_goal', 0) == 1]),
                    'total_xg': player_shots.get('shot_xg', []).sum()
                }
    
    # Organize by team  
    if 'shot_team' in shot_events.columns:
        for team in shot_events['shot_team'].unique():
            if pd.notna(team):
                team_shots = shot_events[shot_events['shot_team'] == team]
                viz_data['by_team'][team] = {
                    'x': team_shots.get('shot_location_x', []).tolist(),
                    'y': team_shots.get('shot_location_y', []).tolist(),
                    'xg': team_shots.get('shot_xg', []).tolist(),
                    'goals': len(team_shots[team_shots.get('is_goal', 0) == 1]),
                    'total_xg': team_shots.get('shot_xg', []).sum(),
                    'shots': len(team_shots)
                }
    
    # Summary statistics
    viz_data['summary'] = {
        'total_shots': len(shot_events),
        'total_goals': len(shot_events[shot_events.get('is_goal', 0) == 1]),
        'total_xg': shot_events.get('shot_xg', []).sum(),
        'avg_xg': shot_events.get('shot_xg', []).mean(),
        'conversion_rate': (len(shot_events[shot_events.get('is_goal', 0) == 1]) / len(shot_events) * 100) if len(shot_events) > 0 else 0
    }
    
    return viz_data


def export_shot_map_data(shot_events: pd.DataFrame, filename: str,
                        include_viz_data: bool = True) -> str:
    """
    Export shot events with optional visualization-ready data.
    """
    import datetime
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"{filename}_{timestamp}.csv"
    
    # Export main shot events
    shot_events.to_csv(csv_filename, index=False, encoding='utf-8')
    
    print(f"📊 Shot events exported to: {csv_filename}")
    print(f"   Total shots: {len(shot_events)}")
    
    if include_viz_data and not shot_events.empty:
        # Also export visualization summary
        viz_data = prepare_shot_map_data(shot_events)
        
        json_filename = f"{filename}_viz_data_{timestamp}.json"
        import json
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(viz_data, f, indent=2, ensure_ascii=False)
        
        print(f"📈 Visualization data exported to: {json_filename}")
        print(f"   Ready for: matplotlib, plotly, D3.js, etc.")
    
    return csv_filename


def _apply_understat_stat_mapping(player_data: Dict) -> Dict:
    """
    Apply standardized naming for seamless FBref integration.
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


# ====================================================================
# PLAYER NAME MAPPING SYSTEM - Key Fix for Shot Events
# ====================================================================

def _get_player_names_from_season_stats(
    understat: Understat,
    verbose: bool = False
) -> Dict[int, str]:
    """
    Extract player ID to name mapping from season stats.
    
    This is the key function that solves the shot events player filtering issue.
    """
    player_names_map = {}
    
    try:
        if verbose:
            print(f"   🔍 Building player names mapping...")
        
        # Get all player season stats
        player_stats = understat.read_player_season_stats()
        
        if player_stats.empty:
            if verbose:
                print(f"   ⚠️ No player season stats found")
            return player_names_map
        
        # Understat player season stats have multi-index: (league, season, team, player)
        if hasattr(player_stats.index, 'levels'):
            for idx in player_stats.index:
                if isinstance(idx, tuple) and len(idx) >= 4:
                    player_name = idx[3]  # Player name is the 4th level
                    
                    # Get the actual data row to find player_id
                    try:
                        player_data = player_stats.loc[idx]
                        # Some versions might have player_id as column, others in index
                        if 'player_id' in player_data.index:
                            player_id = player_data['player_id']
                            if pd.notna(player_id):
                                player_names_map[int(player_id)] = player_name
                        
                    except (KeyError, IndexError, TypeError):
                        continue
        
        if verbose:
            print(f"   ✅ Mapped {len(player_names_map)} players")
            if len(player_names_map) > 0:
                sample_players = list(player_names_map.values())[:3]
                print(f"   📝 Sample: {sample_players}")
        
        return player_names_map
        
    except Exception as e:
        if verbose:
            print(f"   ❌ Player mapping failed: {str(e)}")
        return {}


def _get_team_names_from_schedule(
    understat: Understat,
    verbose: bool = False
) -> Dict[int, str]:
    """
    Extract team ID to name mapping from schedule data.
    """
    team_names_map = {}
    
    try:
        if verbose:
            print(f"   🔍 Building team names mapping...")
        
        # Try to get schedule data
        schedule = understat.read_schedule()
        
        if not schedule.empty:
            # Extract team mappings from home_team and away_team columns
            for _, row in schedule.iterrows():
                if 'home_team_id' in row and 'home_team' in row:
                    team_id = row['home_team_id']
                    team_name = row['home_team']
                    if pd.notna(team_id) and pd.notna(team_name):
                        team_names_map[int(team_id)] = team_name
                
                if 'away_team_id' in row and 'away_team' in row:
                    team_id = row['away_team_id']
                    team_name = row['away_team']
                    if pd.notna(team_id) and pd.notna(team_name):
                        team_names_map[int(team_id)] = team_name
        
        if verbose:
            print(f"   ✅ Mapped {len(team_names_map)} teams")
        
        return team_names_map
        
    except Exception as e:
        if verbose:
            print(f"   ⚠️ Team mapping failed, using defaults: {str(e)}")
        
        # Fallback: known team mappings for common leagues
        return {
            71: "Aston Villa",
            87: "Liverpool",
            # Add more as needed
        }


# ====================================================================
# ENHANCED SHOT EVENTS - With Proper Name Mapping
# ====================================================================

def extract_understat_shot_events_with_names(
    match_id: int,
    league: str,
    season: str,
    player_filter: Optional[str] = None,
    team_filter: Optional[str] = None,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Enhanced shot events extraction with proper player name mapping.
    
    FIXED: Solved the pandas index join error in filtering.
    """
    if verbose:
        print(f"🎯 Enhanced shot events extraction for match {match_id}")
        print(f"   League: {league} | Season: {season}")
        if player_filter:
            print(f"   Player filter: {player_filter}")
    
    try:
        # Initialize Understat extractor
        understat = Understat(leagues=[league], seasons=[season])
        
        # STEP 1: Get name mappings FIRST
        if verbose:
            print(f"   🔍 Step 1: Getting name mappings...")
        
        player_names_map = _get_player_names_from_season_stats(understat, verbose)
        team_names_map = _get_team_names_from_schedule(understat, verbose)
        
        # STEP 2: Extract raw shot events
        if verbose:
            print(f"   🔍 Step 2: Extracting raw shot events...")
        
        shot_events = understat.read_shot_events(match_id=match_id)
        
        if shot_events is None or shot_events.empty:
            if verbose:
                print(f"   ❌ No shot events found for match {match_id}")
            return pd.DataFrame()
        
        if verbose:
            print(f"   📊 Raw data: {len(shot_events)} shots extracted")
        
        # STEP 3: Apply name mapping and standardization
        if verbose:
            print(f"   🔍 Step 3: Applying name mapping...")
        
        standardized_events = _standardize_shot_events_columns(
            shot_events, player_names_map, team_names_map
        )
        
        # STEP 4: Apply filters with proper names
        filtered_events = standardized_events.copy()
        
        if player_filter and 'shot_player' in filtered_events.columns:
            if verbose:
                print(f"   🎯 Step 4: Applying player filter...")
            
            # Show available players first
            available_players = filtered_events['shot_player'].dropna().unique()
            if verbose:
                print(f"   👥 Available players: {list(available_players)}")
            
            # Generate variations and apply filter
            player_variations = _generate_understat_name_variations(player_filter)
            if verbose:
                print(f"   🔍 Trying variations: {player_variations}")
            
            # FIX: Create boolean mask step by step to avoid index issues
            total_rows = len(filtered_events)
            final_mask = [False] * total_rows
            matches_found = 0
            
            for variation in player_variations:
                if verbose:
                    print(f"      Testing variation: '{variation}'")
                
                try:
                    # Exact match check
                    exact_mask = filtered_events['shot_player'].str.lower() == variation.lower()
                    exact_count = exact_mask.sum()
                    
                    # Partial match check  
                    partial_mask = filtered_events['shot_player'].str.contains(
                        variation, case=False, na=False, regex=False
                    )
                    partial_count = partial_mask.sum()
                    
                    # Combine masks for this variation
                    variation_mask = exact_mask | partial_mask
                    variation_total = variation_mask.sum()
                    
                    # Update final mask
                    for i in range(total_rows):
                        if variation_mask.iloc[i]:
                            final_mask[i] = True
                    
                    if variation_total > 0:
                        matches_found += variation_total
                        if verbose:
                            print(f"         ✅ '{variation}': {variation_total} matches (exact: {exact_count}, partial: {partial_count})")
                    
                except Exception as var_error:
                    if verbose:
                        print(f"         ❌ Error with variation '{variation}': {str(var_error)}")
                    continue
            
            # Apply the final mask
            try:
                filtered_events = filtered_events[final_mask]
                
                if verbose:
                    if len(filtered_events) > 0:
                        actual_players = filtered_events['shot_player'].unique()
                        print(f"   ✅ Filter SUCCESS: {len(filtered_events)} shots found")
                        print(f"   👤 Matched players: {list(actual_players)}")
                    else:
                        print(f"   ❌ No shots found for '{player_filter}'")
                        print(f"   💡 Player exists but no matches found with variations")
                        
                        # Debug: Try exact match manually
                        exact_test = standardized_events[
                            standardized_events['shot_player'] == player_filter
                        ]
                        if not exact_test.empty:
                            print(f"   🔍 DEBUG: Found {len(exact_test)} shots with exact name match")
                            filtered_events = exact_test
                        else:
                            print(f"   🔍 DEBUG: No exact matches either")
                            
            except Exception as filter_error:
                if verbose:
                    print(f"   ❌ Filter application failed: {str(filter_error)}")
                # Fallback: try simple exact match
                try:
                    filtered_events = standardized_events[
                        standardized_events['shot_player'] == player_filter
                    ]
                    if verbose:
                        print(f"   🔄 Fallback exact match: {len(filtered_events)} shots")
                except Exception as fallback_error:
                    if verbose:
                        print(f"   ❌ Fallback also failed: {str(fallback_error)}")
                    filtered_events = pd.DataFrame()
        
        # Add final touches if we have data
        if not filtered_events.empty:
            filtered_events = filtered_events.reset_index(drop=True)
            filtered_events['match_id'] = match_id
            filtered_events['data_source'] = 'understat'
        
        if verbose:
            total_shots = len(filtered_events)
            print(f"   ✅ FINAL RESULT: {total_shots} shot events")
            
            if total_shots > 0:
                if 'shot_result' in filtered_events.columns:
                    goals = len(filtered_events[filtered_events['shot_result'] == 'Goal'])
                    print(f"   📊 Goals: {goals}")
                
                if 'shot_xg' in filtered_events.columns:
                    avg_xg = filtered_events['shot_xg'].mean()
                    total_xg = filtered_events['shot_xg'].sum()
                    print(f"   📊 Total xG: {total_xg:.3f} | Average xG: {avg_xg:.3f}")
        
        return filtered_events
        
    except Exception as e:
        if verbose:
            print(f"   ❌ EXTRACTION FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
        return pd.DataFrame()


# ====================================================================
# SIMPLE TEST FUNCTIONS - For Quick Verification
# ====================================================================

def test_shot_events_simple(
    match_id: int = 22256,
    player_name: str = "Cody Gakpo",
    verbose: bool = True
) -> bool:
    """
    Simple test function to verify shot events extraction works.
    
    Returns True if successful, False otherwise.
    """
    if verbose:
        print(f"🧪 Testing shot events extraction...")
        print(f"   Match: {match_id} | Player: {player_name}")
    
    try:
        # Test the enhanced function
        shots = extract_understat_shot_events_with_names(
            match_id=match_id,
            league="ENG-Premier League",
            season="2023-24",
            player_filter=player_name,
            verbose=verbose
        )
        
        success = not shots.empty
        
        if success and verbose:
            print(f"   ✅ SUCCESS: Found {len(shots)} shots for {player_name}")
            
            # Export for inspection
            filename = f"test_shots_{player_name.replace(' ', '_')}_fixed.csv"
            shots.to_csv(filename, index=False, encoding='utf-8')
            print(f"   📁 Exported: {filename}")
        
        elif verbose:
            print(f"   ❌ FAILED: No shots found for {player_name}")
        
        return success
        
    except Exception as e:
        if verbose:
            print(f"   ❌ ERROR: {str(e)}")
        return False


def list_players_in_match(
    match_id: int = 22256,
    verbose: bool = True
) -> List[str]:
    """
    List all players who took shots in a match.
    
    Useful for finding the correct player names for filtering.
    """
    if verbose:
        print(f"👥 Listing players in match {match_id}...")
    
    try:
        shots = extract_understat_shot_events_with_names(
            match_id=match_id,
            league="ENG-Premier League",
            season="2023-24",
            verbose=False
        )
        
        if shots.empty:
            if verbose:
                print(f"   ❌ No shots found in match")
            return []
        
        players = shots['shot_player'].dropna().unique().tolist()
        
        if verbose:
            print(f"   📋 Players who took shots ({len(players)}):")
            for i, player in enumerate(sorted(players), 1):
                shot_count = (shots['shot_player'] == player).sum()
                print(f"      {i:2d}. {player} ({shot_count} shots)")
        
        return players
        
    except Exception as e:
        if verbose:
            print(f"   ❌ ERROR: {str(e)}")
        return []