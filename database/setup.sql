-- ====================================================================
-- FootballDecoded Database Schema - Sistema de IDs Únicos
-- ====================================================================

-- Note: PostGIS and btree_gist extensions removed for compatibility
-- These can be added later by a superuser if needed for spatial operations

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
-- OPTIMIZED INDEXES
-- ====================================================================

-- Unique indexes for data integrity
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

-- Query performance indexes
CREATE INDEX IF NOT EXISTS idx_players_domestic_league_season 
    ON footballdecoded.players_domestic(league, season);

CREATE INDEX IF NOT EXISTS idx_players_european_competition_season 
    ON footballdecoded.players_european(competition, season);

CREATE INDEX IF NOT EXISTS idx_teams_domestic_league_season 
    ON footballdecoded.teams_domestic(league, season);

CREATE INDEX IF NOT EXISTS idx_teams_european_competition_season 
    ON footballdecoded.teams_european(competition, season);

-- Player name search indexes
CREATE INDEX IF NOT EXISTS idx_players_domestic_names 
    ON footballdecoded.players_domestic(normalized_name, player_name);

CREATE INDEX IF NOT EXISTS idx_players_european_names 
    ON footballdecoded.players_european(normalized_name, player_name);

-- Team name search indexes
CREATE INDEX IF NOT EXISTS idx_teams_domestic_names 
    ON footballdecoded.teams_domestic(normalized_name, team_name);

CREATE INDEX IF NOT EXISTS idx_teams_european_names 
    ON footballdecoded.teams_european(normalized_name, team_name);

-- Position and age filtering indexes
CREATE INDEX IF NOT EXISTS idx_players_domestic_position_age 
    ON footballdecoded.players_domestic(position, age) 
    WHERE position IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_players_european_position_age 
    ON footballdecoded.players_european(position, age) 
    WHERE position IS NOT NULL;

-- Nationality filtering indexes
CREATE INDEX IF NOT EXISTS idx_players_domestic_nationality 
    ON footballdecoded.players_domestic(nationality) 
    WHERE nationality IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_players_european_nationality 
    ON footballdecoded.players_european(nationality) 
    WHERE nationality IS NOT NULL;

-- Data quality monitoring indexes
CREATE INDEX IF NOT EXISTS idx_players_domestic_quality 
    ON footballdecoded.players_domestic(data_quality_score, processing_warnings) 
    WHERE data_quality_score < 1.0;

CREATE INDEX IF NOT EXISTS idx_players_european_quality 
    ON footballdecoded.players_european(data_quality_score, processing_warnings) 
    WHERE data_quality_score < 1.0;

CREATE INDEX IF NOT EXISTS idx_teams_domestic_quality 
    ON footballdecoded.teams_domestic(data_quality_score, processing_warnings) 
    WHERE data_quality_score < 1.0;

CREATE INDEX IF NOT EXISTS idx_teams_european_quality 
    ON footballdecoded.teams_european(data_quality_score, processing_warnings) 
    WHERE data_quality_score < 1.0;

-- Transfer analysis indexes
CREATE INDEX IF NOT EXISTS idx_players_domestic_transfers 
    ON footballdecoded.players_domestic(is_transfer, transfer_count, teams_played) 
    WHERE is_transfer = TRUE;

CREATE INDEX IF NOT EXISTS idx_players_european_transfers 
    ON footballdecoded.players_european(is_transfer, transfer_count, teams_played) 
    WHERE is_transfer = TRUE;

-- Timestamp indexes for data management
CREATE INDEX IF NOT EXISTS idx_players_domestic_timestamps 
    ON footballdecoded.players_domestic(created_at, updated_at, processed_at);

CREATE INDEX IF NOT EXISTS idx_players_european_timestamps 
    ON footballdecoded.players_european(created_at, updated_at, processed_at);

CREATE INDEX IF NOT EXISTS idx_teams_domestic_timestamps 
    ON footballdecoded.teams_domestic(created_at, updated_at, processed_at);

CREATE INDEX IF NOT EXISTS idx_teams_european_timestamps 
    ON footballdecoded.teams_european(created_at, updated_at, processed_at);

-- JSONB indexes for metrics queries
CREATE INDEX IF NOT EXISTS idx_players_domestic_fbref_metrics 
    ON footballdecoded.players_domestic USING GIN (fbref_metrics) 
    WHERE fbref_metrics IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_players_domestic_understat_metrics 
    ON footballdecoded.players_domestic USING GIN (understat_metrics) 
    WHERE understat_metrics IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_players_european_fbref_metrics 
    ON footballdecoded.players_european USING GIN (fbref_metrics) 
    WHERE fbref_metrics IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_teams_domestic_fbref_metrics 
    ON footballdecoded.teams_domestic USING GIN (fbref_metrics) 
    WHERE fbref_metrics IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_teams_domestic_understat_metrics 
    ON footballdecoded.teams_domestic USING GIN (understat_metrics) 
    WHERE understat_metrics IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_teams_european_fbref_metrics 
    ON footballdecoded.teams_european USING GIN (fbref_metrics) 
    WHERE fbref_metrics IS NOT NULL;

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

-- ====================================================================
-- CONSTRAINTS VALIDATION - Compatible with all PostgreSQL versions
-- ====================================================================

-- Drop existing constraints if they exist (to handle re-runs)
DO $$ 
BEGIN
    -- Drop constraints if they exist
    BEGIN
        ALTER TABLE footballdecoded.players_domestic DROP CONSTRAINT IF EXISTS chk_players_domestic_uid_format;
        ALTER TABLE footballdecoded.players_european DROP CONSTRAINT IF EXISTS chk_players_european_uid_format;
        ALTER TABLE footballdecoded.teams_domestic DROP CONSTRAINT IF EXISTS chk_teams_domestic_uid_format;
        ALTER TABLE footballdecoded.teams_european DROP CONSTRAINT IF EXISTS chk_teams_european_uid_format;
    EXCEPTION
        WHEN undefined_object THEN null;
    END;
END $$;

-- Add constraints with simplified syntax
ALTER TABLE footballdecoded.players_domestic 
    ADD CONSTRAINT chk_players_domestic_uid_format 
    CHECK (unique_player_id IS NULL OR length(unique_player_id) = 16);

ALTER TABLE footballdecoded.players_european 
    ADD CONSTRAINT chk_players_european_uid_format 
    CHECK (unique_player_id IS NULL OR length(unique_player_id) = 16);

ALTER TABLE footballdecoded.teams_domestic 
    ADD CONSTRAINT chk_teams_domestic_uid_format 
    CHECK (unique_team_id IS NULL OR length(unique_team_id) = 16);

ALTER TABLE footballdecoded.teams_european 
    ADD CONSTRAINT chk_teams_european_uid_format 
    CHECK (unique_team_id IS NULL OR length(unique_team_id) = 16);