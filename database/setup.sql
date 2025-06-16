-- ====================================================================
-- FootballDecoded Database Schema - Sistema de IDs Únicos
-- ====================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- ====================================================================
-- SCHEMA CREATION
-- ====================================================================

CREATE SCHEMA IF NOT EXISTS footballdecoded;

-- ====================================================================
-- TABLE 1: PLAYERS DOMESTIC (FBref + Understat) - CON IDS ÚNICOS
-- ====================================================================

CREATE TABLE IF NOT EXISTS footballdecoded.players_domestic (
    id SERIAL PRIMARY KEY,
    
    -- Sistema de IDs únicos
    unique_player_id VARCHAR(16) NOT NULL,   -- Hash SHA256 (16 chars)
    
    -- Basic identification
    player_name VARCHAR(200) NOT NULL,
    normalized_name VARCHAR(200) NOT NULL,
    league VARCHAR(50) NOT NULL,
    season VARCHAR(10) NOT NULL,
    team VARCHAR(150) NOT NULL,
    teams_played TEXT,
    
    -- Player attributes
    nationality VARCHAR(3),
    position VARCHAR(10),
    age INTEGER CONSTRAINT valid_age CHECK (age >= 15 AND age <= 50),
    birth_year INTEGER CONSTRAINT valid_birth_year CHECK (birth_year >= 1970 AND birth_year <= 2010),
    
    -- Metrics storage (JSON for flexibility)
    fbref_metrics JSONB,
    understat_metrics JSONB,
    
    -- Official names for reconciliation
    fbref_official_name VARCHAR(200),
    understat_official_name VARCHAR(200),
    
    -- Data quality and processing
    data_quality_score DECIMAL(3,2) DEFAULT 1.00 CHECK (data_quality_score >= 0.0 AND data_quality_score <= 1.0),
    processing_warnings TEXT[],
    is_transfer BOOLEAN DEFAULT FALSE,
    transfer_count INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP DEFAULT NOW()
);

-- ====================================================================
-- TABLE 2: PLAYERS EUROPEAN (FBref only) - CON IDS ÚNICOS
-- ====================================================================

CREATE TABLE IF NOT EXISTS footballdecoded.players_european (
    id SERIAL PRIMARY KEY,
    
    -- Sistema de IDs únicos
    unique_player_id VARCHAR(16) NOT NULL,   -- Hash SHA256 (16 chars)
    
    -- Basic identification
    player_name VARCHAR(200) NOT NULL,
    normalized_name VARCHAR(200) NOT NULL,
    competition VARCHAR(50) NOT NULL,
    season VARCHAR(10) NOT NULL,
    team VARCHAR(150) NOT NULL,
    teams_played TEXT,
    
    -- Player attributes
    nationality VARCHAR(3),
    position VARCHAR(10),
    age INTEGER CONSTRAINT valid_age_eu CHECK (age >= 15 AND age <= 50),
    birth_year INTEGER CONSTRAINT valid_birth_year_eu CHECK (birth_year >= 1970 AND birth_year <= 2010),
    
    -- Metrics storage (FBref only for European competitions)
    fbref_metrics JSONB,
    fbref_official_name VARCHAR(200),
    
    -- Data quality and processing
    data_quality_score DECIMAL(3,2) DEFAULT 1.00 CHECK (data_quality_score >= 0.0 AND data_quality_score <= 1.0),
    processing_warnings TEXT[],
    is_transfer BOOLEAN DEFAULT FALSE,
    transfer_count INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP DEFAULT NOW()
);

-- ====================================================================
-- TABLE 3: TEAMS DOMESTIC (FBref + Understat) - CON IDS ÚNICOS
-- ====================================================================

CREATE TABLE IF NOT EXISTS footballdecoded.teams_domestic (
    id SERIAL PRIMARY KEY,
    
    -- Sistema de IDs únicos
    unique_team_id VARCHAR(16) NOT NULL,     -- Hash SHA256 (16 chars)
    
    -- Basic identification
    team_name VARCHAR(200) NOT NULL,
    normalized_name VARCHAR(200) NOT NULL,
    league VARCHAR(50) NOT NULL,
    season VARCHAR(10) NOT NULL,
    
    -- Metrics storage
    fbref_metrics JSONB,
    understat_metrics JSONB,
    
    -- Official names for reconciliation
    fbref_official_name VARCHAR(200),
    understat_official_name VARCHAR(200),
    
    -- Data quality and processing
    data_quality_score DECIMAL(3,2) DEFAULT 1.00 CHECK (data_quality_score >= 0.0 AND data_quality_score <= 1.0),
    processing_warnings TEXT[],
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP DEFAULT NOW()
);

