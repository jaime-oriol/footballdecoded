# ====================================================================
# FootballDecoded Database Status Checker
# ====================================================================
#
# Sistema completo de monitoreo y diagnóstico para PostgreSQL:
# - Status detallado de tablas con conteos y estadísticas
# - Detección automática de problemas de datos
# - Health scoring de 0-100 para evaluar estado general
# - Cleanup automático de datos corruptos y duplicados
# - Análisis de integridad de IDs únicos y transferencias
# - Múltiples modos de ejecución vía CLI
#
# Uso:
#   python database_checker.py                 # Status completo
#   python database_checker.py --quick         # Status rápido
#   python database_checker.py --problems      # Solo detección de problemas
#   python database_checker.py --health        # Solo health score
#   python database_checker.py --cleanup       # Limpiar datos automáticamente
#   python database_checker.py --full          # Análisis completo
#
# ====================================================================

import sys
import os
import pandas as pd
import logging
from typing import Dict, List, Tuple
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database.connection import get_db_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
# PROBLEM DETECTION AND HEALTH SCORING
# ====================================================================

def detect_data_problems(verbose: bool = True) -> Dict[str, List[Dict]]:
    """
    Detectar problemas específicos en los datos con sugerencias de reparación.
    
    Analiza todas las tablas en busca de:
    - Problemas críticos: duplicados, IDs corruptos, datos faltantes críticos
    - Advertencias: calidad baja, problemas menores de formato
    - Info: estadísticas y observaciones generales
    
    Args:
        verbose: Si mostrar output detallado durante el análisis
        
    Returns:
        Dict con problemas categorizados por severidad ('critical', 'warning', 'info')
    """
    if verbose:
        print_header("🔍 Detección de Problemas en Datos")
    
    db = get_db_manager()
    problems = {
        'critical': [],
        'warning': [],
        'info': []
    }
    
    try:
        # 1. Detectar IDs duplicados dentro de la misma liga/temporada/equipo
        if verbose:
            print_section("CRITICAL ISSUES:")
        
        duplicate_queries = {
            'players_domestic': """
                SELECT unique_player_id, player_name, league, season, team, COUNT(*) as count 
                FROM footballdecoded.players_domestic 
                GROUP BY unique_player_id, league, season, team 
                HAVING COUNT(*) > 1
            """,
            'players_european': """
                SELECT unique_player_id, player_name, competition, season, team, COUNT(*) as count 
                FROM footballdecoded.players_european 
                GROUP BY unique_player_id, competition, season, team 
                HAVING COUNT(*) > 1
            """,
            'teams_domestic': """
                SELECT unique_team_id, team_name, league, season, COUNT(*) as count 
                FROM footballdecoded.teams_domestic 
                GROUP BY unique_team_id, league, season 
                HAVING COUNT(*) > 1
            """,
            'teams_european': """
                SELECT unique_team_id, team_name, competition, season, COUNT(*) as count 
                FROM footballdecoded.teams_european 
                GROUP BY unique_team_id, competition, season 
                HAVING COUNT(*) > 1
            """
        }
        
        for table_name, query in duplicate_queries.items():
            duplicates = pd.read_sql(query, db.engine)
            if not duplicates.empty:
                problem = {
                    'table': table_name,
                    'issue': 'Duplicate records',
                    'count': len(duplicates),
                    'description': f"{len(duplicates)} duplicate records found",
                    'fix_query': f"-- Clean duplicates for {table_name}\\nDELETE FROM footballdecoded.{table_name} WHERE id NOT IN (SELECT MIN(id) FROM footballdecoded.{table_name} GROUP BY unique_{'player' if 'player' in table_name else 'team'}_id, {'competition' if 'european' in table_name else 'league'}, season{', team' if 'player' in table_name else ''});"
                }
                problems['critical'].append(problem)
                if verbose:
                    print(f"├─ CRITICAL: {problem['description']} in {table_name}")
        
        # 2. Detectar valores fuera de rango
        if verbose:
            print_section("WARNING ISSUES:")
        
        range_check_queries = {
            'players_domestic_age': "SELECT COUNT(*) as count FROM footballdecoded.players_domestic WHERE age < 15 OR age > 50",
            'players_european_age': "SELECT COUNT(*) as count FROM footballdecoded.players_european WHERE age < 15 OR age > 50",
            'players_domestic_birth_year': "SELECT COUNT(*) as count FROM footballdecoded.players_domestic WHERE birth_year < 1970 OR birth_year > 2010",
            'players_european_birth_year': "SELECT COUNT(*) as count FROM footballdecoded.players_european WHERE birth_year < 1970 OR birth_year > 2010"
        }
        
        for check_name, query in range_check_queries.items():
            result = pd.read_sql(query, db.engine)
            invalid_count = result.iloc[0]['count']
            if invalid_count > 0:
                table_name, field = check_name.rsplit('_', 1)
                problem = {
                    'table': table_name,
                    'issue': f'Invalid {field} values',
                    'count': invalid_count,
                    'description': f"{invalid_count} records with invalid {field}",
                    'fix_query': f"UPDATE footballdecoded.{table_name} SET {field} = NULL WHERE {field} < {'15' if field == 'age' else '1970'} OR {field} > {'50' if field == 'age' else '2010'};"
                }
                problems['warning'].append(problem)
                if verbose:
                    print(f"├─ WARNING: {problem['description']} in {table_name}")
        
        # 3. Detectar registros sin métricas
        if verbose:
            print_section("INFO ISSUES:")
        
        empty_metrics_queries = {
            'players_domestic': "SELECT COUNT(*) as count FROM footballdecoded.players_domestic WHERE fbref_metrics IS NULL OR fbref_metrics = '{}'",
            'players_european': "SELECT COUNT(*) as count FROM footballdecoded.players_european WHERE fbref_metrics IS NULL OR fbref_metrics = '{}'",
            'teams_domestic': "SELECT COUNT(*) as count FROM footballdecoded.teams_domestic WHERE fbref_metrics IS NULL OR fbref_metrics = '{}'",
            'teams_european': "SELECT COUNT(*) as count FROM footballdecoded.teams_european WHERE fbref_metrics IS NULL OR fbref_metrics = '{}'"
        }
        
        for table_name, query in empty_metrics_queries.items():
            result = pd.read_sql(query, db.engine)
            empty_count = result.iloc[0]['count']
            if empty_count > 0:
                problem = {
                    'table': table_name,
                    'issue': 'Empty metrics',
                    'count': empty_count,
                    'description': f"{empty_count} records with empty FBref metrics",
                    'fix_query': f"DELETE FROM footballdecoded.{table_name} WHERE fbref_metrics IS NULL OR fbref_metrics = '{{}}';"
                }
                problems['info'].append(problem)
                if verbose:
                    print(f"├─ INFO: {problem['description']} in {table_name}")
        
        if verbose:
            print_section("DETECTION SUMMARY:")
            total_problems = len(problems['critical']) + len(problems['warning']) + len(problems['info'])
            if total_problems == 0:
                print("└─ No problems detected! Database is healthy.")
            else:
                print(f"├─ Critical issues: {len(problems['critical'])}")
                print(f"├─ Warning issues: {len(problems['warning'])}")
                print(f"├─ Info issues: {len(problems['info'])}")
                print(f"└─ Total problems: {total_problems}")
        
        print_footer()
        db.close()
        return problems
        
    except Exception as e:
        logger.error(f"Error detecting problems: {e}")
        db.close()
        return problems

