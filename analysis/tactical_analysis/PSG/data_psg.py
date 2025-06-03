#!/usr/bin/env python3
"""
PSG Data Extraction Script - Configuración Base
==============================================================================
Script para extraer y consolidar datos del PSG (Paris Saint-Germain) 
comparando temporadas 2023/24 vs 2024/25.

Autor: FootballDecoded Analytics
Fecha: 2025-06-03
Estructura: analysis/tactical_analysis/PSG/psg_complete_data_extractor.py
==============================================================================
"""

import os
import sys
import logging
import warnings
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple
import pandas as pd
import sqlite3
from dataclasses import dataclass

# Configurar el path para importar módulos del proyecto
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# Importar módulos del proyecto
try:
    from data.fbref import FBref
    from data.understat import Understat
    from data.match_history import MatchHistory
except ImportError as e:
    print(f"Error importando módulos del proyecto: {e}")
    print("Asegúrate de ejecutar desde la raíz del proyecto")
    sys.exit(1)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('psg_data_extraction.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Suprimir warnings de pandas
warnings.filterwarnings('ignore', category=FutureWarning)

@dataclass
class ExtractionConfig:
    """Configuración para la extracción de datos del PSG"""
    
    # Temporadas a analizar
    seasons: List[str] = None
    
    # Ligas y competiciones
    leagues: List[str] = None
    
    # Jugadores clave del PSG (nombres como aparecen en las fuentes)
    key_players: List[str] = None
    
    # Directorio de salida
    output_dir: Path = None
    
    # Configuración de base de datos
    use_database: bool = False
    db_path: str = "psg_analysis.db"
    
    def __post_init__(self):
        if self.seasons is None:
            self.seasons = ["2023-24", "2024-25"]
        
        if self.leagues is None:
            self.leagues = ["FRA-Ligue 1"]  # Empezamos solo con Ligue 1
        
        if self.key_players is None:
            # Nombres como aparecen típicamente en FBref/Understat
            self.key_players = [
                "Kylian Mbappé",
                "Ousmane Dembélé", 
                "Vitinha",
                "Warren Zaïre-Emery",
                "Achraf Hakimi",
                "Marquinhos",
                "Gianluigi Donnarumma",
                "Bradley Barcola",
                "Randal Kolo Muani",
                "Lee Kang-in"
            ]
        
        if self.output_dir is None:
            self.output_dir = Path("analysis/tactical_analysis/PSG/data_extracts")
        
        # Crear directorio de salida si no existe
        self.output_dir.mkdir(parents=True, exist_ok=True)

class PSGDataExtractor:
    """Clase principal para extraer datos del PSG"""
    
    def __init__(self, config: ExtractionConfig):
        self.config = config
        self.fbref = None
        self.understat = None
        self.match_history = None
        
        # DataFrames para almacenar datos consolidados
        self.team_stats = pd.DataFrame()
        self.player_stats = pd.DataFrame()
        self.match_results = pd.DataFrame()
        
        logger.info("Inicializando PSGDataExtractor...")
        logger.info(f"Temporadas: {self.config.seasons}")
        logger.info(f"Ligas: {self.config.leagues}")
        logger.info(f"Jugadores clave: {len(self.config.key_players)} jugadores")
    
    def initialize_data_sources(self) -> bool:
        """
        Inicializa las fuentes de datos con configuración optimizada
        
        Returns:
            bool: True si todas las fuentes se inicializaron correctamente
        """
        try:
            logger.info("Inicializando fuentes de datos...")
            
            # FBref - Principal fuente para stats detalladas
            logger.info("Configurando FBref...")
            self.fbref = FBref(
                leagues=self.config.leagues,
                seasons=self.config.seasons,
                no_cache=False,  # Usar cache para evitar re-descargas
                no_store=False   # Guardar datos localmente
            )
            
            # Understat - Para xG y stats avanzadas (solo ligas principales)
            logger.info("Configurando Understat...")
            try:
                # Understat usa diferentes códigos de liga
                understat_leagues = []
                for league in self.config.leagues:
                    if "FRA-Ligue 1" in league:
                        understat_leagues.append("Ligue 1")
                    elif "ENG-Premier" in league:
                        understat_leagues.append("EPL")
                    # Agregar más mapeos según sea necesario
                
                if understat_leagues:
                    self.understat = Understat(
                        leagues=understat_leagues,
                        seasons=self.config.seasons,
                        no_cache=False,
                        no_store=False
                    )
                else:
                    logger.warning("No se encontraron ligas compatibles con Understat")
                    
            except Exception as e:
                logger.warning(f"Error inicializando Understat: {e}")
                self.understat = None
            
            # Match History - Para datos básicos de partidos
            logger.info("Configurando Match History...")
            try:
                # Match History también usa códigos diferentes
                mh_leagues = []
                for league in self.config.leagues:
                    if "FRA-Ligue 1" in league:
                        mh_leagues.append("F1")
                    elif "ENG-Premier" in league:
                        mh_leagues.append("E0")
                    # Agregar más mapeos según sea necesario
                
                if mh_leagues:
                    self.match_history = MatchHistory(
                        leagues=mh_leagues,
                        seasons=self.config.seasons,
                        no_cache=False,
                        no_store=False
                    )
                else:
                    logger.warning("No se encontraron ligas compatibles con Match History")
                    
            except Exception as e:
                logger.warning(f"Error inicializando Match History: {e}")
                self.match_history = None
            
            logger.info("✅ Fuentes de datos inicializadas correctamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando fuentes de datos: {e}")
            return False
    
    def validate_data_sources(self) -> Dict[str, bool]:
        """
        Valida que las fuentes de datos estén funcionando
        
        Returns:
            Dict[str, bool]: Estado de cada fuente de datos
        """
        status = {}
        
        # Validar FBref
        try:
            if self.fbref:
                leagues_available = self.fbref.available_leagues()
                status['fbref'] = len(leagues_available) > 0
                logger.info(f"FBref: {len(leagues_available)} ligas disponibles")
            else:
                status['fbref'] = False
        except Exception as e:
            logger.error(f"Error validando FBref: {e}")
            status['fbref'] = False
        
        # Validar Understat
        try:
            if self.understat:
                leagues_available = self.understat.available_leagues()
                status['understat'] = len(leagues_available) > 0
                logger.info(f"Understat: {len(leagues_available)} ligas disponibles")
            else:
                status['understat'] = False
        except Exception as e:
            logger.error(f"Error validando Understat: {e}")
            status['understat'] = False
        
        # Validar Match History
        try:
            if self.match_history:
                leagues_available = self.match_history.available_leagues()
                status['match_history'] = len(leagues_available) > 0
                logger.info(f"Match History: {len(leagues_available)} ligas disponibles")
            else:
                status['match_history'] = False
        except Exception as e:
            logger.error(f"Error validando Match History: {e}")
            status['match_history'] = False
        
        return status

def main():
    """Función principal - Fase 1: Configuración y validación"""
    print("🚀 PSG Data Extraction Script - Fase 1: Configuración")
    print("=" * 60)
    
    # Crear configuración
    config = ExtractionConfig()
    
    # Crear extractor
    extractor = PSGDataExtractor(config)
    
    # Inicializar fuentes de datos
    if not extractor.initialize_data_sources():
        logger.error("❌ Fallo en la inicialización de fuentes de datos")
        return False
    
    # Validar fuentes de datos
    status = extractor.validate_data_sources()
    
    print("\n📊 Estado de las fuentes de datos:")
    print("-" * 40)
    for source, is_working in status.items():
        status_icon = "✅" if is_working else "❌"
        print(f"{status_icon} {source.capitalize()}: {'Funcionando' if is_working else 'Error'}")
    
    working_sources = sum(status.values())
    print(f"\n📈 Fuentes operativas: {working_sources}/{len(status)}")
    
    if working_sources == 0:
        logger.error("❌ Ninguna fuente de datos está funcionando")
        return False
    
    logger.info("✅ Fase 1 completada - Configuración exitosa")
    print("\n🎯 Siguiente paso: Ejecutar extracción de datos del equipo")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Script configurado correctamente")
        print("💡 Próximo paso: Implementar extracción de estadísticas de equipo")
    else:
        print("\n❌ Error en la configuración")
        sys.exit(1)