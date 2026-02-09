# CLAUDE.md - FootballDecoded Development Guide

---

## Core Philosophy

Ve paso a paso, uno a uno. Despacio es el camino mas rapido. Escribe siempre el codigo lo mas compacto y conciso posible, y que cumpla exactamente lo pedido al 100%. Sin emojis ni florituras. Usa nombres claros y estandar. Incluye solo comentarios utiles y necesarios.

Antes de realizar cualquier tarea, revisa cuidadosamente el archivo CLAUDE.md.

source ~/anaconda3/bin/activate footballdecoded && python3

### Development Principles

- **KISS**: Choose straightforward solutions over complex ones
- **YAGNI**: Implement features only when needed
- **Fail Fast**: Check for errors early and raise exceptions immediately
- **Single Responsibility**: Each function, class, and module has one clear purpose
- **Dependency Inversion**: High-level modules depend on abstractions, not implementations

## Repository Structure

```
FootballDecoded/
├── scrappers/              # Data extraction (~3,500 lines)
│   ├── _common.py          # Base classes: cache, rate limit, TLS (703 lines)
│   ├── _config.py          # LEAGUE_DICT, logging, directories (267 lines)
│   ├── _utils.py           # Name normalization, distance calc (35 lines)
│   ├── fotmob.py           # FotMob API: 35 player + 27 team stats (441 lines)
│   ├── understat.py        # Understat: xG, PPDA, advanced stats (846 lines)
│   ├── whoscored.py        # WhoScored: spatial events with x/y coords (737 lines)
│   └── transfermarkt.py    # Transfermarkt: profiles, market values (460 lines)
│
├── wrappers/               # Simplified API (~2,400 lines)
│   ├── README.md           # Complete API documentation
│   ├── fotmob_data.py      # FotMob: league players/teams extraction (293 lines)
│   ├── understat_data.py   # Understat: metrics + advanced + shots (739 lines)
│   ├── whoscored_data.py   # WhoScored: spatial analysis (1,130 lines)
│   └── transfermarkt_data.py  # Transfermarkt: player profiles (100 lines)
│
├── database/               # PostgreSQL layer (~4,000 lines)
│   ├── connection.py       # Pool, retry logic, v1 + v2 insert methods (603 lines)
│   ├── data_loader.py      # v1 loader: FBref-based, legacy (1,119 lines)
│   ├── data_loader_v2.py   # v2 loader: FotMob + Understat + Transfermarkt (960 lines)
│   ├── database_checker.py # v1 health checker, legacy (941 lines)
│   ├── database_checker_v2.py # v2 health checker (425 lines)
│   ├── setup.sql           # v1 schema: 4 tables (307 lines, legacy)
│   ├── setup_extras.sql    # v1 extras: 2 tables (155 lines, legacy)
│   └── setup_v2.sql        # v2 schema: 4 tables, 22 indexes (264 lines)
│
├── viz/                    # Visualization (~6,800 lines)
│   ├── templates/          # 7 Jupyter notebooks
│   ├── match_data.py       # 10-step pipeline, 5 CSV outputs, Understat xG (979 lines)
│   ├── match_data_v2.py    # 10-step pipeline, 5 CSV outputs, SofaScore xG (1,005 lines)
│   ├── pass_network.py     # Pass network plots (1,253 lines)
│   ├── pass_analysis.py    # Pass flow + hull analysis (685 lines)
│   ├── swarm_radar.py      # Player comparison radars (415 lines)
│   ├── stats_table.py      # Statistical tables (353 lines)
│   ├── scatter.py          # Scatter plots (336 lines)
│   ├── stats_radar.py      # Radar charts (316 lines)
│   ├── shot_map_report.py  # Shot map reports (297 lines)
│   ├── shot_xg.py          # xG shot maps (226 lines)
│   ├── impact_timeline.py  # Impact timelines (196 lines)
│   ├── assisted_goals.py   # Assisted goals maps (189 lines)
│   ├── dribbles_heatmap.py # Dribble heatmaps (175 lines)
│   ├── goals_origin.py     # Goal origin maps (175 lines)
│   └── assist_passes.py    # Assist pass visualizations (162 lines)
│
└── blog/                   # Assets & Utilities
    ├── logos/              # Team logos (6 leagues)
    ├── caras/              # Player face photos
    └── get_match_ids.py    # Match ID extractor: WhoScored/Understat (221 lines)
```

