-- ====================================================================
-- FootballDecoded Database Schema - Enhanced but Simple
-- Fixes key issues while maintaining simplicity
-- ====================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- ====================================================================
-- SCHEMA CREATION
-- ====================================================================

CREATE SCHEMA IF NOT EXISTS footballdecoded;

-- ====================================================================
-- TABLE 1: PLAYERS DOMESTIC (FBref + Understat) - ENHANCED
-- ====================================================================

CREATE TABLE IF NOT EXISTS footballdecoded.players_domestic (
    id SERIAL PRIMARY KEY,
    
    -- Basic identification - enhanced for better duplicate detection
    player_name VARCHAR(200) NOT NULL,
    normalized_name VARCHAR(200) NOT NULL,  -- NEW: For consistent matching
    league VARCHAR(50) NOT NULL,
    season VARCHAR(10) NOT NULL,
    team VARCHAR(150) NOT NULL,
    teams_played TEXT,                       -- NEW: Track transfers "Team A -> Team B"
    
    -- Player attributes - enhanced validation
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
    
    -- Data quality and processing - NEW
    data_quality_score DECIMAL(3,2) DEFAULT 1.00 CHECK (data_quality_score >= 0.0 AND data_quality_score <= 1.0),
    processing_warnings TEXT[],              -- Array of validation warnings
    is_transfer BOOLEAN DEFAULT FALSE,       -- Indicates consolidated transfer data
    transfer_count INTEGER DEFAULT 0,       -- Number of teams played
    
    -- Metadata - enhanced
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP DEFAULT NOW()
);

-- ====================================================================
-- TABLE 2: PLAYERS EUROPEAN (FBref only) - ENHANCED
-- ====================================================================

