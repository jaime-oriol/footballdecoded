# CLAUDE.md - FootballDecoded Development Guide

## Core Philosophy

**Ve paso a paso, uno a uno. Despacio es el camino más rápido. Escribe siempre el código lo más compacto y conciso posible, y que cumpla exactamente lo pedido al 100%. Sin emojis ni florituras. Usa nombres claros y estándar. Incluye solo comentarios útiles y necesarios.**

Antes de realizar cualquier tarea, revisa cuidadosamente el archivo CLAUDE.md.
Ahí encontrarás las directrices de trabajo y la estructura del proyecto que debes seguir.

### Development Principles

- **KISS (Keep It Simple, Stupid)**: Choose straightforward solutions over complex ones
- **YAGNI (You Aren't Gonna Need It)**: Implement features only when needed
- **Fail Fast**: Check for errors early and raise exceptions immediately
- **Single Responsibility**: Each function, class, and module has one clear purpose
- **Dependency Inversion**: High-level modules depend on abstractions, not implementations

## Repository Structure

```
FootballDecoded/
├── scrappers/              # Data extraction from web sources (~4,100 lines)
│   ├── __init__.py         # Package initialization, exports FBref/Understat/WhoScored
│   ├── _common.py          # Base classes: BaseReader, BaseRequestsReader, BaseSeleniumReader (880 lines)
│   ├── _config.py          # Global config, LEAGUE_DICT with 30+ leagues, logging setup (268 lines)
│   ├── _utils.py           # Utilities: distance calculation, name validation (84 lines)
│   ├── fbref.py            # FBref scraper - 15 methods, 11 stat types (1,440 lines)
│   ├── understat.py        # Understat scraper - xG specialist, 5 leagues (727 lines)
│   ├── whoscored.py        # WhoScored scraper - spatial events with x/y coords (853 lines)
│   └── transfermarkt.py    # Transfermarkt scraper - player profiles, market values
│
├── wrappers/               # Simplified API layer (~3,260 lines)
│   ├── __init__.py         # Exports all 51 wrapper functions
│   ├── README.md           # Complete API documentation with examples
│   ├── fbref_data.py       # FBref wrapper: 15 functions, cache 24h (762 lines)
│   ├── understat_data.py   # Understat wrapper: 16 functions, merge capabilities (1,130 lines)
│   ├── whoscored_data.py   # WhoScored wrapper: 18 functions, spatial analysis (1,250 lines)
│   └── transfermarkt_data.py  # Transfermarkt wrapper: 2 functions (118 lines)
│
├── database/               # PostgreSQL persistence layer (~2,050 lines)
│   ├── connection.py       # DatabaseManager with pool, retry logic (539 lines)
│   ├── data_loader.py      # Bulk loading: parallel processing, checkpoints (1,194 lines)
│   ├── database_checker.py # Health monitoring: 8 CLI commands (1,018 lines)
│   ├── setup.sql           # Schema: 4 main tables, 28 indices (302 lines)
│   └── setup_extras.sql    # Schema: 2 extras tables (155 lines)
│
├── viz/                    # Visualization system (~3,500 lines)
│   ├── downloaded_files/   # Selenium temporary files and locks
│   ├── templates/          # Jupyter notebook templates (6 notebooks)
│   │   ├── match_data.ipynb     # Match data processing workflow
│   │   ├── match_data_BB.ipynb  # Match data variant
│   │   ├── pass_analysis.ipynb  # Pass flow and hull analysis
│   │   ├── pass_network.ipynb   # Team pass networks
│   │   ├── shots.ipynb          # Shot map analysis
│   │   └── swarm_radar.ipynb    # Player comparison radar
│   ├── README.md           # Visualization system documentation
│   ├── match_data.py       # Core processing: 10-step pipeline, 5 CSV outputs
│   ├── pass_network.py     # Pass network plots with positions
│   ├── pass_analysis.py    # Advanced pass flow visualization
│   ├── shot_map_report.py  # Shot maps with xG overlay
│   ├── shot_xg.py          # xG analysis and visualization
│   ├── stats_radar.py      # Individual player radar charts
│   ├── swarm_radar.py      # Comparative radar with swarm plots
│   └── stats_table.py      # Statistical comparison tables
│
├── blog/                   # Blog assets and content
│   ├── caras/              # Player photos organized by team
│   │   ├── atm/           # Atlético Madrid player photos
│   │   ├── extras/        # Additional player photos
│   │   └── villareal/     # Villarreal player photos
│   ├── logo/              # FootballDecoded project branding
│   │   └── [Brand assets and design manual]
│   ├── logos/             # Team logos organized by league (6 leagues)
│   │   ├── LaLiga/        # Spanish league team logos (20 teams)
│   │   ├── PL/            # Premier League team logos (20 teams)
│   │   ├── Bundesliga/    # German league team logos (18 teams)
│   │   ├── Ligue 1/       # French league team logos (20 teams)
│   │   ├── Serie A/       # Italian league team logos (20 teams)
│   │   └── Primeira Liga/ # Portuguese league team logos (18 teams)
│   └── notebooks/         # Analysis notebooks for blog posts
│
├── .checkpoints/          # Jupyter and data loader checkpoint files
├── .claude/               # Claude Code configuration
│   └── settings.local.json
├── .env                   # Environment variables (git-ignored)
├── .gitignore            # Git ignore patterns
├── environment.yml       # Conda environment specification
├── CONDA_SETUP.md        # Complete Conda installation and usage guide
├── Makefile             # Common tasks automation
├── LICENSE.rst          # Project license
├── README.rst           # Project overview
└── CLAUDE.md            # This development guide
```

## Quick Start Guide

### Initial Setup

#### 1. Environment Setup (Conda)

```bash
# Install Anaconda/Miniconda (see CONDA_SETUP.md for detailed instructions)
# Then create the environment
conda env create -f environment.yml

# Activate environment
conda activate footballdecoded

# Verify installation
python -c "import pandas; import sqlalchemy; print('Environment ready!')"
```

#### 2. Database Setup

```bash
# Ensure PostgreSQL is running
# Configure .env file with database credentials:
cat > .env << EOF
DB_HOST=localhost
DB_PORT=5432
DB_NAME=footballdecoded
DB_USER=your_user
DB_PASSWORD=your_password
EOF

# Run setup script
python database/data_loader.py
# Select option 6: "Setup database schema"
# This creates all tables and indices
```

#### 3. Verify Database Connection

```bash
python database/data_loader.py
# Select option 5: "Test database connection"
# Should show: "Database connection successful"

# Check initial status
python database/database_checker.py --quick
```

### First Data Load

#### Load Your First League

```bash
# Activate environment
conda activate footballdecoded

# Run data loader
python database/data_loader.py

# Select option 1: "Load single competition"
# Choose league (example: 1 for Premier League)
# Enter season (example: 24-25 for 2024-25)

# The loader will:
# 1. Clear existing data for that league/season
# 2. Extract player list from FBref (~600 players)
# 3. Process in parallel (3 workers)
# 4. Extract FBref stats (11 types)
# 5. Enrich with Understat metrics (xG, PPDA, etc.)
# 6. Add Transfermarkt data (market value, foot, position)
# 7. Insert into database with unique IDs
# 8. Show progress bar with ETA

# Typical load time: 10-15 minutes for one league/season
```

#### Understanding Load Blocks

For efficient bulk loading, use blocks to load multiple leagues with automatic pauses:

```bash
# Block 1: Top 3 leagues (ENG + ESP + ITA)
# Select option 2
# Loads 3 leagues with 10-20 min pauses between them
# Total time: ~45 minutes

# Block 2: Remaining Big 5 + Champions League (GER + FRA + UCL)
# Select option 3
# Total time: ~40 minutes

# Block 3: 7 Extra Leagues (POR, NED, BEL, TUR, SCO, SUI, USA)
# Select option 4
# Total time: ~2 hours
```

### Your First Visualization

#### Extract Match Data

```python
from viz.match_data import extract_match_complete

# Process a match (WhoScored + Understat)
result = extract_match_complete(
    ws_id=1821769,              # WhoScored match ID
    us_id=16364,                # Understat match ID
    league="ESP-La Liga",
    season="2024-25",
    home_team="Athletic Club",
    away_team="Barcelona",
    match_date="2024-08-24"
)

# This generates 5 CSV files in viz/data/:
# - match_events.csv (55 columns, all events with coords)
# - match_aggregates.csv (36 columns, player/zone stats)
# - player_network.csv (18 columns, pass connections)
# - spatial_analysis.csv (29 columns, heatmaps/control)
# - match_info.csv (11 columns, metadata)
```

#### Generate Pass Network

```python
from viz.pass_network import plot_pass_network

fig = plot_pass_network(
    csv_path='viz/data/player_network.csv',
    team_name='Barcelona',
    period='full',
    min_connections=5,
    logo_path='blog/logos/LaLiga/barcelona.png',
    title_text='Barcelona Pass Network',
    subtitle_text='Athletic Club 1-2 Barcelona | 2024-08-24'
)

fig.savefig('barcelona_network.png', dpi=300, bbox_inches='tight')
```

#### Generate xG Map

```python
from viz.shot_xg import plot_shot_xg

fig = plot_shot_xg(
    csv_path='viz/data/match_events.csv',
    filter_by='Barcelona',
    logo_path='blog/logos/LaLiga/barcelona.png',
    title_text='Barcelona xG Map',
    subtitle_text='Athletic Club 1-2 Barcelona | 2024-08-24'
)

fig.savefig('barcelona_xg.png', dpi=300, bbox_inches='tight')
```

### Useful Database Queries

#### Basic Queries

```sql
-- Check what data you have
SELECT league, season, COUNT(*) as players,
       COUNT(DISTINCT unique_player_id) as unique_players,
       COUNT(DISTINCT team) as teams
FROM footballdecoded.players_domestic
GROUP BY league, season
ORDER BY league, season DESC;

-- Top scorers in a league
SELECT player_name, team,
       (fbref_metrics->>'goals')::int as goals,
       (fbref_metrics->>'minutes_played')::float as minutes
FROM footballdecoded.players_domestic
WHERE league = 'ENG-Premier League' AND season = '2024-25'
ORDER BY (fbref_metrics->>'goals')::int DESC
LIMIT 10;

-- Players with high xG Chain (Understat)
SELECT player_name, team,
       (understat_metrics->>'understat_xg_chain')::float as xg_chain,
       (understat_metrics->>'understat_xg_buildup')::float as xg_buildup
FROM footballdecoded.players_domestic
WHERE league = 'ESP-La Liga'
  AND understat_metrics IS NOT NULL
ORDER BY (understat_metrics->>'understat_xg_chain')::float DESC
LIMIT 10;
```

#### Advanced Queries

```sql
-- Track player across seasons
SELECT season, team,
       (fbref_metrics->>'matches_played')::int as matches,
       (fbref_metrics->>'goals')::int as goals,
       (fbref_metrics->>'assists')::int as assists
FROM footballdecoded.players_domestic
WHERE unique_player_id = (
    SELECT unique_player_id
    FROM footballdecoded.players_domestic
    WHERE player_name LIKE '%Haaland%'
    LIMIT 1
)
ORDER BY season DESC;

-- Find transfers (same player, multiple teams in one season)
SELECT unique_player_id, player_name, league, season,
       COUNT(DISTINCT team) as teams_count,
       STRING_AGG(team, ' -> ' ORDER BY team) as transfer_path
FROM footballdecoded.players_domestic
WHERE league = 'ESP-La Liga' AND season = '2024-25'
GROUP BY unique_player_id, player_name, league, season
HAVING COUNT(DISTINCT team) > 1;

-- Market value evolution
SELECT player_name, season, team,
       (transfermarkt_metrics->>'transfermarkt_market_value_eur')::bigint as market_value
FROM footballdecoded.players_domestic
WHERE unique_player_id = 'a3f5d82b9e1c4f7a'
ORDER BY season DESC;
```

## Data Pipeline Architecture

### Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    1. DATA SOURCES                          │
├─────────────────────────────────────────────────────────────┤
│  FBref.com          Understat.com      WhoScored.com        │
│  - 11 stat types    - xG metrics      - Event data          │
│  - Season stats     - PPDA            - x/y coordinates     │
│  - Match stats      - xG Chain        - Qualifiers          │
└──────────────┬──────────────┬──────────────┬───────────────┘
               │              │              │
               ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│              2. EXTRACTION (scrappers/)                     │
├─────────────────────────────────────────────────────────────┤
│  BaseRequestsReader (FBref, Understat, Transfermarkt)       │
│  - HTTP requests with TLS fingerprinting                    │
│  - Rate limiting: 5-7s between requests                     │
│  - User-Agent rotation (15 variants)                        │
│  - Automatic retry (5 attempts)                             │
│                                                             │
│  BaseSeleniumReader (WhoScored)                             │
│  - JavaScript rendering                                     │
│  - Undetected ChromeDriver                                  │
│  - Incapsula blocking detection                             │
│                                                             │
│  Cache System (~/soccerdata/data/)                          │
│  - 30 day expiration (configurable)                         │
│  - Per-source directories                                   │
│  - Season completion detection                              │
└──────────────┬──────────────────────────────┬──────────────┘
               │                              │
               ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│            3. SIMPLIFICATION (wrappers/)                    │
├─────────────────────────────────────────────────────────────┤
│  51 High-Level Functions:                                   │
│                                                             │
│  FBref (15 functions)                                       │
│  - get_player() / get_team()                                │
│  - get_players() with parallel processing                   │
│  - extract_league_players()                                 │
│  Returns: 153 fields for players, 190+ for teams            │
│                                                             │
│  Understat (16 functions)                                   │
│  - get_player() / get_team()                                │
│  - merge_with_fbref() [automatic integration]               │
│  - get_shots() with coordinates                             │
│  Returns: 15 exclusive metrics (xG Chain, PPDA, etc.)       │
│                                                             │
│  WhoScored (18 functions)                                   │
│  - get_match_events() [all actions with x/y]                │
│  - get_pass_network() [connections + positions]             │
│  - get_player_heatmap()                                     │
│  Returns: 42 columns with spatial data                      │
│                                                             │
│  Cache: ~/.footballdecoded_cache/ (24h expiry)              │
└──────────────┬──────────────────────────────┬──────────────┘
               │                              │
               ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│              4. STORAGE (database/)                         │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL Schema (6 tables):                              │
│  - players_domestic  (BIG 5 leagues)                        │
│  - teams_domestic                                           │
│  - players_european  (Champions League, etc.)               │
│  - teams_european                                           │
│  - players_extras    (Portugal, Netherlands, etc.)          │
│  - teams_extras                                             │
│                                                             │
│  Unique ID System (SHA256):                                 │
│  - Players: hash(name + birth_year + nationality)           │
│  - Teams: hash(team_name + league)                          │
│  - 16-char hexadecimal identifiers                          │
│  - Enables multi-season tracking and transfer detection     │
│                                                             │
│  JSONB Fields:                                              │
│  - fbref_metrics: 145+ metrics                              │
│  - understat_metrics: 15 metrics                            │
│  - transfermarkt_metrics: 9 fields                          │
│                                                             │
│  Data Quality:                                              │
│  - data_quality_score: 0.0-1.0                              │
│  - processing_warnings: TEXT[]                              │
│  - Validation on insert                                     │
│                                                             │
│  Loading Strategy:                                          │
│  - Parallel processing (3 workers)                          │
│  - Checkpoints every 25 records                             │
│  - Adaptive rate limiting (0.5-3.0s)                        │
│  - Block loading with pauses (10-20 min between leagues)    │
└──────────────┬──────────────────────────────┬──────────────┘
               │                              │
               ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│           5. ANALYSIS & VISUALIZATION (viz/)                │
├─────────────────────────────────────────────────────────────┤
│  match_data.py - 10-Step Enrichment Pipeline:               │
│  1. Carries detection                                       │
│  2. xThreat calculation (12x8 grid)                         │
│  3. Pre-assists identification                              │
│  4. Possession chains                                       │
│  5. Progressive actions (FIFA criteria)                     │
│  6. Box entries detection                                   │
│  7. Pass outcomes classification                            │
│  8. Action type classification                              │
│  9. Zone classification (18 zones)                          │
│  10. xG merge with Understat                                │
│                                                             │
│  Output: 5 Optimized CSVs                                   │
│  - match_events.csv (55 cols)                               │
│  - match_aggregates.csv (36 cols)                           │
│  - player_network.csv (18 cols)                             │
│  - spatial_analysis.csv (29 cols)                           │
│  - match_info.csv (11 cols)                                 │
│                                                             │
│  Visualizations:                                            │
│  - Pass networks with player positions                      │
│  - xG maps with shot outcomes                               │
│  - Player radars with swarm plots                           │
│  - Statistical comparison tables                            │
│                                                             │
│  Design System:                                             │
│  - Unified colormap (deepskyblue → tomato)                  │
│  - Background: #313332                                    │
│  - Typography: DejaVu Sans                                  │
└─────────────────────────────────────────────────────────────┘
```

### Real Example: Load Premier League 2024-25

#### Step-by-Step Process

```bash
# Step 1: Activate environment
conda activate footballdecoded

# Step 2: Run data loader
python database/data_loader.py
# Select: 1 (Load single competition)
# Select: 1 (ENG-Premier League)
# Enter season: 24-25
```

#### What Happens Internally

```
[00:00:00] Initializing...
  ✓ Database connection successful
  ✓ Adaptive rate limiter configured (1.0s initial delay)

[00:00:02] Cleaning existing data...
  ✓ Deleted 0 existing players for ENG-Premier League 2024-25
  ✓ Deleted 0 existing teams

[00:00:05] Extracting player list from FBref...
  ✓ Found 647 players across 20 teams

[00:00:10] Processing players (3 parallel workers)...

  Progress: [████████░░░░░░░░░░] 100/647 (15%)
  Current: Erling Haaland | Manchester City
  Status: ✓ Success (1.2s)
    - FBref: 47 metrics extracted
    - Understat: 15 metrics added
    - Transfermarkt: Market value €180M, Right Foot, ST
  Failed: 2 (network timeout, will retry)
  ETA: 8m 45s

  Progress: [████████████████░░] 550/647 (85%)
  Current: Bukayo Saka | Arsenal
  Delay: 0.8s (adaptive - success rate high)

[00:11:23] Processing complete!

SUMMARY:
  ═══════════════════════════════════════════════════════
  Total Entities: 647 players + 20 teams
  Successful: 662 | Failed: 5 | Success Rate: 99.2%

  Unique Player IDs: 621 (26 players with transfer records)
  Unique Team IDs: 20

  Data Coverage:
    - FBref metrics: 100% (all records)
    - Understat metrics: 98.5% (637/647)
    - Transfermarkt data: 95.2% (616/647)

  Processing Time: 11m 23s
  Records/second: 0.97
  Database Size: +3.2 MB
  ═══════════════════════════════════════════════════════

[00:11:25] Verifying data quality...
  ✓ Health Score: 97/100 (Excellent)
  ✓ No duplicate IDs detected
  ✓ Average quality score: 0.96
```

#### Verify Loaded Data

```bash
# Check database status
python database/database_checker.py --quick

# Output:
# ┌─────────────────────────────────────────────────────┐
# │ ENG-Premier League 2024-25: 647 players | 20 teams  │
# │ Understat coverage: 98.5%                           │
# │ Unique player IDs: 621                              │
# │ Transfer detection: 26 players with multiple teams  │
# └─────────────────────────────────────────────────────┘
```

### Performance Metrics

**Single League Load:**
- Players: 600-700 (depending on league size)
- Time: 10-15 minutes
- Rate: ~1 player/second
- Network requests: ~2,000 (cached afterwards)

**Block 1 Load (ENG + ESP + ITA):**
- Players: ~2,000
- Time: 45-60 minutes (including pauses)
- Pauses: 10-20 minutes between leagues (rate limit compliance)

**Full Load (All 13 competitions):**
- Players: ~8,000
- Teams: ~250
- Time: 3-4 hours
- Database size: ~40 MB

## Module Documentation

### Scrapers Module (scrappers/)

The foundation layer that extracts raw data from web sources. Implements robust scraping with rate limiting, caching, and error handling.

#### Architecture Overview

**Three-tier class hierarchy:**
1. `BaseReader` (ABC) - Core interface and cache logic
2. `BaseRequestsReader` - HTTP requests with TLS evasion
3. `BaseSeleniumReader` - Browser automation for JavaScript-heavy sites

**Key features:**
- Multi-level caching (HTTP → wrapper → database)
- Rate limiting: 5-10s between requests
- Automatic retry with exponential backoff
- Proxy support (Tor, HTTP, rotating lists)
- User-Agent rotation (15 variants)
- Session management with auto-reconnection

---

#### _common.py - Base Classes (880 lines)

##### BaseReader (Abstract Base Class)

Core functionality shared by all scrapers.

**Constructor:**
```python
BaseReader(
    leagues: Optional[Union[str, List[str]]] = None,
    seasons: Optional[Union[str, int, List]] = None,
    proxy: Optional[Union[str, List[str], Callable]] = None,
    no_cache: bool = False,
    no_store: bool = False,
    data_dir: Path = DATA_DIR
)
```

**Key Methods:**
- `get(url, filepath, max_age, no_cache, var)` - Core cache/download logic
- `_is_cached(filepath, max_age)` - Validate cache freshness
- `_download_and_save(url, filepath, var)` - Abstract (implemented by subclasses)
- `available_leagues()` - Classmethod returning supported leagues
- `_translate_league(df, col)` - Map source-specific IDs to canonical names
- `_is_complete(league, season)` - Check if season finished (for cache strategy)

**Proxy Support:**
```python
# Tor network
scraper = FBref(proxy="tor")

# Single proxy
scraper = FBref(proxy="http://proxy.example.com:8080")

# Rotating list
scraper = FBref(proxy=["proxy1.com:8080", "proxy2.com:8080"])

# Custom function
def get_proxy():
    return random.choice(proxy_pool)
scraper = FBref(proxy=get_proxy)
```

##### BaseRequestsReader

HTTP-based scraping with TLS fingerprinting evasion.

**Features:**
- Uses `tls_requests` library (bypasses Cloudflare)
- Session pooling with auto-reconnect
- JavaScript variable extraction (regex-based)
- Rate limiting: `time.sleep(rate_limit + random.random() * max_delay)`
- 5 retry attempts with session reset between failures

**User-Agent Rotation:**
```python
_USER_AGENTS = [
    # 15 realistic browser signatures
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ...",
    # ... rotation prevents blocking
]
```

##### BaseSeleniumReader

Browser automation for JavaScript-heavy sites (WhoScored).

**Features:**
- SeleniumBase with undetected-chromedriver
- Incapsula blocking detection
- JavaScript variable extraction (execute_script)
- 5 retry attempts with incremental delays (0s, 10s, 20s, 30s, 40s)
- Automatic driver restart on errors

**Constructor additions:**
```python
BaseSeleniumReader(
    path_to_browser: Optional[Path] = None,
    headless: bool = True,
    ...  # plus BaseReader params
)
```

---

#### _config.py - Global Configuration (268 lines)

Central configuration hub with environment-based settings.

##### Environment Variables

```python
# Read from environment (with fallbacks)
NOCACHE = os.getenv('SOCCERDATA_NOCACHE', False)
NOSTORE = os.getenv('SOCCERDATA_NOSTORE', False)
MAXAGE = os.getenv('SOCCERDATA_MAXAGE', None)  # Days
LOGLEVEL = os.getenv('SOCCERDATA_LOGLEVEL', 'INFO')

# Directories
BASE_DIR = Path(os.getenv('SOCCERDATA_DIR', '~/soccerdata')).expanduser()
DATA_DIR = BASE_DIR / 'data'
LOGS_DIR = BASE_DIR / 'logs'
CONFIG_DIR = BASE_DIR / 'config'
```

##### LEAGUE_DICT - Complete Mapping

30+ leagues mapped to source-specific identifiers:

**Big 5 Leagues:**
```python
"ENG-Premier League": {
    "FBref": "Premier League",
    "WhoScored": "England - Premier League",
    "Understat": "EPL",
    "season_start": "Aug",
    "season_end": "May"
}

"ESP-La Liga": {
    "FBref": "La Liga",
    "WhoScored": "Spain - LaLiga",
    "Understat": "La liga",
    "season_start": "Aug",
    "season_end": "May"
}

"ITA-Serie A": {
    "FBref": "Serie A",
    "WhoScored": "Italy - Serie A",
    "Understat": "Serie A",
    "season_start": "Aug",
    "season_end": "May"
}

"GER-Bundesliga": {
    "FBref": "Fußball-Bundesliga",
    "WhoScored": "Germany - Bundesliga",
    "Understat": "Bundesliga",
    "season_start": "Aug",
    "season_end": "May"
}

"FRA-Ligue 1": {
    "FBref": "Ligue 1",
    "WhoScored": "France - Ligue 1",
    "Understat": "Ligue 1",
    "season_start": "Aug",
    "season_end": "May"
}
```

**International Competitions:**
```python
"INT-Champions League": {
    "FBref": "Champions League",
    "WhoScored": "Europe - Champions League",
    "season_start": "Sep",
    "season_end": "May",
    "season_code": "multi-year"
}

"INT-World Cup": {
    "FBref": "FIFA World Cup",
    "WhoScored": "International - FIFA World Cup",
    "season_code": "single-year"  # Format: "2022" not "2122"
}

"INT-European Championship": {
    "FBref": "UEFA European Football Championship",
    "WhoScored": "International - European Championship",
    "season_start": "Jun",
    "season_end": "Jul",
    "season_code": "single-year"
}
```

**Additional Leagues (7 leagues):**
```python
"POR-Primeira Liga": {...}
"NED-Eredivisie": {...}
"BEL-Pro League": {...}
"TUR-Süper Lig": {...}
"SCO-Premiership": {...}
"SUI-Super League": {...}
"USA-MLS": {...}
```

**National Cups:**
```python
"ESP-Copa del Rey": {...}
"ENG-FA Cup": {...}
"ENG-EFL Cup": {...}
"FRA-Coupe de France": {...}
"GER-DFB-Pokal": {...}
"ITA-Coppa Italia": {...}
```

##### Logging System

Three handlers with rotation:
```python
# Console: RichHandler with color
# info.log: All INFO+ messages (10MB, 10 backups)
# error.log: Only ERROR+ messages (10MB, 10 backups)
```

---

#### _utils.py - Utility Functions (84 lines)

Shared utilities used across scrapers and analysis modules.

##### calculate_euclidean_distance()
```python
def calculate_euclidean_distance(
    x1: pd.Series,
    y1: pd.Series,
    x2: float,
    y2: float,
    scale_factor: float = 1.0
) -> pd.Series
```
Calculates distance between series of points and a reference point. Handles NaN values correctly.

**Use cases:**
- Distance to goal from shot locations
- Pass distance calculations
- Spatial analysis in viz module

##### validate_name_field()
```python
def validate_name_field(name: Any) -> bool
```
Validates player/team name fields before processing. Returns False for null/empty strings.

##### format_player_name_base()
```python
def format_player_name_base(full_name: str, default: str = "Unknown") -> str
```
Cleans and formats player names, removing extra whitespace.

---

#### fbref.py - FBref Scraper (1,440 lines)

Primary statistics source with comprehensive coverage.

**Configuration:**
```python
FBREF_API = "https://fbref.com"
FBREF_DATADIR = DATA_DIR / "FBref"
rate_limit = 7  # seconds
max_delay = 3   # seconds
```

**Special Features:**
- "Big 5 European Leagues Combined" optimization (one request for 5 leagues)
- 11 stat types for players and teams
- Match-level data with detailed reports
- Shot events with xG
- Lineup data

##### Constructor
```python
class FBref(BaseRequestsReader):
    def __init__(
        self,
        leagues: Optional[Union[str, List[str]]] = None,
        seasons: Optional[Union[str, int, List]] = None,
        proxy: Optional[Union[str, List[str], Callable]] = None,
        no_cache: bool = NOCACHE,
        no_store: bool = NOSTORE,
        data_dir: Path = FBREF_DATADIR
    )
```

##### Main Methods (15 public methods)

**1. read_leagues()**
```python
def read_leagues(split_up_big5: bool = False) -> pd.DataFrame
```
Returns available leagues with URLs and season ranges.

**Columns:** `[league, url, first_season, last_season, country]`
**Index:** `league`

**2. read_seasons()**
```python
def read_seasons(split_up_big5: bool = False) -> pd.DataFrame
```
Returns available seasons for selected leagues.

**Columns:** `[format, url]`
**Index:** `MultiIndex[league, season]`
**format:** "round-robin" (leagues) or "elimination" (cups)

**3. read_team_season_stats()**
```python
def read_team_season_stats(
    stat_type: str = "standard",
    opponent_stats: bool = False
) -> pd.DataFrame
```
Team aggregated statistics by season.

**stat_type options (11 types):**
- `'standard'` - Goals, assists, xG, discipline
- `'keeper'` - GK stats: saves, clean sheets
- `'keeper_adv'` - Advanced GK: PSxG, distribution
- `'shooting'` - Shots, accuracy, xG per shot
- `'passing'` - Completion %, progressive passes
- `'passing_types'` - Pass types (crosses, through balls)
- `'goal_shot_creation'` - SCA, GCA metrics
- `'defense'` - Tackles, blocks, interceptions
- `'possession'` - Touches, carries, take-ons
- `'playing_time'` - Minutes, rotation
- `'misc'` - Cards, fouls, aerials

**Returns:** DataFrame with 30-50 columns (varies by stat_type)
**Index:** `MultiIndex[league, season, team]`

**4. read_team_match_stats()**
```python
def read_team_match_stats(
    stat_type: str = "schedule",
    opponent_stats: bool = False,
    team: Optional[Union[str, List[str]]] = None,
    force_cache: bool = False
) -> pd.DataFrame
```
Team statistics per match.

**stat_type options:** Same as team_season_stats (except 'schedule' has no opponent_stats)

**Returns:** DataFrame with 20-40 columns
**Index:** `MultiIndex[league, season, team, game]`

**Note:** Slow for many teams (processes individual team pages)

**5. read_player_season_stats()**
```python
def read_player_season_stats(stat_type: str = "standard") -> pd.DataFrame
```
Player aggregated statistics by season.

**stat_type options:** Same 11 types as teams

**Returns:** DataFrame with 30-60 columns
**Index:** `MultiIndex[league, season, team, player]`
**Extra columns:** `player, nation, pos, age, born`

**6. read_schedule()**
```python
def read_schedule(force_cache: bool = False) -> pd.DataFrame
```
Complete fixture list with results.

**Returns:** DataFrame with columns:
`[week, date, home_team, away_team, home_xg, away_xg, score, referee, venue, match_report, game_id]`
**Index:** `MultiIndex[league, season, game]`

**7. read_player_match_stats()**
```python
def read_player_match_stats(
    stat_type: str = "summary",
    match_id: Optional[Union[str, List[str]]] = None,
    force_cache: bool = False
) -> pd.DataFrame
```
Player statistics per match (requires match reports).

**stat_type options:**
- `'summary'` - Basic match stats
- `'keepers'` - GK match performance
- `'passing'`, `'passing_types'`, `'defense'`, `'possession'`, `'misc'`

**Returns:** DataFrame varies by stat_type
**Index:** `MultiIndex[league, season, game, team, player]`

**8. read_lineup()**
```python
def read_lineup(
    match_id: Optional[Union[str, List[str]]] = None,
    force_cache: bool = False
) -> pd.DataFrame
```
Starting lineups and substitutes.

**Returns:** DataFrame with columns:
`[jersey_number, player, team, is_starter, position, minutes_played]`
**Index:** `MultiIndex[league, season, game]`

**9. read_events()**
```python
def read_events(
    match_id: Optional[Union[str, List[str]]] = None,
    force_cache: bool = False
) -> pd.DataFrame
```
Key match events (goals, cards, subs).

**Returns:** DataFrame with columns:
`[team, minute, score, player1, player2, event_type]`
**Index:** `MultiIndex[league, season, game]`

**10. read_shot_events()**
```python
def read_shot_events(
    match_id: Optional[Union[str, List[str]]] = None,
    force_cache: bool = False
) -> pd.DataFrame
```
All shots with xG values.

**Returns:** DataFrame with columns:
`[team, player, minute, outcome, distance, body_part, notes, event]`
**Index:** `MultiIndex[league, season, game]`

---

#### understat.py - Understat Scraper (727 lines)

Advanced metrics specialist with exclusive statistics.

**Configuration:**
```python
UNDERSTAT_URL = "https://understat.com"
UNDERSTAT_DATADIR = DATA_DIR / "Understat"
rate_limit = 5  # seconds (approx)
```

**Limitations:**
- Only 5 leagues (Big 5)
- No European competitions
- Not all matches have data

**Exclusive Metrics:**
- `xG Chain` - xG in all possessions where player participated
- `xG Buildup` - xG in build-up (excluding shot/assist)
- `PPDA` - Passes Per Defensive Action (pressure metric)
- `Deep Completions` - Passes to attacking third
- `Expected Points` - xPts based on xG

##### Constructor
```python
class Understat(BaseRequestsReader):
    def __init__(
        self,
        leagues: Optional[Union[str, List[str]]] = None,
        seasons: Optional[Union[str, int, Iterable]] = None,
        proxy: Optional[Union[str, List[str], Callable]] = None,
        no_cache: bool = NOCACHE,
        no_store: bool = NOSTORE,
        data_dir: Path = UNDERSTAT_DATADIR
    )
```

##### Main Methods (5 public methods)

**1. read_leagues()**
```python
def read_leagues() -> pd.DataFrame
```
Returns available leagues (always 5).

**Columns:** `[league_id, league, url]`
**Index:** `league`

**2. read_seasons()**
```python
def read_seasons() -> pd.DataFrame
```
Returns available seasons for selected leagues.

**Columns:** `[league_id, season_id, url]`
**Index:** `MultiIndex[league, season]`

**3. read_schedule()**
```python
def read_schedule(
    include_matches_without_data: bool = True,
    force_cache: bool = False
) -> pd.DataFrame
```
Fixture list with xG values.

**Returns:** DataFrame with columns:
`[game_id, date, home_team, away_team, home_goals, away_goals, home_xg, away_xg, is_result, has_data, url, home_team_id, away_team_id, home_team_code, away_team_code]`
**Index:** `MultiIndex[league, season, game]`

**4. read_team_match_stats()**
```python
def read_team_match_stats(force_cache: bool = False) -> pd.DataFrame
```
Team advanced metrics per match.

**Returns:** DataFrame with columns:
`[home/away_points, home/away_expected_points, home/away_goals, home/away_xg, home/away_np_xg, home/away_np_xg_difference, home/away_ppda, home/away_deep_completions]`
**Index:** `MultiIndex[league, season, game]`

**Exclusive metrics:**
- `ppda` - Passes Allowed per Defensive Action (lower = higher pressure)
- `deep_completions` - Passes completed in attacking third
- `expected_points` - xPts based on goal probabilities
- `np_xg` - Non-penalty xG
- `np_xg_difference` - Net npxG (for minus against)

**5. read_player_season_stats()**
```python
def read_player_season_stats(force_cache: bool = False) -> pd.DataFrame
```
Player season aggregates with exclusive metrics.

**Returns:** DataFrame with columns:
`[player_id, team_id, position, matches, minutes, goals, xg, np_goals, np_xg, assists, xa, shots, key_passes, yellow_cards, red_cards, xg_chain, xg_buildup]`
**Index:** `MultiIndex[league, season, team, player]`

**Exclusive metrics:**
- `xg_chain` - Total xG in possessions where player was involved
- `xg_buildup` - xG in build-up phase (no shot/assist)
- `xa` - Expected assists
- `key_passes` - Passes leading directly to shots

**6. read_player_match_stats()**
```python
def read_player_match_stats(
    match_id: Optional[Union[int, List[int]]] = None
) -> pd.DataFrame
```
Player match performance with xG metrics.

**Returns:** DataFrame with columns:
`[player_id, team_id, position, position_id, minutes, goals, own_goals, shots, xg, xg_chain, xg_buildup, assists, xa, key_passes, yellow_cards, red_cards]`
**Index:** `MultiIndex[league, season, game, team, player]`

**7. read_shot_events()**
```python
def read_shot_events(
    match_id: Optional[Union[int, List[int]]] = None
) -> pd.DataFrame
```
All shots with coordinates and xG.

**Returns:** DataFrame with columns:
`[shot_id, date, player_id, assist_player, assist_player_id, xg, location_x, location_y, minute, body_part, situation, result]`
**Index:** `MultiIndex[league, season, game, team, player]`

**Coordinates:**
- `location_x`, `location_y` - 0-1 scale
- X: 0 = own goal, 1 = opponent goal
- Y: 0 = left, 1 = right (attacking view)

---

#### whoscored.py - WhoScored Scraper (853 lines)

Spatial event data specialist with full match coverage.

**Configuration:**
```python
WHOSCORED_URL = "https://www.whoscored.com"
WHOSCORED_DATADIR = DATA_DIR / "WhoScored"
rate_limit = 5  # seconds
max_delay = 5   # seconds
```

**Key Features:**
- Complete event data with x/y coordinates
- All player actions (passes, shots, tackles, etc.)
- Qualifiers for detailed context
- SPADL format support (via socceraction)
- Live match data support

##### Constructor
```python
class WhoScored(BaseSeleniumReader):
    def __init__(
        self,
        leagues: Optional[Union[str, List[str]]] = None,
        seasons: Optional[Union[str, int, Iterable]] = None,
        proxy: Optional[Union[str, List[str], Callable]] = None,
        no_cache: bool = NOCACHE,
        no_store: bool = NOSTORE,
        data_dir: Path = WHOSCORED_DATADIR,
        path_to_browser: Optional[Path] = None,
        headless: bool = False  # False recommended!
    )
```

**Note:** `headless=False` recommended to avoid detection.

##### Main Methods (5 public methods)

**1. read_leagues()**
```python
def read_leagues() -> pd.DataFrame
```
Returns available leagues with region info.

**Columns:** `[region_id, region, league_id, league]`
**Index:** `league` (format: "Region - League")

**2. read_seasons()**
```python
def read_seasons() -> pd.DataFrame
```
Returns available seasons.

**Columns:** `[region_id, league_id, season_id]`
**Index:** `MultiIndex[league, season]`

**3. read_schedule()**
```python
def read_schedule(force_cache: bool = False) -> pd.DataFrame
```
Complete fixture list.

**Returns:** DataFrame with many columns including stage info
**Index:** `MultiIndex[league, season, game]`

**4. read_missing_players()**
```python
def read_missing_players(
    match_id: Optional[Union[int, List[int]]] = None,
    force_cache: bool = False
) -> pd.DataFrame
```
Injured/suspended players for match.

**Returns:** DataFrame with columns:
`[player_id, reason, status]`
**Index:** `MultiIndex[league, season, game, team, player]`

**5. read_events()** ⭐ **PRIMARY METHOD**
```python
def read_events(
    match_id: Optional[Union[int, List[int]]] = None,
    force_cache: bool = False,
    live: bool = False,
    output_fmt: Optional[str] = "events",
    retry_missing: bool = True,
    on_error: Literal["raise", "skip"] = "raise"
) -> Optional[Union[pd.DataFrame, dict, OptaLoader]]
```
Complete match event data with coordinates.

**output_fmt options:**
- `'events'` (default) - Standard DataFrame (42 columns)
- `'raw'` - Original JSON dict
- `'spadl'` - SPADL format (requires socceraction)
- `'atomic-spadl'` - Atomic SPADL format
- `'loader'` - OptaLoader instance for socceraction
- `None` - Cache only, no return

**Returns (events format):** DataFrame with columns:
```python
[game_id, period, minute, second, expanded_minute, type, outcome_type,
 team_id, team, player_id, player, x, y, end_x, end_y, goal_mouth_y,
 goal_mouth_z, blocked_x, blocked_y, qualifiers, is_touch, is_shot,
 is_goal, card_type, related_event_id, related_player_id, ...]
```
**Index:** `MultiIndex[league, season, game]`

**Coordinates:**
- `x`, `y` - 0-100 scale (% of pitch)
- `end_x`, `end_y` - Destination (passes/carries)
- `goal_mouth_y`, `goal_mouth_z` - Shot target (includes height)

**Qualifiers:** List of dicts with additional context:
- Pass type: "Longball", "Cross", "Through Ball"
- Shot type: "Header", "VolleyPass"
- Defensive: "Clearance", "Interception"
- And many more...

---

### Wrappers Module (wrappers/)

Simplified, production-ready API over raw scrapers. Provides caching, parallel processing, error handling, and data integration.

**Key features:**
- 24-hour cache (separate from scrapers)
- Parallel processing with ThreadPoolExecutor
- Automatic name matching and disambiguation
- Data merge capabilities (FBref + Understat)
- CSV export with timestamps
- Progress bars for batch operations

---

#### fbref_data.py - FBref Wrapper (762 lines)

Comprehensive statistics extraction with intelligent caching.

##### Quick Access Functions (7 functions)

**1. get_player()**
```python
def get_player(
    player_name: str,
    league: str,
    season: str,
    use_cache: bool = True
) -> Dict
```
Extract single player with all 11 stat types merged.

**Returns:** Dict with 153 fields:
- Identification (7): player_name, normalized_name, fbref_official_name, team, league, season, url
- Personal (4): nationality, position, age, birth_year
- Performance (142): All stats from 11 types merged

**Example:**
```python
from wrappers import fbref_get_player

player = fbref_get_player("Erling Haaland", "ENG-Premier League", "24-25")
# Returns: {
#     'player_name': 'Erling Haaland',
#     'team': 'Manchester City',
#     'goals': 27,
#     'assists': 5,
#     'expected_goals': 24.3,
#     'shots': 156,
#     ... 148 more fields
# }
```

**2. get_team()**
```python
def get_team(
    team_name: str,
    league: str,
    season: str,
    use_cache: bool = True
) -> Dict
```
Extract single team with all stats merged.

**Returns:** Dict with 190+ fields (all player metrics aggregated)

**3. get_players()**
```python
def get_players(
    players: List[str],
    league: str,
    season: str,
    max_workers: int = 3,
    show_progress: bool = True
) -> pd.DataFrame
```
Batch extract multiple players with parallel processing.

**Returns:** DataFrame with 153 columns, one row per player

**Example:**
```python
players = ["Haaland", "Salah", "Kane"]
df = fbref_get_players(players, "ENG-Premier League", "24-25")
# Returns DataFrame with 3 rows × 153 columns
```

**4. get_teams()**
```python
def get_teams(
    teams: List[str],
    league: str,
    season: str,
    max_workers: int = 3,
    show_progress: bool = True
) -> pd.DataFrame
```
Batch extract multiple teams.

**Returns:** DataFrame with 190+ columns

**5. get_league_players()**
```python
def get_league_players(
    league: str,
    season: str,
    team: Optional[str] = None
) -> pd.DataFrame
```
Extract all players from league (or specific team).

**Returns:** DataFrame with 153 columns, hundreds of rows

**6. get_match_data()**
```python
def get_match_data(
    match_id: str,
    league: str,
    season: str,
    data_type: str = 'all'
) -> Union[pd.DataFrame, Dict]
```
Extract match-level data.

**data_type options:**
- `'all'` - Dict with all types
- `'events'` - Key events (goals, cards, subs)
- `'shots'` - Shot events with xG
- `'lineup'` - Starting XI and subs

**7. get_schedule()**
```python
def get_schedule(league: str, season: str) -> pd.DataFrame
```
Extract complete fixture list with results.

**Returns:** DataFrame with schedule

##### Core Functions (2 main functions)

**extract_data()**
```python
def extract_data(
    entity_name: str,
    entity_type: str,  # 'player' or 'team'
    league: str,
    season: str,
    match_id: Optional[str] = None,
    include_opponent_stats: bool = False,
    use_cache: bool = True
) -> Dict
```
Core extraction function (used by all quick access functions).

**extract_multiple()**
```python
def extract_multiple(
    entities: List[str],
    entity_type: str,
    league: str,
    season: str,
    match_id: Optional[str] = None,
    include_opponent_stats: bool = False,
    max_workers: int = 3,
    show_progress: bool = True,
    use_cache: bool = True
) -> pd.DataFrame
```
Parallel batch extraction with ThreadPoolExecutor.

---

#### understat_data.py - Understat Wrapper (1,130 lines)

Advanced metrics with automatic FBref integration.

##### Quick Access Functions (5 functions)

**1. get_player()**
```python
def get_player(
    player_name: str,
    league: str,
    season: str,
    use_cache: bool = True,
    team_name: Optional[str] = None  # For disambiguation
) -> Dict
```
Extract player with exclusive Understat metrics.

**Returns:** Dict with 15 fields:
- IDs: understat_player_id, understat_team_id
- Basics: position, matches, minutes, goals, assists
- Exclusive: xg, np_xg, xa, xg_chain, xg_buildup, key_passes

**Example:**
```python
from wrappers import understat_get_player

player = understat_get_player(
    "Vinicius Jr",
    "ESP-La Liga",
    "24-25",
    team_name="Real Madrid"  # Helps with name matching
)
# Returns: {
#     'understat_xg_chain': 18.4,
#     'understat_xg_buildup': 12.7,
#     'understat_np_xg': 14.2,
#     'understat_xa': 10.3,
#     ...
# }
```

**2. get_team()**
```python
def get_team(
    team_name: str,
    league: str,
    season: str,
    use_cache: bool = True
) -> Dict
```
Extract team with PPDA and xPts.

**Returns:** Dict with team-level metrics including `ppda_avg`, `expected_points_total`

**3. merge_with_fbref()** ⭐ **KEY INTEGRATION FUNCTION**
```python
def merge_with_fbref(
    fbref_data: Union[Dict, pd.DataFrame],
    league: str,
    season: str,
    data_type: str = 'player',  # or 'team'
    show_progress: bool = True,
    fallback_matching: bool = True
) -> Union[Dict, pd.DataFrame]
```
Automatically enriches FBref data with Understat metrics.

**Logic:**
1. Identifies entities (players/teams) in FBref data
2. Extracts matching Understat data
3. Merges on normalized names
4. Falls back to fuzzy matching if needed
5. Preserves original data if merge fails

**Example:**
```python
# Get base FBref data
fbref_df = fbref_get_players(["Messi", "Ronaldo"], "ESP-La Liga", "23-24")

# Enrich with Understat
enriched_df = understat_merge_with_fbref(fbref_df, "ESP-La Liga", "23-24")

# Result: fbref_df columns + understat_metrics
# Total: 153 FBref + 15 Understat = 168 columns
```

**4. get_shots()**
```python
def get_shots(
    match_id: int,
    league: str,
    season: str,
    player_filter: Optional[str] = None
) -> pd.DataFrame
```
Extract shot events with coordinates and xG.

**Returns:** DataFrame with columns including `location_x`, `location_y`, `xg`

---

#### whoscored_data.py - WhoScored Wrapper (1,250 lines)

Spatial event data with advanced analysis functions.

##### Quick Access Functions (8 functions)

**1. get_match_events()**
```python
def get_match_events(
    match_id: int,
    league: str,
    season: str
) -> pd.DataFrame
```
Extract all match events with x/y coordinates.

**Returns:** DataFrame with 42 columns, typically 1,500-2,000 rows per match

**2. get_match_events_viz()** ⭐ **OPTIMIZED FOR VIZ**
```python
def get_match_events_viz(
    match_id: int,
    league: str,
    season: str
) -> pd.DataFrame
```
Optimized event extraction for visualization pipeline.

**Includes extra processing:**
- Field zone classification (18 zones)
- Distance calculations
- Pass outcome classification
- Ready for viz/match_data.py input

**3. get_pass_network()**
```python
def get_pass_network(
    match_id: int,
    team: str,
    league: str,
    season: str
) -> Dict[str, pd.DataFrame]
```
Extract pass network data.

**Returns:** Dict with 3 DataFrames:
- `'passes'` - Individual pass events
- `'positions'` - Average player positions
- `'connections'` - Pass connections with strength

**4. get_player_heatmap()**
```python
def get_player_heatmap(
    match_id: int,
    player: str,
    league: str,
    season: str
) -> pd.DataFrame
```
Extract player action heatmap data.

**Returns:** DataFrame with x/y coordinates for all player actions

**5. get_shot_map()**
```python
def get_shot_map(
    match_id: int,
    league: str,
    season: str,
    team: Optional[str] = None
) -> pd.DataFrame
```
Extract shot map data.

**Returns:** DataFrame with shot coordinates and outcomes

**6. get_field_occupation()**
```python
def get_field_occupation(
    match_id: int,
    team: str,
    league: str,
    season: str
) -> pd.DataFrame
```
Extract field occupation data by zone.

**Returns:** DataFrame with zone-based statistics

**7. get_schedule()**
```python
def get_schedule(
    league: str,
    season: str
) -> pd.DataFrame
```
Extract complete fixture list.

**8. get_missing_players()**
```python
def get_missing_players(
    match_id: int,
    league: str,
    season: str
) -> pd.DataFrame
```
Extract injured/suspended players.

##### Core Function

**extract_match_events()** - Main extraction with filters
```python
def extract_match_events(
    match_id: int,
    league: str,
    season: str,
    event_filter: Optional[List[str]] = None,
    player_filter: Optional[str] = None,
    team_filter: Optional[str] = None,
    for_viz: bool = False,
    verbose: bool = False,
    use_cache: bool = True
) -> pd.DataFrame
```

**event_filter examples:**
- `['Pass', 'Shot']` - Only passes and shots
- `['Tackle', 'Interception']` - Defensive actions

---

#### transfermarkt_data.py - Transfermarkt Wrapper (118 lines)

Player profile and market value data.

##### Functions (2 functions)

**1. transfermarkt_get_player()**
```python
def transfermarkt_get_player(
    player_name: str,
    league: str,
    season: str,
    birth_year: Optional[int] = None
) -> Dict
```
Extract player profile from Transfermarkt.

**Returns:** Dict with 9 fields:
- `transfermarkt_player_id`
- `transfermarkt_position_specific` - Exact position (e.g., "Left Winger")
- `transfermarkt_primary_foot` - "right", "left", or "both"
- `transfermarkt_market_value_eur` - Current market value
- `transfermarkt_birth_date`
- `transfermarkt_club`
- `transfermarkt_contract_start_date`
- `transfermarkt_contract_end_date`
- `transfermarkt_contract_is_current`

**Example:**
```python
from wrappers import transfermarkt_get_player

player = transfermarkt_get_player(
    "Vinicius Junior",
    "ESP-La Liga",
    "24-25",
    birth_year=2000  # Helps with disambiguation
)
# Returns: {
#     'transfermarkt_market_value_eur': 180000000,
#     'transfermarkt_position_specific': 'Left Winger',
#     'transfermarkt_primary_foot': 'right',
#     ...
# }
```

**2. clear_cache()**
```python
def clear_cache() -> None
```
Clears Transfermarkt wrapper cache.

---

### Database Module (database/)

PostgreSQL persistence layer with unique ID system, parallel loading, and health monitoring.

**Key features:**
- SHA256-based unique IDs (16-char hex)
- JSONB storage for flexible metrics (145+ FBref, 15 Understat, 9 Transfermarkt)
- Connection pooling (5 connections + 10 overflow)
- Automatic retry with exponential backoff
- Parallel loading (3 workers, checkpoints every 25 records)
- Adaptive rate limiting (0.5-3.0s)
- Health monitoring with 8 CLI commands
- 28 indices for query performance

---

#### connection.py - Database Connection (539 lines)

Core database management with connection pooling and ID generation.

##### DatabaseManager Class

**Initialization:**
```python
from database.connection import get_db_manager

db = get_db_manager()
# Reads credentials from .env
# Creates pool: 5 connections + 10 overflow, 30s timeout, 1h recycle
```

**Main Methods:**

**1. connect()**
```python
def connect() -> bool
```
Establishes connection with retry (3 attempts, exponential backoff).

**2. execute_sql_file()**
```python
def execute_sql_file(filepath: str) -> bool
```
Executes SQL file (multi-line support). Used for setup.sql and setup_extras.sql.

**3. insert_player_data()**
```python
def insert_player_data(
    player_data: Dict,
    table_type: str = 'domestic'  # 'domestic', 'european', 'extras'
) -> bool
```
Inserts player with automatic JSON serialization.

**Process:**
1. Validates required fields (player_name, league/competition, season, team)
2. Separates basic fields from JSONB metrics
3. Serializes fbref_metrics, understat_metrics, transfermarkt_metrics to JSON
4. Inserts with retry (2 attempts)
5. Returns True on success

**4. insert_team_data()**
```python
def insert_team_data(
    team_data: Dict,
    table_type: str = 'domestic'
) -> bool
```
Similar to insert_player_data but for teams.

**5. clear_season_data()**
```python
def clear_season_data(
    competition: str,
    season: str,
    table_type: str,
    entity_type: str  # 'player' or 'team'
) -> int
```
Deletes existing data before reload. Returns number of deleted records.

**6. query_players()**
```python
def query_players(
    league: str = None,
    season: str = None,
    team: str = None,
    table_type: str = 'domestic'
) -> pd.DataFrame
```
Queries players with optional filters.

**7. get_transfers_by_unique_id()**
```python
def get_transfers_by_unique_id(
    table_type: str = 'domestic'
) -> pd.DataFrame
```
Finds players who played for multiple teams.

**Returns:** DataFrame with columns:
`[unique_player_id, player_name, league, season, teams_count, teams_path, avg_quality]`

**8. get_unique_entities_count()**
```python
def get_unique_entities_count() -> Dict[str, int]
```
Counts unique entities across all tables.

**Returns:**
```python
{
    'unique_domestic_players': 3261,
    'unique_european_players': 348,
    'unique_domestic_teams': 110,
    'unique_european_teams': 0,
    ...
}
```

##### ID Generation System

**IDGenerator Class:**

**1. generate_player_hash_id()**
```python
@staticmethod
def generate_player_hash_id(
    name: str,
    birth_year: int,
    nationality: str
) -> str
```

**Logic:**
```python
# Example: Erling Haaland
name = "Erling Haaland"      → "erling_haaland"
birth_year = 2000             → "2000"
nationality = "NOR"           → "nor"

combined = "erling_haaland_2000_nor"
hash_obj = hashlib.sha256(combined.encode('utf-8'))
unique_id = hash_obj.hexdigest()[:16]  # "a7f3d9e2b5c8a1f4"
```

**Benefits:**
- Same player = same ID across seasons/teams
- Enables transfer detection
- Enables multi-season tracking

**2. generate_team_hash_id()**
```python
@staticmethod
def generate_team_hash_id(team_name: str, league: str) -> str
```

**Logic:**
```python
# Example: Manchester City
team_name = "Manchester City"      → "manchester_city"
league = "ENG-Premier League"      → "eng_premier_league"

combined = "manchester_city_eng_premier_league"
hash_obj = hashlib.sha256(combined.encode('utf-8'))
unique_id = hash_obj.hexdigest()[:16]  # "b9e4c7a1d6f2e8b3"
```

##### Utility Functions

**validate_data_structure()**
```python
def validate_data_structure(
    data: Dict,
    entity_type: str  # 'player' or 'team'
) -> Dict
```
Validates required fields and ID format before insertion.

**Required for players:**
- player_name, normalized_name
- league (or competition for european)
- season, team
- unique_player_id (16-char hex)

**Required for teams:**
- team_name, normalized_name
- league (or competition)
- season
- unique_team_id (16-char hex)

---

#### data_loader.py - Bulk Loading System (1,194 lines)

Orchestrates parallel data loading with checkpoints and adaptive rate limiting.

##### Configuration (LOAD_CONFIG)

```python
LOAD_CONFIG = {
    'parallel_workers': 3,              # ThreadPoolExecutor workers
    'checkpoint_interval': 25,          # Save progress every N records
    'checkpoint_dir': '.checkpoints',   # Checkpoint storage
    'adaptive_rate_limiting': True,     # Adjust delays based on success
    'min_delay': 0.5,                   # Minimum delay (seconds)
    'max_delay': 3.0,                   # Maximum delay (seconds)
    'initial_delay': 1.0,               # Starting delay
    'block_pause_min': 10,              # Min pause between leagues (minutes)
    'block_pause_max': 20               # Max pause between leagues (minutes)
}
```

##### Key Classes

**1. CheckpointManager**

Manages progress checkpoints for crash recovery.

```python
class CheckpointManager:
    def __init__(self, competition: str, season: str, entity_type: str)

    def save_progress(self, processed_entities: List, stats: Dict, current_index: int)
    def load_progress() -> Optional[Dict]
    def clear_checkpoint()
```

**Checkpoint file:** `.checkpoints/{competition}_{season}_{entity_type}.pkl`
**Expiry:** 24 hours (older checkpoints ignored)

**2. AdaptiveRateLimit**

Adjusts delays based on response times and failures.

```python
class AdaptiveRateLimit:
    def record_request(self, response_time: float, success: bool)
    def get_delay() -> float  # Returns current delay (0.5-3.0s)
    def wait()                # Sleeps for current delay
```

**Logic:**
- Success + fast response → decrease delay (min 0.5s)
- Failure or slow response → increase delay (max 3.0s)
- Gradual adjustment prevents aggressive rate limiting

**3. IDGenerator**

See connection.py documentation above.

##### Main Loading Function

**load_entities()**
```python
def load_entities(
    entity_type: str,      # 'player' or 'team'
    competition: str,      # 'ENG-Premier League'
    season: str,           # '24-25'
    table_type: str        # 'domestic', 'european', 'extras'
) -> Dict[str, int]
```

**Complete workflow:**

1. **Initialize**
   - Connect to database
   - Create checkpoint manager
   - Initialize rate limiter

2. **Clear existing data**
   ```python
   db.clear_season_data(competition, season, table_type, entity_type)
   ```

3. **Extract entity list**
   ```python
   # For players
   from wrappers import fbref_get_league_players
   entities_df = fbref_get_league_players(competition, season)
   # Returns: DataFrame with ['player', 'team'] columns
   ```

4. **Check for checkpoint**
   ```python
   checkpoint = checkpoint_manager.load_progress()
   if checkpoint:
       # Resume from checkpoint
       processed = checkpoint['processed_entities']
       start_index = checkpoint['current_index']
   ```

5. **Parallel processing**
   ```python
   with ThreadPoolExecutor(max_workers=3) as executor:
       futures = []
       for entity in entities[start_index:]:
           future = executor.submit(process_entity, entity, ...)
           futures.append(future)
   ```

6. **Process each entity**
   ```python
   # a. Extract FBref data
   fbref_data = fbref_get_player(name, competition, season)

   # b. Enrich with Understat
   understat_data = understat_get_player(name, competition, season, team)

   # c. Add Transfermarkt
   transfermarkt_data = transfermarkt_get_player(name, competition, season, birth_year)

   # d. Merge all sources
   merged_data = {**fbref_data, **understat_data, **transfermarkt_data}

   # e. Generate unique ID
   unique_id = IDGenerator.generate_player_hash_id(name, birth_year, nationality)
   merged_data['unique_player_id'] = unique_id

   # f. Validate
   validated_data = validate_data_structure(merged_data, 'player')

   # g. Insert
   db.insert_player_data(validated_data, table_type)
   ```

7. **Save checkpoints**
   ```python
   if (count % 25) == 0:
       checkpoint_manager.save_progress(processed, stats, current_index)
   ```

8. **Adaptive rate limiting**
   ```python
   rate_limiter.record_request(response_time, success)
   rate_limiter.wait()  # Sleep for adaptive delay
   ```

9. **Return summary**
   ```python
   return {
       'total': 647,
       'successful': 642,
       'failed': 5,
       'unique_ids': 621,
       'transfers': 26,
       'understat_coverage': 0.985,
       'processing_time_seconds': 683,
       'records_per_second': 0.97
   }
   ```

##### Interactive Menu (main)

```bash
python database/data_loader.py
```

**Menu options:**

```
FootballDecoded Data Loader
════════════════════════════════════════════════════════

1. Load single competition
   → Select league and season
   → Load players and teams for one competition

2. Load Block 1: ENG + ESP + ITA
   → Premier League, La Liga, Serie A
   → 10-20 minute pauses between leagues
   → Total time: ~45 minutes

3. Load Block 2: GER + FRA + Champions League
   → Bundesliga, Ligue 1, UCL
   → 10-20 minute pauses between leagues
   → Total time: ~40 minutes

4. Load Block 3: Extras (7 leagues)
   → POR, NED, BEL, TUR, SCO, SUI, USA
   → 10-20 minute pauses between leagues
   → Total time: ~2 hours

5. Test database connection
   → Verify PostgreSQL connectivity
   → Show connection details

6. Setup database schema
   → Execute setup.sql and setup_extras.sql
   → Create all tables and indices

7. Clear all existing data
   → DELETE from all tables (requires 'YES' confirmation)
   → Warning: This is irreversible!

8. Check database status
   → Execute database_checker.py --full
   → Show health score, data coverage, transfers
```

##### Block Definitions

**Block 1:**
```python
BLOCK_1_COMPETITIONS = [
    ('ENG-Premier League', 'domestic'),
    ('ESP-La Liga', 'domestic'),
    ('ITA-Serie A', 'domestic')
]
```

**Block 2:**
```python
BLOCK_2_COMPETITIONS = [
    ('GER-Bundesliga', 'domestic'),
    ('FRA-Ligue 1', 'domestic'),
    ('INT-Champions League', 'european')
]
```

**Block 3:**
```python
BLOCK_3_EXTRAS = [
    ('POR-Primeira Liga', 'extras'),
    ('NED-Eredivisie', 'extras'),
    ('BEL-Pro League', 'extras'),
    ('TUR-Süper Lig', 'extras'),
    ('SCO-Premiership', 'extras'),
    ('SUI-Super League', 'extras'),
    ('USA-MLS', 'extras')
]
```

---

#### database_checker.py - Health Monitoring (1,018 lines)

Comprehensive database diagnostics with 8 CLI commands.

##### CLI Commands

**1. Default (no args) - Full Status**
```bash
python database/database_checker.py
```
Shows complete status: tables, unique IDs, transfers, quality summary.

**2. --quick - Quick Status**
```bash
python database/database_checker.py --quick
```
Fast overview: unique entities count, total records, transfer count.

**3. --problems - Problem Detection**
```bash
python database/database_checker.py --problems
```
Scans for:
- **Critical:** Duplicate records (same unique_id + league + season + team)
- **Warning:** Invalid ages (<15 or >50), invalid birth_years (<1970 or >2010)
- **Info:** Empty metrics (fbref_metrics = NULL or '{}')

Provides SQL fix queries for each problem.

**4. --health - Health Score**
```bash
python database/database_checker.py --health
```
Calculates 0-100 health score:
- Base: 100 points
- Critical issues: -10 each (max -50)
- Warnings: -5 each (max -30)
- Info issues: -2 each (max -20)
- Low data quality: up to -20
- Large dataset bonus: +5 (>10k records)

**Status categories:**
- 90-100: EXCELLENT
- 70-89: GOOD
- 50-69: NEEDS ATTENTION
- 0-49: CRITICAL

**5. --cleanup - Auto Cleanup (Dry Run)**
```bash
python database/database_checker.py --cleanup
```
Shows what would be cleaned:
- Duplicate removal (keeps MIN(id))
- Invalid value fixing (sets to NULL)
- Empty record deletion

Add `dry_run=False` in code to actually execute.

**6. --full - Complete Analysis**
```bash
python database/database_checker.py --full
```
Runs all checks:
1. Full status
2. Problem detection
3. Health score calculation

**7. --integrity - ID System Check**
```bash
python database/database_checker.py --integrity
```
Verifies unique ID system:
- Missing IDs (unique_player_id = NULL)
- Duplicate IDs (same ID + league + season + team)
- Invalid format (LENGTH != 16 or non-hex characters)

**8. --transfers - Transfer Analysis**
```bash
python database/database_checker.py --transfers
```
Analyzes transfers:
- Players with multiple teams in same season
- Multi-season tracking
- Transfer statistics (avg teams, max teams, 3+ teams count)

##### Key Functions

**detect_data_problems()**
```python
def detect_data_problems(verbose: bool = True) -> Dict[str, List[Dict]]
```

**Returns:**
```python
{
    'critical': [
        {
            'table': 'players_domestic',
            'issue': 'Duplicate records',
            'count': 5,
            'description': '5 duplicate records found',
            'fix_query': 'DELETE FROM ... WHERE id NOT IN ...'
        }
    ],
    'warning': [...],
    'info': [...]
}
```

**calculate_health_score()**
```python
def calculate_health_score(verbose: bool = True) -> int
```
Returns 0-100 score.

**auto_cleanup_database()**
```python
def auto_cleanup_database(
    dry_run: bool = True,
    verbose: bool = True
) -> Dict[str, int]
```

**Returns:**
```python
{
    'duplicates_removed': 5,
    'invalid_records_cleaned': 12,
    'empty_records_removed': 3
}
```

**check_database_status()**
```python
def check_database_status(verbose: bool = True) -> Dict[str, pd.DataFrame]
```

**Returns:** Dict with DataFrames for each table (players_domestic, teams_domestic, etc.)

---

#### setup.sql - Schema Definition (302 lines)

Creates 4 main tables with 28 indices.

##### Table: players_domestic

```sql
CREATE TABLE footballdecoded.players_domestic (
    -- Identification
    id SERIAL PRIMARY KEY,
    unique_player_id VARCHAR(16),                    -- SHA256 hash (16-char hex)

    -- Basic Information
    player_name VARCHAR(200) NOT NULL,
    normalized_name VARCHAR(200) NOT NULL,           -- Lowercase, no accents
    league VARCHAR(50) NOT NULL,                     -- 'ENG-Premier League'
    season VARCHAR(10) NOT NULL,                     -- '24-25'
    team VARCHAR(150) NOT NULL,
    teams_played TEXT,                               -- 'Team A, Team B' if transfer

    -- Demographics
    nationality VARCHAR(3),                          -- ISO code (ENG, ESP, ARG)
    position VARCHAR(10),                            -- GK, DF, MF, FW
    age INTEGER CHECK (age >= 15 AND age <= 50),
    birth_year INTEGER CHECK (birth_year >= 1970 AND birth_year <= 2010),

    -- Metrics (JSONB for flexibility)
    fbref_metrics JSONB,                             -- 145+ metrics from FBref
    understat_metrics JSONB,                         -- 15 metrics from Understat
    transfermarkt_metrics JSONB,                     -- 9 fields from Transfermarkt

    -- Official Names (as appear in source)
    fbref_official_name VARCHAR(200),
    understat_official_name VARCHAR(200),
    transfermarkt_official_name VARCHAR(200),

    -- Data Quality
    data_quality_score DECIMAL(3,2) DEFAULT 1.00 CHECK (data_quality_score >= 0.0 AND data_quality_score <= 1.0),
    processing_warnings TEXT[],                      -- Array of warning messages

    -- Transfer Detection
    is_transfer BOOLEAN DEFAULT FALSE,               -- TRUE if multiple teams
    transfer_count INTEGER DEFAULT 0,                -- Number of teams in season

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP DEFAULT NOW()
);
```

**Typical record:**
- Basic fields: 10 fields (id, names, league, season, team, nationality, position, age, birth_year)
- JSONB fields: 3 fields (fbref_metrics: 145 keys, understat_metrics: 15 keys, transfermarkt_metrics: 9 keys)
- Quality/transfer: 5 fields
- Timestamps: 3 fields
- **Total:** ~180 effective fields per player

##### Table: teams_domestic

```sql
CREATE TABLE footballdecoded.teams_domestic (
    id SERIAL PRIMARY KEY,
    unique_team_id VARCHAR(16),
    team_name VARCHAR(200) NOT NULL,
    normalized_name VARCHAR(200) NOT NULL,
    league VARCHAR(50) NOT NULL,
    season VARCHAR(10) NOT NULL,

    fbref_metrics JSONB,
    understat_metrics JSONB,

    fbref_official_name VARCHAR(200),
    understat_official_name VARCHAR(200),

    data_quality_score DECIMAL(3,2) DEFAULT 1.00,
    processing_warnings TEXT[],

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP DEFAULT NOW()
);
```

##### Table: players_european

```sql
CREATE TABLE footballdecoded.players_european (
    -- Same as players_domestic EXCEPT:
    -- 1. Uses 'competition' field instead of 'league'
    -- 2. NO understat_metrics (Understat doesn't cover European competitions)
    -- 3. NO understat_official_name

    competition VARCHAR(50) NOT NULL,  -- 'INT-Champions League'
    ...
);
```

##### Table: teams_european

```sql
CREATE TABLE footballdecoded.teams_european (
    -- Same as teams_domestic EXCEPT:
    -- 1. Uses 'competition' instead of 'league'
    -- 2. NO understat_metrics
    -- 3. NO understat_official_name

    competition VARCHAR(50) NOT NULL,
    ...
);
```

##### Indices (28 total)

**Unique Indices (prevent duplicates):**
```sql
-- Players domestic
CREATE UNIQUE INDEX idx_players_domestic_unique
ON footballdecoded.players_domestic(unique_player_id, league, season, team)
WHERE unique_player_id IS NOT NULL;

-- Teams domestic
CREATE UNIQUE INDEX idx_teams_domestic_unique
ON footballdecoded.teams_domestic(unique_team_id, league, season)
WHERE unique_team_id IS NOT NULL;

-- Similar for european and extras tables...
```

**Query Performance Indices:**
```sql
-- League/Season lookups (fast filtering)
CREATE INDEX idx_players_domestic_league_season
ON footballdecoded.players_domestic(league, season);

-- Name searches (case-insensitive)
CREATE INDEX idx_players_domestic_names
ON footballdecoded.players_domestic(normalized_name, player_name);

-- Position filtering
CREATE INDEX idx_players_domestic_position_age
ON footballdecoded.players_domestic(position, age)
WHERE position IS NOT NULL;

-- Nationality filtering
CREATE INDEX idx_players_domestic_nationality
ON footballdecoded.players_domestic(nationality)
WHERE nationality IS NOT NULL;

-- Transfer detection
CREATE INDEX idx_players_domestic_transfers
ON footballdecoded.players_domestic(unique_player_id, is_transfer)
WHERE is_transfer = TRUE;

-- Data quality filtering
CREATE INDEX idx_players_domestic_quality
ON footballdecoded.players_domestic(data_quality_score, processing_warnings)
WHERE data_quality_score < 1.0;
```

**JSONB Indices (fast JSON queries):**
```sql
-- GIN indices for JSONB fields (enable ->>, @>, etc. operators)
CREATE INDEX idx_players_domestic_fbref_metrics
ON footballdecoded.players_domestic USING GIN (fbref_metrics)
WHERE fbref_metrics IS NOT NULL;

CREATE INDEX idx_players_domestic_understat_metrics
ON footballdecoded.players_domestic USING GIN (understat_metrics)
WHERE understat_metrics IS NOT NULL;

-- Similar for teams and other tables...
```

**Timestamp Indices:**
```sql
CREATE INDEX idx_players_domestic_created
ON footballdecoded.players_domestic(created_at);

CREATE INDEX idx_players_domestic_updated
ON footballdecoded.players_domestic(updated_at);
```

##### Triggers

```sql
-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION footballdecoded.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_players_domestic_timestamp
BEFORE UPDATE ON footballdecoded.players_domestic
FOR EACH ROW EXECUTE FUNCTION footballdecoded.update_timestamp();

-- Similar triggers for all 6 tables...
```

---

#### setup_extras.sql - Extras Schema (155 lines)

Creates 2 additional tables for extra leagues.

##### Table: players_extras

```sql
CREATE TABLE footballdecoded.players_extras (
    -- IDENTICAL structure to players_domestic
    -- Used for: POR, NED, BEL, TUR, SCO, SUI, USA leagues
    -- Has both fbref_metrics and understat_metrics (POR has Understat coverage)

    id SERIAL PRIMARY KEY,
    unique_player_id VARCHAR(16),
    league VARCHAR(50) NOT NULL,  -- Uses 'league' not 'competition'
    ...
);
```

##### Table: teams_extras

```sql
CREATE TABLE footballdecoded.teams_extras (
    -- IDENTICAL structure to teams_domestic

    id SERIAL PRIMARY KEY,
    unique_team_id VARCHAR(16),
    league VARCHAR(50) NOT NULL,
    ...
);
```

**Indices:** Same 14 indices as domestic tables (unique, query performance, JSONB, timestamps).

---

### Visualization Module (viz/)

Advanced visualization system with 10-step enrichment pipeline and professional design.

**Key features:**
- Processes WhoScored + Understat match data
- 10-step enrichment (carries, xThreat, progressive actions, etc.)
- Generates 5 optimized CSVs (events, aggregates, network, spatial, info)
- 6 visualization types with unified design
- 6 Jupyter templates for workflows
- Colormap: deepskyblue → tomato
- Background: #313332 (dark professional)
- Typography: DejaVu Sans

---

#### match_data.py - Core Processing Pipeline

Processes match data with 10-step enrichment and generates 5 CSV outputs.

##### Main Function

**extract_match_complete()**
```python
def extract_match_complete(
    ws_id: int,                # WhoScored match ID
    us_id: int,                # Understat match ID
    league: str,               # 'ESP-La Liga'
    season: str,               # '24-25'
    home_team: str,            # 'Athletic Club'
    away_team: str,            # 'Barcelona'
    match_date: str            # '2024-08-24'
) -> Dict[str, pd.DataFrame]
```

**Returns:** Dict with 5 DataFrames (also saves as CSV in `viz/data/`)

##### 10-Step Enrichment Pipeline

**Step 1: Carries Detection**
- Detects continuous possession (3-60 units, 1-10 seconds)
- Counts successful take-ons during carry
- Adds `is_carry`, `carry_distance`, `take_ons_in_carry` fields

**Step 2: xThreat Calculation**
- Grid-based threat model (12x8 zones)
- Bilinear interpolation for smooth values
- `xthreat_gen`: Only positive threat changes
- Uses pre-computed threat matrix

**Step 3: Pre-Assists Detection**
- Identifies passes leading to assists
- Marks with `is_pre_assist` boolean
- Tracks `pre_assist_player`

**Step 4: Possession Chains**
- Assigns unique `possession_id` to each possession
- Detects chain breaks (team change, period end, out of play)
- Enables possession-level analysis

**Step 5: Progressive Actions**
- FIFA criteria by field zone:
  - Own half: 30m+ towards opponent goal
  - Crossing halfway: 15m+ minimum
  - Opponent half: 10m+ towards goal
- Marks passes and carries with `is_progressive`

**Step 6: Box Entries**
- Detects entries to penalty area (x ≥ 83, 21.1 ≤ y ≤ 78.9)
- Includes both passes and carries ending in box
- Field `is_box_entry`

**Step 7: Pass Outcomes Classification**
- Categories: Goal, Shot, Assist, Key Pass, Retention, Unsuccessful
- Field `pass_outcome`

**Step 8: Action Type Classification**
- Categories: Offensive, Defensive, Neutral
- Based on event type and context
- Field `action_type`

**Step 9: Zone Classification**
- 18-zone grid (6 horizontal × 3 vertical)
- Field `zone_id` (1-18)
- Enables zone-based heatmaps

**Step 10: xG Merge (Understat)**
- Matches shots by team and minute
- Fuzzy matching (±2 minutes) if exact match fails
- Adds precise xG values to shot events

##### CSV Outputs (5 files)

**1. match_events.csv (55 columns)**

All events enriched with calculated metrics:

```python
Columns:
[
    # Identification (10)
    'game_id', 'match_id', 'period', 'minute', 'second', 'expanded_minute',
    'team_id', 'team', 'player_id', 'player',

    # Event Type (6)
    'type', 'event_type', 'outcome_type', 'is_successful',
    'action_type', 'field_zone',

    # Coordinates (8)
    'x', 'y', 'end_x', 'end_y', 'goal_mouth_y', 'goal_mouth_z',
    'blocked_x', 'blocked_y',

    # Calculated Metrics (13)
    'distance_to_goal', 'pass_distance', 'xthreat', 'xthreat_gen',
    'xg', 'possession_id', 'possession_team', 'zone_id',
    'is_progressive', 'is_box_entry', 'is_pre_assist',
    'is_carry', 'carry_distance',

    # Context (8)
    'qualifiers', 'next_player', 'pass_outcome', 'event_id',
    'take_ons_in_carry', 'is_assist', 'is_shot', 'is_goal',

    # Metadata (2)
    'data_source', 'enrichment_version'
]
```

**Typical size:** 1,500-2,000 rows per match

**2. match_aggregates.csv (36 columns)**

Player and zone aggregates:

```python
# Entity Types: 'player' or 'zone'

# Common fields (11)
[
    'entity_type', 'entity_id', 'entity_name', 'team',
    'total_actions', 'offensive_actions', 'defensive_actions', 'neutral_actions',
    'box_entries', 'xthreat_total', 'xthreat_per_action'
]

# Player-specific (19)
[
    'minutes_active', 'actions_per_minute',
    'avg_x', 'avg_y', 'position_variance_x', 'position_variance_y',
    'passes_attempted', 'passes_completed', 'pass_completion_pct',
    'progressive_passes', 'pre_assists',
    'carries', 'progressive_carries', 'carry_distance_total',
    'passes_to_goal', 'passes_to_shot', 'key_passes',
    'shots', 'goals'
]

# Zone-specific (8)
[
    'zone_id', 'zone_x_center', 'zone_y_center',
    'possession_pct', 'action_density',
    'progressive_actions', 'passes_through_zone', 'successful_passes'
]
```

**Typical size:** 50-70 rows (30-40 players + 36 zone records)

**3. player_network.csv (18 columns)**

Pass network and player positions:

```python
# Record Types: 'connection' or 'position'

# Connection records
[
    'record_type', 'team', 'source_player', 'target_player', 'connection_id',
    'connection_strength',  # Pass count
    'avg_xthreat', 'progressive_passes', 'box_entries', 'pass_distance_avg',
    'avg_x_start', 'avg_y_start', 'avg_x_end', 'avg_y_end'
]

# Position records
[
    'record_type', 'team', 'player',
    'avg_x', 'avg_y',  # Average position
    'position_variance_x', 'position_variance_y',  # Movement spread
    'total_actions', 'minutes_active'
]
```

**Typical size:** 200-300 rows (150-250 connections + 30-40 positions)

**4. spatial_analysis.csv (29 columns)**

Four types of spatial analysis:

```python
# Analysis Types: 'convex_hull', 'pressure_map', 'territorial_control', 'flow_pattern'

# Convex Hull (2 records: home + away)
[
    'analysis_type', 'team',
    'coordinates_json',  # JSON string of hull vertices
    'hull_area', 'hull_perimeter', 'center_x', 'center_y', 'area_percentage'
]

# Pressure Map (36 records: 18 zones × 2 teams)
[
    'analysis_type', 'team', 'zone_id',
    'zone_center_x', 'zone_center_y',
    'pressure_intensity',  # Actions per zone area
    'action_efficiency',   # Successful actions %
    'avg_xthreat', 'xthreat_total', 'progressive_actions'
]

# Territorial Control (6 records: 3 thirds × 2 teams)
[
    'analysis_type', 'team', 'third_name',  # 'defensive', 'middle', 'attacking'
    'x_range_min', 'x_range_max',
    'control_percentage',  # % actions in this third
    'avg_xthreat_per_action', 'box_entries'
]

# Flow Pattern (6 records: 3 directions × 2 teams)
[
    'analysis_type', 'team', 'flow_direction',  # 'forward', 'backward', 'lateral'
    'pass_count', 'avg_distance', 'avg_xthreat',
    'progressive_count', 'flow_efficiency'  # Success rate
]
```

**Typical size:** 50 rows (2 hulls + 36 pressure + 6 control + 6 flow)

**5. match_info.csv (11 columns)**

Match metadata and statistics:

```python
# Info Categories: 'match_metadata', 'team_stats', 'player_participation',
#                  'timeline', 'data_quality'

[
    'info_category', 'info_key', 'info_value', 'team',
    'event_type', 'minute', 'period',
    'first_minute', 'last_minute', 'minutes_active',
    'numeric_value'
]
```

**Content:**
- Match Metadata (8 records): match_id, teams, date, league, season, total_events, duration
- Team Stats (20 records): possession%, passes, accuracy, xthreat, progressive actions, etc.
- Player Participation (30-40 records): minutes played by player
- Timeline (events): Goals, cards, substitutions with timestamps
- Data Quality (6 records): Events with coords, xthreat, outcome, unique players, etc.

**Typical size:** 90-100 rows

---

#### Visualization Functions

##### pass_network.py - Pass Network Plots

**plot_pass_network()**
```python
def plot_pass_network(
    csv_path: str,                  # Path to player_network.csv
    team_name: str,                 # Team to visualize
    period: str = 'full',           # 'full', 'FirstHalf', 'SecondHalf'
    min_connections: int = 5,       # Minimum passes for edge
    logo_path: str = None,          # Team logo
    title_text: str = None,
    subtitle_text: str = None
) -> plt.Figure
```

**Features:**
- Vertical pitch (Opta coordinates 0-100)
- Node size: Linear 5-100 passes (5-30 pt radius)
- Edge width: 3 levels (thin ≤5, medium 5-9, thick ≥9 passes)
- Edge color: xThreat gradient (deepskyblue → tomato)
- Anti-overlap positioning algorithm
- 4-tier legend (thickness, color, size, value)

**Visual Design:**
- Background: #313332
- Pitch lines: white
- Nodes: Team colors with alpha
- Edges: Colormap with alpha 0.6

---

##### shot_xg.py - xG Maps

**plot_shot_xg()**
```python
def plot_shot_xg(
    csv_path: str,                  # Path to match_events.csv (shots only)
    filter_by: str = 'all',         # 'all', team name, or player name
    invert_filter: bool = False,    # Invert selection
    logo_path: str = None,
    title_text: str = None,
    subtitle_text: str = None,
    subsubtitle_text: str = None
) -> plt.Figure
```

**Features:**
- Half-pitch view (attacking half only)
- Markers: Hexagons (foot), circles (head)
- Opacity: Goals 100%, attempts 20%
- Color: xG gradient (deepskyblue → tomato)
- Extreme markers: Lowest xG goal (green), highest xG miss (red)
- Stats panel: Shots, goals, xG, accuracy, efficiency

**Visual Design:**
- Background: #313332
- Half-pitch with goal drawn
- Colorbar with xG scale
- Stats in bottom-right corner

---

##### swarm_radar.py - Comparative Radar Charts

**create_player_radar()**
```python
def create_player_radar(
    df_data: pd.DataFrame,          # Dataset with percentiles
    player_1_id: str,               # unique_player_id
    metrics: List[str],             # Exactly 10 metrics
    metric_titles: List[str],       # Exactly 10 titles
    player_2_id: str = None,        # Optional comparison
    player_1_color: str = '#FF6B6B',
    player_2_color: str = '#4ECDC4',
    team_colors: List = None,       # [[p1_primary, p1_secondary], [p2_primary, p2_secondary]]
    use_swarm: bool = True,         # True: Swarm Radar, False: Traditional
    save_path: str = 'player_radar.png',
    show_plot: bool = True,
    team_logos: Dict = None         # {player_1_id: path1, player_2_id: path2}
) -> None
```

**Two Modes:**

1. **Swarm Radar** (`use_swarm=True`)
   - 10 swarm plots around radar showing distribution
   - Player highlighted in context
   - Population context visible

2. **Traditional Radar** (`use_swarm=False`)
   - Clean radar without distributions
   - Concentric circles for percentiles

**Requirements:**
- Exactly 10 metrics (no more, no less)
- DataFrame must have `{metric}_pct` columns (percentiles 0-100)
- Metrics reordered for visual balance

**Visual Design:**
- Background: #313332
- Radar rings: Alternating colors (single player) or solid (dual)
- Swarm points: Scattered with jitter
- Metric labels: Radial positioning

---

##### stats_table.py - Statistical Tables

**create_stats_table()**
```python
def create_stats_table(
    df_data: pd.DataFrame,
    player_1_id: str,
    metrics: List[str],             # Same 10 as radar
    metric_titles: List[str],
    player_2_id: str = None,
    team_colors: List = None,
    save_path: str = 'stats_table.png',
    show_plot: bool = True,
    team_logos: Dict = None,
    footer_text: str = 'Percentiles vs dataset'
) -> str
```

**Features:**
- Designed to match swarm_radar dimensions
- Color-coded by percentile (unified colormap)
- Shows: Raw value, percentile, context (minutes/matches)
- Alternating row colors for readability
- Team logos in header

**Dimensions:**
- Width: 2320px
- Height: 2755px (matches swarm radar)
- Compatible for side-by-side layout

---

##### Jupyter Templates (6 notebooks)

**1. match_data.ipynb**
Workflow for processing match data (WhoScored + Understat → 5 CSVs).

**2. match_data_BB.ipynb**
Alternative match processing workflow.

**3. pass_network.ipynb**
Template for generating pass network visualizations.

**4. pass_analysis.ipynb**
Template for pass flow and hull analysis.

**5. shots.ipynb**
Template for shot map generation and xG analysis.

**6. swarm_radar.ipynb**
Template for player comparison with swarm plots and statistical tables.

**Usage:**
```bash
# Copy template
cp viz/templates/pass_network.ipynb notebooks/barcelona_network.ipynb

# Edit parameters and run
jupyter notebook notebooks/barcelona_network.ipynb
```

---

## Supported Competitions

Complete list of leagues and competitions with data source coverage.

### Big 5 European Leagues

| League | Code | FBref | Understat | Transfermarkt | Season Format |
|--------|------|-------|-----------|---------------|---------------|
| Premier League | ENG-Premier League | ✅ | ✅ | ✅ | Multi-year (2425) |
| La Liga | ESP-La Liga | ✅ | ✅ | ✅ | Multi-year (2425) |
| Serie A | ITA-Serie A | ✅ | ✅ | ✅ | Multi-year (2425) |
| Bundesliga | GER-Bundesliga | ✅ | ✅ | ✅ | Multi-year (2425) |
| Ligue 1 | FRA-Ligue 1 | ✅ | ✅ | ✅ | Multi-year (2425) |

**Season period:** August - May

### International Competitions

| Competition | Code | FBref | Understat | Season Format |
|------------|------|-------|-----------|---------------|
| Champions League | INT-Champions League | ✅ | ❌ | Multi-year (2425) |
| World Cup | INT-World Cup | ✅ | ❌ | Single-year (2022) |
| European Championship | INT-European Championship | ✅ | ❌ | Single-year (2024) |
| Women's World Cup | INT-Women's World Cup | ✅ | ❌ | Single-year (2023) |
| Copa América | INT-Copa America | ✅ | ❌ | Single-year (2024) |

**Season periods:**
- Champions League: September - May
- World Cup / Euros / Copa: June/July (tournament month)

### Additional European Leagues (7 leagues)

| League | Code | FBref | Understat | Transfermarkt | Season Format |
|--------|------|-------|-----------|---------------|---------------|
| Primeira Liga | POR-Primeira Liga | ✅ | ✅ | ✅ | Multi-year |
| Eredivisie | NED-Eredivisie | ✅ | ❌ | ✅ | Multi-year |
| Pro League | BEL-Pro League | ✅ | ❌ | ✅ | Multi-year |
| Süper Lig | TUR-Süper Lig | ✅ | ❌ | ✅ | Multi-year |
| Premiership | SCO-Premiership | ✅ | ❌ | ✅ | Multi-year |
| Super League | SUI-Super League | ✅ | ❌ | ✅ | Multi-year |
| MLS | USA-MLS | ✅ | ❌ | ✅ | Multi-year |

**Season periods:** Most August - May (MLS: February - November)

### National Cups

| Cup | Code | FBref | Season Format |
|-----|------|-------|---------------|
| Copa del Rey | ESP-Copa del Rey | ✅ | Multi-year |
| FA Cup | ENG-FA Cup | ✅ | Multi-year |
| EFL Cup | ENG-EFL Cup | ✅ | Multi-year |
| Coupe de France | FRA-Coupe de France | ✅ | Multi-year |
| DFB-Pokal | GER-DFB-Pokal | ✅ | Multi-year |
| Coppa Italia | ITA-Coppa Italia | ✅ | Multi-year |

**Note:** Cup competitions typically span full domestic season (August - May).

### Season Code Formats

**Multi-year format:** `YYWW` (e.g., `2425` for 2024-25 season)
- Used for: Domestic leagues, Champions League, most cups
- Spans two calendar years

**Single-year format:** `YYYY` (e.g., `2022` for 2022 World Cup)
- Used for: World Cup, Euros, Copa América
- Tournament held in single calendar year

**Examples:**
```python
# Multi-year
scraper = FBref(leagues="ENG-Premier League", seasons="24-25")  # OK
scraper = FBref(leagues="ENG-Premier League", seasons="2425")   # Also OK (auto-converted)

# Single-year
scraper = FBref(leagues="INT-World Cup", seasons="2022")  # OK
scraper = FBref(leagues="INT-World Cup", seasons="22")    # Also OK (auto-converted)
```

### Data Coverage Summary

**Total Leagues:** 30+

**By Source:**
- FBref: 30+ leagues (most comprehensive)
- Understat: 6 leagues (Big 5 + Portugal)
- Transfermarkt: All domestic leagues
- WhoScored: 20+ leagues (event data)

**Database Tables:**
- `players_domestic` / `teams_domestic` - Big 5 leagues
- `players_european` / `teams_european` - International competitions
- `players_extras` / `teams_extras` - Additional 7 leagues

## Development Standards

### Code Style

```python
# Naming conventions
user_name = "example"          # snake_case for variables/functions
class UserManager:              # PascalCase for classes
MAX_RETRY_COUNT = 3            # UPPER_CASE for constants
_internal_method()             # Leading underscore for private

# Type hints required
def process_data(data: List[Dict]) -> pd.DataFrame:
    """Process with clear types."""

# Docstrings mandatory
def extract_data(league: str, season: str) -> Dict[str, Any]:
    """
    Extract data from source.

    Args:
        league: League identifier (e.g., 'ESP-La Liga')
        season: Season in YY-YY format (e.g., '23-24')

    Returns:
        Dictionary with extracted data

    Raises:
        ValueError: If league or season invalid
    """
```

### Error Handling

```python
# Specific exception handling
try:
    data = scraper.extract()
except ConnectionError as e:
    logger.error(f"Network error: {e}")
    return cached_data
except ValueError as e:
    logger.error(f"Data validation failed: {e}")
    raise
```

### Database Operations

```python
# Always use context managers
with db.engine.begin() as conn:
    conn.execute(query)

# Parameterized queries only
query = text("SELECT * FROM players WHERE league = :league")
conn.execute(query, {"league": league_name})
```

## Configuration Management

### Environment Variables

```bash
# .env file (never commit)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=footballdecoded
DB_USER=your_user
DB_PASSWORD=your_password
```

### League Configuration

All league IDs standardized in `_config.py`:
- Format: `COUNTRY-League Name`
- Examples: `ESP-La Liga`, `ENG-Premier League`, `INT-Champions League`

### Rate Limiting

- FBref: 7 second minimum between requests
- Understat: 5 second minimum
- WhoScored: 10 second minimum
- Block pauses: 30-60 minutes between leagues

## Development Tools

### Environment Management (Conda)

**Instalación inicial**: Ver `CONDA_SETUP.md` para guía completa de instalación de Anaconda.

```bash
# Crear el entorno (primera vez)
conda env create -f environment.yml

# Activar el entorno
conda activate footballdecoded

# Desactivar el entorno
conda deactivate

# Actualizar entorno tras cambios en environment.yml
conda env update -f environment.yml --prune

# Ver paquetes instalados
conda list

# Instalar nuevo paquete
conda install nombre_paquete

# Instalar paquete específico (si no está en conda)
pip install nombre_paquete

# Actualizar paquete
conda update nombre_paquete

# Exportar entorno
conda env export > environment_backup.yml

# Eliminar entorno
conda env remove -n footballdecoded
```

**Workflow diario**:
1. Activar entorno: `conda activate footballdecoded`
2. Trabajar en el proyecto
3. Desactivar al terminar: `conda deactivate`

**Nota importante**: Siempre activa el entorno antes de trabajar. Verás `(footballdecoded)` en tu prompt.

Para más detalles, troubleshooting y comandos avanzados, consulta `CONDA_SETUP.md`.

### Database Tasks

```bash
# Via data_loader.py
python database/data_loader.py
# Options:
# 1. Load single competition
# 2. Load Block 1 (ENG, ESP, ITA)
# 3. Load Block 2 (GER, FRA, Champions)
# 4. Load Block 3: Extras (POR, NED, BEL, TUR, SCO, SUI, USA)
# 5. Test connection
# 6. Setup schema
# 7. Clear data
# 8. Check status
```

## Git Workflow

### Branch Strategy

```
main (protected branch)
  ├── feature/new-visualization
  ├── fix/scraper-timeout
  ├── docs/update-readme
  └── refactor/database-optimization
```

### Branch Naming Conventions

- `feature/` - New functionality
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code improvements without changing functionality
- `test/` - Test additions or modifications

### Workflow Steps

```bash
# 1. Start new task - always from main
git checkout main
git pull origin main
git checkout -b feature/add-new-visualization

# 2. Work on feature with incremental commits
git add -p  # Review changes piece by piece
git commit -m "feat: add base structure for radar chart"
git commit -m "feat: implement data processing for radar"
git commit -m "feat: add styling and export functionality"

# 3. Keep branch updated with main
git fetch origin
git rebase origin/main  # Preferred over merge for cleaner history

# 4. Push to remote
git push origin feature/add-new-visualization

# 5. After approval and merge
git checkout main
git pull origin main
git branch -d feature/add-new-visualization  # Delete local branch
```

### Commit Message Format

Follow conventional commits specification:

```bash
# Format: <type>(<scope>): <subject>

# Types
feat: New feature
fix: Bug fix
docs: Documentation changes
style: Code style changes (formatting, missing semicolons, etc.)
refactor: Code changes that neither fix bugs nor add features
perf: Performance improvements
test: Add or modify tests
chore: Maintenance tasks

# Examples
git commit -m "feat(scrapers): add retry logic for FBref timeout"
git commit -m "fix(database): resolve connection pool exhaustion"
git commit -m "docs: update wrappers API documentation"
git commit -m "refactor(viz): simplify pass network calculation"
```

### Protected Branch Rules

Main branch protection:
- Dismiss stale reviews on new commits
- Require status checks to pass
- No direct pushes to main
- Include administrators in restrictions

## Claude Code Configuration

### Initial Setup

```bash
# Skip permission prompts for faster workflow
claude --dangerously-skip-permissions

# Configure terminal for better experience
/terminal-setup

# Clear chat between different tasks
/clear
```

### Best Practices

**File Operations**
- Shift+drag to reference files (not regular drag)
- Control+V to paste images (not Command+V)
- Use `@filename` to reference specific files

**Chat Management**
- Queue multiple prompts for batch processing
- Escape to stop Claude (not Control+C)
- Escape twice to see message history
- Up arrow to navigate previous commands

### Project Context (CLAUDE.md)

CLAUDE.md files provide project context hierarchically:
- Root `CLAUDE.md` - Project overview and standards
- Subdirectory `README.md` - Module-specific guidelines
- More specific files take precedence

Example structure:
```
CLAUDE.md                    # Project-wide
├── scrapers/README.md       # Scraper-specific
└── viz/README.md            # Visualization-specific
```

## Data Quality Assurance

### Validation Pipeline

1. **Type checking**: Pydantic models for all data structures
2. **Range validation**: Statistical outlier detection
3. **Completeness scoring**: Track missing fields
4. **Normalization**: Consistent naming and formats
5. **Deduplication**: SHA256-based unique IDs

### Quality Metrics

Each record includes:
- `data_quality_score`: 0.0 to 1.0 quality indicator
- `processing_warnings`: List of issues found
- `last_updated`: Timestamp of last update
- `source_reliability`: Source-specific confidence

## Security Considerations

### API Keys and Credentials

- Never hardcode credentials
- Use environment variables exclusively
- Rotate database passwords regularly
- Implement least privilege principle

### Web Scraping Ethics

- Respect robots.txt
- Implement proper rate limiting
- Use random delays between requests
- Rotate user agents and proxies
- Cache aggressively to minimize requests

### Data Privacy

- No personal data collection
- Aggregate statistics only
- Comply with GDPR requirements
- Regular data purging policies

## References

### Internal Documentation

- **Wrappers API**: See `wrappers/README.md` for complete function reference
- **Visualization Guide**: See `viz/README.md` for plotting documentation
- **Database Schema**: See `database/setup.sql` for table definitions

### External Resources

- [FBref Data Dictionary](https://fbref.com/en/about/datafeed)
- [Understat API Structure](https://understat.com/)
- [WhoScored Event Types](https://www.whoscored.com/)
- [PostgreSQL Best Practices](https://wiki.postgresql.org/wiki/Main_Page)

## Contributing Guidelines

### Code Review Criteria

- Functionality correctness
- Documentation completeness
- Security implications
- Code style compliance
- Test coverage adequacy

### Review Process

1. Self-review before requesting reviews
2. Address all CI/CD warnings
3. Respond to feedback constructively
4. Request re-review after changes
5. Squash commits before merge

---

**Remember**: This guide is the single source of truth for development. Keep it updated as the project evolves. When using Claude Code, reference this guide for consistent development practices.