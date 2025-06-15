# ====================================================================
# FootballDecoded - Pitch Renderer Module
# ====================================================================
# Professional football pitch rendering - extracted from pass_network.py
# ====================================================================

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# ====================================================================
# PITCH CONFIGURATION
# ====================================================================

FIELD_CONFIG = {
    'length': 105, 'width': 68, 'color': 'white',
    'line_color': 'black', 'line_width': 2.5,
    'goal_color': '#333333', 'goal_width': 8.0
}

# ====================================================================
# MAIN PITCH DRAWING FUNCTION
# ====================================================================

def draw_pitch(ax):
    """
    Draw professional football pitch with all markings.
    
    Args:
        ax: Matplotlib axis object
    """
    length, width = FIELD_CONFIG['length'], FIELD_CONFIG['width']
    
    # Main pitch rectangle
    pitch = patches.Rectangle((0, 0), length, width, 
                            linewidth=0, facecolor=FIELD_CONFIG['color'])
    ax.add_patch(pitch)
    
    # All field markings
    _draw_field_lines(ax, length, width)
    _draw_penalty_areas(ax, length, width)
    _draw_goals(ax, length, width)
    
    # Outer border
    border = patches.Rectangle((0, 0), length, width,
                             linewidth=FIELD_CONFIG['line_width'],
                             edgecolor=FIELD_CONFIG['line_color'],
                             facecolor='none')
    ax.add_patch(border)

# ====================================================================
# PITCH COMPONENTS
# ====================================================================

def _draw_field_lines(ax, length: float, width: float):
    """Draw center lines and circle."""
    color, lw = FIELD_CONFIG['line_color'], FIELD_CONFIG['line_width']
    
    # Center line
    ax.plot([length/2, length/2], [0, width], color=color, linewidth=lw)
    
    # Center circle
    center_circle = patches.Circle((length/2, width/2), 9.15, 
                                  linewidth=lw, edgecolor=color, facecolor='none')
    ax.add_patch(center_circle)
    
    # Center spot
    ax.plot(length/2, width/2, 'o', color=color, markersize=4)

def _draw_penalty_areas(ax, length: float, width: float):
    """Draw penalty areas and goal areas."""
    color, lw = FIELD_CONFIG['line_color'], FIELD_CONFIG['line_width']
    
    # Penalty area dimensions
    penalty_length, penalty_width = 16.5, 40.32
    small_length, small_width = 5.5, 18.32
    penalty_y = (width - penalty_width) / 2
    small_y = (width - small_width) / 2
    
    # Draw penalty areas (both sides)
    for side in [0, length]:
        x_offset = penalty_length if side == 0 else length - penalty_length
        ax.plot([x_offset, x_offset], [penalty_y, penalty_y + penalty_width], color=color, linewidth=lw)
        ax.plot([side, x_offset], [penalty_y, penalty_y], color=color, linewidth=lw)
        ax.plot([side, x_offset], [penalty_y + penalty_width, penalty_y + penalty_width], color=color, linewidth=lw)
    
    # Draw goal areas (both sides)
    for side in [0, length]:
        x_offset = small_length if side == 0 else length - small_length
        ax.plot([x_offset, x_offset], [small_y, small_y + small_width], color=color, linewidth=lw)
        ax.plot([side, x_offset], [small_y, small_y], color=color, linewidth=lw)
        ax.plot([side, x_offset], [small_y + small_width, small_y + small_width], color=color, linewidth=lw)
    
    # Penalty arcs
    penalty_spot = 11.0
    semicircle_radius = 9.15
    distance_to_edge = penalty_length - penalty_spot
    
    if distance_to_edge < semicircle_radius:
        angle_rad = np.arccos(distance_to_edge / semicircle_radius)
        angle_deg = np.degrees(angle_rad)
        
        # Left penalty arc
        semicircle_l = patches.Arc((penalty_spot, width/2), 
                                  semicircle_radius*2, semicircle_radius*2,
                                  angle=0, theta1=-angle_deg, theta2=angle_deg, 
                                  linewidth=lw, edgecolor=color, fill=False)
        ax.add_patch(semicircle_l)
        
        # Right penalty arc
        semicircle_r = patches.Arc((length - penalty_spot, width/2), 
                                  semicircle_radius*2, semicircle_radius*2,
                                  angle=0, theta1=180-angle_deg, theta2=180+angle_deg, 
                                  linewidth=lw, edgecolor=color, fill=False)
        ax.add_patch(semicircle_r)
    
    # Penalty spots
    ax.plot(penalty_spot, width/2, 'o', color=color, markersize=4)
    ax.plot(length - penalty_spot, width/2, 'o', color=color, markersize=4)

def _draw_goals(ax, length: float, width: float):
    """Draw goal posts."""
    goal_width = 7.32
    goal_y = (width - goal_width) / 2
    color, lw = FIELD_CONFIG['goal_color'], FIELD_CONFIG['goal_width']
    
    # Goal posts
    ax.plot([0, 0], [goal_y, goal_y + goal_width], color=color, linewidth=lw, solid_capstyle='round')
    ax.plot([length, length], [goal_y, goal_y + goal_width], color=color, linewidth=lw, solid_capstyle='round')

# ====================================================================
# UTILITY FUNCTIONS
# ====================================================================

def setup_pitch_axes(ax, title: str = None):
    """
    Configure axes for pitch visualization.
    
    Args:
        ax: Matplotlib axis object
        title: Optional title for the pitch
    """
    ax.set_xlim(-5, 110)
    ax.set_ylim(-16, 68)
    ax.set_aspect('equal')
    ax.axis('off')
    
    if title:
        ax.text(52.5, 75, title, ha='center', va='center', 
               fontsize=16, fontweight='bold', family='DejaVu Sans')