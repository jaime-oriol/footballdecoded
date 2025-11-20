"""
Validation Module

Valida pipeline completo UMAP + GMM + Similarity usando ground truth y métricas.

Clase principal:
    PipelineValidator: Validación end-to-end del sistema
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PipelineValidator:
    """
    Validador para pipeline completo similitud.

    Valida:
        - Precisión similitud con pares conocidos (ground truth)
        - Estabilidad embedding y clustering
        - Sensibilidad a hiperparámetros
        - Performance en casos uso reales

    Attributes:
        similarity_engine: Instancia PlayerSimilarity
        ground_truth_pairs: Lista pares (player1_id, player2_id) conocidos similares
    """

    def __init__(self, similarity_engine):
        """
        Inicializa validador.

        Parameters:
            similarity_engine: Instancia PlayerSimilarity fitted
        """
        self.similarity_engine = similarity_engine
        self.ground_truth_pairs = []

        logger.info("PipelineValidator initialized")

    def add_ground_truth_pair(self, player1_id: str, player2_id: str):
        """
        Añade par ground truth (jugadores conocidos similares).

        Parameters:
            player1_id, player2_id: IDs jugadores similares
        """
        self.ground_truth_pairs.append((player1_id, player2_id))
        logger.info(f"Added ground truth pair: {player1_id} <-> {player2_id}")

    def validate_known_pairs(self, top_k: int = 10) -> pd.DataFrame:
        """
        Valida que pares ground truth aparezcan en top_k similares mutuamente.

        Parameters:
            top_k: Top K similares a verificar

        Returns:
            DataFrame con resultados validación:
                - player_1, player_2: Par ground truth
                - found_in_top_k: bool
                - rank_1to2: Rank player2 en similares de player1
                - rank_2to1: Rank player1 en similares de player2
                - similarity_score: Score similitud

        Notes:
            Métrica clave: recall@K = % pares encontrados en top K.
            Objetivo: recall@10 > 80%
        """
        if not self.ground_truth_pairs:
            logger.warning("No ground truth pairs defined")
            return pd.DataFrame()

        logger.info(f"Validating {len(self.ground_truth_pairs)} ground truth pairs...")

        results = []

        for player1_id, player2_id in self.ground_truth_pairs:
            try:
                # Similares de player1
                similar1 = self.similarity_engine.find_similar_players(
                    player1_id, top_n=top_k, return_scores=True
                )

                # Similares de player2
                similar2 = self.similarity_engine.find_similar_players(
                    player2_id, top_n=top_k, return_scores=True
                )

                # Verificar reciprocidad
                found_2in1 = player2_id in similar1['unique_player_id'].values
                found_1in2 = player1_id in similar2['unique_player_id'].values

                rank_2in1 = np.nan
                rank_1in2 = np.nan
                score = 0.0

                if found_2in1:
                    rank_2in1 = similar1[similar1['unique_player_id'] == player2_id].index[0] + 1
                    score = similar1[similar1['unique_player_id'] == player2_id]['similarity_score'].iloc[0]

                if found_1in2:
                    rank_1in2 = similar2[similar2['unique_player_id'] == player1_id].index[0] + 1

                results.append({
                    'player_1': player1_id,
                    'player_2': player2_id,
                    'found_in_top_k': found_2in1 or found_1in2,
                    'mutual_in_top_k': found_2in1 and found_1in2,
                    'rank_1to2': rank_2in1,
                    'rank_2to1': rank_1in2,
                    'similarity_score': score
                })

            except Exception as e:
                logger.error(f"Validation failed for pair {player1_id}, {player2_id}: {e}")

        df_results = pd.DataFrame(results)

        if len(df_results) > 0:
            recall = df_results['found_in_top_k'].mean()
            mutual_recall = df_results['mutual_in_top_k'].mean()

            logger.info(f"Validation results: Recall@{top_k} = {recall:.2%}")
            logger.info(f"Mutual recall@{top_k} = {mutual_recall:.2%}")

        return df_results

    def generate_validation_report(self) -> Dict:
        """
        Genera reporte completo validación.

        Returns:
            Dict con métricas agregadas y recomendaciones
        """
        logger.info("Generating validation report...")

        report = {
            'ground_truth_pairs': len(self.ground_truth_pairs),
            'validation_results': None,
            'recommendations': []
        }

        if self.ground_truth_pairs:
            df_val = self.validate_known_pairs(top_k=10)
            report['validation_results'] = {
                'recall_at_10': df_val['found_in_top_k'].mean(),
                'mutual_recall_at_10': df_val['mutual_in_top_k'].mean(),
                'mean_rank': df_val['rank_1to2'].mean(),
                'mean_score': df_val['similarity_score'].mean()
            }

            # Recomendaciones
            if report['validation_results']['recall_at_10'] < 0.7:
                report['recommendations'].append(
                    "Low recall detected. Consider: (1) adjusting UMAP parameters, "
                    "(2) increasing GMM weight, (3) adding more features"
                )

        logger.info("Validation report generated")

        return report
