# CLAUDE.md - FootballDecoded Development Guide

## Core Philosophy

**Ve paso a paso, uno a uno. Despacio es el camino más rápido. Escribe siempre el código lo más compacto y conciso posible, y que cumpla exactamente lo pedido al 100%. Sin emojis ni florituras. Usa nombres claros y estándar. Incluye solo comentarios útiles y necesarios.**

Antes de realizar cualquier tarea, revisa cuidadosamente el archivo CLAUDE.md.

### Development Principles

- **KISS**: Choose straightforward solutions over complex ones
- **YAGNI**: Implement features only when needed
- **Fail Fast**: Check for errors early and raise exceptions immediately
- **Single Responsibility**: Each function, class, and module has one clear purpose
- **Dependency Inversion**: High-level modules depend on abstractions, not implementations

## Repository Structure

```
FootballDecoded/
├── scrappers/              # Data extraction (~4,400 lines)
│   ├── _common.py          # Base classes (880 lines)
│   ├── _config.py          # LEAGUE_DICT with 30+ leagues (268 lines)
│   ├── fbref.py            # 15 methods, 11 stat types (1,440 lines)
│   ├── understat.py        # xG specialist, Big 5 only (727 lines)
│   ├── sofascore.py        # xG data, all leagues (285 lines)
│   ├── whoscored.py        # Spatial events with x/y coords (853 lines)
│   └── transfermarkt.py    # Player profiles, market values
│
├── wrappers/               # Simplified API (~3,400 lines)
│   ├── README.md           # Complete API documentation
│   ├── fbref_data.py       # 15 functions, 24h cache (762 lines)
│   ├── understat_data.py   # 16 functions, merge capabilities (1,130 lines)
│   ├── sofascore_data.py   # Shot events with xG (115 lines)
│   ├── whoscored_data.py   # 18 functions, spatial analysis (1,250 lines)
│   └── transfermarkt_data.py  # 2 functions (118 lines)
│
├── database/               # PostgreSQL layer (~2,050 lines)
│   ├── connection.py       # Pool, retry logic (539 lines)
│   ├── data_loader.py      # Parallel processing, checkpoints (1,194 lines)
│   ├── database_checker.py # 8 CLI health commands (1,018 lines)
│   ├── setup.sql           # 4 tables, 28 indices
│   └── setup_extras.sql    # 2 extras tables
│
├── viz/                    # Visualization (~4,800 lines)
│   ├── templates/          # 6 Jupyter notebooks
│   ├── match_data.py       # 10-step pipeline, 5 CSV outputs (Understat)
│   ├── match_data_v2.py    # 10-step pipeline, 5 CSV outputs (SofaScore)
│   ├── pass_network.py     # Network plots
│   ├── shot_xg.py          # xG maps
│   └── swarm_radar.py      # Player comparison radars
│
└── blog/                   # Assets & Utilities
    ├── logos/              # Team logos (6 leagues)
    ├── notebooks/          # Analysis notebooks
    └── get_match_ids.py    # Match ID extractor (WhoScored/Understat)
```

## Quick Start

### 1. Environment Setup

```bash
# Create environment (see CONDA_SETUP.md for details)
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

# Setup schema
python database/data_loader.py
# Select option 6: "Setup database schema"
```

### 3. Load Data

```bash
python database/data_loader.py
# Option 1: Single league (~10-15 min)
# Option 2: Block 1 (ENG+ESP+ITA, ~45 min)
# Option 3: Block 2 (GER+FRA+UCL, ~40 min)
# Option 4: Block 3 (7 extras, ~2 hours)
```

### 4. First Visualization

**Big 5 Leagues (use Understat for xG):**
```python
from viz.match_data import extract_match_complete

# Process match
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

**Other Leagues like MLS (use SofaScore for xG):**
```python
from viz.match_data_v2 import extract_match_complete_v2

