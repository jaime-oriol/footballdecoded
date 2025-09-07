-- ====================================================================
-- FootballDecoded Database Schema - EXTRAS Tables (Portuguese Liga, etc)
-- ====================================================================
-- IMPORTANTE: Este script SOLO crea tablas nuevas, NO modifica las existentes
-- Preserva todos los datos en players_domestic, teams_domestic, players_european, teams_european

-- ====================================================================
-- NUEVAS TABLAS EXTRAS - Para ligas adicionales (Portugal, Holanda, etc)
-- ====================================================================

CREATE TABLE IF NOT EXISTS footballdecoded.players_extras (
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

CREATE TABLE IF NOT EXISTS footballdecoded.teams_extras (
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

-- ====================================================================
-- INDICES PARA TABLAS EXTRAS
-- ====================================================================

-- Unique indexes for data integrity
CREATE UNIQUE INDEX IF NOT EXISTS idx_players_extras_unique 
    ON footballdecoded.players_extras(unique_player_id, league, season, team)
    WHERE unique_player_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_teams_extras_unique 
    ON footballdecoded.teams_extras(unique_team_id, league, season)
    WHERE unique_team_id IS NOT NULL;

-- Query performance indexes
CREATE INDEX IF NOT EXISTS idx_players_extras_league_season 
    ON footballdecoded.players_extras(league, season);

CREATE INDEX IF NOT EXISTS idx_teams_extras_league_season 
    ON footballdecoded.teams_extras(league, season);

-- Player name search indexes
CREATE INDEX IF NOT EXISTS idx_players_extras_names 
    ON footballdecoded.players_extras(normalized_name, player_name);

-- Team name search indexes
CREATE INDEX IF NOT EXISTS idx_teams_extras_names 
    ON footballdecoded.teams_extras(normalized_name, team_name);

-- Position and age filtering indexes
CREATE INDEX IF NOT EXISTS idx_players_extras_position_age 
    ON footballdecoded.players_extras(position, age) 
    WHERE position IS NOT NULL;

-- Nationality filtering indexes
CREATE INDEX IF NOT EXISTS idx_players_extras_nationality 
    ON footballdecoded.players_extras(nationality) 
    WHERE nationality IS NOT NULL;

-- Data quality monitoring indexes
CREATE INDEX IF NOT EXISTS idx_players_extras_quality 
    ON footballdecoded.players_extras(data_quality_score, processing_warnings) 
    WHERE data_quality_score < 1.0;

CREATE INDEX IF NOT EXISTS idx_teams_extras_quality 
    ON footballdecoded.teams_extras(data_quality_score, processing_warnings) 
    WHERE data_quality_score < 1.0;

-- Transfer analysis indexes
CREATE INDEX IF NOT EXISTS idx_players_extras_transfers 
    ON footballdecoded.players_extras(is_transfer, transfer_count, teams_played) 
    WHERE is_transfer = TRUE;

-- Timestamp indexes for data management
CREATE INDEX IF NOT EXISTS idx_players_extras_timestamps 
    ON footballdecoded.players_extras(created_at, updated_at, processed_at);

CREATE INDEX IF NOT EXISTS idx_teams_extras_timestamps 
    ON footballdecoded.teams_extras(created_at, updated_at, processed_at);

-- JSONB indexes for metrics queries
CREATE INDEX IF NOT EXISTS idx_players_extras_fbref_metrics 
    ON footballdecoded.players_extras USING GIN (fbref_metrics) 
    WHERE fbref_metrics IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_players_extras_understat_metrics 
    ON footballdecoded.players_extras USING GIN (understat_metrics) 
    WHERE understat_metrics IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_teams_extras_fbref_metrics 
    ON footballdecoded.teams_extras USING GIN (fbref_metrics) 
    WHERE fbref_metrics IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_teams_extras_understat_metrics 
    ON footballdecoded.teams_extras USING GIN (understat_metrics) 
    WHERE understat_metrics IS NOT NULL;

-- ====================================================================
-- TRIGGERS PARA TABLAS EXTRAS
-- ====================================================================

DROP TRIGGER IF EXISTS update_players_extras_timestamp ON footballdecoded.players_extras;
CREATE TRIGGER update_players_extras_timestamp 
    BEFORE UPDATE ON footballdecoded.players_extras 
    FOR EACH ROW EXECUTE FUNCTION footballdecoded.update_timestamp();

DROP TRIGGER IF EXISTS update_teams_extras_timestamp ON footballdecoded.teams_extras;
CREATE TRIGGER update_teams_extras_timestamp 
    BEFORE UPDATE ON footballdecoded.teams_extras 
    FOR EACH ROW EXECUTE FUNCTION footballdecoded.update_timestamp();

-- ====================================================================
-- CONSTRAINTS PARA TABLAS EXTRAS
-- ====================================================================

ALTER TABLE footballdecoded.players_extras 
    ADD CONSTRAINT chk_players_extras_uid_format 
    CHECK (unique_player_id IS NULL OR length(unique_player_id) = 16);

ALTER TABLE footballdecoded.teams_extras 
    ADD CONSTRAINT chk_teams_extras_uid_format 
    CHECK (unique_team_id IS NULL OR length(unique_team_id) = 16);