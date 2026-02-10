"""World Cup 2026 configuration: groups, bracket, venues, qualified teams.

The 2026 FIFA World Cup uses a 48-team format with 12 groups of 4.
Top 2 per group advance to a 32-team knockout bracket (R32 -> R16 -> QF -> SF -> F).
"""

from typing import Dict, List

# --------------------------------------------------------------------------
# Qualified teams (48) with confederation and 2-letter ELO codes
# --------------------------------------------------------------------------

QUALIFIED_TEAMS: Dict[str, Dict] = {
    # Host nations (automatic qualification)
    "United States":  {"confederation": "CONCACAF", "code": "us", "host": True},
    "Mexico":         {"confederation": "CONCACAF", "code": "mx", "host": True},
    "Canada":         {"confederation": "CONCACAF", "code": "ca", "host": True},
    # UEFA (16 spots)
    "Germany":        {"confederation": "UEFA", "code": "de", "host": False},
    "France":         {"confederation": "UEFA", "code": "fr", "host": False},
    "Spain":          {"confederation": "UEFA", "code": "es", "host": False},
    "England":        {"confederation": "UEFA", "code": "en", "host": False},
    "Portugal":       {"confederation": "UEFA", "code": "pt", "host": False},
    "Netherlands":    {"confederation": "UEFA", "code": "nl", "host": False},
    "Belgium":        {"confederation": "UEFA", "code": "be", "host": False},
    "Italy":          {"confederation": "UEFA", "code": "it", "host": False},
    "Croatia":        {"confederation": "UEFA", "code": "hr", "host": False},
    "Switzerland":    {"confederation": "UEFA", "code": "ch", "host": False},
    "Austria":        {"confederation": "UEFA", "code": "at", "host": False},
    "Denmark":        {"confederation": "UEFA", "code": "dk", "host": False},
    "Serbia":         {"confederation": "UEFA", "code": "rs", "host": False},
    "Turkey":         {"confederation": "UEFA", "code": "tr", "host": False},
    "Scotland":       {"confederation": "UEFA", "code": "sco", "host": False},
    "Slovenia":       {"confederation": "UEFA", "code": "si", "host": False},
    "Wales":          {"confederation": "UEFA", "code": "wa", "host": False},
    # CONMEBOL (6 spots)
    "Argentina":      {"confederation": "CONMEBOL", "code": "ar", "host": False},
    "Brazil":         {"confederation": "CONMEBOL", "code": "br", "host": False},
    "Uruguay":        {"confederation": "CONMEBOL", "code": "uy", "host": False},
    "Colombia":       {"confederation": "CONMEBOL", "code": "co", "host": False},
    "Ecuador":        {"confederation": "CONMEBOL", "code": "ec", "host": False},
    "Paraguay":       {"confederation": "CONMEBOL", "code": "py", "host": False},
    # CAF (9 spots)
    "Morocco":        {"confederation": "CAF", "code": "ma", "host": False},
    "Senegal":        {"confederation": "CAF", "code": "sn", "host": False},
    "Nigeria":        {"confederation": "CAF", "code": "ng", "host": False},
    "Egypt":          {"confederation": "CAF", "code": "eg", "host": False},
    "Cameroon":       {"confederation": "CAF", "code": "cm", "host": False},
    "South Africa":   {"confederation": "CAF", "code": "za", "host": False},
    "Algeria":        {"confederation": "CAF", "code": "dz", "host": False},
    "DR Congo":       {"confederation": "CAF", "code": "cd", "host": False},
    "Ivory Coast":    {"confederation": "CAF", "code": "ci", "host": False},
    # AFC (8 spots)
    "Japan":          {"confederation": "AFC", "code": "jp", "host": False},
    "South Korea":    {"confederation": "AFC", "code": "kr", "host": False},
    "Australia":      {"confederation": "AFC", "code": "au", "host": False},
    "Saudi Arabia":   {"confederation": "AFC", "code": "sa", "host": False},
    "Iran":           {"confederation": "AFC", "code": "ir", "host": False},
    "Iraq":           {"confederation": "AFC", "code": "iq", "host": False},
    "Qatar":          {"confederation": "AFC", "code": "qa", "host": False},
    "Uzbekistan":     {"confederation": "AFC", "code": "uz", "host": False},
    # CONCACAF (remaining)
    "Jamaica":        {"confederation": "CONCACAF", "code": "jm", "host": False},
    "Honduras":       {"confederation": "CONCACAF", "code": "hn", "host": False},
    "Panama":         {"confederation": "CONCACAF", "code": "pa", "host": False},
    # OFC (1-2 spots)
    "New Zealand":    {"confederation": "OFC", "code": "nz", "host": False},
    # Playoff/TBD slots -- update when confirmed
    # "TBD_1":        {"confederation": "TBD", "code": "??", "host": False},
}

