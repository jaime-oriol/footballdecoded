# ====================================================================
# FootballDecoded - Style Manager Module
# ====================================================================
# Centralized configuration and styling system
# ====================================================================

from typing import Dict, Tuple

# ====================================================================
# SCALING CONFIGURATION
# ====================================================================

SCALE_CONFIG = {
    'node_size_min': 500, 'node_size_max': 15000,
    'node_threshold_halves': 10, 'node_threshold_full_match': 20,
    'line_width_min': 1.0, 'line_width_max': 8.0,
    'name_length_threshold': 12
}

# ====================================================================
# CONNECTION CONFIGURATION
# ====================================================================

CONNECTION_CONFIG = {
    'min_passes_halves': 4, 'min_passes_full_match': 8,
    'alpha': 0.8, 'base_offset': 0.4,
    'arrow_length': 1.0, 'arrow_width': 0.6, 'name_margin': 2.0
}

# ====================================================================
# FONT CONFIGURATION
# ====================================================================

FONT_CONFIG = {
    'family': 'DejaVu Sans', 
    'fallback': 'sans-serif'
}

# ====================================================================
# MATCH PERIODS CONFIGURATION
# ====================================================================

HALVES_CONFIG = {
    'first_half_end': 48, 
    'second_half_start': 45, 
    'match_end': 120
}

# ====================================================================
# TEAM COLORS DATABASE
# ====================================================================

TEAM_COLORS = {
    'Barcelona': {
        'primary': '#A50044',
        'secondary': '#004D98',
        'accent': '#EDBB00'
    },
    'Real Madrid': {
        'primary': '#FEBE10',
        'secondary': '#00529F',
        'accent': '#FFFFFF'
    },
    'Manchester City': {
        'primary': '#6CABDD',
        'secondary': '#1C2C5B',
        'accent': '#FFCC00'
    },
    'Liverpool': {
        'primary': '#C8102E',
        'secondary': '#F6EB61',
        'accent': '#00B2A9'
    },
    'Arsenal': {
        'primary': '#EF0107',
        'secondary': '#023474',
        'accent': '#9C824A'
    },
    'Chelsea': {
        'primary': '#034694',
        'secondary': '#6A7FDB',
        'accent': '#FFFFFF'
    },
    'Bayern Munich': {
        'primary': '#DC052D',
        'secondary': '#0066B2',
        'accent': '#FFFFFF'
    },
    'PSG': {
        'primary': '#004170',
        'secondary': '#ED1C24',
        'accent': '#FFFFFF'
    },
    'Juventus': {
        'primary': '#000000',
        'secondary': '#FFFFFF',
        'accent': '#D4AF37'
    },
    'Inter Milan': {
        'primary': '#0068A8',
        'secondary': '#000000',
        'accent': '#FFFFFF'
    },
    'AC Milan': {
        'primary': '#AC1A2F',
        'secondary': '#000000',
        'accent': '#FFFFFF'
    },
    'Atletico Madrid': {
        'primary': '#CE2029',
        'secondary': '#244C9C',
        'accent': '#FFFFFF'
    },
    'Borussia Dortmund': {
        'primary': '#FDE100',
        'secondary': '#000000',
        'accent': '#FFFFFF'
    },
    'Ajax': {
        'primary': '#D2122E',
        'secondary': '#FFFFFF',
        'accent': '#000000'
    },
    'Espanyol': {
        'primary': '#2C63B8',
        'secondary': '#004595',
        'accent': '#FFFFFF'
    },
    # Default colors
    'Default': {
        'primary': '#2E4A87',
        'secondary': '#1A365D',
        'accent': '#4A90A4'
    }
}

# ====================================================================
# COLOR FUNCTIONS
# ====================================================================

def get_team_colors(team_name: str) -> Dict[str, str]:
    """
    Get team colors with fallback to default.
    
    Args:
        team_name: Name of the team
        
    Returns:
        Dict with primary, secondary, and accent colors
    """
    # Normalize team name for matching
    normalized_name = team_name.strip()
    
    # Direct match
    if normalized_name in TEAM_COLORS:
        return TEAM_COLORS[normalized_name]
    
    # Partial match for common variations
    for team, colors in TEAM_COLORS.items():
        if team.lower() in normalized_name.lower() or normalized_name.lower() in team.lower():
            return colors
    
    # Return default colors
    return TEAM_COLORS['Default']

def get_primary_color(team_name: str) -> str:
    """Get primary color for a team."""
    return get_team_colors(team_name)['primary']

def get_secondary_color(team_name: str) -> str:
    """Get secondary color for a team."""
    return get_team_colors(team_name)['secondary']

def get_accent_color(team_name: str) -> str:
    """Get accent color for a team."""
    return get_team_colors(team_name)['accent']

def get_color_palette(team_name: str) -> Tuple[str, str, str]:
    """
    Get complete color palette for a team.
    
    Returns:
        Tuple of (primary, secondary, accent) colors
    """
    colors = get_team_colors(team_name)
    return colors['primary'], colors['secondary'], colors['accent']

# ====================================================================
# STYLE VALIDATION
# ====================================================================

def validate_color(color: str) -> bool:
    """
    Validate if a color string is properly formatted.
    
    Args:
        color: Color string (hex format expected)
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(color, str):
        return False
    
    # Check hex format
    if color.startswith('#') and len(color) == 7:
        try:
            int(color[1:], 16)
            return True
        except ValueError:
            return False
    
    return False

def get_contrast_color(background_color: str) -> str:
    """
    Get contrasting color (black or white) for text on background.
    
    Args:
        background_color: Background color in hex format
        
    Returns:
        '#FFFFFF' or '#000000' for best contrast
    """
    if not validate_color(background_color):
        return '#000000'
    
    # Convert hex to RGB
    hex_color = background_color.lstrip('#')
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Calculate luminance
    luminance = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
    
    # Return contrasting color
    return '#000000' if luminance > 0.5 else '#FFFFFF'

# ====================================================================
# EXPORT CONFIGURATIONS
# ====================================================================

EXPORT_CONFIG = {
    'dpi': 300,
    'format': 'png',
    'bbox_inches': 'tight',
    'facecolor': 'white',
    'edgecolor': 'none',
    'quality': 95
}

def get_export_settings(high_quality: bool = True) -> Dict:
    """Get export settings based on quality preference."""
    settings = EXPORT_CONFIG.copy()
    
    if not high_quality:
        settings['dpi'] = 150
        settings['quality'] = 80
    
    return settings