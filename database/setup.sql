-- ====================================================================
-- FootballDecoded Database Schema
-- Complete setup with tables, indexes and constraints
-- ====================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- ====================================================================
-- SCHEMA CREATION
-- ====================================================================

CREATE SCHEMA IF NOT EXISTS footballdecoded;

-- ====================================================================
-- TABLE 1: PLAYERS DOMESTIC (FBref + Understat)
-- ====================================================================

CREATE TABLE IF NOT EXISTS footballdecoded.players_domestic (
    id SERIAL PRIMARY KEY,
    
    -- Basic identification
    player_name VARCHAR(100) NOT NULL,
    league VARCHAR(50) NOT NULL,
    season VARCHAR(10) NOT NULL,
    team VARCHAR(100) NOT NULL,
    
    -- Player attributes
    nationality VARCHAR(3),
    position VARCHAR(10),
    age INTEGER,
    birth_year INTEGER,
    
    -- Metrics storage (JSON for flexibility)
    fbref_metrics JSONB,
    understat_metrics JSONB,
    
    -- Official names for reconciliation
    fbref_official_name VARCHAR(100),
    understat_official_name VARCHAR(100),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Prevent duplicates
    UNIQUE(player_name, league, season, team)
);

-- ====================================================================
-- TABLE 2: PLAYERS EUROPEAN (FBref only)
-- ====================================================================

CREATE TABLE IF NOT EXISTS footballdecoded.players_european (
    id SERIAL PRIMARY KEY,
    
    -- Basic identification
    player_name VARCHAR(100) NOT NULL,
    competition VARCHAR(50) NOT NULL,  -- Champions League, etc.
    season VARCHAR(10) NOT NULL,
    team VARCHAR(100) NOT NULL,
    
    -- Player attributes
    nationality VARCHAR(3),
    position VARCHAR(10),
    age INTEGER,
    birth_year INTEGER,
    
    -- Metrics storage (FBref only for European competitions)
    fbref_metrics JSONB,
    fbref_official_name VARCHAR(100),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Prevent duplicates
    UNIQUE(player_name, competition, season, team)
);

-- ====================================================================
-- TABLE 3: TEAMS DOMESTIC (FBref + Understat)
-- ====================================================================

CREATE TABLE IF NOT EXISTS footballdecoded.teams_domestic (
    id SERIAL PRIMARY KEY,
    
    -- Basic identification
    team_name VARCHAR(100) NOT NULL,
    league VARCHAR(50) NOT NULL,
    season VARCHAR(10) NOT NULL,
    
    -- Metrics storage
    fbref_metrics JSONB,
    understat_metrics JSONB,
    
    -- Official names for reconciliation
    fbref_official_name VARCHAR(100),
    understat_official_name VARCHAR(100),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Prevent duplicates
    UNIQUE(team_name, league, season)
);

-- ====================================================================
-- TABLE 4: TEAMS EUROPEAN (FBref only)
-- ====================================================================

CREATE TABLE IF NOT EXISTS footballdecoded.teams_european (
    id SERIAL PRIMARY KEY,
    
    -- Basic identification
    team_name VARCHAR(100) NOT NULL,
    competition VARCHAR(50) NOT NULL,  -- Champions League, etc.
    season VARCHAR(10) NOT NULL,
    
    -- Metrics storage (FBref only)
    fbref_metrics JSONB,
    fbref_official_name VARCHAR(100),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Prevent duplicates
    UNIQUE(team_name, competition, season)
);

-- ====================================================================
-- PERFORMANCE INDEXES
-- ====================================================================

-- Basic query indexes (league/competition + season)
CREATE INDEX IF NOT EXISTS idx_players_domestic_league_season 
    ON footballdecoded.players_domestic(league, season);

CREATE INDEX IF NOT EXISTS idx_players_european_competition_season 
    ON footballdecoded.players_european(competition, season);

CREATE INDEX IF NOT EXISTS idx_teams_domestic_league_season 
    ON footballdecoded.teams_domestic(league, season);

CREATE INDEX IF NOT EXISTS idx_teams_european_competition_season 
    ON footballdecoded.teams_european(competition, season);

-- Team-based indexes for player searches
CREATE INDEX IF NOT EXISTS idx_players_domestic_team 
    ON footballdecoded.players_domestic(team);

CREATE INDEX IF NOT EXISTS idx_players_european_team 
    ON footballdecoded.players_european(team);

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
-- HELPER FUNCTIONS
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
    BEFORE UPDATE ON footballdecoded.teams_european 
    FOR EACH ROW EXECUTE FUNCTION footballdecoded.update_updated_at_column();

-- ====================================================================
-- VERIFICATION QUERIES
-- ====================================================================

-- List all tables
-- \dt footballdecoded.*

-- Check table structures
-- \d footballdecoded.players_domestic
-- \d footballdecoded.players_european  
-- \d footballdecoded.teams_domestic
-- \d footballdecoded.teams_european