# Extract one players data of a season form Fbref
# Extractor completo de datos de jugador desde FBref

import sys
import os
# Ajustar path para acceder a extractors
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from extractors import FBref

def clean_column_name(col):
    """Limpia un nombre de columna individual"""
    if isinstance(col, tuple):
        level0, level1 = col[0], col[1]
        
        # Si level1 está vacío, usar solo level0
        if level1 == '' or pd.isna(level1) or level1 is None:
            return level0
        else:
            # Para casos específicos, usar solo el level1 (la estadística real)
            if level0 in ['Standard', 'Performance', 'Expected', 'Total', 'Short', 'Medium', 'Long', 'Playing Time', 'Per 90 Minutes']:
                return level1
            else:
                return f"{level0}_{level1}"
    else:
        return str(col)

def get_stat_mapping():
    """Mapeo completo de nombres técnicos a nombres descriptivos"""
    return {
        # Info básica
        'nation': 'nationality',
        'pos': 'position', 
        'age': 'age',
        'born': 'birth_year',
        
        # Tiempo de juego
        'MP': 'matches_played',
        'Starts': 'matches_started',
        'Min': 'minutes_played',
        '90s': 'full_matches_equivalent',
        'Mn/MP': 'minutes_per_match',
        'Min%': 'minutes_percentage',
        'Starts_Starts': 'matches_started',
        'Starts_Mn/Start': 'minutes_per_start',
        'Starts_Compl': 'complete_matches',
        'Subs_Subs': 'substitute_appearances',
        'Subs_Mn/Sub': 'minutes_per_substitution',
        'Subs_unSub': 'unused_substitute',
        
        # Rendimiento básico
        'Gls': 'goals',
        'Ast': 'assists', 
        'G+A': 'goals_plus_assists',
        'G-PK': 'non_penalty_goals',
        'PK': 'penalty_goals',
        'PKatt': 'penalty_attempts',
        'CrdY': 'yellow_cards',
        'CrdR': 'red_cards',
        '2CrdY': 'second_yellow_cards',
        'G+A-PK': 'goals_assists_minus_penalties',
        
        # Tiro y finalización
        'Sh': 'shots',
        'SoT': 'shots_on_target',
        'SoT%': 'shots_on_target_pct',
        'Sh/90': 'shots_per_90',
        'SoT/90': 'shots_on_target_per_90',
        'G/Sh': 'goals_per_shot',
        'G/SoT': 'goals_per_shot_on_target',
        'Dist': 'avg_shot_distance',
        'FK': 'free_kick_shots',
        
        # Expected Goals
        'xG': 'expected_goals',
        'npxG': 'non_penalty_expected_goals',
        'npxG/Sh': 'non_penalty_xG_per_shot',
        'G-xG': 'goals_minus_expected',
        'np:G-xG': 'non_penalty_goals_minus_expected',
        'xAG': 'expected_assists',
        'xA': 'expected_assists_alt',
        'A-xAG': 'assists_minus_expected',
        'npxG+xAG': 'non_penalty_xG_plus_xAG',
        'xG+xAG': 'expected_goals_plus_assists',
        
        # Pases
        'Cmp': 'passes_completed',
        'Att': 'passes_attempted', 
        'Cmp%': 'pass_completion_pct',
        'TotDist': 'total_pass_distance',
        'PrgDist': 'progressive_pass_distance',
        'KP': 'key_passes',
        '1/3': 'passes_final_third',
        'PPA': 'passes_penalty_area',
        'CrsPA': 'crosses_penalty_area',
        'PrgP': 'progressive_passes',
        
        # Progresión
        'Progression_PrgC': 'progressive_carries',
        'Progression_PrgP': 'progressive_passes_total',
        'Progression_PrgR': 'progressive_passes_received',
        
        # Tipos de pases
        'Pass Types_Live': 'live_ball_passes',
        'Pass Types_Dead': 'dead_ball_passes',
        'Pass Types_FK': 'free_kick_passes',
        'Pass Types_TB': 'through_balls',
        'Pass Types_Sw': 'switches',
        'Pass Types_Crs': 'crosses',
        'Pass Types_TI': 'throw_ins',
        'Pass Types_CK': 'corner_kicks',
        'Corner Kicks_In': 'inswinging_corners',
        'Corner Kicks_Out': 'outswinging_corners',
        'Corner Kicks_Str': 'straight_corners',
        'Outcomes_Cmp': 'completed_passes',
        'Outcomes_Off': 'offsides_from_passes',
        'Outcomes_Blocks': 'blocked_passes',
        
        # Creación de ocasiones
        'SCA_SCA': 'shot_creating_actions',
        'SCA_SCA90': 'shot_creating_actions_per_90',
        'SCA Types_PassLive': 'sca_live_passes',
        'SCA Types_PassDead': 'sca_dead_ball_passes',
        'SCA Types_TO': 'sca_take_ons',
        'SCA Types_Sh': 'sca_shots',
        'SCA Types_Fld': 'sca_fouls_drawn',
        'SCA Types_Def': 'sca_defensive_actions',
        'GCA_GCA': 'goal_creating_actions',
        'GCA_GCA90': 'goal_creating_actions_per_90',
        'GCA Types_PassLive': 'gca_live_passes',
        'GCA Types_PassDead': 'gca_dead_ball_passes',
        'GCA Types_TO': 'gca_take_ons',
        'GCA Types_Sh': 'gca_shots',
        'GCA Types_Fld': 'gca_fouls_drawn',
        'GCA Types_Def': 'gca_defensive_actions',
        
        # Defensa
        'Tackles_Tkl': 'tackles_total',
        'Tackles_TklW': 'tackles_won',
        'Tackles_Def 3rd': 'tackles_defensive_third',
        'Tackles_Mid 3rd': 'tackles_middle_third',
        'Tackles_Att 3rd': 'tackles_attacking_third',
        'Challenges_Tkl': 'challenges_tackled',
        'Challenges_Att': 'challenges_attempted',
        'Challenges_Tkl%': 'challenge_success_pct',
        'Challenges_Lost': 'challenges_lost',
        'Blocks_Blocks': 'blocks_total',
        'Blocks_Sh': 'shots_blocked',
        'Blocks_Pass': 'passes_blocked',
        'Tkl': 'tackles',
        'TklW': 'tackles_won',
        'Int': 'interceptions',
        'Tkl+Int': 'tackles_plus_interceptions',
        'Clr': 'clearances',
        'Err': 'errors',
        
        # Posesión y toques
        'Touches_Touches': 'touches_total',
        'Touches_Def Pen': 'touches_defensive_penalty_area',
        'Touches_Def 3rd': 'touches_defensive_third',
        'Touches_Mid 3rd': 'touches_middle_third',
        'Touches_Att 3rd': 'touches_attacking_third',
        'Touches_Att Pen': 'touches_attacking_penalty_area',
        'Touches_Live': 'live_ball_touches',
        'Take-Ons_Att': 'take_ons_attempted',
        'Take-Ons_Succ': 'take_ons_successful',
        'Take-Ons_Succ%': 'take_on_success_pct',
        'Take-Ons_Tkld': 'take_ons_tackled',
        'Take-Ons_Tkld%': 'take_on_tackled_pct',
        'Touches': 'touches',
        'Succ': 'successful_take_ons',
        'Succ%': 'take_on_success_pct',
        'Tkld': 'tackled_during_take_on',
        'Tkld%': 'tackled_during_take_on_pct',
        
        # Conducciones
        'Carries_Carries': 'carries_total',
        'Carries_TotDist': 'carry_total_distance',
        'Carries_PrgDist': 'carry_progressive_distance',
        'Carries_PrgC': 'progressive_carries',
        'Carries_1/3': 'carries_into_final_third',
        'Carries_CPA': 'carries_into_penalty_area',
        'Carries_Mis': 'miscontrols',
        'Carries_Dis': 'dispossessed',
        'Carries': 'carries',
        'PrgC': 'progressive_carries',
        'Mis': 'miscontrols',
        'Dis': 'dispossessed',
        
        # Recepción
        'Receiving_Rec': 'passes_received',
        'Receiving_PrgR': 'progressive_passes_received',
        'Rec': 'passes_received',
        'PrgR': 'progressive_passes_received',
        
        # Éxito del equipo
        'Team Success_PPM': 'points_per_match',
        'Team Success_onG': 'goals_while_on_pitch',
        'Team Success_onGA': 'goals_against_while_on_pitch',
        'Team Success_+/-': 'plus_minus',
        'Team Success_+/-90': 'plus_minus_per_90',
        'Team Success_On-Off': 'team_performance_difference',
        'Team Success (xG)_onxG': 'expected_goals_while_on_pitch',
        'Team Success (xG)_onxGA': 'expected_goals_against_while_on_pitch',
        'Team Success (xG)_xG+/-': 'expected_plus_minus',
        'Team Success (xG)_xG+/-90': 'expected_plus_minus_per_90',
        'Team Success (xG)_On-Off': 'expected_team_performance_difference',
        
        # Faltas y disciplina
        'Fls': 'fouls_committed',
        'Fld': 'fouls_drawn',
        'Off': 'offsides',
        'Crs': 'crosses',
        'PKwon': 'penalties_won',
        'PKcon': 'penalties_conceded',
        'OG': 'own_goals',
        'Recov': 'ball_recoveries',
        
        # Duelos aéreos
        'Aerial Duels_Won': 'aerial_duels_won',
        'Aerial Duels_Lost': 'aerial_duels_lost',
        'Aerial Duels_Won%': 'aerial_duels_won_pct',
        'Won': 'aerial_duels_won',
        'Lost': 'aerial_duels_lost',
        'Won%': 'aerial_duels_won_pct'
    }

