# ====================================================================
# FootballDecoded - Export Manager Module
# ====================================================================
# Universal export and file management for all visualizations
# ====================================================================

import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, Any

# ====================================================================
# EXPORT CONFIGURATIONS
# ====================================================================

EXPORT_SETTINGS = {
    'high': {
        'dpi': 300,
        'format': 'png',
        'bbox_inches': 'tight',
        'facecolor': 'white',
        'edgecolor': 'none',
        'quality': 95
    },
    'medium': {
        'dpi': 150,
        'format': 'png', 
        'bbox_inches': 'tight',
        'facecolor': 'white',
        'edgecolor': 'none',
        'quality': 80
    },
    'web': {
        'dpi': 96,
        'format': 'png',
        'bbox_inches': 'tight',
        'facecolor': 'white',
        'edgecolor': 'none',
        'quality': 75
    }
}

# ====================================================================
# EXPORT FUNCTIONS
# ====================================================================

def save_high_quality(fig: plt.Figure, base_name: str, suffix: str = "") -> str:
    """
    Save figure with high quality settings and timestamp.
    
    Args:
        fig: Matplotlib figure to save
        base_name: Base filename (e.g., team name)
        suffix: Optional suffix for filename
        
    Returns:
        Full path of saved file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_name = base_name.replace(" ", "_").replace("-", "_")
    
    filename = f"{clean_name}"
    if suffix:
        filename += f"_{suffix}"
    filename += f"_{timestamp}.png"
    
    settings = get_export_settings('high')
    fig.savefig(filename, **settings)
    
    print(f"Saved: {filename}")
    return filename

def get_export_settings(quality: str = 'high') -> Dict[str, Any]:
    """
    Get export settings for specified quality level.
    
    Args:
        quality: Quality level ('high', 'medium', 'web')
        
    Returns:
        Dictionary with export settings
    """
    return EXPORT_SETTINGS.get(quality, EXPORT_SETTINGS['high'])