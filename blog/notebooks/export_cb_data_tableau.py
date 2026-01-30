"""Export CB data from Big 5 + Portugal to Excel for Tableau."""
import pandas as pd
import numpy as np
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from database.connection import get_db_manager

# Config
LEAGUES_DOMESTIC = ['ENG-Premier League', 'ESP-La Liga', 'ITA-Serie A', 'GER-Bundesliga', 'FRA-Ligue 1']
LEAGUES_EXTRAS = ['POR-Primeira Liga']
SEASON = '2425'
OUTPUT_FILE = './cb_data_tableau.xlsx'

# Metrics to exclude from normalization (ratios, percentages, counts)
EXCLUDE_NORMALIZATION = {
    'minutes_played', 'age', 'birth_year', 'games_started', 'minutes_per_game',
    'minutes_per_start', 'games', 'games_subs', 'unused_sub', 'points_per_game',
    'on_goals_for', 'on_goals_against', 'plus_minus', 'plus_minus_per90',
    'plus_minus_wowy', 'on_xg_for', 'on_xg_against', 'xg_plus_minus',
    'xg_plus_minus_per90', 'xg_plus_minus_wowy', 'Touches_Touches',
    'pass_completion_pct', 'shots_on_target_pct', 'Take-Ons_Succ%', 'Take-Ons_Tkld%',
    'Aerial Duels_Won%', 'Challenges_Tkl%', 'Save%', 'Launched_Cmp%', 'Crosses_Stp%'
}

def extract_metrics(df, col_name):
    """Extract numeric metrics from JSONB column."""
    result = pd.DataFrame(index=df.index)
    all_keys = set()
    for _, row in df.iterrows():
        if isinstance(row[col_name], dict):
            all_keys.update(row[col_name].keys())

    for key in all_keys:
        values = []
        for _, row in df.iterrows():
            if isinstance(row[col_name], dict) and key in row[col_name]:
                raw = row[col_name][key]
                if isinstance(raw, (int, float)):
                    values.append(float(raw))
                elif isinstance(raw, str):
                    try:
                        values.append(float(raw))
                    except:
                        values.append(np.nan)
                else:
                    values.append(np.nan)
            else:
                values.append(np.nan)
        if pd.Series(values).notna().sum() >= 5:
            result[key] = values
    return result

def main():
    print("Connecting to database...")
    db = get_db_manager()

    # Query domestic (Big 5)
    league_domestic_str = "', '".join(LEAGUES_DOMESTIC)
    query_domestic = f"""
    SELECT unique_player_id, player_name, team, league, season, position, nationality, age,
           fbref_metrics, understat_metrics, transfermarkt_metrics
    FROM footballdecoded.players_domestic
    WHERE league IN ('{league_domestic_str}') AND season = '{SEASON}'
    """

    # Query extras (Portugal)
    league_extras_str = "', '".join(LEAGUES_EXTRAS)
    query_extras = f"""
    SELECT unique_player_id, player_name, team, league, season, position, nationality, age,
           fbref_metrics, understat_metrics, transfermarkt_metrics
    FROM footballdecoded.players_extras
    WHERE league IN ('{league_extras_str}') AND season = '{SEASON}'
    """

    df_domestic = pd.read_sql(query_domestic, db.engine)
    df_extras = pd.read_sql(query_extras, db.engine)
    db.close()

    df_raw = pd.concat([df_domestic, df_extras], ignore_index=True)
    print(f"Total: {len(df_raw)} players (domestic: {len(df_domestic)}, extras: {len(df_extras)})")

    # Filter CBs only (using transfermarkt position or FBref DF)
    df_cb = df_raw[
        (df_raw['transfermarkt_metrics'].apply(
            lambda x: x.get('transfermarkt_position_specific', '') if isinstance(x, dict) else ''
        ) == 'CB') |
        (df_raw['position'].str.contains('DF', case=False, na=False))
    ].copy()
    print(f"CBs/DFs: {len(df_cb)} players")

    # Extract metrics
    fbref_nums = extract_metrics(df_cb, 'fbref_metrics')
    understat_nums = extract_metrics(df_cb, 'understat_metrics')
    print(f"Metrics: FBref {fbref_nums.shape[1]}, Understat {understat_nums.shape[1]}")

    # Per 90 normalization
    minutes = fbref_nums['minutes_played']
    fbref_per90 = fbref_nums.loc[:, ~fbref_nums.columns.isin(EXCLUDE_NORMALIZATION)]
    fbref_per90 = (fbref_per90.div(minutes, axis=0) * 90).round(3)
    fbref_per90.columns = [f'{col}_per90' for col in fbref_per90.columns]

    understat_per90 = understat_nums.loc[:, ~understat_nums.columns.isin(EXCLUDE_NORMALIZATION)]
    understat_per90 = (understat_per90.div(minutes, axis=0) * 90).round(3)
    understat_per90.columns = [f'{col}_per90' for col in understat_per90.columns]

    # Per 100 touches normalization
    touches = fbref_nums['Touches_Touches']
    fbref_per100 = fbref_nums.loc[:, ~fbref_nums.columns.isin(EXCLUDE_NORMALIZATION)]
    fbref_per100 = (fbref_per100.div(touches, axis=0) * 100).round(3)
    fbref_per100.columns = [f'{col}_per100touches' for col in fbref_per100.columns]

    understat_per100 = understat_nums.loc[:, ~understat_nums.columns.isin(EXCLUDE_NORMALIZATION)]
    understat_per100 = (understat_per100.div(touches, axis=0) * 100).round(3)
    understat_per100.columns = [f'{col}_per100touches' for col in understat_per100.columns]

    # Base info columns
    base_cols = ['unique_player_id', 'player_name', 'team', 'league', 'season', 'position', 'nationality', 'age']
    df_base = df_cb[base_cols].reset_index(drop=True)

    # Reset indices for concat
    fbref_nums = fbref_nums.reset_index(drop=True)
    understat_nums = understat_nums.reset_index(drop=True)
    fbref_per90 = fbref_per90.reset_index(drop=True)
    understat_per90 = understat_per90.reset_index(drop=True)
    fbref_per100 = fbref_per100.reset_index(drop=True)
    understat_per100 = understat_per100.reset_index(drop=True)

    # Combine all
    df_final = pd.concat([
        df_base,
        fbref_nums,
        understat_nums,
        fbref_per90,
        understat_per90,
        fbref_per100,
        understat_per100
    ], axis=1)

    print(f"Final: {df_final.shape[0]} rows, {df_final.shape[1]} columns")

    # Export to Excel
    df_final.to_excel(OUTPUT_FILE, index=False, engine='openpyxl')
    print(f"Exported: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
