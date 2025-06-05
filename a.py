# Test rápido
from edata.understat_data import test_shot_events_simple, list_players_in_match

# Ver qué jugadores están disponibles
players = list_players_in_match(22256, verbose=True)

# Test con Cody Gakpo
success = test_shot_events_simple(22256, "Cody Gakpo", verbose=True)

# O usar la función mejorada directamente
from edata.understat_data import extract_understat_shot_events_with_names

gakpo_shots = extract_understat_shot_events_with_names(
    22256, "ENG-Premier League", "2023-24", 
    player_filter="Cody Gakpo", verbose=True
)