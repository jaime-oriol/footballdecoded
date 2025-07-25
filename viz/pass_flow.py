import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mplsoccer.pitch import VerticalPitch
from collections import Counter
from PIL import Image

def get_zone_jdp_custom(x, y):
    """Identifica zona usando sistema jdp_custom (19 zonas)."""
    if pd.isna(x) or pd.isna(y):
        return np.nan
    
    box_x_ratio, box_y_ratio = 0.17, 0.21
    
    if x <= box_x_ratio * 100:
        if y < box_y_ratio * 100:
            return 2
        elif y <= (1-box_y_ratio) * 100:
            return 1
        else:
            return 0
    elif x <= 50:
        if y < box_y_ratio * 100:
            return 7
        elif y < 36.75:
            return 6
        elif y <= 63.25:
            return 5
        elif y <= (1-box_y_ratio) * 100:
            return 4
        else:
            return 3
    elif x < 66.67:
        if y < box_y_ratio * 100:
            return 10
        elif y < 36.75:
            return 12
        elif y <= 63.25:
            return 9
        elif y <= (1-box_y_ratio) * 100:
            return 11
        else:
            return 8
    elif x < (1-box_x_ratio) * 100:
        if y < box_y_ratio * 100:
            return 15
        elif y < 36.75:
            return 12
        elif y <= 63.25:
            return 14
        elif y <= (1-box_y_ratio) * 100:
            return 11
        else:
            return 13
    else:
        if y < box_y_ratio * 100:
            return 18
        elif y <= (1-box_y_ratio) * 100:
            return 17
        else:
            return 16

def get_zone_center(zone_id):
    """Retorna centro de zona para dibujar líneas."""
    box_x_ratio, box_y_ratio = 0.17, 0.21
    
    centers = {
        0: (box_x_ratio * 50, (1 + (1-box_y_ratio)) * 50),
        1: (box_x_ratio * 50, ((1-box_y_ratio) + box_y_ratio) * 50),
        2: (box_x_ratio * 50, box_y_ratio * 50),
        3: ((box_x_ratio + 0.5) * 50, ((1-box_y_ratio) + 1) * 50),
        4: ((box_x_ratio + 0.5) * 50, ((1-box_y_ratio) + 0.6325) * 50),
        5: ((box_x_ratio + 0.5) * 50, (0.3675 + 0.6325) * 50),
        6: ((box_x_ratio + 0.5) * 50, (0.3675 + box_y_ratio) * 50),
        7: ((box_x_ratio + 0.5) * 50, box_y_ratio * 50),
        8: (((2/3) + 0.5) * 50, (1 + (1-box_y_ratio)) * 50),
        9: (((2/3) + 0.5) * 50, (0.6325 + 0.3675) * 50),
        10: (((2/3) + 0.5) * 50, box_y_ratio * 50),
        11: (((1-box_x_ratio) + 0.5) * 50, (0.6325 + (1-box_y_ratio)) * 50),
        12: (((1-box_x_ratio) + 0.5) * 50, (0.3675 + box_y_ratio) * 50),
        13: (((2/3) + (1-box_x_ratio)) * 50, (1 + (1-box_y_ratio)) * 50),
        14: (((2/3) + (1-box_x_ratio)) * 50, (0.6325 + 0.3675) * 50),
        15: (((2/3) + (1-box_x_ratio)) * 50, box_y_ratio * 50),
        16: ((1 + (1-box_x_ratio)) * 50, (1 + (1-box_y_ratio)) * 50),
        17: ((1 + (1-box_x_ratio)) * 50, (box_y_ratio + (1-box_y_ratio)) * 50),
        18: ((1 + (1-box_x_ratio)) * 50, box_y_ratio * 50)
    }
    return centers.get(zone_id, (50, 50))

