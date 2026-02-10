"""Monte Carlo tournament simulator for World Cup 2026.

Simulates group stage + knockout bracket N times (default 100K) to produce
probability distributions for each team advancing to each round.
Uses vectorized NumPy for performance (~2 min for 100K simulations).
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ._config import (
    GROUPS,
    HOST_COUNTRIES,
    MC_SEED,
    MC_SIMULATIONS,
    QUALIFIED_TEAMS,
)
from .ensemble import MatchPredictor

logger = logging.getLogger(__name__)


class TournamentSimulator:
    """Monte Carlo simulator for 48-team World Cup.

    Parameters
    ----------
    predictor : MatchPredictor
        Fitted ensemble model.
    rankings_df : pd.DataFrame
        Current ELO rankings.
    squad_features : dict
        Squad features for all teams.
    n_simulations : int
        Number of Monte Carlo runs.
    seed : int
        Random seed for reproducibility.
    """

    def __init__(
        self,
        predictor: MatchPredictor,
        rankings_df: pd.DataFrame,
        squad_features: Dict[str, Dict[str, float]],
        n_simulations: int = MC_SIMULATIONS,
        seed: int = MC_SEED,
    ):
        self.predictor = predictor
        self.rankings_df = rankings_df
        self.squad_features = squad_features
        self.n_sims = n_simulations
        self.rng = np.random.default_rng(seed)
        self._match_cache: Dict[Tuple[str, str], Dict] = {}

    def simulate_tournament(
        self,
        groups: Optional[Dict[str, List[str]]] = None,
    ) -> Dict[str, Any]:
        """Run full tournament simulation.

        Parameters
        ----------
        groups : dict, optional
            Group assignments (default: GROUPS from config).

        Returns
        -------
        Dict with:
            - team_probabilities: DataFrame with P(advance), P(R16)..P(champion)
            - group_standings: Dict[group_letter -> DataFrame]
            - match_predictions: DataFrame with all group match predictions
        """
        if groups is None:
            groups = GROUPS

        # Validate groups have real teams (skip TBD placeholders)
        valid_groups = {}
        for letter, teams in groups.items():
            real_teams = [t for t in teams if t != "TBD"]
            if len(real_teams) >= 2:
                valid_groups[letter] = real_teams

        if not valid_groups:
            logger.error("No valid groups found. Provide groups with real team names.")
            return {"team_probabilities": pd.DataFrame(), "group_standings": {}, "match_predictions": pd.DataFrame()}

        logger.info("Simulating tournament: %d groups, %d simulations", len(valid_groups), self.n_sims)

        # Pre-compute all group match probabilities
        group_match_probs = self._precompute_group_matches(valid_groups)

        # Pre-compute match predictions for output
        match_predictions = self._build_match_predictions(valid_groups, group_match_probs)

        # Simulate group stages
        group_results = {}
        group_standings = {}
        for letter, teams in valid_groups.items():
            standings, positions = self._simulate_group(teams, group_match_probs, letter)
            group_results[letter] = positions  # {team: [finish_position per sim]}
            group_standings[letter] = standings

        # Collect group winners and runners-up for knockout
        team_probs = self._simulate_knockout(valid_groups, group_results)

        # Add group advance probabilities
        for team, probs in team_probs.items():
            for letter, positions in group_results.items():
                if team in positions:
                    finishes = positions[team]
                    probs["p_group_1st"] = float(np.mean(finishes == 1))
                    probs["p_group_2nd"] = float(np.mean(finishes == 2))
                    probs["p_group_3rd"] = float(np.mean(finishes == 3))
                    probs["p_group_advance"] = probs["p_group_1st"] + probs["p_group_2nd"]
                    break

        # Build output DataFrame
        prob_rows = []
        for team, probs in team_probs.items():
            row = {"team": team}
            row.update(probs)
            prob_rows.append(row)

        team_probabilities = pd.DataFrame(prob_rows)
        if not team_probabilities.empty:
            team_probabilities = team_probabilities.sort_values(
                "p_champion", ascending=False
            ).reset_index(drop=True)

        logger.info("Simulation complete. Top 5 favorites:")
        for _, row in team_probabilities.head(5).iterrows():
            logger.info(
                "  %s: %.1f%% champion, %.1f%% final",
                row["team"],
                row.get("p_champion", 0) * 100,
                row.get("p_final", 0) * 100,
            )

        return {
            "team_probabilities": team_probabilities,
            "group_standings": group_standings,
            "match_predictions": match_predictions,
        }

    def _precompute_group_matches(
        self,
        groups: Dict[str, List[str]],
    ) -> Dict[Tuple[str, str], Dict[str, float]]:
        """Pre-compute match probabilities for all group fixtures."""
        probs = {}
        for letter, teams in groups.items():
            for i in range(len(teams)):
                for j in range(i + 1, len(teams)):
                    key = (teams[i], teams[j])
                    if key not in self._match_cache:
                        pred = self.predictor.predict(
                            teams[i], teams[j],
                            rankings_df=self.rankings_df,
                            squad_features=self.squad_features,
                            stage=0,
                        )
                        self._match_cache[key] = pred
                    probs[key] = self._match_cache[key]
        logger.debug("Pre-computed %d group match probabilities", len(probs))
        return probs

    def _simulate_group(
        self,
        teams: List[str],
        match_probs: Dict[Tuple[str, str], Dict[str, float]],
        group_letter: str,
    ) -> Tuple[pd.DataFrame, Dict[str, np.ndarray]]:
        """Simulate a single group N times.

        Returns
        -------
        standings : pd.DataFrame
            Average standings with columns: team, avg_points, avg_gd,
            p_1st, p_2nd, p_3rd, p_4th.
        positions : dict
            {team: np.ndarray of finish positions (1-4) per simulation}.
        """
        n_teams = len(teams)
        n = self.n_sims

        # Points and goals arrays: shape (n_sims, n_teams)
        points = np.zeros((n, n_teams), dtype=np.int32)
        goals_for = np.zeros((n, n_teams), dtype=np.int32)
        goals_against = np.zeros((n, n_teams), dtype=np.int32)

        # Simulate each match
        for i in range(n_teams):
            for j in range(i + 1, n_teams):
                key = (teams[i], teams[j])
                pred = match_probs.get(key)
                if pred is None:
                    logger.warning("No pre-computed probability for %s vs %s, using uniform", teams[i], teams[j])
                    pred = {"p_win_a": 0.33, "p_draw": 0.34, "p_win_b": 0.33, "lambda_a": 1.2, "lambda_b": 1.0}
                p_w = pred["p_win_a"]
                p_d = pred["p_draw"]

                lambda_a = pred.get("lambda_a", 1.2)
                lambda_b = pred.get("lambda_b", 1.0)

                # Sample outcomes
                rand = self.rng.random(n)
                win_a = rand < p_w
                draw = (rand >= p_w) & (rand < p_w + p_d)
                win_b = ~win_a & ~draw

                # Points
                points[:, i] += 3 * win_a.astype(np.int32) + draw.astype(np.int32)
                points[:, j] += 3 * win_b.astype(np.int32) + draw.astype(np.int32)

                # Goals (sample from Poisson for goal difference)
                ga = self.rng.poisson(lambda_a, n).astype(np.int32)
                gb = self.rng.poisson(lambda_b, n).astype(np.int32)

                # Adjust goals to be consistent with result
                # If win_a but ga <= gb, set ga = gb + 1
                fix_a = win_a & (ga <= gb)
                ga[fix_a] = gb[fix_a] + 1
                # If win_b but gb <= ga, set gb = ga + 1
                fix_b = win_b & (gb <= ga)
                gb[fix_b] = ga[fix_b] + 1
                # If draw but ga != gb, set gb = ga
                ga[draw] = np.minimum(ga[draw], gb[draw])
                gb[draw] = ga[draw]

                goals_for[:, i] += ga
                goals_against[:, i] += gb
                goals_for[:, j] += gb
                goals_against[:, j] += ga

        # Determine positions per simulation
        goal_diff = goals_for - goals_against
        # Composite sort key: points * 1000 + gd * 10 + gf (breaks ties)
        sort_key = points * 10000 + (goal_diff + 500) * 10 + goals_for
        # Rank teams per simulation (argsort descending)
        positions = {}
        for sim in range(n):
            order = np.argsort(-sort_key[sim])
            for rank, idx in enumerate(order):
                team = teams[idx]
                if team not in positions:
                    positions[team] = np.zeros(n, dtype=np.int32)
                positions[team][sim] = rank + 1  # 1-indexed

        # Build standings summary
        rows = []
        for idx, team in enumerate(teams):
            pos = positions.get(team, np.full(n, 4))
            rows.append({
                "team": team,
                "group": group_letter,
                "avg_points": float(points[:, idx].mean()),
                "avg_gd": float(goal_diff[:, idx].mean()),
                "avg_gf": float(goals_for[:, idx].mean()),
                "p_1st": float(np.mean(pos == 1)),
                "p_2nd": float(np.mean(pos == 2)),
                "p_3rd": float(np.mean(pos == 3)),
                "p_4th": float(np.mean(pos == 4)) if n_teams >= 4 else 0.0,
            })

        standings = pd.DataFrame(rows).sort_values("p_1st", ascending=False).reset_index(drop=True)
        return standings, positions

    def _simulate_knockout(
        self,
        groups: Dict[str, List[str]],
        group_results: Dict[str, Dict[str, np.ndarray]],
    ) -> Dict[str, Dict[str, float]]:
        """Simulate knockout bracket from group results.

        Collects group winners and runners-up, then runs a generic
        single-elimination bracket. Works for any number of groups.

        Returns
        -------
        Dict mapping team -> {p_r32, p_r16, p_qf, p_sf, p_final, p_champion}.
        """
        n = self.n_sims
        all_teams = set()
        for teams_dict in group_results.values():
            all_teams.update(teams_dict.keys())

        # Initialize counters
        counters = {team: {
            "p_r32": 0, "p_r16": 0, "p_qf": 0,
            "p_sf": 0, "p_final": 0, "p_champion": 0,
        } for team in all_teams}

        # Round labels by depth (from R32 inward)
        round_labels = ["p_r32", "p_r16", "p_qf", "p_sf", "p_final", "p_champion"]
        group_letters = sorted(groups.keys())

        for sim in range(n):
            # Get group winners and runners-up for this simulation
            winners = []
            runners_up = []

            for letter in group_letters:
                teams_pos = group_results[letter]
                w, r = None, None
                for team, positions in teams_pos.items():
                    if positions[sim] == 1:
                        w = team
                    elif positions[sim] == 2:
                        r = team
                if w:
                    winners.append(w)
                if r:
                    runners_up.append(r)

            # Build initial bracket: cross-pair winners vs runners-up
            bracket_teams = []
            n_pairs = min(len(winners), len(runners_up))
            for i in range(n_pairs):
                j = (n_pairs - 1 - i)  # Cross-pairing
                bracket_teams.append(winners[i])
                bracket_teams.append(runners_up[j])

            # Generic single-elimination bracket
            current_round = bracket_teams
            round_idx = 0
            stage = 1

            while len(current_round) > 1:
                # Determine round label
                rounds_remaining = 0
                t = len(current_round)
                while t > 1:
                    t = (t + 1) // 2
                    rounds_remaining += 1
                label_idx = max(0, len(round_labels) - rounds_remaining - 1)
                round_label = round_labels[min(label_idx, len(round_labels) - 1)]

                # Mark participation in this round
                for team in current_round:
                    if team in counters and round_label != "p_champion":
                        counters[team][round_label] += 1

                # Play matches
                next_round = []
                for i in range(0, len(current_round) - 1, 2):
                    team_a = current_round[i]
                    team_b = current_round[i + 1]
                    winner = self._simulate_knockout_match(team_a, team_b, stage=stage)
                    next_round.append(winner)

                # Odd team gets a bye
                if len(current_round) % 2 == 1:
                    next_round.append(current_round[-1])

                current_round = next_round
                stage += 1

            # Champion
            if current_round:
                counters[current_round[0]]["p_champion"] += 1

        # Normalize
        for team in counters:
            for key in counters[team]:
                counters[team][key] /= n

        return counters

    def _simulate_knockout_match(
        self,
        team_a: str,
        team_b: str,
        stage: int,
    ) -> str:
        """Simulate a single knockout match, return winner."""
        cache_key = (team_a, team_b, stage)
        if cache_key not in self._match_cache:
            pred = self.predictor.predict_knockout(
                team_a, team_b,
                rankings_df=self.rankings_df,
                squad_features=self.squad_features,
                stage=stage,
            )
            self._match_cache[cache_key] = pred

        pred = self._match_cache[cache_key]
        p_a = pred["p_advance_a"]

        if self.rng.random() < p_a:
            return team_a
        return team_b

    def _build_match_predictions(
        self,
        groups: Dict[str, List[str]],
        match_probs: Dict[Tuple[str, str], Dict[str, float]],
    ) -> pd.DataFrame:
        """Build DataFrame of all group match predictions."""
        rows = []
        for letter, teams in groups.items():
            match_num = 0
            for i in range(len(teams)):
                for j in range(i + 1, len(teams)):
                    match_num += 1
                    key = (teams[i], teams[j])
                    pred = match_probs.get(key, {})
                    rows.append({
                        "group": letter,
                        "match_number": match_num,
                        "team_a": teams[i],
                        "team_b": teams[j],
                        "stage": "group",
                        "p_win_a": pred.get("p_win_a", 0.0),
                        "p_draw": pred.get("p_draw", 0.0),
                        "p_win_b": pred.get("p_win_b", 0.0),
                        "lambda_a": pred.get("lambda_a", 0.0),
                        "lambda_b": pred.get("lambda_b", 0.0),
                    })
        return pd.DataFrame(rows)