## Quick Start

### 1. Environment Setup

```bash
conda env create -f environment.yml
conda activate footballdecoded
```

### 2. Database Setup

```bash
# Configure .env with DB credentials
cat > .env << EOF
DB_HOST=localhost
DB_PORT=5432
DB_NAME=footballdecoded
DB_USER=your_user
DB_PASSWORD=your_password
EOF

# Setup v2 schema
psql -U your_user -d footballdecoded -f database/setup_v2.sql
```

### 3. Load Data (v2)

```bash
python database/data_loader_v2.py
# Option 1: Single league
# Option 2: Block 1 (ENG+ESP+ITA)
# Option 3: Block 2 (GER+FRA+UCL)
# Option 4: Block 3 (7 extras)
# Option 5: All leagues
# Option 6: Setup database schema
```

### 4. First Visualization

**Big 5 Leagues (Understat xG):**
```python
from viz.match_data import extract_match_complete

result = extract_match_complete(
    ws_id=1821769,
    us_id=16364,
    league="ESP-La Liga",
    season="24-25",
    home_team="Athletic Club",
    away_team="Barcelona",
    match_date="2024-08-24"
)
# Generates 5 CSVs: events, aggregates, network, spatial, info
```

**Other Leagues (SofaScore xG):**
```python
from viz.match_data_v2 import extract_match_complete_v2

result = extract_match_complete_v2(
    ws_id=1953302,
    ss_id=14924703,
    league="USA-MLS",
    season="25-26",
    home_team="Inter Miami CF",
    away_team="Vancouver Whitecaps",
    match_date="2024-12-06"
)
# Generates 5 CSVs: events, aggregates, network, spatial, info
```

**Generate visualization:**
```python
from viz.pass_network import plot_pass_network
fig = plot_pass_network(
    csv_path='viz/data/player_network.csv',
    team_name='Barcelona'
)
fig.savefig('barcelona_network.png', dpi=300)
```

## Data Pipeline Architecture

```
DATA SOURCES
    FotMob (all 16 leagues) | Understat (Big 5) | Transfermarkt (all) | WhoScored (spatial)
    |
EXTRACTION (scrappers/)
    - FotMob: JSON API, 3-5s rate limit
    - Understat: AJAX API, 5s rate limit
    - WhoScored: Selenium, 10s rate limit
    - Transfermarkt: HTTP scraping, 5s rate limit
    - Cache: 30 days (raw API responses on disk)
    |
SIMPLIFICATION (wrappers/)
    - fotmob_data: league-wide player/team season stats
    - understat_data: xG metrics + advanced breakdown + shots
    - whoscored_data: spatial events + pass networks
    - transfermarkt_data: player profiles + market values
    - No pickle cache (always fresh data from scraper cache)
    |
STORAGE (database/)
    - v2 schema: 4 tables (players, teams, matches, shots)
    - JSONB metrics: fotmob (29 keys), understat (27), transfermarkt (9)
    - Pipeline: FotMob bulk -> Understat merge -> Transfermarkt enrich
    - SHA256 unique IDs (16-char hex)
    |
VISUALIZATION (viz/)
    - 10-step match enrichment pipeline
    - 5 optimized CSVs per match
    - 15 plot modules (pass networks, xG maps, radars, scatter, timelines)
```

**xG Data Source Selection (match-level):**
- **Big 5 Leagues**: Understat via match_data.py
- **Other Leagues** (MLS, Portugal, etc.): SofaScore via match_data_v2.py

## Module Overview

### Scrapers (scrappers/)

