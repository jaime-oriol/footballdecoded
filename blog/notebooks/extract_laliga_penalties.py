"""Extract LaLiga penalty data from 2004 to 2025 for analysis."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pandas as pd
from scrappers.transfermarkt_penalties import TransfermarktPenalties

# Config
START_YEAR = 2004
END_YEAR = 2025
OUTPUT_FILE = './laliga_penalties_2004_2025.xlsx'


def main():
    print("="*60)
    print("EXTRACCIÓN DE PENALTIS LALIGA (2004-2025)")
    print("="*60)

    tp = TransfermarktPenalties(no_cache=True)  # Force fresh download

    all_received = []
    all_conceded = []
    all_scorers = []
    all_detail = []

    for year in range(START_YEAR, END_YEAR + 1):
        season_str = f"{year}-{str(year+1)[-2:]}"
        print(f"\n>>> Temporada {season_str}")

        # Penaltis recibidos (a favor)
        try:
            received = tp.get_team_penalties_received(year)
            if not received.empty:
                all_received.append(received)
                print(f"    Recibidos: {len(received)} equipos")
        except Exception as e:
            print(f"    ERROR recibidos: {e}")

        # Penaltis concedidos (en contra)
        try:
            conceded = tp.get_team_penalties_conceded(year)
            if not conceded.empty:
                all_conceded.append(conceded)
                print(f"    Concedidos: {len(conceded)} equipos")
        except Exception as e:
            print(f"    ERROR concedidos: {e}")

        # Goleadores
        try:
            scorers = tp.get_penalty_scorers(year)
            if not scorers.empty:
                all_scorers.append(scorers)
                print(f"    Goleadores: {len(scorers)} jugadores")
        except Exception as e:
            print(f"    ERROR goleadores: {e}")

        # Detalle completo (convertidos + fallados con minuto y marcador)
        try:
            detail = tp.get_all_penalties_detail(year)
            if not detail.empty:
                all_detail.append(detail)
                scored_count = len(detail[detail['scored'] == True])
                missed_count = len(detail[detail['scored'] == False])
                print(f"    Detalle: {len(detail)} penaltis ({scored_count} gol, {missed_count} fallo)")
        except Exception as e:
            print(f"    ERROR detalle: {e}")

    # Combinar todos los datos
    print("\n" + "="*60)
    print("COMBINANDO DATOS...")

    df_received = pd.concat(all_received, ignore_index=True) if all_received else pd.DataFrame()
    df_conceded = pd.concat(all_conceded, ignore_index=True) if all_conceded else pd.DataFrame()
    df_scorers = pd.concat(all_scorers, ignore_index=True) if all_scorers else pd.DataFrame()
    df_detail = pd.concat(all_detail, ignore_index=True) if all_detail else pd.DataFrame()

    print(f"\nResumen:")
    print(f"  - Recibidos: {len(df_received)} filas")
    print(f"  - Concedidos: {len(df_conceded)} filas")
    print(f"  - Goleadores: {len(df_scorers)} filas")
    print(f"  - Detalle: {len(df_detail)} filas")

    # Crear métricas adicionales
    print("\nCalculando métricas adicionales...")

    # Top goleadores históricos
    if not df_scorers.empty:
        top_scorers = df_scorers.groupby('player').agg({
            'penalties': 'sum',
            'scored': 'sum',
            'missed': 'sum',
            'team': lambda x: ', '.join(x.unique()),
            'season': 'count'
        }).reset_index()
        top_scorers.columns = ['player', 'total_penalties', 'total_scored', 'total_missed', 'teams', 'seasons_played']
        top_scorers['conversion_rate'] = (top_scorers['total_scored'] / top_scorers['total_penalties'] * 100).round(1)
        top_scorers = top_scorers.sort_values('total_scored', ascending=False)

    # Equipos históricos
    if not df_received.empty:
        team_received = df_received.groupby('team').agg({
            'penalties_received': 'sum',
            'scored': 'sum',
            'missed': 'sum',
            'season': 'count'
        }).reset_index()
        team_received.columns = ['team', 'total_received', 'total_scored', 'total_missed', 'seasons']
        team_received['conversion_rate'] = (team_received['total_scored'] / team_received['total_received'] * 100).round(1)
        team_received = team_received.sort_values('total_received', ascending=False)

    if not df_conceded.empty:
        team_conceded = df_conceded.groupby('team').agg({
            'penalties_conceded': 'sum',
            'saved': 'sum',
            'goals_against': 'sum',
            'season': 'count'
        }).reset_index()
        team_conceded.columns = ['team', 'total_conceded', 'total_saved', 'total_goals_against', 'seasons']
        team_conceded['save_rate'] = (team_conceded['total_saved'] / team_conceded['total_conceded'] * 100).round(1)
        team_conceded = team_conceded.sort_values('total_conceded', ascending=False)

    # Análisis por minuto (todos los penaltis tienen minuto y marcador)
    if not df_detail.empty:
        df_with_minute = df_detail[df_detail['minute'].notna()].copy()
        if not df_with_minute.empty:
            # Rangos de minutos
            df_with_minute['minute_range'] = pd.cut(
                df_with_minute['minute'],
                bins=[0, 15, 30, 45, 60, 75, 90, 120],
                labels=['1-15', '16-30', '31-45', '46-60', '61-75', '76-90', '90+']
            )
            minute_analysis = df_with_minute.groupby('minute_range', observed=True).size().reset_index(name='count')

    # Análisis por marcador
    if not df_detail.empty:
        df_with_score = df_detail[df_detail['score_at_penalty'].notna()].copy()
        if not df_with_score.empty:
            score_analysis = df_with_score.groupby(['score_at_penalty', 'scored']).size().reset_index(name='count')

    # Exportar a Excel con múltiples hojas
    print(f"\nExportando a {OUTPUT_FILE}...")

    with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:
        # Datos brutos
        df_received.to_excel(writer, sheet_name='Penaltis_A_Favor', index=False)
        df_conceded.to_excel(writer, sheet_name='Penaltis_En_Contra', index=False)
        df_scorers.to_excel(writer, sheet_name='Goleadores_Por_Temporada', index=False)
        df_detail.to_excel(writer, sheet_name='Detalle_Penaltis', index=False)

        # Rankings históricos
        if not df_scorers.empty:
            top_scorers.to_excel(writer, sheet_name='Top_Goleadores_Historico', index=False)
        if not df_received.empty:
            team_received.to_excel(writer, sheet_name='Equipos_A_Favor_Historico', index=False)
        if not df_conceded.empty:
            team_conceded.to_excel(writer, sheet_name='Equipos_En_Contra_Historico', index=False)

        # Análisis adicional
        if not df_detail.empty and not df_with_minute.empty:
            minute_analysis.to_excel(writer, sheet_name='Analisis_Minutos', index=False)
        if not df_detail.empty and not df_with_score.empty:
            score_analysis.to_excel(writer, sheet_name='Analisis_Marcador', index=False)

    print("\n" + "="*60)
    print("EXTRACCIÓN COMPLETADA")
    print("="*60)
    print(f"\nArchivo generado: {OUTPUT_FILE}")
    print(f"\nHojas incluidas:")
    print("  1. Penaltis_A_Favor - Por equipo y temporada")
    print("  2. Penaltis_En_Contra - Por equipo y temporada")
    print("  3. Goleadores_Por_Temporada - Jugadores por temporada")
    print("  4. Detalle_Penaltis - TODOS con minuto, marcador, home/away, is_home (scored/missed)")
    print("  5. Top_Goleadores_Historico - Ranking histórico")
    print("  6. Equipos_A_Favor_Historico - Ranking equipos")
    print("  7. Equipos_En_Contra_Historico - Ranking equipos")
    print("  8. Analisis_Minutos - Distribución por minuto")
    print("  9. Analisis_Marcador - Penaltis por marcador")


if __name__ == '__main__':
    main()
