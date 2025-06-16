-- ====================================================================
-- FootballDecoded Database Schema - Sistema de IDs Únicos
-- ====================================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE SCHEMA IF NOT EXISTS footballdecoded;

-- ====================================================================
-- TABLES
-- ====================================================================

CREATE TABLE IF NOT EXISTS footballdecoded.players_domestic (
    id SERIAL PRIMARY KEY,
    unique_player_id VARCHAR(16),
    player_name VARCHAR(200) NOT NULL,
    normalized_name VARCHAR(200) NOT NULL,
    league VARCHAR(50) NOT NULL,
    season VARCHAR(10) NOT NULL,
    team VARCHAR(150) NOT NULL,
    teams_played TEXT,
    nationality VARCHAR(3),
    position VARCHAR(10),
    age INTEGER CHECK (age >= 15 AND age <= 50),
    birth_year INTEGER CHECK (birth_year >= 1970 AND birth_year <= 2010),
    fbref_metrics JSONB,
    understat_metrics JSONB,
    fbref_official_name VARCHAR(200),
    understat_official_name VARCHAR(200),
    data_quality_score DECIMAL(3,2) DEFAULT 1.00 CHECK (data_quality_score >= 0.0 AND data_quality_score <= 1.0),
    processing_warnings TEXT[],
    is_transfer BOOLEAN DEFAULT FALSE,
    transfer_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS footballdecoded.players_european (
    id SERIAL PRIMARY KEY,
    unique_player_id VARCHAR(16),
    player_name VARCHAR(200) NOT NULL,
    normalized_name VARCHAR(200) NOT NULL,
    competition VARCHAR(50) NOT NULL,
    season VARCHAR(10) NOT NULL,
    team VARCHAR(150) NOT NULL,
    teams_played TEXT,
    nationality VARCHAR(3),
    position VARCHAR(10),
    age INTEGER CHECK (age >= 15 AND age <= 50),
    birth_year INTEGER CHECK (birth_year >= 1970 AND birth_year <= 2010),
    fbref_metrics JSONB,
    fbref_official_name VARCHAR(200),
    data_quality_score DECIMAL(3,2) DEFAULT 1.00 CHECK (data_quality_score >= 0.0 AND data_quality_score <= 1.0),
    processing_warnings TEXT[],
    is_transfer BOOLEAN DEFAULT FALSE,
    transfer_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS footballdecoded.teams_domestic (
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
    data_quality_score DECIMAL(3,2) DEFAULT 1.00 CHECK (data_quality_score >= 0.0 AND data_quality_score <= 1.0),
    processing_warnings TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS footballdecoded.teams_european (
    id SERIAL PRIMARY KEY,
    unique_team_id VARCHAR(16),
    team_name VARCHAR(200) NOT NULL,
    normalized_name VARCHAR(200) NOT NULL,
    competition VARCHAR(50) NOT NULL,
    season VARCHAR(10) NOT NULL,
    fbref_metrics JSONB,
    fbref_official_name VARCHAR(200),
    data_quality_score DECIMAL(3,2) DEFAULT 1.00 CHECK (data_quality_score >= 0.0 AND data_quality_score <= 1.0),
    processing_warnings TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP DEFAULT NOW()
);

-- ====================================================================
-- ADD MISSING COLUMNS
-- ====================================================================

ALTER TABLE footballdecoded.players_domestic ADD COLUMN IF NOT EXISTS unique_player_id VARCHAR(16);
ALTER TABLE footballdecoded.players_european ADD COLUMN IF NOT EXISTS unique_player_id VARCHAR(16);
ALTER TABLE footballdecoded.teams_domestic ADD COLUMN IF NOT EXISTS unique_team_id VARCHAR(16);
ALTER TABLE footballdecoded.teams_european ADD COLUMN IF NOT EXISTS unique_team_id VARCHAR(16);

-- ====================================================================
-- INDEXES
-- ====================================================================

CREATE UNIQUE INDEX IF NOT EXISTS idx_players_domestic_unique 
    ON footballdecoded.players_domestic(unique_player_id, league, season, team)
    WHERE unique_player_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_players_european_unique 
    ON footballdecoded.players_european(unique_player_id, competition, season, team)
    WHERE unique_player_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_teams_domestic_unique 
    ON footballdecoded.teams_domestic(unique_team_id, league, season)
    WHERE unique_team_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_teams_european_unique 
    ON footballdecoded.teams_european(unique_team_id, competition, season)
    WHERE unique_team_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_players_domestic_league_season 
    ON footballdecoded.players_domestic(league, season);

CREATE INDEX IF NOT EXISTS idx_players_european_competition_season 
    ON footballdecoded.players_european(competition, season);

CREATE INDEX IF NOT EXISTS idx_teams_domestic_league_season 
    ON footballdecoded.teams_domestic(league, season);

CREATE INDEX IF NOT EXISTS idx_teams_european_competition_season 
    ON footballdecoded.teams_european(competition, season);

-- ====================================================================
-- TRIGGERS - SIMPLE VERSION
-- ====================================================================

CREATE OR REPLACE FUNCTION footballdecoded.update_timestamp()
RETURNS TRIGGER AS 
'BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;'
LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_players_domestic_timestamp ON footballdecoded.players_domestic;
CREATE TRIGGER update_players_domestic_timestamp 
    BEFORE UPDATE ON footballdecoded.players_domestic 
    FOR EACH ROW EXECUTE FUNCTION footballdecoded.update_timestamp();

DROP TRIGGER IF EXISTS update_players_european_timestamp ON footballdecoded.players_european;
CREATE TRIGGER update_players_european_timestamp 
    BEFORE UPDATE ON footballdecoded.players_european 
    FOR EACH ROW EXECUTE FUNCTION footballdecoded.update_timestamp();

DROP TRIGGER IF EXISTS update_teams_domestic_timestamp ON footballdecoded.teams_domestic;
CREATE TRIGGER update_teams_domestic_timestamp 
    BEFORE UPDATE ON footballdecoded.teams_domestic 
    FOR EACH ROW EXECUTE FUNCTION footballdecoded.update_timestamp();

DROP TRIGGER IF EXISTS update_teams_european_timestamp ON footballdecoded.teams_european;
CREATE TRIGGER update_teams_european_timestamp 
    BEFORE UPDATE ON footballdecoded.teams_european 
    FOR EACH ROW EXECUTE FUNCTION footballdecoded.update_timestamp();