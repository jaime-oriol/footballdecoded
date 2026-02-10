"""Dixon-Coles bivariate Poisson model for international football.

Estimates attack/defense strength parameters per team via maximum likelihood,
with time-weighted decay and rho correction for low-scoring results.
Uses scipy.optimize.minimize (L-BFGS-B) -- no extra ML dependencies needed.

References:
    Dixon & Coles (1997): "Modelling Association Football Scores and
    Inefficiencies in the Football Betting Market"
"""

import logging
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson

from ._config import DC_DECAY_RATE, DC_MAX_GOALS, DC_RHO_INIT

logger = logging.getLogger(__name__)


class DixonColesModel:
    """Bivariate Poisson model with time-weighted decay and rho correction.

    Parameters
    ----------
    decay_rate : float
        Exponential decay rate for older matches (default from config).
    max_goals : int
        Maximum goals per team in the score probability matrix.
    """

    def __init__(
        self,
        decay_rate: float = DC_DECAY_RATE,
        max_goals: int = DC_MAX_GOALS,
    ):
        self.decay_rate = decay_rate
        self.max_goals = max_goals
        self.params: Optional[Dict[str, float]] = None
        self.teams: list = []
        self._fitted = False

    def fit(self, matches_df: pd.DataFrame) -> "DixonColesModel":
        """Fit attack/defense parameters on historical match results.

        Parameters
        ----------
        matches_df : pd.DataFrame
            Must contain: team1, team2, team1_score, team2_score, date.
            Optionally: venue ('Home' or 'Neutral').

        Returns
        -------
        self
        """
        df = matches_df.dropna(subset=["team1", "team2", "team1_score", "team2_score"]).copy()
        df["team1_score"] = df["team1_score"].astype(int)
        df["team2_score"] = df["team2_score"].astype(int)

        # Compute time weights (exponential decay from most recent match)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            max_date = df["date"].max()
            df["days_ago"] = (max_date - df["date"]).dt.days.fillna(0)
            df["weight"] = np.exp(-self.decay_rate * df["days_ago"] / 365.0)
        else:
            df["weight"] = 1.0

        # Build team index
        self.teams = sorted(set(df["team1"].tolist() + df["team2"].tolist()))
        team_idx = {t: i for i, t in enumerate(self.teams)}
        n_teams = len(self.teams)

        # Vectorize match data
        home_idx = df["team1"].map(team_idx).values
        away_idx = df["team2"].map(team_idx).values
        home_goals = df["team1_score"].values.astype(float)
        away_goals = df["team2_score"].values.astype(float)
        weights = df["weight"].values
        if "venue" in df.columns:
            is_home = (df["venue"] == "Home").values.astype(float)
        else:
            is_home = np.ones(len(df))  # Assume all home if no venue data

        # Initial parameters: [attack_1..n, defense_1..n, home_advantage, rho]
        # attack > 0, defense > 0 (log-space), home ~ 0.2, rho ~ -0.13
        n_params = 2 * n_teams + 2
        x0 = np.zeros(n_params)
        x0[:n_teams] = 0.0        # log(attack) ~ 0 -> attack ~ 1
        x0[n_teams:2*n_teams] = 0.0  # log(defense) ~ 0 -> defense ~ 1
        x0[-2] = 0.2              # home advantage
        x0[-1] = DC_RHO_INIT      # rho

        # Optimize
        result = minimize(
            self._neg_log_likelihood,
            x0,
            args=(home_idx, away_idx, home_goals, away_goals, weights, is_home, n_teams),
            method="L-BFGS-B",
            options={"maxiter": 500, "disp": False},
        )

        if not result.success:
            logger.warning("Dixon-Coles optimization did not converge: %s", result.message)

        # Extract parameters
        params = result.x
        attack = np.exp(params[:n_teams])
        defense = np.exp(params[n_teams:2*n_teams])
        home_adv = params[-2]
        rho = params[-1]

        # Normalize: mean attack = 1 (identifiability constraint)
        mean_attack = attack.mean()
        attack /= mean_attack
        defense *= mean_attack

        self.params = {
            "attack": {self.teams[i]: attack[i] for i in range(n_teams)},
            "defense": {self.teams[i]: defense[i] for i in range(n_teams)},
            "home_advantage": home_adv,
            "rho": rho,
        }
        self._fitted = True
        logger.info(
            "Dixon-Coles fitted: %d teams, %d matches, home_adv=%.3f, rho=%.3f",
            n_teams, len(df), home_adv, rho,
        )
        return self

    def predict_score_matrix(
        self,
        team_a: str,
        team_b: str,
        neutral: bool = True,
    ) -> np.ndarray:
        """Predict joint probability matrix P(goals_a=i, goals_b=j).

        Parameters
        ----------
        team_a : str
            Team A name (listed first / nominal "home").
        team_b : str
            Team B name.
        neutral : bool
            If True, no home advantage applied (World Cup default).

        Returns
        -------
        np.ndarray
            Shape (max_goals+1, max_goals+1) probability matrix.
        """
        self._check_fitted()
        att_a = self.params["attack"].get(team_a, 1.0)
        def_a = self.params["defense"].get(team_a, 1.0)
        att_b = self.params["attack"].get(team_b, 1.0)
        def_b = self.params["defense"].get(team_b, 1.0)
        rho = self.params["rho"]
        home_adv = 0.0 if neutral else self.params["home_advantage"]

        # Expected goals
        lambda_a = att_a * def_b * np.exp(home_adv)
        lambda_b = att_b * def_a

        # Independent Poisson probabilities
        g = self.max_goals + 1
        prob_a = poisson.pmf(np.arange(g), lambda_a)
        prob_b = poisson.pmf(np.arange(g), lambda_b)
        matrix = np.outer(prob_a, prob_b)

        # Rho correction for low scores (0-0, 1-0, 0-1, 1-1)
        matrix[0, 0] *= 1.0 - lambda_a * lambda_b * rho
        matrix[1, 0] *= 1.0 + lambda_b * rho
        matrix[0, 1] *= 1.0 + lambda_a * rho
        matrix[1, 1] *= 1.0 - rho

        # Renormalize
        matrix = np.maximum(matrix, 0.0)
        matrix /= matrix.sum()

        return matrix

    def predict_outcome(
        self,
        team_a: str,
        team_b: str,
        neutral: bool = True,
    ) -> Dict[str, float]:
        """Predict match outcome probabilities.

        Returns
        -------
        Dict with keys: p_win_a, p_draw, p_win_b, lambda_a, lambda_b.
        """
        matrix = self.predict_score_matrix(team_a, team_b, neutral=neutral)
        g = self.max_goals + 1

        p_win_a = sum(matrix[i, j] for i in range(g) for j in range(i))
        p_draw = sum(matrix[i, i] for i in range(g))
        p_win_b = sum(matrix[i, j] for i in range(g) for j in range(i + 1, g))

        att_a = self.params["attack"].get(team_a, 1.0)
        def_a = self.params["defense"].get(team_a, 1.0)
        att_b = self.params["attack"].get(team_b, 1.0)
        def_b = self.params["defense"].get(team_b, 1.0)
        home_adv = 0.0 if neutral else self.params["home_advantage"]

        return {
            "p_win_a": float(p_win_a),
            "p_draw": float(p_draw),
            "p_win_b": float(p_win_b),
            "lambda_a": float(att_a * def_b * np.exp(home_adv)),
            "lambda_b": float(att_b * def_a),
        }

    def get_team_strengths(self) -> pd.DataFrame:
        """Return attack/defense parameters for all teams.

        Returns
        -------
        pd.DataFrame
            Columns: team, attack, defense, overall (attack / defense).
        """
        self._check_fitted()
        rows = []
        for team in self.teams:
            att = self.params["attack"][team]
            dfn = self.params["defense"][team]
            rows.append({
                "team": team,
                "attack": att,
                "defense": dfn,
                "overall": att / dfn if dfn > 0 else 0.0,
            })
        return pd.DataFrame(rows).sort_values("overall", ascending=False).reset_index(drop=True)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _neg_log_likelihood(
        params: np.ndarray,
        home_idx: np.ndarray,
        away_idx: np.ndarray,
        home_goals: np.ndarray,
        away_goals: np.ndarray,
        weights: np.ndarray,
        is_home: np.ndarray,
        n_teams: int,
    ) -> float:
        """Negative log-likelihood for Dixon-Coles model."""
        attack = np.exp(params[:n_teams])
        defense = np.exp(params[n_teams:2*n_teams])
        home_adv = params[-2]
        rho = params[-1]

        # Expected goals per match
        lambda_h = attack[home_idx] * defense[away_idx] * np.exp(home_adv * is_home)
        lambda_a = attack[away_idx] * defense[home_idx]

        # Avoid log(0)
        lambda_h = np.maximum(lambda_h, 1e-10)
        lambda_a = np.maximum(lambda_a, 1e-10)

        # Poisson log-likelihood
        ll = (
            home_goals * np.log(lambda_h) - lambda_h
            + away_goals * np.log(lambda_a) - lambda_a
        )

        # Rho correction for low scores
        tau = np.ones_like(ll)
        mask_00 = (home_goals == 0) & (away_goals == 0)
        mask_10 = (home_goals == 1) & (away_goals == 0)
        mask_01 = (home_goals == 0) & (away_goals == 1)
        mask_11 = (home_goals == 1) & (away_goals == 1)

        tau[mask_00] = 1.0 - lambda_h[mask_00] * lambda_a[mask_00] * rho
        tau[mask_10] = 1.0 + lambda_a[mask_10] * rho
        tau[mask_01] = 1.0 + lambda_h[mask_01] * rho
        tau[mask_11] = 1.0 - rho

        tau = np.maximum(tau, 1e-10)
        ll += np.log(tau)

        return -np.sum(weights * ll)

    def _check_fitted(self):
        if not self._fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")
