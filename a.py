# ====================================================================
# Test FBref Simple - Dembélé y PSG
# ====================================================================
# Test directo sin complicaciones
# ====================================================================

from wrappers import (
    fbref_get_player,
    fbref_get_team,
    fbref_export_to_csv
)

# ====================================================================
# CONFIGURACIÓN SIMPLE
# ====================================================================

LEAGUE = "INT-Champions League"
SEASON = "2024-25"
PLAYER = "Ousmane Dembélé"
TEAM = "PSG"

def test_dembele_champions():
    """Test 1: Dembélé en Champions"""
    print("🎯 TEST 1: Dembélé en Champions League")
    
    dembele_data = fbref_get_player(PLAYER, LEAGUE, SEASON)
    
    if dembele_data:
        print(f"   ✅ Datos de {PLAYER} extraídos")
        print(f"   📊 Campos disponibles: {len(dembele_data)}")
        
        # Stats clave
        key_stats = ['matches_played', 'goals', 'assists', 'minutes_played', 'shots', 'passes_completed']
        
        print("   📈 Estadísticas principales:")
        for stat in key_stats:
            if stat in dembele_data:
                print(f"      {stat}: {dembele_data[stat]}")
        
        # Export
        filename = fbref_export_to_csv(dembele_data, "dembele_champions", include_timestamp=False)
        print(f"   💾 Exportado: {filename}")
        
        return True
    else:
        print(f"   ❌ No se pudieron extraer datos de {PLAYER}")
        return False

def test_psg_champions():
    """Test 2: PSG en Champions"""
    print("\n🏟️ TEST 2: PSG en Champions League")
    
    psg_data = fbref_get_team(TEAM, LEAGUE, SEASON)
    
    if psg_data:
        print(f"   ✅ Datos del {TEAM} extraídos")
        print(f"   📊 Campos disponibles: {len(psg_data)}")
        
        # Stats del equipo
        team_stats = ['wins', 'draws', 'losses', 'goals_for', 'goals_against', 'points']
        
        print("   📈 Estadísticas del equipo:")
        for stat in team_stats:
            if stat in psg_data:
                print(f"      {stat}: {psg_data[stat]}")
        
        # Export
        filename = fbref_export_to_csv(psg_data, "psg_champions", include_timestamp=False)
        print(f"   💾 Exportado: {filename}")
        
        return True
    else:
        print(f"   ❌ No se pudieron extraer datos del {TEAM}")
        return False

def test_comparison():
    """Test 3: Comparación rápida"""
    print("\n📊 TEST 3: Resumen comparativo")
    
    # Datos ya extraídos
    dembele = fbref_get_player(PLAYER, LEAGUE, SEASON)
    psg = fbref_get_team(TEAM, LEAGUE, SEASON)
    
    if dembele and psg:
        print("   ✅ Comparación Dembélé vs PSG:")
        
        # Dembélé
        dembele_goals = dembele.get('goals', 0)
        dembele_minutes = dembele.get('minutes_played', 0)
        
        # PSG
        psg_goals = psg.get('goals_for', 0)
        psg_matches = psg.get('wins', 0) + psg.get('draws', 0) + psg.get('losses', 0)
        
        print(f"      🎯 Goles Dembélé: {dembele_goals}")
        print(f"      🎯 Goles PSG total: {psg_goals}")
        print(f"      🕐 Minutos Dembélé: {dembele_minutes}")
        print(f"      ⚽ Partidos PSG: {psg_matches}")
        
        if dembele_goals and psg_goals:
            contribution = (dembele_goals / psg_goals * 100) if psg_goals > 0 else 0
            print(f"      📈 Contribución goleadora: {contribution:.1f}%")
        
        return True
    else:
        print("   ❌ No hay datos suficientes para comparar")
        return False

def run_simple_tests():
    """Ejecutar tests simples"""
    print("🚀 TESTS SIMPLES FBREF - DEMBÉLÉ Y PSG")
    print("=" * 50)
    
    tests = [
        test_dembele_champions,
        test_psg_champions,
        test_comparison
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 RESULTADOS")
    print(f"✅ Exitosos: {sum(results)}/{len(results)}")
    print(f"❌ Fallidos: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("🎉 TODOS LOS TESTS PASARON")
    else:
        print("⚠️ ALGUNOS TESTS FALLARON")

if __name__ == "__main__":
    run_simple_tests()