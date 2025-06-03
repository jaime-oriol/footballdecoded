#!/usr/bin/env python3
"""
PSG Data Extraction Script - Configuración Base
==============================================================================
Script para extraer y consolidar datos del PSG (Paris Saint-Germain) 
comparando temporadas 2023/24 vs 2024/25.

Autor: FootballDecoded Analytics
Fecha: 2025-06-03
Estructura: analysis/tactical_analysis/PSG/data_psg.py
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
            
            # Understat - Para xG y stats avanzadas
            logger.info("Configurando Understat...")
            try:
                # Understat usa los mismos códigos que FBref
                self.understat = Understat(
                    leagues=self.config.leagues,  # Usar directamente los códigos de FBref
                    seasons=self.config.seasons,
                    no_cache=False,
                    no_store=False
                )
                    
            except Exception as e:
                logger.warning(f"Error inicializando Understat: {e}")
                self.understat = None
            
            # Match History - Saltamos por ahora debido a códigos incompatibles
            logger.info("Configurando Match History...")
            logger.info("Match History: Saltando por incompatibilidad de códigos de liga")
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
        
        # Match History está deshabilitado por ahora
        status['match_history'] = False
        
        return status
    
    def extract_team_stats(self) -> pd.DataFrame:
        """
        Extrae estadísticas del PSG como equipo
        
        Returns:
            pd.DataFrame: Estadísticas consolidadas del equipo
        """
        logger.info("🏟️ Iniciando extracción de estadísticas del equipo PSG...")
        
        team_data_list = []
        
        # Extraer desde FBref
        if self.fbref:
            logger.info("📊 Extrayendo datos de equipo desde FBref...")
            try:
                # Estadísticas estándar del equipo
                team_stats = self.fbref.read_team_season_stats(stat_type='standard')
                
                if not team_stats.empty:
                    # Filtrar solo PSG (diferentes variaciones del nombre)
                    psg_mask = (
                        team_stats.index.get_level_values('team').str.contains('Paris Saint-Germain|PSG|Paris SG', case=False, na=False)
                    )
                    psg_stats = team_stats[psg_mask]
                    
                    if not psg_stats.empty:
                        # Convertir a formato largo para consolidación
                        psg_reset = psg_stats.reset_index()
                        psg_reset['source'] = 'FBref'
                        psg_reset['stat_type'] = 'standard'
                        team_data_list.append(psg_reset)
                        logger.info(f"✅ Extraídas {len(psg_stats)} filas de estadísticas estándar FBref")
                    else:
                        logger.warning("❌ No se encontraron datos del PSG en FBref")
                
                # Intentar otras categorías de estadísticas
                for stat_type in ['shooting', 'passing', 'defense', 'possession']:
                    try:
                        logger.info(f"📊 Extrayendo estadísticas de {stat_type}...")
                        stats = self.fbref.read_team_season_stats(stat_type=stat_type)
                        
                        if not stats.empty:
                            psg_mask = (
                                stats.index.get_level_values('team').str.contains('Paris Saint-Germain|PSG|Paris SG', case=False, na=False)
                            )
                            psg_stats = stats[psg_mask]
                            
                            if not psg_stats.empty:
                                psg_reset = psg_stats.reset_index()
                                psg_reset['source'] = 'FBref'
                                psg_reset['stat_type'] = stat_type
                                team_data_list.append(psg_reset)
                                logger.info(f"✅ Extraídas {len(psg_stats)} filas de estadísticas {stat_type}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error extrayendo {stat_type}: {e}")
                        
            except Exception as e:
                logger.error(f"❌ Error extrayendo datos de FBref: {e}")
        
        # Extraer desde Understat
        if self.understat:
            logger.info("📊 Extrayendo datos de equipo desde Understat...")
            try:
                # Intentar extraer datos de temporada
                team_match_stats = self.understat.read_team_match_stats()
                
                if not team_match_stats.empty:
                    # Filtrar PSG
                    psg_mask = (
                        team_match_stats.index.get_level_values('team').str.contains('Paris Saint-Germain|PSG|Paris SG', case=False, na=False)
                    )
                    psg_stats = team_match_stats[psg_mask]
                    
                    if not psg_stats.empty:
                        psg_reset = psg_stats.reset_index()
                        psg_reset['source'] = 'Understat'
                        psg_reset['stat_type'] = 'match_stats'
                        team_data_list.append(psg_reset)
                        logger.info(f"✅ Extraídas {len(psg_stats)} filas de Understat")
                
            except Exception as e:
                logger.error(f"❌ Error extrayendo datos de Understat: {e}")
        
        # Consolidar todos los datos
        if team_data_list:
            consolidated_data = pd.concat(team_data_list, ignore_index=True)
            logger.info(f"✅ Consolidadas {len(consolidated_data)} filas de datos del equipo")
            
            # Guardar datos
            output_file = self.config.output_dir / "psg_team_stats.csv"
            consolidated_data.to_csv(output_file, index=False)
            logger.info(f"💾 Datos guardados en: {output_file}")
            
            return consolidated_data
        else:
            logger.warning("❌ No se pudieron extraer datos del equipo")
            return pd.DataFrame()

def main():
    """Función principal - Ahora incluye extracción de datos"""
    print("🚀 PSG Data Extraction Script - Configuración y Extracción")
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
    
    logger.info("✅ Configuración completada - Iniciando extracción")
    
    # NUEVA FUNCIONALIDAD: Extraer datos del equipo
    print("\n🏟️ Extrayendo estadísticas del equipo PSG...")
    print("-" * 50)
    
    team_data = extractor.extract_team_stats()
    
    if not team_data.empty:
        print(f"\n✅ Extracción completada: {len(team_data)} registros")
        print(f"📁 Datos guardados en: {config.output_dir}")
        
        # Mostrar resumen de datos extraídos
        print("\n📊 Resumen de datos extraídos:")
        print(team_data.groupby(['source', 'stat_type', 'season']).size().to_string())
        
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Extracción de datos del equipo completada")
        print("💡 Próximo paso: Implementar extracción de estadísticas de jugadores")
    else:
        print("\n❌ Error en la extracción")
        sys.exit(1)