def add_pitch_zones(ax):
    """Dibuja líneas de zona jdp_custom."""
    box_x_ratio, box_y_ratio = 0.17, 0.21
    
    lines = [
        ([box_y_ratio * 100] * 2, [(box_x_ratio + 0.001) * 100, 49.9]),
        ([box_y_ratio * 100] * 2, [50.1, (1 - box_x_ratio - 0.001) * 100]),
        ([(1 - box_y_ratio) * 100] * 2, [(box_x_ratio + 0.001) * 100, 49.9]),
        ([(1 - box_y_ratio) * 100] * 2, [50.1, (1 - box_x_ratio - 0.001) * 100]),
        ([36.75] * 2, [(box_x_ratio + 0.001) * 100, 49.9]),
        ([36.75] * 2, [50.1, (1 - box_x_ratio - 0.001) * 100]),
        ([63.25] * 2, [(box_x_ratio + 0.001) * 100, 49.9]),
        ([63.25] * 2, [50.1, (1 - box_x_ratio - 0.001) * 100]),
        ([0.1, (box_y_ratio - 0.001) * 100], [box_x_ratio * 100] * 2),
        ([(1 - box_y_ratio + 0.001) * 100, 99.9], [box_x_ratio * 100] * 2),
        ([0.1, (box_y_ratio - 0.001) * 100], [(1 - box_x_ratio) * 100] * 2),
        ([(1 - box_y_ratio + 0.001) * 100, 99.9], [(1 - box_x_ratio) * 100] * 2),
        ([0.1, (box_y_ratio - 0.001) * 100], [66.67] * 2),
        ([36.75, 63.25], [66.67] * 2),
        ([99.9, (1 - box_y_ratio + 0.001) * 100], [66.67] * 2)
    ]
    
    for line in lines:
        ax.plot(line[0], line[1], color='grey', alpha=0.3, lw=1, linestyle='--')

