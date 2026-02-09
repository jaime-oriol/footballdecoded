"""FotMob data wrapper: season-level player (35 stats) and team (27 stats) metrics.

All metrics are fotmob_ prefixed. Data fetched fresh from FotMob API (no pickle cache).
Supports Big 5 leagues, UCL, MLS, and 7 extra leagues.
"""

import os
import sys
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional, Union

import pandas as pd

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    def tqdm(iterable, **kwargs):
        return iterable

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrappers import FotMob

warnings.filterwarnings('ignore', category=FutureWarning)

def _validate_inputs(entity_name: str, entity_type: str, league: str, season: str) -> bool:
    """Validate entity_name, entity_type, league, and season format (YY-YY, consecutive)."""
    if not entity_name or not isinstance(entity_name, str) or entity_name.strip() == "":
        raise ValueError("entity_name must be a non-empty string")

    if entity_type not in ('player', 'team'):
        raise ValueError(f"entity_type must be 'player' or 'team', got '{entity_type}'")

    if not league or not isinstance(league, str):
        raise ValueError("league must be a non-empty string")

    if not season or not isinstance(season, str):
        raise ValueError("season must be a string")

    season_parts = season.split('-')
    if len(season_parts) != 2:
        raise ValueError(f"season must be in YY-YY format, got '{season}'")

    try:
        year1, year2 = int(season_parts[0]), int(season_parts[1])
        if not (0 <= year1 <= 99 and 0 <= year2 <= 99):
            raise ValueError(f"season years must be 00-99, got '{season}'")
        if year2 != (year1 + 1) % 100:
            raise ValueError(f"season must be consecutive years, got '{season}'")
    except ValueError as e:
        if "invalid literal" in str(e):
            raise ValueError(f"season must contain valid numbers, got '{season}'")
        raise

    return True


def _get_league_data(league: str, season: str) -> dict:
    """Fetch all player and team stats for a league/season from the FotMob scraper."""
    fm = FotMob(leagues=[league], seasons=[season])
    data = fm.read_league_stats()
    return {"players": data["players"], "teams": data["teams"]}


def _find_entity(df: pd.DataFrame, entity_name: str) -> Optional[pd.Series]:
    """Find entity row by name. Tries exact match first, then partial via name variations."""
    if df is None or df.empty:
        return None

    names = df.index.get_level_values("name")

    mask = names.str.lower() == entity_name.lower()
    if mask.any():
        return df[mask].iloc[0]

    # Fall back to partial matching with accent-stripped and split-name variations
    variations = _generate_name_variations(entity_name)
    for var in variations:
        mask = names.str.contains(var, case=False, na=False, regex=False)
        if mask.any():
            return df[mask].iloc[0]

    return None


def _generate_name_variations(name: str) -> List[str]:
    """Generate search variations: original, accent-stripped, individual parts, first+last."""
    variations = [name]

    # Strip common diacritics for matching against ASCII-normalized sources
    clean = (name.replace('é', 'e').replace('ñ', 'n').replace('í', 'i')
             .replace('ó', 'o').replace('á', 'a').replace('ú', 'u')
             .replace('ç', 'c').replace('ü', 'u').replace('ø', 'o'))
    if clean != name:
        variations.append(clean)

    if ' ' in name:
        parts = name.split()
        variations.extend(parts)
        if len(parts) >= 2:
            variations.append(f"{parts[0]} {parts[-1]}")

    # Deduplicate while preserving order
    return list(dict.fromkeys(variations))


def extract_data(
    entity_name: str,
    entity_type: str,
    league: str,
    season: str,
) -> Optional[Dict]:
    """Extract all FotMob metrics for a single player or team. Returns dict or None."""
    try:
        _validate_inputs(entity_name, entity_type, league, season)
    except ValueError as e:
        print(f"FotMob input validation failed: {e}")
        return None

    try:
        league_data = _get_league_data(league, season)

        if entity_type == 'player':
            df = league_data.get("players")
        else:
            df = league_data.get("teams")

        if df is None or df.empty:
            return None

        row = _find_entity(df, entity_name)
        if row is None:
            return None

        name_key = 'player_name' if entity_type == 'player' else 'team_name'
        official_key = 'official_player_name' if entity_type == 'player' else 'official_team_name'
        result = {
            name_key: entity_name,
            "league": league,
            "season": season,
            official_key: row.name if isinstance(row.name, str) else entity_name,
        }

        for col in row.index:
            val = row[col]
            if pd.notna(val):
                # Convert numpy scalars to native Python types for JSON compatibility
                result[col] = val if not hasattr(val, 'item') else val.item()
            else:
                result[col] = None

        return result

    except Exception as e:
        print(f"Error extracting FotMob data for {entity_name}: {e}")
        return None


