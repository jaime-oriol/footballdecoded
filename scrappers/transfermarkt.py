"""Transfermarkt scraper: player profiles, positions, market values, contracts."""

import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union
from urllib.parse import quote

from lxml import html

from ._common import BaseRequestsReader
from ._config import DATA_DIR, NOCACHE, NOSTORE, logger

TRANSFERMARKT_DATADIR = DATA_DIR / "Transfermarkt"
TRANSFERMARKT_URL = "https://www.transfermarkt.com"

# Translate Transfermarkt's verbose position names to standard abbreviations
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
    """Scraper for transfermarkt.com player data.

    Extracts player profiles (position, foot, market value, contract dates)
    via HTML scraping and Transfermarkt's internal JSON API for market value
    history. Includes fuzzy name search with birth year disambiguation.

    Cached locally in ``data/Transfermarkt/``.
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
        # Rate limiting: 6-9s total per request to avoid 429 errors
        self.rate_limit = 6
        self.max_delay = 3

    def search_player(
        self, player_name: str, birth_year: Optional[int] = None
    ) -> Optional[str]:
        """Search for a player by name and return their Transfermarkt ID.

        Uses fuzzy matching (85% threshold) with optional birth year filtering
        to disambiguate common names.
        """
        # "schnellsuche" = German for "quick search"
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
                # "hauptlink" = "main link" (German) - player profile link
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

                # Filter by birth year (+-1 year tolerance for age rounding)
                if birth_year:
                    # "zentriert" = "centered" (German) - 3rd column holds age
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

        # 85% threshold avoids false positives (e.g. "Dani Olmo" vs "Dani Alves")
        if best_score >= 0.85:
            return best_match

        logger.debug(
            f"No match found with sufficient similarity for: {player_name} (best: {best_score:.2f})"
        )
        return None

    def read_player_market_value_history(self, player_id: str) -> list:
        """Extract market value history from Transfermarkt's internal JSON API.

        Returns list of dicts with 'date' (ISO) and 'market_value' keys.
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
                    # "datum_mw" = market value date, "mw" = market value (German)
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
        """Extract complete player profile (position, foot, value, contract, birth date, club).

        If season is provided (YY-YY format), fetches historical market value
        from the API instead of the current value shown on the profile page.
        """
        # "spieler" = "player" (German), slug "-" is ignored by Transfermarkt
        url = f"{TRANSFERMARKT_URL}/-/profil/spieler/{player_id}"

        filepath = self.data_dir / "players" / f"{player_id}.html"
        reader = self.get(url, filepath, max_age=30)

        tree = html.parse(reader)

        profile = {
            "player_id": player_id,
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
        """Get market value closest to a season (YY-YY format).

        Tries end-of-season (June, +-90 days) first, then start-of-season
        (October, +-60 days) as fallback.
        """
        try:
            from datetime import datetime

            parts = season.split('-')
            if len(parts) != 2:
                return None

            first_year = int('20' + parts[0])   # "24-25" -> 2024
            second_year = int('20' + parts[1])  # "24-25" -> 2025

            target_date_primary = f"{second_year}-06-01"    # End of season
            target_date_fallback = f"{first_year}-10-01"    # Start of season

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

            # Fallback: start-of-season (October) within 60 days
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
        """Extract main position, mapped to standard abbreviation (e.g. ST, CB)."""
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
        """Extract dominant foot (Left, Right, or Ambidextrous)."""
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
        """Extract current market value in EUR from profile header."""
        try:
            xpath = "//a[@class='data-header__market-value-wrapper']"
            value_elem = tree.xpath(xpath)
            if value_elem:
                # Exclude <p> children ("last updated" text)
                texts = value_elem[0].xpath(".//text()[not(parent::p)]")
                value_str = "".join(texts).strip()
                return self._parse_market_value(value_str)
        except Exception as e:
            logger.debug(f"Error extracting market value: {e}")
        return None

    def _extract_contract_expires(self, tree) -> Optional[str]:
        """Extract contract expiration date as ISO string."""
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
        """Extract date player joined current club as ISO string."""
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
        """Extract birth date as ISO string."""
        try:
            # schema.org itemprop is stable across layout changes
            xpath = "//span[@itemprop='birthDate']//text()"
            date_text = tree.xpath(xpath)
            if date_text:
                # Strip age suffix: '21/08/1988 (37)' -> '21/08/1988'
                date_str = date_text[0].strip().split('(')[0].strip()
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
                # Skip whitespace-only text nodes
                club = next((t.strip() for t in club_text if t.strip()), None)
                return club
        except Exception as e:
            logger.debug(f"Error extracting club: {e}")
        return None

    @staticmethod
    def _extract_player_id(url: str) -> Optional[str]:
        """Extract numeric player ID from Transfermarkt URL."""
        match = re.search(r"/spieler/(\d+)", url)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize name for comparison: lowercase, strip accents and punctuation."""
        name = name.lower().strip()
        # Decompose unicode then remove accent marks (category "Mn")
        name = unicodedata.normalize("NFD", name)
        name = "".join(c for c in name if unicodedata.category(c) != "Mn")
        name = re.sub(r"[^\w\s]", "", name)
        name = re.sub(r"\s+", " ", name)
        return name

    @staticmethod
    def _calculate_similarity(name1: str, name2: str) -> float:
        """Calculate name similarity ratio (0.0 to 1.0) via SequenceMatcher."""
        return SequenceMatcher(None, name1, name2).ratio()

    @staticmethod
    def _parse_market_value(value_str: str) -> Optional[float]:
        """Parse market value string to EUR float (e.g. '€25.00m' -> 25000000.0)."""
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
        """Parse date string to ISO format YYYY-MM-DD (e.g. 'Jul 1, 2022' -> '2022-07-01')."""
        try:
            from datetime import datetime

            # Transfermarkt uses different formats depending on locale/page section
            date_formats = [
                "%b %d, %Y",   # "Jul 1, 2022" (English)
                "%d %b %Y",   # "01 Jul 2022"
                "%d/%m/%Y",   # "01/07/2022" (market value API)
                "%Y-%m-%d",   # "2022-07-01" (already ISO)
                "%d.%m.%Y",   # "01.07.2022" (German)
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
