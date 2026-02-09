# FootballDecoded Wrappers - Technical Documentation

## Table of Contents
1. [FotMob Wrapper](#fotmob-wrapper)
2. [Understat Wrapper](#understat-wrapper)
3. [WhoScored Wrapper](#whoscored-wrapper)
4. [Transfermarkt Wrapper](#transfermarkt-wrapper)

---

# FotMob Wrapper

Primary data source for season statistics. Provides player and team stats for ALL 16 supported leagues via JSON API.

## fotmob_data.py

### Functions

#### `fotmob_get_player_stats(league, season)` -> pd.DataFrame
Fetch all player season stats (35 metrics) for a league/season.

#### `fotmob_get_team_stats(league, season)` -> pd.DataFrame
Fetch all team season stats (27 metrics) for a league/season.

#### `fotmob_get_league_stats(league, season)` -> dict
Returns `{'players': DataFrame, 'teams': DataFrame}`.

### Player Stats (35 metrics, prefixed `fotmob_`)
- goals, goal_assist, goals_and_goal_assist, rating, mins_played
- goals_per_90, expected_goals, expected_goals_per_90
- expected_goalsontarget, ontarget_scoring_att, total_scoring_att
- accurate_pass, big_chance_created, total_att_assist, accurate_long_balls
- expected_assists, expected_assists_per_90, expected_goals_and_expected_assists_per_90
- won_contest, big_chance_missed, penalty_won
- total_tackle, interception, effective_clearance, outfielder_block
- penalty_conceded, poss_won_att_3rd
- clean_sheet, save_percentage, saves, goals_prevented, goals_conceded
- fouls, yellow_card, red_card

### Team Stats (27 metrics, prefixed `fotmob_`)
- rating_team, goals_team_match, goals_conceded_team_match
- possession_percentage_team, clean_sheet_team, home_attendance_team
- expected_goals_team, xg_diff_team
- ontarget_scoring_att_team, big_chance_team, big_chance_missed_team
- accurate_pass_team, accurate_long_balls_team, accurate_cross_team
- penalty_won_team, touches_in_opp_box_team, corner_taken_team
- expected_goals_conceded_team
- interception_team, total_tackle_team, effective_clearance_team
- poss_won_att_3rd_team, penalty_conceded_team, saves_team
- fk_foul_lost_team, total_yel_card_team, total_red_card_team

### Coverage
ALL 16 leagues: ENG, ESP, ITA, GER, FRA, UCL, WC, EURO, WWC, POR, NED, BEL, TUR, SCO, SUI, MLS

---

# Understat Wrapper

Advanced metrics exclusive to Understat. Big 5 leagues only (ENG, ESP, ITA, GER, FRA).

## understat_data.py

### Core Functions

#### `understat_get_player(player_name, league, season)` -> Optional[Dict]
Extract advanced player metrics.

Returns:
```python
{
    'player_name': str,
    'team': str,
    'understat_xg_chain': float,        # xG in chains where player participates
    'understat_xg_buildup': float,       # xG in build-up (excl. shot/assist)
    'understat_buildup_involvement_pct': float,
    'understat_npxg_plus_xa': float,     # Non-penalty xG + xA
    'understat_key_passes': int,
    'understat_np_xg': float,
    'understat_xa': float,
    'understat_np_goals': int,
    'understat_player_id': int,
    'understat_team_id': int
}
```

#### `understat_get_team(team_name, league, season)` -> Optional[Dict]
Extract team-level metrics.

Returns:
```python
{
    'team_name': str,
    'understat_ppda_avg': float,         # Passes Per Defensive Action
    'understat_ppda_std': float,
    'understat_deep_completions_total': int,
    'understat_deep_completions_avg': float,
    'understat_expected_points_total': float,
    'understat_expected_points_avg': float,
    'understat_points_efficiency': float,
    'understat_np_xg_total': float,
    'understat_np_xg_avg': float,
    'understat_matches_analyzed': int
}
```

#### `get_team_advanced(team_name, league, season)` -> Dict
Extract advanced team stats from Understat's getTeamData API.

Returns ~200 keys across 7 categories:
- **situation**: Open Play, Set Piece, Counter, Penalty, From Corner
- **formation**: Stats per formation used
- **gameState**: Winning, Drawing, Losing
- **timing**: 0-15, 15-30, 30-45, 45-60, 60-75, 75-90 minutes
- **shotZone**: Inside Box, Outside Box, Penalty Area Edge
- **attackSpeed**: Normal, Standard, Fast, Slow
- **result**: Win, Draw, Loss

Each sub-key has: shots, goals, xG, and against variants.

#### `get_player_shots(player_name, league, season)` -> pd.DataFrame
Extract shot events for a player in a season.

Returns DataFrame with columns: minute, xG, result, x, y, situation, shotType, match_id, etc.

### Batch Functions

#### `understat_get_players(players, league, season)` -> pd.DataFrame
#### `understat_get_teams(teams, league, season)` -> pd.DataFrame

### Shot Events

#### `understat_get_shots(match_id, league, season)` -> pd.DataFrame
Shot events with coordinates and xG (25 columns).

### Coverage
Big 5 only: ENG-Premier League, ESP-La Liga, ITA-Serie A, GER-Bundesliga, FRA-Ligue 1

---

# WhoScored Wrapper

Spatial event data with x/y coordinates. Selenium-based scraping.

## whoscored_data.py

### Core Functions

#### `whoscored_extract_match_events(match_id, league, season)` -> pd.DataFrame
All match events with spatial coordinates (42 columns).

Key columns:
- `x`, `y`, `end_x`, `end_y`: Opta coordinates (0-100)
- `event_type`: Pass, Shot, Tackle, Carry, etc.
- `outcome_type`: Successful / Unsuccessful
- `field_zone`: 9-zone classification
- `distance_to_goal`, `pass_distance`: Calculated metrics

#### `whoscored_extract_pass_network(match_id, team, league, season)` -> Dict
Returns `{'passes': DataFrame, 'positions': DataFrame, 'connections': DataFrame}`.

#### `whoscored_extract_player_heatmap(match_id, player_name, league, season)` -> pd.DataFrame
Zone-based activity distribution (9 columns).

#### `whoscored_extract_shot_map(match_id, league, season)` -> pd.DataFrame
Shot events with zone classification.

#### `whoscored_extract_field_occupation(match_id, team, league, season)` -> pd.DataFrame
Spatial occupation analysis (8 columns).

#### `whoscored_extract_league_schedule(league, season)` -> pd.DataFrame
Full league schedule with results (43 columns).

#### `whoscored_extract_missing_players(match_id, league, season)` -> pd.DataFrame
Injured/suspended players.

### Quick Access Functions
- `whoscored_get_match_events()`, `whoscored_get_match_events_viz()`
- `whoscored_get_pass_network()`, `whoscored_get_player_heatmap()`
- `whoscored_get_shot_map()`, `whoscored_get_field_occupation()`
- `whoscored_get_schedule()`, `whoscored_get_missing_players()`

### Coordinate System
- Origin (0,0): Bottom-left of own half
- X: 0-100 (left to right), Y: 0-100 (bottom to top)
- Own goal: X=0, Opponent goal: X=100

### Coverage
All leagues with WhoScored mapping in LEAGUE_DICT.

---

# Transfermarkt Wrapper

Player profiles, market values, and contract details.

## transfermarkt_data.py

### Functions

#### `transfermarkt_get_player(player_name, league, season, birth_year)` -> Optional[Dict]
Returns:
```python
{
    'transfermarkt_position_specific': str,   # LW, CB, CDM, etc.
    'transfermarkt_primary_foot': str,        # Right, Left, Both
    'transfermarkt_market_value_eur': int,    # Market value in EUR
    'transfermarkt_birth_date': str,          # YYYY-MM-DD
    'transfermarkt_current_club': str,
    'transfermarkt_contract_expires': str,    # YYYY-MM-DD
    'transfermarkt_player_id': str,
    'transfermarkt_contract_is_current': bool, # True if season >= 25-26
    'transfermarkt_market_value_date': str    # When the value was recorded
}
```

#### `clear_cache()`
Clear in-memory player ID cache.

### Market Value Logic
- Season 25-26 and later: uses CURRENT market value
- Earlier seasons: uses HISTORICAL value from season end date

### Coverage
All leagues (searches by player name globally).

---

## Usage Notes

### Wrapper Compatibility
The four wrappers work together in the v2 pipeline:
1. **FotMob**: Bulk season stats (primary source for all leagues)
2. **Understat**: Advanced metrics merge (Big 5 only)
3. **Transfermarkt**: Player profile enrichment
4. **WhoScored**: Match-level spatial events (for visualization)

### Example: v2 Pipeline
```python
from wrappers.fotmob_data import fotmob_get_league_stats
from wrappers.understat_data import understat_get_player, get_team_advanced
from wrappers.transfermarkt_data import transfermarkt_get_player

# 1. Bulk load from FotMob
stats = fotmob_get_league_stats("ESP-La Liga", "24-25")
players_df = stats['players']
teams_df = stats['teams']

# 2. Enrich with Understat (Big 5 only)
us_data = understat_get_player("Vinicius Junior", "ESP-La Liga", "24-25")
adv_data = get_team_advanced("Barcelona", "ESP-La Liga", "24-25")

# 3. Enrich with Transfermarkt
tm_data = transfermarkt_get_player("Vinicius Junior", "ESP-La Liga", "24-25", 2000)
```

### Performance Notes
- FotMob: 3-5s between requests (JSON API, fast)
- Understat: 5s between requests
- WhoScored: 10s between requests (Selenium)
- Transfermarkt: 3-5s between requests
