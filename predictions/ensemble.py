"""Ensemble combiner: Dixon-Coles + GradientBoosting classifier.

Combines statistical (Dixon-Coles) and ML (GBM) predictions via
calibrated weighted average optimized on log-loss.
"""

import logging
import pickle
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier

from ._config import ALL_FEATURES, ENSEMBLE_W_DC, ENSEMBLE_W_GBM, GBM_PARAMS
from .dixon_coles import DixonColesModel
from .features import build_match_features

logger = logging.getLogger(__name__)


class MatchPredictor:
    """Ensemble match outcome predictor.

    Combines Dixon-Coles bivariate Poisson (Layer 1) with a
    GradientBoostingClassifier (Layer 3) via weighted average.

    Parameters
    ----------
    w_dc : float
        Weight for Dixon-Coles predictions.
    w_gbm : float
        Weight for GBM predictions.
    """

    def __init__(
        self,
        w_dc: float = ENSEMBLE_W_DC,
        w_gbm: float = ENSEMBLE_W_GBM,
    ):
        self.w_dc = w_dc
        self.w_gbm = w_gbm
        self.dc_model = DixonColesModel()
        self.gbm_model: Optional[GradientBoostingClassifier] = None
        self._fitted = False

    def fit(
        self,
        matches_df: pd.DataFrame,
        X_train: pd.DataFrame,
        y_train: pd.Series,
    ) -> "MatchPredictor":
        """Fit both models.

        Parameters
        ----------
        matches_df : pd.DataFrame
            Historical matches for Dixon-Coles (team1, team2, team1_score,
            team2_score, date, venue).
        X_train : pd.DataFrame
            Feature matrix for GBM (from features.build_training_matrix).
        y_train : pd.Series
            Target: 2=win_a, 1=draw, 0=win_b.

        Returns
        -------
        self
        """
        # Layer 1: Dixon-Coles
        logger.info("Fitting Dixon-Coles model...")
        self.dc_model.fit(matches_df)

        # Layer 3: GBM
        logger.info("Fitting GBM classifier...")
        self.gbm_model = GradientBoostingClassifier(**GBM_PARAMS)
        self.gbm_model.fit(X_train, y_train)

        self._fitted = True
        logger.info(
            "Ensemble fitted: DC + GBM (w_dc=%.2f, w_gbm=%.2f)",
            self.w_dc, self.w_gbm,
        )
        return self

    def predict(
        self,
        team_a: str,
        team_b: str,
        rankings_df: pd.DataFrame,
        squad_features: Dict[str, Dict[str, float]],
        neutral: bool = True,
        h2h_record: Optional[Dict] = None,
        stage: int = 0,
        rest_days_a: int = 3,
        rest_days_b: int = 3,
        group_match_number: int = 0,
        must_win_a: bool = False,
        must_win_b: bool = False,
    ) -> Dict[str, float]:
        """Predict match outcome probabilities.

        Parameters
        ----------
        team_a, team_b : str
            Team names.
        rankings_df : pd.DataFrame
            Current ELO rankings.
        squad_features : dict
            Squad features for all teams.
        neutral : bool
            Neutral venue (default True for World Cup).
        h2h_record, stage, rest_days_a/b, group_match_number, must_win_a/b:
            Context parameters.

        Returns
        -------
        Dict with: p_win_a, p_draw, p_win_b, lambda_a, lambda_b,
                   p_dc (Dixon-Coles raw), p_gbm (GBM raw).
        """
        self._check_fitted()

        # Dixon-Coles prediction
        dc_pred = self.dc_model.predict_outcome(team_a, team_b, neutral=neutral)
        p_dc = np.array([dc_pred["p_win_a"], dc_pred["p_draw"], dc_pred["p_win_b"]])

        # GBM prediction
        feat = build_match_features(
            team_a, team_b,
            rankings_df=rankings_df,
            squad_features=squad_features,
            h2h_record=h2h_record,
            stage=stage,
            rest_days_a=rest_days_a,
            rest_days_b=rest_days_b,
            group_match_number=group_match_number,
            must_win_a=must_win_a,
            must_win_b=must_win_b,
        )
        X = pd.DataFrame([feat])[ALL_FEATURES].fillna(0.0)
        # GBM classes: [0, 1, 2] -> [win_b, draw, win_a]
        p_gbm_raw = self.gbm_model.predict_proba(X)[0]
        # Reorder to [p_win_a, p_draw, p_win_b]
        class_order = list(self.gbm_model.classes_)
        p_gbm = np.array([
            p_gbm_raw[class_order.index(2)] if 2 in class_order else 0.0,
            p_gbm_raw[class_order.index(1)] if 1 in class_order else 0.0,
            p_gbm_raw[class_order.index(0)] if 0 in class_order else 0.0,
        ])

        # Ensemble
        p_final = self.w_dc * p_dc + self.w_gbm * p_gbm
        p_final = np.maximum(p_final, 1e-6)
        p_final /= p_final.sum()

        return {
            "p_win_a": float(p_final[0]),
            "p_draw": float(p_final[1]),
            "p_win_b": float(p_final[2]),
            "lambda_a": dc_pred["lambda_a"],
            "lambda_b": dc_pred["lambda_b"],
            "p_dc": {"win_a": float(p_dc[0]), "draw": float(p_dc[1]), "win_b": float(p_dc[2])},
            "p_gbm": {"win_a": float(p_gbm[0]), "draw": float(p_gbm[1]), "win_b": float(p_gbm[2])},
        }

    def predict_knockout(
        self,
        team_a: str,
        team_b: str,
        rankings_df: pd.DataFrame,
        squad_features: Dict[str, Dict[str, float]],
        stage: int = 1,
        **kwargs,
    ) -> Dict[str, float]:
        """Predict knockout match (with extra time / penalties).

        Returns
        -------
        Dict with: p_advance_a, p_advance_b (after ET/PKs),
                   p_90min (win/draw/loss in regulation).
        """
        from ._config import ET_PROB, PK_HOME_EDGE

        p90 = self.predict(
            team_a, team_b,
            rankings_df=rankings_df,
            squad_features=squad_features,
            stage=stage,
            **kwargs,
        )

        p_win_a_90 = p90["p_win_a"]
        p_draw_90 = p90["p_draw"]
        p_win_b_90 = p90["p_win_b"]

        # Extra time: draw probability distributed proportionally
        if p_win_a_90 + p_win_b_90 > 0:
            ratio_a = p_win_a_90 / (p_win_a_90 + p_win_b_90)
        else:
            ratio_a = 0.5

        p_et_a = p_draw_90 * ET_PROB * ratio_a
        p_et_b = p_draw_90 * ET_PROB * (1 - ratio_a)

        # Penalties: remaining draw probability
        p_pk = p_draw_90 * (1 - ET_PROB)
        # Slight edge to higher-ELO team
        elo_a = rankings_df.loc[team_a, "elo_rating"] if team_a in rankings_df.index else 1500
        elo_b = rankings_df.loc[team_b, "elo_rating"] if team_b in rankings_df.index else 1500
        pk_edge_a = PK_HOME_EDGE if elo_a >= elo_b else (1 - PK_HOME_EDGE)

        p_pk_a = p_pk * pk_edge_a
        p_pk_b = p_pk * (1 - pk_edge_a)

        p_advance_a = p_win_a_90 + p_et_a + p_pk_a
        p_advance_b = p_win_b_90 + p_et_b + p_pk_b

        return {
            "p_advance_a": float(p_advance_a),
            "p_advance_b": float(p_advance_b),
            "p_90min": {
                "win_a": float(p_win_a_90),
                "draw": float(p_draw_90),
                "win_b": float(p_win_b_90),
            },
        }

    def optimize_weights(
        self,
        matches_df: pd.DataFrame,
        X_val: pd.DataFrame,
        y_val: pd.Series,
        rankings_df: pd.DataFrame,
        squad_features: Dict[str, Dict[str, float]],
    ) -> Tuple[float, float]:
        """Optimize ensemble weights on validation data.

        Grid search over w_dc in [0.3, 0.4, ..., 0.9] minimizing log-loss.

        Returns
        -------
        Tuple of (optimal_w_dc, optimal_w_gbm).
        """
        from sklearn.metrics import log_loss

        best_w = self.w_dc
        best_ll = float("inf")

        for w_dc in np.arange(0.3, 0.95, 0.05):
            w_gbm = 1.0 - w_dc
            self.w_dc = w_dc
            self.w_gbm = w_gbm

            # Predict on validation set
            probs = []
            for i, (_, match) in enumerate(matches_df.iterrows()):
                if i >= len(X_val):
                    break
                team_a = match["team1"]
                team_b = match["team2"]
                pred = self.predict(
                    team_a, team_b,
                    rankings_df=rankings_df,
                    squad_features=squad_features,
                )
                probs.append([pred["p_win_a"], pred["p_draw"], pred["p_win_b"]])

            if probs:
                probs_arr = np.array(probs)
                # Convert y_val to one-hot for log_loss
                y_arr = y_val.values[:len(probs)]
                ll = log_loss(y_arr, probs_arr, labels=[2, 1, 0])
                if ll < best_ll:
                    best_ll = ll
                    best_w = w_dc

        self.w_dc = best_w
        self.w_gbm = 1.0 - best_w
        logger.info("Optimized weights: w_dc=%.2f, w_gbm=%.2f (log_loss=%.4f)", best_w, 1.0 - best_w, best_ll)
        return (self.w_dc, self.w_gbm)

    def save(self, filepath: str):
        """Serialize model to disk."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "wb") as f:
            pickle.dump(self, f)
        logger.info("Model saved to %s", filepath)

    @classmethod
    def load(cls, filepath: str) -> "MatchPredictor":
        """Load serialized model."""
        with open(filepath, "rb") as f:
            model = pickle.load(f)
        logger.info("Model loaded from %s", filepath)
        return model

    def _check_fitted(self):
        if not self._fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")
