# ====================================================================
# FootballDecoded - FBref Optimized Data Extractor
# ====================================================================
# Compacto, eficiente y sin redundancias para extraer TODOS los datos FBref
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

warnings.filterwarnings('ignore', category=FutureWarning)

# ====================================================================
# CORE ENGINE - UNIFIED EXTRACTION
# ====================================================================

def extract_data(
    entity_name: str,
    entity_type: str,  # 'player' or 'team'
    league: str,
    season: str,
    match_id: Optional[str] = None,
    include_opponent_stats: bool = False,
    verbose: bool = False
) -> Optional[Dict]:
    """
    Unified extraction engine for both players and teams.
    
    Args:
        entity_name: Player or team name
        entity_type: 'player' or 'team'
        league: League ID
        season: Season ID
        match_id: Optional match ID for match-specific data
        include_opponent_stats: Include opponent stats (teams only)
        verbose: Show progress
        
    Returns:
        Dict with ALL available FBref statistics
    """
    if verbose:
        data_scope = "match" if match_id else "season"
        print(f"🔍 Extracting {entity_name} {data_scope} data: {league} {season}")
    
    try:
        fbref = FBref(leagues=[league], seasons=[season])
        
        # Define stat types based on context
        if entity_type == 'player':
            if match_id:
                stat_types = ['summary', 'passing', 'passing_types', 'defense', 'possession', 'misc', 'keepers']
            else:
                stat_types = ['standard', 'shooting', 'passing', 'passing_types', 'goal_shot_creation', 
                             'defense', 'possession', 'playing_time', 'misc', 'keeper', 'keeper_adv']
        else:  # team
            stat_types = ['standard', 'shooting', 'passing', 'passing_types', 'goal_shot_creation',
                         'defense', 'possession', 'playing_time', 'misc', 'keeper', 'keeper_adv']
        
        extracted_data = {}
        basic_info = {}
        stats_found = 0
        
        for i, stat_type in enumerate(stat_types, 1):
            if verbose:
                print(f"   [{i}/{len(stat_types)}] {stat_type}")
            
            try:
                # Get stats based on entity type and context
                if entity_type == 'player':
                    if match_id:
                        stats = fbref.read_player_match_stats(stat_type=stat_type, match_id=match_id)
                    else:
                        stats = fbref.read_player_season_stats(stat_type=stat_type)
                    entity_row = _find_entity(stats, entity_name, 'player')
                else:  # team
                    stats = fbref.read_team_season_stats(stat_type=stat_type, opponent_stats=False)
                    entity_row = _find_entity(stats, entity_name, 'team')
                
                if entity_row is not None:
                    if not basic_info:
                        basic_info = _extract_basic_info(entity_row, entity_name, entity_type, match_id)
                    
                    _process_columns(entity_row, extracted_data)
                    stats_found += 1
                    
                    if verbose:
                        print(f"      ✅ Success")
                        
                    # Extract opponent stats for teams if requested
                    if entity_type == 'team' and include_opponent_stats and not match_id:
                        try:
                            opp_stats = fbref.read_team_season_stats(stat_type=stat_type, opponent_stats=True)
                            opp_row = _find_entity(opp_stats, entity_name, 'team')
                            if opp_row is not None:
                                _process_columns(opp_row, extracted_data, prefix='opponent_')
                        except Exception:
                            pass
                elif verbose:
                    print(f"      ⚠️  Not found")
                    
            except Exception as e:
                if verbose:
                    print(f"      ❌ Error: {str(e)[:30]}...")
                continue
        
        if not basic_info:
            if verbose:
                print(f"   ❌ {entity_type.title()} not found: {entity_name}")
            return None
        
        # Combine and standardize
        final_data = {**basic_info, **extracted_data}
        standardized_data = _apply_stat_mapping(final_data)
        
        if verbose:
            print(f"   ✅ Extracted {len(standardized_data)} fields from {stats_found} stat types")
        
        return standardized_data
        
    except Exception as e:
        if verbose:
            print(f"   ❌ Extraction failed: {str(e)}")
        return None


# ====================================================================
# BATCH EXTRACTION
# ====================================================================