def extract_player_complete_data(player_name, leagues, seasons):
    """
    Extrae todos los datos de un jugador y los combina en una sola fila
    """
    print(f"🔄 Extrayendo datos completos para: {player_name}")
    print(f"📊 Ligas: {leagues}")
    print(f"📅 Temporadas: {seasons}")
    
    # Tipos de estadísticas a extraer
    stat_types = [
        'standard', 'shooting', 'passing', 'passing_types', 
        'goal_shot_creation', 'defense', 'possession', 
        'playing_time', 'misc'
    ]
    
    fbref = FBref(leagues=leagues, seasons=seasons)
    player_data = {}
    
    # Información básica del jugador
    basic_info = {}
    
    # Extraer cada tipo de estadística
    for i, stat_type in enumerate(stat_types, 1):
        print(f"[{i}/{len(stat_types)}] 🔄 {stat_type}")
        
        try:
            # Obtener datos
            stats = fbref.read_player_season_stats(stat_type=stat_type)
            
            # Buscar jugador
            player_row = find_player(stats, player_name)
            
            if player_row is not None:
                # Obtener info básica solo una vez
                if i == 1:  # Primera iteración
                    basic_info = {
                        'player_name': player_name,
                        'league': player_row.index.get_level_values('league')[0],
                        'season': player_row.index.get_level_values('season')[0],
                        'team': player_row.index.get_level_values('team')[0]
                    }
                
                # Procesar cada columna individualmente
                for col in player_row.columns:
                    clean_name = clean_column_name(col)
                    value = player_row.iloc[0][col]
                    
                    # Solo añadir si no lo tenemos ya (evitar duplicados)
                    if clean_name not in player_data:
                        player_data[clean_name] = value
                
                print(f"    ✅ {len(player_row.columns)} campos procesados")
            else:
                print(f"    ❌ Jugador no encontrado")
                
        except Exception as e:
            print(f"    ⚠️ Error: {str(e)[:60]}...")
    
    # Combinar info básica con estadísticas
    final_data = {**basic_info, **player_data}
    
    return final_data

