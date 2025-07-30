#!/usr/bin/env python3

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import font_manager
from mplsoccer import PyPizza
import seaborn as sns
from PIL import Image
import warnings
warnings.filterwarnings('ignore')

class HybridPizzaSwarm:
    """
    Hybrid pizza chart: raw values + percentile labels + swarm distribution
    """
    
    def __init__(self, df, background_color='#313332'):
        self.df = df
        self.bg_color = background_color
        
    def create_chart(self, player1_id, player2_id=None, metrics_config=None, 
                    title_template="Forward Template", comparison_desc="", 
                    player1_color='#1A78CF', player2_color='coral', figsize=(11, 11)):
        """
        Create hybrid pizza with swarm background
        
        Args:
            player1_id: unique_player_id for primary player
            player2_id: unique_player_id for comparison (optional)
            metrics_config: dict with 'metrics' and 'titles'
            title_template: Template name (e.g., "Centre Mid Template")
            comparison_desc: Description text for comparison group
            player1_color: Primary player color
            player2_color: Comparison player color
            figsize: Figure size
        """
        # Get player data
        p1_data = self._get_player_data(player1_id)
        p2_data = self._get_player_data(player2_id) if player2_id else None
        
        if p1_data is None:
            raise ValueError(f"Player {player1_id} not found")
            
        # Extract metrics
        metrics = metrics_config['metrics']
        titles = metrics_config['titles']
        
        # Get raw values and percentiles
        p1_values, p1_pcts = self._extract_values_and_pcts(p1_data, metrics)
        p2_values, p2_pcts = None, None
        if p2_data is not None:
            p2_values, p2_pcts = self._extract_values_and_pcts(p2_data, metrics)
        
        # Get metric ranges from full dataset
        ranges = self._calculate_ranges(metrics)
        
        # Create figure
        fig = plt.figure(figsize=figsize, facecolor=self.bg_color)
        
        # Add swarm plots in background
        self._add_swarm_background(fig, metrics, titles, ranges)
        
        # Add pizza chart overlay
        pizza_ax = fig.add_axes([0.09, 0.065, 0.82, 0.82], projection='polar')
        self._create_pizza_overlay(pizza_ax, p1_values, p1_pcts, p2_values, p2_pcts, 
                                  ranges, player1_color, player2_color)
        
        # Add headers and info
        self._add_headers(fig, p1_data, p2_data, title_template, comparison_desc,
                         player1_color, player2_color)
        
        # Add footer
        fig.text(0.5, 0.02, "data: fbref via footballdecoded | viz: custom hybrid chart",
                fontstyle="italic", ha="center", fontsize=9, color="white")
        
        return fig
    
    def _get_player_data(self, player_id):
        """Get player row by unique_player_id"""
        if player_id is None:
            return None
        mask = self.df['unique_player_id'] == player_id
        return self.df[mask].iloc[0] if mask.any() else None
    
    def _extract_values_and_pcts(self, player_data, metrics):
        """Extract raw values and percentiles for metrics"""
        values, pcts = [], []
        
        for metric in metrics:
            # Raw value
            val = player_data.get(metric, np.nan)
            if pd.isna(val):
                values.append(0)
            else:
                values.append(float(val))
            
            # Percentile
            pct_col = f"{metric}_pct"
            pct = player_data.get(pct_col, np.nan)
            if pd.isna(pct):
                pcts.append(50)
            else:
                pcts.append(int(pct))
            
        return values, pcts
    
    def _calculate_ranges(self, metrics):
        """Calculate min/max ranges for each metric"""
        ranges = []
        for metric in metrics:
            if metric in self.df.columns:
                valid_vals = self.df[metric].dropna()
                if len(valid_vals) > 0:
                    ranges.append((valid_vals.min(), valid_vals.max()))
                else:
                    ranges.append((0, 1))
            else:
                ranges.append((0, 1))
        return ranges
    
    def _add_swarm_background(self, fig, metrics, titles, ranges):
        """Add swarm plots as background layer"""
        n_metrics = len(metrics)
        angles = np.linspace(0, 2*np.pi, n_metrics, endpoint=False)
        
        # Create swarm for each metric
        for i, (metric, title, (min_val, max_val)) in enumerate(zip(metrics, titles, ranges)):
            if metric not in self.df.columns:
                continue
                
            # Get metric values
            values = self.df[metric].dropna()
            if len(values) == 0:
                continue
            
            # Normalize to 0-1 for plotting
            norm_values = (values - min_val) / (max_val - min_val + 1e-10)
            
            # Create radial positions with jitter
            angle = angles[i]
            n_points = len(norm_values)
            
            # Add angular jitter
            angle_jitter = np.random.normal(0, 0.02, n_points)
            point_angles = angle + angle_jitter
            
            # Radial positions (0.15 to 0.85 of radius)
            radial_positions = 0.15 + norm_values * 0.7
            
            # Convert to x,y
            x = 0.5 + radial_positions * np.cos(point_angles + np.pi/2) * 0.45
            y = 0.48 + radial_positions * np.sin(point_angles + np.pi/2) * 0.45
            
            # Plot swarm points
            ax_swarm = fig.add_axes([0, 0, 1, 1])
            ax_swarm.scatter(x, y, s=15, alpha=0.3, color='grey', edgecolors='none')
            ax_swarm.set_xlim(0, 1)
            ax_swarm.set_ylim(0, 1)
            ax_swarm.axis('off')
    
    def _create_pizza_overlay(self, ax, p1_vals, p1_pcts, p2_vals, p2_pcts, 
                             ranges, color1, color2):
        """Create pizza chart with raw values and percentile labels"""
        # Normalize values to 0-100 scale for pizza
        norm_p1_vals = []
        norm_p2_vals = [] if p2_vals else None
        
        for i, (val, (min_r, max_r)) in enumerate(zip(p1_vals, ranges)):
            norm_val = ((val - min_r) / (max_r - min_r + 1e-10)) * 100
            norm_p1_vals.append(norm_val)
            
            if p2_vals:
                val2 = p2_vals[i]
                norm_val2 = ((val2 - min_r) / (max_r - min_r + 1e-10)) * 100
                norm_p2_vals.append(norm_val2)
        
        # Create pizza
        baker = PyPizza(
            params=[''] * len(p1_vals),  # Empty params, we'll add custom labels
            background_color=self.bg_color,
            straight_line_color="#FFFFFF",
            straight_line_lw=1,
            last_circle_color="#FFFFFF",
            last_circle_lw=1,
            other_circle_lw=0.5,
            other_circle_color="#666666",
            inner_circle_size=20
        )
        
        # Make pizza
        if norm_p2_vals:
            baker.make_pizza(
                norm_p1_vals,
                compare_values=norm_p2_vals,
                ax=ax,
                color_blank_space=['#000000', '#000000'],
                slice_colors=[color1] * len(p1_vals),
                blank_alpha=0.1,
                kwargs_slices=dict(edgecolor="#FFFFFF", zorder=2, linewidth=1.5, alpha=0.8),
                kwargs_compare=dict(facecolor=color2, edgecolor="#FFFFFF", zorder=3, 
                                  linewidth=1.5, alpha=0.8),
                kwargs_params=dict(fontsize=0),  # Hide param labels
                kwargs_values=dict(fontsize=0)   # Hide values
            )
        else:
            baker.make_pizza(
                norm_p1_vals,
                ax=ax,
                color_blank_space='#000000',
                slice_colors=[color1] * len(p1_vals),
                blank_alpha=0.1,
                kwargs_slices=dict(edgecolor="#FFFFFF", zorder=2, linewidth=1.5, alpha=0.8),
                kwargs_params=dict(fontsize=0),
                kwargs_values=dict(fontsize=0)
            )
        
        # Add percentile labels at arc ends
        angles = np.linspace(0, 2*np.pi, len(p1_vals), endpoint=False)
        for i, (pct1, angle) in enumerate(zip(p1_pcts, angles)):
            # Position for percentile label (at edge of arc)
            radius = 0.85 + (norm_p1_vals[i] / 100) * 0.7
            x = radius * np.cos(angle + np.pi/2)
            y = radius * np.sin(angle + np.pi/2)
            
            # Add percentile badge
            ax.text(x, y, str(pct1), ha='center', va='center',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor=color1, 
                            edgecolor='white', linewidth=1),
                   fontsize=9, color='white', fontweight='bold', zorder=10)
            
            # Add second player percentile if exists
            if p2_pcts:
                radius2 = 0.85 + (norm_p2_vals[i] / 100) * 0.7
                x2 = radius2 * np.cos(angle + np.pi/2)
                y2 = radius2 * np.sin(angle + np.pi/2)
                
                # Offset to avoid overlap
                offset_angle = 0.08
                x2 += np.cos(angle + np.pi/2 + offset_angle) * 0.1
                y2 += np.sin(angle + np.pi/2 + offset_angle) * 0.1
                
                ax.text(x2, y2, str(p2_pcts[i]), ha='center', va='center',
                       bbox=dict(boxstyle="round,pad=0.3", facecolor=color2,
                                edgecolor='white', linewidth=1),
                       fontsize=9, color='white', fontweight='bold', zorder=10)
        
        # Add metric labels
        for i, (title, angle) in enumerate(zip(metrics_config['titles'], angles)):
            x = 1.15 * np.cos(angle + np.pi/2)
            y = 1.15 * np.sin(angle + np.pi/2)
            
            rotation = np.degrees(angle) - 90
            if rotation < -90:
                rotation += 180
                
            ax.text(x, y, title, ha='center', va='center', rotation=rotation,
                   fontsize=10, color='white', fontweight='bold')
        
        ax.set_xlim(-1.5, 1.5)
        ax.set_ylim(-1.5, 1.5)
        ax.axis('off')
    
    def _add_headers(self, fig, p1_data, p2_data, template, desc, color1, color2):
        """Add player info, logos and descriptions"""
        # Player 1 info
        fig.text(0.11, 0.95, p1_data['player_name'], fontweight="bold", 
                fontsize=16, color=color1)
        fig.text(0.11, 0.925, f"{p1_data['team']} | {p1_data['league']}", 
                fontsize=12, color='white')
        fig.text(0.11, 0.905, f"Season {p1_data['season']}", 
                fontsize=11, color='#CCCCCC')
        
        # Player 2 info (if exists)
        if p2_data is not None:
            fig.text(0.5, 0.95, p2_data['player_name'], fontweight="bold",
                    fontsize=16, color=color2)
            fig.text(0.5, 0.925, f"{p2_data['team']} | {p2_data['league']}",
                    fontsize=12, color='white')
            fig.text(0.5, 0.905, f"Season {p2_data['season']}", 
                    fontsize=11, color='#CCCCCC')
        
        # Template and description
        fig.text(0.89, 0.95, template, fontweight="bold", fontsize=14,
                color='white', ha='right')
        if desc:
            fig.text(0.89, 0.925, desc, fontsize=10, color='#CCCCCC',
                    ha='right', va='top', wrap=True)

# Convenience function
def create_hybrid_chart(df, player1_id, player2_id=None, metrics_config=None,
                       title_template="Position Template", comparison_desc="",
                       player1_color='#1A78CF', player2_color='coral'):
    """Quick function to create hybrid pizza chart"""
    chart = HybridPizzaSwarm(df)
    return chart.create_chart(player1_id, player2_id, metrics_config,
                             title_template, comparison_desc, 
                             player1_color, player2_color)