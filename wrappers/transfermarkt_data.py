"""Transfermarkt data wrapper.

Extracts player profiles (position, foot, market value, contract) with
in-memory player ID caching to avoid repeated search requests.
"""

from typing import Dict, Optional, Any

from scrappers.transfermarkt import Transfermarkt
from scrappers._config import logger

_transfermarkt_player_cache = {}  # "name_birthyear" -> player_id


def transfermarkt_get_player(
    player_name: str,
    league: str,
    season: str,
    birth_year: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """Fetch a player's Transfermarkt profile with player ID caching.

    Args:
        player_name: Player name to search.
        league: League code (context only, not used in query).
        season: Season in YY-YY format (e.g. '24-25').
        birth_year: Birth year to disambiguate search results.

    Returns:
        Dict with 'transfermarkt_'-prefixed keys, or None if not found.
        Season >= 25-26 returns current market value; earlier uses historical.
    """
    if not player_name or not isinstance(player_name, str):
        logger.debug("Invalid player_name provided to transfermarkt_get_player")
        return None

    cache_key = f"{player_name}_{birth_year}"

    try:
        tm = Transfermarkt()
    except Exception as e:
        logger.error(f"Error initializing Transfermarkt: {e}")
        return None

    if cache_key in _transfermarkt_player_cache:
        player_id = _transfermarkt_player_cache[cache_key]
        logger.debug(f"Using cached player_id for {player_name}: {player_id}")
    else:
        try:
            player_id = tm.search_player(player_name, birth_year)

            if not player_id:
                logger.debug(f"Player not found on Transfermarkt: {player_name}")
                return None

            _transfermarkt_player_cache[cache_key] = player_id
            logger.debug(f"Found player_id for {player_name}: {player_id}")

        except Exception as e:
            logger.error(f"Error searching player {player_name}: {e}")
            return None

    try:
        # TM only has historical market values for past seasons;
        # for current/future seasons, fetch the live value instead
        use_current_value = False
        if season:
            try:
                first_year = int(season.split('-')[0])
                use_current_value = first_year >= 25
            except (ValueError, IndexError):
                logger.warning(f"Invalid season format: {season}, using historical value")

        if use_current_value:
            profile = tm.read_player_profile(player_id, season=None)
            logger.debug(f"Using CURRENT market value for {player_name} (season {season})")
        else:
            profile = tm.read_player_profile(player_id, season=season)
            logger.debug(f"Using HISTORICAL market value for {player_name} (season {season})")

        if not profile:
            logger.debug(f"Could not extract profile for player_id: {player_id}")
            return None

        # TM has no contract history, so contract fields are only reliable for current seasons
        profile['contract_is_current'] = use_current_value

        prefixed_data = {f"transfermarkt_{k}": v for k, v in profile.items()}

        return prefixed_data

    except Exception as e:
        logger.error(f"Error extracting profile for {player_name}: {e}")
        return None


def clear_cache():
    """Clear the in-memory player ID cache."""
    _transfermarkt_player_cache.clear()
    logger.info("Transfermarkt cache cleared")
