#!/usr/bin/env python3
"""
PSG Data Unifier
================

Procesador que convierte todos los CSVs raw en datasets limpios y estandarizados
para visualizaciones potentes.

Genera:
- psg_team_stats_unified.csv: Todas las estadísticas de equipo
- psg_player_stats_unified.csv: Todas las estadísticas de jugadores  
- psg_match_data_unified.csv: Todos los datos partido a partido
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Union
import warnings
warnings.filterwarnings('ignore')

class PSGDataUnifier:
    """Unificador de datos del PSG para visualizaciones."""
    
    def __init__(self, raw_data_dir: Path = None):
        """Initialize data unifier."""
        self.raw_dir = raw_data_dir or Path("data/raw")
        self.output_dir = Path("data/processed")
        self.output_dir.mkdir(exist_ok=True)
        
        print("📂 PSG Data Unifier inicializado")
        print(f"📁 Directorio raw: {self.raw_dir}")
        print(f"💾 Directorio output: {self.output_dir}")
    
    def convert_season_format(self, season):
        """Convert season to standard format."""
        if pd.isna(season):
            return None
        
        season_str = str(season).strip()
        
        # Handle numeric format (2324 -> 2023-24)
        if season_str.isdigit() and len(season_str) == 4:
            year1 = "20" + season_str[:2]
            year2 = season_str[2:]
            return f"{year1}-{year2}"
        
        # Already in correct format
        if '-' in season_str and len(season_str) == 7:
            return season_str
        
        return season_str
    
    def load_csv_robust(self, file_path: Path) -> pd.DataFrame:
        """Load CSV with robust handling of different structures."""
        try:
            # Try standard loading first
            df = pd.read_csv(file_path)
            
            # Check if it has MultiIndex columns
            if df.columns.str.contains('Unnamed').any() or df.iloc[0].isna().all():
                # Try with MultiIndex
                df = pd.read_csv(file_path, header=[0, 1])
                # Flatten MultiIndex columns
                df.columns = [f"{col[0]}_{col[1]}" if col[1] and col[1] != col[0] else col[0] 
                             for col in df.columns]
            
            # Clean column names
            df.columns = [str(col).strip().replace(' ', '_').lower() for col in df.columns]
            
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            return df
            
        except Exception as e:
            print(f"❌ Error loading {file_path.name}: {e}")
            return pd.DataFrame()
    
    def unify_team_stats(self) -> pd.DataFrame:
        """Unify all team statistics into single dataset."""
        print("\n🏆 UNIFICANDO ESTADÍSTICAS DE EQUIPO")
        print("-" * 40)
        
        team_files = list(self.raw_dir.glob("team_season_stats_*.csv"))
        print(f"📊 Encontrados {len(team_files)} archivos de equipo")
        
        unified_data = []
        
        for file in team_files:
            print(f"🔄 Procesando: {file.name}")
            
            df = self.load_csv_robust(file)
            if df.empty:
                continue
            
            # Extract source and category from filename
            source = self._extract_source_info(file.name)
            
            # Process each row
            for idx, row in df.iterrows():
                # Extract season information
                season = self._find_season_in_row(row, df.index.names if hasattr(df, 'index') else None)
                
                if not season:
                    continue
                
                # Create base record
                record = {
                    'source': source['source'],
                    'category': source['category'],
                    'season': self.convert_season_format(season),
                    'team': 'PSG'
                }
                
                # Add all numeric columns with standardized names
                for col in df.columns:
                    if col.lower() in ['unnamed', 'index'] or col.startswith('unnamed'):
                        continue
                    
                    value = row[col]
                    if pd.notna(value) and value != '':
                        # Try to convert to numeric
                        try:
                            numeric_value = float(value)
                            if not np.isnan(numeric_value):
                                standardized_col = self._standardize_column_name(col)
                                record[standardized_col] = numeric_value
                        except (ValueError, TypeError):
                            # Keep as string if not numeric
                            if isinstance(value, str) and len(value) < 50:
                                record[col] = value
                
                if len(record) > 4:  # Only add if we have actual data
                    unified_data.append(record)
        
        if unified_data:
            team_df = pd.DataFrame(unified_data)
            
            # Remove duplicates and sort
            team_df = team_df.drop_duplicates()
            team_df = team_df.sort_values(['season', 'source', 'category'])
            
            # Save unified team stats
            output_path = self.output_dir / "psg_team_stats_unified.csv"
            team_df.to_csv(output_path, index=False)
            
            print(f"✅ Equipo: {len(team_df)} registros → {output_path}")
            print(f"📊 Temporadas: {sorted(team_df['season'].unique())}")
            print(f"📈 Fuentes: {sorted(team_df['source'].unique())}")
            print(f"📋 Categorías: {sorted(team_df['category'].unique())}")
            
            return team_df
        else:
            print("❌ No se pudieron procesar datos de equipo")
            return pd.DataFrame()
    
    def unify_player_stats(self) -> pd.DataFrame:
        """Unify all player statistics into single dataset."""
        print("\n👥 UNIFICANDO ESTADÍSTICAS DE JUGADORES")
        print("-" * 40)
        
        player_files = list(self.raw_dir.glob("player_season_stats_*.csv"))
        print(f"📊 Encontrados {len(player_files)} archivos de jugadores")
        
        unified_data = []
        
        for file in player_files:
            print(f"🔄 Procesando: {file.name}")
            
            df = self.load_csv_robust(file)
            if df.empty:
                continue
            
            # Extract source and category
            source = self._extract_source_info(file.name)
            
            # Look for player name column
            player_col = self._find_player_column(df.columns)
            
            for idx, row in df.iterrows():
                # Extract basic info
                season = self._find_season_in_row(row, df.index.names if hasattr(df, 'index') else None)
                player_name = row.get(player_col, '') if player_col else ''
                
                if not season or not player_name:
                    continue
                
                # Create base record
                record = {
                    'source': source['source'],
                    'category': source['category'],
                    'season': self.convert_season_format(season),
                    'team': 'PSG',
                    'player': str(player_name).strip()
                }
                
                # Add all numeric columns
                for col in df.columns:
                    if col.lower() in ['unnamed', 'index', player_col] or col.startswith('unnamed'):
                        continue
                    
                    value = row[col]
                    if pd.notna(value) and value != '':
                        try:
                            numeric_value = float(value)
                            if not np.isnan(numeric_value):
                                standardized_col = self._standardize_column_name(col)
                                record[standardized_col] = numeric_value
                        except (ValueError, TypeError):
                            # Keep non-numeric data if useful
                            if isinstance(value, str) and len(value) < 30:
                                record[col] = value
                
                if len(record) > 5:  # Only add if we have actual data
                    unified_data.append(record)
        
        if unified_data:
            player_df = pd.DataFrame(unified_data)
            
            # Clean player names
            player_df['player'] = player_df['player'].str.replace(r'[^\w\s-]', '', regex=True)
            player_df = player_df[player_df['player'].str.len() > 1]
            
            # Remove duplicates and sort
            player_df = player_df.drop_duplicates()
            player_df = player_df.sort_values(['season', 'player', 'source', 'category'])
            
            # Save unified player stats
            output_path = self.output_dir / "psg_player_stats_unified.csv"
            player_df.to_csv(output_path, index=False)
            
            print(f"✅ Jugadores: {len(player_df)} registros → {output_path}")
            print(f"📊 Temporadas: {sorted(player_df['season'].unique())}")
            print(f"👤 Jugadores únicos: {player_df['player'].nunique()}")
            print(f"📈 Fuentes: {sorted(player_df['source'].unique())}")
            
            return player_df
        else:
            print("❌ No se pudieron procesar datos de jugadores")
            return pd.DataFrame()
    
    def unify_match_data(self) -> pd.DataFrame:
        """Unify all match data into single dataset."""
        print("\n⚽ UNIFICANDO DATOS DE PARTIDOS")
        print("-" * 40)
        
        match_files = list(self.raw_dir.glob("match_data_*.csv"))
        print(f"📊 Encontrados {len(match_files)} archivos de partidos")
        
        # Start with schedule as base
        schedule_file = None
        for file in match_files:
            if 'schedule' in file.name:
                schedule_file = file
                break
        
        if not schedule_file:
            print("❌ No se encontró archivo de calendario")
            return pd.DataFrame()
        
        # Load schedule as base
        base_df = pd.read_csv(schedule_file)
        print(f"📅 Base: {len(base_df)} partidos del calendario")
        
        # Standardize season format
        base_df['season'] = base_df['season'].apply(self.convert_season_format)
        
        # Process other match files
        for file in match_files:
            if 'schedule' in file.name:
                continue
                
            print(f"🔄 Agregando: {file.name}")
            
            df = self.load_csv_robust(file)
            if df.empty:
                continue
            
            # Standardize season
            if 'season' in df.columns:
                df['season'] = df['season'].apply(self.convert_season_format)
            
            # Try to merge with base data
            merge_cols = ['season', 'team', 'game'] if all(col in df.columns for col in ['season', 'team', 'game']) else None
            
            if merge_cols:
                # Add suffix to avoid column conflicts
                source_suffix = f"_{self._extract_source_info(file.name)['category']}"
                df_for_merge = df.add_suffix(source_suffix)
                
                # Restore merge columns
                for col in merge_cols:
                    df_for_merge[col] = df[col]
                
                base_df = base_df.merge(df_for_merge, on=merge_cols, how='left')
                print(f"   ✅ Merged on: {merge_cols}")
            else:
                print(f"   ⚠️ No se pudo hacer merge para {file.name}")
        
        # Clean and standardize column names
        base_df.columns = [self._standardize_column_name(col) for col in base_df.columns]
        
        # Save unified match data
        output_path = self.output_dir / "psg_match_data_unified.csv"
        base_df.to_csv(output_path, index=False)
        
        print(f"✅ Partidos: {len(base_df)} registros → {output_path}")
        print(f"📊 Temporadas: {sorted(base_df['season'].unique())}")
        print(f"📈 Columnas totales: {len(base_df.columns)}")
        
        return base_df
    
    def _extract_source_info(self, filename: str) -> Dict[str, str]:
        """Extract source and category from filename."""
        # Remove timestamp and extension
        name = filename.replace('.csv', '').split('_202')[0]
        
        # Determine source
        if 'fbref' in name:
            source = 'fbref'
        elif 'understat' in name:
            source = 'understat'
        elif 'fotmob' in name:
            source = 'fotmob'
        else:
            source = 'unknown'
        
        # Determine category
        if 'standard' in name:
            category = 'standard'
        elif 'shooting' in name:
            category = 'shooting'
        elif 'passing' in name:
            category = 'passing'
        elif 'defense' in name:
            category = 'defense'
        elif 'possession' in name:
            category = 'possession'
        elif 'keeper' in name:
            category = 'goalkeeper'
        elif 'misc' in name:
            category = 'miscellaneous'
        elif 'schedule' in name:
            category = 'schedule'
        else:
            category = 'other'
        
        return {'source': source, 'category': category}
    
    def _find_season_in_row(self, row, index_names=None):
        """Find season information in a row."""
        # Check common season column names
        season_cols = ['season', 'Season', 'year', 'Year']
        
        for col in season_cols:
            if col in row and pd.notna(row[col]):
                return row[col]
        
        # Check index if available
        if index_names and 'season' in index_names:
            return row.name if hasattr(row, 'name') else None
        
        return None
    
    def _find_player_column(self, columns) -> str:
        """Find the column that contains player names."""
        player_indicators = ['player', 'Player', 'nombre', 'name']
        
        for col in columns:
            col_lower = str(col).lower()
            if any(indicator.lower() in col_lower for indicator in player_indicators):
                return col
        
        return None
    
    def _standardize_column_name(self, col_name: str) -> str:
        """Standardize column names for consistency."""
        col = str(col_name).lower().strip()
        
        # Common replacements
        replacements = {
            'gf': 'goals_for',
            'ga': 'goals_against',
            'w': 'wins',
            'd': 'draws',
            'l': 'losses',
            'pts': 'points',
            'mp': 'matches_played',
            'sh': 'shots',
            'sot': 'shots_on_target',
            'poss': 'possession',
            'tkl': 'tackles',
            'int': 'interceptions',
            'ast': 'assists',
            'cmp': 'passes_completed',
            'att': 'passes_attempted',
            'pct': 'percentage'
        }
        
        # Replace common abbreviations
        for abbr, full in replacements.items():
            if col == abbr or col.endswith(f'_{abbr}'):
                col = col.replace(abbr, full)
        
        # Clean up
        col = col.replace(' ', '_').replace('-', '_').replace('.', '_')
        col = '_'.join(word for word in col.split('_') if word)  # Remove empty parts
        
        return col
    
    def generate_data_summary(self, team_df, player_df, match_df) -> Dict:
        """Generate summary of unified datasets."""
        summary = {
            'datasets': {
                'team_stats': {
                    'records': len(team_df),
                    'columns': len(team_df.columns),
                    'seasons': team_df['season'].unique().tolist() if not team_df.empty else [],
                    'sources': team_df['source'].unique().tolist() if not team_df.empty else [],
                    'categories': team_df['category'].unique().tolist() if not team_df.empty else []
                },
                'player_stats': {
                    'records': len(player_df),
                    'columns': len(player_df.columns),
                    'seasons': player_df['season'].unique().tolist() if not player_df.empty else [],
                    'unique_players': player_df['player'].nunique() if not player_df.empty else 0,
                    'sources': player_df['source'].unique().tolist() if not player_df.empty else []
                },
                'match_data': {
                    'records': len(match_df),
                    'columns': len(match_df.columns),
                    'seasons': match_df['season'].unique().tolist() if not match_df.empty else []
                }
            },
            'files_generated': [
                'psg_team_stats_unified.csv',
                'psg_player_stats_unified.csv', 
                'psg_match_data_unified.csv'
            ]
        }
        
        return summary
    
    def run_unification(self) -> Dict:
        """Run complete data unification process."""
        print("🚀 PSG DATA UNIFICATION")
        print("=" * 50)
        
        # Unify all datasets
        team_df = self.unify_team_stats()
        player_df = self.unify_player_stats()
        match_df = self.unify_match_data()
        
        # Generate summary
        summary = self.generate_data_summary(team_df, player_df, match_df)
        
        # Save summary
        summary_path = self.output_dir / "unification_summary.json"
        import json
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n🎉 UNIFICACIÓN COMPLETADA")
        print(f"📁 Archivos generados en: {self.output_dir}")
        print(f"📋 Resumen guardado en: {summary_path}")
        
        return summary


def main():
    """Main execution function."""
    unifier = PSGDataUnifier()
    summary = unifier.run_unification()
    
    print("\n📊 RESUMEN FINAL:")
    for dataset, info in summary['datasets'].items():
        print(f"  {dataset}: {info['records']} registros, {info['columns']} columnas")
    
    return summary


if __name__ == "__main__":
    main()