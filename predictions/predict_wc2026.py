"""World Cup 2026 prediction CLI.

Interactive menu for training, predicting, simulating, and backtesting.
Usage: python predictions/predict_wc2026.py
"""

import logging
import sys
from pathlib import Path

import pandas as pd

# Add parent dir for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from predictions._config import (
    BACKTEST_TOURNAMENTS,
    GROUPS,
    MC_SIMULATIONS,
    QUALIFIED_TEAMS,
)
from predictions.data_collector import (
    collect_historical_matches,
    collect_rankings_by_year,
    prepare_backtest_data,
)
from predictions.ensemble import MatchPredictor
from predictions.evaluation import backtest_tournament, plot_calibration
from predictions.features import build_training_matrix
from predictions.simulation import TournamentSimulator

logger = logging.getLogger("predictions")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

MODEL_PATH = Path(__file__).parent / "model" / "wc2026_ensemble.pkl"
PREDICTIONS_DIR = Path(__file__).parent / "output"


def menu():
    """Main interactive menu."""
    print("\n" + "=" * 60)
    print("  WORLD CUP 2026 PREDICTION MODEL")
    print("  Hybrid Ensemble: Dixon-Coles + Squad Power + GBM")
    print("=" * 60)
    print()
    print("  1. Train model on historical data")
    print("  2. Predict single match")
    print("  3. Simulate full World Cup 2026")
    print("  4. Backtest on historical tournaments")
    print("  5. Export predictions to CSV")
    print("  6. Show team rankings (ELO + Squad)")
    print("  0. Exit")
    print()

    choice = input("  Select option: ").strip()
    return choice


def option_train():
    """Train the ensemble model on historical international matches."""
    print("\n--- Training Model ---")
    print("Collecting historical data (2014-2026)...")

    matches_df = collect_historical_matches(start_year=2014, end_year=2026)
    if matches_df.empty:
        print("ERROR: No match data found. Run the ELO scraper first.")
        return

    print(f"  {len(matches_df)} matches collected")

    rankings_by_year = collect_rankings_by_year(start_year=2014, end_year=2026)
    print(f"  Rankings collected for {len(rankings_by_year)} years")

    # Build feature matrix (ELO-only mode for training -- squad features
    # would require FotMob data for historical seasons)
    print("Building feature matrix...")
    X, y = build_training_matrix(matches_df, rankings_by_year)
    print(f"  {len(X)} training samples, {X.shape[1]} features")

    # Fit ensemble
    print("Fitting ensemble model...")
    predictor = MatchPredictor()
    predictor.fit(matches_df, X, y)

    # Save
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    predictor.save(str(MODEL_PATH))
    print(f"  Model saved to {MODEL_PATH}")


def option_predict():
    """Predict a single match."""
    predictor = _load_model()
    if predictor is None:
        return

    print("\n--- Single Match Prediction ---")
    team_a = input("  Team A: ").strip()
    team_b = input("  Team B: ").strip()

    if not team_a or not team_b:
        print("ERROR: Both team names required.")
        return

    from wrappers.elo_data import get_rankings
    rankings_df = get_rankings()

    # Empty squad features (ELO-only unless squad data is loaded)
    squad_features = {}

    pred = predictor.predict(
        team_a, team_b,
        rankings_df=rankings_df,
        squad_features=squad_features,
    )

    print(f"\n  {team_a} vs {team_b}")
    print(f"  ─────────────────────────────")
    print(f"  Win {team_a}:  {pred['p_win_a']:.1%}")
    print(f"  Draw:         {pred['p_draw']:.1%}")
    print(f"  Win {team_b}:  {pred['p_win_b']:.1%}")
    print(f"  Expected goals: {pred['lambda_a']:.2f} - {pred['lambda_b']:.2f}")
    print(f"  (DC: {pred['p_dc']['win_a']:.1%}/{pred['p_dc']['draw']:.1%}/{pred['p_dc']['win_b']:.1%})")
    print(f"  (GBM: {pred['p_gbm']['win_a']:.1%}/{pred['p_gbm']['draw']:.1%}/{pred['p_gbm']['win_b']:.1%})")


def option_simulate():
    """Simulate full World Cup 2026."""
    predictor = _load_model()
    if predictor is None:
        return

    print("\n--- World Cup 2026 Simulation ---")

    # Check if groups are filled
    tbd_count = sum(1 for teams in GROUPS.values() for t in teams if t == "TBD")
    if tbd_count > 0:
        print(f"WARNING: {tbd_count} TBD slots in group draw.")
        print("Update predictions/_config.py GROUPS after the official draw.")
        print("Running with available teams only...\n")

    from wrappers.elo_data import get_rankings
    rankings_df = get_rankings()
    squad_features = {}  # Load separately if available

    n_sims = MC_SIMULATIONS
    custom = input(f"  Simulations [{n_sims}]: ").strip()
    if custom.isdigit():
        n_sims = int(custom)

    print(f"Running {n_sims:,} simulations...")
    simulator = TournamentSimulator(
        predictor=predictor,
        rankings_df=rankings_df,
        squad_features=squad_features,
        n_simulations=n_sims,
    )

    results = simulator.simulate_tournament()

    # Display results
    tp = results["team_probabilities"]
    if not tp.empty:
        print("\n  CHAMPION PROBABILITIES (Top 15)")
        print("  " + "─" * 50)
        for _, row in tp.head(15).iterrows():
            print(
                f"  {row['team']:<20s} "
                f"Champ: {row.get('p_champion', 0):>5.1%}  "
                f"Final: {row.get('p_final', 0):>5.1%}  "
                f"SF: {row.get('p_sf', 0):>5.1%}"
            )

        # Group standings
        gs = results["group_standings"]
        if gs:
            print("\n  GROUP STANDINGS")
            print("  " + "─" * 50)
            for letter in sorted(gs.keys()):
                print(f"\n  Group {letter}:")
                for _, row in gs[letter].iterrows():
                    print(
                        f"    {row['team']:<20s} "
                        f"1st: {row['p_1st']:>5.1%}  "
                        f"2nd: {row['p_2nd']:>5.1%}  "
                        f"Pts: {row['avg_points']:.1f}"
                    )

    return results


