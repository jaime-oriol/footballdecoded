"""Scraper for Transfermarkt penalty statistics.

Extracts complete penalty data from LaLiga (2004-2026):
- Team penalties received (a favor)
- Team penalties conceded (en contra)
- Penalty scorers (goleadores)
- ALL penalties detail (scored + missed with minute, score, home/away)
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
                # Cell 3 = "Successful" = goles encajados (éxito del LANZADOR)
                goals_against = self._parse_int(cells[3].text_content())
                # Cell 4 = "Conceded penalties" = total penaltis en contra
                conceded = self._parse_int(cells[4].text_content())
                # Cell 5 = "Missed" = fallados por el rival
                missed = self._parse_int(cells[5].text_content())
                # Saved = total - goles - fallados
                saved = conceded - goals_against - missed if conceded and goals_against is not None else None

                data.append({
                    'season': f"{season}-{str(season+1)[-2:]}",
                    'team': team,
                    'penalties_conceded': conceded,
                    'goals_against': goals_against,
                    'saved': saved,
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
        """Get detailed info about ALL penalties (scored and missed) with pagination.

        Extracts complete penalty data including minute, score at penalty,
        player, home/away teams, and final result for both scored and missed penalties.
        Handles pagination to get all penalties, not just first page.

        Note: Both tables (missed/scored) share the same pagination, but one may
        run out of data before the other. We track each table independently to avoid
        duplicates when one exhausts before the other.

        Args:
            season: Year of season start (e.g., 2023 for 2023-24)

        Returns:
            DataFrame with all penalty details: player, minute, score, home/away, is_home, scored/missed.
        """
        all_data = []
        page = 1
        has_more_missed = True
        has_more_scored = True
        seen_penalties = set()  # Track unique penalties to avoid duplicates

        while has_more_missed or has_more_scored:
            # Build URL with pagination
            if page == 1:
                url = f"{TRANSFERMARKT_URL}/laliga/elfmeterstatistik/wettbewerb/{LALIGA_ID}/saison_id/{season}/plus/1"
            else:
                url = f"{TRANSFERMARKT_URL}/laliga/elfmeterstatistik/wettbewerb/{LALIGA_ID}/saison_id/{season}/plus/1/page/{page}"

            filepath = self.data_dir / "detail" / f"{season}_page{page}.html"
            filepath.parent.mkdir(parents=True, exist_ok=True)

            try:
                reader = self.get(url, filepath, max_age=30)
                tree = html.parse(reader)

                # Parse both tables (only if they still have data)
                page_data_missed = []
                page_data_scored = []

                if has_more_missed:
                    page_data_missed = self._parse_penalty_detail_table(tree, season, scored=False)

                    # Check for duplicates (when table exhausts, Transfermarkt shows last page again)
                    new_missed = []
                    for penalty in page_data_missed:
                        pen_id = (penalty['player'], penalty['home_team'], penalty['minute'], penalty['score_at_penalty'])
                        if pen_id not in seen_penalties:
                            seen_penalties.add(pen_id)
                            new_missed.append(penalty)
                        else:
                            logger.debug(f"DUPLICATE missed: {penalty['player']}, min {penalty['minute']}, {penalty['home_team']}")

                    if not new_missed:
                        has_more_missed = False
                        page_data_missed = []  # Explicitly set to empty
                    else:
                        page_data_missed = new_missed

                if has_more_scored:
                    page_data_scored = self._parse_penalty_detail_table(tree, season, scored=True)

                    # Check for duplicates
                    new_scored = []
                    for penalty in page_data_scored:
                        pen_id = (penalty['player'], penalty['home_team'], penalty['minute'], penalty['score_at_penalty'])
                        if pen_id not in seen_penalties:
                            seen_penalties.add(pen_id)
                            new_scored.append(penalty)
                        else:
                            logger.debug(f"DUPLICATE scored: {penalty['player']}, min {penalty['minute']}, {penalty['home_team']}")

                    if not new_scored:
                        has_more_scored = False
                        page_data_scored = []  # Explicitly set to empty
                    else:
                        page_data_scored = new_scored

                # Combine data from both tables
                page_data = page_data_missed + page_data_scored

                if page_data:
                    all_data.extend(page_data)
                    logger.info(f"Season {season} page {page}: {len(page_data_missed)} missed + {len(page_data_scored)} scored = {len(page_data)} total")

                page += 1

                # Safety limit to avoid infinite loops
                if page > 20:
                    logger.warning(f"Reached page limit (20) for season {season}")
                    break

            except Exception as e:
                logger.warning(f"Error getting page {page} for {season}: {e}")
                break

        logger.info(f"Season {season} TOTAL: {len(all_data)} penalties extracted")
        return pd.DataFrame(all_data)

    def _parse_penalty_detail_table(self, tree, season: int, scored: bool) -> List[Dict]:
        """Parse penalty detail table (scored or missed).

        Args:
            tree: HTML tree
            season: Season year
            scored: True for scored penalties, False for missed

        Returns:
            List of penalty records with all details
        """
        # Tables are in divs with IDs: yw1 (missed), yw2 (scored)
        div_id = 'yw2' if scored else 'yw1'
        tables = tree.xpath(f"//div[@id='{div_id}']//table[@class='items']")

        if not tables:
            logger.warning(f"No {'scored' if scored else 'missed'} penalty table found for {season}")
            return []

        table = tables[0]
        rows = table.xpath(".//tbody//tr")

        data = []
        for row in rows:
            cells = row.xpath(".//td")
            if len(cells) < 13:
                continue

            try:
                # Cell structure (13 cells):
                # 0: Matchday
                # 1: Player team logo (link title)
                # 4: Player name
                # 8: Score at penalty (e.g., "2:1" = home:away)
                # 9: Minute (e.g., "45'")
                # 10: Home team logo (link title) - LOCAL
                # 11: Final result (e.g., "3:1")
                # 12: Away team logo (link title) - VISITANTE

                matchday = self._parse_int(cells[0].text_content())

                # Player
                player = cells[4].text_content().strip()
                if not player or len(player) <= 1:
                    continue

                # Player team (from cell 1 link title)
                player_team_link = cells[1].xpath(".//a/@title")
                player_team = player_team_link[0] if player_team_link else None

                # Score at penalty (format: home:away)
                score_at_penalty = cells[8].text_content().strip()

                # Minute
                minute_text = cells[9].text_content().strip().replace("'", "")
                minute = int(minute_text) if minute_text.isdigit() else None

                # Home team (LOCAL)
                home_team_link = cells[10].xpath(".//a/@title")
                home_team = home_team_link[0] if home_team_link else None

                # Final result
                final_result = cells[11].text_content().strip()

                # Away team (VISITANTE)
                away_team_link = cells[12].xpath(".//a/@title")
                away_team = away_team_link[0] if away_team_link else None

                # Determine if player_team is home or away
                is_home = (player_team == home_team) if player_team and home_team else None

                data.append({
                    'season': f"{season}-{str(season+1)[-2:]}",
                    'matchday': matchday,
                    'player': player,
                    'player_team': player_team,
                    'minute': minute,
                    'score_at_penalty': score_at_penalty,
                    'home_team': home_team,
                    'away_team': away_team,
                    'final_result': final_result,
                    'is_home': is_home,
                    'scored': scored,
                })

            except (ValueError, TypeError, AttributeError) as e:
                logger.debug(f"Error parsing penalty row: {e}")
                continue

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
            - 'detail': ALL penalties (scored + missed) with minute, score, home/away, is_home
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
