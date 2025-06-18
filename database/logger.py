# ====================================================================
# FootballDecoded Unified Logger - Sistema Visual Profesional
# ====================================================================

import time
from typing import Optional
from datetime import datetime

class UnifiedLogger:
    """Sistema de logging profesional y consistente."""
    
    def __init__(self):
        self.start_time = None
        self.phase_start_time = None
        self.line_width = 80
        self.current_line_count = 0
    
    def header(self, competition: str, season: str, data_sources: str):
        """Header principal con información de la carga."""
        print("FootballDecoded Data Loader")
        print("═" * self.line_width)
        print(f"Competition: {competition} {season}")
        print(f"Data sources: {data_sources}")
        print(f"Database: Connected | Schema: footballdecoded") 
        print("─" * self.line_width)
        print()
        self.start_time = datetime.now()
    
    def massive_header(self, season: str):
        """Header para carga masiva."""
        print("FootballDecoded Massive Annual Loader")
        print("═" * self.line_width)
        print(f"Season: {season} | All Competitions")
        print(f"Block 1: ENG + ESP + ITA")
        print(f"Block 2: GER + FRA + Champions")
        print(f"Pause between blocks: 30-60 minutes (random)")
        print("─" * self.line_width)
        print()
        self.start_time = datetime.now()
    
    def phase_start(self, phase_name: str, total_entities: int):
        """Inicio de fase (Players/Teams)."""
        self.phase_start_time = datetime.now()
        print(f"{phase_name.upper()} EXTRACTION")
        print(f"Entities found: {total_entities:,}")
        print("─" * 50)
        self.current_line_count = 0
    
    def entity_update(self, entity_type: str, name: str, team_or_league: str, 
                     metrics: int, state: str, failed_count: int):
        """Update individual para cada entidad con formato solicitado."""
        # Limpiar línea anterior
        if self.current_line_count > 0:
            print(f"\033[1A\033[K", end="")
        
        # Formato específico solicitado
        if entity_type.lower() == 'player':
            status_line = f"Player: {name} | Team: {team_or_league} | Metrics: {metrics} | State: {state} | Failed: {failed_count}"
        else:
            status_line = f"Team: {name} | League: {team_or_league} | Metrics: {metrics} | State: {state} | Failed: {failed_count}"
        
        # Truncar si es muy largo
        if len(status_line) > self.line_width:
            status_line = status_line[:self.line_width-3] + "..."
        
        print(status_line)
        self.current_line_count = 1
    
    def progress_bar(self, current: int, total: int):
        """Barra de progreso elegante - fondo blanco, relleno verde."""
        if self.current_line_count > 0:
            print(f"\033[1A\033[K", end="")
        
        percentage = (current / total) * 100
        filled = int(40 * current // total)
        
        # Barra elegante: fondo blanco, relleno verde
        bar_filled = '\033[42m' + ' ' * filled + '\033[0m'  # Verde
        bar_empty = '\033[47m' + ' ' * (40 - filled) + '\033[0m'  # Blanco
        
        progress_line = f"Progress: [{bar_filled}{bar_empty}] {current}/{total} ({percentage:.1f}%)"
        print(progress_line)
        self.current_line_count = 1
    
    def phase_complete(self, successful: int, failed: int, total: int):
        """Completar fase con resumen."""
        if self.current_line_count > 0:
            print()  # Saltar línea después del último update
        
        success_rate = (successful / total * 100) if total > 0 else 0
        
        if self.phase_start_time:
            elapsed = (datetime.now() - self.phase_start_time).total_seconds()
            elapsed_formatted = self._format_time(int(elapsed))
            print(f"✅ Completed in: {elapsed_formatted}")
        
        print(f"Success: {successful}/{total} ({success_rate:.1f}%) | Failed: {failed}")
        print()
    
    def competition_summary(self, competition: str, player_stats: dict, team_stats: dict):
        """Resumen de competición."""
        total_success = player_stats['successful'] + team_stats['successful']
        total_entities = player_stats['total'] + team_stats['total']
        success_rate = (total_success / total_entities * 100) if total_entities > 0 else 0
        
        print(f"COMPETITION SUMMARY: {competition}")
        print(f"Total: {total_entities} | Success: {total_success} | Rate: {success_rate:.1f}%")
        print(f"Players: {player_stats['successful']} | Teams: {team_stats['successful']}")
        print()
    
    def block_pause(self, block_name: str, minutes: int):
        """Pausa entre bloques de carga masiva."""
        print("─" * self.line_width)
        print(f"BLOCK COMPLETED: {block_name}")
        print(f"Pausing {minutes} minutes before next block...")
        print("─" * self.line_width)
        
        # Countdown elegante
        for minute in range(minutes, 0, -1):
            print(f"\rResuming in: {minute} minutes...", end="", flush=True)
            time.sleep(60)
        print(f"\rResuming now...                  ")
        print()
    
    def final_summary(self, stats: dict):
        """Resumen final con formato elegante."""
        print("─" * self.line_width)
        print("EXTRACTION SUMMARY")
        print("─" * self.line_width)
        
        total = stats['players']['total'] + stats['teams']['total']
        successful = stats['players']['successful'] + stats['teams']['successful']
        failed = stats['players']['failed'] + stats['teams']['failed']
        success_rate = (successful / total * 100) if total > 0 else 0
        
        print(f"Total entities: {total:,}")
        print(f"Successful: {successful:,} ({success_rate:.1f}%)")
        print(f"Failed: {failed:,}")
        print(f"Players: {stats['players']['successful']:,} | Teams: {stats['teams']['successful']:,}")
        
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            total_seconds = elapsed.total_seconds()
            elapsed_formatted = self._format_time(int(total_seconds))
            print(f"Processing time: {elapsed_formatted}")
        
        print("═" * self.line_width)
    
    def _format_time(self, seconds: int) -> str:
        """Formatear tiempo de forma elegante."""
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