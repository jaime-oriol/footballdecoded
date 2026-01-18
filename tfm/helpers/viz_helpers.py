"""
Visualización helpers para TFM

Funciones de visualización siguiendo el estilo FootballDecoded para generar
imágenes de rankings y comparaciones de jugadores.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image
import os
from typing import Dict
import pandas as pd

BACKGROUND_COLOR = '#313332'
FONT_FAMILY = 'DejaVu Sans'


def plot_top10_ranking(
    result: Dict,
    df_data: pd.DataFrame,
    save_path: str = 'top10_ranking.png',
    target_face_path: str = None,
    highlight_target: bool = True,
    dpi: int = 300
) -> str:
    """
    Genera imagen PNG del TOP 10 ranking con estilo FootballDecoded.

    Args:
        result: Dict retornado por find_similar_players_cosine()
        df_data: DataFrame original con datos completos
        save_path: Ruta de salida PNG
        target_face_path: Ruta a la foto del target (opcional)
        highlight_target: Si True, destaca fila del target
        dpi: Resolución imagen

    Returns:
        Ruta absoluta del archivo PNG generado
    """
    # Extraer datos
    similar_df = result['similar_players'].head(10).copy()
    target_info = result['target_info']
    replacement_info = result.get('replacement_info')

    # Enriquecer con age y market_value (solo si no vienen pre-calculados)
    has_age = 'age' in similar_df.columns and similar_df['age'].notna().any()
    has_market = 'market_value_m' in similar_df.columns and similar_df['market_value_m'].notna().any()

    if not has_age or not has_market:
        merge_cols = ['unique_player_id']
        if not has_age:
            merge_cols.append('age')
        if not has_market:
            merge_cols.append('transfermarkt_metrics')

        similar_df = similar_df.merge(
            df_data[merge_cols],
            on='unique_player_id',
            how='left',
            suffixes=('', '_db')
        )

        # Si age vino del merge, usarlo
        if 'age_db' in similar_df.columns:
            similar_df['age'] = similar_df['age'].fillna(similar_df['age_db'])
            similar_df = similar_df.drop(columns=['age_db'])

    def extract_market_value(row):
        if pd.notna(row.get('transfermarkt_metrics')) and isinstance(row['transfermarkt_metrics'], dict):
            val = row['transfermarkt_metrics'].get('transfermarkt_market_value_eur')
            if val:
                try:
                    return float(val) / 1_000_000
                except:
                    return None
        return None

    # Solo calcular market_value_m si no viene pre-calculado
    if not has_market:
        similar_df['market_value_m'] = similar_df.apply(extract_market_value, axis=1)

    # Si replacement no está en top-10, añadirlo al final
    add_replacement_row = False
    rank = replacement_info.get('rank') if replacement_info else None
    if replacement_info and rank is not None and rank > 10:
        replacement_id = replacement_info['unique_player_id']

        # Construir replacement_row directamente desde replacement_info
        replacement_row = pd.DataFrame([{
            'unique_player_id': replacement_info['unique_player_id'],
            'player_name': replacement_info['player_name'],
            'team': replacement_info['team'],
            'league': replacement_info['league'],
            'season': replacement_info['season'],
            'rank': replacement_info['rank'],
            'cosine_similarity': replacement_info['cosine_similarity'],
            'age': replacement_info.get('age'),
            'market_value_m': replacement_info.get('market_value_m')
        }])

        # Solo enriquecer desde BD si faltan age o market_value_m
        needs_age = pd.isna(replacement_row['age'].iloc[0])
        needs_market = pd.isna(replacement_row['market_value_m'].iloc[0])

        if needs_age or needs_market:
            merge_cols = ['unique_player_id']
            if needs_age:
                merge_cols.append('age')
            if needs_market:
                merge_cols.append('transfermarkt_metrics')

            replacement_row = replacement_row.merge(
                df_data[merge_cols],
                on='unique_player_id',
                how='left',
                suffixes=('', '_db')
            )
            if 'age_db' in replacement_row.columns:
                replacement_row['age'] = replacement_row['age'].fillna(replacement_row['age_db'])
                replacement_row = replacement_row.drop(columns=['age_db'])
            if needs_market:
                replacement_row['market_value_m'] = replacement_row.apply(extract_market_value, axis=1)

        # Añadir al dataframe
        similar_df = pd.concat([similar_df, replacement_row], ignore_index=True)
        add_replacement_row = True

    # Setup figura
    num_rows = len(similar_df)
    has_footer = False  # Ya no necesitamos footer si añadimos la fila
    fig_height = 2.5 + (num_rows * 0.65) + 0.5

    fig, ax = plt.subplots(figsize=(12, fig_height), facecolor=BACKGROUND_COLOR)
    ax.set_facecolor(BACKGROUND_COLOR)
    ax.set_xlim(0, 12)
    y_max = 2.5 + (num_rows * 0.65) + (0.5 if has_footer else 0.3)
    ax.set_ylim(0, y_max)
    ax.axis('off')

    y_top = y_max - 0.3
    y_header_pos = y_top - 1.5
    y_separator = y_header_pos - 0.2
    y_rows_start = y_separator - 0.3

    # Foto del target
    target_name = target_info['player_name']
    if target_face_path and os.path.exists(target_face_path):
        try:
            face_img = Image.open(target_face_path)
            face_y_frac = (y_top - 1.25) / y_max
            face_ax = fig.add_axes([0.05, face_y_frac, 0.12, 0.12])
            face_ax.imshow(face_img)
            face_ax.axis('off')
        except:
            pass

    # Header
    ax.text(
        2, y_top - 0.4, "TOP 10 - Most Similar Players",
        fontsize=18, fontweight='bold', color='white',
        ha='left', va='center', family=FONT_FAMILY
    )

    target_season = target_info['season']
    target_team = target_info.get('team', '')
    ax.text(
        2, y_top - 0.7, f"Target: {target_name} ({target_team}, {target_season})",
        fontsize=14, color='white', ha='left', va='center', family=FONT_FAMILY
    )

    # Logo FootballDecoded
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Subir desde tfm/helpers/ hasta data/
        data_root = os.path.dirname(os.path.dirname(current_dir))
        logo_path = os.path.join(data_root, "blog", "logo", "Logo-blanco.png")

        if os.path.exists(logo_path):
            logo = Image.open(logo_path)
            logo_y_frac = (y_top - 1.3) / y_max
            logo_ax = fig.add_axes([0.675, logo_y_frac, 0.31, 0.145])
            logo_ax.imshow(logo)
            logo_ax.axis('off')
    except:
        pass

    # Column headers
    y_header = y_header_pos
    ax.text(0.8, y_header, "Rank", fontsize=14, fontweight='bold',
            color='white', family=FONT_FAMILY, va='center')
    ax.text(1.8, y_header, "Player", fontsize=14, fontweight='bold',
            color='white', family=FONT_FAMILY, va='center')
    ax.text(5.5, y_header, "Team", fontsize=14, fontweight='bold',
            color='white', family=FONT_FAMILY, va='center')
    ax.text(8.0, y_header, "Age", fontsize=14, fontweight='bold',
            color='white', ha='center', family=FONT_FAMILY, va='center')
    ax.text(9.5, y_header, "Value (M€)", fontsize=14, fontweight='bold',
            color='white', ha='right', family=FONT_FAMILY, va='center')
    ax.text(11.2, y_header, "Similarity", fontsize=14, fontweight='bold',
            color='white', ha='right', family=FONT_FAMILY, va='center')

    # Header separator
    ax.plot([0.5, 11.5], [y_separator, y_separator], color='grey', linewidth=0.5, alpha=0.6)

    # Rows
    y_start = y_rows_start
    row_height = 0.65
    replacement_id = replacement_info['unique_player_id'] if replacement_info else None

    for idx, row in similar_df.iterrows():
        # Si es el replacement añadido (último y fuera del top-10), añadir separador
        if add_replacement_row and idx == len(similar_df) - 1:
            y_separator_replacement = y_start - ((idx - 0.3) * row_height)

        y_pos = y_start - (idx * row_height)
        player_id = row['unique_player_id']

        if idx % 2 == 0:
            rect = Rectangle(
                (0.5, y_pos - 0.32), 11.0, row_height,
                facecolor='white', alpha=0.05,
                edgecolor='none'
            )
            ax.add_patch(rect)

        is_target = (highlight_target and replacement_id and player_id == replacement_id)
        if is_target:
            # Fondo azul
            rect_hl = Rectangle(
                (0.5, y_pos - 0.32), 11.0, row_height,
                facecolor='deepskyblue', alpha=0.15,
                edgecolor='none', linewidth=0
            )
            ax.add_patch(rect_hl)
            # Recuadro blanco grueso
            rect_border = Rectangle(
                (0.5, y_pos - 0.32), 11.0, row_height,
                facecolor='none',
                edgecolor='white', linewidth=2.5
            )
            ax.add_patch(rect_border)

        rank = int(row['rank'])
        player_name = str(row['player_name'])[:22]
        team = str(row['team'])[:18]
        similarity = float(row['cosine_similarity'])
        age = int(row['age']) if pd.notna(row.get('age')) else '-'
        market_val = row.get('market_value_m')
        market_str = f"{market_val:.1f}" if pd.notna(market_val) else '-'

        ax.text(0.8, y_pos, str(rank), fontsize=12, color='white',
                family=FONT_FAMILY, va='center')
        ax.text(1.8, y_pos, player_name, fontsize=12, color='white',
                family=FONT_FAMILY, va='center')
        ax.text(5.5, y_pos, team, fontsize=12, color='white',
                family=FONT_FAMILY, va='center')
        ax.text(8.0, y_pos, str(age), fontsize=12, color='white',
                ha='center', family=FONT_FAMILY, va='center')
        ax.text(9.5, y_pos, market_str, fontsize=12, color='white',
                ha='right', family=FONT_FAMILY, va='center')
        ax.text(11.2, y_pos, f"{similarity:.3f}", fontsize=12,
                color='white', ha='right', family=FONT_FAMILY, va='center')

    plt.tight_layout()
    plt.savefig(save_path, dpi=dpi, bbox_inches='tight', facecolor=BACKGROUND_COLOR)
    plt.close()

    return os.path.abspath(save_path)