# --------------------------------------------------------------------------
# Group draw (12 groups of 4) -- placeholder, update after official draw
# --------------------------------------------------------------------------

GROUPS: Dict[str, List[str]] = {
    "A": ["United States", "TBD", "TBD", "TBD"],
    "B": ["TBD", "TBD", "TBD", "TBD"],
    "C": ["TBD", "TBD", "TBD", "TBD"],
    "D": ["TBD", "TBD", "TBD", "TBD"],
    "E": ["Mexico", "TBD", "TBD", "TBD"],
    "F": ["TBD", "TBD", "TBD", "TBD"],
    "G": ["TBD", "TBD", "TBD", "TBD"],
    "H": ["TBD", "TBD", "TBD", "TBD"],
    "I": ["Canada", "TBD", "TBD", "TBD"],
    "J": ["TBD", "TBD", "TBD", "TBD"],
    "K": ["TBD", "TBD", "TBD", "TBD"],
    "L": ["TBD", "TBD", "TBD", "TBD"],
}

# --------------------------------------------------------------------------
# Knockout bracket topology (R32 -> Final)
# 48-team format: top 2 per group = 24 teams, +8 best 3rd-place = 32 in R32
# --------------------------------------------------------------------------

# R32 matchups: (group_position, group_position) pairs
# Official bracket TBD -- this follows FIFA's expected structure
KNOCKOUT_BRACKET = {
    "R32": [
        ("A1", "B3"), ("C1", "D3"), ("E1", "F3"), ("G1", "H3"),
        ("I1", "J3"), ("K1", "L3"), ("B1", "A3"), ("D1", "C3"),
        ("F1", "E3"), ("H1", "G3"), ("J1", "I3"), ("L1", "K3"),
        ("A2", "B2"), ("C2", "D2"), ("E2", "F2"), ("G2", "H2"),
    ],
    # Subsequent rounds pair winners: match 1 vs match 2, match 3 vs match 4, etc.
}

# --------------------------------------------------------------------------
# Host venues (16 stadiums across 3 countries)
# --------------------------------------------------------------------------

VENUES: Dict[str, Dict] = {
    # USA (11 venues)
    "MetLife Stadium":           {"city": "New York/New Jersey", "country": "United States", "capacity": 82500},
    "AT&T Stadium":              {"city": "Dallas", "country": "United States", "capacity": 80000},
    "SoFi Stadium":              {"city": "Los Angeles", "country": "United States", "capacity": 70240},
    "NRG Stadium":               {"city": "Houston", "country": "United States", "capacity": 72220},
    "Mercedes-Benz Stadium":     {"city": "Atlanta", "country": "United States", "capacity": 71000},
    "Hard Rock Stadium":         {"city": "Miami", "country": "United States", "capacity": 65326},
    "Lincoln Financial Field":   {"city": "Philadelphia", "country": "United States", "capacity": 69176},
    "Lumen Field":               {"city": "Seattle", "country": "United States", "capacity": 68740},
    "Gillette Stadium":          {"city": "Boston", "country": "United States", "capacity": 65878},
    "Arrowhead Stadium":         {"city": "Kansas City", "country": "United States", "capacity": 76416},
    "Levi's Stadium":            {"city": "San Francisco", "country": "United States", "capacity": 68500},
    # Mexico (3 venues)
    "Estadio Azteca":            {"city": "Mexico City", "country": "Mexico", "capacity": 87523},
    "Estadio BBVA":              {"city": "Monterrey", "country": "Mexico", "capacity": 53500},
    "Estadio Akron":             {"city": "Guadalajara", "country": "Mexico", "capacity": 49850},
    # Canada (2 venues)
    "BMO Field":                 {"city": "Toronto", "country": "Canada", "capacity": 30000},
    "BC Place":                  {"city": "Vancouver", "country": "Canada", "capacity": 54500},
}

HOST_COUNTRIES = {"United States", "Mexico", "Canada"}

# --------------------------------------------------------------------------
# Historical tournament data for backtesting
# --------------------------------------------------------------------------

