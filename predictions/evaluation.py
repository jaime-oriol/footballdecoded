"""Backtesting and calibration evaluation for match predictions.

Temporal walk-forward validation on historical tournaments (WC 2018, WC 2022,
Euro 2024). Metrics: Brier score, log loss, accuracy, calibration curves.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def brier_score(predictions: np.ndarray, outcomes: np.ndarray) -> float:
    """Compute multi-class Brier score.

    Parameters
    ----------
    predictions : np.ndarray
        Shape (n, 3): [p_win_a, p_draw, p_win_b] per match.
    outcomes : np.ndarray
        Shape (n,): 2=win_a, 1=draw, 0=win_b.

    Returns
    -------
    float
        Brier score (lower is better, 0 = perfect, 0.67 = random baseline).
    """
    n = len(outcomes)
    if n == 0:
        return 0.0

    # One-hot encode outcomes: [win_a, draw, win_b]
    one_hot = np.zeros((n, 3))
    for i, o in enumerate(outcomes):
        if o == 2:
            one_hot[i, 0] = 1.0
        elif o == 1:
            one_hot[i, 1] = 1.0
        else:
            one_hot[i, 2] = 1.0

    return float(np.mean(np.sum((predictions - one_hot) ** 2, axis=1)))


def log_loss_score(predictions: np.ndarray, outcomes: np.ndarray) -> float:
    """Compute multi-class log loss.

    Parameters
    ----------
    predictions : np.ndarray
        Shape (n, 3): [p_win_a, p_draw, p_win_b] per match.
    outcomes : np.ndarray
        Shape (n,): 2=win_a, 1=draw, 0=win_b.

    Returns
    -------
    float
        Log loss (lower is better, 1.099 = random baseline for 3 classes).
    """
    n = len(outcomes)
    if n == 0:
        return 0.0

    eps = 1e-10
    preds = np.clip(predictions, eps, 1 - eps)

    ll = 0.0
    for i, o in enumerate(outcomes):
        if o == 2:
            ll -= np.log(preds[i, 0])
        elif o == 1:
            ll -= np.log(preds[i, 1])
        else:
            ll -= np.log(preds[i, 2])

    return float(ll / n)


def accuracy_score(predictions: np.ndarray, outcomes: np.ndarray) -> float:
    """Compute prediction accuracy (most probable outcome vs actual).

    Parameters
    ----------
    predictions : np.ndarray
        Shape (n, 3).
    outcomes : np.ndarray
        Shape (n,): 2=win_a, 1=draw, 0=win_b.

    Returns
    -------
    float
        Fraction correct (0 to 1).
    """
    n = len(outcomes)
    if n == 0:
        return 0.0

    # Map prediction argmax to outcome encoding
    # predictions columns: [win_a, draw, win_b] -> argmax 0=win_a, 1=draw, 2=win_b
    pred_class = np.argmax(predictions, axis=1)
    # Map: 0->2(win_a), 1->1(draw), 2->0(win_b)
    pred_outcome = np.array([2, 1, 0])[pred_class]

    return float(np.mean(pred_outcome == outcomes))


def ranked_probability_score(predictions: np.ndarray, outcomes: np.ndarray) -> float:
    """Compute Ranked Probability Score (RPS) for ordinal outcomes.

    Parameters
    ----------
    predictions : np.ndarray
        Shape (n, 3): [p_win_a, p_draw, p_win_b].
    outcomes : np.ndarray
        Shape (n,): 2=win_a, 1=draw, 0=win_b.

    Returns
    -------
    float
        RPS (lower is better).
    """
    n = len(outcomes)
    if n == 0:
        return 0.0

    rps_total = 0.0
    for i in range(n):
        # Cumulative predicted: [p_win_a, p_win_a+p_draw, 1.0]
        cum_pred = np.cumsum(predictions[i])
        # Cumulative actual
        o = outcomes[i]
        cum_actual = np.array([
            1.0 if o == 2 else 0.0,
            1.0 if o >= 1 else 0.0,
            1.0,
        ])
        rps_total += np.mean((cum_pred - cum_actual) ** 2)

    return float(rps_total / n)


def calibration_curve(
    predictions: np.ndarray,
    outcomes: np.ndarray,
    n_bins: int = 10,
) -> pd.DataFrame:
    """Compute calibration curve data.

    For each probability bin, compute mean predicted probability vs
    observed frequency.

    Parameters
    ----------
    predictions : np.ndarray
        Shape (n, 3).
    outcomes : np.ndarray
        Shape (n,): 2=win_a, 1=draw, 0=win_b.
    n_bins : int
        Number of bins.

    Returns
    -------
    pd.DataFrame
        Columns: bin_center, predicted_prob, observed_freq, count.
    """
    # Flatten: treat each class prediction independently
    rows = []
    # Class mapping: col 0 = win_a (outcome=2), col 1 = draw (outcome=1), col 2 = win_b (outcome=0)
    class_map = {0: 2, 1: 1, 2: 0}

    for col_idx, outcome_val in class_map.items():
        probs = predictions[:, col_idx]
        actual = (outcomes == outcome_val).astype(float)

        bin_edges = np.linspace(0, 1, n_bins + 1)
        for b in range(n_bins):
            lo, hi = bin_edges[b], bin_edges[b + 1]
            mask = (probs >= lo) & (probs < hi)
            if b == n_bins - 1:
                mask = (probs >= lo) & (probs <= hi)
            count = mask.sum()
            if count > 0:
                rows.append({
                    "bin_center": (lo + hi) / 2,
                    "predicted_prob": float(probs[mask].mean()),
                    "observed_freq": float(actual[mask].mean()),
                    "count": int(count),
                    "class": ["win_a", "draw", "win_b"][col_idx],
                })

    return pd.DataFrame(rows)


def backtest_tournament(
    predictor,
    tournament_matches: pd.DataFrame,
    rankings_df: pd.DataFrame,
    squad_features: Dict[str, Dict[str, float]],
    tournament_name: str = "",
) -> Dict[str, Any]:
    """Run full backtest on a historical tournament.

    Parameters
    ----------
    predictor : MatchPredictor
        Fitted model (trained on data BEFORE the tournament).
    tournament_matches : pd.DataFrame
        Actual match results with: team1, team2, team1_score, team2_score.
    rankings_df : pd.DataFrame
        ELO rankings as of the tournament start.
    squad_features : dict
        Squad features at tournament time.
    tournament_name : str
        Name for logging.

    Returns
    -------
    Dict with metrics and detailed predictions.
    """
    predictions = []
    outcomes = []

    for _, match in tournament_matches.iterrows():
        team_a = match["team1"]
        team_b = match["team2"]
        score_a = int(match["team1_score"])
        score_b = int(match["team2_score"])

        # Predict
        pred = predictor.predict(
            team_a, team_b,
            rankings_df=rankings_df,
            squad_features=squad_features,
        )
        predictions.append([pred["p_win_a"], pred["p_draw"], pred["p_win_b"]])

        # Actual outcome
        if score_a > score_b:
            outcomes.append(2)
        elif score_a == score_b:
            outcomes.append(1)
        else:
            outcomes.append(0)

    preds = np.array(predictions)
    outs = np.array(outcomes)

    metrics = {
        "tournament": tournament_name,
        "n_matches": len(outcomes),
        "brier_score": brier_score(preds, outs),
        "log_loss": log_loss_score(preds, outs),
        "accuracy": accuracy_score(preds, outs),
        "rps": ranked_probability_score(preds, outs),
    }

    # Baselines
    # Random baseline: uniform [1/3, 1/3, 1/3]
    random_preds = np.full_like(preds, 1.0 / 3.0)
    metrics["baseline_random_brier"] = brier_score(random_preds, outs)
    metrics["baseline_random_ll"] = log_loss_score(random_preds, outs)

    # ELO-only baseline (predict favorite wins based on elo_rating_diff sign)
    elo_preds = []
    for _, match in tournament_matches.iterrows():
        team_a = match["team1"]
        team_b = match["team2"]
        ra = rankings_df.loc[team_a, "elo_rating"] if team_a in rankings_df.index else 1500
        rb = rankings_df.loc[team_b, "elo_rating"] if team_b in rankings_df.index else 1500
        delta = ra - rb
        # Simple ELO win probability
        p_a = 1.0 / (1.0 + 10 ** (-delta / 400.0))
        p_draw = 0.25  # Flat draw prior
        p_a_adj = p_a * (1 - p_draw)
        p_b_adj = (1 - p_a) * (1 - p_draw)
        elo_preds.append([p_a_adj, p_draw, p_b_adj])

    elo_preds = np.array(elo_preds)
    metrics["baseline_elo_brier"] = brier_score(elo_preds, outs)
    metrics["baseline_elo_ll"] = log_loss_score(elo_preds, outs)

    cal = calibration_curve(preds, outs)

    logger.info("Backtest %s: %d matches", tournament_name, len(outcomes))
    logger.info("  Brier=%.4f (random=%.4f, elo=%.4f)", metrics["brier_score"], metrics["baseline_random_brier"], metrics["baseline_elo_brier"])
    logger.info("  LogLoss=%.4f (random=%.4f, elo=%.4f)", metrics["log_loss"], metrics["baseline_random_ll"], metrics["baseline_elo_ll"])
    logger.info("  Accuracy=%.1f%%", metrics["accuracy"] * 100)

    return {
        "metrics": metrics,
        "predictions": preds,
        "outcomes": outs,
        "calibration": cal,
    }


def plot_calibration(
    calibration_df: pd.DataFrame,
    title: str = "Calibration Plot",
) -> "matplotlib.figure.Figure":
    """Plot calibration curve (predicted vs observed probability).

    Parameters
    ----------
    calibration_df : pd.DataFrame
        Output of calibration_curve().
    title : str
        Plot title.

    Returns
    -------
    matplotlib Figure.
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 8), facecolor="#313332")
    ax.set_facecolor("#313332")

    colors = {"win_a": "deepskyblue", "draw": "#888888", "win_b": "tomato"}
    labels = {"win_a": "Win A", "draw": "Draw", "win_b": "Win B"}

    for cls in ["win_a", "draw", "win_b"]:
        subset = calibration_df[calibration_df["class"] == cls]
        if subset.empty:
            continue
        ax.scatter(
            subset["predicted_prob"],
            subset["observed_freq"],
            c=colors[cls],
            s=subset["count"] * 3,
            alpha=0.8,
            label=labels[cls],
            edgecolors="white",
            linewidths=0.5,
        )

    ax.plot([0, 1], [0, 1], "w--", alpha=0.5, label="Perfect calibration")
    ax.set_xlabel("Predicted Probability", color="white", fontsize=12)
    ax.set_ylabel("Observed Frequency", color="white", fontsize=12)
    ax.set_title(title, color="white", fontsize=14, fontweight="bold")
    ax.legend(facecolor="#444444", edgecolor="white", labelcolor="white")
    ax.tick_params(colors="white")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    for spine in ax.spines.values():
        spine.set_color("white")
        spine.set_alpha(0.3)

    plt.tight_layout()
    return fig