def extract_multiple(
    entities: List[str],
    entity_type: str,
    league: str,
    season: str,
    max_workers: int = 3,
    show_progress: bool = True,
) -> pd.DataFrame:
    """Extract FotMob metrics for multiple entities in parallel. Returns DataFrame."""
    if not entities:
        return pd.DataFrame()

    # Pre-fetch once so all threads hit the scraper's file cache instead of the API
    _get_league_data(league, season)

    def extract_single(name: str) -> Optional[Dict]:
        try:
            return extract_data(name, entity_type, league, season)
        except Exception as e:
            if show_progress:
                print(f"Error extracting {name}: {e}")
            return None

    all_data = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_entity = {
            executor.submit(extract_single, name): name for name in entities
        }

        if show_progress and TQDM_AVAILABLE:
            futures = tqdm(as_completed(future_to_entity), total=len(entities),
                          desc=f"Extracting FotMob {entity_type}s")
        else:
            futures = as_completed(future_to_entity)
            if show_progress:
                print(f"Processing {len(entities)} FotMob {entity_type}s...")

        for future in futures:
            try:
                data = future.result()
                if data:
                    all_data.append(data)
            except Exception:
                pass

    if show_progress:
        print(f"Successfully extracted {len(all_data)}/{len(entities)} FotMob {entity_type}s")

    return pd.DataFrame(all_data) if all_data else pd.DataFrame()


def extract_league_players(league: str, season: str) -> pd.DataFrame:
    """Return DataFrame with all player stats for a league/season."""
    league_data = _get_league_data(league, season)
    df = league_data.get("players")
    if df is None or df.empty:
        return pd.DataFrame()
    return df.reset_index()


def extract_league_teams(league: str, season: str) -> pd.DataFrame:
    """Return DataFrame with all team stats for a league/season."""
    league_data = _get_league_data(league, season)
    df = league_data.get("teams")
    if df is None or df.empty:
        return pd.DataFrame()
    return df.reset_index()


def export_to_csv(data: Union[Dict, pd.DataFrame], filename: str, include_timestamp: bool = True) -> str:
    """Export dict or DataFrame to CSV. Returns the output filename."""
    if isinstance(data, dict):
        df = pd.DataFrame([data])
    else:
        df = data

    if include_timestamp:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"{filename}_{ts}.csv"
    else:
        full_filename = f"{filename}.csv"

    df.to_csv(full_filename, index=False, encoding='utf-8')
    return full_filename


def clear_cache():
    """Delete all cached FotMob JSON files from the scraper's data directory."""
    from scrappers._config import DATA_DIR
    fotmob_dir = DATA_DIR / "FotMob"
    try:
        if fotmob_dir.exists():
            for f in fotmob_dir.glob("*.json"):
                f.unlink()
            print("FotMob scraper cache cleared successfully")
    except Exception as e:
        print(f"Error clearing cache: {e}")


def get_player(player_name: str, league: str, season: str) -> Optional[Dict]:
    """Get all FotMob metrics for a single player. Returns dict or None."""
    return extract_data(player_name, 'player', league, season)


def get_team(team_name: str, league: str, season: str) -> Optional[Dict]:
    """Get all FotMob metrics for a single team. Returns dict or None."""
    return extract_data(team_name, 'team', league, season)


def get_players(players: List[str], league: str, season: str, max_workers: int = 3,
                show_progress: bool = True) -> pd.DataFrame:
    """Get FotMob metrics for multiple players in parallel. Returns DataFrame."""
    return extract_multiple(players, 'player', league, season, max_workers=max_workers,
                            show_progress=show_progress)


def get_teams(teams: List[str], league: str, season: str, max_workers: int = 3,
              show_progress: bool = True) -> pd.DataFrame:
    """Get FotMob metrics for multiple teams in parallel. Returns DataFrame."""
    return extract_multiple(teams, 'team', league, season, max_workers=max_workers,
                            show_progress=show_progress)


def get_league_players(league: str, season: str) -> pd.DataFrame:
    """Get all player stats for a league/season. Returns DataFrame."""
    return extract_league_players(league, season)


def get_league_teams(league: str, season: str) -> pd.DataFrame:
    """Get all team stats for a league/season. Returns DataFrame."""
    return extract_league_teams(league, season)
