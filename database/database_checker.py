# ====================================================================
# FootballDecoded Database Status Checker
# ====================================================================

import sys
import os
import pandas as pd
from typing import Dict

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.connection import get_db_manager

# ====================================================================
# DATABASE STATUS FUNCTIONS
# ====================================================================

def check_database_status(verbose: bool = True) -> Dict[str, pd.DataFrame]:
    """Check available data in database with comprehensive reporting."""
    if verbose:
        print("Checking FootballDecoded Database Status")
        print("=" * 60)
    
    db = get_db_manager()
    results = {}
    
    try:
        # Domestic players query
        query_players_domestic = """
        SELECT 
            league,
            season,
            COUNT(*) as total_players,
            COUNT(DISTINCT team) as total_teams,
            COUNT(CASE WHEN understat_metrics IS NOT NULL THEN 1 END) as with_understat,
            MIN(created_at::date) as first_loaded,
            MAX(updated_at::date) as last_updated
        FROM footballdecoded.players_domestic 
        GROUP BY league, season 
        ORDER BY league, season DESC
        """
        
        players_domestic = pd.read_sql(query_players_domestic, db.engine)
        results['players_domestic'] = players_domestic
        
        if verbose and not players_domestic.empty:
            print("DOMESTIC PLAYERS (FBref + Understat)")
            print("-" * 50)
            for _, row in players_domestic.iterrows():
                understat_pct = (row['with_understat'] / row['total_players'] * 100) if row['total_players'] > 0 else 0
                print(f"   {row['league']} {row['season']}: {row['total_players']} players | {row['total_teams']} teams | Understat: {understat_pct:.1f}%")
            print()
        
        # European players query
        query_players_european = """
        SELECT 
            competition,
            season,
            COUNT(*) as total_players,
            COUNT(DISTINCT team) as total_teams,
            MIN(created_at::date) as first_loaded,
            MAX(updated_at::date) as last_updated
        FROM footballdecoded.players_european 
        GROUP BY competition, season 
        ORDER BY competition, season DESC
        """
        
        players_european = pd.read_sql(query_players_european, db.engine)
        results['players_european'] = players_european
        
        if verbose and not players_european.empty:
            print("EUROPEAN PLAYERS (FBref only)")
            print("-" * 50)
            for _, row in players_european.iterrows():
                print(f"   {row['competition']} {row['season']}: {row['total_players']} players | {row['total_teams']} teams")
            print()
        
        # Domestic teams query
        query_teams_domestic = """
        SELECT 
            league,
            season,
            COUNT(*) as total_teams,
            COUNT(CASE WHEN understat_metrics IS NOT NULL THEN 1 END) as with_understat,
            MIN(created_at::date) as first_loaded,
            MAX(updated_at::date) as last_updated
        FROM footballdecoded.teams_domestic 
        GROUP BY league, season 
        ORDER BY league, season DESC
        """
        
        teams_domestic = pd.read_sql(query_teams_domestic, db.engine)
        results['teams_domestic'] = teams_domestic
        
        if verbose and not teams_domestic.empty:
            print("DOMESTIC TEAMS (FBref + Understat)")
            print("-" * 50)
            for _, row in teams_domestic.iterrows():
                understat_pct = (row['with_understat'] / row['total_teams'] * 100) if row['total_teams'] > 0 else 0
                print(f"   {row['league']} {row['season']}: {row['total_teams']} teams | Understat: {understat_pct:.1f}%")
            print()
        
        # European teams query
        query_teams_european = """
        SELECT 
            competition,
            season,
            COUNT(*) as total_teams,
            MIN(created_at::date) as first_loaded,
            MAX(updated_at::date) as last_updated
        FROM footballdecoded.teams_european 
        GROUP BY competition, season 
        ORDER BY competition, season DESC
        """
        
        teams_european = pd.read_sql(query_teams_european, db.engine)
        results['teams_european'] = teams_european
        
        if verbose and not teams_european.empty:
            print("EUROPEAN TEAMS (FBref only)")
            print("-" * 50)
            for _, row in teams_european.iterrows():
                print(f"   {row['competition']} {row['season']}: {row['total_teams']} teams")
            print()
        
        # Summary totals
        if verbose:
            total_domestic_players = players_domestic['total_players'].sum() if not players_domestic.empty else 0
            total_european_players = players_european['total_players'].sum() if not players_european.empty else 0
            total_domestic_teams = teams_domestic['total_teams'].sum() if not teams_domestic.empty else 0
            total_european_teams = teams_european['total_teams'].sum() if not teams_european.empty else 0
            
            print("SUMMARY")
            print("-" * 50)
            print(f"   Domestic players: {total_domestic_players}")
            print(f"   European players: {total_european_players}")
            print(f"   Domestic teams: {total_domestic_teams}")
            print(f"   European teams: {total_european_teams}")
            print(f"   TOTAL: {total_domestic_players + total_european_players + total_domestic_teams + total_european_teams} records")
        
        db.close()
        return results
        
    except Exception as e:
        if verbose:
            print(f"Error checking database: {e}")
        db.close()
        return {}

def quick_status():
    """Quick database status check without details."""
    print("Quick database status:")
    
    db = get_db_manager()
    
    tables = [
        ('players_domestic', 'Domestic players'),
        ('players_european', 'European players'),
        ('teams_domestic', 'Domestic teams'),
        ('teams_european', 'European teams')
    ]
    
    total_records = 0
    
    for table_name, display_name in tables:
        try:
            count = pd.read_sql(f"SELECT COUNT(*) as count FROM footballdecoded.{table_name}", db.engine)
            records = count.iloc[0]['count']
            total_records += records
            print(f"   {display_name}: {records}")
        except Exception:
            print(f"   {display_name}: 0 (table does not exist)")
    
    print(f"   TOTAL: {total_records} records")
    db.close()

# ====================================================================
# MAIN EXECUTION
# ====================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        quick_status()
    else:
        check_database_status(verbose=True)