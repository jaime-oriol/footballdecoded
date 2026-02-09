"""Understat wrapper: advanced metrics (xG Chain, xG Buildup, PPDA, shots).

Big 5 leagues only. Provides player/team extraction, shot events,
match ID lookup, and batch processing with parallel support.

Usage:
    from wrappers import understat_data
    player = understat_data.get_player("Lewandowski", "ESP-La Liga", "24-25")
    team = understat_data.get_team("Barcelona", "ESP-La Liga", "24-25")
    shots = understat_data.get_shots(26982, "ESP-La Liga", "24-25")
"""

import time
import warnings
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    def tqdm(iterable, **kwargs):
        return iterable

from scrappers import Understat
from scrappers._config import LEAGUE_DICT

warnings.filterwarnings('ignore', category=FutureWarning)

def _validate_inputs(entity_name: str, entity_type: str, league: str, season: str) -> bool:
    """Validate entity name, type, league and season format (YY-YY)."""
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


def clear_cache():
    """Delete all cached JSON files from the Understat scraper directory."""
    from pathlib import Path
    from scrappers._config import DATA_DIR
    cache_dir = DATA_DIR / "Understat"
    try:
        if cache_dir.exists():
            count = 0
            for f in cache_dir.glob("*.json"):
                f.unlink()
                count += 1
            print(f"Understat cache cleared ({count} files)")
    except Exception as e:
        print(f"Error clearing cache: {e}")


def extract_data(
    entity_name: str,
    entity_type: str,
    league: str,
    season: str,
    team_name: Optional[str] = None
) -> Optional[Dict]:
    """Extract Understat advanced metrics for a player or team.

    Args:
        entity_name: Player or team name.
        entity_type: 'player' or 'team'.
        league: League code (e.g. 'ESP-La Liga').
        season: Season in YY-YY format (e.g. '24-25').
        team_name: Team name for player disambiguation.

    Returns:
        Dict with understat_ prefixed metrics, or None if not found.
    """
    try:
        _validate_inputs(entity_name, entity_type, league, season)
    except ValueError as e:
        print(f"Understat input validation failed: {e}")
        return None

    try:
        understat = Understat(leagues=[league], seasons=[season])

        if entity_type == 'player':
            stats = understat.read_player_season_stats()
            entity_row = _find_entity(stats, entity_name, 'player', team_name=team_name)

            if entity_row is None:
                return None

            basic_info = {
                'player_name': entity_name,
                'league': league,
                'season': season,
                'team': entity_row.index.get_level_values('team')[0],
                'official_player_name': entity_row.index.get_level_values('player')[0]
            }
            understat_metrics = _extract_player_metrics(entity_row)

        else:
            team_stats = understat.read_team_match_stats()
            team_matches = _find_team_matches(team_stats, entity_name)

            if team_matches is None or team_matches.empty:
                return None

            basic_info = {
                'team_name': entity_name,
                'league': league,
                'season': season,
                'official_team_name': team_matches.iloc[0]['home_team'] if 'home_team' in team_matches.columns else entity_name
            }
            understat_metrics = _calculate_team_metrics(team_matches, entity_name)

        return {**basic_info, **understat_metrics}

    except Exception as e:
        print(f"Error extracting Understat data for {entity_name}: {e}")
        return None


def extract_multiple(
    entities: List[str],
    entity_type: str,
    league: str,
    season: str,
    max_workers: int = 3,
    show_progress: bool = True,
) -> pd.DataFrame:
    """Extract metrics for multiple players/teams in parallel.

    Returns standardized DataFrame with one row per entity.
    """
    if not entities:
        return pd.DataFrame()

    def extract_single(name: str) -> Optional[Dict]:
        try:
            time.sleep(1.0)
            return extract_data(name, entity_type, league, season)
        except Exception as e:
            if show_progress:
                print(f"Error extracting {name}: {e}")
            return None

    all_data = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_entity = {executor.submit(extract_single, e): e for e in entities}

        if show_progress and TQDM_AVAILABLE:
            futures = tqdm(as_completed(future_to_entity), total=len(entities),
                          desc=f"Extracting Understat {entity_type}s")
        else:
            futures = as_completed(future_to_entity)
            if show_progress:
                print(f"Processing {len(entities)} Understat {entity_type}s...")

        for future in futures:
            try:
                result = future.result()
                if result:
                    all_data.append(result)
            except Exception as e:
                if show_progress:
                    print(f"Failed: {e}")

    if show_progress:
        print(f"Extracted {len(all_data)}/{len(entities)} Understat {entity_type}s")

    df = pd.DataFrame(all_data) if all_data else pd.DataFrame()
    return _standardize_dataframe(df, entity_type)


