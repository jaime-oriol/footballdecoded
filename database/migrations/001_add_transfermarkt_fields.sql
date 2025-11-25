-- Migration: Add Transfermarkt fields to player tables
-- Date: 2025-11-25
-- Description: Adds specific position, dominant foot, and Transfermarkt ID fields.
--              Creates audit table for market values and contract history.

-- Add columns to players_domestic
ALTER TABLE footballdecoded.players_domestic
ADD COLUMN IF NOT EXISTS position_specific VARCHAR(30),
ADD COLUMN IF NOT EXISTS primary_foot VARCHAR(10) CHECK (primary_foot IN ('Left', 'Right', 'Ambidextrous')),
ADD COLUMN IF NOT EXISTS transfermarkt_player_id VARCHAR(20);

-- Add columns to players_european
ALTER TABLE footballdecoded.players_european
ADD COLUMN IF NOT EXISTS position_specific VARCHAR(30),
ADD COLUMN IF NOT EXISTS primary_foot VARCHAR(10) CHECK (primary_foot IN ('Left', 'Right', 'Ambidextrous')),
ADD COLUMN IF NOT EXISTS transfermarkt_player_id VARCHAR(20);

-- Add columns to players_extras
ALTER TABLE footballdecoded.players_extras
ADD COLUMN IF NOT EXISTS position_specific VARCHAR(30),
ADD COLUMN IF NOT EXISTS primary_foot VARCHAR(10) CHECK (primary_foot IN ('Left', 'Right', 'Ambidextrous')),
ADD COLUMN IF NOT EXISTS transfermarkt_player_id VARCHAR(20);

-- Create audit table for market values and contract history
CREATE TABLE IF NOT EXISTS footballdecoded.player_market_history (
    id SERIAL PRIMARY KEY,
    unique_player_id VARCHAR(16) NOT NULL,
    transfermarkt_player_id VARCHAR(20),

    market_value_eur DECIMAL(12,2),
    market_value_confidence DECIMAL(3,2) DEFAULT 1.00 CHECK (market_value_confidence >= 0.0 AND market_value_confidence <= 1.0),

    contract_start_date DATE,
    contract_end_date DATE,
    contract_status VARCHAR(20) CHECK (contract_status IN ('Active', 'Expiring', 'Expired', NULL)),

    season VARCHAR(10) NOT NULL,
    recorded_at TIMESTAMP DEFAULT NOW(),
    source VARCHAR(50) DEFAULT 'Transfermarkt',

    CONSTRAINT unique_player_season UNIQUE (unique_player_id, season, source)
);

-- Indexes for players_domestic
CREATE INDEX IF NOT EXISTS idx_players_domestic_position_specific
    ON footballdecoded.players_domestic(position_specific)
    WHERE position_specific IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_players_domestic_foot
    ON footballdecoded.players_domestic(primary_foot)
    WHERE primary_foot IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_players_domestic_tm_id
    ON footballdecoded.players_domestic(transfermarkt_player_id)
    WHERE transfermarkt_player_id IS NOT NULL;

-- Indexes for players_european
CREATE INDEX IF NOT EXISTS idx_players_european_position_specific
    ON footballdecoded.players_european(position_specific)
    WHERE position_specific IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_players_european_foot
    ON footballdecoded.players_european(primary_foot)
    WHERE primary_foot IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_players_european_tm_id
    ON footballdecoded.players_european(transfermarkt_player_id)
    WHERE transfermarkt_player_id IS NOT NULL;

-- Indexes for players_extras
CREATE INDEX IF NOT EXISTS idx_players_extras_position_specific
    ON footballdecoded.players_extras(position_specific)
    WHERE position_specific IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_players_extras_foot
    ON footballdecoded.players_extras(primary_foot)
    WHERE primary_foot IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_players_extras_tm_id
    ON footballdecoded.players_extras(transfermarkt_player_id)
    WHERE transfermarkt_player_id IS NOT NULL;

-- Indexes for market history table
CREATE INDEX IF NOT EXISTS idx_market_history_player
    ON footballdecoded.player_market_history(unique_player_id);

CREATE INDEX IF NOT EXISTS idx_market_history_season
    ON footballdecoded.player_market_history(season);

CREATE INDEX IF NOT EXISTS idx_market_history_contract_end
    ON footballdecoded.player_market_history(contract_end_date)
    WHERE contract_end_date IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_market_history_tm_id
    ON footballdecoded.player_market_history(transfermarkt_player_id)
    WHERE transfermarkt_player_id IS NOT NULL;