def calculate_health_score(verbose: bool = True) -> int:
    """
    Calcular puntuación de salud de la base de datos (0-100).
    
    El score se calcula empezando desde 100 y deduciendo puntos por:
    - Problemas críticos: -10 puntos cada uno (máximo -50)
    - Problemas warning: -5 puntos cada uno (máximo -30)  
    - Problemas info: -2 puntos cada uno (máximo -20)
    - Calidad de datos baja: hasta -20 puntos adicionales
    
    Args:
        verbose: Si mostrar detalles del cálculo
        
    Returns:
        int: Score de 0-100 (100 = perfecto, 0 = crítico)
    """
    if verbose:
        print_header("💚 Health Score de Base de Datos")
    
    db = get_db_manager()
    score = 100
    deductions = []
    
    try:
        # Obtener estadísticas básicas
        tables = ['players_domestic', 'players_european', 'teams_domestic', 'teams_european']
        total_records = 0
        
        for table in tables:
            try:
                count = pd.read_sql(f"SELECT COUNT(*) as count FROM footballdecoded.{table}", db.engine)
                total_records += count.iloc[0]['count']
            except:
                continue
        
        if total_records == 0:
            if verbose:
                print("└─ Database is empty")
            return 0
        
        # Detectar problemas y calcular puntuaciones
        problems = detect_data_problems(verbose=False)
        
        # Deducciones por problemas críticos
        if problems['critical']:
            critical_deduction = min(50, len(problems['critical']) * 10)
            score -= critical_deduction
            deductions.append(f"Critical issues: -{critical_deduction} points")
        
        # Deducciones por warnings
        if problems['warning']:
            warning_deduction = min(30, len(problems['warning']) * 5)
            score -= warning_deduction
            deductions.append(f"Warning issues: -{warning_deduction} points")
        
        # Deducciones por problemas informativos
        if problems['info']:
            info_deduction = min(20, len(problems['info']) * 2)
            score -= info_deduction
            deductions.append(f"Info issues: -{info_deduction} points")
        
        # Bonificación por volumen de datos
        if total_records > 10000:
            score += 5  # Bonus for large dataset
            deductions.append(f"Large dataset bonus: +5 points")
        
        # Verificar calidad promedio de datos
        try:
            avg_quality_query = """
                SELECT AVG(data_quality_score) as avg_score 
                FROM (
                    SELECT data_quality_score FROM footballdecoded.players_domestic 
                    WHERE data_quality_score IS NOT NULL
                    UNION ALL
                    SELECT data_quality_score FROM footballdecoded.players_european 
                    WHERE data_quality_score IS NOT NULL
                    UNION ALL
                    SELECT data_quality_score FROM footballdecoded.teams_domestic 
                    WHERE data_quality_score IS NOT NULL
                    UNION ALL
                    SELECT data_quality_score FROM footballdecoded.teams_european 
                    WHERE data_quality_score IS NOT NULL
                ) as all_scores
            """
            avg_quality = pd.read_sql(avg_quality_query, db.engine)
            if not avg_quality.empty and avg_quality.iloc[0]['avg_score'] is not None:
                quality_score = avg_quality.iloc[0]['avg_score']
                if quality_score < 0.7:
                    quality_deduction = int((0.7 - quality_score) * 50)
                    score -= quality_deduction
                    deductions.append(f"Low data quality: -{quality_deduction} points")
        except:
            pass
        
        # Asegurar que el score esté entre 0 y 100
        score = max(0, min(100, score))
        
        if verbose:
            print_section("HEALTH CALCULATION:")
            print("Base score: 100 points")
            for deduction in deductions:
                print(f"├─ {deduction}")
            
            print_section("FINAL SCORE:")
            if score >= 90:
                status = "EXCELLENT"
                color = "\033[92m"  # Green
            elif score >= 70:
                status = "GOOD"
                color = "\033[93m"  # Yellow
            elif score >= 50:
                status = "NEEDS ATTENTION"
                color = "\033[91m"  # Red
            else:
                status = "CRITICAL"
                color = "\033[91m"  # Red
            
            print(f"├─ Health Score: {color}{score}/100{'\033[0m'}")
            print(f"└─ Status: {color}{status}{'\033[0m'}")
        
        print_footer()
        db.close()
        return score
        
    except Exception as e:
        logger.error(f"Error calculating health score: {e}")
        db.close()
        return 0

