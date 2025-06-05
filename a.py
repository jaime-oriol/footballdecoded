# ====================================================================
# Ejemplo de Uso Real - Understat Data Extractor
# ====================================================================
# Test simple y funcional del wrapper de Understat
# Basado en la documentación real del scraper
# ====================================================================

# Importar el wrapper de Understat
from edata.understat_data import (
    extract_understat_player_season,
    extract_understat_team_season,
    extract_multiple_understat_players,
    merge_fbref_with_understat,
    quick_enriched_analysis
)

# También necesitamos FBref para el merge
from edata.fbref_data import extract_multiple_players_season

def test_understat_simple():
    """Test básico del extractor de Understat."""
    
    print("🧪 TEST 1: Extracción simple de jugador")
    print("-" * 40)
    
    # Extraer métricas avanzadas de Haaland
    player_stats = extract_understat_player_season(
        player_name="Erling Haaland",
        league="ENG-Premier League", 
        season="2023-24",
        verbose=True
    )
    
    if player_stats:
        print(f"✅ Datos extraídos para Haaland:")
        print(f"   xGChain: {player_stats.get('understat_xg_chain', 'N/A')}")
        print(f"   xGBuildup: {player_stats.get('understat_xg_buildup', 'N/A')}")
        print(f"   npxG + xA: {player_stats.get('understat_npxg_plus_xa', 'N/A')}")
    else:
        print("❌ No se encontraron datos")


def test_understat_multiple():
    """Test de múltiples jugadores."""
    
    print("\n🧪 TEST 2: Múltiples jugadores")
    print("-" * 40)
    
    players = ["Erling Haaland", "Kevin De Bruyne", "Phil Foden"]
    
    df = extract_multiple_understat_players(
        players=players,
        league="ENG-Premier League",
        season="2023-24", 
        verbose=True
    )
    
    if not df.empty:
        print(f"✅ DataFrame creado con {len(df)} jugadores")
        print("\nColumnas Understat:")
        understat_cols = [col for col in df.columns if col.startswith('understat_')]
        for col in understat_cols:
            print(f"   • {col}")
    else:
        print("❌ DataFrame vacío")


def test_team_stats():
    """Test de estadísticas de equipo."""
    
    print("\n🧪 TEST 3: Estadísticas de equipo")
    print("-" * 40)
    
    team_stats = extract_understat_team_season(
        team_name="Manchester City",
        league="ENG-Premier League",
        season="2023-24",
        verbose=True
    )
    
    if team_stats:
        print(f"✅ Datos de equipo extraídos:")
        print(f"   PPDA promedio: {team_stats.get('understat_ppda_avg', 'N/A')}")
        print(f"   Deep completions: {team_stats.get('understat_deep_completions_total', 'N/A')}")
        print(f"   xPoints total: {team_stats.get('understat_expected_points_total', 'N/A')}")
    else:
        print("❌ No se encontraron datos del equipo")


def test_merge_with_fbref():
    """Test del merge con datos de FBref."""
    
    print("\n🧪 TEST 4: Merge FBref + Understat")
    print("-" * 40)
    
    # Primero obtener datos de FBref
    print("📊 Extrayendo datos de FBref...")
    fbref_data = extract_multiple_players_season(
        players=["Erling Haaland", "Kevin De Bruyne"],
        league="ENG-Premier League",
        season="2023-24",
        verbose=False
    )
    
    if not fbref_data.empty:
        print(f"✅ FBref: {len(fbref_data)} jugadores, {len(fbref_data.columns)} columnas")
        
        # Ahora hacer el merge
        print("🔗 Haciendo merge con Understat...")
        enriched_data = merge_fbref_with_understat(
            fbref_data=fbref_data,
            league="ENG-Premier League", 
            season="2023-24",
            verbose=True
        )
        
        if not enriched_data.empty:
            print(f"✅ Merge exitoso: {len(enriched_data)} jugadores")
            
            # Mostrar algunas columnas combinadas
            key_columns = ['player_name', 'goals', 'understat_xg_chain', 'understat_xg_buildup']
            available_cols = [col for col in key_columns if col in enriched_data.columns]
            
            if available_cols:
                print("\n📊 Muestra de datos combinados:")
                print(enriched_data[available_cols].to_string(index=False))
        else:
            print("❌ Merge falló")
    else:
        print("❌ No se pudieron obtener datos de FBref")


def test_quick_analysis():
    """Test de análisis completo rápido."""
    
    print("\n🧪 TEST 5: Análisis completo automático")
    print("-" * 40)
    
    analysis = quick_enriched_analysis(
        players=["Erling Haaland", "Kevin De Bruyne"],
        league="ENG-Premier League",
        season="2023-24",
        export=False,  # No exportar en test
        verbose=True
    )
    
    print(f"\n📋 Resultados del análisis:")
    for key, value in analysis.items():
        if isinstance(value, pd.DataFrame):
            print(f"   {key}: DataFrame con {len(value)} filas, {len(value.columns)} columnas")
        else:
            print(f"   {key}: {type(value).__name__}")


if __name__ == "__main__":
    """Ejecutar todos los tests de ejemplo."""
    
    print("🚀 TESTS UNDERSTAT DATA EXTRACTOR")
    print("=" * 50)
    
    try:
        # Tests individuales
        test_understat_simple()
        test_understat_multiple() 
        test_team_stats()
        test_merge_with_fbref()
        test_quick_analysis()
        
        print("\n" + "=" * 50)
        print("✅ TODOS LOS TESTS COMPLETADOS")
        print("💡 Si algún test falló, revisa:")
        print("   • Conexión a internet")
        print("   • Nombres de jugadores correctos")
        print("   • Disponibilidad de datos en Understat")
        
    except Exception as e:
        print(f"\n❌ ERROR EN TESTS: {str(e)}")
        print("💡 Revisa que:")
        print("   • El módulo scrappers esté disponible")
        print("   • Los archivos edata/fbref_data.py y edata/understat_data.py existan")
        print("   • La conexión a internet funcione")


# ====================================================================
# TESTS ESPECÍFICOS DE MÉTRICAS
# ====================================================================

def test_specific_metrics():
    """Test enfocado en las métricas específicas que queremos."""
    
    print("\n🎯 TEST MÉTRICAS ESPECÍFICAS")
    print("-" * 30)
    
    # Test con un jugador conocido
    stats = extract_understat_player_season(
        "Erling Haaland",
        "ENG-Premier League", 
        "2023-24",
        verbose=False
    )
    
    if stats:
        print("📊 Métricas objetivo encontradas:")
        
        # Las métricas que necesitamos específicamente
        target_metrics = {
            'understat_xg_chain': 'xGChain',
            'understat_xg_buildup': 'xGBuildup', 
            'understat_npxg_plus_xa': 'npxG + xA',
            'understat_np_xg': 'npxG',
            'understat_xa': 'xA'
        }
        
        for key, label in target_metrics.items():
            value = stats.get(key, 'NO ENCONTRADO')
            status = "✅" if value != 'NO ENCONTRADO' else "❌"
            print(f"   {status} {label}: {value}")
    else:
        print("❌ No se pudieron extraer métricas")


# Ejecutar test específico si se llama directamente
if __name__ == "__main__":
    test_specific_metrics()