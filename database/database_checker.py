# ====================================================================
# FootballDecoded Database Status Checker - Sistema de IDs Únicos
# ====================================================================

import sys
import os
import pandas as pd
from typing import Dict

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.connection import get_db_manager

# ====================================================================
# CONSISTENT VISUAL FORMATTING
# ====================================================================

LINE_WIDTH = 80

def print_header(title: str):
    """Consistent header formatting matching data_loader."""
    print(title)
    print("═" * LINE_WIDTH)

def print_section(title: str):
    """Consistent section formatting."""
    print(title)
    print("─" * LINE_WIDTH)

def print_footer():
    """Consistent footer formatting."""
    print("═" * LINE_WIDTH)

# ====================================================================
# DATABASE STATUS FUNCTIONS
# ====================================================================

def check_database_status(verbose: bool = True) -> Dict[str, pd.DataFrame]:
    """Check available data in database with unique ID reporting."""
    if verbose:
        print_header("FootballDecoded Database Status - Unique ID System")
    
    db = get_db_manager()
    results = {}
    
    try:
        # Domestic players query with unique IDs
        query_players_domestic = """
        SELECT 
            league,
            season,
            COUNT(*) as total_records,
            COUNT(DISTINCT unique_player_id) as unique_players,
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
            print_section("DOMESTIC PLAYERS (FBref + Understat)")
            for _, row in players_domestic.iterrows():
                understat_pct = (row['with_understat'] / row['total_records'] * 100) if row['total_records'] > 0 else 0
                transfer_ratio = row['total_records'] / row['unique_players'] if row['unique_players'] > 0 else 1
                print(f"├─ {row['league']} {row['season']}: {row['unique_players']} players | {row['total_records']} records | Ratio: {transfer_ratio:.2f} | Understat: {understat_pct:.1f}%")
            print()
        
        # European players query with unique IDs
        query_players_european = """
        SELECT 
            competition,
            season,
            COUNT(*) as total_records,
            COUNT(DISTINCT unique_player_id) as unique_players,
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
            print_section("EUROPEAN PLAYERS (FBref only)")
            for _, row in players_european.iterrows():
                transfer_ratio = row['total_records'] / row['unique_players'] if row['unique_players'] > 0 else 1
                print(f"├─ {row['competition']} {row['season']}: {row['unique_players']} players | {row['total_records']} records | Ratio: {transfer_ratio:.2f}")
            print()
        
        # Domestic teams query with unique IDs
        query_teams_domestic = """
        SELECT 
            league,
            season,
            COUNT(*) as total_records,
            COUNT(DISTINCT unique_team_id) as unique_teams,
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
            print_section("DOMESTIC TEAMS (FBref + Understat)")
            for _, row in teams_domestic.iterrows():
                understat_pct = (row['with_understat'] / row['total_records'] * 100) if row['total_records'] > 0 else 0
                print(f"├─ {row['league']} {row['season']}: {row['unique_teams']} teams | Understat: {understat_pct:.1f}%")
            print()
        
        # European teams query with unique IDs
        query_teams_european = """
        SELECT 
            competition,
            season,
            COUNT(*) as total_records,
            COUNT(DISTINCT unique_team_id) as unique_teams,
            MIN(created_at::date) as first_loaded,
            MAX(updated_at::date) as last_updated
        FROM footballdecoded.teams_european 
        GROUP BY competition, season 
        ORDER BY competition, season DESC
        """
        
        teams_european = pd.read_sql(query_teams_european, db.engine)
        results['teams_european'] = teams_european
        
        if verbose and not teams_european.empty:
            print_section("EUROPEAN TEAMS (FBref only)")
            for _, row in teams_european.iterrows():
                print(f"├─ {row['competition']} {row['season']}: {row['unique_teams']} teams")
            print()
        
        # Transfers report using unique IDs
        if verbose:
            print_section("TRANSFER ANALYSIS (Multi-team players)")
            
            # Get transfers for domestic leagues
            transfers_domestic = db.get_transfers_by_unique_id('domestic')
            if not transfers_domestic.empty:
                print("Domestic leagues:")
                for _, transfer in transfers_domestic.head(5).iterrows():
                    print(f"├─ {transfer['player_name']} ({transfer['league']} {transfer['season']}): {transfer['teams_count']} teams - {transfer['teams_path']}")
                if len(transfers_domestic) > 5:
                    print(f"└─ ... and {len(transfers_domestic) - 5} more transfers")
            
            # Get transfers for european competitions
            transfers_european = db.get_transfers_by_unique_id('european')
            if not transfers_european.empty:
                print("European competitions:")
                for _, transfer in transfers_european.head(5).iterrows():
                    print(f"├─ {transfer['player_name']} ({transfer['league']} {transfer['season']}): {transfer['teams_count']} teams - {transfer['teams_path']}")
                if len(transfers_european) > 5:
                    print(f"└─ ... and {len(transfers_european) - 5} more transfers")
            
            if transfers_domestic.empty and transfers_european.empty:
                print("└─ No transfers detected")
            print()
        
        # Data quality summary
        if verbose:
            print_section("DATA QUALITY SUMMARY")
            
            quality_queries = [
                ("players_domestic", "SELECT 'players_domestic' as table_name, COUNT(*) as total_records, COUNT(DISTINCT unique_player_id) as unique_entities, AVG(data_quality_score) as avg_quality_score FROM footballdecoded.players_domestic WHERE unique_player_id IS NOT NULL"),
                ("players_european", "SELECT 'players_european' as table_name, COUNT(*) as total_records, COUNT(DISTINCT unique_player_id) as unique_entities, AVG(data_quality_score) as avg_quality_score FROM footballdecoded.players_european WHERE unique_player_id IS NOT NULL"),
                ("teams_domestic", "SELECT 'teams_domestic' as table_name, COUNT(*) as total_records, COUNT(DISTINCT unique_team_id) as unique_entities, AVG(data_quality_score) as avg_quality_score FROM footballdecoded.teams_domestic WHERE unique_team_id IS NOT NULL"),
                ("teams_european", "SELECT 'teams_european' as table_name, COUNT(*) as total_records, COUNT(DISTINCT unique_team_id) as unique_entities, AVG(data_quality_score) as avg_quality_score FROM footballdecoded.teams_european WHERE unique_team_id IS NOT NULL")
            ]
            
            for name, query in quality_queries:
                try:
                    result = pd.read_sql(query, db.engine)
                    if not result.empty and result.iloc[0]['total_records'] > 0:
                        row = result.iloc[0]
                        print(f"├─ {row['table_name']}: {row['total_records']} records | {row['unique_entities']} unique entities | Quality: {row['avg_quality_score']:.3f}")
                except Exception:
                    print(f"├─ {name}: Error retrieving quality data")
            print()
        
        # Overall summary with unique counts
        if verbose:
            unique_counts = db.get_unique_entities_count()
            
            total_domestic_records = players_domestic['total_records'].sum() if not players_domestic.empty else 0
            total_european_records = players_european['total_records'].sum() if not players_european.empty else 0
            total_domestic_teams = teams_domestic['total_records'].sum() if not teams_domestic.empty else 0
            total_european_teams = teams_european['total_records'].sum() if not teams_european.empty else 0
            
            print_section("SUMMARY")
            print(f"├─ Unique domestic players: {unique_counts.get('unique_domestic_players', 0)}")
            print(f"├─ Unique european players: {unique_counts.get('unique_european_players', 0)}")
            print(f"├─ Unique domestic teams: {unique_counts.get('unique_domestic_teams', 0)}")
            print(f"├─ Unique european teams: {unique_counts.get('unique_european_teams', 0)}")
            print(f"├─ Total records: {total_domestic_records + total_european_records + total_domestic_teams + total_european_teams}")
            
            # Transfer statistics
            total_transfers = len(transfers_domestic) + len(transfers_european) if 'transfers_domestic' in locals() and 'transfers_european' in locals() else 0
            if total_transfers > 0:
                print(f"└─ Players with transfers: {total_transfers}")
            else:
                print("└─ No transfers detected")
        
        print_footer()
        db.close()
        return results
        
    except Exception as e:
        if verbose:
            print(f"Error checking database: {e}")
        db.close()
        return {}

def check_unique_id_integrity(verbose: bool = True) -> Dict[str, any]:
    """Check integrity of unique ID system."""
    if verbose:
        print_header("Unique ID System Integrity Check")
    
    db = get_db_manager()
    results = {}
    
    try:
        # Check for missing unique IDs
        missing_ids_queries = {
            'players_domestic': "SELECT COUNT(*) as count FROM footballdecoded.players_domestic WHERE unique_player_id IS NULL",
            'players_european': "SELECT COUNT(*) as count FROM footballdecoded.players_european WHERE unique_player_id IS NULL",
            'teams_domestic': "SELECT COUNT(*) as count FROM footballdecoded.teams_domestic WHERE unique_team_id IS NULL",
            'teams_european': "SELECT COUNT(*) as count FROM footballdecoded.teams_european WHERE unique_team_id IS NULL"
        }
        
        print_section("Missing ID Check:")
        for table, query in missing_ids_queries.items():
            result = pd.read_sql(query, db.engine)
            missing_count = result.iloc[0]['count']
            results[f'{table}_missing_ids'] = missing_count
            if verbose:
                status = "OK" if missing_count == 0 else f"ERROR: {missing_count} missing"
                print(f"├─ {table}: {status}")
        print()
        
        # Check for duplicate unique IDs within same league/season/team
        print_section("Duplicate ID Check:")
        
        duplicate_queries = {
            'players_domestic': """
                SELECT unique_player_id, league, season, team, COUNT(*) as count 
                FROM footballdecoded.players_domestic 
                GROUP BY unique_player_id, league, season, team 
                HAVING COUNT(*) > 1
            """,
            'players_european': """
                SELECT unique_player_id, competition, season, team, COUNT(*) as count 
                FROM footballdecoded.players_european 
                GROUP BY unique_player_id, competition, season, team 
                HAVING COUNT(*) > 1
            """
        }
        
        for table, query in duplicate_queries.items():
            duplicates = pd.read_sql(query, db.engine)
            results[f'{table}_duplicates'] = len(duplicates)
            if verbose:
                status = "OK" if len(duplicates) == 0 else f"ERROR: {len(duplicates)} duplicates"
                print(f"├─ {table}: {status}")
        print()
        
        # Check ID format consistency
        print_section("ID Format Check:")
        
        format_queries = {
            'players_domestic': "SELECT COUNT(*) as count FROM footballdecoded.players_domestic WHERE LENGTH(unique_player_id) != 16",
            'players_european': "SELECT COUNT(*) as count FROM footballdecoded.players_european WHERE LENGTH(unique_player_id) != 16",
            'teams_domestic': "SELECT COUNT(*) as count FROM footballdecoded.teams_domestic WHERE LENGTH(unique_team_id) != 16",
            'teams_european': "SELECT COUNT(*) as count FROM footballdecoded.teams_european WHERE LENGTH(unique_team_id) != 16"
        }
        
        for table, query in format_queries.items():
            result = pd.read_sql(query, db.engine)
            invalid_count = result.iloc[0]['count']
            results[f'{table}_invalid_format'] = invalid_count
            if verbose:
                status = "OK" if invalid_count == 0 else f"ERROR: {invalid_count} invalid format"
                print(f"├─ {table}: {status}")
        
        print_footer()
        db.close()
        return results
        
    except Exception as e:
        if verbose:
            print(f"Error checking ID integrity: {e}")
        db.close()
        return {}

def analyze_transfers(league: str = None, season: str = None, verbose: bool = True) -> pd.DataFrame:
    """Detailed transfer analysis using unique ID system."""
    if verbose:
        filter_text = f" for {league} {season}" if league and season else ""
        print_header(f"Transfer Analysis{filter_text}")
    
    db = get_db_manager()
    
    try:
        # Get all transfers
        transfers_domestic = db.get_transfers_by_unique_id('domestic')
        transfers_european = db.get_transfers_by_unique_id('european')
        
        # Combine and filter
        all_transfers = pd.concat([transfers_domestic, transfers_european], ignore_index=True) if not transfers_domestic.empty or not transfers_european.empty else pd.DataFrame()
        
        if league:
            all_transfers = all_transfers[all_transfers['league'] == league]
        if season:
            all_transfers = all_transfers[all_transfers['season'] == season]
        
        if verbose:
            if not all_transfers.empty:
                print(f"Found {len(all_transfers)} players with multiple teams")
                print()
                print_section("Top transfers by team count:")
                for _, transfer in all_transfers.head(10).iterrows():
                    print(f"├─ {transfer['player_name']} ({transfer['league']} {transfer['season']})")
                    print(f"   Teams: {transfer['teams_path']} | Quality: {transfer['avg_quality']:.3f}")
                print()
                
                # Statistics
                print_section("Transfer Statistics:")
                print(f"├─ Average teams per transfer: {all_transfers['teams_count'].mean():.2f}")
                print(f"├─ Max teams for one player: {all_transfers['teams_count'].max()}")
                print(f"└─ Players with 3+ teams: {len(all_transfers[all_transfers['teams_count'] >= 3])}")
            else:
                print("└─ No transfers found with current filters")
        
        print_footer()
        db.close()
        return all_transfers
        
    except Exception as e:
        if verbose:
            print(f"Error analyzing transfers: {e}")
        db.close()
        return pd.DataFrame()

def quick_status():
    """Quick database status check with unique ID info."""
    print_header("FootballDecoded Database Quick Status")
    
    db = get_db_manager()
    
    try:
        unique_counts = db.get_unique_entities_count()
        
        print_section("UNIQUE ENTITIES")
        print(f"├─ Unique domestic players: {unique_counts.get('unique_domestic_players', 0)}")
        print(f"├─ Unique european players: {unique_counts.get('unique_european_players', 0)}")
        print(f"├─ Unique domestic teams: {unique_counts.get('unique_domestic_teams', 0)}")
        print(f"└─ Unique european teams: {unique_counts.get('unique_european_teams', 0)}")
        print()
        
        # Total records
        tables = [
            ('players_domestic', 'Domestic player records'),
            ('players_european', 'European player records'),
            ('teams_domestic', 'Domestic team records'),
            ('teams_european', 'European team records')
        ]
        
        print_section("RECORD COUNTS")
        total_records = 0
        for i, (table_name, display_name) in enumerate(tables):
            try:
                count = pd.read_sql(f"SELECT COUNT(*) as count FROM footballdecoded.{table_name}", db.engine)
                records = count.iloc[0]['count']
                total_records += records
                connector = "├─" if i < len(tables) - 1 else "├─"
                print(f"{connector} {display_name}: {records}")
            except Exception:
                connector = "├─" if i < len(tables) - 1 else "├─"
                print(f"{connector} {display_name}: 0 (table does not exist)")
        
        print(f"└─ TOTAL RECORDS: {total_records}")
        print()
        
        # Quick transfer count
        transfers_domestic = db.get_transfers_by_unique_id('domestic')
        transfers_european = db.get_transfers_by_unique_id('european')
        total_transfers = len(transfers_domestic) + len(transfers_european)
        
        print_section("TRANSFER DETECTION")
        print(f"└─ Players with transfers: {total_transfers}")
        
        print_footer()
        db.close()
        
    except Exception as e:
        print(f"└─ Error: {e}")
        db.close()

# ====================================================================
# MAIN EXECUTION
# ====================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--quick':
            quick_status()
        elif sys.argv[1] == '--integrity':
            check_unique_id_integrity(verbose=True)
        elif sys.argv[1] == '--transfers':
            analyze_transfers(verbose=True)
        else:
            print("Usage: python database_checker.py [--quick|--integrity|--transfers]")
    else:
        check_database_status(verbose=True)