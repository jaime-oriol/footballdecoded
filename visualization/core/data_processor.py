# ====================================================================
# FootballDecoded - Data Processing Module
# ====================================================================
# Universal data processing functions for all visualizations
# ====================================================================

import numpy as np
from typing import List

# ====================================================================
# UNIVERSAL SCALING FUNCTIONS
# ====================================================================

def scale_values(values: List[float], min_output: float, max_output: float) -> np.ndarray:
    """
    Scale array of values to specified output range.
    
    Args:
        values: Input values to scale
        min_output: Minimum output value
        max_output: Maximum output value
        
    Returns:
        Scaled values as numpy array
    """
    values_array = np.array(values)
    
    if len(values_array) == 0:
        return values_array
    
    min_val = values_array.min()
    max_val = values_array.max()
    
    if max_val == min_val:
        return np.full_like(values_array, (min_output + max_output) / 2)
    
    normalized = (values_array - min_val) / (max_val - min_val)
    return min_output + normalized * (max_output - min_output)

# ====================================================================
# TEXT PROCESSING
# ====================================================================

def optimize_name(full_name: str, max_length: int = 12) -> str:
    """
    Optimize player name for display in visualizations.
    
    Args:
        full_name: Complete player name
        max_length: Maximum character length
        
    Returns:
        Optimized name for display
    """
    if len(full_name) <= max_length:
        return full_name
    
    name_parts = full_name.split()
    
    if len(name_parts) >= 2:
        return name_parts[-1]
    
    return full_name[:max_length]