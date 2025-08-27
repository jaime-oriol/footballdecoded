# shot_map_report.py

"""
FootballDecoded Shot Map Report Visualization Module
====================================================

Comprehensive shot analysis visualization system for dual-team comparison.
Creates professional shot maps with integrated statistics and xG analysis.

Key Features:
- Dual-pitch shot comparison (side-by-side teams)
- Comprehensive shot marker system (foot, header, set-piece)
- Result-based styling (goal, saved, missed/blocked)
- xG color coding with unified colormap
- Advanced legend system with shot type classification
- Statistical integration with match context
- Special case highlighting (low xG goals, high xG misses)

Shot Classification System:
- Marker Types: Hexagon (foot), Circle (header), Square (set-piece)
- Result Styling: Goals (white outline + double border), Saves (grey outline), Misses (dark grey, reduced opacity)
- Special Cases: Low xG goals (lime secondary border), High xG misses (crimson outline)
- xG Color Mapping: 0.0-1.0 scale using unified node colormap

Technical Implementation:
- Half-pitch visualization for goal-focused analysis
- Coordinate transformation (Opta to matplotlib)
- Player initials extraction and positioning
- Statistical calculation and formatting
- Logo integration and metadata display

Visual Design:
- Consistent with FootballDecoded design language
- Professional sports broadcast aesthetics
- Clear statistical hierarchy and data visualization
- Comprehensive legend for shot interpretation

Author: Jaime Oriol
Created: 2025 - FootballDecoded Project
Coordinate System: Half-pitch Opta (attacking direction)
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.colors as mcolors
from mplsoccer.pitch import VerticalPitch
from PIL import Image

# Configuración visual unificada
BACKGROUND_COLOR = '#313332'
PITCH_COLOR = '#313332'

def plot_shot_report(csv_path, home_logo_path=None, away_logo_path=None, season='2024-2025'):
    """
    Create dual-pitch shot report visualization with unified aesthetics.
    
    Args:
        csv_path: Path to shots CSV file
        home_logo_path: Path to home team logo (PNG with transparency)
        away_logo_path: Path to away team logo (PNG with transparency)
        season: Season string
    """
    # Font unificado
    font = 'DejaVu Sans'
    
    # Colormap unificado
    node_cmap = mcolors.LinearSegmentedColormap.from_list("", [
        'deepskyblue', 'cyan', 'lawngreen', 'yellow', 
        'gold', 'lightpink', 'tomato'
    ])
    
    # Read data
    shots_df = pd.read_csv(csv_path)
    
    # Get teams
    teams = shots_df['team'].unique()
    if len(teams) != 2:
        return print("Error: Need exactly 2 teams in data")
    
    home_team, away_team = teams[0], teams[1]
    
    # Separate shots by team
    home_shots = shots_df[shots_df['team'] == home_team].copy()
    away_shots = shots_df[shots_df['team'] == away_team].copy()
    
    # Add initials
    def get_initials(name):
        parts = name.split()
        if len(parts) == 1:
            return parts[0][:2].upper()
        return ''.join([p[0].upper() for p in parts[:2]])
    
    home_shots['initials'] = home_shots['player'].apply(get_initials)
    away_shots['initials'] = away_shots['player'].apply(get_initials)
    
    # Calculate stats
    def calc_stats(df):
        shots = len(df)
        goals = df['is_goal'].sum()
        xg = df['xg'].sum()
        xg_per_shot = xg / shots if shots > 0 else 0
        goal_per_shot = goals / shots if shots > 0 else 0
        xg_perf = goals - xg
        
        goal_df = df[df['is_goal'] == True]
        miss_df = df[df['is_goal'] == False]
        
        low_xg_goal = goal_df['xg'].min() if not goal_df.empty else None
        high_xg_miss = miss_df['xg'].max() if not miss_df.empty else None
        
        return {
            'shots': shots,
            'goals': goals,
            'xg': xg,
            'xg_per_shot': xg_per_shot,
            'goal_per_shot': goal_per_shot,
            'xg_perf': xg_perf,
            'low_xg_goal': low_xg_goal,
            'high_xg_miss': high_xg_miss
        }
    
    h_stats = calc_stats(home_shots)
    a_stats = calc_stats(away_shots)
    
    # Plot setup
    mpl.rcParams.update({'xtick.color': 'w', 'ytick.color': 'w'})
    
    pitch = VerticalPitch(half=True, pitch_color=PITCH_COLOR, line_color='white', 
                          linewidth=1, pitch_type='opta')
    fig, ax = pitch.grid(nrows=1, ncols=2, title_height=0.03, grid_height=0.51, 
                         endnote_height=0, axis=False)
    fig.set_size_inches(12, 7)
    fig.set_facecolor(BACKGROUND_COLOR)
    
    # Set limits
    for i in range(2):
        ax['pitch'][i].set_xlim((8.33, 91.67))
        ax['pitch'][i].set_ylim((62.5, 100))
        for axis in ['left', 'right', 'bottom']:
            ax['pitch'][i].spines[axis].set_visible(True)
            ax['pitch'][i].spines[axis].set_color('grey')
    
    # Plot function
    def plot_shots(shots_df, pitch_num):
        for _, shot in shots_df.iterrows():
            # Marker type
            if shot['body_part'] == 'Head':
                marker, s, s_delta = 'o', 250, 150
            elif shot.get('situation', '') in ['DirectFreeKick', 'Penalty']:
                marker, s, s_delta = 's', 175, 125
            else:
                marker, s, s_delta = 'h', 300, 150
            
            # Style based on result usando 'type' field
            if shot['type'] == 'Goal':
                lw, alpha, edge, fontweight, zorder = 2, 1, 'w', 'bold', 4
                s -= 25
                edge_g = 'lime' if shot['xg'] <= 0.05 else 'w'
            elif shot['type'] == 'SavedShot':
                lw, alpha, edge, fontweight, zorder = 2.0, 1, 'grey', 'regular', 2
                edge_g = 'w'
            else:  # MissedShots
                lw, alpha, edge, fontweight, zorder = 0.5, 0.7, 'darkgrey', 'regular', 1
                edge_g = 'w'
                if shot['xg'] >= 0.6:
                    edge = 'crimson'
            
            # Iniciales siempre en negro
            textcolor = 'k'
            
            # Convert coordinates
            x = shot['x']  # Already 0-100
            y = 100 - shot['y']  # Flip Y
            
            # Plot shot usando colormap unificado (0 a 1)
            p1 = ax['pitch'][pitch_num].scatter(
                y, x, marker=marker, s=s, alpha=alpha, c=shot['xg'], 
                lw=lw, edgecolors=edge, vmin=-0.04, vmax=1.0, 
                cmap=node_cmap, zorder=zorder
            )
            
            # Double outline for goals
            if shot['type'] == 'Goal':
                ax['pitch'][pitch_num].scatter(
                    y, x, marker=marker, s=s + s_delta, alpha=1, 
                    c=PITCH_COLOR, edgecolors=edge_g, zorder=zorder - 1
                )
            
            # Player initials
            ax['pitch'][pitch_num].text(
                y, x - 0.1, shot['initials'], color=textcolor, 
                fontsize=7, ha='center', va='center', 
                fontweight=fontweight, zorder=zorder, fontfamily=font
            )
        
        return p1 if len(shots_df) > 0 else None
    
    # Plot both teams
    p1 = plot_shots(home_shots, 0)
    plot_shots(away_shots, 1)
    
    # Stats text
    def format_stat(value, is_float=True, sign=False):
        if value is None:
            return '-'
        if sign and value > 0:
            return f"+{value:.2f}" if is_float else f"+{value}"
        return f"{value:.2f}" if is_float else str(value)
    
    # Home stats
    fig.text(0.07, 0.27, "Shots:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.07, 0.241, "xG/shot:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.17, 0.27, "Goals/shot:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.17, 0.24, "xG Performance:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.34, 0.27, "L. xG Goal:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.34, 0.24, "H. xG Miss:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    
    fig.text(0.13, 0.27, format_stat(h_stats['shots'], False), fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.13, 0.24, format_stat(h_stats['xg_per_shot']), fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.287, 0.27, format_stat(h_stats['goal_per_shot']), fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.285, 0.24, format_stat(h_stats['xg_perf'], sign=True), fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.42, 0.27, format_stat(h_stats['low_xg_goal']), fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.42, 0.24, format_stat(h_stats['high_xg_miss']), fontweight="regular", fontsize=10, color='w', fontfamily=font)
    
    # Away stats
    fig.text(0.554, 0.27, "Shots:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.554, 0.241, "xG/shot:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.654, 0.27, "Goals/shot:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.654, 0.24, "xG Performance:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.824, 0.27, "L. xG Goal:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    fig.text(0.824, 0.24, "H. xG Miss:", fontweight="bold", fontsize=10, color='w', fontfamily=font)
    
    fig.text(0.614, 0.27, format_stat(a_stats['shots'], False), fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.614, 0.24, format_stat(a_stats['xg_per_shot']), fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.771, 0.27, format_stat(a_stats['goal_per_shot']), fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.769, 0.24, format_stat(a_stats['xg_perf'], sign=True), fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.904, 0.27, format_stat(a_stats['low_xg_goal']), fontweight="regular", fontsize=10, color='w', fontfamily=font)
    fig.text(0.904, 0.24, format_stat(a_stats['high_xg_miss']), fontweight="regular", fontsize=10, color='w', fontfamily=font)
    
    # Colorbar con colormap unificado (0 a 1)
    if p1:
        cb_ax = fig.add_axes([0.57, 0.152, 0.35, 0.03])
        cbar = fig.colorbar(p1, cax=cb_ax, orientation='horizontal')
        cbar.outline.set_edgecolor('w')
        cbar.set_label(" xG", loc="left", color='w', fontweight='bold', labelpad=-28.5)
    
    # Legend con lógica de campo exacta
    legend_ax = fig.add_axes([0.055, 0.065, 0.5, 0.14])
    legend_ax.axis("off")
    legend_ax.set_xlim([0, 5])
    legend_ax.set_ylim([0, 1])
    
    # Color verde unificado para columna izquierda
    legend_green = node_cmap(0.3)
    
    # Marker types
    legend_ax.scatter(0.2, 0.8, marker='h', s=300, c=PITCH_COLOR, edgecolors='w')
    legend_ax.scatter(0.2, 0.5, marker='o', s=250, c=PITCH_COLOR, edgecolors='w')
    legend_ax.scatter(0.2, 0.2, marker='s', s=150, c=PITCH_COLOR, edgecolors='w')
    legend_ax.text(0.37, 0.74, "Foot", color="w", fontfamily=font)
    legend_ax.text(0.37, 0.44, "Header", color="w", fontfamily=font)
    legend_ax.text(0.37, 0.14, "Set-Piece", color="w", fontfamily=font)
    
    # Result types - reflejan lógica exacta del campo
    # Goal: verde + borde blanco + lw=2 + double outline
    legend_ax.scatter(1.3, 0.8, marker='h', s=250, c=legend_green, edgecolors='w', lw=2, zorder=2)
    legend_ax.scatter(1.3, 0.8, marker='h', s=400, c=PITCH_COLOR, edgecolors='w', zorder=1)
    # Saved: verde + borde gris + lw=1.5
    legend_ax.scatter(1.3, 0.5, marker='h', s=300, c=legend_green, edgecolors='grey', lw=2, alpha=1)
    # Missed: verde + borde darkgrey + lw=0.5  
    legend_ax.scatter(1.3, 0.2, marker='h', s=300, c=legend_green, edgecolors='darkgrey', lw=0.5, alpha=0.7)
    legend_ax.text(1.47, 0.74, "Goal", color="w", fontfamily=font)
    legend_ax.text(1.47, 0.44, "Saved", color="w", fontfamily=font)
    legend_ax.text(1.47, 0.14, "Missed or Blocked", color="w", fontfamily=font)
    
    # Special cases con colores corregidos
    legend_ax.scatter(3, 0.8, marker='h', s=300, c=node_cmap(0.2), edgecolors='w', lw=1.5, alpha=1)
    # Low xG Goal con double outline: azul + blanco + rojo
    legend_ax.scatter(3, 0.5, marker='h', s=250, c=node_cmap(0.0), edgecolors='w', lw=1.5, zorder=2)
    legend_ax.scatter(3, 0.5, marker='h', s=400, c='red', edgecolors='red', zorder=1)
    # High xG Miss: colormap alto + borde negro
    legend_ax.scatter(3, 0.2, marker='h', s=300, c=node_cmap(0.9), edgecolors='black', lw=1.5, alpha=1)
    legend_ax.text(3.17, 0.74, "Own Goal", color="w", fontfamily=font)
    legend_ax.text(3.17, 0.44, "Low xG (<0.05) Goal", color="w", fontfamily=font)
    legend_ax.text(3.17, 0.14, "High xG (>0.60) Miss", color="w", fontfamily=font)
    
    # Title
    league = "ESP-La Liga"  # Extract from path if needed
    title_text = "Shot Map"
    subtitle_text = f"{home_team} {h_stats['goals']}-{a_stats['goals']} {away_team}"
    subsubtitle_text = f"{league} | {season}"
    
    fig.text(0.5, 0.89, title_text, ha='center', fontweight="bold", fontsize=23, color='w', fontfamily=font)
    fig.text(0.5, 0.835, subtitle_text, ha='center', fontweight="regular", fontsize=21, color='w', fontfamily=font)
    fig.text(0.5, 0.79, subsubtitle_text, ha='center', fontweight="regular", fontsize=17, color='w', fontfamily=font)
    
    # Logos
    if home_logo_path:
        ax_logo = fig.add_axes([0.195, 0.75, 0.2, 0.2])
        ax_logo.axis("off")
        try:
            img = Image.open(home_logo_path)
            ax_logo.imshow(img)
        except:
            pass
    
    if away_logo_path:
        ax_logo = fig.add_axes([0.61, 0.75, 0.2, 0.2])
        ax_logo.axis("off")
        try:
            img = Image.open(away_logo_path)
            ax_logo.imshow(img)
        except:
            pass
    
    # Footer unificado
    fig.text(0.05, 0.02, "Created by Jaime Oriol", fontweight='bold', fontsize=10, color="white", fontfamily=font)
    fig.text(0.8, 0.02, "Football Decoded", fontweight='bold', fontsize=14, color="white", fontfamily=font)
    
    plt.tight_layout()
    return fig