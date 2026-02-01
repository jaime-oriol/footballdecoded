"""Scraper for Transfermarkt penalty statistics.

Extracts penalty data from LaLiga (2004-2026):
- Team penalties received (a favor)
- Team penalties conceded (en contra)
- Penalty scorers (goleadores)
- Penalty misses detail (fallos con minuto, marcador, portero)
"""

import re
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from lxml import html

from ._common import BaseRequestsReader
from ._config import DATA_DIR, NOCACHE, NOSTORE, logger

PENALTIES_DATADIR = DATA_DIR / "TransfermarktPenalties"
TRANSFERMARKT_URL = "https://www.transfermarkt.com"

# LaLiga competition ID
LALIGA_ID = "ES1"


class TransfermarktPenalties(BaseRequestsReader):
    """Scraper for Transfermarkt penalty statistics."""

    def __init__(
        self,
        no_cache: bool = NOCACHE,
        no_store: bool = NOSTORE,
        data_dir: Path = PENALTIES_DATADIR,
    ):
        """Initialize penalty scraper."""
        super().__init__(
            leagues=None,
            proxy=None,
            no_cache=no_cache,
            no_store=no_store,
            data_dir=data_dir,
        )
        self.rate_limit = 6
        self.max_delay = 3

    def get_team_penalties_received(self, season: int) -> pd.DataFrame:
        """Get penalties received (a favor) by team for a season.

        Args:
            season: Year of season start (e.g., 2023 for 2023-24)

        Returns:
            DataFrame with columns: team, penalties_received, scored, missed, goal_rate
        """
        url = f"{TRANSFERMARKT_URL}/laliga/topErhalteneElfmeter/wettbewerb/{LALIGA_ID}/saison_id/{season}"
        filepath = self.data_dir / "received" / f"{season}.html"
        filepath.parent.mkdir(parents=True, exist_ok=True)

        reader = self.get(url, filepath, max_age=30)
        tree = html.parse(reader)

        # Find the table with class 'items' that has penalty headers
        tables = tree.xpath("//table[@class='items']")
        table = None
        for t in tables:
            headers = t.xpath(".//thead//th//text()")
            if any('received' in h.lower() or 'scored' in h.lower() for h in headers):
                table = t
                break

        if table is None:
            logger.warning(f"No penalties received table found for season {season}")
            return pd.DataFrame()

        rows = table.xpath(".//tbody//tr")

        data = []
        for row in rows:
            cells = row.xpath(".//td")
            if len(cells) >= 7:
                # Team name is in cell 2
                team = cells[2].text_content().strip()

                data.append({
                    'season': f"{season}-{str(season+1)[-2:]}",
                    'team': team,
                    'penalties_received': self._parse_int(cells[3].text_content()),
                    'scored': self._parse_int(cells[4].text_content()),
                    'missed': self._parse_int(cells[5].text_content()),
                    'goal_rate': self._parse_pct(cells[6].text_content()),
                })

        return pd.DataFrame(data)

    def get_team_penalties_conceded(self, season: int) -> pd.DataFrame:
        """Get penalties conceded (en contra) by team for a season.

        Args:
            season: Year of season start (e.g., 2023 for 2023-24)

        Returns:
            DataFrame with columns: team, penalties_conceded, saved, goals_against, save_rate
        """
        url = f"{TRANSFERMARKT_URL}/laliga/topVerursachteElfmeter/wettbewerb/{LALIGA_ID}/saison_id/{season}"
        filepath = self.data_dir / "conceded" / f"{season}.html"
        filepath.parent.mkdir(parents=True, exist_ok=True)

        reader = self.get(url, filepath, max_age=30)
        tree = html.parse(reader)

        # Find the table with class 'items' that has penalty headers
        tables = tree.xpath("//table[@class='items']")
        table = None
        for t in tables:
            headers = t.xpath(".//thead//th//text()")
            if any('conceded' in h.lower() or 'defence' in h.lower() for h in headers):
                table = t
                break

        if table is None:
            logger.warning(f"No penalties conceded table found for season {season}")
            return pd.DataFrame()

        rows = table.xpath(".//tbody//tr")

        data = []
        for row in rows:
            cells = row.xpath(".//td")
            if len(cells) >= 7:
                team = cells[2].text_content().strip()
                saved = self._parse_int(cells[3].text_content())
                conceded = self._parse_int(cells[4].text_content())
                missed = self._parse_int(cells[5].text_content())

                data.append({
                    'season': f"{season}-{str(season+1)[-2:]}",
                    'team': team,
                    'penalties_conceded': conceded,
                    'saved': saved,
                    'goals_against': conceded - saved if conceded and saved else None,
                    'missed_by_opponent': missed,
                    'save_rate': self._parse_pct(cells[6].text_content()),
                })

        return pd.DataFrame(data)

    def get_penalty_scorers(self, season: int) -> pd.DataFrame:
        """Get penalty scorers for a season.

        Args:
            season: Year of season start (e.g., 2023 for 2023-24)

        Returns:
            DataFrame with columns: player, team, penalties, scored, missed, conversion_rate
        """
        url = f"{TRANSFERMARKT_URL}/laliga/elfmeterschuetzen/wettbewerb/{LALIGA_ID}/saison_id/{season}"
        filepath = self.data_dir / "scorers" / f"{season}.html"
        filepath.parent.mkdir(parents=True, exist_ok=True)

        reader = self.get(url, filepath, max_age=30)
        tree = html.parse(reader)

        # Find the main table with player penalty data (first items table)
        tables = tree.xpath("//table[@class='items']")
        if not tables:
            logger.warning(f"No penalty scorers table found for season {season}")
            return pd.DataFrame()

        table = tables[0]  # First table has player data
        rows = table.xpath(".//tbody//tr")

        data = []
        current_team = None

        for row in rows:
            cells = row.xpath(".//td")

            # Team header row: has class 'extrarow' or 'bg_blau' and team links
            first_cell = cells[0] if cells else None
            if first_cell is not None:
                cell_class = first_cell.get('class', '')
                if 'extrarow' in cell_class or 'bg_blau' in cell_class:
                    # Get team from title attribute of link
                    team_links = row.xpath(".//a[contains(@href, '/startseite/verein/')]")
                    if team_links:
                        current_team = team_links[0].get('title', '').strip()
                        if not current_team:
                            current_team = team_links[0].text_content().strip()
                    continue

            # Skip sub-rows (1-2 cells without extrarow class) - positions etc
            if len(cells) <= 2:
                continue

            # Player row: 8 cells, has 'odd' or 'even' class
            row_class = row.get('class', '')
            if 'odd' in row_class or 'even' in row_class:
                player_link = row.xpath(".//a[contains(@href, '/spieler/')]")
                if player_link:
                    player = player_link[0].text_content().strip()

                    # Get numeric values from cells with class 'zentriert'
                    num_cells = row.xpath(".//td[contains(@class, 'zentriert')]")
                    nums = [nc.text_content().strip() for nc in num_cells]
                    nums = [n for n in nums if n]  # Remove empty

                    if len(nums) >= 3:
                        penalties = self._parse_int(nums[0])
                        scored = self._parse_int(nums[1])
                        missed = self._parse_int(nums[2])
                        rate = round(scored / penalties * 100, 1) if penalties and scored is not None else None

                        data.append({
                            'season': f"{season}-{str(season+1)[-2:]}",
                            'player': player,
                            'team': current_team,
                            'penalties': penalties,
                            'scored': scored,
                            'missed': missed,
                            'conversion_rate': rate,
                        })

        return pd.DataFrame(data)

    def get_all_penalties_detail(self, season: int) -> pd.DataFrame:
        """Get detailed info about MISSED penalties (only these have minute/score data).

        Note: Transfermarkt only provides detailed info (minute, score at penalty)
        for missed penalties. Scored penalties don't have this detail available.

        Args:
            season: Year of season start (e.g., 2023 for 2023-24)

        Returns:
            DataFrame with missed penalty details: player, keeper, minute, score, etc.
        """
        # Only missed penalties have detailed info (minute, score)
        url_missed = f"{TRANSFERMARKT_URL}/laliga/elfmeterstatistik/wettbewerb/{LALIGA_ID}/saison_id/{season}/plus/1"
        filepath_missed = self.data_dir / "missed_detail" / f"{season}.html"
        filepath_missed.parent.mkdir(parents=True, exist_ok=True)

        try:
            reader = self.get(url_missed, filepath_missed, max_age=30)
            tree = html.parse(reader)
            data = self._parse_penalty_detail_table(tree, season, scored=False)
            return pd.DataFrame(data)
        except Exception as e:
            logger.warning(f"Error getting missed penalties for {season}: {e}")
            return pd.DataFrame()

    def _parse_penalty_detail_table(self, tree, season: int, scored: bool) -> List[Dict]:
        """Parse penalty detail table.

        Structure for missed (13 cells):
        [0]: Matchday, [4]: Player name, [7]: Keeper, [8]: Score at penalty, [9]: Minute, [11]: Final result

        Structure for scored (11 cells):
        [0]: Matchday, [4]: Player name, [7]: Keeper, [9]: Final result (no minute)
        """
        tables = tree.xpath("//table[.//th[contains(text(), 'Matchday')]]")

        data = []
        for table in tables:
            rows = table.xpath(".//tbody//tr")

            for row in rows:
                cells = row.xpath(".//td")
                if len(cells) < 10:
                    continue

                # Matchday (cell 0)
                matchday = self._parse_int(cells[0].text_content())

                # Player (cell 4 has hauptlink class)
                player_cell = row.xpath(".//td[@class='hauptlink']")
                player = player_cell[0].text_content().strip() if player_cell else None

                # Keeper (cell 7)
                keeper = cells[7].text_content().strip() if len(cells) > 7 else None

                # Teams from links with title attribute
                team_links = row.xpath(".//a[contains(@href, '/verein/')]/@title")
                player_team = team_links[0] if len(team_links) > 0 else None
                keeper_team = team_links[1] if len(team_links) > 1 else None

                # For missed penalties (13 cells): minute is in cell 9, scores in cells 8 and 11
                # For scored penalties (11 cells): no minute, result in cell 9
                minute = None
                score_at_penalty = None
                final_result = None

                if len(cells) >= 13:  # Missed penalties with minute
                    minute_text = cells[9].text_content().strip()
                    minute_match = re.search(r"(\d+)", minute_text)
                    minute = int(minute_match.group(1)) if minute_match else None
                    score_at_penalty = cells[8].text_content().strip()
                    final_result = cells[11].text_content().strip()
                elif len(cells) >= 10:  # Scored penalties without minute
                    final_result = cells[9].text_content().strip()

                if player and len(player) > 1:
                    data.append({
                        'season': f"{season}-{str(season+1)[-2:]}",
                        'matchday': matchday,
                        'player': player,
                        'player_team': player_team,
                        'keeper': keeper,
                        'keeper_team': keeper_team,
                        'minute': minute,
                        'score_at_penalty': score_at_penalty,
                        'final_result': final_result,
                        'scored': scored,
                    })

        return data

    def extract_all_seasons(self, start_year: int = 2004, end_year: int = 2025) -> Dict[str, pd.DataFrame]:
        """Extract all penalty data for multiple seasons.

        Args:
            start_year: First season start year (e.g., 2004 for 2004-05)
            end_year: Last season start year (e.g., 2025 for 2025-26)

        Returns:
            Dictionary with DataFrames:
            - 'received': team penalties received
            - 'conceded': team penalties conceded
            - 'scorers': player penalty scorers
            - 'detail': all penalties with minute/score
        """
        all_received = []
        all_conceded = []
        all_scorers = []
        all_detail = []

        for year in range(start_year, end_year + 1):
            logger.info(f"Extracting season {year}-{str(year+1)[-2:]}")

            try:
                received = self.get_team_penalties_received(year)
                if not received.empty:
                    all_received.append(received)
            except Exception as e:
                logger.warning(f"Error getting received for {year}: {e}")

            try:
                conceded = self.get_team_penalties_conceded(year)
                if not conceded.empty:
                    all_conceded.append(conceded)
            except Exception as e:
                logger.warning(f"Error getting conceded for {year}: {e}")

            try:
                scorers = self.get_penalty_scorers(year)
                if not scorers.empty:
                    all_scorers.append(scorers)
            except Exception as e:
                logger.warning(f"Error getting scorers for {year}: {e}")

            try:
                detail = self.get_all_penalties_detail(year)
                if not detail.empty:
                    all_detail.append(detail)
            except Exception as e:
                logger.warning(f"Error getting detail for {year}: {e}")

        return {
            'received': pd.concat(all_received, ignore_index=True) if all_received else pd.DataFrame(),
            'conceded': pd.concat(all_conceded, ignore_index=True) if all_conceded else pd.DataFrame(),
            'scorers': pd.concat(all_scorers, ignore_index=True) if all_scorers else pd.DataFrame(),
            'detail': pd.concat(all_detail, ignore_index=True) if all_detail else pd.DataFrame(),
        }

    @staticmethod
    def _parse_int(text: str) -> Optional[int]:
        """Parse integer from text."""
        try:
            clean = re.sub(r'[^\d]', '', str(text))
            return int(clean) if clean else None
        except (ValueError, TypeError, AttributeError):
            return None

    @staticmethod
    def _parse_pct(text: str) -> Optional[float]:
        """Parse percentage from text."""
        try:
            clean = str(text).replace('%', '').replace(',', '.').strip()
            return float(clean) if clean else None
        except (ValueError, TypeError, AttributeError):
            return None
