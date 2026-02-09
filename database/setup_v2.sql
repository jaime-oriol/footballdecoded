-- ====================================================================
-- FootballDecoded v2 Database Schema
-- ====================================================================
-- Unified schema merging 3 sources: FotMob + Understat + Transfermarkt
-- 4 tables: players, teams, understat_team_matches, understat_shots
-- Metrics stored as JSONB for flexibility (different key counts per source)
-- ====================================================================

-- Create isolated schema (does not affect footballdecoded v1)
CREATE SCHEMA IF NOT EXISTS footballdecoded_v2;

-- ====================================================================
-- TRIGGER FUNCTION: auto-update updated_at on row changes
-- ====================================================================

CREATE OR REPLACE FUNCTION footballdecoded_v2.update_timestamp()
RETURNS TRIGGER AS
'BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;'
LANGUAGE plpgsql;

-- ====================================================================
-- TABLE 1: PLAYERS (one row per player per league per season)
-- ====================================================================
-- fotmob_metrics:       ~29 keys (goals, xG, xA, rating, tackles...)
-- understat_metrics:    ~27 keys (xG chain, buildup, per90s...) NULL for non-Big5
-- transfermarkt_metrics: ~9 keys (position, foot, market value, contract...)

CREATE TABLE IF NOT EXISTS footballdecoded_v2.players (
    id SERIAL PRIMARY KEY,                          -- Auto-increment PK
    unique_player_id VARCHAR(16),                   -- SHA256(name+birth_year+nationality)[:16]
    player_name VARCHAR(200) NOT NULL,              -- Original name from FotMob
    normalized_name VARCHAR(200) NOT NULL,           -- Lowercase, no accents, for search
    league VARCHAR(50) NOT NULL,                    -- "ESP-La Liga", "ENG-Premier League", etc.
    season VARCHAR(10) NOT NULL,                    -- "2425", "2526" (parsed format)
    team VARCHAR(150) NOT NULL,                     -- Team name (resolved from fotmob_team_id)
    nationality VARCHAR(3),                         -- 3-letter country code
    position VARCHAR(10),                           -- From Transfermarkt (LW, CB, CDM...)
    age INTEGER,                                    -- Age at season start
    birth_year INTEGER,                             -- For unique ID generation
    fotmob_metrics JSONB,                           -- All FotMob stats as JSON
    understat_metrics JSONB,                        -- All Understat stats as JSON (Big 5 only)
    transfermarkt_metrics JSONB,                    -- All Transfermarkt data as JSON
    fotmob_id INTEGER,                              -- FotMob player ID
    fotmob_name VARCHAR(200),                       -- Name as it appears on FotMob
    understat_id INTEGER,                           -- Understat player ID
    understat_name VARCHAR(200),                    -- Name as it appears on Understat
    transfermarkt_id VARCHAR(20),                   -- Transfermarkt player ID
    data_quality_score DECIMAL(3,2) DEFAULT 1.00,   -- 0.00-1.00 quality indicator
    processing_warnings TEXT[],                     -- Array of issues found during load
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ====================================================================
-- TABLE 2: TEAMS (one row per team per league per season)
-- ====================================================================
-- fotmob_metrics:      ~29 keys (xG, possession, clean sheets, attendance...)
-- understat_metrics:   ~26 keys (xG, PPDA, goals, xG against...) Big 5 only
-- understat_advanced:  ~200 keys (7 categories: situation, formation, gameState,
--                       timing, shotZone, attackSpeed, result) Big 5 only

CREATE TABLE IF NOT EXISTS footballdecoded_v2.teams (
    id SERIAL PRIMARY KEY,
    unique_team_id VARCHAR(16),                     -- SHA256(team_name+league)[:16]
    team_name VARCHAR(200) NOT NULL,
    normalized_name VARCHAR(200) NOT NULL,
    league VARCHAR(50) NOT NULL,
    season VARCHAR(10) NOT NULL,
    fotmob_metrics JSONB,                           -- FotMob team stats
    understat_metrics JSONB,                        -- Understat basic team stats (Big 5)
    understat_advanced JSONB,                       -- Understat advanced breakdowns (Big 5)
    fotmob_id INTEGER,
    fotmob_name VARCHAR(200),
    understat_name VARCHAR(200),
    data_quality_score DECIMAL(3,2) DEFAULT 1.00,
    processing_warnings TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ====================================================================
-- TABLE 3: UNDERSTAT TEAM MATCHES (Big 5 only)
-- ====================================================================
-- One row per team per match (so each match = 2 rows: home + away)
-- Contains xG, PPDA, deep completions, expected points per match

CREATE TABLE IF NOT EXISTS footballdecoded_v2.understat_team_matches (
    id SERIAL PRIMARY KEY,
    unique_team_id VARCHAR(16),                     -- Links to teams table
    team_name VARCHAR(200) NOT NULL,
    league VARCHAR(50) NOT NULL,
    season VARCHAR(10) NOT NULL,
    match_id INTEGER NOT NULL,                      -- Understat match ID
    match_date TIMESTAMP,
    opponent VARCHAR(200),
    is_home BOOLEAN,                                -- True = home, False = away
    goals INTEGER,
    goals_against INTEGER,
    xg DECIMAL(5,2),                                -- Expected goals
    xg_against DECIMAL(5,2),                        -- Opponent expected goals
    np_xg DECIMAL(5,2),                             -- Non-penalty xG
    np_xg_against DECIMAL(5,2),
    ppda DECIMAL(5,2),                              -- Passes per defensive action
    ppda_against DECIMAL(5,2),
    deep_completions INTEGER,                       -- Passes completed within 20m of goal
    deep_completions_against INTEGER,
    points INTEGER,                                 -- 3/1/0
    expected_points DECIMAL(5,2),                   -- Based on xG model
    np_xg_difference DECIMAL(5,2),                  -- np_xg - np_xg_against
    result VARCHAR(1),                              -- W/D/L
    forecast_win DECIMAL(4,3),                      -- Pre-match win probability
    forecast_draw DECIMAL(4,3),
    forecast_loss DECIMAL(4,3),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ====================================================================
-- TABLE 4: UNDERSTAT SHOTS (Big 5 only)
-- ====================================================================
-- One row per shot event with xG, coordinates, and context

CREATE TABLE IF NOT EXISTS footballdecoded_v2.understat_shots (
    id SERIAL PRIMARY KEY,
    league VARCHAR(50) NOT NULL,
    season VARCHAR(10) NOT NULL,
    match_id INTEGER NOT NULL,                      -- Understat match ID
    shot_id INTEGER,                                -- Unique shot ID within match
    team VARCHAR(200),
    player VARCHAR(200),
    player_id INTEGER,                              -- Understat player ID
    assist_player VARCHAR(200),
    minute INTEGER,
    xg DECIMAL(5,4),                                -- Shot expected goals (0.0000-1.0000)
    location_x DECIMAL(6,4),                        -- Pitch X coordinate (0-1)
    location_y DECIMAL(6,4),                        -- Pitch Y coordinate (0-1)
    body_part VARCHAR(20),                          -- Right Foot, Left Foot, Other
    situation VARCHAR(30),                          -- Open Play, Set Piece, From Corner...
    result VARCHAR(30),                             -- Goal, Saved Shot, Blocked Shot...
    created_at TIMESTAMP DEFAULT NOW()
);

-- ====================================================================
-- UNIQUE INDEXES (prevent duplicate records)
-- ====================================================================

-- One player per team per league per season
CREATE UNIQUE INDEX IF NOT EXISTS idx_v2_players_unique
    ON footballdecoded_v2.players(unique_player_id, league, season, team)
    WHERE unique_player_id IS NOT NULL;

-- One team per league per season
CREATE UNIQUE INDEX IF NOT EXISTS idx_v2_teams_unique
    ON footballdecoded_v2.teams(unique_team_id, league, season)
    WHERE unique_team_id IS NOT NULL;

-- One record per team per match
CREATE UNIQUE INDEX IF NOT EXISTS idx_v2_team_matches_unique
    ON footballdecoded_v2.understat_team_matches(unique_team_id, match_id)
    WHERE unique_team_id IS NOT NULL;

-- One record per shot per match
CREATE UNIQUE INDEX IF NOT EXISTS idx_v2_shots_unique
    ON footballdecoded_v2.understat_shots(match_id, shot_id)
    WHERE shot_id IS NOT NULL;

-- ====================================================================
-- B-TREE INDEXES (fast lookups)
-- ====================================================================

-- League + season filtering (used in every query)
CREATE INDEX IF NOT EXISTS idx_v2_players_league_season
    ON footballdecoded_v2.players(league, season);

CREATE INDEX IF NOT EXISTS idx_v2_teams_league_season
    ON footballdecoded_v2.teams(league, season);

CREATE INDEX IF NOT EXISTS idx_v2_team_matches_league_season
    ON footballdecoded_v2.understat_team_matches(league, season);

CREATE INDEX IF NOT EXISTS idx_v2_shots_league_season
    ON footballdecoded_v2.understat_shots(league, season);

-- Name search (for player/team lookups)
CREATE INDEX IF NOT EXISTS idx_v2_players_normalized_name
    ON footballdecoded_v2.players(normalized_name);

CREATE INDEX IF NOT EXISTS idx_v2_teams_normalized_name
    ON footballdecoded_v2.teams(normalized_name);

-- Match date (for time-based queries)
CREATE INDEX IF NOT EXISTS idx_v2_team_matches_date
    ON footballdecoded_v2.understat_team_matches(match_date);

-- Player shot history (for per-player shot analysis)
CREATE INDEX IF NOT EXISTS idx_v2_shots_player_season
    ON footballdecoded_v2.understat_shots(player_id, season);

-- ====================================================================
-- GIN INDEXES (JSONB key/value queries)
-- ====================================================================

-- Allow queries like: WHERE fotmob_metrics @> '{"fotmob_goals": 10}'
CREATE INDEX IF NOT EXISTS idx_v2_players_fotmob_metrics
    ON footballdecoded_v2.players USING GIN (fotmob_metrics)
    WHERE fotmob_metrics IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_v2_players_understat_metrics
    ON footballdecoded_v2.players USING GIN (understat_metrics)
    WHERE understat_metrics IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_v2_players_transfermarkt_metrics
    ON footballdecoded_v2.players USING GIN (transfermarkt_metrics)
    WHERE transfermarkt_metrics IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_v2_teams_fotmob_metrics
    ON footballdecoded_v2.teams USING GIN (fotmob_metrics)
    WHERE fotmob_metrics IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_v2_teams_understat_metrics
    ON footballdecoded_v2.teams USING GIN (understat_metrics)
    WHERE understat_metrics IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_v2_teams_understat_advanced
    ON footballdecoded_v2.teams USING GIN (understat_advanced)
    WHERE understat_advanced IS NOT NULL;

-- ====================================================================
-- TRIGGERS (auto-update timestamps on row modification)
-- ====================================================================

DROP TRIGGER IF EXISTS update_v2_players_timestamp ON footballdecoded_v2.players;
CREATE TRIGGER update_v2_players_timestamp
    BEFORE UPDATE ON footballdecoded_v2.players
    FOR EACH ROW EXECUTE FUNCTION footballdecoded_v2.update_timestamp();

DROP TRIGGER IF EXISTS update_v2_teams_timestamp ON footballdecoded_v2.teams;
CREATE TRIGGER update_v2_teams_timestamp
    BEFORE UPDATE ON footballdecoded_v2.teams
    FOR EACH ROW EXECUTE FUNCTION footballdecoded_v2.update_timestamp();

-- ====================================================================
-- CONSTRAINTS (validate unique ID format: 16-char hex string)
-- ====================================================================

DO $$
BEGIN
    BEGIN
        ALTER TABLE footballdecoded_v2.players DROP CONSTRAINT IF EXISTS chk_v2_players_uid_format;
        ALTER TABLE footballdecoded_v2.teams DROP CONSTRAINT IF EXISTS chk_v2_teams_uid_format;
    EXCEPTION
        WHEN undefined_object THEN null;
    END;
END $$;

ALTER TABLE footballdecoded_v2.players
    ADD CONSTRAINT chk_v2_players_uid_format
    CHECK (unique_player_id IS NULL OR length(unique_player_id) = 16);

ALTER TABLE footballdecoded_v2.teams
    ADD CONSTRAINT chk_v2_teams_uid_format
    CHECK (unique_team_id IS NULL OR length(unique_team_id) = 16);
