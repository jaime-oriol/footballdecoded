"""Scraper for https://www.sofascore.com.

SofaScore provides shot data with xG values for various leagues.
Uses Selenium to find event IDs and API for data extraction.
"""

import re
import time
from typing import Optional, Union
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ._common import BaseSeleniumReader
from ._config import DATA_DIR, TEAMNAME_REPLACEMENTS, logger

SOFASCORE_DATADIR = DATA_DIR / "SofaScore"
SOFASCORE_URL = "https://www.sofascore.com"
SOFASCORE_API_URL = "https://api.sofascore.com/api/v1"

# Shot body part mapping
SHOT_BODY_PARTS = {
    "right-foot": "Right foot",
    "left-foot": "Left foot",
    "head": "Head",
    "other": "Other"
}

# Shot situation mapping
SHOT_SITUATIONS = {
    "regular": "Open play",
    "set-piece": "Set piece",
    "direct-free-kick": "Direct free kick",
    "penalty": "Penalty",
    "fast-break": "Counter attack",
    "assisted": "Assisted"
}

# Shot result mapping
SHOT_RESULTS = {
    "goal": "Goal",
    "saved-shot": "Saved",
    "missed-shot": "Missed",
    "blocked-shot": "Blocked",
    "shot-on-post": "Post"
}


