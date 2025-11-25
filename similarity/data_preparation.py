"""
Data Preparation Module

Extrae datos desde PostgreSQL, convierte métricas JSON a DataFrame numérico,
maneja valores faltantes y detecta outliers por posición.

Basado en:
    - Little & Rubin (2002): Statistical Analysis with Missing Data
    - Imputation específica por posición (crítico en análisis fútbol)
    - Isolation Forest para detección outliers multivariante

Clase principal:
    DataPreparator: Orquesta extracción, limpieza y preparación datos
"""

import sys
import os
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy import text
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import DatabaseManager, get_db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataPreparator:
    """
    Prepara datos desde BD PostgreSQL para análisis similitud.

    Workflow:
        1. Conecta a BD usando DatabaseManager existente
        2. Ejecuta query SQL con filtros especificados
        3. Extrae métricas JSON (fbref_metrics, understat_metrics)
        4. Convierte a DataFrame numérico con todas las features
        5. Maneja valores faltantes con estrategia por posición
        6. Detecta outliers multivariantes

    Attributes:
        db_manager: Conexión a PostgreSQL
        table_type: Tipo tabla ('domestic', 'european', 'extras')
        df_raw: DataFrame crudo desde BD
        df_clean: DataFrame limpio post-procesamiento
    """

    def __init__(self, db_manager: Optional[DatabaseManager] = None,
                 table_type: str = 'domestic'):
        """
        Inicializa preparador de datos.

        Parameters:
            db_manager: Instancia DatabaseManager. Si None, crea nueva conexión.
            table_type: Tipo de tabla a consultar.
                       'domestic' -> players_domestic (Big 5)
                       'european' -> players_european (Champions League)
                       'extras' -> players_extras (Portugal, etc.)
        """
        self.db_manager = db_manager if db_manager else get_db_manager()
        self.table_type = table_type
        self.df_raw = None
        self.df_clean = None
        self._position_medians = {}

        logger.info(f"DataPreparator initialized for table type: {table_type}")

    def load_players(self,
                    leagues: List[str],
                    season: str,
                    position_filter: Optional[str] = None,
                    min_minutes: int = 0,
                    max_age: Optional[int] = None) -> pd.DataFrame:
        """
        Carga jugadores desde BD con filtros especificados.

        Parameters:
            leagues: Lista ligas a incluir (ej: ['ESP-La Liga', 'ENG-Premier League'])
            season: Temporada formato 'YXYY' (ej: '2526' para 2025/26)
            position_filter: Filtro posición inicial ('GK', 'DF', 'MF', 'FW'). None = todas.
            min_minutes: Minutos mínimos jugados para inclusión
            max_age: Edad máxima (opcional)

        Returns:
            DataFrame con jugadores y métricas JSON sin expandir

        Raises:
            ValueError: Si table_type inválido o query falla
        """
        # Validar table_type
        valid_types = ['domestic', 'european', 'extras']
        if self.table_type not in valid_types:
            raise ValueError(f"table_type must be one of {valid_types}")

        # Determinar columna liga/competición según tabla
        league_col = 'league' if self.table_type == 'domestic' else 'competition'

        # Construir query SQL
        leagues_str = "', '".join(leagues)

        query_parts = [
            f"SELECT unique_player_id, player_name, team, {league_col} as league,",
            f"       season, position, nationality, age,",
            f"       fbref_metrics"
        ]

        # Agregar understat_metrics solo para domestic
        if self.table_type == 'domestic':
            query_parts.append(", understat_metrics")

        query_parts.extend([
            f"FROM footballdecoded.players_{self.table_type}",
            f"WHERE {league_col} IN ('{leagues_str}')",
            f"AND season = '{season}'"
        ])

        # Aplicar filtros opcionales
        if position_filter:
            query_parts.append(f"AND position LIKE '{position_filter}%'")

        if max_age:
            query_parts.append(f"AND (age IS NULL OR CAST(age AS INTEGER) <= {max_age})")

        query_parts.append(f"ORDER BY {league_col}, team, player_name")

        query_sql = "\n".join(query_parts)

        logger.info(f"Executing query for {len(leagues)} leagues, season {season}")
        logger.debug(f"Query: {query_sql}")

        # Ejecutar query
        try:
            self.df_raw = pd.read_sql(text(query_sql), self.db_manager.engine)
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise ValueError(f"Database query failed: {e}")

        # Filtrar por minutos (requiere expandir fbref_metrics temporalmente)
        if min_minutes > 0:
            mask = self.df_raw['fbref_metrics'].apply(
                lambda x: x.get('minutes_played', 0) if isinstance(x, dict) else 0
            ) >= min_minutes
            self.df_raw = self.df_raw[mask].copy()

        logger.info(f"Loaded {len(self.df_raw)} players matching criteria")

        return self.df_raw

    def set_raw_data(self, df: pd.DataFrame) -> None:
        """
        Establece df_raw manualmente con un DataFrame concatenado.

        Util cuando se cargan multiples temporadas por separado y se
        necesita combinarlas antes de procesar.

        Parameters:
            df: DataFrame concatenado con estructura compatible

        Raises:
            ValueError: Si el DataFrame no tiene columnas requeridas
        """
        required_cols = ['unique_player_id', 'player_name', 'fbref_metrics']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            raise ValueError(f"DataFrame must contain columns: {missing_cols}")

        self.df_raw = df.copy()
        logger.info(f"Raw data manually set with {len(self.df_raw)} players")

    def extract_all_metrics(self) -> pd.DataFrame:
        """
        Extrae todas las métricas JSON y convierte a DataFrame numérico.

        Proceso:
            1. Extrae fbref_metrics (dict) a columnas individuales
            2. Extrae understat_metrics si disponible (solo domestic)
            3. Convierte valores string a float cuando posible
            4. Mantiene columnas con >= 5 valores válidos
            5. Genera columnas per90 para métricas absolutas

        Returns:
            DataFrame con todas las features numéricas expandidas

        Notes:
            Similar a extract_metrics en notebooks existentes pero optimizado
            para pipeline producción.
        """
        if self.df_raw is None:
            raise ValueError("Must call load_players() first")

        logger.info("Extracting metrics from JSON columns...")

        # Extraer FBref metrics
        fbref_cols = self._extract_metric_dict(self.df_raw, 'fbref_metrics')
        logger.info(f"Extracted {len(fbref_cols.columns)} FBref metrics")

        # Extraer Understat metrics si disponible
        if self.table_type == 'domestic':
            understat_cols = self._extract_metric_dict(self.df_raw, 'understat_metrics')
            logger.info(f"Extracted {len(understat_cols.columns)} Understat metrics")
        else:
            understat_cols = pd.DataFrame(index=self.df_raw.index)

        # Calcular métricas per90
        fbref_per90, understat_per90 = self._calculate_per90_metrics(
            fbref_cols, understat_cols
        )
        logger.info(f"Calculated {len(fbref_per90.columns)} FBref per90 metrics")

        # Combinar todo
        base_cols = ['unique_player_id', 'player_name', 'team', 'league',
                     'season', 'position', 'age']

        # Agregar minutes_played si no está en fbref_cols
        if 'minutes_played' not in fbref_cols.columns and 'minutes_played' in self.df_raw.columns:
            base_cols.append('minutes_played')

        self.df_clean = pd.concat([
            self.df_raw[base_cols],
            fbref_cols,
            understat_cols,
            fbref_per90,
            understat_per90
        ], axis=1)

        # Convertir age a numérico para evitar errores de tipo
        if 'age' in self.df_clean.columns:
            self.df_clean['age'] = pd.to_numeric(self.df_clean['age'], errors='coerce')
            logger.debug(f"Converted 'age' column to numeric type")

        logger.info(f"Final DataFrame: {self.df_clean.shape[0]} players, "
                   f"{self.df_clean.shape[1]} total columns")

        return self.df_clean

    def _extract_metric_dict(self, df: pd.DataFrame, col_name: str) -> pd.DataFrame:
        """
        Extrae métricas de columna JSON/dict a DataFrame.

        Implementa conversión robusta string->float y filtrado por valores válidos.
        """
        # Obtener todas las keys únicas
        all_keys = set()
        for _, row in df.iterrows():
            if isinstance(row[col_name], dict):
                all_keys.update(row[col_name].keys())

        # Construir dict de columnas en lugar de asignar una por una
        columns_dict = {}
        for key in all_keys:
            values = []
            for _, row in df.iterrows():
                if isinstance(row[col_name], dict) and key in row[col_name]:
                    raw_value = row[col_name][key]
                    converted = self._convert_to_float(raw_value)
                    values.append(converted)
                else:
                    values.append(np.nan)

            # Solo incluir si >= 5 valores válidos
            valid_count = pd.Series(values).notna().sum()
            if valid_count >= 5:
                columns_dict[key] = values

        # Crear DataFrame de una sola vez (evita fragmentación)
        result = pd.DataFrame(columns_dict, index=df.index)

        return result

    @staticmethod
    def _convert_to_float(value: Any) -> float:
        """
        Convierte valor a float de manera robusta.

        Maneja: int, float, string numérico, None, string vacío
        """
        if isinstance(value, (int, float)):
            return float(value)

        if value is None or pd.isna(value):
            return np.nan

        if isinstance(value, str):
            value_clean = value.strip()
            if value_clean == '' or value_clean.lower() in ['nan', 'none', 'null', '-']:
                return np.nan

            try:
                return float(value_clean)
            except (ValueError, TypeError):
                return np.nan

        return np.nan

    def _calculate_per90_metrics(self,
                                 fbref_df: pd.DataFrame,
                                 understat_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Calcula métricas per90 para todas las métricas absolutas.

        Excluye ratios/porcentajes y métricas ya normalizadas.
        """
        # Métricas a excluir de per90 (ya son ratios/porcentajes)
        exclude_per90 = {
            'pass_completion_pct', 'shots_on_target_pct', 'Take-Ons_Succ%',
            'Take-Ons_Tkld%', 'Aerial Duels_Won%', 'Challenges_Tkl%', 'Save%',
            'Launched_Cmp%', 'Crosses_Stp%', 'shots_per_90', 'GA90', 'GCA_GCA90',
            'SCA_SCA90', 'Team Success_+/-90', 'SoT/90', 'npxG/Sh', 'xG+xAG',
            'non_penalty_xG_plus_xAG', 'avg_shot_distance', 'minutes_per_match',
            'Passes_AvgLen', 'Goal Kicks_AvgLen', 'Starts_Mn/Start', 'Subs_Mn/Sub',
            'Min%', 'matches_played', 'matches_started', 'minutes_played',
            'wins', 'draws', 'losses', 'understat_buildup_involvement_pct',
            'understat_player_id', 'understat_team_id', 'CS%', 'Passes_Launch%',
            'Goal Kicks_Launch%', 'Penalty Kicks_Save%'
        }

        # Obtener minutes_played de df_raw o fbref_df
        if 'minutes_played' in fbref_df.columns:
            minutes = fbref_df['minutes_played']
        elif 'minutes_played' in self.df_raw.columns:
            minutes = self.df_raw['minutes_played']
        else:
            logger.warning("minutes_played not found, skipping per90 calculations")
            return pd.DataFrame(index=fbref_df.index), pd.DataFrame(index=understat_df.index)

        # Calcular FBref per90
        fbref_per90 = fbref_df.loc[:, ~fbref_df.columns.isin(exclude_per90)]
        fbref_per90 = (fbref_per90.div(minutes, axis=0) * 90).round(3)
        fbref_per90.columns = [f'{col}_per90' for col in fbref_per90.columns]

        # Calcular Understat per90
        understat_per90 = understat_df.loc[:, ~understat_df.columns.isin(exclude_per90)]
        understat_per90 = (understat_per90.div(minutes, axis=0) * 90).round(3)
        understat_per90.columns = [f'{col}_per90' for col in understat_per90.columns]

        return fbref_per90, understat_per90

    def handle_missing_values(self, strategy: str = 'median_by_position',
                             max_missing_pct: float = 0.4) -> pd.DataFrame:
        """
        Maneja valores faltantes con estrategias específicas por posición.

        Parameters:
            strategy: Estrategia imputation
                     'median_by_position' -> Median por posición (default, robusto)
                     'mean_by_position' -> Media por posición
                     'drop' -> Eliminar columnas con muchos missing
            max_missing_pct: Eliminar columnas con > este % de missing (0-1)

        Returns:
            DataFrame con valores faltantes imputados

        Notes:
            Median preferido vs mean por robustez a outliers (Little & Rubin, 2002)
        """
        if self.df_clean is None:
            raise ValueError("Must call extract_all_metrics() first")

        logger.info(f"Handling missing values with strategy: {strategy}")

        # Identificar columnas numéricas (excluir metadata)
        metadata_cols = ['unique_player_id', 'player_name', 'team', 'league',
                        'season', 'position']
        numeric_cols = [col for col in self.df_clean.columns
                       if col not in metadata_cols]

        # Diagnostico inicial
        logger.info(f"Input shape: {self.df_clean.shape} ({len(self.df_clean)} rows, {len(numeric_cols)} numeric cols)")

        # Eliminar columnas con demasiados missing
        missing_pct = self.df_clean[numeric_cols].isna().sum() / len(self.df_clean)
        cols_to_keep = missing_pct[missing_pct <= max_missing_pct].index.tolist()
        cols_removed = len(numeric_cols) - len(cols_to_keep)

        if cols_removed > 0:
            logger.warning(f"Removed {cols_removed} columns with >{max_missing_pct*100}% missing")
            logger.info(f"Numeric columns remaining: {len(cols_to_keep)}")

        df_result = self.df_clean[metadata_cols + cols_to_keep].copy()
        logger.info(f"Output shape: {df_result.shape}")

        # Aplicar estrategia imputation
        if strategy in ['median_by_position', 'mean_by_position']:
            # Calcular estadístico por posición (primera letra: G, D, M, F)
            df_result['position_group'] = df_result['position'].str[0]

            for pos_group in df_result['position_group'].unique():
                mask = df_result['position_group'] == pos_group

                if strategy == 'median_by_position':
                    fill_values = df_result.loc[mask, cols_to_keep].median()
                else:  # mean
                    fill_values = df_result.loc[mask, cols_to_keep].mean()

                # Guardar medians por posición para futuro uso
                self._position_medians[pos_group] = fill_values

                # Imputar
                df_result.loc[mask, cols_to_keep] = df_result.loc[
                    mask, cols_to_keep
                ].fillna(fill_values)

            df_result = df_result.drop('position_group', axis=1)

            logger.info(f"Imputed missing values using {strategy}")

        elif strategy == 'drop':
            # Ya eliminamos columnas arriba
            pass

        self.df_clean = df_result

        # Report final missing
        final_missing = self.df_clean[cols_to_keep].isna().sum().sum()
        logger.info(f"Final missing values: {final_missing}")

        return self.df_clean

    def detect_outliers(self, method: str = 'isolation_forest',
                       contamination: float = 0.05) -> pd.DataFrame:
        """
        Detecta outliers multivariantes.

        Parameters:
            method: Método detección
                   'isolation_forest' -> Isolation Forest (default, eficiente)
                   'lof' -> Local Outlier Factor
                   'zscore' -> Z-score univariante (simple)
            contamination: Proporción esperada outliers (0-0.5)

        Returns:
            DataFrame con columna 'is_outlier' añadida (boolean)

        Notes:
            Isolation Forest preferido por eficiencia en high-dimensional data
            (Liu et al., 2008: Isolation Forest)
        """
        if self.df_clean is None:
            raise ValueError("Must call handle_missing_values() first")

        logger.info(f"Detecting outliers using {method}")

        # Columnas numéricas
        metadata_cols = ['unique_player_id', 'player_name', 'team', 'league',
                        'season', 'position']
        numeric_cols = [col for col in self.df_clean.columns
                       if col not in metadata_cols]

        # Validacion critica
        if len(self.df_clean) == 0:
            raise ValueError("Cannot detect outliers: DataFrame is empty (0 rows)")

        if len(numeric_cols) == 0:
            raise ValueError("Cannot detect outliers: No numeric columns found")

        logger.info(f"Processing {len(self.df_clean)} players with {len(numeric_cols)} numeric features")

        X = self.df_clean[numeric_cols].values

        if method == 'isolation_forest':
            from sklearn.ensemble import IsolationForest
            clf = IsolationForest(contamination=contamination, random_state=42)
            outlier_labels = clf.fit_predict(X)
            # IsolationForest retorna -1 para outliers, 1 para inliers
            is_outlier = outlier_labels == -1

        elif method == 'lof':
            from sklearn.neighbors import LocalOutlierFactor
            clf = LocalOutlierFactor(contamination=contamination)
            outlier_labels = clf.fit_predict(X)
            is_outlier = outlier_labels == -1

        elif method == 'zscore':
            # Z-score univariante simple
            z_scores = np.abs((X - np.nanmean(X, axis=0)) / np.nanstd(X, axis=0))
            is_outlier = (z_scores > 3).any(axis=1)

        else:
            raise ValueError(f"Unknown outlier detection method: {method}")

        self.df_clean['is_outlier'] = is_outlier

        n_outliers = is_outlier.sum()
        logger.info(f"Detected {n_outliers} outliers ({n_outliers/len(self.df_clean)*100:.1f}%)")

        return self.df_clean

    def get_feature_matrix(self, exclude_outliers: bool = True,
                          exclude_metadata: bool = True) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Retorna matriz de features limpia lista para UMAP/GMM.

        Parameters:
            exclude_outliers: Si True, excluye jugadores marcados como outliers
            exclude_metadata: Si True, excluye columnas metadata (nombres, equipos, etc.)

        Returns:
            Tuple (DataFrame completo, array features numéricas)
        """
        if self.df_clean is None:
            raise ValueError("Must complete data preparation pipeline first")

        df = self.df_clean.copy()

        if exclude_outliers and 'is_outlier' in df.columns:
            df = df[~df['is_outlier']].copy()
            logger.info(f"Excluded outliers, {len(df)} players remaining")

        metadata_cols = ['unique_player_id', 'player_name', 'team', 'league',
                        'season', 'position', 'is_outlier']

        if exclude_metadata:
            feature_cols = [col for col in df.columns if col not in metadata_cols]
            X = df[feature_cols].values
        else:
            X = df.values

        logger.info(f"Feature matrix shape: {X.shape}")

        return df, X

    def close_connection(self):
        """Cierra conexión a BD."""
        if self.db_manager:
            self.db_manager.close()
            logger.info("Database connection closed")
