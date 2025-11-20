"""
Feature Engineering Module

Selecciona features relevantes por posición, normaliza datos y elimina
redundancias para optimizar reducción dimensional posterior.

Basado en:
    - Guyon & Elisseeff (2003): An introduction to variable and feature selection
    - Normalización crítica para métricas distancia (UMAP usa euclidiana)
    - Feature selection específica por posición de fútbol

Clase principal:
    FeatureEngineer: Selección, normalización y preparación features
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.feature_selection import VarianceThreshold
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Ingeniería de features para análisis similitud jugadores.

    Workflow:
        1. Selecciona features relevantes por posición
        2. Excluye métricas portero para jugadores campo
        3. Elimina features alta correlación (redundantes)
        4. Normaliza por posición usando StandardScaler
        5. Calcula feature importance scores

    Attributes:
        position_type: Posición filtro ('GK', 'DF', 'MF', 'FW', 'ALL')
        scaler: Instancia sklearn scaler
        selected_features: Lista features post-selección
        feature_importance: Dict con importance scores
    """

    # Features relevantes por posición (basado en análisis fútbol)
    # Prioriza métricas per90 normalizadas y ratios
    POSITION_FEATURES = {
        'GK': [
            'Save%', 'PSxG+/-', 'CS%', 'GA90', 'pass_completion_pct',
            'Launched_Cmp%', 'Goal Kicks_Launch%', 'Sweeper_#OPA/90',
            'Sweeper_AvgDist', 'SoT/90', 'Passes_Launch%', 'Saves_per90',
            'SoTA_per90', 'PSxG_per90', 'Goal Kicks_Att_per90'
        ],
        'DF': [
            'pass_completion_pct', 'Challenges_Tkl%', 'Aerial Duels_Won_per90',
            'Aerial Duels_Won%', 'passes_final_third_per90', 'clearances_per90',
            'progressive_passes_per90', 'Tkl+Int_per90', 'interceptions_per90',
            'Blocks_Sh_per90', 'Tackles_TklW_per90', 'Blocks_Blocks_per90',
            'Carries_PrgC_per90', 'Carries_PrgDist_per90', 'errors_per90',
            'expected_assists_per90', 'passes_penalty_area_per90',
            'Touches_Att 3rd_per90', 'progressive_pass_distance_per90'
        ],
        'MF': [
            'progressive_passes_per90', 'Carries_PrgC_per90', 'SCA_SCA90',
            'expected_assists_per90', 'passes_penalty_area_per90',
            'Take-Ons_Succ_per90', 'Tkl+Int_per90', 'interceptions_per90',
            'Fld_per90', 'pass_completion_pct', 'key_passes_per90',
            'passes_final_third_per90', 'Touches_Att 3rd_per90',
            'Carries_1/3_per90', 'Progression_PrgP_per90',
            'expected_goals_per90', 'shots_per_90', 'GCA_GCA90',
            'assists_per90', 'goals_per90', 'Challenges_Tkl%'
        ],
        'FW': [
            'expected_goals_per90', 'goals_per90', 'shots_per_90',
            'Touches_Att Pen_per90', 'expected_assists_per90',
            'Take-Ons_Succ_per90', 'npxG/Sh', 'G-xG_per90',
            'Fld_per90', 'SCA_SCA90', 'key_passes_per90',
            'Carries_PrgC_per90', 'Crs_per90', 'shots_on_target_per90',
            'non_penalty_expected_goals_per90', 'assists_per90',
            'passes_penalty_area_per90', 'Aerial Duels_Won_per90',
            'Challenges_Tkl%', 'GCA_GCA90'
        ]
    }

    # Métricas portero a excluir para jugadores campo
    GK_METRICS = [
        'Save%', 'PSxG+/-', 'PSxG', 'PSxG/SoT', 'CS%', 'GA90', 'SoT/90',
        'SoTA', 'Saves', 'Goal Kicks_Att', 'Goal Kicks_AvgLen',
        'Goal Kicks_Launch%', 'Sweeper_#OPA', 'Sweeper_#OPA/90',
        'Sweeper_AvgDist', 'Penalty Kicks_PKA', 'Penalty Kicks_PKatt',
        'Penalty Kicks_PKm', 'Penalty Kicks_PKsv', 'Penalty Kicks_Save%',
        'Goals_GA', 'goals_against'
    ]

    def __init__(self, position_type: str = 'ALL'):
        """
        Inicializa feature engineer.

        Parameters:
            position_type: Tipo posición para feature selection
                          'GK', 'DF', 'MF', 'FW' -> Filtro específico
                          'ALL' -> Usa todas las features disponibles
        """
        valid_positions = ['GK', 'DF', 'MF', 'FW', 'ALL']
        if position_type not in valid_positions:
            raise ValueError(f"position_type must be one of {valid_positions}")

        self.position_type = position_type
        self.scaler = None
        self.selected_features = None
        self.feature_importance = None
        self._position_scalers = {}

        logger.info(f"FeatureEngineer initialized for position: {position_type}")

    def select_relevant_features(self,
                                df: pd.DataFrame,
                                exclude_gk_metrics: bool = True,
                                min_variance: float = 0.01) -> pd.DataFrame:
        """
        Selecciona features relevantes basado en posición y varianza.

        Parameters:
            df: DataFrame con todas las features
            exclude_gk_metrics: Si True, excluye métricas portero (para DF/MF/FW)
            min_variance: Threshold varianza mínima (eliminar features constantes)

        Returns:
            DataFrame con features seleccionadas

        Notes:
            Features con varianza baja (<min_variance) eliminadas por no aportar
            información discriminativa (Guyon & Elisseeff, 2003)
        """
        logger.info("Selecting relevant features...")

        # Separar metadata de features numéricas
        metadata_cols = ['unique_player_id', 'player_name', 'team', 'league',
                        'season', 'position', 'age', 'is_outlier']
        feature_cols = [col for col in df.columns if col not in metadata_cols]

        # Excluir métricas portero si especificado
        if exclude_gk_metrics and self.position_type != 'GK':
            feature_cols = [col for col in feature_cols
                          if not any(gk_m in col for gk_m in self.GK_METRICS)]
            logger.info(f"Excluded GK metrics, {len(feature_cols)} features remaining")

        # Si posición específica, usar lista predefinida
        if self.position_type != 'ALL':
            position_features = self.POSITION_FEATURES[self.position_type]
            # Intersección entre features disponibles y predefinidas
            feature_cols = [col for col in feature_cols if col in position_features]
            logger.info(f"Using {len(feature_cols)} position-specific features for {self.position_type}")

        # Filtrar por varianza mínima
        X = df[feature_cols].values
        selector = VarianceThreshold(threshold=min_variance)
        selector.fit(X)

        mask = selector.get_support()
        feature_cols_filtered = [col for col, keep in zip(feature_cols, mask) if keep]

        n_removed = len(feature_cols) - len(feature_cols_filtered)
        if n_removed > 0:
            logger.info(f"Removed {n_removed} low-variance features")

        self.selected_features = feature_cols_filtered

        # Return DataFrame con metadata + features seleccionadas
        result_cols = [col for col in metadata_cols if col in df.columns] + feature_cols_filtered
        df_result = df[result_cols].copy()

        logger.info(f"Final feature count: {len(feature_cols_filtered)}")

        return df_result

    def remove_correlated_features(self,
                                  df: pd.DataFrame,
                                  threshold: float = 0.95) -> pd.DataFrame:
        """
        Elimina features altamente correlacionadas (redundantes).

        Parameters:
            df: DataFrame con features
            threshold: Threshold correlación absoluta (0-1). Default 0.95.

        Returns:
            DataFrame con features no-redundantes

        Notes:
            Features con |correlation| > threshold son redundantes y pueden
            distorsionar reducción dimensional. Mantiene feature con mayor
            varianza de cada par correlacionado.
        """
        logger.info(f"Removing highly correlated features (threshold={threshold})...")

        metadata_cols = ['unique_player_id', 'player_name', 'team', 'league',
                        'season', 'position', 'is_outlier']
        feature_cols = [col for col in df.columns if col not in metadata_cols]

        # Calcular matriz correlación
        corr_matrix = df[feature_cols].corr().abs()

        # Upper triangle para evitar duplicados
        upper = corr_matrix.where(
            np.triu(np.ones(corr_matrix.shape), k=1).astype(bool)
        )

        # Features a eliminar
        to_drop = []
        for column in upper.columns:
            if (upper[column] > threshold).any():
                # Encuentra feature correlacionada
                correlated = upper.index[upper[column] > threshold].tolist()
                # Mantiene feature con mayor varianza
                variances = df[[column] + correlated].var()
                to_drop.extend(variances.index[variances != variances.max()].tolist())

        to_drop = list(set(to_drop))  # Eliminar duplicados

        if len(to_drop) > 0:
            logger.info(f"Removing {len(to_drop)} highly correlated features")
            feature_cols_filtered = [col for col in feature_cols if col not in to_drop]
        else:
            feature_cols_filtered = feature_cols
            logger.info("No highly correlated features found")

        # Update selected_features
        self.selected_features = feature_cols_filtered

        # Return DataFrame
        result_cols = [col for col in metadata_cols if col in df.columns] + feature_cols_filtered
        return df[result_cols].copy()

    def normalize_by_position(self,
                             df: pd.DataFrame,
                             method: str = 'standard',
                             fit_per_position: bool = True) -> pd.DataFrame:
        """
        Normaliza features por posición (CRÍTICO para comparación cross-position).

        Parameters:
            df: DataFrame con features
            method: Método normalización
                   'standard' -> StandardScaler (mean=0, std=1) [default]
                   'robust' -> RobustScaler (median, IQR) [robusto outliers]
            fit_per_position: Si True, fit scaler separado por posición (recomendado)

        Returns:
            DataFrame con features normalizadas

        Notes:
            Normalización por posición ESENCIAL porque DF/MF/FW tienen distribuciones
            completamente diferentes en métricas ofensivas/defensivas.
            Sin esto, UMAP agrupa incorrectamente.
        """
        logger.info(f"Normalizing features using {method} method...")

        metadata_cols = ['unique_player_id', 'player_name', 'team', 'league',
                        'season', 'position', 'is_outlier']
        feature_cols = [col for col in df.columns if col not in metadata_cols]

        if self.selected_features:
            feature_cols = [col for col in feature_cols if col in self.selected_features]

        df_result = df.copy()

        if fit_per_position and 'position' in df.columns:
            # Normalizar por grupo de posición
            df_result['position_group'] = df_result['position'].str[0]

            for pos_group in df_result['position_group'].unique():
                mask = df_result['position_group'] == pos_group

                # Crear scaler
                if method == 'standard':
                    scaler = StandardScaler()
                elif method == 'robust':
                    scaler = RobustScaler()
                else:
                    raise ValueError(f"Unknown normalization method: {method}")

                # Fit y transform
                X_scaled = scaler.fit_transform(df_result.loc[mask, feature_cols])
                df_result.loc[mask, feature_cols] = X_scaled

                # Guardar scaler para uso futuro
                self._position_scalers[pos_group] = scaler

            df_result = df_result.drop('position_group', axis=1)
            logger.info(f"Normalized features by position group")

        else:
            # Normalizar todo junto
            if method == 'standard':
                self.scaler = StandardScaler()
            elif method == 'robust':
                self.scaler = RobustScaler()
            else:
                raise ValueError(f"Unknown normalization method: {method}")

            X_scaled = self.scaler.fit_transform(df_result[feature_cols])
            df_result[feature_cols] = X_scaled
            logger.info(f"Normalized features globally")

        return df_result

    def get_feature_importance(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calcula feature importance basado en varianza normalizada.

        Parameters:
            df: DataFrame con features normalizadas

        Returns:
            Dict {feature_name: importance_score}

        Notes:
            Features con mayor varianza capturan más información discriminativa.
            Scores normalizados a suma=1.0
        """
        metadata_cols = ['unique_player_id', 'player_name', 'team', 'league',
                        'season', 'position', 'is_outlier', 'position_group']
        feature_cols = [col for col in df.columns if col not in metadata_cols]

        # Calcular varianzas
        variances = df[feature_cols].var()

        # Normalizar a suma=1
        importance = variances / variances.sum()

        # Ordenar descendente
        importance = importance.sort_values(ascending=False)

        self.feature_importance = importance.to_dict()

        logger.info(f"Computed feature importance for {len(importance)} features")
        logger.info(f"Top 5 features: {list(importance.index[:5])}")

        return self.feature_importance

    def prepare_for_umap(self, df: pd.DataFrame,
                        return_dataframe: bool = False) -> Tuple[np.ndarray, pd.DataFrame]:
        """
        Prepara matriz de features final para UMAP.

        Parameters:
            df: DataFrame procesado (features seleccionadas y normalizadas)
            return_dataframe: Si True, también retorna DataFrame metadata

        Returns:
            Tuple (feature_matrix, metadata_df)
            - feature_matrix: Array NumPy (n_samples, n_features)
            - metadata_df: DataFrame con metadata (ids, nombres, etc.)

        Notes:
            Output de este método es input directo para UMAPReducer.
        """
        metadata_cols = ['unique_player_id', 'player_name', 'team', 'league',
                        'season', 'position', 'is_outlier']

        # Features numéricas
        feature_cols = [col for col in df.columns if col not in metadata_cols]
        X = df[feature_cols].values

        logger.info(f"Prepared feature matrix: {X.shape}")

        if return_dataframe:
            metadata_df = df[[col for col in metadata_cols if col in df.columns]].copy()
            return X, metadata_df
        else:
            return X, df

    def transform_new_data(self, df_new: pd.DataFrame,
                          position_group: Optional[str] = None) -> np.ndarray:
        """
        Transforma nuevos datos usando scalers ya fitted.

        Parameters:
            df_new: DataFrame con nuevos jugadores (mismas features)
            position_group: Grupo posición (G, D, M, F). Si None, auto-detecta.

        Returns:
            Array normalizado

        Notes:
            Útil para añadir nuevos jugadores al espacio UMAP existente.
        """
        if not self._position_scalers and not self.scaler:
            raise ValueError("Must call normalize_by_position() first to fit scalers")

        feature_cols = self.selected_features

        if self._position_scalers:
            # Usar scaler por posición
            if position_group is None:
                position_group = df_new['position'].iloc[0][0]

            if position_group not in self._position_scalers:
                raise ValueError(f"No scaler fitted for position group: {position_group}")

            scaler = self._position_scalers[position_group]
            X_scaled = scaler.transform(df_new[feature_cols])

        else:
            # Usar scaler global
            X_scaled = self.scaler.transform(df_new[feature_cols])

        return X_scaled
