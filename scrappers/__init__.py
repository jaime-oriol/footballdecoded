"""Web scrapers for football data extraction (FotMob, Understat, WhoScored, EloRatings)."""

__version__ = "1.8.8"

__all__ = [
    "EloRatings",
    "FotMob",
    "Understat",
    "WhoScored",
]

from .elo import EloRatings
from .fotmob import FotMob
from .understat import Understat
from .whoscored import WhoScored
