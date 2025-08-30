"""
FootballDecoded Statistical Table Module - Simplified
====================================================

Clean and focused statistical table module for player analysis.
Creates professional statistical tables with spatial field visualizations.

Key Features:
- Single function interface: create_player_analysis_complete()
- External statistics calculation (no internal computation)
- Large statistical table + 4 spatial field maps (2x2 layout)
- Unified aesthetics with pass_network.py colors and styling
- Clean separation of concerns

Layout:
[LARGE STATS TABLE] | [ACTIONS 1ST] [PASSES 1ST]
                    | [ACTIONS 2ND] [PASSES 2ND]

Author: Jaime Oriol
Created: 2025 - FootballDecoded Project
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
from mplsoccer.pitch import VerticalPitch
from PIL import Image
import os
from typing import List, Tuple

# Visual configuration consistent with FootballDecoded standards
BACKGROUND_COLOR = '#313332'

def create_player_analysis_complete(
    player_name: str,
    team_name: str,
    enriched_metrics: List[Tuple[str, str]],
    events_df: pd.DataFrame,
    player_image_path: str = None
):
    """
    Create complete professional player analysis with stats table and spatial maps.
    
    Generates professional visualization combining:
    - Large enriched statistical table (left side)
    - 4 spatial field maps in 2x2 grid (right side)
    
    Features:
    - External statistics (no internal calculation)
    - Unified FootballDecoded aesthetics
    - deepskyblue for successful actions, white for failures
    - Professional layout and typography
    
    Args:
        player_name: Player name string
        team_name: Team name string
        enriched_metrics: List of (metric_name, formatted_value) tuples
        events_df: DataFrame with match events including coordinates
        player_image_path: Optional path to player image file
        
    Returns:
        matplotlib figure object
        
    Example:
        fig = create_player_analysis_complete(
            player_name='Nicolas Pépé',
            team_name='Villarreal',
            enriched_metrics=[
                ("Goals", "2"),
                ("Shots", "7/12 58%"),
                ("xG", "1.85"),
                ("Passes", "45/52 87%"),
                ("Take Ons", "8/12 67%"),
                ("xThreat", "0.45"),
                ("Minutes", "78"),
                ("Box Entries", "6")
            ],
            events_df=match_events,
            player_image_path='path/to/player.png'
        )
    """
    # Validate inputs
    if not (8 <= len(enriched_metrics) <= 12):
        raise ValueError("Must provide between 8 and 12 enriched metrics")
    
    # Create individual components
    table_path = 'temp_stats_table.png'
    spatial_paths = {}
    
    # Generate large stats table
    _create_large_stats_table(
        player_name, team_name, enriched_metrics, 
        player_image_path, table_path
    )
    
    # Generate 4 spatial field maps
    spatial_paths = _create_spatial_fields_2x2(events_df, player_name)
    
    # Load all components
    table_img = Image.open(table_path)
    
    # Load spatial field images
    field_images = {}
    for key, path in spatial_paths.items():
        if path and os.path.exists(path):
            field_images[key] = Image.open(path)
        else:
            # Create blank placeholder if no data
            field_images[key] = _create_blank_field()
    
    # Calculate combined layout dimensions
    table_width, table_height = table_img.size
    field_width, field_height = field_images['actions_1st'].size
    
    # Layout: table (left) + 2x2 field grid (right)
    fields_grid_width = field_width * 2
    fields_grid_height = field_height * 2
    
    total_width = table_width + fields_grid_width
    total_height = max(table_height, fields_grid_height)
    
    # Create combined canvas
    combined = Image.new('RGB', (total_width, total_height), color=BACKGROUND_COLOR)
    
    # Paste large table on left (centered vertically)
    table_y = (total_height - table_height) // 2
    combined.paste(table_img, (0, table_y))
    
    # Paste 4 spatial fields in 2x2 grid on right
    fields_start_x = table_width
    fields_y_offset = (total_height - fields_grid_height) // 2
    
    # Top row: Actions 1st | Passes 1st
    combined.paste(field_images['actions_1st'], (fields_start_x, fields_y_offset))
    combined.paste(field_images['passes_1st'], (fields_start_x + field_width, fields_y_offset))
    
    # Bottom row: Actions 2nd | Passes 2nd
    combined.paste(field_images['actions_2nd'], (fields_start_x, fields_y_offset + field_height))
    combined.paste(field_images['passes_2nd'], (fields_start_x + field_width, fields_y_offset + field_height))
    
    # Convert combined image to matplotlib figure
    fig, ax = plt.subplots(figsize=(total_width/100, total_height/100), dpi=100)
    ax.imshow(combined)
    ax.axis('off')
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0, hspace=0, wspace=0)
    
    # Clean up temporary files
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
    # Setup figure with proper dimensions to match 2x2 field grid height
    fig, ax = plt.subplots(figsize=(6, 8))
    fig.patch.set_facecolor(BACKGROUND_COLOR)
    ax.set_facecolor(BACKGROUND_COLOR)
    ax.set_xlim(0, 6)
    ax.set_ylim(0, len(enriched_metrics) + 3)
    ax.axis('off')
    
    # Header with player and team - ADJUSTED positioning
    ax.text(1.5, len(enriched_metrics) + 1.5, player_name, fontsize=15, color='white',
            fontweight='bold', ha='left', va='center', family='DejaVu Sans')
    ax.text(1.5, len(enriched_metrics) + 1.2, team_name, fontsize=12, color='white',
            ha='left', va='center', family='DejaVu Sans')
    
    # Player image in top left if provided - SMALLER size
    if player_image_path and os.path.exists(player_image_path):
        try:
            player_img = Image.open(player_image_path)
            player_ax = fig.add_axes([0.1, 0.83, 0.15, 0.125])
            player_ax.imshow(player_img)
            player_ax.axis('off')
        except:
            pass
    
    # Football Decoded logo in top right
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
    
    # Statistics table with alternating row backgrounds
    for i, (metric_name, metric_value) in enumerate(enriched_metrics):
        y_pos = len(enriched_metrics) - i + 0.5
        
        # Alternating row background
        if i % 2 == 0:
            rect = Rectangle((0.4, y_pos - 0.45), 5.2, 0.9, facecolor='white', alpha=0.05)
            ax.add_patch(rect)
        
        # Metric name (left)
        ax.text(0.6, y_pos, metric_name, fontsize=12, color='white',
                ha='left', va='center', family='DejaVu Sans', fontweight='bold')
        
        # Metric value (right)
        ax.text(5.2, y_pos, metric_value, fontsize=12, color='white',
                ha='right', va='center', family='DejaVu Sans')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)
    plt.close()

def _create_spatial_fields_2x2(events_df: pd.DataFrame, player_name: str) -> dict:
    """Create 4 spatial field maps for each half-period combination."""
    paths = {}
    
    # 1. Actions 1st half (minutes 1-44)
    paths['actions_1st'] = _create_actions_field(
        events_df, player_name, 1, 44, 'temp_actions_1st.png', 'Actions 1st Half'
    )
    
    # 2. Passes 1st half (minutes 1-44)  
    paths['passes_1st'] = _create_passes_field(
        events_df, player_name, 1, 44, 'temp_passes_1st.png', 'Passes 1st Half'
    )
    
    # 3. Actions 2nd half (minutes 46-90)
    paths['actions_2nd'] = _create_actions_field(
        events_df, player_name, 46, 90, 'temp_actions_2nd.png', 'Actions 2nd Half'
    )
    
    # 4. Passes 2nd half (minutes 46-90)
    paths['passes_2nd'] = _create_passes_field(
        events_df, player_name, 46, 90, 'temp_passes_2nd.png', 'Passes 2nd Half'
    )
    
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
    # Filter player events (exclude passes, include coordinates, time period)
    actions = events_df[
        (events_df['player'] == player_name) & 
        (events_df['minute'] >= min_minute) &
        (events_df['minute'] <= max_minute) &
        (events_df['x'].notna()) & 
        (events_df['y'].notna()) &
        (events_df['event_type'] != 'Pass')
    ].copy()
    
    if len(actions) == 0:
        return None  # No data for this period
    
    # Setup pitch
    pitch = VerticalPitch(
        pitch_color=BACKGROUND_COLOR,
        line_color='white', 
        linewidth=2,
        pitch_type='opta'
    )
    
    fig, ax = pitch.draw(figsize=(2.5, 3.5))
    fig.set_facecolor(BACKGROUND_COLOR)
    
    # Colors from pass_network.py
    success_color = 'deepskyblue'  # Ganadas
    failure_color = 'white'        # Perdidas
    
    # Separate successful vs failed actions
    successful = actions[actions['is_successful'] == True]
    failed = actions[actions['is_successful'] == False]
    
    # Plot successful actions (blue)
    if len(successful) > 0:
        ax.scatter(successful['y'], successful['x'], 
                  c=success_color, s=60, marker='o', alpha=0.8,
                  edgecolors='white', linewidths=1, zorder=3)
    
    # Plot failed actions (white)
    if len(failed) > 0:
        ax.scatter(failed['y'], failed['x'],
                  c=failure_color, s=60, marker='o', alpha=0.8,
                  edgecolors='black', linewidths=1, zorder=3)
    
    # Title and legend - ADJUSTED positioning (same as passes)
    ax.set_title(title, color='white', fontsize=12, pad=3, family='DejaVu Sans')
    
    # Simple legend at bottom - SAME position as passes
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
    # Filter player pass events with coordinates and time period
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
        return None  # No data for this period
    
    # Setup pitch
    pitch = VerticalPitch(
        pitch_color=BACKGROUND_COLOR,
        line_color='white',
        linewidth=2,
        pitch_type='opta'
    )
    
    fig, ax = pitch.draw(figsize=(2.5, 3.5))
    fig.set_facecolor(BACKGROUND_COLOR)
    
    # Colors from pass_network.py
    success_color = 'deepskyblue'  # Precisos
    failure_color = 'white'        # No precisos
    
    # Separate successful vs failed passes
    successful = passes[passes['is_successful'] == True]
    failed = passes[passes['is_successful'] == False]
    
    # Draw arrows for successful passes (sample to avoid clutter)
    if len(successful) > 0:
        sample_size = min(15, len(successful))
        sample_passes = successful.sample(sample_size)
        for _, pass_event in sample_passes.iterrows():
            ax.annotate('', 
                       xy=(pass_event['end_y'], pass_event['end_x']), 
                       xytext=(pass_event['y'], pass_event['x']),
                       arrowprops=dict(arrowstyle='->', color=success_color, 
                                     alpha=0.9, lw=2.0, connectionstyle="arc3,rad=0.05"))
    
    # Draw arrows for failed passes (smaller sample)
    if len(failed) > 0:
        sample_size = min(8, len(failed))
        sample_fails = failed.sample(sample_size)
        for _, pass_event in sample_fails.iterrows():
            # Black outline for visibility
            ax.annotate('', 
                       xy=(pass_event['end_y'], pass_event['end_x']), 
                       xytext=(pass_event['y'], pass_event['x']),
                       arrowprops=dict(arrowstyle='->', color='black', 
                                     alpha=1.0, lw=2.5, connectionstyle="arc3,rad=0.05"))
            # White arrow on top
            ax.annotate('', 
                       xy=(pass_event['end_y'], pass_event['end_x']), 
                       xytext=(pass_event['y'], pass_event['x']),
                       arrowprops=dict(arrowstyle='->', color=failure_color, 
                                     alpha=0.9, lw=1.8, connectionstyle="arc3,rad=0.05"))
    
    # Title and legend - ADJUSTED positioning (lower)
    ax.set_title(title, color='white', fontsize=12, pad=3, family='DejaVu Sans')
    
    # Simple legend at bottom - LOWER position
    legend_text = f"Accurate: {len(successful)} | Inaccurate: {len(failed)}"
    fig.text(0.5, 0.0, legend_text, ha='center', va='bottom',
             fontsize=10, color='white', family='DejaVu Sans')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor=BACKGROUND_COLOR)
    plt.close()
    
    return save_path

def _create_blank_field() -> Image.Image:
    """Create blank field placeholder when no data available."""
    blank = Image.new('RGB', (500, 700), color=BACKGROUND_COLOR)
    return blank