def extract_shot_events(
    match_id: int,
    league: str,
    season: str,
    player_filter: Optional[str] = None,
    team_filter: Optional[str] = None,
    verbose: bool = False
) -> pd.DataFrame:
    """Extract shot events for a match with xG, coordinates, and derived analytics.

    Returns DataFrame with shot details, zone classification, and goal flags.
    """
    try:
        if verbose:
            print(f"   Extracting shot data for match {match_id}...")

        understat = Understat(leagues=[league], seasons=[season])
        shot_events = understat.read_shot_events(match_id=match_id)

        if shot_events is None or shot_events.empty:
            if verbose:
                print(f"   No shot events found for match {match_id}")
            return pd.DataFrame()

        enhanced = _process_shot_events(shot_events)
        filtered = _apply_shot_filters(enhanced, player_filter, team_filter)

        if not filtered.empty:
            filtered['match_id'] = match_id
            filtered['data_source'] = 'understat'

        if verbose:
            print(f"   Found {len(filtered)} shot events")

        return filtered

    except Exception as e:
        if verbose:
            print(f"   Error extracting shot events: {e}")
        return pd.DataFrame()


def _find_entity(stats: pd.DataFrame, entity_name: str, entity_type: str,
                 team_name: Optional[str] = None) -> Optional[pd.DataFrame]:
    """Find a player/team row by name with fuzzy matching and team disambiguation."""
    if stats is None or stats.empty:
        return None

    variations = _generate_name_variations(entity_name)
    index_level = entity_type
    all_matches = []

    for variation in variations:
        matches = stats[stats.index.get_level_values(index_level).str.lower() == variation.lower()]
        if not matches.empty:
            all_matches.append(matches)

    # Fall back to partial (substring) matching
    if not all_matches:
        for variation in variations:
            matches = stats[stats.index.get_level_values(index_level).str.contains(
                variation, case=False, na=False, regex=False)]
            if not matches.empty:
                all_matches.append(matches)

    if not all_matches:
        return None

    combined = pd.concat(all_matches).drop_duplicates()

    if len(combined) == 1:
        return combined

    # Multiple matches found: narrow down by team name
    if len(combined) > 1 and team_name:
        for team_var in _generate_name_variations(team_name):
            team_matches = combined[
                combined.index.get_level_values('team').str.contains(
                    team_var, case=False, na=False, regex=False
                )
            ]
            if not team_matches.empty:
                return team_matches.iloc[:1]

    return combined.iloc[:1]


def _find_team_matches(stats: pd.DataFrame, team_name: str) -> Optional[pd.DataFrame]:
    """Find all matches involving a team (home or away) by fuzzy name matching."""
    if stats is None or stats.empty:
        return None

    for variation in _generate_name_variations(team_name):
        home = stats[stats['home_team'].str.contains(variation, case=False, na=False, regex=False)]
        away = stats[stats['away_team'].str.contains(variation, case=False, na=False, regex=False)]
        if not home.empty or not away.empty:
            return pd.concat([home, away]).drop_duplicates()

    return None


def _generate_name_variations(name: str) -> List[str]:
    """Generate name variations: diacritics removal, split parts, known aliases."""
    variations = [name]

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

    mappings = {
        "Kylian Mbappé": ["Kylian Mbappe", "K. Mbappe", "Mbappe"],
        "Erling Haaland": ["E. Haaland", "Haaland"],
        "Vinicius Jr": ["Vinicius Junior", "Vinicius"],
        'Manchester United': ['Manchester Utd', 'Man United'],
        'Manchester City': ['Man City'],
        'Tottenham': ['Tottenham Hotspur'],
        'Real Madrid': ['Madrid'],
        'Barcelona': ['Barça', 'FC Barcelona']
    }

    if name in mappings:
        variations.extend(mappings[name])

    return list(dict.fromkeys(variations))