**Base Classes** (_common.py):
- `BaseReader`: File cache (30-day), download/retry logic
- `BaseRequestsReader`: HTTP with TLS evasion, User-Agent rotation
- `BaseSeleniumReader`: Browser automation (WhoScored)

**Sources**:
- **FotMob** (fotmob.py): 35 player + 27 team stat keys, all 16 leagues, JSON API
- **Understat** (understat.py): xG Chain, PPDA, 7 advanced categories, shot events, Big 5 only
- **WhoScored** (whoscored.py): Event data with x/y coordinates (0-100), Selenium-based
- **Transfermarkt** (transfermarkt.py): Market values, positions, contracts, fuzzy search

**Config** (_config.py):
- `LEAGUE_DICT`: 23 competition entries with source mappings (FotMob, Understat, WhoScored keys)
- 16 leagues have FotMob IDs, 5 have Understat, all have WhoScored
- Rate limits, cache settings, team name replacements

### Wrappers (wrappers/)

**See wrappers/README.md for complete API reference**

**FotMob** (fotmob_data.py):
- `get_league_players()`: All players in league with 35 stats
- `get_league_teams()`: All teams in league with 27 stats
- Prefix: `fotmob_*` | Coverage: all 16 leagues

**Understat** (understat_data.py):
- `get_player()`, `get_team()`: Season metrics (xG, PPDA, xG Chain)
- `get_team_advanced()`: 7 category breakdown (~200 keys)
- `get_player_shots()`: Shot events with xG and coordinates
- `get_shots()`: Match-level shot events
- Prefix: `understat_*` | Coverage: Big 5 only

**WhoScored** (whoscored_data.py):
- `get_match_events()`: All events with x/y coords (42 columns)
- `get_pass_network()`: Pass network (passes, positions, connections)
- `get_shot_map()`, `get_field_occupation()`, `get_player_heatmap()`
- Coverage: all leagues with WhoScored mapping

**Transfermarkt** (transfermarkt_data.py):
- `get_player()`: Position, foot, market value, contract, birth date
- Prefix: `transfermarkt_*` | Coverage: all leagues

### Database (database/)

**v2 Schema** (`footballdecoded_v2`, 4 tables):
- `players`: One row per player per league per season
- `teams`: One row per team per league per season
- `understat_team_matches`: One row per team per match (Big 5 only)
- `understat_shots`: One row per shot event (Big 5 only)

**v1 Schema** (`footballdecoded`, legacy, read-only):
- `players_domestic` / `teams_domestic`: Big 5 leagues (FBref-based)
- `players_european` / `teams_european`: International
- `players_extras` / `teams_extras`: 7 additional leagues

**Unique ID System**:
- Players: SHA256(name + birth_year + nationality) -> 16-char hex
- Teams: SHA256(team_name + league) -> 16-char hex

**v2 JSONB Fields**:
- `fotmob_metrics`: 29 keys (goals, xG, xA, rating, tackles...)
- `understat_metrics`: 27 keys (xG chain, buildup, per90s...) NULL for non-Big5
- `transfermarkt_metrics`: 9 keys (position, foot, market value, contract...)
- `understat_advanced`: ~200 keys (7 categories) teams only, Big 5 only
- `data_quality_score`: 0.00-1.00

**CLI Tools**:
```bash
# v2 health monitoring
python database/database_checker_v2.py --quick    # Row counts
python database/database_checker_v2.py --health   # Health score (0-100)
python database/database_checker_v2.py --problems # Detect issues
python database/database_checker_v2.py --full     # Complete analysis

# v2 data loading
python database/data_loader_v2.py                 # Interactive menu
```

**Connection** (connection.py):
- Pool: 5 connections + 10 overflow (SQLAlchemy QueuePool)
- Retry with exponential backoff (3 attempts)
- `DatabaseManager` singleton
- v1 + v2 insert methods

**v2 Loading Pipeline** (data_loader_v2.py):
1. FotMob bulk (all leagues) -> base player/team records
2. Understat merge (Big 5 only) -> player/team advanced metrics
3. Transfermarkt enrich (all leagues) -> player profiles
4. Insert with SHA256 IDs and quality scoring
- Checkpoints every 25 records, adaptive rate limiting

