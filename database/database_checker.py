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
# CONFIGURATION
# ====================================================================

LINE_WIDTH = 80

TABLE_CONFIGS = {
    'players_domestic': {
        'id_field': 'unique_player_id',
        'league_field': 'league',
        'has_understat': True
    },
    'players_european': {
        'id_field': 'unique_player_id', 
        'league_field': 'competition',
        'has_understat': False
    },
    'teams_domestic': {
        'id_field': 'unique_team_id',
        'league_field': 'league', 
        'has_understat': True
    },
    'teams_european': {
        'id_field': 'unique_team_id',
        'league_field': 'competition',
        'has_understat': False
    }
}

# ====================================================================
# VISUAL FORMATTING
# ====================================================================

def print_header(title: str):
    print(title)
    print("═" * LINE_WIDTH)

def print_section(title: str):
    print(title)
    print("─" * LINE_WIDTH)

def print_footer():
    print("═" * LINE_WIDTH)

# ====================================================================
# QUERY BUILDERS
# ====================================================================

def build_summary_query(table_name: str, config: dict) -> str:
    """Build summary query for any table type."""
    league_field = config['league_field']
    id_field = config['id_field']
    
    base_query = f"""
    SELECT 
        {league_field},
        season,
        COUNT(*) as total_records,
        COUNT(DISTINCT {id_field}) as unique_entities,
        COUNT(DISTINCT team) as total_teams,
        MIN(created_at::date) as first_loaded,
        MAX(updated_at::date) as last_updated
    """
    
    if config['has_understat']:
        base_query += ", COUNT(CASE WHEN understat_metrics IS NOT NULL THEN 1 END) as with_understat"
    
    base_query += f"""
    FROM footballdecoded.{table_name} 
    GROUP BY {league_field}, season 
    ORDER BY {league_field}, season DESC
    """
    
    return base_query

def build_quality_query(table_name: str, config: dict) -> str:
    """Build data quality query for any table type."""
    id_field = config['id_field']
    
    return f"""
    SELECT '{table_name}' as table_name, 
           COUNT(*) as total_records, 
           COUNT(DISTINCT {id_field}) as unique_entities, 
           AVG(data_quality_score) as avg_quality_score 
    FROM footballdecoded.{table_name} 
    WHERE {id_field} IS NOT NULL
    """

def build_missing_ids_query(table_name: str, config: dict) -> str:
    """Build missing IDs query for any table type."""
    id_field = config['id_field']
    return f"SELECT COUNT(*) as count FROM footballdecoded.{table_name} WHERE {id_field} IS NULL"

def build_duplicate_query(table_name: str, config: dict) -> str:
    """Build duplicate IDs query for any table type."""
    id_field = config['id_field']
    league_field = config['league_field']
    
    return f"""
    SELECT {id_field}, {league_field}, season, team, COUNT(*) as count 
    FROM footballdecoded.{table_name} 
    GROUP BY {id_field}, {league_field}, season, team 
    HAVING COUNT(*) > 1
    """