def auto_cleanup_database(dry_run: bool = True, verbose: bool = True) -> Dict[str, int]:
    """Limpiar automáticamente problemas detectados en la base de datos."""
    if verbose:
        mode_text = "DRY RUN" if dry_run else "LIVE RUN"
        print_header(f"Database Auto Cleanup - {mode_text}")
    
    db = get_db_manager()
    cleanup_stats = {
        'duplicates_removed': 0,
        'invalid_records_cleaned': 0,
        'empty_records_removed': 0
    }
    
    try:
        # Detectar problemas primero
        problems = detect_data_problems(verbose=False)
        
        if verbose:
            total_issues = len(problems['critical']) + len(problems['warning']) + len(problems['info'])
            if total_issues == 0:
                print("└─ No issues found. Database is clean!")
                print_footer()
                return cleanup_stats
            
            print_section("CLEANUP ACTIONS:")
            if dry_run:
                print("├─ Running in DRY RUN mode - no changes will be made")
                print("├─ Run with dry_run=False to apply fixes")
        
        # 1. Limpiar duplicados críticos
        for problem in problems['critical']:
            if problem['issue'] == 'Duplicate records':
                if verbose:
                    print(f"├─ FIXING: {problem['description']} in {problem['table']}")
                
                if not dry_run:
                    try:
                        with db.engine.begin() as conn:
                            # Query más segura para limpiar duplicados
                            if 'player' in problem['table']:
                                league_field = 'competition' if 'european' in problem['table'] else 'league'
                                query = f"""
                                DELETE FROM footballdecoded.{problem['table']} 
                                WHERE id NOT IN (
                                    SELECT MIN(id) FROM footballdecoded.{problem['table']} 
                                    GROUP BY unique_player_id, {league_field}, season, team
                                )
                                """
                            else:  # teams
                                league_field = 'competition' if 'european' in problem['table'] else 'league'
                                query = f"""
                                DELETE FROM footballdecoded.{problem['table']} 
                                WHERE id NOT IN (
                                    SELECT MIN(id) FROM footballdecoded.{problem['table']} 
                                    GROUP BY unique_team_id, {league_field}, season
                                )
                                """
                            
                            result = conn.execute(text(query))
                            cleanup_stats['duplicates_removed'] += result.rowcount
                            
                    except Exception as e:
                        logger.error(f"Error cleaning duplicates in {problem['table']}: {e}")
        
        # 2. Limpiar valores fuera de rango
        for problem in problems['warning']:
            if 'Invalid' in problem['issue']:
                if verbose:
                    print(f"├─ FIXING: {problem['description']} in {problem['table']}")
                
                if not dry_run:
                    try:
                        with db.engine.begin() as conn:
                            if 'age' in problem['issue']:
                                query = f"UPDATE footballdecoded.{problem['table']} SET age = NULL WHERE age < 15 OR age > 50"
                            else:  # birth_year
                                query = f"UPDATE footballdecoded.{problem['table']} SET birth_year = NULL WHERE birth_year < 1970 OR birth_year > 2010"
                            
                            result = conn.execute(text(query))
                            cleanup_stats['invalid_records_cleaned'] += result.rowcount
                            
                    except Exception as e:
                        logger.error(f"Error cleaning invalid values in {problem['table']}: {e}")
        
        # 3. Limpiar registros vacíos
        for problem in problems['info']:
            if problem['issue'] == 'Empty metrics':
                if verbose:
                    print(f"├─ FIXING: {problem['description']} in {problem['table']}")
                
                if not dry_run:
                    try:
                        with db.engine.begin() as conn:
                            query = f"DELETE FROM footballdecoded.{problem['table']} WHERE fbref_metrics IS NULL OR fbref_metrics = '{{}}'"
                            result = conn.execute(text(query))
                            cleanup_stats['empty_records_removed'] += result.rowcount
                            
                    except Exception as e:
                        logger.error(f"Error cleaning empty records in {problem['table']}: {e}")
        
        if verbose:
            print_section("CLEANUP SUMMARY:")
            if dry_run:
                print("├─ DRY RUN completed - no changes made")
                print("├─ Issues detected:")
                print(f"│  ├─ Duplicates to remove: {sum(p['count'] for p in problems['critical'] if p['issue'] == 'Duplicate records')}")
                print(f"│  ├─ Invalid values to clean: {sum(p['count'] for p in problems['warning'])}")
                print(f"│  └─ Empty records to remove: {sum(p['count'] for p in problems['info'])}")
                print("└─ Run with dry_run=False to apply fixes")
            else:
                total_cleaned = sum(cleanup_stats.values())
                print(f"├─ Records cleaned: {total_cleaned}")
                print(f"│  ├─ Duplicates removed: {cleanup_stats['duplicates_removed']}")
                print(f"│  ├─ Invalid values cleaned: {cleanup_stats['invalid_records_cleaned']}")
                print(f"│  └─ Empty records removed: {cleanup_stats['empty_records_removed']}")
                
                if total_cleaned > 0:
                    print("├─ Database cleanup completed successfully")
                    print("└─ Recommend running health check to verify improvements")
                else:
                    print("└─ No records needed cleaning")
        
        print_footer()
        db.close()
        return cleanup_stats
        
    except Exception as e:
        logger.error(f"Error in auto cleanup: {e}")
        db.close()
        return cleanup_stats

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
        elif sys.argv[1] == '--problems':
            problems = detect_data_problems(verbose=True)
            print(f"\n🚨 Problemas críticos: {len(problems['critical'])}")
            print(f"⚠️ Advertencias: {len(problems['warning'])}")
            print(f"ℹ️ Info: {len(problems['info'])}")
        elif sys.argv[1] == '--health':
            score = calculate_health_score(verbose=True)
            print(f"\n💚 Health Score: {score}/100")
        elif sys.argv[1] == '--cleanup':
            print("🧹 Iniciando limpieza automática...")
            auto_cleanup_database()
        elif sys.argv[1] == '--full':
            print("🔍 Análisis completo de la base de datos\n")
            check_database_status(verbose=True)
            print("\n" + "="*60)
            problems = detect_data_problems(verbose=True)
            print("\n" + "="*60)
            score = calculate_health_score(verbose=True)
            print(f"\n💚 Health Score Final: {score}/100")
        else:
            print("Usage: python database_checker.py [--quick|--integrity|--transfers|--problems|--health|--cleanup|--full]")
            print("\nOpciones:")
            print("  --quick      Estado rápido de tablas")
            print("  --integrity  Verificar integridad de IDs únicos")
            print("  --transfers  Analizar transferencias")
            print("  --problems   Detectar problemas en los datos")
            print("  --health     Calcular score de salud (0-100)")
            print("  --cleanup    Limpiar datos corruptos automáticamente")
            print("  --full       Análisis completo con todas las opciones")
    else:
        check_database_status(verbose=True)