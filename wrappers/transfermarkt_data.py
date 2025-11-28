"""Transfermarkt wrapper with caching and error handling.

Simplified API for extracting player data from Transfermarkt including
specific positions, dominant foot, market values, and contract details.
"""

import sys
import os
from typing import Dict, Optional, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrappers.transfermarkt import Transfermarkt
from scrappers._config import logger

_transfermarkt_player_cache = {}


def transfermarkt_get_player(
    player_name: str,
    league: str,
    season: str,
    birth_year: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """Get player data from Transfermarkt with caching.

    Args:
        player_name: Player name to search
        league: League code (for context, not directly used)
        season: Season string in YY-YY format (e.g., '24-25', '25-26')
        birth_year: Optional birth year for filtering search results

    Returns:
        Dictionary with Transfermarkt data prefixed with 'transfermarkt_'
        or None if player not found

    Notes:
        - For season '25-26' (2025-2026) and later: uses CURRENT market value
        - For earlier seasons: uses HISTORICAL market value from season end

    Example:
        data = transfermarkt_get_player("Vinicius Junior", "ESP-La Liga", "24-25", 2000)
        if data:
            print(data['transfermarkt_position_specific'])
            print(data['transfermarkt_primary_foot'])
            print(data['transfermarkt_market_value_eur'])
    """
    if not player_name or not isinstance(player_name, str):
        logger.debug("Invalid player_name provided to transfermarkt_get_player")
        return None

    cache_key = f"{player_name}_{birth_year}"

    if cache_key in _transfermarkt_player_cache:
        player_id = _transfermarkt_player_cache[cache_key]
        logger.debug(f"Using cached player_id for {player_name}: {player_id}")
    else:
        try:
            tm = Transfermarkt()
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
        tm = Transfermarkt()

        # Determine if we should use current or historical market value
        # For season 25-26 and later, use current value (season=None)
        # For earlier seasons, use historical value
        # Note: season format is "YY-YY" (e.g., "24-25", "25-26")
        use_current_value = False
        if season:
            try:
                # Extract first year from season (e.g., "25-26" -> 25)
                first_year = int(season.split('-')[0])
                use_current_value = first_year >= 25  # Season 25-26 and later
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

        # Añadir indicador de si los datos de contrato son actuales o históricos
        # Nota: Transfermarkt API no proporciona historial de contratos, solo de valores de mercado
        # Por lo tanto, contract_start_date y contract_end_date son siempre actuales
        profile['contract_is_current'] = use_current_value

        prefixed_data = {f"transfermarkt_{k}": v for k, v in profile.items()}

        return prefixed_data

    except Exception as e:
        logger.error(f"Error extracting profile for {player_name}: {e}")
        return None


def clear_cache():
    """Clear Transfermarkt player ID cache."""
    global _transfermarkt_player_cache
    _transfermarkt_player_cache.clear()
    logger.info("Transfermarkt cache cleared")