def _extract_player_metrics(player_row: pd.DataFrame) -> Dict:
    """Extract raw metrics, compute derived stats (npxG+xA), and per-90 rates."""
    data = {}
    metrics_map = {
        'player_id': 'understat_player_id',
        'team_id': 'understat_team_id',
        'position': 'understat_position',
        'matches': 'understat_matches',
        'minutes': 'understat_minutes',
        'goals': 'understat_goals',
        'xg': 'understat_xg',
        'np_goals': 'understat_np_goals',
        'np_xg': 'understat_np_xg',
        'assists': 'understat_assists',
        'xa': 'understat_xa',
        'shots': 'understat_shots',
        'key_passes': 'understat_key_passes',
        'yellow_cards': 'understat_yellow_cards',
        'red_cards': 'understat_red_cards',
        'xg_chain': 'understat_xg_chain',
        'xg_buildup': 'understat_xg_buildup',
    }

    for col, key in metrics_map.items():
        if col in player_row.columns:
            value = player_row.iloc[0][col]
            data[key] = value if pd.notna(value) else None

    np_xg = data.get('understat_np_xg') or 0
    xa = data.get('understat_xa') or 0
    if np_xg or xa:
        data['understat_npxg_plus_xa'] = np_xg + xa
    xg_chain = data.get('understat_xg_chain') or 0
    if xg_chain and np_xg > 0:
        data['understat_buildup_involvement_pct'] = (xg_chain / np_xg) * 100

    minutes = data.get('understat_minutes') or 0
    if minutes > 0:
        p90 = 90 / minutes
        data['understat_xg_per90'] = (data.get('understat_xg') or 0) * p90
        data['understat_xa_per90'] = xa * p90
        data['understat_npxg_per90'] = np_xg * p90
        data['understat_npxg_plus_xa_per90'] = (np_xg + xa) * p90
        data['understat_xg_chain_per90'] = xg_chain * p90
        data['understat_xg_buildup_per90'] = (data.get('understat_xg_buildup') or 0) * p90
        data['understat_key_passes_per90'] = (data.get('understat_key_passes') or 0) * p90
        data['understat_shots_per90'] = (data.get('understat_shots') or 0) * p90

    return data


def _calculate_team_metrics(team_matches: pd.DataFrame, team_name: str) -> Dict:
    """Aggregate team metrics across all matches, resolving home/away sides.

    Each match stat is extracted from the correct column (home_ or away_)
    depending on which side the team played. Opponent metrics use the opposite side.
    """
    metrics = {}
    total = len(team_matches)
    metrics['understat_matches_analyzed'] = total
    if total == 0:
        return metrics

    stat_keys = {
        'ppda': ('avg', 'std'),
        'deep_completions': ('total', 'avg'),
        'expected_points': ('total', 'avg'),
        'np_xg': ('total', 'avg'),
        'xg': ('total', 'avg'),
        'goals': ('total', 'avg'),
        'points': ('total', 'avg'),
        'np_xg_difference': ('total', 'avg'),
    }

    for stat, agg_types in stat_keys.items():
        vals = _extract_team_side_values(team_matches, team_name, stat)
        if not vals:
            continue
        for agg in agg_types:
            if agg == 'total':
                metrics[f'understat_{stat}_total'] = np.sum(vals)
            elif agg == 'avg':
                metrics[f'understat_{stat}_avg'] = np.mean(vals)
            elif agg == 'std':
                metrics[f'understat_{stat}_std'] = np.std(vals)

    opp_xg = _extract_team_side_values(team_matches, team_name, 'xg', opponent=True)
    opp_npxg = _extract_team_side_values(team_matches, team_name, 'np_xg', opponent=True)
    opp_goals = _extract_team_side_values(team_matches, team_name, 'goals', opponent=True)
    opp_ppda = _extract_team_side_values(team_matches, team_name, 'ppda', opponent=True)
    if opp_xg:
        metrics['understat_xg_against_total'] = np.sum(opp_xg)
        metrics['understat_xg_against_avg'] = np.mean(opp_xg)
    if opp_npxg:
        metrics['understat_np_xg_against_total'] = np.sum(opp_npxg)
        metrics['understat_np_xg_against_avg'] = np.mean(opp_npxg)
    if opp_goals:
        metrics['understat_goals_against_total'] = np.sum(opp_goals)
        metrics['understat_goals_against_avg'] = np.mean(opp_goals)
    if opp_ppda:
        metrics['understat_ppda_against_avg'] = np.mean(opp_ppda)

    if 'understat_expected_points_total' in metrics:
        metrics['understat_points_efficiency'] = metrics['understat_expected_points_total'] / total
    if 'understat_xg_total' in metrics and 'understat_xg_against_total' in metrics:
        metrics['understat_xg_difference_total'] = metrics['understat_xg_total'] - metrics['understat_xg_against_total']

    return metrics