def find_player(stats, player_name):
    """Busca un jugador en los datos"""
    if stats is None or stats.empty:
        return None
    
    # Variaciones del nombre
    variations = [
        player_name,
        player_name.replace('é', 'e').replace('ñ', 'n'),
        player_name.split()[-1] if ' ' in player_name else player_name,
        player_name.split()[0] if ' ' in player_name else player_name
    ]
    
    for variation in variations:
        matches = stats[
            stats.index.get_level_values('player').str.contains(
                variation, case=False, na=False
            )
        ]
        if not matches.empty:
            return matches
    
    return None

def create_final_dataset(player_data, player_name):
    """Crea el dataset final con nombres descriptivos"""
    if not player_data:
        return None
    
    print(f"\n🔧 Procesando datos finales...")
    
    # Aplicar mapeo de nombres
    stat_mapping = get_stat_mapping()
    
    final_data = {}
    
    # Procesar todas las estadísticas
    for original_name, value in player_data.items():
        if original_name in stat_mapping:
            clean_name = stat_mapping[original_name]
            final_data[clean_name] = value
        else:
            # Usar el nombre tal como está (ya debería estar limpio)
            final_data[original_name] = value
    
    # Convertir a DataFrame
    df = pd.DataFrame([final_data])
    
    print(f"    ✅ Dataset final: {len(df.columns)} columnas")
    
    # Mostrar algunas estadísticas clave
    key_stats = {}
    if 'goals' in df.columns:
        key_stats['goals'] = df['goals'].iloc[0]
    if 'assists' in df.columns:
        key_stats['assists'] = df['assists'].iloc[0]
    if 'shots' in df.columns:
        key_stats['shots'] = df['shots'].iloc[0]
    if 'expected_goals' in df.columns:
        key_stats['expected_goals'] = df['expected_goals'].iloc[0]
    
    if key_stats:
        print(f"    📈 Estadísticas clave: {key_stats}")
    
    return df

def main():
    """Función principal"""
    print("🚀 FootballDecoded - Extractor de Jugador FBref")
    print("=" * 60)
    
    # Configuración
    PLAYER_NAME = "Mbappé"
    LEAGUES = ["ESP-La Liga"]  
    SEASONS = ["2024-25"]
    
    # Extracción
    player_data = extract_player_complete_data(PLAYER_NAME, LEAGUES, SEASONS)
    
    # Crear dataset final
    final_dataset = create_final_dataset(player_data, PLAYER_NAME)
    
    if final_dataset is not None:
        # Guardar
        filename = f"{PLAYER_NAME.replace(' ', '_')}_complete_stats.csv"
        final_dataset.to_csv(filename, index=False)
        
        print(f"\n💾 ✅ Archivo guardado: {filename}")
        print(f"📊 Columnas totales: {len(final_dataset.columns)}")
        print(f"🎯 Listo para análisis y visualización")
        
        # Mostrar preview
        print(f"\n📋 Preview de algunas estadísticas:")
        key_cols = ['player_name', 'team', 'goals', 'assists', 'shots', 'expected_goals', 'passes_completed']
        available_cols = [col for col in key_cols if col in final_dataset.columns]
        if available_cols:
            print(final_dataset[available_cols].head())
    else:
        print("\n❌ No se pudieron extraer datos")
    
    print(f"\n" + "=" * 60)
    print("✅ Extracción completada")

if __name__ == "__main__":
    main()