-- ====================================================================
-- TABLE 4: TEAMS EUROPEAN (FBref only) - CON IDS ÚNICOS
-- ====================================================================

CREATE TABLE IF NOT EXISTS footballdecoded.teams_european (
    id SERIAL PRIMARY KEY,
    
    -- Sistema de IDs únicos
    unique_team_id VARCHAR(16) NOT NULL,     -- Hash SHA256 (16 chars)
    
    -- Basic identification
    team_name VARCHAR(200) NOT NULL,
    normalized_name VARCHAR(200) NOT NULL,
    competition VARCHAR(50) NOT NULL,
    season VARCHAR(10) NOT NULL,
    
    -- Metrics storage (FBref only)
    fbref_metrics JSONB,
    fbref_official_name VARCHAR(200),
    
    -- Data quality and processing
    data_quality_score DECIMAL(3,2) DEFAULT 1.00 CHECK (data_quality_score >= 0.0 AND data_quality_score <= 1.0),
    processing_warnings TEXT[],
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP DEFAULT NOW()
);

-- ====================================================================
-- CONSTRAINTS NUEVOS - BASADOS EN IDS ÚNICOS
-- ====================================================================

-- Players: unique_player_id + league + season + team (permite transfers)
CREATE UNIQUE INDEX IF NOT EXISTS idx_players_domestic_unique_id 
    ON footballdecoded.players_domestic(unique_player_id, league, season, team);

CREATE UNIQUE INDEX IF NOT EXISTS idx_players_european_unique_id 
    ON footballdecoded.players_european(unique_player_id, competition, season, team);

-- Teams: unique_team_id + league + season
CREATE UNIQUE INDEX IF NOT EXISTS idx_teams_domestic_unique_id 
    ON footballdecoded.teams_domestic(unique_team_id, league, season);

CREATE UNIQUE INDEX IF NOT EXISTS idx_teams_european_unique_id 
    ON footballdecoded.teams_european(unique_team_id, competition, season);

-- ====================================================================
-- PERFORMANCE INDEXES - OPTIMIZADOS PARA IDS ÚNICOS
-- ====================================================================

-- IDs únicos para rendimiento máximo
CREATE INDEX IF NOT EXISTS idx_players_domestic_unique_id_only 
    ON footballdecoded.players_domestic(unique_player_id);

CREATE INDEX IF NOT EXISTS idx_players_european_unique_id_only 
    ON footballdecoded.players_european(unique_player_id);

CREATE INDEX IF NOT EXISTS idx_teams_domestic_unique_id_only 
    ON footballdecoded.teams_domestic(unique_team_id);

CREATE INDEX IF NOT EXISTS idx_teams_european_unique_id_only 
    ON footballdecoded.teams_european(unique_team_id);

-- Query indexes (league/competition + season)
CREATE INDEX IF NOT EXISTS idx_players_domestic_league_season 
    ON footballdecoded.players_domestic(league, season);

CREATE INDEX IF NOT EXISTS idx_players_european_competition_season 
    ON footballdecoded.players_european(competition, season);

CREATE INDEX IF NOT EXISTS idx_teams_domestic_league_season 
    ON footballdecoded.teams_domestic(league, season);

CREATE INDEX IF NOT EXISTS idx_teams_european_competition_season 
    ON footballdecoded.teams_european(competition, season);

-- Normalized name indexes for legacy support
CREATE INDEX IF NOT EXISTS idx_players_domestic_normalized_name 
    ON footballdecoded.players_domestic(normalized_name);

CREATE INDEX IF NOT EXISTS idx_players_european_normalized_name 
    ON footballdecoded.players_european(normalized_name);

CREATE INDEX IF NOT EXISTS idx_teams_domestic_normalized_name 
    ON footballdecoded.teams_domestic(normalized_name);

CREATE INDEX IF NOT EXISTS idx_teams_european_normalized_name 
    ON footballdecoded.teams_european(normalized_name);

-- Team-based indexes for player searches
CREATE INDEX IF NOT EXISTS idx_players_domestic_team 
    ON footballdecoded.players_domestic(team);

CREATE INDEX IF NOT EXISTS idx_players_european_team 
    ON footballdecoded.players_european(team);

-- Data quality indexes
CREATE INDEX IF NOT EXISTS idx_players_domestic_quality_score 
    ON footballdecoded.players_domestic(data_quality_score);

CREATE INDEX IF NOT EXISTS idx_players_european_quality_score 
    ON footballdecoded.players_european(data_quality_score);

