# ====================================================================
# FootballDecoded Data Loading Pipeline
# ====================================================================
# Loads data from wrappers into PostgreSQL database
# ====================================================================

import sys
import os
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime

# Add wrappers to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wrappers import (fbref_get_player, fbref_get_team, fbref_get_players, fbref_get_teams,
                     understat_get_player, understat_get_team, understat_merge_with_fbref)
from database.connection import DatabaseManager, get_db_manager

# ====================================================================
# CONFIGURATION
# ====================================================================

# Major European leagues
DOMESTIC_LEAGUES = [
    'ENG-Premier League',
    'ESP-La Liga', 
    'ITA-Serie A',
    'GER-Bundesliga',
    'FRA-Ligue 1'
]

# European competitions
EUROPEAN_COMPETITIONS = [
    'INT-Champions League'
]

# Current season
CURRENT_SEASON = '2024-25'

# ====================================================================
# DATA LOADER CLASS
# ====================================================================

class FootballDataLoader:
    """Manages data loading from wrappers to database."""
    
    def __init__(self):
        self.db = get_db_manager()
        
    def load_domestic_players(self, leagues: List[str] = None, season: str = CURRENT_SEASON, 
                            verbose: bool = True) -> Dict[str, int]:
        """
        Load domestic league players (FBref + Understat).
        
        Args:
            leagues: List of leagues to process
            season: Season to load
            verbose: Show progress
            
        Returns:
            Dict with load statistics
        """
        if leagues is None:
            leagues = DOMESTIC_LEAGUES
            
        stats = {'total_players': 0, 'successful': 0, 'failed': 0}
        
        for league in leagues:
            if verbose:
                print(f"\n🔍 Loading {league} players for {season}")
            
            try:
                # Get all players from league using FBref
                from wrappers import fbref_get_league_players
                players_list_df = fbref_get_league_players(league, season)
                
                if players_list_df.empty:
                    if verbose:
                        print(f"   ⚠️ No players found for {league}")
                    continue
                
                players_list = players_list_df['player'].unique().tolist()
                stats['total_players'] += len(players_list)
                
                if verbose:
                    print(f"   📊 Found {len(players_list)} players")
                
                # Process players in batches
                batch_size = 10
                for i in range(0, len(players_list), batch_size):
                    batch = players_list[i:i + batch_size]
                    
                    if verbose:
                        print(f"   Processing batch {i//batch_size + 1}/{(len(players_list)-1)//batch_size + 1}")
                    
                    for player_name in batch:
                        if self._load_single_domestic_player(player_name, league, season, verbose=False):
                            stats['successful'] += 1
                        else:
                            stats['failed'] += 1
                            
            except Exception as e:
                if verbose:
                    print(f"   ❌ Failed to load {league}: {e}")
                continue
        
        if verbose:
            print(f"\n✅ Domestic players loading complete:")
            print(f"   Total: {stats['total_players']}")
            print(f"   Successful: {stats['successful']}")
            print(f"   Failed: {stats['failed']}")
            
        return stats
    
    def load_european_players(self, competitions: List[str] = None, season: str = CURRENT_SEASON,
                            verbose: bool = True) -> Dict[str, int]:
        """
        Load European competition players (FBref only).
        
        Args:
            competitions: List of competitions to process
            season: Season to load
            verbose: Show progress
            
        Returns:
            Dict with load statistics
        """
        if competitions is None:
            competitions = EUROPEAN_COMPETITIONS
            
        stats = {'total_players': 0, 'successful': 0, 'failed': 0}
        
        for competition in competitions:
            if verbose:
                print(f"\n🏆 Loading {competition} players for {season}")
            
            try:
                # Get all players from competition using FBref
                from wrappers import fbref_get_league_players
                players_list_df = fbref_get_league_players(competition, season)
                
                if players_list_df.empty:
                    if verbose:
                        print(f"   ⚠️ No players found for {competition}")
                    continue
                
                players_list = players_list_df['player'].unique().tolist()
                stats['total_players'] += len(players_list)
                
                if verbose:
                    print(f"   📊 Found {len(players_list)} players")
                
                # Process players in batches
                batch_size = 10
                for i in range(0, len(players_list), batch_size):
                    batch = players_list[i:i + batch_size]
                    
                    if verbose:
                        print(f"   Processing batch {i//batch_size + 1}/{(len(players_list)-1)//batch_size + 1}")
                    
                    for player_name in batch:
                        if self._load_single_european_player(player_name, competition, season, verbose=False):
                            stats['successful'] += 1
                        else:
                            stats['failed'] += 1
                            
            except Exception as e:
                if verbose:
                    print(f"   ❌ Failed to load {competition}: {e}")
                continue
        
        if verbose:
            print(f"\n✅ European players loading complete:")
            print(f"   Total: {stats['total_players']}")
            print(f"   Successful: {stats['successful']}")
            print(f"   Failed: {stats['failed']}")
            
        return stats
    
    def load_domestic_teams(self, leagues: List[str] = None, season: str = CURRENT_SEASON,
                          verbose: bool = True) -> Dict[str, int]:
        """
        Load domestic league teams (FBref + Understat).
        
        Args:
            leagues: List of leagues to process
            season: Season to load
            verbose: Show progress
            
        Returns:
            Dict with load statistics
        """
        if leagues is None:
            leagues = DOMESTIC_LEAGUES
            
        stats = {'total_teams': 0, 'successful': 0, 'failed': 0}
        
        for league in leagues:
            if verbose:
                print(f"\n🏟️ Loading {league} teams for {season}")
            
            try:
                # Get teams from FBref
                from wrappers import fbref_get_schedule
                schedule_df = fbref_get_schedule(league, season)
                
                if schedule_df.empty:
                    if verbose:
                        print(f"   ⚠️ No schedule found for {league}")
                    continue
                
                # Extract unique teams
                teams_list = []
                if 'home_team' in schedule_df.columns:
                    teams_list.extend(schedule_df['home_team'].unique().tolist())
                if 'away_team' in schedule_df.columns:
                    teams_list.extend(schedule_df['away_team'].unique().tolist())
                
                teams_list = list(set([t for t in teams_list if pd.notna(t)]))
                stats['total_teams'] += len(teams_list)
                
                if verbose:
                    print(f"   📊 Found {len(teams_list)} teams")
                
                # Process each team
                for team_name in teams_list:
                    if self._load_single_domestic_team(team_name, league, season, verbose=False):
                        stats['successful'] += 1
                    else:
                        stats['failed'] += 1
                        
            except Exception as e:
                if verbose:
                    print(f"   ❌ Failed to load {league}: {e}")
                continue
        
        if verbose:
            print(f"\n✅ Domestic teams loading complete:")
            print(f"   Total: {stats['total_teams']}")
            print(f"   Successful: {stats['successful']}")
            print(f"   Failed: {stats['failed']}")
            
        return stats
    
    def _load_single_domestic_player(self, player_name: str, league: str, season: str, 
                                   verbose: bool = False) -> bool:
        """Load single domestic player with FBref + Understat data."""
        try:
            # Get FBref data
            fbref_data = fbref_get_player(player_name, league, season)
            if not fbref_data:
                if verbose:
                    print(f"   ⚠️ No FBref data for {player_name}")
                return False
            
            # Get Understat data
            understat_data = understat_get_player(player_name, league, season)
            
            # Merge data
            if understat_data:
                # Combine both sources
                combined_data = {**fbref_data, **understat_data}
                combined_data['understat_official_name'] = understat_data.get('official_player_name')
            else:
                combined_data = fbref_data
                combined_data['understat_official_name'] = None
            
            combined_data['fbref_official_name'] = combined_data.get('player_name')
            
            # Insert into database
            return self.db.insert_player_data(combined_data, 'domestic')
            
        except Exception as e:
            if verbose:
                print(f"   ❌ Error loading {player_name}: {e}")
            return False
    
    def _load_single_european_player(self, player_name: str, competition: str, season: str,
                                   verbose: bool = False) -> bool:
        """Load single European player with FBref data only."""
        try:
            # Get FBref data
            fbref_data = fbref_get_player(player_name, competition, season)
            if not fbref_data:
                if verbose:
                    print(f"   ⚠️ No FBref data for {player_name}")
                return False
            
            # Adjust for European table structure
            fbref_data['competition'] = fbref_data.pop('league')
            fbref_data['fbref_official_name'] = fbref_data.get('player_name')
            
            # Insert into database
            return self.db.insert_player_data(fbref_data, 'european')
            
        except Exception as e:
            if verbose:
                print(f"   ❌ Error loading {player_name}: {e}")
            return False
    
    def _load_single_domestic_team(self, team_name: str, league: str, season: str,
                                 verbose: bool = False) -> bool:
        """Load single domestic team with FBref + Understat data."""
        try:
            # Get FBref data
            fbref_data = fbref_get_team(team_name, league, season)
            if not fbref_data:
                if verbose:
                    print(f"   ⚠️ No FBref data for {team_name}")
                return False
            
            # Get Understat data
            understat_data = understat_get_team(team_name, league, season)
            
            # Merge data
            if understat_data:
                combined_data = {**fbref_data, **understat_data}
                combined_data['understat_official_name'] = understat_data.get('official_team_name')
            else:
                combined_data = fbref_data
                combined_data['understat_official_name'] = None
            
            combined_data['fbref_official_name'] = combined_data.get('official_team_name')
            
            # Insert into database
            return self.db.insert_team_data(combined_data, 'domestic')
            
        except Exception as e:
            if verbose:
                print(f"   ❌ Error loading {team_name}: {e}")
            return False