def option_backtest():
    """Backtest on historical tournaments."""
    print("\n--- Backtesting ---")

    matches_df = collect_historical_matches(start_year=2014, end_year=2026)
    if matches_df.empty:
        print("ERROR: No match data. Run the ELO scraper first.")
        return

    rankings_by_year = collect_rankings_by_year(start_year=2014, end_year=2026)
    folds = prepare_backtest_data(matches_df, rankings_by_year)

    if not folds:
        print("ERROR: No backtest folds prepared.")
        return

    for fold in folds:
        print(f"\n  Fold: {fold['name']}")
        print(f"  Train: {len(fold['train_df'])} matches")
        print(f"  Test: {len(fold['test_df'])} matches")

        # Build features and train
        X_train, y_train = build_training_matrix(
            fold["train_df"], rankings_by_year
        )

        predictor = MatchPredictor()
        predictor.fit(fold["train_df"], X_train, y_train)

        # Backtest
        result = backtest_tournament(
            predictor=predictor,
            tournament_matches=fold["test_df"],
            rankings_df=fold["rankings_df"],
            squad_features={},
            tournament_name=fold["name"],
        )

        m = result["metrics"]
        print(f"  Results:")
        print(f"    Brier Score: {m['brier_score']:.4f} (random: {m['baseline_random_brier']:.4f}, ELO: {m['baseline_elo_brier']:.4f})")
        print(f"    Log Loss:    {m['log_loss']:.4f} (random: {m['baseline_random_ll']:.4f}, ELO: {m['baseline_elo_ll']:.4f})")
        print(f"    Accuracy:    {m['accuracy']:.1%}")
        print(f"    RPS:         {m['rps']:.4f}")

        # Save calibration plot
        try:
            fig = plot_calibration(result["calibration"], title=f"Calibration: {fold['name']}")
            PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
            fig_path = PREDICTIONS_DIR / f"calibration_{fold['name'].replace(' ', '_').lower()}.png"
            fig.savefig(fig_path, dpi=150, bbox_inches="tight")
            print(f"    Calibration plot: {fig_path}")
            import matplotlib.pyplot as plt
            plt.close(fig)
        except Exception as e:
            logger.debug("Could not save calibration plot: %s", e)


def option_export(results=None):
    """Export predictions to CSV."""
    if results is None:
        print("Run simulation first (option 3).")
        return

    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)

    tp = results.get("team_probabilities", pd.DataFrame())
    if not tp.empty:
        path = PREDICTIONS_DIR / "team_probabilities.csv"
        tp.to_csv(path, index=False)
        print(f"  Saved: {path}")

    mp = results.get("match_predictions", pd.DataFrame())
    if not mp.empty:
        path = PREDICTIONS_DIR / "match_predictions.csv"
        mp.to_csv(path, index=False)
        print(f"  Saved: {path}")

    gs = results.get("group_standings", {})
    if gs:
        frames = []
        for letter, df in gs.items():
            frames.append(df)
        all_gs = pd.concat(frames, ignore_index=True)
        path = PREDICTIONS_DIR / "group_standings.csv"
        all_gs.to_csv(path, index=False)
        print(f"  Saved: {path}")


def option_rankings():
    """Show current team rankings."""
    from wrappers.elo_data import get_rankings

    print("\n--- Current ELO Rankings (WC 2026 Qualified Teams) ---")
    rankings_df = get_rankings()

    if rankings_df.empty:
        print("ERROR: Could not fetch rankings.")
        return

    qualified = set(QUALIFIED_TEAMS.keys())
    rows = []
    for team in qualified:
        if team in rankings_df.index:
            row = rankings_df.loc[team]
            rows.append({
                "team": team,
                "elo_rank": row.get("elo_rank", "?"),
                "elo_rating": row.get("elo_rating", "?"),
                "elo_rating_3m_chg": row.get("elo_rating_3m_chg", 0),
                "confederation": QUALIFIED_TEAMS[team]["confederation"],
            })

    if rows:
        df = pd.DataFrame(rows).sort_values("elo_rank")
        print(f"\n  {'Team':<22s} {'Rank':>5s} {'Rating':>7s} {'3m Chg':>7s} {'Confed':<10s}")
        print("  " + "─" * 55)
        for _, r in df.iterrows():
            chg = r["elo_rating_3m_chg"]
            chg_str = f"+{chg}" if chg > 0 else str(chg)
            print(f"  {r['team']:<22s} {r['elo_rank']:>5} {r['elo_rating']:>7} {chg_str:>7s} {r['confederation']:<10s}")


def _load_model() -> MatchPredictor:
    """Load saved model or return None."""
    if not MODEL_PATH.exists():
        print(f"ERROR: No trained model found at {MODEL_PATH}")
        print("Run option 1 (Train) first.")
        return None
    return MatchPredictor.load(str(MODEL_PATH))


def main():
    """Main entry point."""
    sim_results = None

    while True:
        choice = menu()

        if choice == "1":
            option_train()
        elif choice == "2":
            option_predict()
        elif choice == "3":
            sim_results = option_simulate()
        elif choice == "4":
            option_backtest()
        elif choice == "5":
            option_export(sim_results)
        elif choice == "6":
            option_rankings()
        elif choice == "0":
            print("\nExiting.")
            break
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