# Process match
result = extract_match_complete_v2(
    ws_id=1953302,
    ss_id=14924703,  # SofaScore event ID
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
DATA SOURCES (FBref, Understat, SofaScore, WhoScored, Transfermarkt)
    ↓
EXTRACTION (scrappers/)
    - Rate limiting: 5-7s between requests
    - Cache: 30 days
    - TLS fingerprinting, User-Agent rotation
    ↓
SIMPLIFICATION (wrappers/)
    - 53 high-level functions
    - 24h cache
    - Parallel processing
    ↓
STORAGE (database/)
    - 6 PostgreSQL tables
    - SHA256 unique IDs
    - JSONB metrics (145+ FBref, 15 Understat, 9 Transfermarkt)
    - Parallel loading (3 workers)
    ↓
VISUALIZATION (viz/)
    - 10-step enrichment
    - 5 optimized CSVs
    - Professional plots
```

**xG Data Source Selection:**
- **Big 5 Leagues**: Use Understat (match_data.py) - More accurate xG models
- **Other Leagues** (MLS, Portugal, etc.): Use SofaScore (match_data_v2.py) - Broader coverage

## Module Overview

### Scrapers (scrappers/)

**Base Classes** (_common.py):
- `BaseReader`: Core cache/download logic
- `BaseRequestsReader`: HTTP with TLS evasion
- `BaseSeleniumReader`: Browser automation

**Sources**:
- **FBref** (fbref.py): 11 stat types, comprehensive coverage
- **Understat** (understat.py): xG Chain, PPDA, xG Buildup (Big 5 only)
- **SofaScore** (sofascore.py): xG/xgot data, all leagues (Selenium + API)
- **WhoScored** (whoscored.py): Event data with x/y coordinates
- **Transfermarkt** (transfermarkt.py): Market values, positions

**Key Config** (_config.py):
- `LEAGUE_DICT`: 30+ leagues with source mappings
- Rate limits, cache settings

### Wrappers (wrappers/)

**See wrappers/README.md for complete API reference**

**FBref** (fbref_data.py):
- `get_player()`, `get_team()`: Single entity
- `get_players()`, `get_teams()`: Batch with parallelization
- `get_league_players()`: All players in league
- Returns: 153 fields (players), 190+ (teams)

**Understat** (understat_data.py):
- `get_player()`, `get_team()`: Exclusive metrics
- `merge_with_fbref()`: Auto-enrichment (KEY FUNCTION)
- Returns: 15 exclusive metrics
- **Coverage**: Big 5 leagues only

**SofaScore** (sofascore_data.py):
- `extract_shot_events()`: Shot data with xG/xgot values
- `get_match_xg_summary()`: xG summary by team
- Returns: 18 columns with shot data
- **Coverage**: All major leagues (MLS, Big 5, Portugal, etc.)

**WhoScored** (whoscored_data.py):
- `get_match_events()`: All events with coords
- `get_pass_network()`: Network data
- Returns: 42 columns with spatial data

### Database (database/)

**Schema** (6 tables):
- `players_domestic` / `teams_domestic`: Big 5 leagues
- `players_european` / `teams_european`: International
- `players_extras` / `teams_extras`: 7 additional leagues

**Unique ID System**:
- Players: SHA256(name + birth_year + nationality) → 16-char hex
- Teams: SHA256(team_name + league) → 16-char hex
- Enables multi-season tracking and transfer detection

**Key Fields**:
- `fbref_metrics` JSONB: 145+ metrics
- `understat_metrics` JSONB: 15 metrics
- `transfermarkt_metrics` JSONB: 9 fields
- `data_quality_score`: 0.0-1.0
- `is_transfer`, `transfer_count`

**CLI Tools**:
```bash
# Health monitoring
python database/database_checker.py --quick    # Fast overview
python database/database_checker.py --health   # Health score (0-100)
python database/database_checker.py --problems # Detect issues
python database/database_checker.py --full     # Complete analysis
```

**Connection** (connection.py):
- Pool: 5 connections + 10 overflow
- Retry logic with exponential backoff
- `DatabaseManager` singleton

**Loading** (data_loader.py):
- Parallel: 3 workers
- Checkpoints: Every 25 records
- Adaptive rate limiting: 0.5-3.0s
- Block pauses: 10-20 min between leagues

### Visualization (viz/)

**See viz/README.md for complete documentation**

**match_data.py** - Core Processing (Understat xG):
- 10-step enrichment pipeline
- Outputs 5 CSVs: events (55 cols), aggregates (36), network (18), spatial (29), info (11)
- **Use for**: Big 5 leagues

**match_data_v2.py** - Core Processing (SofaScore xG):
- Same 10-step enrichment pipeline
- Outputs same 5 CSVs with identical structure
- **Use for**: MLS, Portugal, and other non-Big 5 leagues

**Plots**:
- `pass_network.py`: Network with positions
- `shot_xg.py`: xG maps
- `swarm_radar.py`: Player comparison
- `stats_table.py`: Statistical tables

**Design System**:
- Colormap: deepskyblue → tomato
- Background: #313332
- Typography: DejaVu Sans

**Templates**: 6 Jupyter notebooks in viz/templates/

### Utilities (blog/)

**get_match_ids.py** - Match ID Extractor:
- Extracts match IDs from WhoScored and Understat
- Supports team name variations and fuzzy matching
- **Usage**:
  ```python
  from blog.get_match_ids import extract_match_ids

  ids = extract_match_ids(
      team_name="Inter Miami",
      league="USA-MLS",
      season="2025",
      sources=['whoscored']  # or ['understat'] for Big 5
  )
  ```
- Returns: DataFrame with match_id, date, home_team, away_team, league, season
- Handles both WhoScored slugs and Understat numeric IDs

## Supported Competitions

### Big 5 Leagues
| League | Code | FBref | Understat | Transfermarkt |
|--------|------|-------|-----------|---------------|
| Premier League | ENG-Premier League | ✅ | ✅ | ✅ |
| La Liga | ESP-La Liga | ✅ | ✅ | ✅ |
| Serie A | ITA-Serie A | ✅ | ✅ | ✅ |
| Bundesliga | GER-Bundesliga | ✅ | ✅ | ✅ |
| Ligue 1 | FRA-Ligue 1 | ✅ | ✅ | ✅ |

### International
- Champions League (INT-Champions League): FBref ✅
- World Cup (INT-World Cup): FBref ✅
- European Championship (INT-European Championship): FBref ✅

### Extras (7 leagues)
Portugal, Netherlands, Belgium, Turkey, Scotland, Switzerland, USA
- FBref: ✅ All
- Understat: ✅ Portugal only
- Transfermarkt: ✅ All

**Season Formats**:
- Multi-year: `24-25` or `2425` (domestic leagues, UCL)
- Single-year: `2022` (World Cup, Euros)

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
    """
    Extract data from source.

    Args:
        league: League identifier
        season: Season in YY-YY format

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

- FBref: 7s minimum
- Understat: 5s minimum
- WhoScored: 10s minimum
- Block pauses: 10-20 min between leagues

## Environment Management (Conda)

**Ver CONDA_SETUP.md para guía completa**

```bash
# Crear entorno (primera vez)
conda env create -f environment.yml

# Activar/desactivar
conda activate footballdecoded
conda deactivate

# Actualizar tras cambios
conda env update -f environment.yml --prune

# Gestión de paquetes
conda list
conda install package_name
pip install package_name  # Si no está en conda
```

**Workflow**: Siempre activa el entorno antes de trabajar. Verás `(footballdecoded)` en tu prompt.

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
# 1. Nueva tarea desde main
git checkout main
git pull origin main
git checkout -b feature/add-new-viz

# 2. Commits incrementales
git add -p
git commit -m "feat: add base structure for radar"
git commit -m "feat: implement data processing"

# 3. Mantener actualizado
git fetch origin
git rebase origin/main

# 4. Push
git push origin feature/add-new-viz

# 5. Después de merge
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

# Ejemplos
git commit -m "feat(scrapers): add retry logic for FBref"
git commit -m "fix(database): resolve connection pool exhaustion"
git commit -m "docs: update wrappers API"
```

## Data Quality

### Validation Pipeline

1. **Type checking**: Pydantic models
2. **Range validation**: Statistical outlier detection
3. **Completeness**: `data_quality_score` (0.0-1.0)
4. **Normalization**: Consistent naming/formats
5. **Deduplication**: SHA256 unique IDs

### Quality Metrics

Each record includes:
- `data_quality_score`: Quality indicator
- `processing_warnings`: Array of issues
- `created_at`, `updated_at`: Timestamps

## Security

### Credentials

- Never hardcode credentials
- Use .env exclusively
- Rotate passwords regularly
- Least privilege principle

### Web Scraping Ethics

- Respect robots.txt
- Rate limiting (5-10s between requests)
- Random delays
- User-Agent rotation
- Aggressive caching

## References

### Internal Docs

- **Wrappers API**: wrappers/README.md
- **Visualization**: viz/README.md
- **Database Schema**: database/setup.sql
- **Conda Setup**: CONDA_SETUP.md

### External

- [FBref Data Dictionary](https://fbref.com/en/about/datafeed)
- [Understat API](https://understat.com/)
- [WhoScored Events](https://www.whoscored.com/)
- [PostgreSQL Wiki](https://wiki.postgresql.org/wiki/Main_Page)

---

**Remember**: This guide is the single source of truth. Keep it updated. Reference for consistent development practices.