# ====================================================================
# CONVENIENCE FUNCTIONS
# ====================================================================

def load_sample_data(verbose: bool = True):
    """Load sample data for testing."""
    loader = FootballDataLoader()
    
    if verbose:
        print("🧪 Loading sample data...")
    
    # Load a few players from Real Madrid
    sample_players = ["Kylian Mbappé", "Vinicius Jr", "Jude Bellingham"]
    
    for player in sample_players:
        success = loader._load_single_domestic_player(player, "ESP-La Liga", CURRENT_SEASON, verbose)
        if verbose:
            status = "✅" if success else "❌"
            print(f"   {status} {player}")
    
    # Load Real Madrid team data
    success = loader._load_single_domestic_team("Real Madrid", "ESP-La Liga", CURRENT_SEASON, verbose)
    if verbose:
        status = "✅" if success else "❌"
        print(f"   {status} Real Madrid")

def load_full_league(league: str, season: str = CURRENT_SEASON, verbose: bool = True):
    """Load complete league data (players + teams)."""
    loader = FootballDataLoader()
    
    if verbose:
        print(f"🚀 Loading complete {league} data for {season}")
    
    # Load players
    player_stats = loader.load_domestic_players([league], season, verbose)
    
    # Load teams  
    team_stats = loader.load_domestic_teams([league], season, verbose)
    
    return {
        'players': player_stats,
        'teams': team_stats
    }

