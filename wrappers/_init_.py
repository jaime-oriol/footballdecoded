"""A collection of tools to read and process soccer data from various sources."""

__version__ = "1.8.7"

__all__ = [
    "FBref",
    "Understat",
    "WhoScored",
]

from .fbref_data import FBref
from .understat_data import Understat
from .whoscored_data import WhoScored