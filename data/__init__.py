"""A collection of tools to read and process soccer data from various sources."""

__version__ = "1.8.7"

__all__ = [
    "ClubElo",
    "FBref",
    "FotMob",
    "MatchHistory",
    "Understat",
]

from .clubelo import ClubElo
from .fbref import FBref
from .fotmob import FotMob
from .match_history import MatchHistory
from .understat import Understat