"""
Visualization Module

Visualizaciones científicas para análisis e interpretación resultados UMAP + GMM.

Clase principal:
    SimilarityVisualizer: Plots publicación-ready
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Optional, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimilarityVisualizer:
    """
    Generador visualizaciones para player similarity system.

    Plots disponibles:
        - UMAP embedding 2D/3D con clusters GMM
        - Heatmap matriz similaridad
        - Cluster profiles (radar charts)
        - Feature importance bar plots
        - Validation metrics

    Style: Científico (matplotlib + seaborn), sin decoraciones excesivas.
    """

    def __init__(self, figsize: Tuple[int, int] = (12, 8), dpi: int = 100):
        """
        Inicializa visualizer.

        Parameters:
            figsize: Tamaño default figuras (width, height)
            dpi: Resolución plots
        """
        self.figsize = figsize
        self.dpi = dpi

        # Estilo científico
        sns.set_style("whitegrid")
        plt.rcParams['figure.dpi'] = dpi
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 11
        plt.rcParams['axes.titlesize'] = 12
        plt.rcParams['xtick.labelsize'] = 9
        plt.rcParams['ytick.labelsize'] = 9

        logger.info("SimilarityVisualizer initialized")

    def plot_umap_embedding(self,
                           embedding_df: pd.DataFrame,
                           color_by: str = 'cluster_id',
                           highlight_players: Optional[List[str]] = None,
                           save_path: Optional[str] = None,
                           show: bool = True) -> plt.Figure:
        """
        Plot UMAP embedding 2D con colores por cluster.

        Parameters:
            embedding_df: DataFrame con umap_1, umap_2 y metadata
            color_by: Columna para colorear ('cluster_id', 'position', 'league')
            highlight_players: Lista player_ids a destacar
            save_path: Path guardar figura (opcional)
            show: Si True, muestra plot

        Returns:
            Figure matplotlib
        """
        logger.info("Plotting UMAP embedding...")

        fig, ax = plt.subplots(figsize=self.figsize)

        # Scatter plot
        if color_by in embedding_df.columns:
            unique_vals = embedding_df[color_by].unique()
            n_colors = len(unique_vals)
            colors = sns.color_palette("husl", n_colors)

            for i, val in enumerate(unique_vals):
                mask = embedding_df[color_by] == val
                ax.scatter(
                    embedding_df.loc[mask, 'umap_1'],
                    embedding_df.loc[mask, 'umap_2'],
                    c=[colors[i]],
                    label=f'{color_by}={val}',
                    alpha=0.6,
                    s=50,
                    edgecolors='white',
                    linewidth=0.5
                )
        else:
            ax.scatter(
                embedding_df['umap_1'],
                embedding_df['umap_2'],
                alpha=0.6,
                s=50
            )

        # Highlight jugadores específicos
        if highlight_players:
            mask = embedding_df['unique_player_id'].isin(highlight_players)
            ax.scatter(
                embedding_df.loc[mask, 'umap_1'],
                embedding_df.loc[mask, 'umap_2'],
                c='red',
                marker='*',
                s=200,
                edgecolors='black',
                linewidth=1.5,
                label='Highlighted',
                zorder=10
            )

            # Anotar nombres
            for _, row in embedding_df[mask].iterrows():
                ax.annotate(
                    row['player_name'],
                    (row['umap_1'], row['umap_2']),
                    xytext=(5, 5),
                    textcoords='offset points',
                    fontsize=8,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7)
                )

        ax.set_xlabel('UMAP Dimension 1')
        ax.set_ylabel('UMAP Dimension 2')
        ax.set_title('Player Similarity - UMAP Embedding')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Figure saved to {save_path}")

        if show:
            plt.show()

        return fig

    def plot_similarity_heatmap(self,
                               similarity_matrix: np.ndarray,
                               player_names: List[str],
                               save_path: Optional[str] = None,
                               show: bool = True) -> plt.Figure:
        """
        Plot heatmap matriz similaridad.

        Parameters:
            similarity_matrix: Matriz NxN similaridad
            player_names: Nombres jugadores (orden matriz)
            save_path: Path guardar
            show: Si True, muestra plot

        Returns:
            Figure matplotlib
        """
        logger.info("Plotting similarity heatmap...")

        fig, ax = plt.subplots(figsize=(10, 8))

        sns.heatmap(
            similarity_matrix,
            annot=False,
            cmap='RdYlGn',
            vmin=0,
            vmax=1,
            xticklabels=player_names,
            yticklabels=player_names,
            cbar_kws={'label': 'Similarity Score'},
            ax=ax
        )

        ax.set_title('Player Similarity Matrix')
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Figure saved to {save_path}")

        if show:
            plt.show()

        return fig

    def plot_cluster_profiles(self,
                             cluster_profiles_df: pd.DataFrame,
                             save_path: Optional[str] = None,
                             show: bool = True) -> plt.Figure:
        """
        Plot perfiles clusters (top features por cluster).

        Parameters:
            cluster_profiles_df: DataFrame de get_cluster_profiles()
            save_path: Path guardar
            show: Si True, muestra plot

        Returns:
            Figure matplotlib
        """
        logger.info("Plotting cluster profiles...")

        n_clusters = cluster_profiles_df['cluster_id'].nunique()
        fig, axes = plt.subplots(1, n_clusters, figsize=(5*n_clusters, 6), sharey=True)

        if n_clusters == 1:
            axes = [axes]

        for cluster_id in range(n_clusters):
            df_cluster = cluster_profiles_df[
                cluster_profiles_df['cluster_id'] == cluster_id
            ].nlargest(10, 'z_score', keep='all')

            axes[cluster_id].barh(
                df_cluster['feature'],
                df_cluster['z_score'],
                color=sns.color_palette("husl", n_clusters)[cluster_id]
            )

            axes[cluster_id].set_xlabel('Z-Score')
            axes[cluster_id].set_title(f'Cluster {cluster_id}\n(n={df_cluster["cluster_size"].iloc[0]})')
            axes[cluster_id].axvline(x=0, color='black', linestyle='--', linewidth=0.8)
            axes[cluster_id].grid(True, alpha=0.3, axis='x')

        axes[0].set_ylabel('Features')
        plt.suptitle('Cluster Profiles - Top Distinctive Features', fontsize=14)
        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Figure saved to {save_path}")

        if show:
            plt.show()

        return fig

    def plot_feature_importance(self,
                               importance_dict: Dict[str, float],
                               top_n: int = 20,
                               save_path: Optional[str] = None,
                               show: bool = True) -> plt.Figure:
        """
        Plot feature importance (bar chart).

        Parameters:
            importance_dict: Dict {feature_name: importance_score}
            top_n: Top features a mostrar
            save_path: Path guardar
            show: Si True, muestra plot

        Returns:
            Figure matplotlib
        """
        logger.info("Plotting feature importance...")

        # Ordenar y tomar top_n
        importance_series = pd.Series(importance_dict).nlargest(top_n)

        fig, ax = plt.subplots(figsize=(8, 6))

        ax.barh(
            range(len(importance_series)),
            importance_series.values,
            color='steelblue'
        )

        ax.set_yticks(range(len(importance_series)))
        ax.set_yticklabels(importance_series.index)
        ax.set_xlabel('Importance Score (Normalized Variance)')
        ax.set_title(f'Top {top_n} Most Important Features')
        ax.grid(True, alpha=0.3, axis='x')
        ax.invert_yaxis()

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Figure saved to {save_path}")

        if show:
            plt.show()

        return fig

    def plot_validation_metrics(self,
                               validation_results: pd.DataFrame,
                               save_path: Optional[str] = None,
                               show: bool = True) -> plt.Figure:
        """
        Plot métricas validación (recall, ranks).

        Parameters:
            validation_results: DataFrame de validate_known_pairs()
            save_path: Path guardar
            show: Si True, muestra plot

        Returns:
            Figure matplotlib
        """
        logger.info("Plotting validation metrics...")

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        # Plot 1: Recall por threshold
        thresholds = [5, 10, 20, 50]
        recalls = []

        for k in thresholds:
            recall = (validation_results['rank_1to2'] <= k).mean()
            recalls.append(recall)

        axes[0].plot(thresholds, recalls, marker='o', linewidth=2)
        axes[0].set_xlabel('Top K')
        axes[0].set_ylabel('Recall')
        axes[0].set_title('Recall@K for Ground Truth Pairs')
        axes[0].grid(True, alpha=0.3)
        axes[0].set_ylim([0, 1.05])

        # Plot 2: Distribución ranks
        axes[1].hist(
            validation_results['rank_1to2'].dropna(),
            bins=20,
            color='steelblue',
            edgecolor='black',
            alpha=0.7
        )
        axes[1].set_xlabel('Rank in Top K')
        axes[1].set_ylabel('Frequency')
        axes[1].set_title('Distribution of Ranks for Ground Truth Pairs')
        axes[1].grid(True, alpha=0.3, axis='y')

        plt.tight_layout()

        if save_path:
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Figure saved to {save_path}")

        if show:
            plt.show()

        return fig