def _extract_team_side_values(
    matches: pd.DataFrame, team_name: str, stat_suffix: str,
    opponent: bool = False
) -> List[float]:
    """Extract per-match values from the correct home/away column.

    If opponent=True, returns the opposite side's values instead.
    """
    home_col = f'home_{stat_suffix}'
    away_col = f'away_{stat_suffix}'
    if home_col not in matches.columns or away_col not in matches.columns:
        return []

    values = []
    team_lower = team_name.lower()
    for _, row in matches.iterrows():
        home_team = str(row.get('home_team', '')).lower()
        away_team = str(row.get('away_team', '')).lower()
        if team_lower in home_team or home_team in team_lower:
            val = row[away_col if opponent else home_col]
        elif team_lower in away_team or away_team in team_lower:
            val = row[home_col if opponent else away_col]
        else:
            continue
        if pd.notna(val):
            values.append(float(val))
    return values


def _process_shot_events(shot_events: pd.DataFrame) -> pd.DataFrame:
    """Rename columns, add goal/target flags, distance, and zone classification."""
    if shot_events.empty:
        return shot_events

    df = shot_events.copy()
    rename_map = {
        'xg': 'shot_xg', 'location_x': 'shot_location_x',
        'location_y': 'shot_location_y', 'body_part': 'shot_body_part',
        'situation': 'shot_situation', 'result': 'shot_result',
        'minute': 'shot_minute', 'player': 'shot_player',
        'team': 'shot_team', 'assist_player': 'assist_player_name'
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    if 'shot_result' in df.columns:
        df['is_goal'] = (df['shot_result'] == 'Goal').astype(int)
        df['is_on_target'] = df['shot_result'].isin(['Goal', 'Saved Shot']).astype(int)
        df['is_blocked'] = (df['shot_result'] == 'Blocked Shot').astype(int)

    if 'shot_location_x' in df.columns and 'shot_location_y' in df.columns:
        x, y = df['shot_location_x'].astype(float), df['shot_location_y'].astype(float)
        # Understat coords are 0-1 normalized; goal center is at (1.0, 0.5)
        df['shot_distance_to_goal'] = np.sqrt((x - 1.0)**2 + (y - 0.5)**2) * 100
        df['shot_zone'] = pd.cut(
            x * 100, bins=[0, 67, 83, 88, 100],
            labels=['Long_Range', 'Penalty_Area_Edge', 'Penalty_Box', 'Six_Yard_Box']
        )

    if 'assist_player_name' in df.columns:
        df['is_assisted'] = (~df['assist_player_name'].isna()).astype(int)

    return df


def _apply_shot_filters(df: pd.DataFrame, player_filter: Optional[str],
                        team_filter: Optional[str]) -> pd.DataFrame:
    """Filter shot events by player and/or team name (fuzzy matching)."""
    result = df.copy()

    if player_filter and 'shot_player' in result.columns:
        mask = pd.Series(False, index=result.index)
        for var in _generate_name_variations(player_filter):
            mask |= result['shot_player'].str.contains(var, case=False, na=False, regex=False)
        result = result[mask]

    if team_filter and 'shot_team' in result.columns:
        mask = pd.Series(False, index=result.index)
        for var in _generate_name_variations(team_filter):
            mask |= result['shot_team'].str.contains(var, case=False, na=False, regex=False)
        result = result[mask]

    return result


def _standardize_dataframe(df: pd.DataFrame, entity_type: str) -> pd.DataFrame:
    """Reorder columns with key identifiers and metrics first."""
    if df.empty:
        return df

    if entity_type == 'player':
        priority = [
            'player_name', 'team', 'league', 'season', 'official_player_name',
            'understat_position', 'understat_matches', 'understat_minutes',
            'understat_goals', 'understat_xg', 'understat_np_goals', 'understat_np_xg',
            'understat_assists', 'understat_xa', 'understat_npxg_plus_xa',
            'understat_shots', 'understat_key_passes',
            'understat_xg_chain', 'understat_xg_buildup',
            'understat_xg_per90', 'understat_npxg_per90', 'understat_xa_per90',
            'understat_npxg_plus_xa_per90', 'understat_xg_chain_per90',
            'understat_xg_buildup_per90', 'understat_key_passes_per90', 'understat_shots_per90',
        ]
    else:
        priority = [
            'team_name', 'league', 'season', 'official_team_name',
            'understat_matches_analyzed',
            'understat_xg_total', 'understat_xg_against_total', 'understat_xg_difference_total',
            'understat_np_xg_total', 'understat_np_xg_against_total',
            'understat_goals_total', 'understat_goals_against_total',
            'understat_expected_points_total', 'understat_points_total',
            'understat_ppda_avg', 'understat_ppda_against_avg',
            'understat_deep_completions_total',
        ]

    available = [c for c in priority if c in df.columns]
    remaining = sorted([c for c in df.columns if c not in priority])
    return df[available + remaining]


def export_to_csv(data: Union[Dict, pd.DataFrame], filename: str, include_timestamp: bool = True) -> str:
    """Export dict or DataFrame to CSV. Returns the output file path."""
    df = pd.DataFrame([data]) if isinstance(data, dict) else data
    if include_timestamp:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        full = f"{filename}_{ts}.csv"
    else:
        full = f"{filename}.csv"
    df.to_csv(full, index=False, encoding='utf-8')
    return full


def get_match_ids(league: str, season: str, team_filter: Optional[str] = None) -> pd.DataFrame:
    """Retrieve all match IDs for a league/season from Understat.

    Returns DataFrame with: match_id, home_team, away_team, date, league, season.
    Optional team_filter narrows results to matches involving that team.
    """
    try:
        scraper = Understat(leagues=[league], seasons=[season])
        schedule = scraper.read_schedule()

        if schedule.empty:
            print(f"No matches found for {league} {season}")
            return pd.DataFrame()

        result = schedule.reset_index()[['game_id', 'home_team', 'away_team', 'date']].copy()
        result = result.rename(columns={'game_id': 'match_id'})
        result['league'] = league
        result['season'] = season

        if team_filter and not result.empty:
            mask = pd.Series(False, index=result.index)
            for var in _generate_name_variations(team_filter):
                mask |= result['home_team'].str.contains(var, case=False, na=False, regex=False)
                mask |= result['away_team'].str.contains(var, case=False, na=False, regex=False)
            result = result[mask]

        print(f"Found {len(result)} matches for {league} {season}")
        return result.sort_values('date').reset_index(drop=True)

    except Exception as e:
        raise ConnectionError(f"Error retrieving match IDs from Understat: {e}")


def search_player_id(player_name: str, league: str, season: str) -> Optional[Dict[str, Any]]:
    """Look up a player's official name and team in Understat."""
    try:
        data = extract_data(player_name, 'player', league, season)
        if data:
            return {
                'player_name': data.get('official_player_name', player_name),
                'team': data.get('team'),
                'league': league,
                'season': season,
                'found': True,
            }
        return None
    except Exception as e:
        print(f"Error searching for player {player_name}: {e}")
        return None


def search_team_id(team_name: str, league: str, season: str) -> Optional[Dict[str, Any]]:
    """Look up a team's official name in Understat."""
    try:
        data = extract_data(team_name, 'team', league, season)
        if data:
            return {
                'team_name': data.get('official_team_name', team_name),
                'league': league,
                'season': season,
                'found': True,
            }
        return None
    except Exception as e:
        print(f"Error searching for team {team_name}: {e}")
        return None


def get_player(player_name: str, league: str, season: str,
               team_name: Optional[str] = None) -> Optional[Dict]:
    """Get advanced metrics for a single player."""
    return extract_data(player_name, 'player', league, season, team_name=team_name)

def get_team(team_name: str, league: str, season: str) -> Optional[Dict]:
    """Get advanced metrics for a single team."""
    return extract_data(team_name, 'team', league, season)

def get_players(players: List[str], league: str, season: str,
                max_workers: int = 3, show_progress: bool = True) -> pd.DataFrame:
    """Get advanced metrics for multiple players in parallel."""
    return extract_multiple(players, 'player', league, season,
                            max_workers=max_workers, show_progress=show_progress)

def get_teams(teams: List[str], league: str, season: str,
              max_workers: int = 3, show_progress: bool = True) -> pd.DataFrame:
    """Get advanced metrics for multiple teams in parallel."""
    return extract_multiple(teams, 'team', league, season,
                            max_workers=max_workers, show_progress=show_progress)

def get_shots(match_id: int, league: str, season: str,
              player_filter: Optional[str] = None) -> pd.DataFrame:
    """Get shot events for a match, optionally filtered by player."""
    return extract_shot_events(match_id, league, season, player_filter=player_filter)


def get_team_advanced(team_name: str, league: str, season: str) -> Optional[Dict]:
    """Get advanced team stats (~200 keys across 7 categories).

    Categories: situation, formation, gameState, timing, shotZone,
    attackSpeed, result. All keys prefixed with understat_adv_.
    """
    try:
        understat = Understat(leagues=[league], seasons=[season])
        adv_df = understat.read_team_advanced_stats()

        if adv_df is None or adv_df.empty:
            return None

        # Index is (league, season, team); match on idx[2]
        team_lower = team_name.lower()
        for idx in adv_df.index:
            if team_lower in idx[2].lower() or idx[2].lower() in team_lower:
                row = adv_df.loc[idx]
                result = {}
                for col in row.index:
                    val = row[col]
                    if pd.notna(val):
                        # Convert numpy types to native Python for JSON serialization
                        result[f"understat_adv_{col}"] = val if not hasattr(val, 'item') else val.item()
                return result

        return None

    except Exception as e:
        print(f"Error extracting advanced stats for {team_name}: {e}")
        return None


def get_player_shots(player_name: str, league: str, season: str) -> pd.DataFrame:
    """Get all shot events for a player in a season.

    Resolves the player's Understat ID, fetches career shots,
    and filters to the requested season.
    """
    try:
        understat = Understat(leagues=[league], seasons=[season])

        stats = understat.read_player_season_stats()
        if stats is None or stats.empty:
            return pd.DataFrame()

        entity_row = _find_entity(stats, player_name, 'player')
        if entity_row is None:
            return pd.DataFrame()

        player_id = entity_row.iloc[0]['player_id']
        if pd.isna(player_id):
            return pd.DataFrame()

        result = understat.read_player_career_shots(int(player_id))
        shots_df = result.get("shots", pd.DataFrame())

        if shots_df.empty:
            return shots_df

        # Convert "24-25" -> 2024 to match Understat's season year format
        season_parts = season.split('-')
        season_year = int(f"20{season_parts[0]}")
        shots_df = shots_df[shots_df['season'] == season_year]

        return shots_df.reset_index(drop=True)

    except Exception as e:
        print(f"Error extracting player shots for {player_name}: {e}")
        return pd.DataFrame()