### Visualization (viz/)

**See viz/README.md for complete documentation**

**match_data.py** - Core Processing (Understat xG):
- 10-step enrichment pipeline
- Outputs 5 CSVs: events (55 cols), aggregates (36), network (18), spatial (29), info (11)
- Use for: Big 5 leagues

**match_data_v2.py** - Core Processing (SofaScore xG):
- Same 10-step pipeline, identical CSV structure
- Use for: MLS, Portugal, and other non-Big 5 leagues

**Plot Modules (15 files)**:
| Module | Description |
|--------|-------------|
| pass_network.py | Pass network with positions and connections |
| pass_analysis.py | Pass flow arrows and convex hull zones |
| swarm_radar.py | Player comparison bee-swarm radars |
| stats_table.py | Statistical comparison tables |
| scatter.py | Diamond scatter plots with percentile labels |
| stats_radar.py | Radar charts |
| shot_map_report.py | Shot report with xG colormap |
| shot_xg.py | xG shot maps on pitch |
| impact_timeline.py | Match timeline with event markers |
| assisted_goals.py | Assisted goal maps |
| dribbles_heatmap.py | Dribble KDE heatmaps |
| goals_origin.py | Goal origin maps with markers |
| assist_passes.py | Assist pass arrows with xG scaling |

**Design System**:
- Colormap: deepskyblue -> tomato
- Background: #313332
- Typography: DejaVu Sans

**Templates**: 7 Jupyter notebooks in viz/templates/

### Utilities (blog/)

**get_match_ids.py** - Match ID Extractor:
```python
from blog.get_match_ids import extract_match_ids

ids = extract_match_ids(
    team_name="Inter Miami",
    league="USA-MLS",
    season="2025",
    sources=['whoscored']  # or ['understat'] for Big 5
)
```
Returns: DataFrame with match_id, date, home_team, away_team, league, season

## Supported Competitions

### Big 5 Leagues
| League | Code | FotMob | Understat | Transfermarkt |
|--------|------|--------|-----------|---------------|
| Premier League | ENG-Premier League | Yes | Yes | Yes |
| La Liga | ESP-La Liga | Yes | Yes | Yes |
| Serie A | ITA-Serie A | Yes | Yes | Yes |
| Bundesliga | GER-Bundesliga | Yes | Yes | Yes |
| Ligue 1 | FRA-Ligue 1 | Yes | Yes | Yes |

### International
- Champions League (INT-Champions League): FotMob
- World Cup (INT-World Cup): FotMob
- European Championship (INT-European Championship): FotMob

### Extras (7 leagues)
Portugal, Netherlands, Belgium, Turkey, Scotland, Switzerland, USA
- FotMob: Yes (all 7)
- Understat: No (Big 5 only)
- Transfermarkt: Yes (all 7)

### FotMob League IDs
47:ENG, 87:ESP, 55:ITA, 54:GER, 53:FRA, 42:UCL, 77:WC, 50:EURO, 76:WWC, 61:POR, 57:NED, 40:BEL, 71:TUR, 64:SCO, 69:SUI, 130:MLS

**Season Formats**:
- Multi-year: `24-25` or `2425` (domestic leagues, UCL)
- Single-year: `2022` (World Cup, Euros)
- FotMob season IDs: numeric (e.g. 23686 for La Liga 2024/2025)

## Development Standards

### Code Style

```python
# Naming
user_name = "example"          # snake_case
class UserManager:              # PascalCase
MAX_RETRY = 3                  # UPPER_CASE
_internal_method()             # Leading _ for private

# Type hints required
def process_data(data: List[Dict]) -> pd.DataFrame:
    """Process with clear types."""

# Docstrings mandatory for public functions
def extract_data(league: str, season: str) -> Dict[str, Any]:
    """Extract data from source.

    Args:
        league: League identifier (e.g. "ESP-La Liga")
        season: Season in YY-YY format (e.g. "24-25")

    Returns:
        Dictionary with extracted data
    """
```

