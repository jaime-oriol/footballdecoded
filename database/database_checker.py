# ====================================================================
# FootballDecoded - Database Status Checker
# ====================================================================

import sys
import os
import pandas as pd
from typing import Dict

# Add database to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.connection import get_db_manager

def check_database_status(verbose: bool = True) -> Dict[str, pd.DataFrame]:
    """
    Verificar qué datos están disponibles en la base de datos.
    
    Returns:
        Dict con resumen de datos por tabla
    """
    if verbose:
        print("🔍 Verificando datos en FootballDecoded Database")
        print("=" * 60)
    
    db = get_db_manager()
    results = {}
    
    try:
        # ================================================================
        # JUGADORES DOMÉSTICOS (FBref + Understat)
        # ================================================================
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
            print("⚽ JUGADORES DOMÉSTICOS (FBref + Understat)")
            print("-" * 50)
            for _, row in players_domestic.iterrows():
                understat_pct = (row['with_understat'] / row['total_players'] * 100) if row['total_players'] > 0 else 0
                print(f"   {row['league']} {row['season']}: {row['total_players']} jugadores | {row['total_teams']} equipos | Understat: {understat_pct:.1f}%")
            print()
        
        # ================================================================
        # JUGADORES EUROPEOS (Solo FBref)
        # ================================================================
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
            print("🏆 JUGADORES EUROPEOS (Solo FBref)")
            print("-" * 50)
            for _, row in players_european.iterrows():
                print(f"   {row['competition']} {row['season']}: {row['total_players']} jugadores | {row['total_teams']} equipos")
            print()
        
        # ================================================================
        # EQUIPOS DOMÉSTICOS (FBref + Understat)
        # ================================================================
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
            print("🏟️  EQUIPOS DOMÉSTICOS (FBref + Understat)")
            print("-" * 50)
            for _, row in teams_domestic.iterrows():
                understat_pct = (row['with_understat'] / row['total_teams'] * 100) if row['total_teams'] > 0 else 0
                print(f"   {row['league']} {row['season']}: {row['total_teams']} equipos | Understat: {understat_pct:.1f}%")
            print()
        
        # ================================================================
        # EQUIPOS EUROPEOS (Solo FBref)
        # ================================================================
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
            print("⭐ EQUIPOS EUROPEOS (Solo FBref)")
            print("-" * 50)
            for _, row in teams_european.iterrows():
                print(f"   {row['competition']} {row['season']}: {row['total_teams']} equipos")
            print()
        
        # ================================================================
        # RESUMEN TOTAL
        # ================================================================
        if verbose:
            total_domestic_players = players_domestic['total_players'].sum() if not players_domestic.empty else 0
            total_european_players = players_european['total_players'].sum() if not players_european.empty else 0
            total_domestic_teams = teams_domestic['total_teams'].sum() if not teams_domestic.empty else 0
            total_european_teams = teams_european['total_teams'].sum() if not teams_european.empty else 0
            
            print("📊 RESUMEN TOTAL")
            print("-" * 50)
            print(f"   Jugadores domésticos: {total_domestic_players}")
            print(f"   Jugadores europeos: {total_european_players}")
            print(f"   Equipos domésticos: {total_domestic_teams}")
            print(f"   Equipos europeos: {total_european_teams}")
            print(f"   TOTAL: {total_domestic_players + total_european_players + total_domestic_teams + total_european_teams} registros")
        
        db.close()
        return results
        
    except Exception as e:
        if verbose:
            print(f"❌ Error verificando base de datos: {e}")
        db.close()
        return {}

def quick_status():
    """Verificación rápida sin detalles."""
    print("🔍 Estado rápido de la base de datos:")
    
    db = get_db_manager()
    
    # Contar registros por tabla
    tables = [
        ('players_domestic', 'Jugadores domésticos'),
        ('players_european', 'Jugadores europeos'),
        ('teams_domestic', 'Equipos domésticos'),
        ('teams_european', 'Equipos europeos')
    ]
    
    total_records = 0
    
    for table_name, display_name in tables:
        try:
            count = pd.read_sql(f"SELECT COUNT(*) as count FROM footballdecoded.{table_name}", db.engine)
            records = count.iloc[0]['count']
            total_records += records
            print(f"   {display_name}: {records}")
        except Exception:
            print(f"   {display_name}: 0 (tabla no existe)")
    
    print(f"   TOTAL: {total_records} registros")
    db.close()

# ====================================================================
# INTEGRACIÓN CON DATA_LOADER
# ====================================================================

def add_database_status_to_menu():
    """Función para integrar en el menú principal de data_loader.py"""
    return {
        'option_9': ('9. Check database status (detailed)', lambda: check_database_status(verbose=True)),
        'option_10': ('10. Quick database status', lambda: quick_status())
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        quick_status()
    else:
        check_database_status(verbose=True)