class SofaScore(BaseSeleniumReader):
    """Scraper for https://www.sofascore.com."""

    def __init__(self, leagues=None, proxy=None, no_cache=False, no_store=False, data_dir=DATA_DIR):
        """Initialize SofaScore scraper.

        Args:
            leagues: League(s) to scrape
            proxy: Proxy configuration
            no_cache: Bypass cache
            no_store: Don't save to cache
            data_dir: Data directory for cache
        """
        super().__init__(
            leagues=leagues,
            proxy=proxy,
            no_cache=no_cache,
            no_store=no_store,
            data_dir=data_dir / "SofaScore"
        )

    def read_shot_events(
        self,
        event_id: Optional[int] = None,
        home_team: Optional[str] = None,
        away_team: Optional[str] = None,
        match_date: Optional[str] = None
    ) -> pd.DataFrame:
        """Retrieve shot events for a match.

        Args:
            event_id: SofaScore event ID (if known)
            home_team: Home team name (for searching)
            away_team: Away team name (for searching)
            match_date: Match date in YYYY-MM-DD format

        Returns:
            DataFrame with shot data including xG values
        """
        # If event_id not provided, search for it
        if event_id is None:
            if not all([home_team, away_team, match_date]):
                raise ValueError("Must provide either event_id or (home_team, away_team, match_date)")
            event_id = self._find_event_id(home_team, away_team, match_date)
            if event_id is None:
                logger.error(f"Could not find event ID for {home_team} vs {away_team} on {match_date}")
                return pd.DataFrame()

        # Get shot data from API
        shots_data = self._get_shot_data_from_api(event_id)

        if not shots_data:
            return pd.DataFrame()

        # Convert to DataFrame
        return self._parse_shots_to_dataframe(shots_data, event_id)

    def _find_event_id(self, home_team: str, away_team: str, match_date: str) -> Optional[int]:
        """Find SofaScore event ID for a match using Selenium.

        Args:
            home_team: Home team name
            away_team: Away team name
            match_date: Match date in YYYY-MM-DD format

        Returns:
            Event ID or None if not found
        """
        try:
            # Navigate to search page with team name
            search_term = home_team.replace(' ', '-').lower()
            url = f"{SOFASCORE_URL}/team/football/{search_term}"

            logger.info(f"Searching for match: {home_team} vs {away_team} on {match_date}")
            self._driver.get(url)
            time.sleep(3)  # Wait for page load

            # Look for the match in recent fixtures
            # Try to find match links containing both team names
            match_date_formatted = match_date.replace('-', '/')

            # Search for event links in the page
            page_source = self._driver.page_source

            # Pattern: /event/{event_id}
            event_pattern = r'/football/[^/]+/[^/]+/[^/]+/[^/]+/(\d+)'
            event_ids = re.findall(event_pattern, page_source)

            if event_ids:
                # Return first found event ID
                # TODO: Improve matching logic to verify correct match
                event_id = int(event_ids[0])
                logger.info(f"Found event ID: {event_id}")
                return event_id

            logger.warning(f"No event ID found for {home_team} vs {away_team}")
            return None

        except Exception as e:
            logger.error(f"Error finding event ID: {e}")
            return None

    def _get_shot_data_from_api(self, event_id: int) -> dict:
        """Get shot data from SofaScore API.

        Args:
            event_id: SofaScore event ID

        Returns:
            Dictionary with shotmap data and event info
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.sofascore.com/',
            'Origin': 'https://www.sofascore.com',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
        }

        # First get event info for team names
        event_url = f"{SOFASCORE_API_URL}/event/{event_id}"
        shotmap_url = f"{SOFASCORE_API_URL}/event/{event_id}/shotmap"

        try:
            # Get event info
            event_response = requests.get(event_url, headers=headers, timeout=10)
            if event_response.status_code != 200:
                logger.error(f"Event info request failed: {event_response.status_code}")
                return {}

            event_data = event_response.json()
            event_info = event_data.get('event', {})

            # Get shotmap
            shotmap_response = requests.get(shotmap_url, headers=headers, timeout=10)
            if shotmap_response.status_code != 200:
                logger.error(f"Shotmap request failed: {shotmap_response.status_code}")
                return {}

            shotmap_data = shotmap_response.json()
            logger.info(f"Successfully retrieved {len(shotmap_data.get('shotmap', []))} shots")

            # Combine event info and shotmap
            return {
                'event_info': event_info,
                'shotmap': shotmap_data.get('shotmap', [])
            }

        except Exception as e:
            logger.error(f"Error fetching shot data: {e}")
            return {}

    def _parse_shots_to_dataframe(self, shots_data: dict, event_id: int) -> pd.DataFrame:
        """Parse SofaScore shot data to DataFrame.

        Args:
            shots_data: Raw shot data from API (includes event_info and shotmap)
            event_id: Event ID for reference

        Returns:
            DataFrame with standardized shot data
        """
        event_info = shots_data.get('event_info', {})
        shotmap = shots_data.get('shotmap', [])

        if not shotmap:
            return pd.DataFrame()

        # Extract team information
        home_team = event_info.get('homeTeam', {}).get('name', np.nan)
        home_team_id = event_info.get('homeTeam', {}).get('id', np.nan)
        away_team = event_info.get('awayTeam', {}).get('name', np.nan)
        away_team_id = event_info.get('awayTeam', {}).get('id', np.nan)

        shots = []
        for shot in shotmap:
            player = shot.get('player', {})
            coords = shot.get('playerCoordinates', {})
            is_home = shot.get('isHome', False)

            # Assign team based on isHome flag
            team = home_team if is_home else away_team
            team_id = home_team_id if is_home else away_team_id

            shots.append({
                'event_id': event_id,
                'shot_id': shot.get('id', np.nan),
                'team': team,
                'team_id': team_id,
                'player': player.get('name', np.nan),
                'player_id': player.get('id', np.nan),
                'xg': shot.get('xg', 0.0),
                'xgot': shot.get('xgot', 0.0),
                'location_x': coords.get('x', np.nan),
                'location_y': coords.get('y', np.nan),
                'location_z': coords.get('z', np.nan),
                'minute': shot.get('time', np.nan),
                'added_time': shot.get('addedTime', 0),
                'body_part': SHOT_BODY_PARTS.get(shot.get('bodyPart', ''), np.nan),
                'situation': SHOT_SITUATIONS.get(shot.get('situation', ''), np.nan),
                'result': SHOT_RESULTS.get(shot.get('shotType', ''), np.nan),
                'is_home': is_home,
                'goal_mouth_y': shot.get('goalMouthLocation', np.nan)
            })

        if not shots:
            return pd.DataFrame()

        df = pd.DataFrame(shots)

        # Apply team name replacements for consistency
        df = df.replace({'team': TEAMNAME_REPLACEMENTS})

        # Convert types
        df = df.convert_dtypes()

        return df

    def __del__(self):
        """Clean up Selenium driver."""
        if hasattr(self, '_driver'):
            try:
                self._driver.quit()
            except:
                pass