CREATE TABLE IF NOT EXISTS footballdecoded.players_european (
    id SERIAL PRIMARY KEY,
    
    -- Basic identification
    player_name VARCHAR(200) NOT NULL,
    normalized_name VARCHAR(200) NOT NULL,
    competition VARCHAR(50) NOT NULL,        -- Champions League, etc.
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
-- TABLE 3: TEAMS DOMESTIC (FBref + Understat) - ENHANCED
-- ====================================================================

CREATE TABLE IF NOT EXISTS footballdecoded.teams_domestic (
    id SERIAL PRIMARY KEY,
    
    -- Basic identification
    team_name VARCHAR(200) NOT NULL,
    normalized_name VARCHAR(200) NOT NULL,  -- NEW: For consistent matching
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
-- TABLE 4: TEAMS EUROPEAN (FBref only) - ENHANCED
-- ====================================================================

CREATE TABLE IF NOT EXISTS footballdecoded.teams_european (
    id SERIAL PRIMARY KEY,
    
    -- Basic identification
    team_name VARCHAR(200) NOT NULL,
    normalized_name VARCHAR(200) NOT NULL,
    competition VARCHAR(50) NOT NULL,        -- Champions League, etc.
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
-- SMART CONSTRAINTS - Prevents duplicates but allows transfers
-- ====================================================================

-- For players - unique combination that allows transfers
CREATE UNIQUE INDEX idx_players_domestic_unique 
    ON footballdecoded.players_domestic(normalized_name, age, nationality, league, season, team);

CREATE UNIQUE INDEX idx_players_european_unique 
    ON footballdecoded.players_european(normalized_name, age, nationality, competition, season, team);

-- For teams - simple unique constraint
CREATE UNIQUE INDEX idx_teams_domestic_unique 
    ON footballdecoded.teams_domestic(normalized_name, league, season);

CREATE UNIQUE INDEX idx_teams_european_unique 
    ON footballdecoded.teams_european(normalized_name, competition, season);

-- ====================================================================
-- PERFORMANCE INDEXES
-- ====================================================================

-- Basic query indexes (league/competition + season)
CREATE INDEX idx_players_domestic_league_season 
    ON footballdecoded.players_domestic(league, season);

CREATE INDEX idx_players_european_competition_season 
    ON footballdecoded.players_european(competition, season);

CREATE INDEX idx_teams_domestic_league_season 
    ON footballdecoded.teams_domestic(league, season);

CREATE INDEX idx_teams_european_competition_season 
    ON footballdecoded.teams_european(competition, season);

-- Normalized name indexes for fast duplicate detection
CREATE INDEX idx_players_domestic_normalized_name 
    ON footballdecoded.players_domestic(normalized_name);

CREATE INDEX idx_players_european_normalized_name 
    ON footballdecoded.players_european(normalized_name);

CREATE INDEX idx_teams_domestic_normalized_name 
    ON footballdecoded.teams_domestic(normalized_name);

CREATE INDEX idx_teams_european_normalized_name 
    ON footballdecoded.teams_european(normalized_name);

-- Team-based indexes for player searches
CREATE INDEX idx_players_domestic_team 
    ON footballdecoded.players_domestic(team);

CREATE INDEX idx_players_european_team 
    ON footballdecoded.players_european(team);

-- Data quality indexes
CREATE INDEX idx_players_domestic_quality_score 
    ON footballdecoded.players_domestic(data_quality_score);

CREATE INDEX idx_players_european_quality_score 
    ON footballdecoded.players_european(data_quality_score);

-- Transfer detection indexes
CREATE INDEX idx_players_domestic_transfers 
    ON footballdecoded.players_domestic(normalized_name, league, season) 
    WHERE is_transfer = true;

CREATE INDEX idx_players_european_transfers 
    ON footballdecoded.players_european(normalized_name, competition, season) 
    WHERE is_transfer = true;

-- JSON search indexes (GIN for fast JSON queries)
CREATE INDEX idx_players_domestic_fbref_gin 
    ON footballdecoded.players_domestic USING gin(fbref_metrics);

CREATE INDEX idx_players_domestic_understat_gin 
    ON footballdecoded.players_domestic USING gin(understat_metrics);

CREATE INDEX idx_teams_domestic_fbref_gin 
    ON footballdecoded.teams_domestic USING gin(fbref_metrics);

CREATE INDEX idx_teams_domestic_understat_gin 
    ON footballdecoded.teams_domestic USING gin(understat_metrics);

-- ====================================================================
-- TRIGGERS FOR AUTOMATIC MAINTENANCE
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
CREATE TRIGGER update_players_domestic_updated_at 
    BEFORE UPDATE ON footballdecoded.players_domestic 
    FOR EACH ROW EXECUTE FUNCTION footballdecoded.update_updated_at_column();

CREATE TRIGGER update_players_european_updated_at 
    BEFORE UPDATE ON footballdecoded.players_european 
    FOR EACH ROW EXECUTE FUNCTION footballdecoded.update_updated_at_column();

CREATE TRIGGER update_teams_domestic_updated_at 
    BEFORE UPDATE ON footballdecoded.teams_domestic 
    FOR EACH ROW EXECUTE FUNCTION footballdecoded.update_updated_at_column();

CREATE TRIGGER update_teams_european_updated_at 
    ON footballdecoded.teams_european 
    FOR EACH ROW EXECUTE FUNCTION footballdecoded.update_updated_at_column();

-- ====================================================================
-- USEFUL VIEWS FOR MONITORING
-- ====================================================================

-- View for data quality monitoring
CREATE OR REPLACE VIEW footballdecoded.data_quality_summary AS
SELECT 
    'players_domestic' as table_name,
    COUNT(*) as total_records,
    ROUND(AVG(data_quality_score), 3) as avg_quality_score,
    COUNT(CASE WHEN data_quality_score < 0.7 THEN 1 END) as low_quality_records,
    COUNT(CASE WHEN is_transfer THEN 1 END) as transfer_records,
    COUNT(CASE WHEN array_length(processing_warnings, 1) > 0 THEN 1 END) as records_with_warnings
FROM footballdecoded.players_domestic
UNION ALL
SELECT 
    'players_european',
    COUNT(*),
    ROUND(AVG(data_quality_score), 3),
    COUNT(CASE WHEN data_quality_score < 0.7 THEN 1 END),
    COUNT(CASE WHEN is_transfer THEN 1 END),
    COUNT(CASE WHEN array_length(processing_warnings, 1) > 0 THEN 1 END)
FROM footballdecoded.players_european
UNION ALL
SELECT 
    'teams_domestic',
    COUNT(*),
    ROUND(AVG(data_quality_score), 3),
    COUNT(CASE WHEN data_quality_score < 0.7 THEN 1 END),
    0 as transfer_records,
    COUNT(CASE WHEN array_length(processing_warnings, 1) > 0 THEN 1 END)
FROM footballdecoded.teams_domestic
UNION ALL
SELECT 
    'teams_european',
    COUNT(*),
    ROUND(AVG(data_quality_score), 3),
    COUNT(CASE WHEN data_quality_score < 0.7 THEN 1 END),
    0 as transfer_records,
    COUNT(CASE WHEN array_length(processing_warnings, 1) > 0 THEN 1 END)
FROM footballdecoded.teams_european;

-- View for transfer analysis
CREATE OR REPLACE VIEW footballdecoded.transfer_summary AS
SELECT 
    player_name,
    normalized_name,
    league,
    season,
    teams_played,
    transfer_count,
    data_quality_score,
    processed_at
FROM footballdecoded.players_domestic 
WHERE is_transfer = true
UNION ALL
SELECT 
    player_name,
    normalized_name,
    competition as league,
    season,
    teams_played,
    transfer_count,
    data_quality_score,
    processed_at
FROM footballdecoded.players_european 
WHERE is_transfer = true
ORDER BY transfer_count DESC, processed_at DESC;

-- View for low quality records that need review
CREATE OR REPLACE VIEW footballdecoded.quality_review_queue AS
SELECT 
    'player_domestic' as table_type,
    id,
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
    id,
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
    id,
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
    id,
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
-- VERIFICATION AND CLEANUP
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