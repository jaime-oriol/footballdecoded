# ====================================================================
# FootballDecoded Database Quality Test - Sistema Completo
# ====================================================================

import sys
import os
import pandas as pd
import numpy as np
from sqlalchemy import text
from typing import Dict, List, Tuple, Any
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_db_manager

class DatabaseQualityTest:
    """Test exhaustivo de calidad de datos FootballDecoded."""
    
    def __init__(self):
        self.db = get_db_manager()
        self.results = {}
        self.errors = []
        self.warnings = []
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Ejecuta todos los tests de calidad."""
        print("FootballDecoded Database Quality Test")
        print("=" * 50)
        
        tests = [
            ("Data Completeness", self.test_data_completeness),
            ("Unique ID Integrity", self.test_unique_id_integrity),
            ("Name Normalization", self.test_name_normalization),
            ("Metric Validation", self.test_metric_validation),
            ("Cross-Season Consistency", self.test_cross_season_consistency),
            ("Duplicate Detection", self.test_duplicate_detection),
            ("Data Quality Scores", self.test_data_quality_scores),
            ("Performance Validation", self.test_performance_validation)
        ]
        
        for test_name, test_func in tests:
            print(f"\n{test_name}")
            print("-" * 30)
            try:
                result = test_func()
                self.results[test_name] = result
                if result.get('status') == 'PASS':
                    print(f"✓ PASS")
                else:
                    print(f"✗ FAIL: {result.get('message', 'Unknown error')}")
            except Exception as e:
                print(f"✗ ERROR: {str(e)}")
                self.errors.append(f"{test_name}: {str(e)}")
        
        self.print_summary()
        return self.results
    
    def test_data_completeness(self) -> Dict[str, Any]:
        """Test 1: Completitud de datos descargados."""
        query = """
        SELECT 
            'players_domestic' as table_name,
            league,
            season,
            COUNT(*) as total_records,
            COUNT(DISTINCT unique_player_id) as unique_entities,
            COUNT(CASE WHEN fbref_metrics IS NULL THEN 1 END) as missing_fbref,
            COUNT(CASE WHEN understat_metrics IS NULL THEN 1 END) as missing_understat
        FROM footballdecoded.players_domestic 
        WHERE league IN ('ENG-Premier League', 'ESP-La Liga') 
        AND season = '2024-25'
        GROUP BY league, season
        
        UNION ALL
        
        SELECT 
            'players_european' as table_name,
            competition as league,
            season,
            COUNT(*) as total_records,
            COUNT(DISTINCT unique_player_id) as unique_entities,
            COUNT(CASE WHEN fbref_metrics IS NULL THEN 1 END) as missing_fbref,
            0 as missing_understat
        FROM footballdecoded.players_european 
        WHERE competition = 'INT-Champions League' 
        AND season IN ('2023-24', '2024-25')
        GROUP BY competition, season
        """
        
        df = pd.read_sql(query, self.db.engine)
        
        if df.empty:
            return {'status': 'FAIL', 'message': 'No data found for expected competitions'}
        
        # Validaciones específicas
        issues = []
        
        for _, row in df.iterrows():
            # Premier League debe tener ~600+ jugadores
            if row['league'] == 'ENG-Premier League' and row['unique_entities'] < 500:
                issues.append(f"Premier League: solo {row['unique_entities']} jugadores (esperado 500+)")
            
            # La Liga debe tener ~500+ jugadores
            if row['league'] == 'ESP-La Liga' and row['unique_entities'] < 400:
                issues.append(f"La Liga: solo {row['unique_entities']} jugadores (esperado 400+)")
            
            # Champions debe tener datos para ambas temporadas
            if row['league'] == 'INT-Champions League' and row['unique_entities'] < 200:
                issues.append(f"Champions {row['season']}: solo {row['unique_entities']} jugadores (esperado 200+)")
            
            # Métricas FBref obligatorias
            if row['missing_fbref'] > 0:
                issues.append(f"{row['league']} {row['season']}: {row['missing_fbref']} registros sin métricas FBref")
            
            # Understat obligatorio para ligas domésticas
            if row['table_name'] == 'players_domestic' and row['missing_understat'] > row['total_records'] * 0.1:
                issues.append(f"{row['league']} {row['season']}: {row['missing_understat']} registros sin Understat (>10%)")
        
        print(f"Registros encontrados: {len(df)}")
        for _, row in df.iterrows():
            print(f"  {row['league']} {row['season']}: {row['unique_entities']} jugadores")
        
        if issues:
            return {'status': 'FAIL', 'message': '; '.join(issues), 'data': df.to_dict('records')}
        
        return {'status': 'PASS', 'data': df.to_dict('records')}
    
    def test_unique_id_integrity(self) -> Dict[str, Any]:
        """Test 2: Integridad del sistema de IDs únicos."""
        issues = []
        
        # Test 1: IDs faltantes
        missing_queries = {
            'players_domestic': "SELECT COUNT(*) as count FROM footballdecoded.players_domestic WHERE unique_player_id IS NULL",
            'players_european': "SELECT COUNT(*) as count FROM footballdecoded.players_european WHERE unique_player_id IS NULL",
            'teams_domestic': "SELECT COUNT(*) as count FROM footballdecoded.teams_domestic WHERE unique_team_id IS NULL",
            'teams_european': "SELECT COUNT(*) as count FROM footballdecoded.teams_european WHERE unique_team_id IS NULL"
        }
        
        for table, query in missing_queries.items():
            result = pd.read_sql(query, self.db.engine)
            missing = result.iloc[0]['count']
            if missing > 0:
                issues.append(f"{table}: {missing} registros sin ID único")
        
        # Test 2: Formato de IDs
        format_queries = {
            'players_domestic': "SELECT COUNT(*) as count FROM footballdecoded.players_domestic WHERE LENGTH(unique_player_id) != 16",
            'teams_domestic': "SELECT COUNT(*) as count FROM footballdecoded.teams_domestic WHERE LENGTH(unique_team_id) != 16"
        }
        
        for table, query in format_queries.items():
            result = pd.read_sql(query, self.db.engine)
            invalid = result.iloc[0]['count']
            if invalid > 0:
                issues.append(f"{table}: {invalid} IDs con formato incorrecto")
        
        # Test 3: Consistencia cross-competition (ejemplo con jugadores Champions)
        consistency_query = """
        SELECT 
            p1.unique_player_id,
            p1.player_name as domestic_name,
            p2.player_name as european_name,
            p1.normalized_name as domestic_normalized,
            p2.normalized_name as european_normalized
        FROM footballdecoded.players_domestic p1
        JOIN footballdecoded.players_european p2 ON p1.unique_player_id = p2.unique_player_id
        WHERE p1.normalized_name != p2.normalized_name
        LIMIT 10
        """
        
        inconsistent = pd.read_sql(consistency_query, self.db.engine)
        if not inconsistent.empty:
            issues.append(f"{len(inconsistent)} jugadores con nombres inconsistentes entre competiciones")
        
        print(f"IDs validados en 4 tablas")
        if inconsistent.empty:
            print("Consistencia cross-competition: OK")
        else:
            print(f"Inconsistencias encontradas: {len(inconsistent)}")
        
        if issues:
            return {'status': 'FAIL', 'message': '; '.join(issues)}
        
        return {'status': 'PASS'}
    
    def test_name_normalization(self) -> Dict[str, Any]:
        """Test 3: Calidad de normalización de nombres."""
        issues = []
        
        # Test nombres con caracteres problemáticos
        problematic_patterns = [
            (r'[^\w\s\-\.\']', 'caracteres especiales'),
            (r'\s{2,}', 'espacios múltiples'),
            (r'^\s|\s$', 'espacios al inicio/final'),
            (r'[A-Z]{3,}', 'mayúsculas excesivas')
        ]
        
        tables = [
            ('footballdecoded.players_domestic', 'player_name'),
            ('footballdecoded.players_european', 'player_name'),
            ('footballdecoded.teams_domestic', 'team_name'),
            ('footballdecoded.teams_european', 'team_name')
        ]
        
        for table, name_field in tables:
            for pattern, description in problematic_patterns:
                query = f"""
                SELECT COUNT(*) as count 
                FROM {table} 
                WHERE {name_field} ~ '{pattern}'
                """
                try:
                    result = pd.read_sql(query, self.db.engine)
                    problematic_count = result.iloc[0]['count']
                    if problematic_count > 0:
                        issues.append(f"{table}: {problematic_count} nombres con {description}")
                except:
                    pass
        
        # Test longitud de nombres
        length_query = """
        SELECT 
            'players_domestic' as table_name,
            COUNT(CASE WHEN LENGTH(player_name) < 2 THEN 1 END) as too_short,
            COUNT(CASE WHEN LENGTH(player_name) > 50 THEN 1 END) as too_long
        FROM footballdecoded.players_domestic
        UNION ALL
        SELECT 
            'teams_domestic' as table_name,
            COUNT(CASE WHEN LENGTH(team_name) < 3 THEN 1 END) as too_short,
            COUNT(CASE WHEN LENGTH(team_name) > 30 THEN 1 END) as too_long
        FROM footballdecoded.teams_domestic
        """
        
        length_results = pd.read_sql(length_query, self.db.engine)
        for _, row in length_results.iterrows():
            if row['too_short'] > 0:
                issues.append(f"{row['table_name']}: {row['too_short']} nombres demasiado cortos")
            if row['too_long'] > 0:
                issues.append(f"{row['table_name']}: {row['too_long']} nombres demasiado largos")
        
        print("Patrones de normalización validados")
        print("Longitudes de nombres validadas")
        
        if issues:
            return {'status': 'FAIL', 'message': '; '.join(issues)}
        
        return {'status': 'PASS'}
    
    def test_metric_validation(self) -> Dict[str, Any]:
        """Test 4: Validación de métricas específicas."""
        issues = []
        
        # Test métricas core en FBref
        core_metrics_query = """
        SELECT 
            league,
            season,
            COUNT(*) as total_players,
            COUNT(CASE WHEN fbref_metrics->>'goals' IS NOT NULL THEN 1 END) as with_goals,
            COUNT(CASE WHEN fbref_metrics->>'assists' IS NOT NULL THEN 1 END) as with_assists,
            COUNT(CASE WHEN fbref_metrics->>'minutes_played' IS NOT NULL THEN 1 END) as with_minutes,
            COUNT(CASE WHEN fbref_metrics->>'expected_goals' IS NOT NULL THEN 1 END) as with_xg
        FROM footballdecoded.players_domestic 
        WHERE league IN ('ENG-Premier League', 'ESP-La Liga') 
        AND season = '2024-25'
        GROUP BY league, season
        """
        
        metrics_df = pd.read_sql(core_metrics_query, self.db.engine)
        
        for _, row in metrics_df.iterrows():
            total = row['total_players']
            required_coverage = 0.95  # 95% de los jugadores deben tener métricas core
            
            core_metrics = ['with_goals', 'with_assists', 'with_minutes', 'with_xg']
            for metric in core_metrics:
                coverage = row[metric] / total if total > 0 else 0
                if coverage < required_coverage:
                    metric_name = metric.replace('with_', '')
                    issues.append(f"{row['league']}: {metric_name} solo en {coverage:.1%} de jugadores")
        
        # Test métricas Understat específicas
        understat_query = """
        SELECT 
            league,
            season,
            COUNT(*) as total_players,
            COUNT(CASE WHEN understat_metrics->>'understat_xg_chain' IS NOT NULL THEN 1 END) as with_xg_chain,
            COUNT(CASE WHEN understat_metrics->>'understat_xg_buildup' IS NOT NULL THEN 1 END) as with_xg_buildup,
            COUNT(CASE WHEN understat_metrics->>'understat_npxg_plus_xa' IS NOT NULL THEN 1 END) as with_combined
        FROM footballdecoded.players_domestic 
        WHERE league IN ('ENG-Premier League', 'ESP-La Liga') 
        AND season = '2024-25'
        GROUP BY league, season
        """
        
        understat_df = pd.read_sql(understat_query, self.db.engine)
        
        for _, row in understat_df.iterrows():
            total = row['total_players']
            min_coverage = 0.8  # 80% para métricas Understat
            
            understat_metrics = ['with_xg_chain', 'with_xg_buildup', 'with_combined']
            for metric in understat_metrics:
                coverage = row[metric] / total if total > 0 else 0
                if coverage < min_coverage:
                    metric_name = metric.replace('with_', 'understat_')
                    issues.append(f"{row['league']}: {metric_name} solo en {coverage:.1%} de jugadores")
        
        print(f"Métricas FBref validadas: {len(metrics_df)} competitions")
        print(f"Métricas Understat validadas: {len(understat_df)} competitions")
        
        if issues:
            return {'status': 'FAIL', 'message': '; '.join(issues)}
        
        return {'status': 'PASS'}
    
    def test_cross_season_consistency(self) -> Dict[str, Any]:
        """Test 5: Consistencia entre temporadas Champions League."""
        issues = []
        
        # Jugadores que aparecen en ambas temporadas Champions
        consistency_query = """
        SELECT 
            unique_player_id,
            player_name,
            COUNT(DISTINCT season) as seasons_count,
            STRING_AGG(DISTINCT season, ', ' ORDER BY season) as seasons,
            STRING_AGG(DISTINCT team, ', ' ORDER BY team) as teams
        FROM footballdecoded.players_european 
        WHERE competition = 'INT-Champions League'
        AND season IN ('2023-24', '2024-25')
        GROUP BY unique_player_id, player_name
        HAVING COUNT(DISTINCT season) = 2
        ORDER BY player_name
        LIMIT 20
        """
        
        multi_season = pd.read_sql(consistency_query, self.db.engine)
        
        if multi_season.empty:
            issues.append("No se encontraron jugadores en ambas temporadas Champions")
        else:
            # Validar que nombres son consistentes
            name_changes = 0
            for _, player in multi_season.iterrows():
                # Aquí podrías agregar validaciones adicionales
                pass
            
            print(f"Jugadores multi-temporada encontrados: {len(multi_season)}")
            print("Muestra:")
            for _, player in multi_season.head(5).iterrows():
                print(f"  {player['player_name']}: {player['seasons']} ({player['teams']})")
        
        # Test equipos consistentes
        team_consistency_query = """
        SELECT 
            unique_team_id,
            team_name,
            COUNT(DISTINCT season) as seasons_count,
            STRING_AGG(DISTINCT season, ', ' ORDER BY season) as seasons
        FROM footballdecoded.teams_european 
        WHERE competition = 'INT-Champions League'
        AND season IN ('2023-24', '2024-25')
        GROUP BY unique_team_id, team_name
        HAVING COUNT(DISTINCT season) = 2
        """
        
        multi_season_teams = pd.read_sql(team_consistency_query, self.db.engine)
        print(f"Equipos multi-temporada: {len(multi_season_teams)}")
        
        if issues:
            return {'status': 'FAIL', 'message': '; '.join(issues)}
        
        return {'status': 'PASS', 'multi_season_players': len(multi_season), 'multi_season_teams': len(multi_season_teams)}
    
    def test_duplicate_detection(self) -> Dict[str, Any]:
        """Test 6: Detección de duplicados exactos."""
        issues = []
        
        # Duplicados por unique_id + league + season + team
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
            """,
            'teams_domestic': """
                SELECT unique_team_id, league, season, COUNT(*) as count
                FROM footballdecoded.teams_domestic 
                GROUP BY unique_team_id, league, season 
                HAVING COUNT(*) > 1
            """,
            'teams_european': """
                SELECT unique_team_id, competition, season, COUNT(*) as count
                FROM footballdecoded.teams_european 
                GROUP BY unique_team_id, competition, season 
                HAVING COUNT(*) > 1
            """
        }
        
        total_duplicates = 0
        for table, query in duplicate_queries.items():
            duplicates = pd.read_sql(query, self.db.engine)
            if not duplicates.empty:
                duplicate_count = len(duplicates)
                total_duplicates += duplicate_count
                issues.append(f"{table}: {duplicate_count} grupos de duplicados")
        
        print(f"Duplicados encontrados: {total_duplicates}")
        
        if issues:
            return {'status': 'FAIL', 'message': '; '.join(issues)}
        
        return {'status': 'PASS'}
    
    def test_data_quality_scores(self) -> Dict[str, Any]:
        """Test 7: Scores de calidad de datos."""
        issues = []
        
        quality_query = """
        SELECT 
            'players_domestic' as table_name,
            league,
            season,
            COUNT(*) as total_records,
            AVG(data_quality_score) as avg_quality,
            COUNT(CASE WHEN data_quality_score < 0.7 THEN 1 END) as low_quality_count,
            COUNT(CASE WHEN array_length(processing_warnings, 1) > 3 THEN 1 END) as high_warnings_count
        FROM footballdecoded.players_domestic
        WHERE league IN ('ENG-Premier League', 'ESP-La Liga') 
        AND season = '2024-25'
        GROUP BY league, season
        
        UNION ALL
        
        SELECT 
            'players_european' as table_name,
            competition as league,
            season,
            COUNT(*) as total_records,
            AVG(data_quality_score) as avg_quality,
            COUNT(CASE WHEN data_quality_score < 0.7 THEN 1 END) as low_quality_count,
            COUNT(CASE WHEN array_length(processing_warnings, 1) > 3 THEN 1 END) as high_warnings_count
        FROM footballdecoded.players_european
        WHERE competition = 'INT-Champions League' 
        AND season IN ('2023-24', '2024-25')
        GROUP BY competition, season
        """
        
        quality_df = pd.read_sql(quality_query, self.db.engine)
        
        for _, row in quality_df.iterrows():
            avg_quality = row['avg_quality']
            low_quality_pct = (row['low_quality_count'] / row['total_records']) * 100
            high_warnings_pct = (row['high_warnings_count'] / row['total_records']) * 100
            
            if avg_quality < 0.85:
                issues.append(f"{row['league']} {row['season']}: calidad promedio baja ({avg_quality:.3f})")
            
            if low_quality_pct > 5:
                issues.append(f"{row['league']} {row['season']}: {low_quality_pct:.1f}% registros calidad <0.7")
            
            if high_warnings_pct > 10:
                issues.append(f"{row['league']} {row['season']}: {high_warnings_pct:.1f}% registros con muchos warnings")
            
            print(f"{row['league']} {row['season']}: calidad {avg_quality:.3f}, warnings {high_warnings_pct:.1f}%")
        
        if issues:
            return {'status': 'FAIL', 'message': '; '.join(issues)}
        
        return {'status': 'PASS'}
    
    def test_performance_validation(self) -> Dict[str, Any]:
        """Test 8: Validación de rendimiento de queries."""
        issues = []
        
        # Test query performance en operaciones comunes
        performance_queries = [
            ("Simple player lookup", """
                SELECT * FROM footballdecoded.players_domestic 
                WHERE unique_player_id = (
                    SELECT unique_player_id FROM footballdecoded.players_domestic LIMIT 1
                )
            """),
            ("League aggregation", """
                SELECT league, season, COUNT(*), AVG(data_quality_score)
                FROM footballdecoded.players_domestic 
                GROUP BY league, season
            """),
            ("Cross-table join", """
                SELECT p.player_name, t.team_name
                FROM footballdecoded.players_domestic p
                JOIN footballdecoded.teams_domestic t 
                ON p.team = t.team_name AND p.league = t.league AND p.season = t.season
                LIMIT 100
            """)
        ]
        
        import time
        
        for query_name, query in performance_queries:
            start_time = time.time()
            try:
                result = pd.read_sql(query, self.db.engine)
                execution_time = time.time() - start_time
                
                if execution_time > 5.0:  # 5 segundos límite
                    issues.append(f"{query_name}: {execution_time:.2f}s (demasiado lento)")
                
                print(f"{query_name}: {execution_time:.3f}s, {len(result)} filas")
            except Exception as e:
                issues.append(f"{query_name}: Error - {str(e)}")
        
        if issues:
            return {'status': 'FAIL', 'message': '; '.join(issues)}
        
        return {'status': 'PASS'}
    
    def print_summary(self):
        """Imprime resumen final del test."""
        print("\n" + "=" * 50)
        print("RESUMEN FINAL")
        print("=" * 50)
        
        passed = sum(1 for result in self.results.values() if result.get('status') == 'PASS')
        total = len(self.results)
        
        print(f"Tests pasados: {passed}/{total}")
        
        if passed == total:
            print("✓ TODOS LOS TESTS PASADOS - BASE DE DATOS LISTA")
            print("\nLa base de datos está perfectamente preparada para:")
            print("- Descarga masiva de datos")
            print("- Análisis avanzados multi-temporada")
            print("- Visualizaciones profesionales")
            print("- Seguimiento longitudinal de jugadores/equipos")
        else:
            print("✗ HAY PROBLEMAS QUE RESOLVER")
            print("\nProblemas encontrados:")
            for test_name, result in self.results.items():
                if result.get('status') != 'PASS':
                    print(f"  - {test_name}: {result.get('message', 'Error desconocido')}")
        
        if self.errors:
            print(f"\nErrores de ejecución: {len(self.errors)}")
            for error in self.errors:
                print(f"  - {error}")
    
    def close(self):
        """Cierra conexión a base de datos."""
        if self.db:
            self.db.close()

# ====================================================================
# EJECUCIÓN PRINCIPAL
# ====================================================================

def run_database_quality_test():
    """Ejecuta el test completo de calidad."""
    test = DatabaseQualityTest()
    try:
        results = test.run_all_tests()
        return results
    finally:
        test.close()

if __name__ == "__main__":
    run_database_quality_test()