-- Transfer detection con IDs únicos
CREATE INDEX IF NOT EXISTS idx_players_domestic_transfers 
    ON footballdecoded.players_domestic(unique_player_id, league, season) 
    WHERE is_transfer = true;

CREATE INDEX IF NOT EXISTS idx_players_european_transfers 
    ON footballdecoded.players_european(unique_player_id, competition, season) 
    WHERE is_transfer = true;

-- JSON search indexes (GIN for fast JSON queries)
CREATE INDEX IF NOT EXISTS idx_players_domestic_fbref_gin 
    ON footballdecoded.players_domestic USING gin(fbref_metrics);

CREATE INDEX IF NOT EXISTS idx_players_domestic_understat_gin 
    ON footballdecoded.players_domestic USING gin(understat_metrics);

CREATE INDEX IF NOT EXISTS idx_teams_domestic_fbref_gin 
    ON footballdecoded.teams_domestic USING gin(fbref_metrics);

CREATE INDEX IF NOT EXISTS idx_teams_domestic_understat_gin 
    ON footballdecoded.teams_domestic USING gin(understat_metrics);

-- ====================================================================
-- TRIGGERS FOR AUTOMATIC MAINTENANCE - CORREGIDO
-- ====================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION footballdecoded.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic timestamp updates
DROP TRIGGER IF EXISTS update_players_domestic_updated_at ON footballdecoded.players_domestic;
CREATE TRIGGER update_players_domestic_updated_at 
    BEFORE UPDATE ON footballdecoded.players_domestic 
    FOR EACH ROW EXECUTE FUNCTION footballdecoded.update_updated_at_column();

DROP TRIGGER IF EXISTS update_players_european_updated_at ON footballdecoded.players_european;
CREATE TRIGGER update_players_european_updated_at 
    BEFORE UPDATE ON footballdecoded.players_european 
    FOR EACH ROW EXECUTE FUNCTION footballdecoded.update_updated_at_column();

DROP TRIGGER IF EXISTS update_teams_domestic_updated_at ON footballdecoded.teams_domestic;
CREATE TRIGGER update_teams_domestic_updated_at 
    BEFORE UPDATE ON footballdecoded.teams_domestic 
    FOR EACH ROW EXECUTE FUNCTION footballdecoded.update_updated_at_column();

-- TRIGGER CORREGIDO - ERA "ON" EN LUGAR DE "BEFORE UPDATE ON"
DROP TRIGGER IF EXISTS update_teams_european_updated_at ON footballdecoded.teams_european;
CREATE TRIGGER update_teams_european_updated_at 
    BEFORE UPDATE ON footballdecoded.teams_european 
    FOR EACH ROW EXECUTE FUNCTION footballdecoded.update_updated_at_column();

-- ====================================================================
-- VIEWS ACTUALIZADAS CON IDS ÚNICOS
-- ====================================================================

-- View for data quality monitoring
CREATE OR REPLACE VIEW footballdecoded.data_quality_summary AS
SELECT 
    'players_domestic' as table_name,
    COUNT(*) as total_records,
    COUNT(DISTINCT unique_player_id) as unique_entities,
    ROUND(AVG(data_quality_score), 3) as avg_quality_score,
    COUNT(CASE WHEN data_quality_score < 0.7 THEN 1 END) as low_quality_records,
    COUNT(CASE WHEN is_transfer THEN 1 END) as transfer_records,
    COUNT(CASE WHEN array_length(processing_warnings, 1) > 0 THEN 1 END) as records_with_warnings
FROM footballdecoded.players_domestic
UNION ALL
SELECT 
    'players_european',
    COUNT(*),
    COUNT(DISTINCT unique_player_id),
    ROUND(AVG(data_quality_score), 3),
    COUNT(CASE WHEN data_quality_score < 0.7 THEN 1 END),
    COUNT(CASE WHEN is_transfer THEN 1 END),
    COUNT(CASE WHEN array_length(processing_warnings, 1) > 0 THEN 1 END)
FROM footballdecoded.players_european
UNION ALL
SELECT 
    'teams_domestic',
    COUNT(*),
    COUNT(DISTINCT unique_team_id),
    ROUND(AVG(data_quality_score), 3),
    COUNT(CASE WHEN data_quality_score < 0.7 THEN 1 END),
    0 as transfer_records,
    COUNT(CASE WHEN array_length(processing_warnings, 1) > 0 THEN 1 END)
