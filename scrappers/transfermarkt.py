"""Scraper for transfermarkt.com.

Transfermarkt provides detailed player information including specific positions,
dominant foot, market values, and contract details.
"""

import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple, Union
from urllib.parse import quote

from lxml import html

from ._common import BaseRequestsReader
from ._config import DATA_DIR, NOCACHE, NOSTORE, logger

TRANSFERMARKT_DATADIR = DATA_DIR / "Transfermarkt"
TRANSFERMARKT_URL = "https://www.transfermarkt.com"

POSITION_MAPPING = {
    "Goalkeeper": "GK",
    "Centre-Back": "CB",
    "Left-Back": "LB",
    "Right-Back": "RB",
    "Defensive Midfield": "CDM",
    "Central Midfield": "CM",
    "Attacking Midfield": "CAM",
    "Left Midfield": "LM",
    "Right Midfield": "RM",
    "Left Winger": "LW",
    "Right Winger": "RW",
    "Second Striker": "SS",
    "Centre-Forward": "ST",
    "Attack": "FW",
    "midfield": "MF",
    "Defender": "DF",
}

FOOT_MAPPING = {
    "left": "Left",
    "right": "Right",
    "both": "Ambidextrous",
}


class Transfermarkt(BaseRequestsReader):
    """Provides data from https://www.transfermarkt.com.

    Data will be downloaded as necessary and cached locally in
    ``~/soccerdata/data/Transfermarkt``.

    Parameters
    ----------
    proxy : 'tor' or dict or list(dict) or callable, optional
        Use a proxy to hide your IP address.
    no_cache : bool
        If True, will not use cached data.
    no_store : bool
        If True, will not store downloaded data.
    data_dir : Path
        Path to directory where data will be cached.
    """

    def __init__(
        self,
        proxy: Optional[Union[str, list[str], Callable[[], str]]] = None,
        no_cache: bool = NOCACHE,
        no_store: bool = NOSTORE,
        data_dir: Path = TRANSFERMARKT_DATADIR,
    ):
        """Initialize Transfermarkt reader."""
        super().__init__(
            leagues=None,
            proxy=proxy,
            no_cache=no_cache,
            no_store=no_store,
            data_dir=data_dir,
        )
        self.rate_limit = 3
        self.max_delay = 2

    def search_player(
        self, player_name: str, birth_year: Optional[int] = None
    ) -> Optional[str]:
        """Search for player and return Transfermarkt ID.

        Args:
            player_name: Player name to search
            birth_year: Optional birth year for filtering results

        Returns:
            Transfermarkt player ID or None if not found
        """
        query = quote(player_name)
        url = f"{TRANSFERMARKT_URL}/schnellsuche/ergebnis/schnellsuche?query={query}"

        filepath = self.data_dir / "search" / f"{self._normalize_name(player_name)}.html"
        reader = self.get(url, filepath, max_age=60)

        tree = html.parse(reader)
        results_xpath = "//table[contains(@class, 'items')]//tbody//tr"
        results = tree.xpath(results_xpath)

        if not results:
            logger.debug(f"No results found for player: {player_name}")
            return None

        best_match = None
        best_score = 0.0

        normalized_search = self._normalize_name(player_name)

        for result in results:
            try:
                player_link = result.xpath(".//td[@class='hauptlink']//a/@href")
                if not player_link:
                    continue

                player_id = self._extract_player_id(player_link[0])
                if not player_id:
                    continue

                name_elem = result.xpath(".//td[@class='hauptlink']//a/text()")
                if not name_elem:
                    continue

                result_name = name_elem[0].strip()
                normalized_result = self._normalize_name(result_name)

                similarity = self._calculate_similarity(normalized_search, normalized_result)

                if birth_year:
                    age_elem = result.xpath(".//td[@class='zentriert'][3]/text()")
                    if age_elem:
                        try:
                            age = int(age_elem[0].strip())
                            from datetime import datetime

                            current_year = datetime.now().year
                            player_birth_year = current_year - age
                            if abs(player_birth_year - birth_year) > 1:
                                continue
                        except (ValueError, IndexError):
                            pass

                if similarity > best_score:
                    best_score = similarity
                    best_match = player_id

            except Exception as e:
                logger.debug(f"Error processing search result: {e}")
                continue

        if best_score >= 0.85:
            return best_match

        logger.debug(
            f"No match found with sufficient similarity for: {player_name} (best: {best_score:.2f})"
        )
        return None

    def read_player_market_value_history(self, player_id: str) -> list:
        """Extract market value history from API.

        Args:
            player_id: Transfermarkt player ID

        Returns:
            List of dictionaries with date and market_value
        """
        url = f"{TRANSFERMARKT_URL}/ceapi/marketValueDevelopment/graph/{player_id}"

        filepath = self.data_dir / "market_history" / f"{player_id}.json"
        reader = self.get(url, filepath, max_age=30)

        try:
            import json
            from datetime import datetime
            data = json.load(reader)

            history = []
            if 'list' in data:
                for entry in data['list']:
                    if 'datum_mw' in entry and 'mw' in entry:
                        date_str = entry['datum_mw']
                        try:
                            date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                            iso_date = date_obj.strftime('%Y-%m-%d')
                        except ValueError:
                            iso_date = date_str

                        history.append({
                            'date': iso_date,
                            'market_value': entry['mw']
                        })
            return history
        except Exception as e:
            logger.debug(f"Error parsing market value history: {e}")
            return []

    def read_player_profile(self, player_id: str, season: Optional[str] = None) -> Dict[str, Any]:
        """Extract complete player profile.

        Args:
            player_id: Transfermarkt player ID
            season: Season in YY-YY format (e.g., '20-21') for historical market value

        Returns:
            Dictionary with player data
        """
        url = f"{TRANSFERMARKT_URL}/-/profil/spieler/{player_id}"

        filepath = self.data_dir / "players" / f"{player_id}.html"
        reader = self.get(url, filepath, max_age=30)

        tree = html.parse(reader)

        profile = {
            "transfermarkt_player_id": player_id,
            "position_specific": None,
            "primary_foot": None,
            "market_value_eur": None,
            "contract_start_date": None,
            "contract_end_date": None,
            "birth_date": None,
            "club": None,
        }

        profile["position_specific"] = self._extract_position(tree)
        profile["primary_foot"] = self._extract_foot(tree)

        if season:
            profile["market_value_eur"] = self._get_market_value_for_season(player_id, season)
        else:
            profile["market_value_eur"] = self._extract_market_value(tree)

        profile["contract_start_date"] = self._extract_contract_joined(tree)
        profile["contract_end_date"] = self._extract_contract_expires(tree)
        profile["birth_date"] = self._extract_birth_date(tree)
        profile["club"] = self._extract_current_club(tree)

        return profile

    def _get_market_value_for_season(self, player_id: str, season: str) -> Optional[float]:
        """Get market value for specific season.

        Priority:
        1. June 1st of second year (end of season)
        2. October 1st of first year (start of season)

        Args:
            player_id: Transfermarkt player ID
            season: Season in YY-YY format (e.g., '20-21')

        Returns:
            Market value in EUR or None
        """
        try:
            from datetime import datetime

            parts = season.split('-')
            if len(parts) != 2:
                return None

            first_year = int('20' + parts[0])
            second_year = int('20' + parts[1])

            target_date_primary = f"{second_year}-06-01"
            target_date_fallback = f"{first_year}-10-01"

            history = self.read_player_market_value_history(player_id)

            if not history:
                return None

            best_match = None
            min_diff = float('inf')

            for entry in history:
                entry_date = entry['date']

                if entry_date == target_date_primary:
                    value_str = entry['market_value']
                    return self._parse_market_value(value_str)

                try:
                    entry_dt = datetime.strptime(entry_date, '%Y-%m-%d')
                    target_dt = datetime.strptime(target_date_primary, '%Y-%m-%d')
                    diff = abs((entry_dt - target_dt).days)

                    if diff < min_diff:
                        min_diff = diff
                        best_match = entry
                except ValueError:
                    continue

            if best_match and min_diff <= 90:
                value_str = best_match['market_value']
                return self._parse_market_value(value_str)

            for entry in history:
                entry_date = entry['date']

                if entry_date == target_date_fallback:
                    value_str = entry['market_value']
                    return self._parse_market_value(value_str)

                try:
                    entry_dt = datetime.strptime(entry_date, '%Y-%m-%d')
                    fallback_dt = datetime.strptime(target_date_fallback, '%Y-%m-%d')
                    diff = abs((entry_dt - fallback_dt).days)

                    if diff <= 60:
                        value_str = entry['market_value']
                        return self._parse_market_value(value_str)
                except ValueError:
                    continue

            return None

        except Exception as e:
            logger.debug(f"Error getting market value for season {season}: {e}")
            return None

    def _extract_position(self, tree) -> Optional[str]:
        """Extract main position from profile."""
        try:
            xpath = "//dt[contains(text(),'Main position:')]//following::dd[1]//text()"
            position_text = tree.xpath(xpath)
            if position_text:
                position = position_text[0].strip()
                return POSITION_MAPPING.get(position, position)
        except Exception as e:
            logger.debug(f"Error extracting position: {e}")
        return None

    def _extract_foot(self, tree) -> Optional[str]:
        """Extract dominant foot from profile."""
        try:
            xpath = "//span[text()='Foot:']//following::span[1]//text()"
            foot_text = tree.xpath(xpath)
            if foot_text:
                foot = foot_text[0].strip().lower()
                return FOOT_MAPPING.get(foot, None)
        except Exception as e:
            logger.debug(f"Error extracting foot: {e}")
        return None

    def _extract_market_value(self, tree) -> Optional[float]:
        """Extract market value in EUR."""
        try:
            xpath = "//a[@class='data-header__market-value-wrapper']"
            value_elem = tree.xpath(xpath)
            if value_elem:
                texts = value_elem[0].xpath(".//text()[not(parent::p)]")
                value_str = "".join(texts).strip()
                return self._parse_market_value(value_str)
        except Exception as e:
            logger.debug(f"Error extracting market value: {e}")
        return None

    def _extract_contract_expires(self, tree) -> Optional[str]:
        """Extract contract expiration date."""
        try:
            xpath = "//span[contains(text(),'Contract expires')]//following::span[1]//text()"
            date_text = tree.xpath(xpath)
            if date_text:
                date_str = date_text[0].strip()
                return self._parse_date(date_str)
        except Exception as e:
            logger.debug(f"Error extracting contract expiration: {e}")
        return None

    def _extract_contract_joined(self, tree) -> Optional[str]:
        """Extract date player joined current club."""
        try:
            xpath = "//span[contains(text(),'Joined')]//following::span[1]//text()"
            date_text = tree.xpath(xpath)
            if date_text:
                date_str = date_text[0].strip()
                return self._parse_date(date_str)
        except Exception as e:
            logger.debug(f"Error extracting join date: {e}")
        return None

    def _extract_birth_date(self, tree) -> Optional[str]:
        """Extract birth date."""
        try:
            xpath = "//span[@itemprop='birthDate']//text()"
            date_text = tree.xpath(xpath)
            if date_text:
                date_str = date_text[0].strip()
                return self._parse_date(date_str)
        except Exception as e:
            logger.debug(f"Error extracting birth date: {e}")
        return None

    def _extract_current_club(self, tree) -> Optional[str]:
        """Extract current club name."""
        try:
            xpath = "//span[@class='data-header__club']//text()"
            club_text = tree.xpath(xpath)
            if club_text:
                return club_text[0].strip()
        except Exception as e:
            logger.debug(f"Error extracting club: {e}")
        return None

    @staticmethod
    def _extract_player_id(url: str) -> Optional[str]:
        """Extract player ID from URL."""
        match = re.search(r"/spieler/(\d+)", url)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize player name for matching."""
        name = name.lower().strip()
        name = unicodedata.normalize("NFD", name)
        name = "".join(c for c in name if unicodedata.category(c) != "Mn")
        name = re.sub(r"[^\w\s]", "", name)
        name = re.sub(r"\s+", " ", name)
        return name

    @staticmethod
    def _calculate_similarity(name1: str, name2: str) -> float:
        """Calculate similarity between two names."""
        return SequenceMatcher(None, name1, name2).ratio()

    @staticmethod
    def _parse_market_value(value_str: str) -> Optional[float]:
        """Parse market value string to EUR float.

        Examples:
            '€25.00m' -> 25000000.0
            '€1.50m' -> 1500000.0
            '€750k' -> 750000.0
        """
        try:
            value_str = value_str.replace("€", "").replace(" ", "").lower()

            if "m" in value_str:
                value = float(value_str.replace("m", ""))
                return value * 1_000_000
            elif "k" in value_str:
                value = float(value_str.replace("k", ""))
                return value * 1_000
            elif value_str:
                return float(value_str)
        except (ValueError, AttributeError):
            pass
        return None

    @staticmethod
    def _parse_date(date_str: str) -> Optional[str]:
        """Parse date string to ISO format YYYY-MM-DD.

        Examples:
            'Jul 1, 2022' -> '2022-07-01'
            'Jun 30, 2027' -> '2027-06-30'
        """
        try:
            from datetime import datetime

            date_formats = [
                "%b %d, %Y",
                "%d %b %Y",
                "%d/%m/%Y",
                "%Y-%m-%d",
                "%d.%m.%Y",
            ]

            for fmt in date_formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%Y-%m-%d")
                except ValueError:
                    continue

        except Exception:
            pass
        return None


def _as_int(value: Any) -> Optional[int]:
    """Convert value to int safely."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _as_float(value: Any) -> Optional[float]:
    """Convert value to float safely."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _as_str(value: Any) -> Optional[str]:
    """Convert value to str safely."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    return str(value).strip()