def plot_pass_flow(csv_path, home_logo_path=None, away_logo_path=None, season='2024-2025'):
    """Crea visualización de flujo de pases con sistema jdp_custom."""
    passes_df = pd.read_csv(csv_path)
    passes_df = passes_df.dropna(subset=['x', 'y', 'end_x', 'end_y'])
    
    teams = passes_df['team'].unique()
    if len(teams) != 2:
        return print("Error: Need exactly 2 teams")
    
    home_team, away_team = teams[0], teams[1]
    
    passes_df['start_zone'] = passes_df.apply(lambda r: get_zone_jdp_custom(r['x'], r['y']), axis=1)
    passes_df['end_zone'] = passes_df.apply(lambda r: get_zone_jdp_custom(r['end_x'], r['end_y']), axis=1)
    passes_df = passes_df.dropna(subset=['start_zone', 'end_zone'])
    
    zone_popularity = {}
    for team in teams:
        team_passes = passes_df[passes_df['team'] == team]
        team_popularity = {}
        
        for start_zone in team_passes['start_zone'].unique():
            zone_passes = team_passes[team_passes['start_zone'] == start_zone]
            end_zones = Counter(zone_passes['end_zone'].values)
            
            if start_zone in end_zones and len(end_zones) > 1:
                del end_zones[start_zone]
            elif start_zone in end_zones and len(end_zones) == 1:
                continue
                
            if end_zones:
                team_popularity[start_zone] = end_zones
        
        zone_popularity[team] = team_popularity
    
    pitch = VerticalPitch(pitch_color='#313332', pitch_type='opta', line_color='white', linewidth=1)
    fig, ax = pitch.grid(nrows=1, ncols=2, title_height=0.17, grid_height=0.65, 
                         endnote_height=0.12, axis=False)
    fig.set_size_inches(8.5, 8.5)
    fig.set_facecolor('#313332')
    
    add_pitch_zones(ax['pitch'][0])
    add_pitch_zones(ax['pitch'][1])
    
    home_cmap, away_cmap = plt.cm.Oranges, plt.cm.Blues
    cmaps = [home_cmap, away_cmap]
    
    for idx, (team_connections, team) in enumerate([(zone_popularity[home_team], home_team),
                                                    (zone_popularity[away_team], away_team)]):
        for start_zone, end_zones in team_connections.items():
            most_common = end_zones.most_common(1)[0]
            end_zone, count = most_common
            
            start_x, start_y = get_zone_center(start_zone)
            end_x, end_y = get_zone_center(end_zone)
            
            color_intensity = min(1, count / 15)
            color = cmaps[idx](color_intensity)
            
            pitch.lines(start_x, start_y, end_x, end_y, lw=10, comet=True,
                       ax=ax['pitch'][idx], color=color, transparent=True,
                       alpha=0.3, zorder=count)
            
            pitch.scatter(end_x, end_y, s=100, c=[color], zorder=count,
                         ax=ax['pitch'][idx])
    
    title_text = f"La Liga - {season}"
    subtitle_text = f"{home_team} vs {away_team}"
    subsubtitle_text = "Pass Flow - Most Frequent Inter-zone Passes"
    
    fig.text(0.5, 0.93, title_text, ha='center', fontweight="bold", fontsize=20, color='w')
    fig.text(0.5, 0.882, subtitle_text, ha='center', fontweight="bold", fontsize=18, color='w')
    fig.text(0.5, 0.84, subsubtitle_text, ha='center', fontweight="regular", fontsize=13.5, color='w')
    
    if home_logo_path:
        ax_logo = fig.add_axes([0.07, 0.825, 0.14, 0.14])
        ax_logo.axis("off")
        ax_logo.set_facecolor('#313332')
        try:
            img = Image.open(home_logo_path)
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (49, 51, 50))
                background.paste(img, mask=img.split()[3])
                ax_logo.imshow(background)
            else:
                ax_logo.imshow(img)
        except:
            pass
    
    if away_logo_path:
        ax_logo = fig.add_axes([0.79, 0.825, 0.14, 0.14])
        ax_logo.axis("off")
        ax_logo.set_facecolor('#313332')
        try:
            img = Image.open(away_logo_path)
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (49, 51, 50))
                background.paste(img, mask=img.split()[3])
                ax_logo.imshow(background)
            else:
                ax_logo.imshow(img)
        except:
            pass
    
    ax_arrow = fig.add_axes([0.47, 0.17, 0.06, 0.6])
    ax_arrow.set_xlim(0, 1)
    ax_arrow.set_ylim(0, 1)
    ax_arrow.axis("off")
    ax_arrow.arrow(0.65, 0.2, 0, 0.58, color="w", width=0.001,
                   head_width=0.1, head_length=0.02)
    ax_arrow.text(0.495, 0.48, "Direction of play", ha="center", va="center",
                  fontsize=10, color="w", fontweight="regular", rotation=90)
    
    # Leyendas separadas por equipo
    legend_ax_1 = fig.add_axes([0.055, 0.07, 0.4, 0.09])
    legend_ax_1.set_xlim([0, 8])
    legend_ax_1.set_ylim([-0.5, 1])
    legend_ax_1.axis("off")
    
    legend_ax_2 = fig.add_axes([0.545, 0.07, 0.4, 0.09])
    legend_ax_2.set_xlim([0, 8])
    legend_ax_2.set_ylim([-0.5, 1])
    legend_ax_2.axis("off")
    
    for idx, pass_count in enumerate(np.arange(1, 16, 2)):
        ypos = 0.38 if idx % 2 == 0 else 0.62
        xpos = idx / 1.4 + 1.5
        text_color = '#313332' if idx <= 2 else 'w'
        
        color_1 = home_cmap(min(1, pass_count / 15))
        legend_ax_1.scatter(xpos, ypos, marker='H', s=550, color=color_1, edgecolors='w', lw=0.5)
        legend_ax_1.text(xpos, ypos, pass_count, color=text_color, ha="center", va="center", fontsize=9)
        
        color_2 = away_cmap(min(1, pass_count / 15))
        legend_ax_2.scatter(xpos, ypos, marker='H', s=550, color=color_2, edgecolors='w', lw=0.5)
        legend_ax_2.text(xpos, ypos, pass_count, color=text_color, ha="center", va="center", fontsize=9)
    
    legend_ax_1.text(4, -0.2, "Pass Count", color='w', ha="center", va="center", fontsize=9)
    legend_ax_2.text(4, -0.2, "Pass Count", color='w', ha="center", va="center", fontsize=9)
    
    ax_stats = fig.add_axes([0.05, 0.02, 0.9, 0.04])
    ax_stats.axis('off')
    
    home_total = len(passes_df[passes_df['team'] == home_team])
    away_total = len(passes_df[passes_df['team'] == away_team])
    
    stats_text = f"Total passes: {home_team} {home_total} | {away_team} {away_total}"
    ax_stats.text(0.5, 0.5, stats_text, ha='center', va='center',
                 color='white', fontsize=9)
    
    plt.tight_layout()
    return fig