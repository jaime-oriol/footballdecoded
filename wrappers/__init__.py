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
    extract_player_season as fbref_extract_player_season,
    extract_player_match as fbref_extract_player_match,
    extract_multiple_players as fbref_extract_multiple_players,
    extract_league_players as fbref_extract_league_players,
    extract_team_season as fbref_extract_team_season,
    extract_multiple_teams as fbref_extract_multiple_teams,
    extract_match_events as fbref_extract_match_events,
    extract_league_schedule as fbref_extract_league_schedule,
    analyze_full_squad as fbref_analyze_full_squad,
    compare_teams as fbref_compare_teams,
    analyze_league as fbref_analyze_league,
    export_to_csv as fbref_export_to_csv,
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
    extract_player_season as understat_extract_player_season,
    extract_multiple_players as understat_extract_multiple_players,
    extract_team_season as understat_extract_team_season,
    extract_multiple_teams as understat_extract_multiple_teams,
    extract_shot_events as understat_extract_shot_events,
    merge_with_fbref as understat_merge_with_fbref,
    export_to_csv as understat_export_to_csv,
    get_player as understat_get_player,
    get_team as understat_get_team,
    get_squad as understat_get_squad,
    get_shots as understat_get_shots
)

# ====================================================================
# WHOSCORED WRAPPER IMPORTS
# ====================================================================

from .whoscored_data import (
    # Core spatial event extraction
    extract_match_events as whoscored_extract_match_events,
    extract_pass_network as whoscored_extract_pass_network,
    extract_player_heatmap as whoscored_extract_player_heatmap,
    extract_defensive_events as whoscored_extract_defensive_events,
    extract_shot_map as whoscored_extract_shot_map,
    extract_match_momentum as whoscored_extract_match_momentum,
    extract_field_occupation as whoscored_extract_field_occupation,
    
    # Schedule and context
    extract_league_schedule as whoscored_extract_league_schedule,
    extract_match_missing_players as whoscored_extract_match_missing_players,
    
    # Export utilities
    export_to_csv as whoscored_export_to_csv,
    
    # Quick access functions
    get_match_events as whoscored_get_match_events,
    get_match_events_viz as whoscored_get_match_events_viz,
    get_pass_network as whoscored_get_pass_network,
    get_player_heatmap as whoscored_get_player_heatmap,
    get_defensive_events as whoscored_get_defensive_events,
    get_shot_map as whoscored_get_shot_map,
    get_field_occupation as whoscored_get_field_occupation,
    get_match_momentum as whoscored_get_match_momentum,
    get_schedule as whoscored_get_schedule,
    get_missing_players as whoscored_get_missing_players
)

# ====================================================================
# ALL AVAILABLE FUNCTIONS
# ====================================================================

__all__ = [
    # FBref wrapper functions
    "fbref_extract_player_season",
    "fbref_extract_player_match", 
    "fbref_extract_multiple_players",
    "fbref_extract_league_players",
    "fbref_extract_team_season",
    "fbref_extract_multiple_teams",
    "fbref_extract_match_events",
    "fbref_extract_league_schedule",
    "fbref_analyze_full_squad",
    "fbref_compare_teams",
    "fbref_analyze_league",
    "fbref_export_to_csv",
    "fbref_get_player",
    "fbref_get_team",
    "fbref_get_players",
    "fbref_get_teams",
    "fbref_get_league_players",
    "fbref_get_match_data",
    "fbref_get_schedule",
    
    # Understat wrapper functions
    "understat_extract_player_season",
    "understat_extract_multiple_players",
    "understat_extract_team_season",
    "understat_extract_multiple_teams",
    "understat_extract_shot_events",
    "understat_merge_with_fbref",
    "understat_export_to_csv",
    "understat_get_player",
    "understat_get_team",
    "understat_get_squad",
    "understat_get_shots",
    
    # WhoScored wrapper functions - UPDATED
    "whoscored_extract_match_events",
    "whoscored_extract_pass_network",
    "whoscored_extract_player_heatmap",
    "whoscored_extract_defensive_events",
    "whoscored_extract_shot_map",
    "whoscored_extract_match_momentum",
    "whoscored_extract_field_occupation",
    "whoscored_extract_league_schedule",
    "whoscored_extract_match_missing_players",
    "whoscored_export_to_csv",
    "whoscored_get_match_events",
    "whoscored_get_match_events_viz",
    "whoscored_get_pass_network",
    "whoscored_get_player_heatmap",
    "whoscored_get_defensive_events",
    "whoscored_get_shot_map",
    "whoscored_get_field_occupation",
    "whoscored_get_match_momentum",
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
        modules_status['fbref'] = "✅ Available"
    except ImportError as e:
        modules_status['fbref'] = f"❌ Error: {e}"
    
    try:
        from . import understat_data
        modules_status['understat'] = "✅ Available"
    except ImportError as e:
        modules_status['understat'] = f"❌ Error: {e}"
    
    try:
        from . import whoscored_data_optimized
        modules_status['whoscored'] = "✅ Available"
    except ImportError as e:
        modules_status['whoscored'] = f"❌ Error: {e}"
    
    return modules_status