def load_all_domestic_data(season: str = CURRENT_SEASON, verbose: bool = True):
    """Load all domestic leagues data."""
    loader = FootballDataLoader()
    
    if verbose:
        print(f"🌍 Loading ALL domestic data for {season}")
        print("This may take several hours...")
    
    # Load all domestic players and teams
    player_stats = loader.load_domestic_players(DOMESTIC_LEAGUES, season, verbose)
    team_stats = loader.load_domestic_teams(DOMESTIC_LEAGUES, season, verbose)
    
    return {
        'players': player_stats,
        'teams': team_stats,
        'leagues_processed': len(DOMESTIC_LEAGUES)
    }

def load_all_european_data(season: str = CURRENT_SEASON, verbose: bool = True):
    """Load all European competitions data."""
    loader = FootballDataLoader()
    
    if verbose:
        print(f"🏆 Loading ALL European data for {season}")
    
    # Load European players
    player_stats = loader.load_european_players(EUROPEAN_COMPETITIONS, season, verbose)
    
    return {
        'players': player_stats,
        'competitions_processed': len(EUROPEAN_COMPETITIONS)
    }

# ====================================================================
# MAIN EXECUTION
# ====================================================================

def main():
    """Main execution function with menu options."""
    print("=" * 60)
    print("FootballDecoded Data Loader")
    print("=" * 60)
    print("\nOptions:")
    print("1. Load sample data (testing)")
    print("2. Load single league")
    print("3. Load all domestic leagues") 
    print("4. Load European competitions")
    print("5. Setup database schema")
    print("6. Test database connection")
    
    choice = input("\nSelect option (1-6): ").strip()
    
    if choice == "1":
        load_sample_data(verbose=True)
        
    elif choice == "2":
        print("\nAvailable leagues:")
        for i, league in enumerate(DOMESTIC_LEAGUES, 1):
            print(f"  {i}. {league}")
        
        league_choice = input("Select league number: ").strip()
        try:
            league_idx = int(league_choice) - 1
            if 0 <= league_idx < len(DOMESTIC_LEAGUES):
                league = DOMESTIC_LEAGUES[league_idx]
                load_full_league(league, verbose=True)
            else:
                print("❌ Invalid league number")
        except ValueError:
            print("❌ Please enter a valid number")
            
    elif choice == "3":
        confirm = input("⚠️ This will load ALL domestic leagues (may take hours). Continue? (y/N): ")
        if confirm.lower() == 'y':
            load_all_domestic_data(verbose=True)
        else:
            print("Cancelled")
            
    elif choice == "4":
        load_all_european_data(verbose=True)
        
    elif choice == "5":
        from database.connection import setup_database
        if setup_database():
            print("✅ Database schema setup complete")
        else:
            print("❌ Database schema setup failed")
            
    elif choice == "6":
        from database.connection import test_connection
        test_connection()
        
    else:
        print("❌ Invalid option")

if __name__ == "__main__":
    main()