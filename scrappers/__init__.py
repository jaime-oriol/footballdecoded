"""A collection of tools to read and process soccer data from various sources."""

__version__ = "1.8.7"

__all__ = [
    "FBref",
    "Understat",
    "WhoScored",
]

from .fbref import FBref
from .understat import Understat
from .whoscored import WhoScored