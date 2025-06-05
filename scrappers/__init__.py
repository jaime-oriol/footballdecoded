"""A collection of tools to read and process soccer data from various sources."""

__version__ = "1.8.7"

__all__ = [
    "FBref",
    "FotMob",
    "Understat",
    "WhoScored",
]

from .fbref import FBref
from .fotmob import FotMob
from .understat import Understat
from .whoscored import WhoScored