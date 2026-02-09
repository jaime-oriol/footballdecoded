"""
Player analysis table with spatial field maps.
Stats table (left) + 4 half-pitch action/pass maps in 2x2 grid (right).
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
from mplsoccer import VerticalPitch
from PIL import Image
import os
from typing import List, Tuple

BACKGROUND_COLOR = '#313332'

def _format_player_name(name: str, max_length: int = 17) -> str:
    """Shorten long names to 'Initial. Surname' format if exceeding max_length."""
    if len(name) <= max_length:
        return name

    parts = name.split()

    if len(parts) < 2:
        return name

    first_initial = parts[0][0].upper()
    last_name = ' '.join(parts[1:])

    return f"{first_initial}. {last_name}"

def create_player_analysis_complete(
    player_name: str,
    team_name: str,
    enriched_metrics: List[Tuple[str, str]],
    events_df: pd.DataFrame,
    player_image_path: str = None
):
    """Create stats table + 4 spatial field maps (actions/passes per half). Requires 8-12 metrics."""
    if not (8 <= len(enriched_metrics) <= 12):
        raise ValueError("Must provide between 8 and 12 enriched metrics")

    table_path = 'temp_stats_table.png'
    spatial_paths = {}
    _create_large_stats_table(
        player_name, team_name, enriched_metrics, 
        player_image_path, table_path
    )
    
    spatial_paths = _create_spatial_fields_2x2(events_df, player_name)

    table_img = Image.open(table_path)
    field_images = {}
    for key, path in spatial_paths.items():
        if path and os.path.exists(path):
            field_images[key] = Image.open(path)
        else:
            field_images[key] = _create_blank_field()

    table_width, table_height = table_img.size
    field_width, field_height = field_images['actions_1st'].size

    fields_grid_width = field_width * 2
    fields_grid_height = field_height * 2
    total_width = table_width + fields_grid_width
    total_height = max(table_height, fields_grid_height)

    combined = Image.new('RGB', (total_width, total_height), color=BACKGROUND_COLOR)

    table_y = (total_height - table_height) // 2
    combined.paste(table_img, (0, table_y))

    fields_start_x = table_width
    fields_y_offset = (total_height - fields_grid_height) // 2
    combined.paste(field_images['actions_1st'], (fields_start_x, fields_y_offset))
    combined.paste(field_images['passes_1st'], (fields_start_x + field_width, fields_y_offset))
    combined.paste(field_images['actions_2nd'], (fields_start_x, fields_y_offset + field_height))
    combined.paste(field_images['passes_2nd'], (fields_start_x + field_width, fields_y_offset + field_height))

    fig, ax = plt.subplots(figsize=(total_width/100, total_height/100), dpi=100)
    ax.imshow(combined)
    ax.axis('off')
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0, hspace=0, wspace=0)
    
    os.remove(table_path)
    for path in spatial_paths.values():
        if path and os.path.exists(path):
            os.remove(path)

    return fig

def _create_large_stats_table(
    player_name: str, 
    team_name: str, 
    enriched_metrics: List[Tuple[str, str]],
    player_image_path: str,
    save_path: str
):
    """Create large statistical table component."""
    fig, ax = plt.subplots(figsize=(6, 8))
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    ax.set_facecolor(BACKGROUND_COLOR)
    ax.set_xlim(0, 6)
    ax.set_ylim(0, len(enriched_metrics) + 3)
    ax.axis('off')
    
    formatted_name = _format_player_name(player_name)
    ax.text(1.5, len(enriched_metrics) + 1.5, formatted_name, fontsize=15, color='white',
            fontweight='bold', ha='left', va='center', family='DejaVu Sans')
    ax.text(1.5, len(enriched_metrics) + 1.2, team_name, fontsize=12, color='white',
            ha='left', va='center', family='DejaVu Sans')
    
    if player_image_path and os.path.exists(player_image_path):
        try:
            player_img = Image.open(player_image_path)
            player_ax = fig.add_axes([0.1, 0.83, 0.15, 0.125])
            player_ax.imshow(player_img)
            player_ax.axis('off')
        except:
            pass
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        logo_path = os.path.join(project_root, "blog", "logo", "Logo-blanco.png")
        logo = Image.open(logo_path)
        logo_ax = fig.add_axes([0.575, 0.75, 0.35, 0.23])
        logo_ax.imshow(logo)
        logo_ax.axis('off')
    except:
        pass
    
    for i, (metric_name, metric_value) in enumerate(enriched_metrics):
        y_pos = len(enriched_metrics) - i + 0.5
        
        if i % 2 == 0:
            rect = Rectangle((0.4, y_pos - 0.45), 5.2, 0.9, facecolor='white', alpha=0.05)
            ax.add_patch(rect)
        
        ax.text(0.6, y_pos, metric_name, fontsize=12, color='white',
                ha='left', va='center', family='DejaVu Sans', fontweight='bold')
        ax.text(5.2, y_pos, metric_value, fontsize=12, color='white',
                ha='right', va='center', family='DejaVu Sans')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)
    plt.close()

def _create_spatial_fields_2x2(events_df: pd.DataFrame, player_name: str) -> dict:
    """Create 4 spatial field maps for each half-period combination."""
    paths = {}
    paths['actions_1st'] = _create_actions_field(events_df, player_name, 1, 44, 'temp_actions_1st.png', 'Actions 1st Half')
    paths['passes_1st'] = _create_passes_field(events_df, player_name, 1, 44, 'temp_passes_1st.png', 'Passes 1st Half')
    paths['actions_2nd'] = _create_actions_field(events_df, player_name, 46, 90, 'temp_actions_2nd.png', 'Actions 2nd Half')
    paths['passes_2nd'] = _create_passes_field(events_df, player_name, 46, 90, 'temp_passes_2nd.png', 'Passes 2nd Half')
    return paths

def _create_actions_field(
    events_df: pd.DataFrame, 
    player_name: str, 
    min_minute: int, 
    max_minute: int,
    save_path: str,
    title: str
) -> str:
    """Create spatial field showing successful vs failed actions."""
    actions = events_df[
        (events_df['player'] == player_name) & 
        (events_df['minute'] >= min_minute) &
        (events_df['minute'] <= max_minute) &
        (events_df['x'].notna()) & 
        (events_df['y'].notna()) &
        (events_df['event_type'] != 'Pass')
    ].copy()
    
    if len(actions) == 0:
        return _create_blank_field_file(save_path, title)

    pitch = VerticalPitch(
        pitch_color=BACKGROUND_COLOR,
        line_color='white', 
        linewidth=2,
        pitch_type='opta'
    )
    
    fig, ax = pitch.draw(figsize=(2.5, 3.5))
    fig.set_facecolor(BACKGROUND_COLOR)
    
    # KDE heatmap from all touches as background
    all_touches = events_df[
        (events_df['player'] == player_name) &
        (events_df['minute'] >= min_minute) &
        (events_df['minute'] <= max_minute) &
        (events_df['x'].notna()) &
        (events_df['y'].notna())
    ].copy()

    if len(all_touches) > 0:
        pitch.kdeplot(all_touches['x'], all_touches['y'],
                      fill=True, levels=80, shade_lowest=True,
                      cmap='viridis', cut=8, alpha=1,
                      antialiased=True, zorder=0, ax=ax)

    success_color = '#00BFFF'
    failure_color = '#FF6B6B'

    successful = actions[actions['is_successful'] == True]
    failed = actions[actions['is_successful'] == False]

    if len(successful) > 0:
        ax.scatter(successful['y'], successful['x'], 
                  c=success_color, s=60, marker='o', alpha=0.8,
                  edgecolors='white', linewidths=1, zorder=3)
    
    if len(failed) > 0:
        ax.scatter(failed['y'], failed['x'],
                  c=failure_color, s=60, marker='o', alpha=0.8,
                  edgecolors='black', linewidths=1, zorder=3)
    
    ax.set_title(title, color='white', fontsize=12, pad=3, family='DejaVu Sans')
    legend_text = f"Won: {len(successful)} | Lost: {len(failed)}"
    fig.text(0.5, 0.0, legend_text, ha='center', va='bottom',
             fontsize=10, color='white', family='DejaVu Sans')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)
    plt.close()
    
    return save_path

def _create_passes_field(
    events_df: pd.DataFrame,
    player_name: str,
    min_minute: int,
    max_minute: int,
    save_path: str,
    title: str
) -> str:
    """Create spatial field showing successful vs failed passes with arrows."""
    passes = events_df[
        (events_df['player'] == player_name) &
        (events_df['minute'] >= min_minute) &
        (events_df['minute'] <= max_minute) &
        (events_df['event_type'] == 'Pass') &
        (events_df['x'].notna()) &
        (events_df['y'].notna()) &
        (events_df['end_x'].notna()) &
        (events_df['end_y'].notna())
    ].copy()
    
    if len(passes) == 0:
        return _create_blank_field_file(save_path, title)

    pitch = VerticalPitch(
        pitch_color=BACKGROUND_COLOR,
        line_color='white',
        linewidth=2,
        pitch_type='opta'
    )
    
    fig, ax = pitch.draw(figsize=(2.5, 3.5))
    fig.set_facecolor(BACKGROUND_COLOR)
    
    success_color = '#00BFFF'
    failure_color = '#FF6B6B'

    successful = passes[passes['is_successful'] == True]
    failed = passes[passes['is_successful'] == False]

    if len(successful) > 0:
        for _, pass_event in successful.iterrows():
            ax.annotate('',
                       xy=(pass_event['end_y'], pass_event['end_x']),
                       xytext=(pass_event['y'], pass_event['x']),
                       arrowprops=dict(arrowstyle='->', color=success_color,
                                     alpha=0.9, lw=2.0, connectionstyle="arc3,rad=0.05"))

    # Failed passes drawn twice: black outline underneath for contrast, then colored on top
    if len(failed) > 0:
        for _, pass_event in failed.iterrows():
            ax.annotate('',
                       xy=(pass_event['end_y'], pass_event['end_x']),
                       xytext=(pass_event['y'], pass_event['x']),
                       arrowprops=dict(arrowstyle='->', color='black',
                                     alpha=1.0, lw=2.5, connectionstyle="arc3,rad=0.05"))
            ax.annotate('',
                       xy=(pass_event['end_y'], pass_event['end_x']),
                       xytext=(pass_event['y'], pass_event['x']),
                       arrowprops=dict(arrowstyle='->', color=failure_color,
                                     alpha=0.9, lw=1.8, connectionstyle="arc3,rad=0.05"))
    
    ax.set_title(title, color='white', fontsize=12, pad=3, family='DejaVu Sans')
    legend_text = f"Accurate: {len(successful)} | Inaccurate: {len(failed)}"
    fig.text(0.5, 0.0, legend_text, ha='center', va='bottom',
             fontsize=10, color='white', family='DejaVu Sans')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)
    plt.close()
    
    return save_path

def create_goalkeeper_analysis(
    player_name: str,
    team_name: str,
    enriched_metrics: List[Tuple[str, str]],
    player_image_path: str = None
):
    """Create goalkeeper stats table without spatial maps."""
    table_path = 'temp_goalkeeper_stats.png'
    _create_large_stats_table(
        player_name, team_name, enriched_metrics, 
        player_image_path, table_path
    )
    
    table_img = Image.open(table_path)
    table_width, table_height = table_img.size
    
    fig, ax = plt.subplots(figsize=(table_width/100, table_height/100), dpi=100)
    ax.imshow(table_img)
    ax.axis('off')
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0, hspace=0, wspace=0)
    
    os.remove(table_path)
    
    return fig

def _create_blank_field() -> Image.Image:
    """Create blank field placeholder when no data available."""
    blank = Image.new('RGB', (500, 700), color=BACKGROUND_COLOR)
    return blank

def _create_blank_field_file(save_path: str, title: str) -> str:
    """Create blank field file when no data available."""
    pitch = VerticalPitch(
        pitch_color=BACKGROUND_COLOR,
        line_color='white',
        linewidth=2,
        pitch_type='opta'
    )
    fig, ax = pitch.draw(figsize=(2.5, 3.5))
    fig.set_facecolor(BACKGROUND_COLOR)
    ax.set_title(title, color='white', fontsize=12, pad=3, family='DejaVu Sans')

    fig.text(0.5, 0.0, "No data", ha='center', va='bottom',
             fontsize=10, color='white', family='DejaVu Sans')

    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)
    plt.close()
    return save_path