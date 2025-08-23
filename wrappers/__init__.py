# wrappers/__init__.py
"""
FootballDecoded Professional Data Wrappers
==========================================
Complete professional wrappers for extracting ALL metrics from football data sources.
Focus: FBref complete stats, Understat advanced metrics, WhoScored spatial data.
"""

__version__ = "1.0.0"

# ====================================================================
# FBREF WRAPPER IMPORTS
# ====================================================================

from .fbref_data import (
    # Core extraction functions
    extract_data as fbref_extract_data,
    extract_multiple as fbref_extract_multiple,
    extract_league_players as fbref_extract_league_players,
    extract_match_events as fbref_extract_match_events,
    extract_league_schedule as fbref_extract_league_schedule,
    export_to_csv as fbref_export_to_csv,
    
    # Input validation functions
    validate_inputs_with_suggestions as fbref_validate_inputs,
    
    # Cache management
    clear_cache as fbref_clear_cache,
    
    # Quick access functions
    get_player as fbref_get_player,
    get_team as fbref_get_team,
    get_players as fbref_get_players,
    get_teams as fbref_get_teams,
    get_league_players as fbref_get_league_players,
    get_match_data as fbref_get_match_data,
    get_schedule as fbref_get_schedule
)

# ====================================================================
# UNDERSTAT WRAPPER IMPORTS
# ====================================================================

from .understat_data import (
    # Core extraction functions
    extract_data as understat_extract_data,
    extract_multiple as understat_extract_multiple,
    extract_shot_events as understat_extract_shot_events,
    merge_with_fbref as understat_merge_with_fbref,
    export_to_csv as understat_export_to_csv,
    
    # New automatic ID retrieval functions
    get_match_ids as understat_get_match_ids,
    search_player_id as understat_search_player_id,
    search_team_id as understat_search_team_id,
    
    # Cache management
    clear_cache as understat_clear_cache,
    
    # Quick access functions
    get_player as understat_get_player,
    get_team as understat_get_team,
    get_players as understat_get_players,
    get_teams as understat_get_teams,
    get_shots as understat_get_shots
)

# ====================================================================
# WHOSCORED WRAPPER IMPORTS
# ====================================================================

from .whoscored_data import (
    # Core spatial extraction functions
    extract_match_events as whoscored_extract_match_events,
    extract_pass_network as whoscored_extract_pass_network,
    extract_player_heatmap as whoscored_extract_player_heatmap,
    extract_shot_map as whoscored_extract_shot_map,
    extract_field_occupation as whoscored_extract_field_occupation,
    
    # Schedule and context functions
    extract_league_schedule as whoscored_extract_league_schedule,
    extract_missing_players as whoscored_extract_missing_players,
    
    # New automatic ID retrieval functions
    get_match_ids as whoscored_get_match_ids,
    search_player_id as whoscored_search_player_id,
    search_team_id as whoscored_search_team_id,
    
    # Cache management
    clear_cache as whoscored_clear_cache,
    
    # Export utilities
    export_to_csv as whoscored_export_to_csv,
    
    # Quick access functions
    get_match_events as whoscored_get_match_events,
    get_match_events_viz as whoscored_get_match_events_viz,
    get_pass_network as whoscored_get_pass_network,
    get_player_heatmap as whoscored_get_player_heatmap,
    get_shot_map as whoscored_get_shot_map,
    get_field_occupation as whoscored_get_field_occupation,
    get_schedule as whoscored_get_schedule,
    get_missing_players as whoscored_get_missing_players
)

# ====================================================================
# ALL AVAILABLE FUNCTIONS
# ====================================================================

__all__ = [
    # FBref wrapper functions
    "fbref_extract_data",
    "fbref_extract_multiple",
    "fbref_extract_league_players",
    "fbref_extract_match_events",
    "fbref_extract_league_schedule",
    "fbref_export_to_csv",
    "fbref_validate_inputs",
    "fbref_clear_cache",
    "fbref_get_player",
    "fbref_get_team",
    "fbref_get_players",
    "fbref_get_teams",
    "fbref_get_league_players",
    "fbref_get_match_data",
    "fbref_get_schedule",
    
    # Understat wrapper functions
    "understat_extract_data",
    "understat_extract_multiple",
    "understat_extract_shot_events",
    "understat_merge_with_fbref",
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
    
    # WhoScored wrapper functions
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
    "whoscored_get_missing_players"
]

# ====================================================================
# HELPER FUNCTIONS
# ====================================================================

def check_available_modules():
    """Check which modules are available and working."""
    modules_status = {}
    
    try:
        from . import fbref_data
        modules_status['fbref'] = "Available"
    except ImportError as e:
        modules_status['fbref'] = f"Error: {e}"
    
    try:
        from . import understat_data
        modules_status['understat'] = "Available"
    except ImportError as e:
        modules_status['understat'] = f"Error: {e}"
    
    try:
        from . import whoscored_data
        modules_status['whoscored'] = "Available"
    except ImportError as e:
        modules_status['whoscored'] = f"Error: {e}"
    
    return modules_status