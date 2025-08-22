# ====================================================================
# FootballDecoded Utilities - Common functions across modules
# ====================================================================

import pandas as pd
import numpy as np
from typing import Any


def calculate_euclidean_distance(
    x1: pd.Series, y1: pd.Series, x2: float, y2: float, scale_factor: float = 1.0
) -> pd.Series:
    """
    Calculate euclidean distance between points and a reference point.
    
    Args:
        x1, y1: Series with coordinates
        x2, y2: Reference point coordinates
        scale_factor: Scaling factor for final distance
        
    Returns:
        Series with calculated distances
    """
    distances = []
    
    for x, y in zip(x1, y1):
        if pd.isna(x) or pd.isna(y):
            distances.append(None)
            continue
        
        distance = np.sqrt((float(x) - x2) ** 2 + (float(y) - y2) ** 2) * scale_factor
        distances.append(round(distance, 2))
    
    return pd.Series(distances, index=x1.index)


def validate_name_field(name: Any) -> bool:
    """
    Validate if name field has valid content.
    
    Args:
        name: Name field to validate
        
    Returns:
        True if valid, False otherwise
    """
    if pd.isna(name) or not str(name).strip():
        return False
    return True


def format_player_name_base(full_name: str, default: str = "Unknown") -> str:
    """
    Base function for player name formatting with common validation.
    
    Args:
        full_name: Full player name
        default: Default value for invalid names
        
    Returns:
        Formatted name or default
    """
    if not validate_name_field(full_name):
        return default
    
    return full_name.strip()