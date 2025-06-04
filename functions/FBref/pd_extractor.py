# FootballDecoded - Comprehensive Player Data Extractor
# Professional solution for season and match-level player statistics
# Part of TFG2 - Business Analytics & Computer Engineering

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import warnings
from typing import Dict, List, Optional, Union, Literal
from dataclasses import dataclass
from extractors import FBref

# Suppress pandas warnings for cleaner output
warnings.filterwarnings('ignore', category=FutureWarning, 
                       message='.*DataFrame concatenation with empty or all-NA entries.*')


@dataclass
class PlayerExtractionConfig:
    """Configuration class for player data extraction parameters."""
    include_keeper_stats: bool = True
    include_advanced_stats: bool = True
    verbose: bool = False


class PlayerDataExtractor:
    """
    Comprehensive player data extraction system for football analytics.
    
    This class provides a unified interface for extracting both season-aggregated
    and match-specific player statistics from FBref. Designed for professional
    football analytics workflows and academic research.
    
    Features:
    - Season-level statistics extraction
    - Match-specific performance data
    - Standardized column naming
    - Robust error handling
    - Flexible configuration options
    
    Usage:
        extractor = PlayerDataExtractor()
        
        # Season data
        season_stats = extractor.get_season_stats("Mbappé", "ESP-La Liga", "2024-25")
        
        # Match data
        match_stats = extractor.get_match_stats("Mbappé", match_id="abc123")
    """
    
    def __init__(self, config: Optional[PlayerExtractionConfig] = None):
        """
        Initialize the player data extractor.
        
        Args:
            config: Configuration object with extraction parameters
        """
        self.config = config or PlayerExtractionConfig()
        self.stat_mapping = self._initialize_stat_mapping()
        self._fbref_cache = {}  # Cache FBref instances to avoid recreation
        
    def get_season_stats(
        self, 
        player_name: str, 
        league: str, 
        season: str
    ) -> Optional[Dict[str, Union[str, int, float]]]:
        """
        Extract comprehensive season-level statistics for a player.
        
        This method aggregates all available season statistics including:
        - Basic performance metrics (goals, assists, minutes)
        - Advanced shooting statistics (xG, shot accuracy)
        - Passing and possession metrics
        - Defensive contributions
        - Team performance impact
        
        Args:
            player_name: Full or partial player name (e.g., "Mbappé", "Kylian Mbappé")
            league: Standard league identifier (e.g., "ESP-La Liga", "FRA-Ligue 1")
            season: Season in format "YYYY-YY" (e.g., "2024-25", "2023-24")
            
        Returns:
            Dictionary containing all available player statistics with standardized
            column names, or None if player not found.
            
        Example:
            >>> extractor = PlayerDataExtractor()
            >>> stats = extractor.get_season_stats("Mbappé", "ESP-La Liga", "2024-25")
            >>> print(f"Goals: {stats['goals']}, xG: {stats['expected_goals']}")
        """
        if self.config.verbose:
            print(f"Extracting season data for {player_name} ({league}, {season})")
        
        try:
            fbref = self._get_fbref_instance([league], [season])
            
            # Define extraction strategy
            extraction_plan = self._create_season_extraction_plan()
            
            # Execute extraction
            player_data = self._execute_extraction_plan(
                fbref, player_name, extraction_plan
            )
            
            if not player_data:
                if self.config.verbose:
                    print(f"Player '{player_name}' not found in {league} {season}")
                return None
            
            # Apply standardization and return
            standardized_data = self._apply_standardization(player_data)
            
            if self.config.verbose:
                print(f"✅ Extracted {len(standardized_data)} season metrics")
            
            return standardized_data
            
        except Exception as e:
            if self.config.verbose:
                print(f"Error extracting season data: {str(e)}")
            return None
    
    def get_match_stats(
        self,
        player_name: str,
        match_id: str,
        stat_type: Literal['summary', 'passing', 'defense', 'possession'] = 'summary'
    ) -> Optional[Dict[str, Union[str, int, float]]]:
        """
        Extract match-specific performance statistics for a player.
        
        This method retrieves detailed performance data from a specific match,
        providing granular insights into individual game contributions.
        
        Args:
            player_name: Full or partial player name
            match_id: FBref match identifier (8-character string)
            stat_type: Type of match statistics to extract
                - 'summary': Basic match performance
                - 'passing': Detailed passing statistics
                - 'defense': Defensive actions and success rates
                - 'possession': Touch and carry statistics
                
        Returns:
            Dictionary containing match-specific statistics with standardized
            column names, or None if data not available.
            
        Example:
            >>> extractor = PlayerDataExtractor()
            >>> match_stats = extractor.get_match_stats("Mbappé", "abc12345", "summary")
            >>> print(f"Match goals: {match_stats['goals']}")
        """
        if self.config.verbose:
            print(f"Extracting match data for {player_name} (Match: {match_id})")
        
        try:
            # Initialize FBref with minimal configuration for match data
            fbref = FBref()
            
            # Extract match statistics
            match_data = fbref.read_player_match_stats(
                stat_type=stat_type, 
                match_id=match_id
            )
            
            if match_data.empty:
                if self.config.verbose:
                    print(f"No match data found for match ID: {match_id}")
                return None
            
            # Find player in match data
            player_row = self._find_player_in_dataframe(match_data, player_name)
            
            if player_row is None:
                if self.config.verbose:
                    print(f"Player '{player_name}' not found in match {match_id}")
                return None
            
            # Convert to dictionary and standardize
            player_match_data = self._dataframe_row_to_dict(player_row)
            standardized_data = self._apply_standardization(player_match_data)
            
            if self.config.verbose:
                print(f"✅ Extracted {len(standardized_data)} match metrics")
            
            return standardized_data
            
        except Exception as e:
            if self.config.verbose:
                print(f"Error extracting match data: {str(e)}")
            return None
    
    def get_multiple_players_season_stats(
        self, 
        players: List[Dict[str, str]]
    ) -> pd.DataFrame:
        """
        Extract season statistics for multiple players efficiently.
        
        This method processes multiple player requests in batch, optimizing
        API calls and providing comprehensive datasets for comparative analysis.
        
        Args:
            players: List of player configurations, each containing:
                - 'name': Player name
                - 'league': League identifier  
                - 'season': Season identifier
                
        Returns:
            DataFrame with all players' statistics in standardized format.
            
        Example:
            >>> players = [
            ...     {'name': 'Mbappé', 'league': 'ESP-La Liga', 'season': '2024-25'},
            ...     {'name': 'Haaland', 'league': 'ENG-Premier League', 'season': '2024-25'}
            ... ]
            >>> df = extractor.get_multiple_players_season_stats(players)
        """
        all_data = []
        
        for i, player_config in enumerate(players, 1):
            if self.config.verbose:
                print(f"[{i}/{len(players)}] Processing {player_config['name']}")
            
            player_data = self.get_season_stats(
                player_config['name'],
                player_config['league'],
                player_config['season']
            )
            
            if player_data:
                all_data.append(player_data)
            elif self.config.verbose:
                print(f"  ⚠️ Failed to extract data for {player_config['name']}")
        
        return pd.DataFrame(all_data) if all_data else pd.DataFrame()
    
    def _get_fbref_instance(self, leagues: List[str], seasons: List[str]) -> FBref:
        """
        Get or create FBref instance with caching for performance optimization.
        
        Args:
            leagues: List of league identifiers
            seasons: List of season identifiers
            
        Returns:
            Configured FBref instance
        """
        cache_key = f"{'-'.join(leagues)}_{'-'.join(seasons)}"
        
        if cache_key not in self._fbref_cache:
            self._fbref_cache[cache_key] = FBref(leagues=leagues, seasons=seasons)
        
        return self._fbref_cache[cache_key]
    
    def _create_season_extraction_plan(self) -> List[str]:
        """
        Define the extraction strategy for season-level statistics.
        
        Returns:
            List of stat types to extract in optimal order
        """
        base_stats = [
            'standard',      # Core performance metrics
            'shooting',      # Shot creation and conversion
            'passing',       # Passing accuracy and types
            'passing_types', # Advanced passing metrics
            'goal_shot_creation',  # SCA and GCA statistics
            'defense',       # Defensive contributions
            'possession',    # Touch and carry data
            'playing_time',  # Minutes and appearances
            'misc'          # Disciplinary and other metrics
        ]
        
        if self.config.include_keeper_stats:
            base_stats.extend(['keeper', 'keeper_adv'])
        
        return base_stats
    
    def _execute_extraction_plan(
        self, 
        fbref: FBref, 
        player_name: str, 
        extraction_plan: List[str]
    ) -> Dict[str, Union[str, int, float]]:
        """
        Execute the statistical extraction plan for a player.
        
        Args:
            fbref: Configured FBref instance
            player_name: Target player name
            extraction_plan: List of stat types to extract
            
        Returns:
            Combined dictionary of all extracted statistics
        """
        player_data = {}
        basic_info = {}
        
        for i, stat_type in enumerate(extraction_plan, 1):
            if self.config.verbose:
                print(f"  [{i}/{len(extraction_plan)}] Processing {stat_type}")
            
            try:
                stats_df = fbref.read_player_season_stats(stat_type=stat_type)
                player_row = self._find_player_in_dataframe(stats_df, player_name)
                
                if player_row is not None:
                    # Capture basic information on first successful extraction
                    if not basic_info:
                        basic_info = self._extract_basic_info(player_row, player_name)
                    
                    # Process all statistical columns
                    row_data = self._dataframe_row_to_dict(player_row)
                    
                    # Merge without overwriting existing keys
                    for key, value in row_data.items():
                        if key not in player_data:
                            player_data[key] = value
                            
            except Exception as e:
                if self.config.verbose:
                    print(f"    ⚠️ Could not extract {stat_type}: {str(e)[:50]}...")
                continue
        
        # Combine basic info with statistics
        return {**basic_info, **player_data}
    
    def _find_player_in_dataframe(
        self, 
        df: pd.DataFrame, 
        player_name: str
    ) -> Optional[pd.DataFrame]:
        """
        Locate a player in a DataFrame using flexible name matching.
        
        This method implements sophisticated name matching to handle:
        - Partial names (e.g., "Mbappé" matches "Kylian Mbappé")
        - Accent variations (e.g., "Mbappe" matches "Mbappé")
        - Different name orders
        
        Args:
            df: DataFrame containing player statistics
            player_name: Target player name (full or partial)
            
        Returns:
            DataFrame row(s) for the matched player, or None if not found
        """
        if df is None or df.empty:
            return None
        
        # Generate comprehensive name variations
        name_variations = self._generate_name_variations(player_name)
        
        # Search through variations in order of specificity
        for variation in name_variations:
            matches = df[
                df.index.get_level_values('player').str.contains(
                    variation, case=False, na=False, regex=False
                )
            ]
            if not matches.empty:
                return matches
        
        return None
    
    def _generate_name_variations(self, player_name: str) -> List[str]:
        """
        Generate comprehensive name variations for flexible matching.
        
        Args:
            player_name: Original player name
            
        Returns:
            List of name variations ordered by matching priority
        """
        variations = [player_name]  # Start with exact name
        
        # Remove accents for broader matching
        accent_map = {
            'á': 'a', 'à': 'a', 'ä': 'a', 'â': 'a',
            'é': 'e', 'è': 'e', 'ë': 'e', 'ê': 'e',
            'í': 'i', 'ì': 'i', 'ï': 'i', 'î': 'i',
            'ó': 'o', 'ò': 'o', 'ö': 'o', 'ô': 'o',
            'ú': 'u', 'ù': 'u', 'ü': 'u', 'û': 'u',
            'ñ': 'n', 'ç': 'c'
        }
        
        deaccented = player_name
        for accented, plain in accent_map.items():
            deaccented = deaccented.replace(accented, plain)
        
        if deaccented != player_name:
            variations.append(deaccented)
        
        # Add name component variations
        if ' ' in player_name:
            name_parts = player_name.split()
            variations.extend([
                name_parts[-1],  # Last name only
                name_parts[0],   # First name only
            ])
        
        return variations
    
    def _extract_basic_info(
        self, 
        player_row: pd.DataFrame, 
        player_name: str
    ) -> Dict[str, str]:
        """
        Extract basic player information from a DataFrame row.
        
        Args:
            player_row: DataFrame row containing player data
            player_name: Original player name for consistency
            
        Returns:
            Dictionary with basic player information
        """
        return {
            'player_name': player_name,
            'league': player_row.index.get_level_values('league')[0],
            'season': player_row.index.get_level_values('season')[0],
            'team': player_row.index.get_level_values('team')[0]
        }
    
    def _dataframe_row_to_dict(self, df_row: pd.DataFrame) -> Dict[str, Union[str, int, float]]:
        """
        Convert a DataFrame row to a clean dictionary format.
        
        Args:
            df_row: Single-row DataFrame
            
        Returns:
            Dictionary with cleaned column names and values
        """
        row_dict = {}
        
        for col in df_row.columns:
            clean_name = self._clean_column_name(col)
            value = df_row.iloc[0][col]
            row_dict[clean_name] = value
        
        return row_dict
    
    def _clean_column_name(self, col: Union[str, tuple]) -> str:
        """
        Clean and standardize column names from FBref's multi-level headers.
        
        FBref uses hierarchical column names (e.g., ('Performance', 'Goals')).
        This method flattens them into readable single-level names.
        
        Args:
            col: Column name (string or tuple from MultiIndex)
            
        Returns:
            Cleaned, standardized column name
        """
        if isinstance(col, tuple):
            level0, level1 = col[0], col[1]
            
            # Handle empty or null second levels
            if level1 == '' or pd.isna(level1) or level1 is None:
                return level0
            
            # For common category headers, use only the specific metric name
            standard_categories = {
                'Standard', 'Performance', 'Expected', 'Total', 'Short', 
                'Medium', 'Long', 'Playing Time', 'Per 90 Minutes'
            }
            
            if level0 in standard_categories:
                return level1
            else:
                return f"{level0}_{level1}"
        
        return str(col)
    
    def _apply_standardization(
        self, 
        raw_data: Dict[str, Union[str, int, float]]
    ) -> Dict[str, Union[str, int, float]]:
        """
        Apply standardized naming conventions to statistical data.
        
        This method transforms FBref's technical column names into descriptive,
        analysis-friendly names following consistent naming patterns.
        
        Args:
            raw_data: Dictionary with original FBref column names
            
        Returns:
            Dictionary with standardized, descriptive column names
        """
        standardized = {}
        
        for original_name, value in raw_data.items():
            standard_name = self.stat_mapping.get(original_name, original_name)
            standardized[standard_name] = value
        
        return standardized
    
    def _initialize_stat_mapping(self) -> Dict[str, str]:
        """
        Initialize comprehensive mapping from FBref names to standardized names.
        
        This mapping ensures consistent column naming across different data sources
        and extraction methods, facilitating downstream analysis and visualization.
        
        Returns:
            Dictionary mapping FBref column names to standardized names
        """
        return {
            # Basic player information
            'nation': 'nationality',
            'pos': 'position', 
            'age': 'age',
            'born': 'birth_year',
            
            # Playing time and availability
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
            
            # Core performance metrics
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
            
            # Shooting and finishing
            'Sh': 'shots',
            'SoT': 'shots_on_target',
            'SoT%': 'shots_on_target_pct',
            'Sh/90': 'shots_per_90',
            'SoT/90': 'shots_on_target_per_90',
            'G/Sh': 'goals_per_shot',
            'G/SoT': 'goals_per_shot_on_target',
            'Dist': 'avg_shot_distance',
            'FK': 'free_kick_shots',
            
            # Expected performance metrics
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
            
            # Passing statistics
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
            
            # Pass types and techniques
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
            
            # Shot and goal creation
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
            
            # Defensive contributions
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
            
            # Possession and ball control
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
            
            # Team performance impact
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
            
            # Disciplinary record
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
            
            # Goalkeeper-specific metrics
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


# Convenience functions for direct usage
def get_player_season_stats(
    player_name: str, 
    league: str, 
    season: str, 
    verbose: bool = False
) -> Optional[Dict[str, Union[str, int, float]]]:
    """
    Simple convenience function for extracting player season statistics.
    
    Args:
        player_name: Player name (e.g., "Mbappé")
        league: League identifier (e.g., "ESP-La Liga")
        season: Season identifier (e.g., "2024-25")
        verbose: Whether to show extraction progress
        
    Returns:
        Dictionary with standardized player statistics or None if not found
        
    Example:
        >>> stats = get_player_season_stats("Mbappé", "ESP-La Liga", "2024-25")
        >>> print(f"Goals: {stats['goals']}")
    """
    config = PlayerExtractionConfig(verbose=verbose)
    extractor = PlayerDataExtractor(config)
    return extractor.get_season_stats(player_name, league, season)


def get_player_match_stats(
    player_name: str,
    match_id: str,
    stat_type: str = 'summary',
    verbose: bool = False
) -> Optional[Dict[str, Union[str, int, float]]]:
    """
    Simple convenience function for extracting player match statistics.
    
    Args:
        player_name: Player name
        match_id: FBref match identifier
        stat_type: Type of statistics ('summary', 'passing', 'defense', 'possession')
        verbose: Whether to show extraction progress
        
    Returns:
        Dictionary with standardized match statistics or None if not found
        
    Example:
        >>> stats = get_player_match_stats("Mbappé", "abc12345", "summary")
        >>> print(f"Match goals: {stats['goals']}")
    """
    config = PlayerExtractionConfig(verbose=verbose)
    extractor = PlayerDataExtractor(config)
    return extractor.get_match_stats(player_name, match_id, stat_type)