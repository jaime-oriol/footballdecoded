# CLAUDE.md - FootballDecoded Development Guide

## Core Philosophy

**Ve paso a paso, uno a uno. Despacio es el camino más rápido. Escribe siempre el código lo más compacto y conciso posible, y que cumpla exactamente lo pedido al 100%. Sin emojis ni florituras. Usa nombres claros y estándar. Incluye solo comentarios útiles y necesarios.**

### Development Principles

- **KISS (Keep It Simple, Stupid)**: Choose straightforward solutions over complex ones
- **YAGNI (You Aren't Gonna Need It)**: Implement features only when needed
- **Fail Fast**: Check for errors early and raise exceptions immediately
- **Single Responsibility**: Each function, class, and module has one clear purpose
- **Dependency Inversion**: High-level modules depend on abstractions, not implementations

## Repository Structure

```
FootballDecoded/
├── scrappers/              # Data extraction from web sources
│   ├── _common.py          # Base classes for scrapers (BaseRequestsReader, BaseSeleniumReader)
│   ├── _config.py          # Global configuration, paths, league mappings
│   ├── fbref.py            # FBref.com scraper for comprehensive stats
│   ├── understat.py        # Understat.com scraper for advanced metrics
│   └── whoscored.py        # WhoScored.com scraper for spatial/event data
│
├── wrappers/               # Simplified API for scrapers (see wrappers/README.md)
│   ├── __init__.py         # Exports all wrapper functions
│   ├── fbref_data.py       # FBref wrapper with caching and error handling
│   ├── understat_data.py   # Understat wrapper with merge capabilities
│   └── whoscored_data.py   # WhoScored wrapper for match events
│
├── database/               # PostgreSQL data persistence
│   ├── connection.py       # DatabaseManager class, connection pooling
│   ├── data_loader.py      # Bulk data loading with progress tracking
│   ├── database_checker.py # Database status and integrity checks
│   └── setup.sql           # Schema definition (players, teams tables)
│
├── viz/                    # Visualization system (see viz/README.md)
│   ├── data/              # CSV outputs for visualization
│   ├── templates/         # Jupyter notebook templates
│   ├── match_data.py      # Match data processing and aggregation
│   ├── pass_network.py    # Pass network visualization
│   ├── pass_analysis.py   # Pass flow and hull analysis
│   ├── shot_map_report.py # Shot maps with xG overlay
│   ├── shot_xg.py         # xG analysis and visualization
│   ├── swarm_radar.py     # Player comparison radar charts
│   └── stats_table.py     # Statistical comparison tables
│
├── blog/                   # Blog assets and notebooks
│   ├── logos/             # Team logos organized by league
│   │   ├── LaLiga/        # Example: FC Barcelona.png
│   │   └── [Other leagues...]
│   └── notebooks/         # Analysis notebooks for blog posts
│
├── pyproject.toml         # Poetry dependencies and project metadata
├── poetry.lock            # Locked dependency versions
├── Makefile              # Common tasks automation
├── LICENSE.rst           # Project license
└── README.rst            # Project overview
```

## Module Documentation

### Scrapers Module

**_common.py**
Base infrastructure for all scrapers. Provides `BaseRequestsReader` for HTTP-based scraping and `BaseSeleniumReader` for JavaScript-heavy sites. Handles rate limiting, proxy rotation, and caching.

**_config.py**
Central configuration hub. Defines `LEAGUE_DICT` for league ID mapping across sources, data directories, and global constants. All league standardization happens here.

**fbref.py**
Primary statistics source. Extracts 11 different stat types (standard, shooting, passing, etc.) for players and teams. Handles the "Big 5 European Leagues Combined" special case efficiently.

**understat.py**
Advanced metrics specialist. Provides xG, xA, PPDA, and other model-based statistics not available in FBref. Uses regex to extract JavaScript variables from HTML.

**whoscored.py**
Spatial and event data extraction. Requires Selenium for JavaScript rendering. Captures match events with x,y coordinates for passes, shots, and all ball actions.

### Wrappers Module

Simplified, high-level API for data extraction. Key functions:
- `fbref_get_player()`, `fbref_get_team()`: Single entity extraction
- `understat_merge_with_fbref()`: Automatic data enrichment
- `whoscored_get_match_events()`: Quick match event access

See `wrappers/README.md` for complete API documentation.

### Database Module

**connection.py**
PostgreSQL connection management using SQLAlchemy. Implements connection pooling, automatic reconnection, and transaction handling. Supports both raw SQL and ORM operations.

**data_loader.py**
Orchestrates bulk data loading with:
- ID generation system using SHA256 hashing
- Data normalization and validation
- Progress tracking with colored terminal output
- Block loading strategy for rate limit compliance
- Automatic FBref + Understat data merging

**database_checker.py**
Database health monitoring. Checks table existence, data completeness, and generates statistics reports.

**setup.sql**
Schema definition with four main tables:
- `players_domestic`: Domestic league player stats
- `teams_domestic`: Domestic league team stats
- `players_european`: European competition player stats
- `teams_european`: European competition team stats

### Visualization Module

**match_data.py**
Core data processing for visualizations. Generates five optimized CSV outputs:
- `match_events.csv`: All events with coordinates
- `match_aggregates.csv`: Player/team/zone statistics
- `player_network.csv`: Pass connections and positions
- `spatial_analysis.csv`: Heatmaps and field coverage
- `match_info.csv`: Match metadata

**pass_network.py**
Creates publication-quality pass network visualizations. Shows player positions, pass connections weighted by frequency, and team formation analysis.

**swarm_radar.py**
Player comparison tool using pizza/radar charts. Supports both swarm plots (distribution context) and traditional radar comparisons.

**shot_map_report.py**
Shot location visualization with xG values. Differentiates goals, saved shots, and misses with appropriate styling.

See `viz/README.md` for detailed visualization documentation.

## Data Pipeline Architecture

```
1. EXTRACTION (scrappers/)
   ├── FBref → Comprehensive statistics
   ├── Understat → Advanced metrics
   └── WhoScored → Spatial data
       ↓
2. SIMPLIFICATION (wrappers/)
   ├── Unified API
   ├── Error handling
   └── Automatic merging
       ↓
3. STORAGE (database/)
   ├── PostgreSQL persistence
   ├── ID standardization
   └── Quality scoring
       ↓
4. VISUALIZATION (viz/)
   ├── Data aggregation
   ├── CSV generation
   └── Plot creation
```

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

### Claude Memory System

- Use `#` to save project preferences automatically
- CLAUDE.md files are hierarchical (project level takes precedence over subdirectories)
- Local preferences in `.claude/memory` (git-ignored)
- Global preferences apply across all projects

## Development Tools

### Package Management (Poetry)

```bash
# Install dependencies
poetry install

# Add new package
poetry add package-name

# Development dependency
poetry add --dev pytest

# Update dependencies
poetry update
```

### Common Tasks (Makefile)

```bash
make setup          # Initial setup
make test          # Run tests
make lint          # Code quality checks
make format        # Auto-format code
make clean         # Remove artifacts
```

### Database Tasks

```bash
# Via data_loader.py
python database/data_loader.py
# Options:
# 1. Load single competition
# 2. Load Block 1 (ENG, ESP, ITA)
# 3. Load Block 2 (GER, FRA, Champions)
# 4. Test connection
# 5. Setup schema
# 6. Clear data
# 7. Check status
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

### Merge Strategy

- **Squash and merge**: For feature branches with multiple small commits
- **Rebase and merge**: For clean, logical commit history
- **Merge commit**: Only for major branches or releases

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

## Performance Optimization

### Batch Processing

- Use `extract_multiple()` for bulk operations
- Process entire leagues before moving to next
- Implement random delays between requests
- Maximum 10 retries for failed requests

### Database Optimization

- Connection pooling (max 5 connections)
- Batch inserts (1000 records at a time)
- Index on commonly queried fields
- Partitioning by season for large tables

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