def extract_multiple(
    entities: List[str],
    entity_type: str,
    league: str,
    season: str,
    match_id: Optional[str] = None,
    include_opponent_stats: bool = False,
    verbose: bool = False
) -> pd.DataFrame:
    """
    Extract multiple entities efficiently.
    
    Args:
        entities: List of entity names
        entity_type: 'player' or 'team'
        league: League identifier
        season: Season identifier
        match_id: Optional match ID
        include_opponent_stats: Include opponent stats (teams only)
        verbose: Show progress
        
    Returns:
        DataFrame with all entities' statistics
    """
    if verbose:
        data_scope = "match" if match_id else "season"
        print(f"🔍 Extracting {data_scope} data for {len(entities)} {entity_type}s")
    
    all_data = []
    successful = 0
    
    for i, entity_name in enumerate(entities, 1):
        if verbose:
            print(f"[{i}/{len(entities)}] {entity_name}")
        
        entity_data = extract_data(
            entity_name, entity_type, league, season, match_id, include_opponent_stats, verbose=False
        )
        
        if entity_data:
            all_data.append(entity_data)
            successful += 1
        elif verbose:
            print(f"   ❌ Failed: {entity_name}")
    
    if verbose:
        print(f"✅ Extracted {successful}/{len(entities)} {entity_type}s successfully")
    
    df = pd.DataFrame(all_data) if all_data else pd.DataFrame()
    return _standardize_dataframe(df, entity_type)


# ====================================================================
# SPECIALIZED EXTRACTION FUNCTIONS
# ====================================================================

def extract_league_players(
    league: str,
    season: str,
    team_filter: Optional[str] = None,
    position_filter: Optional[str] = None,
    verbose: bool = False
) -> pd.DataFrame:
    """Extract all players from a league with optional filtering."""
    if verbose:
        print(f"🔍 Extracting player list from {league} {season}")
    
    try:
        fbref = FBref(leagues=[league], seasons=[season])
        player_stats = fbref.read_player_season_stats(stat_type='standard')
        
        if player_stats is None or player_stats.empty:
            return pd.DataFrame()
        
        players_df = player_stats.reset_index()
        
        # Apply filters
        if team_filter:
            players_df = players_df[players_df['team'].str.contains(team_filter, case=False, na=False)]
        if position_filter:
            players_df = players_df[players_df['pos'].str.contains(position_filter, case=False, na=False)]
        
        # Select essential columns
        columns = ['player', 'team', 'league', 'season']
        optional_cols = ['pos', 'age', 'nation']
        for col in optional_cols:
            if col in players_df.columns:
                columns.append(col)
        
        result_df = players_df[columns].sort_values(['team', 'player'])
        
        if verbose:
            print(f"   ✅ Found {len(result_df)} players")
        
        return result_df
        
    except Exception as e:
        if verbose:
            print(f"   ❌ Extraction failed: {str(e)}")
        return pd.DataFrame()


def extract_match_events(
    match_id: str,
    league: str,
    season: str,
    event_type: str = 'all',
    verbose: bool = False
) -> Union[pd.DataFrame, Dict]:
    """Extract match events (goals, cards, substitutions, shots)."""
    if verbose:
        print(f"🔍 Extracting {event_type} from match {match_id}")
    
    try:
        fbref = FBref(leagues=[league], seasons=[season])
        result = {}
        
        if event_type in ['all', 'events']:
            events = fbref.read_events(match_id=match_id)
            if event_type == 'events':
                return events
            result['events'] = events
        
        if event_type in ['all', 'shots']:
            shots = fbref.read_shot_events(match_id=match_id)
            if event_type == 'shots':
                return shots
            result['shots'] = shots
        
        if event_type in ['all', 'lineups']:
            lineups = fbref.read_lineup(match_id=match_id)
            if event_type == 'lineups':
                return lineups
            result['lineups'] = lineups
        
        return result if event_type == 'all' else pd.DataFrame()
        
    except Exception as e:
        if verbose:
            print(f"   ❌ Match extraction failed: {str(e)}")
        return pd.DataFrame() if event_type != 'all' else {}


def extract_league_schedule(
    league: str,
    season: str,
    verbose: bool = False
) -> pd.DataFrame:
    """Extract complete league schedule with results."""
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
# UTILITY FUNCTIONS
# ====================================================================

def _find_entity(stats: pd.DataFrame, entity_name: str, entity_type: str) -> Optional[pd.DataFrame]:
    """Find entity with flexible name matching."""
    if stats is None or stats.empty:
        return None
    
    variations = _generate_name_variations(entity_name, entity_type)
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


