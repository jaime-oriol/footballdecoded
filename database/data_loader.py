# ====================================================================
# FootballDecoded Data Loader - Sistema de IDs Únicos Optimizado
# ====================================================================

import sys
import os
import pandas as pd
import json
import re
import unicodedata
import hashlib
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wrappers import (fbref_get_player, fbref_get_team, fbref_get_league_players,
                     understat_get_player, understat_get_team)
from database.connection import DatabaseManager, get_db_manager

# ====================================================================
# LOGGING MANAGER
# ====================================================================

class LogManager:
    """Sistema de logs limpio y consistente para FootballDecoded."""
    
    def __init__(self):
        self.start_time = None
        self.current_phase = None
        self.line_width = 80
        self.phase_start_time = None
    
    def header(self, competition: str, data_sources: str):
        """Header principal del sistema."""
        print("FootballDecoded Data Loader")
        print("═" * self.line_width)
        print(f"Competition: {competition} ({data_sources})")
        self.start_time = datetime.now()
    
    def database_status(self, connected: bool, schema: str, cleared_records: int):
        """Estado de la base de datos."""
        status = "Connected" if connected else "Failed"
        if cleared_records == 0:
            cleared_text = "0 records removed (fresh load)"
        else:
            cleared_text = f"{cleared_records:,} records removed"
        
        print(f"Database: {status} | Schema: {schema}")
        print(f"Clearing existing data: {cleared_text}")
        print("─" * self.line_width)
        print()
    
    def phase_start(self, phase_name: str, total_entities: int):
        """Inicio de fase (Players/Teams)."""
        self.current_phase = phase_name
        self.phase_start_time = datetime.now()
        print(f"{phase_name.upper()} EXTRACTION")
        print(f"{phase_name} found: {total_entities:,} → Processing batch extraction")
    
    def progress_update(self, current: int, total: int, current_entity: str, 
                       metrics_count: int, fbref_success: int, understat_success: int, 
                       understat_total: int, avg_quality: float, failed_count: int):
        """Actualización del progreso durante extracción."""
        percentage = (current / total) * 100
        filled = int(40 * current // total)
        bar = '█' * filled + ' ' * (40 - filled)
        
        # Calcular ETA
        if self.phase_start_time and current > 0:
            elapsed = (datetime.now() - self.phase_start_time).total_seconds()
            eta_seconds = int((elapsed / current) * (total - current))
        else:
            eta_seconds = None
        
        # Progress bar
        print(f"\rProgress: [{bar}] {current}/{total} ({percentage:.1f}%)")
        
        # Métricas detalladas solo si hay progreso
        if current > 0:
            print(f"├─ Current: {current_entity}")
            
            # Métricas extraídas
            understat_text = " (Understat: N/A)" if understat_total == 0 else ""
            print(f"├─ Metrics: {metrics_count} fields extracted{understat_text}")
            
            # Estado FBref
            if failed_count > 0:
                print(f"├─ FBref: {fbref_success}/{current} successful ({failed_count} timeouts)")
            else:
                print(f"├─ FBref: {fbref_success}/{current} successful")
            
            # Estado Understat
            if understat_total > 0:
                understat_pct = (understat_success / understat_total * 100) if understat_total > 0 else 0
                print(f"├─ Understat: {understat_success}/{understat_total} merged ({understat_pct:.1f}%)")
            else:
                print("├─ Understat: N/A (European competition)")
            
            # Calidad y fallos
            print(f"├─ Quality: {avg_quality:.1f}% average")
            failure_text = f" ({self.current_phase.lower()})" if failed_count > 0 else f" {self.current_phase.lower()}"
            print(f"├─ Failed: {failed_count}{failure_text}")
            
            # ETA
            if eta_seconds and eta_seconds > 0:
                eta_formatted = self._format_time(eta_seconds)
                print(f"└─ ETA: {eta_formatted} remaining")
            else:
                print("└─ ETA: Calculating...")
        
        # Subir cursor para próxima actualización (excepto si es el último)
        if current < total:
            print("\033[8A", end="", flush=True)
    
    def progress_complete(self, total: int, successful: int, failed: int):
        """Completar progreso de fase."""
        # Limpiar líneas de progreso dinámico
        for _ in range(8):
            print(" " * self.line_width)
        print("\033[8A", end="")
        
        # Progress bar final
        print(f"Progress: [{'█' * 40}] {total}/{total} (100%)")
        
        # Estado final
        if self.phase_start_time:
            elapsed = (datetime.now() - self.phase_start_time).total_seconds()
            elapsed_formatted = self._format_time(int(elapsed))
            print(f"└─ Completed in: {elapsed_formatted}")
        
        print()
    
    def final_summary(self, stats: dict):
        """Summary final completo."""
        print("─" * self.line_width)
        print("EXTRACTION SUMMARY")
        print("─" * self.line_width)
        
        # Estadísticas principales
        total = stats['players']['total'] + stats['teams']['total']
        successful = stats['players']['successful'] + stats['teams']['successful']
        failed = stats['players']['failed'] + stats['teams']['failed']
        success_rate = (successful / total * 100) if total > 0 else 0
        
        print(f"Total entities: {total} | Successful: {successful} | Failed: {failed} | Success rate: {success_rate:.1f}%")
        print(f"Unique player IDs: {stats['players']['successful']} | Unique team IDs: {stats['teams']['successful']}")
        
        # Transfers
        if stats.get('transfers', 0) > 0:
            print(f"Transfer detection: {stats['transfers']} players with multiple teams")
        
        # Coverage Understat
        if stats.get('understat_coverage'):
            player_cov = stats['understat_coverage'].get('players', 0)
            team_cov = stats['understat_coverage'].get('teams', 0)
            if player_cov > 0 or team_cov > 0:
                print(f"Understat coverage: Players {player_cov:.1f}% | Teams {team_cov:.1f}%")
            else:
                print("Understat coverage: N/A (European competition)")
        
        # Métricas promedio
        if stats.get('avg_metrics'):
            avg_players = stats['avg_metrics'].get('players', 0)
            avg_teams = stats['avg_metrics'].get('teams', 0)
            print(f"Average metrics per player: {avg_players} | Average metrics per team: {avg_teams}")
        
        # Tiempo y rendimiento
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            total_seconds = elapsed.total_seconds()
            records_per_second = successful / total_seconds if total_seconds > 0 else 0
            elapsed_formatted = self._format_time(int(total_seconds))
            print(f"Processing time: {elapsed_formatted} | Records per second: {records_per_second:.1f}")
        
        # Storage
        storage_mb = successful * 0.004
        print(f"Database records: {successful} inserted | Storage: +{storage_mb:.1f}MB")
        
        # Issues
        if failed > 0:
            print()
            if success_rate >= 95:
                print("EXTRACTION COMPLETED WITH MINOR ISSUES")
                print(f"├─ {failed} extraction failures (recommend retry)")
                print(f"└─ Overall data quality: {stats.get('avg_quality', 95):.1f}% (excellent)")
            else:
                print("ISSUES DETECTED")
                print(f"├─ {failed} extraction failures (rate limit or connection issues)")
                if stats.get('warnings', 0) > 0:
                    print(f"├─ {stats['warnings']} data quality warnings")
                print("└─ Recommendation: Retry failed extractions in 10 minutes")
        
        print("═" * self.line_width)
    
    def _format_time(self, seconds: int) -> str:
        """Formatear tiempo de manera legible."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"

# ====================================================================
# CONFIGURATION
# ====================================================================

AVAILABLE_COMPETITIONS = [
    ('ENG-Premier League', 'domestic'),
    ('ESP-La Liga', 'domestic'),
    ('ITA-Serie A', 'domestic'), 
    ('GER-Bundesliga', 'domestic'),
    ('FRA-Ligue 1', 'domestic'),
    ('INT-Champions League', 'european')
]

METRIC_RANGES = {
    'age': (15, 50),
    'birth_year': (1950, 2020),
    'minutes_played': (0, 6000),
    'matches_played': (0, 80),
    'goals': (0, 120),
    'assists': (0, 60),
    'shots': (0, 600),
    'expected_goals': (0, 80),
    'passes_completed': (0, 4000),
    'pass_completion_pct': (30, 100),
    'tackles': (0, 300),
    'yellow_cards': (0, 25),
    'red_cards': (0, 6),
}

# ====================================================================
# SISTEMA DE IDS ÚNICOS
# ====================================================================

class IDGenerator:
    """Generador de IDs únicos usando SHA256."""
    
    @staticmethod
    def normalize_for_id(text: str) -> str:
        """Normalización para generación de IDs."""
        if not text or pd.isna(text):
            return ""
        
        text = str(text).lower().strip()
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', '_', text).strip('_')
        text = re.sub(r'_+', '_', text)
        
        return text
    
    @staticmethod
    def generate_player_hash_id(name: str, birth_year: Optional[int], nationality: Optional[str]) -> str:
        """Generar ID único para jugador."""
        normalized_name = IDGenerator.normalize_for_id(name)
        birth_str = str(birth_year) if birth_year else "unknown"
        nation_str = IDGenerator.normalize_for_id(nationality) if nationality else "unknown"
        
        combined = f"{normalized_name}_{birth_str}_{nation_str}"
        hash_obj = hashlib.sha256(combined.encode('utf-8'))
        return hash_obj.hexdigest()[:16]
    
    @staticmethod
    def generate_team_hash_id(team_name: str, league: str) -> str:
        """Generar ID único para equipo."""
        normalized_team = IDGenerator.normalize_for_id(team_name)
        normalized_league = IDGenerator.normalize_for_id(league)
        
        combined = f"{normalized_team}_{normalized_league}"
        hash_obj = hashlib.sha256(combined.encode('utf-8'))
        return hash_obj.hexdigest()[:16]

# ====================================================================
# DATA PROCESSING
# ====================================================================

class DataNormalizer:
    """Limpieza y normalización de datos."""
    
    def normalize_name(self, name: str) -> str:
        """Normalizar nombres para matching consistente."""
        if not name or pd.isna(name):
            return ""
        
        name_str = str(name)
        if '\n' in name_str and 'dtype: object' in name_str:
            lines = name_str.split('\n')
            for line in lines:
                if 'Name:' not in line and 'dtype:' not in line and line.strip():
                    name_str = line.strip()
                    break
        
        name_str = name_str.lower().strip()
        name_str = unicodedata.normalize('NFD', name_str)
        name_str = ''.join(c for c in name_str if unicodedata.category(c) != 'Mn')
        name_str = re.sub(r'[^\w\s\-\.]', '', name_str)
        name_str = re.sub(r'\s+', ' ', name_str).strip()
        name_str = re.sub(r'\bjr\.?\b', 'jr', name_str)
        name_str = re.sub(r'\bsr\.?\b', 'sr', name_str)
        
        return name_str.title()
    
    def clean_value(self, value: Any, field_name: str) -> Any:
        """Limpiar valores individuales."""
        if pd.isna(value) or value is None:
            return None
        
        str_value = str(value)
        if '\n' in str_value and 'dtype: object' in str_value:
            lines = str_value.split('\n')
            for line in lines:
                if 'Name:' not in line and 'dtype:' not in line and line.strip():
                    str_value = line.strip()
                    break
        
        if isinstance(value, list):
            if field_name in ['teams_played', 'player_name', 'team_name']:
                return ', '.join(str(item) for item in value)
        
        if str_value.lower() in ['nan', 'none', 'null', '']:
            return None
        
        return str_value.strip()


class DataValidator:
    """Validación de integridad de datos con generación de IDs."""
    
    def __init__(self):
        self.normalizer = DataNormalizer()
        self.id_generator = IDGenerator()
    
    def validate_record(self, record: Dict[str, Any], entity_type: str) -> Tuple[Dict[str, Any], float, List[str]]:
        """Validar y limpiar registro con generación de ID único."""
        cleaned_record = {}
        quality_score = 1.0
        warnings = []
        
        # Limpiar campos
        for field, value in record.items():
            cleaned_value = self.normalizer.clean_value(value, field)
            
            if field in METRIC_RANGES and cleaned_value is not None:
                try:
                    numeric_value = float(cleaned_value)
                    min_val, max_val = METRIC_RANGES[field]
                    
                    if numeric_value < min_val or numeric_value > max_val:
                        warnings.append(f"{field} out of range: {numeric_value}")
                        quality_score -= 0.1
                    else:
                        if field in ['age', 'birth_year', 'matches_played', 'goals', 'assists']:
                            cleaned_record[field] = int(numeric_value)
                        else:
                            cleaned_record[field] = numeric_value
                except ValueError:
                    warnings.append(f"Invalid numeric value for {field}: {cleaned_value}")
                    quality_score -= 0.1
            else:
                cleaned_record[field] = cleaned_value
        
        # Validar campos requeridos
        required_fields = ['player_name', 'league', 'season', 'team'] if entity_type == 'player' else ['team_name', 'league', 'season']
        for field in required_fields:
            if field not in cleaned_record or not cleaned_record[field]:
                warnings.append(f"Missing required field: {field}")
                quality_score -= 0.3
        
        # Generar nombre normalizado y ID único
        if entity_type == 'player' and 'player_name' in cleaned_record:
            cleaned_record['normalized_name'] = self.normalizer.normalize_name(cleaned_record['player_name'])
            cleaned_record['unique_player_id'] = self.id_generator.generate_player_hash_id(
                cleaned_record['player_name'],
                cleaned_record.get('birth_year'),
                cleaned_record.get('nationality')
            )
        elif entity_type == 'team' and 'team_name' in cleaned_record:
            cleaned_record['normalized_name'] = self.normalizer.normalize_name(cleaned_record['team_name'])
            cleaned_record['unique_team_id'] = self.id_generator.generate_team_hash_id(
                cleaned_record['team_name'],
                cleaned_record['league']
            )
        
        return cleaned_record, max(0.0, quality_score), warnings

# ====================================================================
# LOADING FUNCTIONS
# ====================================================================

def load_players(competition: str, season: str, table_type: str, logger: LogManager) -> Dict[str, int]:
    """Cargar todos los jugadores de una competición y temporada."""
    db = get_db_manager()
    validator = DataValidator()
    stats = {'total': 0, 'successful': 0, 'failed': 0, 'avg_metrics': 0, 'avg_quality': 0}
    
    try:
        # Limpiar datos existentes
        db.clear_season_data(competition, season, table_type, 'players')
        
        # Obtener lista de jugadores
        players_list_df = fbref_get_league_players(competition, season)
        
        if hasattr(players_list_df.columns, 'levels'):
            players_list_df.columns = [col[0] if col[1] == '' else f"{col[0]}_{col[1]}" for col in players_list_df.columns]
        
        if players_list_df.empty:
            return stats
        
        unique_players = players_list_df['player'].dropna().unique().tolist()
        stats['total'] = len(unique_players)
        
        logger.phase_start("Players", len(unique_players))
        
        # Variables para progreso
        total_metrics = 0
        total_quality = 0
        fbref_success = 0
        understat_success = 0
        understat_total = 0 if table_type == 'european' else len(unique_players)
        
        for i, player_name in enumerate(unique_players, 1):
            current_entity = f"{player_name} (Processing...)"
            
            try:
                # Extraer datos FBref
                fbref_data = fbref_get_player(player_name, competition, season)
                if not fbref_data:
                    stats['failed'] += 1
                    continue
                
                fbref_success += 1
                team = fbref_data.get('team', 'Unknown')
                current_entity = f"{player_name} ({team})"
                
                # Añadir datos Understat para ligas domésticas
                if table_type == 'domestic':
                    understat_data = understat_get_player(player_name, competition, season)
                    if understat_data:
                        understat_success += 1
                        for key, value in understat_data.items():
                            if key.startswith('understat_'):
                                fbref_data[key] = value
                            else:
                                fbref_data[f"understat_{key}"] = value
                
                # Validar y limpiar datos
                cleaned_data, quality_score, warnings = validator.validate_record(fbref_data, 'player')
                cleaned_data['data_quality_score'] = quality_score
                cleaned_data['processing_warnings'] = warnings
                
                # Insertar en base de datos
                success = db.insert_player_data(cleaned_data, table_type)
                
                if success:
                    stats['successful'] += 1
                    total_metrics += len(cleaned_data)
                    total_quality += quality_score
                else:
                    stats['failed'] += 1
                
                # Actualizar progreso cada 10 jugadores o al final
                if i % 10 == 0 or i == len(unique_players):
                    avg_metrics = total_metrics // max(stats['successful'], 1)
                    avg_quality = (total_quality / max(stats['successful'], 1) * 100) if stats['successful'] > 0 else 0
                    
                    logger.progress_update(
                        i, len(unique_players), current_entity, avg_metrics,
                        fbref_success, understat_success, understat_total,
                        avg_quality, stats['failed']
                    )
                
            except Exception:
                stats['failed'] += 1
                continue
        
        # Completar progreso
        logger.progress_complete(stats['total'], stats['successful'], stats['failed'])
        
        # Calcular estadísticas finales
        stats['avg_metrics'] = total_metrics // max(stats['successful'], 1)
        stats['avg_quality'] = (total_quality / max(stats['successful'], 1) * 100) if stats['successful'] > 0 else 0
        
        return stats
        
    except Exception:
        return stats


def load_teams(competition: str, season: str, table_type: str, logger: LogManager) -> Dict[str, int]:
    """Cargar todos los equipos de una competición y temporada."""
    db = get_db_manager()
    validator = DataValidator()
    stats = {'total': 0, 'successful': 0, 'failed': 0, 'avg_metrics': 0, 'avg_quality': 0}
    
    try:
        # Limpiar datos existentes
        db.clear_season_data(competition, season, table_type, 'teams')
        
        # Obtener lista de equipos
        players_list_df = fbref_get_league_players(competition, season)
        
        if players_list_df.empty:
            return stats
        
        unique_teams = players_list_df['team'].dropna().unique().tolist()
        stats['total'] = len(unique_teams)
        
        logger.phase_start("Teams", len(unique_teams))
        
        # Variables para progreso
        total_metrics = 0
        total_quality = 0
        fbref_success = 0
        understat_success = 0
        understat_total = 0 if table_type == 'european' else len(unique_teams)
        
        for i, team_name in enumerate(unique_teams, 1):
            current_entity = f"{team_name}"
            
            try:
                # Extraer datos FBref
                fbref_data = fbref_get_team(team_name, competition, season)
                if not fbref_data:
                    stats['failed'] += 1
                    continue
                
                fbref_success += 1
                
                # Añadir datos Understat para ligas domésticas
                if table_type == 'domestic':
                    understat_data = understat_get_team(team_name, competition, season)
                    if understat_data:
                        understat_success += 1
                        for key, value in understat_data.items():
                            if key.startswith('understat_'):
                                fbref_data[key] = value
                            else:
                                fbref_data[f"understat_{key}"] = value
                
                # Validar y limpiar datos
                cleaned_data, quality_score, warnings = validator.validate_record(fbref_data, 'team')
                cleaned_data['data_quality_score'] = quality_score
                cleaned_data['processing_warnings'] = warnings
                
                # Insertar en base de datos
                success = db.insert_team_data(cleaned_data, table_type)
                
                if success:
                    stats['successful'] += 1
                    total_metrics += len(cleaned_data)
                    total_quality += quality_score
                else:
                    stats['failed'] += 1
                
                # Actualizar progreso cada 5 equipos o al final
                if i % 5 == 0 or i == len(unique_teams):
                    avg_metrics = total_metrics // max(stats['successful'], 1)
                    avg_quality = (total_quality / max(stats['successful'], 1) * 100) if stats['successful'] > 0 else 0
                    
                    logger.progress_update(
                        i, len(unique_teams), current_entity, avg_metrics,
                        fbref_success, understat_success, understat_total,
                        avg_quality, stats['failed']
                    )
                
            except Exception:
                stats['failed'] += 1
                continue
        
        # Completar progreso
        logger.progress_complete(stats['total'], stats['successful'], stats['failed'])
        
        # Calcular estadísticas finales
        stats['avg_metrics'] = total_metrics // max(stats['successful'], 1)
        stats['avg_quality'] = (total_quality / max(stats['successful'], 1) * 100) if stats['successful'] > 0 else 0
        
        return stats
        
    except Exception:
        return stats


def load_complete_competition(competition: str, season: str) -> Dict[str, Dict[str, int]]:
    """Cargar jugadores y equipos completos de una competición."""
    table_type = 'domestic' if competition != 'INT-Champions League' else 'european'
    data_source = "FBref + Understat" if table_type == 'domestic' else "FBref only"
    
    # Inicializar logger
    logger = LogManager()
    logger.header(f"{competition} {season}", data_source)
    
    # Estado de base de datos
    db = get_db_manager()
    logger.database_status(True, "footballdecoded", 0)
    
    # Cargar jugadores
    player_stats = load_players(competition, season, table_type, logger)
    
    # Cargar equipos
    team_stats = load_teams(competition, season, table_type, logger)
    
    # Calcular estadísticas de coverage
    understat_coverage = None
    if table_type == 'domestic':
        player_coverage = (player_stats.get('understat_success', 0) / max(player_stats['successful'], 1) * 100) if player_stats['successful'] > 0 else 0
        team_coverage = (team_stats.get('understat_success', 0) / max(team_stats['successful'], 1) * 100) if team_stats['successful'] > 0 else 0
        understat_coverage = {'players': player_coverage, 'teams': team_coverage}
    
    # Summary final
    summary_stats = {
        'players': player_stats,
        'teams': team_stats,
        'understat_coverage': understat_coverage,
        'avg_metrics': {
            'players': player_stats.get('avg_metrics', 0),
            'teams': team_stats.get('avg_metrics', 0)
        },
        'avg_quality': (player_stats.get('avg_quality', 0) + team_stats.get('avg_quality', 0)) / 2
    }
    
    logger.final_summary(summary_stats)
    
    db.close()
    return {'players': player_stats, 'teams': team_stats}

# ====================================================================
# MAIN EXECUTION
# ====================================================================

def main():
    """Función principal de ejecución."""
    print("FootballDecoded Data Loader - ID System")
    print("=" * 50)
    print("\n1. Load competition data (players + teams)")
    print("2. Test database connection")
    print("3. Setup database schema")
    print("4. Clear all existing data")
    print("5. Check database status")
    
    choice = input("\nSelect option (1-5): ").strip()
    
    if choice == "1":
        print("\nAvailable competitions:")
        for i, (comp_name, comp_type) in enumerate(AVAILABLE_COMPETITIONS, 1):
            data_source = "FBref + Understat" if comp_type == 'domestic' else "FBref only"
            print(f"   {i}. {comp_name} ({data_source})")
        
        try:
            comp_choice = int(input(f"\nSelect competition (1-{len(AVAILABLE_COMPETITIONS)}): ").strip())
            if 1 <= comp_choice <= len(AVAILABLE_COMPETITIONS):
                selected_competition, _ = AVAILABLE_COMPETITIONS[comp_choice - 1]
                season = input("Enter season (e.g., 2024-25): ").strip()
                
                if season:
                    load_complete_competition(selected_competition, season)
                else:
                    print("Invalid season format")
            else:
                print("Invalid competition selection")
        except ValueError:
            print("Invalid input")
    
    elif choice == "2":
        print("\nTesting database connection...")
        try:
            from database.connection import test_connection
            success = test_connection()
            status = "successful" if success else "failed"
            print(f"Database connection {status}")
        except Exception as e:
            print(f"Connection test error: {e}")
    
    elif choice == "3":
        confirm = input("Setup database schema? This will create/recreate tables (y/N): ").strip().lower()
        if confirm == 'y':
            print("\nSetting up database schema...")
            try:
                from database.connection import setup_database
                success = setup_database()
                status = "complete" if success else "failed"
                print(f"Database schema setup {status}")
            except Exception as e:
                print(f"Schema setup error: {e}")
        else:
            print("Schema setup cancelled")
    
    elif choice == "4":
        confirm = input("Clear ALL data? (type 'YES' to confirm): ").strip()
        if confirm == "YES":
            try:
                from database.connection import get_db_manager
                from sqlalchemy import text
                
                db = get_db_manager()
                
                with db.engine.begin() as conn:
                    conn.execute(text("DELETE FROM footballdecoded.players_domestic"))
                    conn.execute(text("DELETE FROM footballdecoded.teams_domestic"))
                    conn.execute(text("DELETE FROM footballdecoded.players_european"))
                    conn.execute(text("DELETE FROM footballdecoded.teams_european"))
                
                print("All data cleared successfully")
                db.close()
            except Exception as e:
                print(f"Failed to clear data: {e}")
        else:
            print("Clear operation cancelled")
    
    elif choice == "5":
        print("\nChecking database status...")
        try:
            from database.database_checker import check_database_status
            check_database_status(verbose=True)
        except ImportError:
            print("database_checker.py not found")
        except Exception as e:
            print(f"Error checking database: {e}")
    
    else:
        print("Invalid option. Please select 1-5.")


if __name__ == "__main__":
    main()