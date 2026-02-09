"""Shared utility functions: distance calculations, name validation, formatting."""

import pandas as pd
import numpy as np
from typing import Any


def calculate_euclidean_distance(
    x1: pd.Series, y1: pd.Series, x2: float, y2: float, scale_factor: float = 1.0
) -> pd.Series:
    """Euclidean distance from each (x1, y1) point to reference (x2, y2), scaled."""
    distances = []

    for x, y in zip(x1, y1):
        if pd.isna(x) or pd.isna(y):
            distances.append(None)
            continue

        distance = np.sqrt((float(x) - x2) ** 2 + (float(y) - y2) ** 2) * scale_factor
        distances.append(round(distance, 2))

    return pd.Series(distances, index=x1.index)


def validate_name_field(name: Any) -> bool:
    """Return True if name is non-null and non-empty after stripping."""
    if pd.isna(name) or not str(name).strip():
        return False
    return True


def format_player_name_base(full_name: str, default: str = "Unknown") -> str:
    """Validate and strip a player name. Returns default if invalid."""
    if not validate_name_field(full_name):
        return default
    return full_name.strip()