BACKTEST_TOURNAMENTS = {
    "WC_2022": {
        "name": "FIFA World Cup 2022",
        "year": 2022,
        "teams": 32,
        "winner": "Argentina",
        "runner_up": "France",
    },
    "EURO_2024": {
        "name": "UEFA Euro 2024",
        "year": 2024,
        "teams": 24,
        "winner": "Spain",
        "runner_up": "England",
    },
    "WC_2018": {
        "name": "FIFA World Cup 2018",
        "year": 2018,
        "teams": 32,
        "winner": "France",
        "runner_up": "Croatia",
    },
}

# --------------------------------------------------------------------------
# Model hyperparameters
# --------------------------------------------------------------------------

# Dixon-Coles
DC_DECAY_RATE = 0.0065       # Exponential decay (half-life ~107 matches, ~2 years)
DC_MAX_GOALS = 8             # Max goals per team in score matrix
DC_RHO_INIT = -0.13          # Initial rho correction for low scores

# Ensemble weights (Dixon-Coles vs GBM)
ENSEMBLE_W_DC = 0.65
ENSEMBLE_W_GBM = 0.35

# GBM hyperparameters
GBM_PARAMS = {
    "n_estimators": 200,
    "max_depth": 4,
    "learning_rate": 0.05,
    "min_samples_leaf": 10,
    "subsample": 0.8,
    "random_state": 42,
}

# Monte Carlo
MC_SIMULATIONS = 100_000
MC_SEED = 42

# Extra time / penalties (based on WC 2006-2022 knockout data)
ET_PROB = 0.65               # P(decided in extra time | draw after 90 min)
PK_HOME_EDGE = 0.52          # Slight edge for higher-ranked team in penalties

# Squad builder
SQUAD_SIZE = 26
MIN_MINUTES = 450            # Minimum minutes played in current season
POSITIONS = {"GK": 3, "DEF": 8, "MID": 8, "FWD": 7}

# Position mapping from Transfermarkt abbreviations to categories
POSITION_TO_CATEGORY = {
    "GK": "GK",
    "CB": "DEF", "LB": "DEF", "RB": "DEF", "DF": "DEF",
    "CDM": "MID", "CM": "MID", "CAM": "MID", "LM": "MID", "RM": "MID", "MF": "MID",
    "LW": "FWD", "RW": "FWD", "ST": "FWD", "SS": "FWD", "FW": "FWD",
}

# Feature columns by source
ELO_FEATURES = [
    "elo_rating_diff", "elo_rating_avg_diff",
    "elo_rating_3m_chg_a", "elo_rating_3m_chg_b",
    "elo_rating_6m_chg_a", "elo_rating_6m_chg_b",
    "elo_rating_1y_chg_a", "elo_rating_1y_chg_b",
    "elo_win_pct_a", "elo_win_pct_b",
    "elo_goals_per_match_a", "elo_goals_per_match_b",
    "elo_form_momentum_a", "elo_form_momentum_b",
]

SQUAD_FEATURES = [
    "squad_avg_rating_a", "squad_avg_rating_b",
    "squad_attack_xg_a", "squad_attack_xg_b",
    "squad_attack_xa_a", "squad_attack_xa_b",
    "squad_defense_tackles_a", "squad_defense_tackles_b",
    "squad_defense_interceptions_a", "squad_defense_interceptions_b",
    "squad_gk_saves_a", "squad_gk_saves_b",
    "squad_gk_clean_sheet_a", "squad_gk_clean_sheet_b",
    "squad_total_market_value_a", "squad_total_market_value_b",
    "squad_median_market_value_a", "squad_median_market_value_b",
    "squad_top5_rating_a", "squad_top5_rating_b",
    "squad_big_league_pct_a", "squad_big_league_pct_b",
    "squad_avg_age_a", "squad_avg_age_b",
    "squad_depth_rating_std_a", "squad_depth_rating_std_b",
    "squad_avg_pass_accuracy_a", "squad_avg_pass_accuracy_b",
]

CONTEXT_FEATURES = [
    "tournament_stage", "is_host_a", "is_host_b",
    "rest_days_a", "rest_days_b",
    "group_match_number", "must_win_a", "must_win_b",
    "h2h_win_pct", "h2h_goal_diff", "h2h_matches",
]

ALL_FEATURES = ELO_FEATURES + SQUAD_FEATURES + CONTEXT_FEATURES