def _generate_name_variations(name: str, entity_type: str) -> List[str]:
    """Generate name variations for robust matching."""
    variations = [name]
    
    # Remove accents
    clean_name = (name.replace('é', 'e').replace('ñ', 'n').replace('í', 'i')
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
    
    # Team-specific variations
    if entity_type == 'team':
        # Remove common suffixes
        for suffix in [' FC', ' CF', ' United', ' City', ' Real', ' Club']:
            if name.endswith(suffix):
                variations.append(name[:-len(suffix)])
        
        # Common mappings
        team_mappings = {
            'Real Madrid': ['Madrid', 'Real Madrid CF'],
            'Barcelona': ['Barça', 'FC Barcelona', 'Barca'],
            'Manchester United': ['Man United', 'Man Utd', 'United'],
            'Manchester City': ['Man City', 'City'],
            'Tottenham': ['Spurs', 'Tottenham Hotspur']
        }
        if name in team_mappings:
            variations.extend(team_mappings[name])
    
    return list(dict.fromkeys(variations))


def _extract_basic_info(row: pd.DataFrame, name: str, entity_type: str, match_id: Optional[str] = None) -> Dict:
    """Extract basic identification info."""
    if entity_type == 'player':
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
    else:  # team
        basic_info = {
            'team_name': name,
            'league': row.index.get_level_values('league')[0],
            'season': row.index.get_level_values('season')[0],
            'official_team_name': row.index.get_level_values('team')[0]
        }
    
    return basic_info


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
        
        common_categories = ['Standard', 'Performance', 'Expected', 'Total', 'Short', 
                           'Medium', 'Long', 'Playing Time', 'Per 90 Minutes']
        
        if level0 in common_categories:
            return level1
        else:
            return f"{level0}_{level1}"
    
    return str(col)


def _apply_stat_mapping(data: Dict) -> Dict:
    """Apply standardized naming convention."""
    stat_mapping = {
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
        # Defense
        'Tkl': 'tackles', 'TklW': 'tackles_won', 'Int': 'interceptions',
        'Clr': 'clearances', 'Err': 'errors',
        # Possession
        'Touches': 'touches', 'Succ': 'successful_take_ons', 'Succ%': 'take_on_success_pct',
        'Carries': 'carries', 'PrgC': 'progressive_carries', 'Mis': 'miscontrols',
        'Dis': 'dispossessed',
        # Team performance
        'W': 'wins', 'D': 'draws', 'L': 'losses', 'Pts': 'points',
        'GF': 'goals_for', 'GA': 'goals_against', 'GD': 'goal_difference',
        'xGF': 'expected_goals_for', 'xGA': 'expected_goals_against'
    }
    
    standardized_data = {}
    for original_name, value in data.items():
        standardized_name = stat_mapping.get(original_name, original_name)
        standardized_data[standardized_name] = value
    
    return standardized_data


def _standardize_dataframe(df: pd.DataFrame, entity_type: str) -> pd.DataFrame:
    """Ensure consistent column ordering."""
    if df.empty:
        return df
    
    if entity_type == 'player':
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
    """Quick player season stats extraction."""
    return extract_data(player_name, 'player', league, season)

def get_team(team_name: str, league: str, season: str) -> Optional[Dict]:
    """Quick team season stats extraction."""
    return extract_data(team_name, 'team', league, season)

def get_players(players: List[str], league: str, season: str) -> pd.DataFrame:
    """Quick multiple players extraction."""
    return extract_multiple(players, 'player', league, season)

def get_teams(teams: List[str], league: str, season: str) -> pd.DataFrame:
    """Quick multiple teams extraction."""
    return extract_multiple(teams, 'team', league, season)

def get_league_players(league: str, season: str, team: Optional[str] = None) -> pd.DataFrame:
    """Quick league players list."""
    return extract_league_players(league, season, team_filter=team)

def get_match_data(match_id: str, league: str, season: str, data_type: str = 'all') -> Union[pd.DataFrame, Dict]:
    """Quick match data extraction."""
    return extract_match_events(match_id, league, season, event_type=data_type)

def get_schedule(league: str, season: str) -> pd.DataFrame:
    """Quick league schedule extraction."""
    return extract_league_schedule(league, season)