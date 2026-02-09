"""
Wrappers package -- high-level API for football data extraction.

Re-exports all public functions with source-prefixed names (e.g. fotmob_get_player)
to avoid collisions and make the data origin explicit at call sites.

Sources:
    fotmob_data        -- Season stats (35 player / 27 team metrics, all leagues)
    understat_data     -- Advanced xG metrics (Big 5 leagues only)
    whoscored_data     -- Spatial event data with x/y coordinates
    transfermarkt_data -- Player profiles, market values, contract details
"""

__version__ = "1.0.0"

# FotMob
from .fotmob_data import (
    extract_data as fotmob_extract_data,
    extract_multiple as fotmob_extract_multiple,
    extract_league_players as fotmob_extract_league_players,
    extract_league_teams as fotmob_extract_league_teams,
    export_to_csv as fotmob_export_to_csv,
    clear_cache as fotmob_clear_cache,
    get_player as fotmob_get_player,
    get_team as fotmob_get_team,
    get_players as fotmob_get_players,
    get_teams as fotmob_get_teams,
    get_league_players as fotmob_get_league_players,
    get_league_teams as fotmob_get_league_teams,
)

# Understat
from .understat_data import (
    extract_data as understat_extract_data,
    extract_multiple as understat_extract_multiple,
    extract_shot_events as understat_extract_shot_events,
    export_to_csv as understat_export_to_csv,
    get_match_ids as understat_get_match_ids,
    search_player_id as understat_search_player_id,
    search_team_id as understat_search_team_id,
    clear_cache as understat_clear_cache,
    get_player as understat_get_player,
    get_team as understat_get_team,
    get_players as understat_get_players,
    get_teams as understat_get_teams,
    get_shots as understat_get_shots,
    get_team_advanced as understat_get_team_advanced,
    get_player_shots as understat_get_player_shots,
)

# WhoScored
from .whoscored_data import (
    extract_match_events as whoscored_extract_match_events,
    extract_pass_network as whoscored_extract_pass_network,
    extract_player_heatmap as whoscored_extract_player_heatmap,
    extract_shot_map as whoscored_extract_shot_map,
    extract_field_occupation as whoscored_extract_field_occupation,
    extract_league_schedule as whoscored_extract_league_schedule,
    extract_missing_players as whoscored_extract_missing_players,
    get_match_ids as whoscored_get_match_ids,
    search_player_id as whoscored_search_player_id,
    search_team_id as whoscored_search_team_id,
    clear_cache as whoscored_clear_cache,
    export_to_csv as whoscored_export_to_csv,
    get_match_events as whoscored_get_match_events,
    get_match_events_viz as whoscored_get_match_events_viz,
    get_pass_network as whoscored_get_pass_network,
    get_player_heatmap as whoscored_get_player_heatmap,
    get_shot_map as whoscored_get_shot_map,
    get_field_occupation as whoscored_get_field_occupation,
    get_schedule as whoscored_get_schedule,
    get_missing_players as whoscored_get_missing_players,
)

# Transfermarkt
from .transfermarkt_data import (
    transfermarkt_get_player,
    clear_cache as transfermarkt_clear_cache,
)

__all__ = [
    # FotMob
    "fotmob_extract_data",
    "fotmob_extract_multiple",
    "fotmob_extract_league_players",
    "fotmob_extract_league_teams",
    "fotmob_export_to_csv",
    "fotmob_clear_cache",
    "fotmob_get_player",
    "fotmob_get_team",
    "fotmob_get_players",
    "fotmob_get_teams",
    "fotmob_get_league_players",
    "fotmob_get_league_teams",
    # Understat
    "understat_extract_data",
    "understat_extract_multiple",
    "understat_extract_shot_events",
    "understat_export_to_csv",
    "understat_get_match_ids",
    "understat_search_player_id",
    "understat_search_team_id",
    "understat_clear_cache",
    "understat_get_player",
    "understat_get_team",
    "understat_get_players",
    "understat_get_teams",
    "understat_get_shots",
    "understat_get_team_advanced",
    "understat_get_player_shots",
    # WhoScored
    "whoscored_extract_match_events",
    "whoscored_extract_pass_network",
    "whoscored_extract_player_heatmap",
    "whoscored_extract_shot_map",
    "whoscored_extract_field_occupation",
    "whoscored_extract_league_schedule",
    "whoscored_extract_missing_players",
    "whoscored_get_match_ids",
    "whoscored_search_player_id",
    "whoscored_search_team_id",
    "whoscored_clear_cache",
    "whoscored_export_to_csv",
    "whoscored_get_match_events",
    "whoscored_get_match_events_viz",
    "whoscored_get_pass_network",
    "whoscored_get_player_heatmap",
    "whoscored_get_shot_map",
    "whoscored_get_field_occupation",
    "whoscored_get_schedule",
    "whoscored_get_missing_players",
    # Transfermarkt
    "transfermarkt_get_player",
    "transfermarkt_clear_cache",
]


def check_available_modules() -> dict[str, str]:
    """Return import status of each wrapper module (for debugging)."""
    status = {}
    for name in ("fotmob_data", "understat_data", "whoscored_data"):
        try:
            __import__(f"{__package__}.{name}")
            status[name.removesuffix("_data")] = "Available"
        except ImportError as e:
            status[name.removesuffix("_data")] = f"Error: {e}"
    return status