def build_format_query(table_name: str, config: dict) -> str:
    """Build ID format validation query for any table type."""
    id_field = config['id_field']
    return f"SELECT COUNT(*) as count FROM footballdecoded.{table_name} WHERE LENGTH({id_field}) != 16"

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
        for table_name, config in TABLE_CONFIGS.items():
            query = build_summary_query(table_name, config)
            df = pd.read_sql(query, db.engine)
            results[table_name] = df
            
            if verbose and not df.empty:
                entity_type = "PLAYERS" if 'players' in table_name else "TEAMS"
                data_source = "FBref + Understat" if config['has_understat'] else "FBref only"
                table_type = "DOMESTIC" if 'domestic' in table_name else "EUROPEAN"
                
                print_section(f"{table_type} {entity_type} ({data_source})")
                
                for _, row in df.iterrows():
                    league_name = row[config['league_field']]
                    season = row['season']
                    unique_entities = row['unique_entities']
                    total_records = row['total_records']
                    
                    if 'players' in table_name:
                        transfer_ratio = total_records / unique_entities if unique_entities > 0 else 1
                        output = f"├─ {league_name} {season}: {unique_entities} players | {total_records} records | Ratio: {transfer_ratio:.2f}"
                    else:
                        output = f"├─ {league_name} {season}: {unique_entities} teams"
                    
                    if config['has_understat'] and 'with_understat' in row:
                        understat_pct = (row['with_understat'] / total_records * 100) if total_records > 0 else 0
                        output += f" | Understat: {understat_pct:.1f}%"
                    
                    print(output)
                print()
        
        # Transfer analysis
        if verbose:
            print_section("TRANSFER ANALYSIS (Multi-team players)")
            
            transfers_domestic = db.get_transfers_by_unique_id('domestic')
            transfers_european = db.get_transfers_by_unique_id('european')
            
            if not transfers_domestic.empty:
                print("Domestic leagues:")
                for _, transfer in transfers_domestic.head(5).iterrows():
                    print(f"├─ {transfer['player_name']} ({transfer['league']} {transfer['season']}): {transfer['teams_count']} teams - {transfer['teams_path']}")
                if len(transfers_domestic) > 5:
                    print(f"└─ ... and {len(transfers_domestic) - 5} more transfers")
            
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
            
            for table_name, config in TABLE_CONFIGS.items():
                try:
                    query = build_quality_query(table_name, config)
                    result = pd.read_sql(query, db.engine)
                    
                    if not result.empty and result.iloc[0]['total_records'] > 0:
                        row = result.iloc[0]
                        print(f"├─ {row['table_name']}: {row['total_records']} records | {row['unique_entities']} unique entities | Quality: {row['avg_quality_score']:.3f}")
                except Exception:
                    print(f"├─ {table_name}: Error retrieving quality data")
            print()
        
        # Overall summary
        if verbose:
            unique_counts = db.get_unique_entities_count()
            
            total_records = sum(df['total_records'].sum() if not df.empty else 0 for df in results.values())
            
            print_section("SUMMARY")
            print(f"├─ Unique domestic players: {unique_counts.get('unique_domestic_players', 0)}")
            print(f"├─ Unique european players: {unique_counts.get('unique_european_players', 0)}")
            print(f"├─ Unique domestic teams: {unique_counts.get('unique_domestic_teams', 0)}")
            print(f"├─ Unique european teams: {unique_counts.get('unique_european_teams', 0)}")
            print(f"├─ Total records: {total_records}")
            
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
        print_section("Missing ID Check:")
        for table_name, config in TABLE_CONFIGS.items():
            query = build_missing_ids_query(table_name, config)
            result = pd.read_sql(query, db.engine)
            missing_count = result.iloc[0]['count']
            results[f'{table_name}_missing_ids'] = missing_count
            if verbose:
                status = "OK" if missing_count == 0 else f"ERROR: {missing_count} missing"
                print(f"├─ {table_name}: {status}")
        print()
        
        print_section("Duplicate ID Check:")
        for table_name, config in TABLE_CONFIGS.items():
            if 'players' in table_name:  # Only check duplicates for players
                query = build_duplicate_query(table_name, config)
                duplicates = pd.read_sql(query, db.engine)
                results[f'{table_name}_duplicates'] = len(duplicates)
                if verbose:
                    status = "OK" if len(duplicates) == 0 else f"ERROR: {len(duplicates)} duplicates"
                    print(f"├─ {table_name}: {status}")
        print()
        
        print_section("ID Format Check:")
        for table_name, config in TABLE_CONFIGS.items():
            query = build_format_query(table_name, config)
            result = pd.read_sql(query, db.engine)
            invalid_count = result.iloc[0]['count']
            results[f'{table_name}_invalid_format'] = invalid_count
            if verbose:
                status = "OK" if invalid_count == 0 else f"ERROR: {invalid_count} invalid format"
                print(f"├─ {table_name}: {status}")
        
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
        transfers_domestic = db.get_transfers_by_unique_id('domestic')
        transfers_european = db.get_transfers_by_unique_id('european')
        
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
        
        print_section("RECORD COUNTS")
        total_records = 0
        table_names = list(TABLE_CONFIGS.keys())
        
        for i, table_name in enumerate(table_names):
            try:
                count = pd.read_sql(f"SELECT COUNT(*) as count FROM footballdecoded.{table_name}", db.engine)
                records = count.iloc[0]['count']
                total_records += records
                connector = "├─" if i < len(table_names) - 1 else "├─"
                display_name = table_name.replace('_', ' ').title() + " records"
                print(f"{connector} {display_name}: {records}")
            except Exception:
                connector = "├─" if i < len(table_names) - 1 else "├─"
                display_name = table_name.replace('_', ' ').title() + " records"
                print(f"{connector} {display_name}: 0 (table does not exist)")
        
        print(f"└─ TOTAL RECORDS: {total_records}")
        print()
        
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