### Error Handling

```python
# Specific exceptions
try:
    data = scraper.extract()
except ConnectionError as e:
    logger.error(f"Network error: {e}")
    return cached_data
except ValueError as e:
    logger.error(f"Validation failed: {e}")
    raise
```

### Database Operations

```python
# Context managers
with db.engine.begin() as conn:
    conn.execute(query)

# Parameterized queries
query = text("SELECT * FROM players WHERE league = :league")
conn.execute(query, {"league": league_name})
```

## Configuration

### Environment Variables (.env)

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=footballdecoded
DB_USER=your_user
DB_PASSWORD=your_password
```

### League IDs

Format: `COUNTRY-League Name`
- Examples: `ESP-La Liga`, `ENG-Premier League`, `INT-Champions League`
- All mappings in `scrappers/_config.py::LEAGUE_DICT`

### Rate Limiting

- FotMob: 3-5s (JSON API)
- Understat: 5s
- WhoScored: 10s (Selenium)
- Transfermarkt: 5s
- Block pauses: 10-20 min between leagues (data loader)

## Environment Management (Conda)

```bash
# Create environment
conda env create -f environment.yml

# Activate/deactivate
conda activate footballdecoded
conda deactivate

# Update after changes
conda env update -f environment.yml --prune

# Package management
conda list
conda install package_name
pip install package_name  # If not in conda
```

**Workflow**: Always activate the environment before working. You will see `(footballdecoded)` in your prompt.

## Git Workflow

### Branch Strategy

```
main (protected)
  ├── feature/new-visualization
  ├── fix/scraper-timeout
  ├── docs/update-readme
  └── refactor/database-optimization
```

### Workflow

```bash
# 1. New task from main
git checkout main
git pull origin main
git checkout -b feature/add-new-viz

# 2. Incremental commits
git add -p
git commit -m "feat: add base structure for radar"
git commit -m "feat: implement data processing"

# 3. Stay up to date
git fetch origin
git rebase origin/main

# 4. Push
git push origin feature/add-new-viz

# 5. After merge
git checkout main
git pull origin main
git branch -d feature/add-new-viz
```

### Commit Format

```bash
# Conventional commits: <type>(<scope>): <subject>

feat: New feature
fix: Bug fix
docs: Documentation
refactor: Code restructuring
perf: Performance improvement
test: Tests
chore: Maintenance

# Examples
git commit -m "feat(scrapers): add FotMob team stats"
git commit -m "fix(database): resolve connection pool exhaustion"
git commit -m "docs: update wrappers API"
```

## Data Quality

### Validation Pipeline

1. **Range validation**: Statistical outlier detection
2. **Completeness**: `data_quality_score` (0.00-1.00)
3. **Normalization**: Consistent naming/formats (accent stripping, title case)
4. **Deduplication**: SHA256 unique IDs

### Quality Metrics

Each record includes:
- `data_quality_score`: 0.00-1.00 quality indicator
- `processing_warnings`: Array of issues found during validation
- `created_at`, `updated_at`: Timestamps

## Security

### Credentials

- Never hardcode credentials
- Use .env exclusively
- Least privilege principle

### Web Scraping Ethics

- Respect robots.txt
- Rate limiting (3-10s between requests)
- Random delays (jitter)
- User-Agent rotation
- Aggressive file caching (30 days)

## References

### Internal Docs

- **Wrappers API**: wrappers/README.md
- **Visualization**: viz/README.md
- **Database v2 Schema**: database/setup_v2.sql
- **Database v1 Schema**: database/setup.sql, database/setup_extras.sql (legacy)

### External

- [FotMob](https://www.fotmob.com/)
- [Understat](https://understat.com/)
- [WhoScored](https://www.whoscored.com/)
- [Transfermarkt](https://www.transfermarkt.com/)
- [PostgreSQL Wiki](https://wiki.postgresql.org/wiki/Main_Page)

---

**Remember**: This guide is the single source of truth. Keep it updated.
