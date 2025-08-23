# ====================================================================
# FootballDecoded Utilities - Common functions across modules
# ====================================================================
# 
# Utility functions shared across the FootballDecoded project.
# Provides helper functions for distance calculations, name validation,
# and common data processing tasks used in scrapers and analysis.

# Third-party imports
import pandas as pd
import numpy as np
from typing import Any


def calculate_euclidean_distance(
    x1: pd.Series, y1: pd.Series, x2: float, y2: float, scale_factor: float = 1.0
) -> pd.Series:
    """
    Calculate euclidean distance between points and a reference point.
    
    Used for spatial analysis of football events, such as calculating
    distances from goal, penalty area, or other field reference points.
    
    Args:
        x1, y1: Series with coordinates (e.g., shot locations)
        x2, y2: Reference point coordinates (e.g., goal center)
        scale_factor: Scaling factor for final distance (e.g., field dimensions)
        
    Returns:
        Series with calculated distances in specified units
    """
    distances = []
    
    # Calculate distance for each point, handling missing values
    for x, y in zip(x1, y1):
        if pd.isna(x) or pd.isna(y):
            distances.append(None)
            continue
        
        # Standard Euclidean distance formula with scaling
        distance = np.sqrt((float(x) - x2) ** 2 + (float(y) - y2) ** 2) * scale_factor
        distances.append(round(distance, 2))
    
    return pd.Series(distances, index=x1.index)


def validate_name_field(name: Any) -> bool:
    """
    Validate if a name field contains valid, non-empty content.
    
    Used to check player names, team names, and other text fields
    scraped from web sources before processing.
    
    Args:
        name: Name field to validate (any type)
        
    Returns:
        True if name is valid (non-null, non-empty string), False otherwise
    """
    if pd.isna(name) or not str(name).strip():
        return False
    return True


def format_player_name_base(full_name: str, default: str = "Unknown") -> str:
    """
    Base function for player name formatting with common validation.
    
    Provides consistent player name handling across different scrapers.
    Used as a foundation for more specific name formatting functions.
    
    Args:
        full_name: Full player name from scraped data
        default: Default value for invalid/missing names
        
    Returns:
        Cleaned and formatted name, or default value if invalid
    """
    # Use validation helper to check name quality
    if not validate_name_field(full_name):
        return default
    
    # Return cleaned name (stripped of whitespace)
    return full_name.strip()