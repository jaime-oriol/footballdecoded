# FootballDecoded - Player Data Extractor
# Professional module for extracting comprehensive player statistics from FBref

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from extractors import FBref
from typing import List, Dict, Optional, Union


class PlayerDataExtractor:
    """
    Extracts comprehensive player statistics from FBref with standardized column names.
    Handles both outfield players and goalkeepers automatically.
    """
    
    def __init__(self):
        """Initialize the extractor with predefined stat mappings."""
        self.stat_mapping = self._get_stat_mapping()
        self.outfield_stat_types = [
            'standard', 'shooting', 'passing', 'passing_types', 
            'goal_shot_creation', 'defense', 'possession', 
            'playing_time', 'misc'
        ]
        self.keeper_stat_types = ['keeper', 'keeper_adv']
    
    def _get_stat_mapping(self) -> Dict[str, str]:
        """Define mapping from FBref column names to standardized descriptive names."""
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
            
            # Performance
            'Gls': 'goals',
            'Ast': 'assists', 
            'G+A': 'goals_plus_assists',
            'G-PK': 'non_penalty_goals',
            'PK': 'penalty_goals',
            'PKatt': 'penalty_attempts',
            'CrdY': 'yellow_cards',
            'CrdR': 'red_cards',
            
            # Expected metrics
            'xG': 'expected_goals',
            'npxG': 'non_penalty_expected_goals',
            'xAG': 'expected_assists',
            'xA': 'expected_assists_alt',
            'G-xG': 'goals_minus_expected',
            'np:G-xG': 'non_penalty_goals_minus_expected',
            'A-xAG': 'assists_minus_expected',
            
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
            
            # Defense
            'Tkl': 'tackles',
            'TklW': 'tackles_won',
            'Int': 'interceptions',
            'Tkl+Int': 'tackles_plus_interceptions',
            'Clr': 'clearances',
            'Err': 'errors',
            
            # Possession
            'Touches': 'touches',
            'Succ': 'successful_take_ons',
            'Succ%': 'take_on_success_pct',
            'Tkld': 'tackled_during_take_on',
            'Tkld%': 'tackled_during_take_on_pct',
            'Carries': 'carries',
            'PrgC': 'progressive_carries',
            'Mis': 'miscontrols',
            'Dis': 'dispossessed',
            
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
            'PKm': 'penalty_kicks_missed_against',
            'Save%_penalty': 'penalty_save_percentage',
            
            # Disciplinary
            'Fls': 'fouls_committed',
            'Fld': 'fouls_drawn',
            'Off': 'offsides',
            'Crs': 'crosses',
            'PKwon': 'penalties_won',
            'PKcon': 'penalties_conceded',
            'OG': 'own_goals',
            'Recov': 'ball_recoveries',
            
            # Aerial duels
            'Won': 'aerial_duels_won',
            'Lost': 'aerial_duels_lost',
            'Won%': 'aerial_duels_won_pct'
        }
    
    def _clean_column_name(self, col: Union[str, tuple]) -> str:
        """
        Clean and standardize column names from FBref's multi-level headers.
        
        Args:
            col: Column name, either string or tuple from multi-index
            
        Returns:
            Cleaned column name as string
        """
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
    
    def _find_player(self, stats: pd.DataFrame, player_name: str) -> Optional[pd.DataFrame]:
        """
        Search for a player in the statistics DataFrame using flexible name matching.
        
        Args:
            stats: DataFrame containing player statistics
            player_name: Name of player to search for
            
        Returns:
            DataFrame row(s) for the player if found, None otherwise
        """
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
    
    def extract_player_data(
        self, 
        player_name: str, 
        leagues: List[str], 
        seasons: List[str], 
        include_keeper_stats: bool = True
    ) -> Dict[str, Union[str, int, float]]:
        """
        Extract comprehensive statistics for a single player.
        
        Args:
            player_name: Name of the player to extract data for
            leagues: List of league identifiers (e.g., ["ESP-La Liga", "UEFA-Champions League"])
            seasons: List of season identifiers (e.g., ["2023-24", "2024-25"])
            include_keeper_stats: Whether to include goalkeeper-specific statistics
            
        Returns:
            Dictionary containing all available statistics for the player
        """
        # Determine which stat types to extract
        stat_types = self.outfield_stat_types.copy()
        if include_keeper_stats:
            stat_types.extend(self.keeper_stat_types)
        
        # Initialize FBref extractor
        fbref = FBref(leagues=leagues, seasons=seasons)
        
        player_data = {}
        basic_info = {}
        
        # Extract each type of statistic
        for stat_type in stat_types:
            try:
                stats = fbref.read_player_season_stats(stat_type=stat_type)
                player_row = self._find_player(stats, player_name)
                
                if player_row is not None:
                    # Capture basic info on first successful extraction
                    if not basic_info:
                        basic_info = {
                            'player_name': player_name,
                            'league': player_row.index.get_level_values('league')[0],
                            'season': player_row.index.get_level_values('season')[0],
                            'team': player_row.index.get_level_values('team')[0]
                        }
                    
                    # Process all columns from this stat type
                    for col in player_row.columns:
                        clean_name = self._clean_column_name(col)
                        value = player_row.iloc[0][col]
                        
                        # Avoid overwriting existing data
                        if clean_name not in player_data:
                            player_data[clean_name] = value
                            
            except Exception:
                # Continue processing other stat types if one fails
                continue
        
        # Combine basic info with statistics
        final_data = {**basic_info, **player_data}
        
        # Apply standardized naming
        processed_data = {}
        for original_name, value in final_data.items():
            standardized_name = self.stat_mapping.get(original_name, original_name)
            processed_data[standardized_name] = value
        
        return processed_data
    
    def extract_multiple_players(
        self, 
        player_names: List[str], 
        leagues: List[str], 
        seasons: List[str], 
        include_keeper_stats: bool = True
    ) -> pd.DataFrame:
        """
        Extract statistics for multiple players and return as DataFrame.
        
        Args:
            player_names: List of player names to extract data for
            leagues: List of league identifiers
            seasons: List of season identifiers
            include_keeper_stats: Whether to include goalkeeper statistics
            
        Returns:
            DataFrame with one row per player and standardized columns
        """
        all_players_data = []
        
        for player_name in player_names:
            player_data = self.extract_player_data(
                player_name, leagues, seasons, include_keeper_stats
            )
            
            if player_data:  # Only add if data was successfully extracted
                all_players_data.append(player_data)
        
        return pd.DataFrame(all_players_data) if all_players_data else pd.DataFrame()


# Convenience functions for direct usage
def extract_player(
    player_name: str, 
    leagues: List[str], 
    seasons: List[str], 
    include_keeper_stats: bool = True
) -> Dict[str, Union[str, int, float]]:
    """
    Convenience function to extract data for a single player.
    
    Args:
        player_name: Name of the player
        leagues: List of leagues
        seasons: List of seasons
        include_keeper_stats: Include goalkeeper statistics
        
    Returns:
        Dictionary with player statistics
    """
    extractor = PlayerDataExtractor()
    return extractor.extract_player_data(player_name, leagues, seasons, include_keeper_stats)


def extract_players(
    player_names: List[str], 
    leagues: List[str], 
    seasons: List[str], 
    include_keeper_stats: bool = True
) -> pd.DataFrame:
    """
    Convenience function to extract data for multiple players.
    
    Args:
        player_names: List of player names
        leagues: List of leagues
        seasons: List of seasons
        include_keeper_stats: Include goalkeeper statistics
        
    Returns:
        DataFrame with all players' statistics
    """
    extractor = PlayerDataExtractor()
    return extractor.extract_multiple_players(player_names, leagues, seasons, include_keeper_stats)