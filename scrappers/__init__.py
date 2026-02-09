"""Web scrapers for football data extraction (FotMob, Understat, WhoScored)."""

__version__ = "1.8.7"

__all__ = [
    "FotMob",
    "Understat",
    "WhoScored",
]

from .fotmob import FotMob
from .understat import Understat
from .whoscored import WhoScored