FROM footballdecoded.teams_domestic
UNION ALL
SELECT 
    'teams_european',
    COUNT(*),
    COUNT(DISTINCT unique_team_id),
    ROUND(AVG(data_quality_score), 3),
    COUNT(CASE WHEN data_quality_score < 0.7 THEN 1 END),
    0 as transfer_records,
    COUNT(CASE WHEN array_length(processing_warnings, 1) > 0 THEN 1 END)
FROM footballdecoded.teams_european;

-- View for transfer analysis con IDs únicos
CREATE OR REPLACE VIEW footballdecoded.transfer_summary AS
SELECT 
    unique_player_id,
    player_name,
    normalized_name,
    league,
    season,
    COUNT(*) as teams_in_season,
    STRING_AGG(team, ' -> ' ORDER BY team) as teams_played,
    MAX(transfer_count) as transfer_count,
    AVG(data_quality_score) as avg_quality_score,
    MAX(processed_at) as last_processed
FROM footballdecoded.players_domestic 
GROUP BY unique_player_id, player_name, normalized_name, league, season
HAVING COUNT(*) > 1
UNION ALL
SELECT 
    unique_player_id,
    player_name,
    normalized_name,
    competition as league,
    season,
    COUNT(*) as teams_in_season,
    STRING_AGG(team, ' -> ' ORDER BY team) as teams_played,
    MAX(transfer_count) as transfer_count,
    AVG(data_quality_score) as avg_quality_score,
    MAX(processed_at) as last_processed
FROM footballdecoded.players_european 
GROUP BY unique_player_id, player_name, normalized_name, competition, season
HAVING COUNT(*) > 1
ORDER BY teams_in_season DESC, last_processed DESC;

-- View for players with multiple teams (transfers detectados automáticamente)
CREATE OR REPLACE VIEW footballdecoded.multi_team_players AS
SELECT 
    unique_player_id,
    player_name,
    league,
    season,
    COUNT(DISTINCT team) as teams_count,
    STRING_AGG(DISTINCT team, ', ' ORDER BY team) as all_teams,
    AVG(data_quality_score) as avg_quality
FROM footballdecoded.players_domestic
GROUP BY unique_player_id, player_name, league, season
HAVING COUNT(DISTINCT team) > 1
UNION ALL
SELECT 
    unique_player_id,
    player_name,
    competition as league,
    season,
    COUNT(DISTINCT team) as teams_count,
    STRING_AGG(DISTINCT team, ', ' ORDER BY team) as all_teams,
    AVG(data_quality_score) as avg_quality
FROM footballdecoded.players_european
GROUP BY unique_player_id, player_name, competition, season
HAVING COUNT(DISTINCT team) > 1
ORDER BY teams_count DESC;

-- View for low quality records that need review
CREATE OR REPLACE VIEW footballdecoded.quality_review_queue AS
SELECT 
    'player_domestic' as table_type,
    unique_player_id as entity_id,
    player_name as entity_name,
    league,
    season,
    team,
    data_quality_score,
    processing_warnings,
    processed_at
FROM footballdecoded.players_domestic 
WHERE data_quality_score < 0.7
UNION ALL
SELECT 
    'player_european',
    unique_player_id,
    player_name,
    competition as league,
    season,
    team,
    data_quality_score,
    processing_warnings,
    processed_at
FROM footballdecoded.players_european 
WHERE data_quality_score < 0.7
UNION ALL
SELECT 
    'team_domestic',
    unique_team_id,
    team_name,
    league,
    season,
    '' as team,
    data_quality_score,
    processing_warnings,
    processed_at
FROM footballdecoded.teams_domestic 
WHERE data_quality_score < 0.7
UNION ALL
SELECT 
    'team_european',
    unique_team_id,
    team_name,
    competition as league,
    season,
    '' as team,
    data_quality_score,
    processing_warnings,
    processed_at
FROM footballdecoded.teams_european 
WHERE data_quality_score < 0.7
ORDER BY data_quality_score ASC, processed_at DESC;

-- ====================================================================
-- VERIFICACIÓN FINAL
-- ====================================================================

-- List all tables to verify creation
SELECT 
    schemaname,
    tablename,
    tableowner,
    hasindexes,
    hasrules,
    hastriggers
FROM pg_tables 
WHERE schemaname = 'footballdecoded'
ORDER BY tablename;

-- Verify constraints
SELECT 
    tc.constraint_name,
    tc.table_name,
    tc.constraint_type,
    cc.check_clause
FROM information_schema.table_constraints tc
LEFT JOIN information_schema.check_constraints cc 
    ON tc.constraint_name = cc.constraint_name
WHERE tc.table_schema = 'footballdecoded'
ORDER BY tc.table_name, tc.constraint_type;