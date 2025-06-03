#!/usr/bin/env python3
"""
PSG Data Extraction Module
==========================

Módulo para extraer y procesar datos del PSG de las temporadas 2023/24 y 2024/25.
Integrado con la arquitectura existente de FootballDecoded.

Author: FootballDecoded
Created: 2025-06-03
"""

import logging
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union
import pandas as pd

# Imports from existing data infrastructure
from data.fbref import FBref
from data.understat import Understat
from data.fotmob import FotMob
from data._config import DATA_DIR, logger

# Configuration - Use project structure instead of default soccerdata path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PSG_DATA_DIR = PROJECT_ROOT / "analysis" / "tactical_analysis" / "PSG" / "data"
PSG_TEAM_VARIATIONS = [
    "Paris S-G",
    "Paris Saint-Germain", 
    "PSG",
    "Paris SG"
]

class PSGDataExtractor:
    """
    Extractor especializado para datos del PSG.
    
    Combina múltiples fuentes de datos siguiendo el patrón híbrido
    establecido en la arquitectura FootballDecoded.
    """
    
    def __init__(
        self,
        seasons: List[str] = ["2023-24", "2024-25"],
        leagues: List[str] = ["FRA-Ligue 1"],
        data_dir: Path = None
    ):
        """
        Initialize PSG data extractor.
        
        Parameters
        ----------
        seasons : List[str]
            Temporadas a analizar
        leagues : List[str] 
            Ligas a incluir (por defecto solo Ligue 1)
        data_dir : Path
            Directorio para almacenar datos procesados
        """
        self.seasons = seasons
        self.leagues = leagues
        
        # Use project structure if no custom path provided
        if data_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            self.data_dir = project_root / "analysis" / "tactical_analysis" / "PSG" / "data"
        else:
            self.data_dir = data_dir
        
        # Create directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "raw").mkdir(exist_ok=True)
        (self.data_dir / "processed").mkdir(exist_ok=True)
        (self.data_dir / "logs").mkdir(exist_ok=True)
        
        # Initialize data sources
        self._init_data_sources()
        
        logger.info(f"PSG Data Extractor initialized for seasons: {seasons}")
    
    def _init_data_sources(self):
        """Initialize data source connections."""
        try:
            self.fbref = FBref(
                leagues=self.leagues,
                seasons=self.seasons,
                no_cache=False
            )
            logger.info("✅ FBref connection initialized")
        except Exception as e:
            logger.error(f"❌ FBref initialization failed: {e}")
            self.fbref = None
            
        try:
            self.understat = Understat(
                leagues=self.leagues,
                seasons=self.seasons,
                no_cache=False
            )
            logger.info("✅ Understat connection initialized")
        except Exception as e:
            logger.error(f"❌ Understat initialization failed: {e}")
            self.understat = None
            
        try:
            self.fotmob = FotMob(
                leagues=self.leagues,
                seasons=self.seasons,
                no_cache=False
            )
            logger.info("✅ FotMob connection initialized")
        except Exception as e:
            logger.error(f"❌ FotMob initialization failed: {e}")
            self.fotmob = None
    
    def extract_team_season_stats(self) -> Dict[str, pd.DataFrame]:
        """
        Extract comprehensive team-level statistics for PSG.
        
        Returns
        -------
        Dict[str, pd.DataFrame]
            Dictionary with stats from different sources
        """
        logger.info("🔄 Starting PSG team season stats extraction...")
        
        stats_dict = {}
        
        # FBref team stats - Multiple stat types
        if self.fbref:
            fbref_stats = self._extract_fbref_team_stats()
            stats_dict.update(fbref_stats)
        
        # Understat team stats
        if self.understat:
            understat_stats = self._extract_understat_team_stats()
            stats_dict['understat_team'] = understat_stats
        
        # FotMob team stats
        if self.fotmob:
            fotmob_stats = self._extract_fotmob_team_stats()
            stats_dict['fotmob_team'] = fotmob_stats
        
        # Save raw data
        self._save_raw_data(stats_dict, "team_season_stats")
        
        logger.info(f"✅ Team stats extraction completed. Sources: {list(stats_dict.keys())}")
        return stats_dict
    
    def _extract_fbref_team_stats(self) -> Dict[str, pd.DataFrame]:
        """Extract all available team stats from FBref."""
        stat_types = [
            'standard', 'keeper', 'keeper_adv', 'shooting', 'passing',
            'passing_types', 'goal_shot_creation', 'defense', 'possession',
            'playing_time', 'misc'
        ]
        
        fbref_data = {}
        
        for stat_type in stat_types:
            try:
                logger.info(f"📊 Extracting FBref {stat_type} stats...")
                
                # Regular stats
                df = self.fbref.read_team_season_stats(stat_type=stat_type)
                psg_data = self._filter_psg_data(df)
                if not psg_data.empty:
                    fbref_data[f'fbref_team_{stat_type}'] = psg_data
                
                # Opponent stats
                df_opp = self.fbref.read_team_season_stats(
                    stat_type=stat_type, 
                    opponent_stats=True
                )
                psg_opp_data = self._filter_psg_data(df_opp)
                if not psg_opp_data.empty:
                    fbref_data[f'fbref_team_{stat_type}_against'] = psg_opp_data
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to extract {stat_type}: {e}")
                continue
        
        return fbref_data
    
    def _extract_understat_team_stats(self) -> pd.DataFrame:
        """Extract team match stats from Understat."""
        try:
            logger.info("📊 Extracting Understat team stats...")
            df = self.understat.read_team_match_stats()
            return self._filter_psg_data(df)
        except Exception as e:
            logger.warning(f"⚠️ Understat team stats failed: {e}")
            return pd.DataFrame()
    
    def _extract_fotmob_team_stats(self) -> pd.DataFrame:
        """Extract team match stats from FotMob."""
        try:
            logger.info("📊 Extracting FotMob team stats...")
            # FotMob requires specific stat types
            stat_types = ['Top stats', 'Shots', 'Expected goals (xG)', 'Passes', 'Defence']
            
            all_stats = []
            for stat_type in stat_types:
                try:
                    df = self.fotmob.read_team_match_stats(stat_type=stat_type)
                    psg_data = self._filter_psg_data(df)
                    if not psg_data.empty:
                        psg_data['stat_type'] = stat_type
                        all_stats.append(psg_data)
                except Exception as e:
                    logger.warning(f"⚠️ FotMob {stat_type} failed: {e}")
                    continue
            
            return pd.concat(all_stats) if all_stats else pd.DataFrame()
            
        except Exception as e:
            logger.warning(f"⚠️ FotMob team stats failed: {e}")
            return pd.DataFrame()
    
    def extract_player_season_stats(self) -> Dict[str, pd.DataFrame]:
        """
        Extract comprehensive player-level statistics for PSG.
        
        Returns
        -------
        Dict[str, pd.DataFrame]
            Dictionary with player stats from different sources
        """
        logger.info("🔄 Starting PSG player season stats extraction...")
        
        stats_dict = {}
        
        # FBref player stats
        if self.fbref:
            fbref_stats = self._extract_fbref_player_stats()
            stats_dict.update(fbref_stats)
        
        # Understat player stats
        if self.understat:
            understat_stats = self._extract_understat_player_stats()
            stats_dict['understat_players'] = understat_stats
        
        # Save raw data
        self._save_raw_data(stats_dict, "player_season_stats")
        
        logger.info(f"✅ Player stats extraction completed. Sources: {list(stats_dict.keys())}")
        return stats_dict
    
    def _extract_fbref_player_stats(self) -> Dict[str, pd.DataFrame]:
        """Extract all available player stats from FBref."""
        stat_types = [
            'standard', 'shooting', 'passing', 'passing_types',
            'goal_shot_creation', 'defense', 'possession', 'playing_time',
            'misc', 'keeper', 'keeper_adv'
        ]
        
        fbref_data = {}
        
        for stat_type in stat_types:
            try:
                logger.info(f"👤 Extracting FBref player {stat_type} stats...")
                df = self.fbref.read_player_season_stats(stat_type=stat_type)
                psg_players = self._filter_psg_data(df)
                if not psg_players.empty:
                    fbref_data[f'fbref_players_{stat_type}'] = psg_players
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to extract player {stat_type}: {e}")
                continue
        
        return fbref_data
    
    def _extract_understat_player_stats(self) -> pd.DataFrame:
        """Extract player season stats from Understat."""
        try:
            logger.info("👤 Extracting Understat player stats...")
            df = self.understat.read_player_season_stats()
            return self._filter_psg_data(df)
        except Exception as e:
            logger.warning(f"⚠️ Understat player stats failed: {e}")
            return pd.DataFrame()
    
    def extract_match_data(self) -> Dict[str, pd.DataFrame]:
        """
        Extract match-by-match data for detailed analysis.
        
        Returns
        -------
        Dict[str, pd.DataFrame]
            Dictionary with match data from different sources
        """
        logger.info("🔄 Starting PSG match data extraction...")
        
        match_dict = {}
        
        # FBref match data
        if self.fbref:
            fbref_matches = self._extract_fbref_match_data()
            match_dict.update(fbref_matches)
        
        # Understat match data
        if self.understat:
            understat_matches = self._extract_understat_match_data()
            match_dict['understat_matches'] = understat_matches
        
        # Save raw data
        self._save_raw_data(match_dict, "match_data")
        
        logger.info(f"✅ Match data extraction completed. Sources: {list(match_dict.keys())}")
        return match_dict
    
    def _extract_fbref_match_data(self) -> Dict[str, pd.DataFrame]:
        """Extract match-by-match data from FBref."""
        stat_types = ['schedule', 'shooting', 'passing', 'defense', 'possession', 'misc']
        
        fbref_matches = {}
        
        for stat_type in stat_types:
            try:
                logger.info(f"⚽ Extracting FBref match {stat_type} data...")
                df = self.fbref.read_team_match_stats(stat_type=stat_type)
                psg_matches = self._filter_psg_data(df)
                if not psg_matches.empty:
                    fbref_matches[f'fbref_matches_{stat_type}'] = psg_matches
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to extract match {stat_type}: {e}")
                continue
        
        return fbref_matches
    
    def _extract_understat_match_data(self) -> pd.DataFrame:
        """Extract match data from Understat."""
        try:
            logger.info("⚽ Extracting Understat match data...")
            df = self.understat.read_team_match_stats()
            return self._filter_psg_data(df)
        except Exception as e:
            logger.warning(f"⚠️ Understat match data failed: {e}")
            return pd.DataFrame()
    
    def _filter_psg_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter dataframe to include only PSG data.
        
        Parameters
        ----------
        df : pd.DataFrame
            Input dataframe
            
        Returns
        -------
        pd.DataFrame
            Filtered dataframe with only PSG data
        """
        if df.empty:
            return df
        
        # Check different possible team column names and index levels
        team_columns = ['team', 'Squad', 'home_team', 'away_team']
        
        # Filter by index if team is in index
        if hasattr(df.index, 'names'):
            for level_name in df.index.names:
                if level_name in team_columns:
                    level_idx = df.index.names.index(level_name)
                    mask = df.index.get_level_values(level_idx).isin(PSG_TEAM_VARIATIONS)
                    return df[mask]
        
        # Filter by columns
        for col in team_columns:
            if col in df.columns:
                mask = df[col].isin(PSG_TEAM_VARIATIONS)
                psg_data = df[mask]
                if not psg_data.empty:
                    return psg_data
        
        # If no direct match, try broader search
        for col in df.columns:
            if 'team' in col.lower() or 'squad' in col.lower():
                mask = df[col].astype(str).str.contains('|'.join(PSG_TEAM_VARIATIONS), na=False)
                psg_data = df[mask]
                if not psg_data.empty:
                    return psg_data
        
        logger.warning(f"⚠️ No PSG data found in dataframe with columns: {list(df.columns)}")
        return pd.DataFrame()
    
    def _save_raw_data(self, data_dict: Dict[str, pd.DataFrame], category: str):
        """Save raw extracted data to files."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        
        for source_name, df in data_dict.items():
            if not df.empty:
                filename = f"{category}_{source_name}_{timestamp}.csv"
                filepath = self.data_dir / "raw" / filename
                df.to_csv(filepath)
                logger.info(f"💾 Saved {source_name}: {len(df)} records to {filename}")
    
    def extract_all_data(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Extract all PSG data comprehensively.
        
        Returns
        -------
        Dict[str, Dict[str, pd.DataFrame]]
            Complete dataset organized by category
        """
        logger.info("🚀 Starting comprehensive PSG data extraction...")
        
        all_data = {
            'team_stats': self.extract_team_season_stats(),
            'player_stats': self.extract_player_season_stats(),
            'match_data': self.extract_match_data()
        }
        
        # Generate summary report
        self._generate_extraction_report(all_data)
        
        logger.info("🎉 Comprehensive PSG data extraction completed!")
        return all_data
    
    def _generate_extraction_report(self, all_data: Dict):
        """Generate extraction summary report."""
        report = {
            'extraction_timestamp': datetime.now(timezone.utc).isoformat(),
            'seasons': self.seasons,
            'leagues': self.leagues,
            'summary': {}
        }
        
        for category, data_dict in all_data.items():
            category_summary = {}
            for source, df in data_dict.items():
                category_summary[source] = {
                    'records': len(df),
                    'columns': list(df.columns),
                    'seasons_covered': list(df.index.get_level_values('season').unique()) if 'season' in df.index.names else 'N/A'
                }
            report['summary'][category] = category_summary
        
        # Save report
        report_path = self.data_dir / "processed" / f"extraction_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 Extraction report saved to {report_path}")


def main():
    """Main execution function."""
    logger.info("🔥 PSG Data Extraction Starting...")
    
    # Initialize extractor
    extractor = PSGDataExtractor(
        seasons=["2023-24", "2024-25"],
        leagues=["FRA-Ligue 1"]
    )
    
    # Extract all data
    all_data = extractor.extract_all_data()
    
    logger.info("✅ PSG Data Extraction Completed Successfully!")
    return all_data


if __name__ == "__main__":
    main()