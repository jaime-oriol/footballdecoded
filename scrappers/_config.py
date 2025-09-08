"""Configurations."""

import json
import logging
import logging.config
import os
import sys
from pathlib import Path

from rich.logging import RichHandler

# Configuration
NOCACHE = os.environ.get("SOCCERDATA_NOCACHE", "False").lower() in ("true", "1", "t")
NOSTORE = os.environ.get("SOCCERDATA_NOSTORE", "False").lower() in ("true", "1", "t")
MAXAGE = None
if os.environ.get("SOCCERDATA_MAXAGE") is not None:
    MAXAGE = int(os.environ.get("SOCCERDATA_MAXAGE", 0))
LOGLEVEL = os.environ.get("SOCCERDATA_LOGLEVEL", "INFO").upper()

# Directories
BASE_DIR = Path(os.environ.get("SOCCERDATA_DIR", Path.home() / "soccerdata"))
LOGS_DIR = Path(BASE_DIR, "logs")
DATA_DIR = Path(BASE_DIR, "data")
CONFIG_DIR = Path(BASE_DIR, "config")

# Create dirs
LOGS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Logger configuration
logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "minimal_clean": {
            "format": "%(message)s"
        },
        "info_clean": {
            "format": "[%(asctime)s] %(levelname)s %(message)s",
            "datefmt": "%d/%m/%y %H:%M:%S"
        },
        "detailed_clean": {
            "format": "[%(asctime)s] %(levelname)s [%(filename)s:%(lineno)d] %(message)s",
            "datefmt": "%d/%m/%y %H:%M:%S"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "minimal_clean",
            "level": logging.DEBUG,
        },
        "info": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": Path(LOGS_DIR, "info.log"),
            "maxBytes": 10485760,  # 1 MB
            "backupCount": 10,
            "formatter": "info_clean",
            "level": logging.INFO,
        },
        "error": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": Path(LOGS_DIR, "error.log"),
            "maxBytes": 10485760,  # 1 MB
            "backupCount": 10,
            "formatter": "detailed_clean",
            "level": logging.ERROR,
        },
    },
    "loggers": {
        "root": {
            "handlers": ["console", "info", "error"],
            "level": LOGLEVEL,
            "propagate": True,
        },
    },
}
logging.config.dictConfig(logging_config)
logging.captureWarnings(True)
logger = logging.getLogger("root")
logger.handlers[0] = RichHandler(markup=True, show_time=False, show_path=False)

# Team name replacements
TEAMNAME_REPLACEMENTS = {}
_f_custom_teamnname_replacements = CONFIG_DIR / "teamname_replacements.json"
if _f_custom_teamnname_replacements.is_file():
    with _f_custom_teamnname_replacements.open(encoding="utf8") as json_file:
        for team, to_replace_list in json.load(json_file).items():
            for to_replace in to_replace_list:
                TEAMNAME_REPLACEMENTS[to_replace] = team
    logger.debug(
        "Team name replacements loaded from %s",
        _f_custom_teamnname_replacements.name,
    )
else:
    logger.debug(
        "Team name replacements config not found at %s",
        _f_custom_teamnname_replacements.name,
    )

# League dict - Only sources used in FootballDecoded: FBref, WhoScored, Understat, FotMob
LEAGUE_DICT = {
    "ENG-Premier League": {
        "FBref": "Premier League",
        "WhoScored": "England - Premier League",
        "Understat": "EPL",
        "FotMob": "ENG-Premier League",
        "season_start": "Aug",
        "season_end": "May",
    },
    "ESP-La Liga": {
        "FBref": "La Liga",
        "WhoScored": "Spain - LaLiga",
        "Understat": "La liga",
        "FotMob": "ESP-LaLiga",
        "season_start": "Aug",
        "season_end": "May",
    },
    "ITA-Serie A": {
        "FBref": "Serie A",
        "WhoScored": "Italy - Serie A",
        "Understat": "Serie A",
        "FotMob": "ITA-Serie A",
        "season_start": "Aug",
        "season_end": "May",
    },
    "GER-Bundesliga": {
        "FBref": "Fußball-Bundesliga",
        "WhoScored": "Germany - Bundesliga",
        "Understat": "Bundesliga",
        "FotMob": "GER-Bundesliga",
        "season_start": "Aug",
        "season_end": "May",
    },
    "FRA-Ligue 1": {
        "FBref": "Ligue 1",
        "WhoScored": "France - Ligue 1",
        "Understat": "Ligue 1",
        "FotMob": "FRA-Ligue 1",
        "season_start": "Aug",
        "season_end": "May",
    },
    "INT-Champions League": {
        "FBref": "Champions League",
        "WhoScored": "Europe - Champions League",
        "FotMob": "INT-Champions League",
        "season_start": "Sep",
        "season_end": "May",
        "season_code": "multi-year",
    },
    "INT-World Cup": {
        "FBref": "FIFA World Cup",
        "FotMob": "INT-World Cup",
        "WhoScored": "International - FIFA World Cup",
        "season_code": "single-year",
    },
    "INT-European Championship": {
        "FBref": "UEFA European Football Championship",
        "FotMob": "INT-EURO",
        "WhoScored": "International - European Championship",
        "season_start": "Jun",
        "season_end": "Jul",
        "season_code": "single-year",
    },
    "INT-Women's World Cup": {
        "FBref": "FIFA Women's World Cup",
        "FotMob": "INT-Women's World Cup",
        "WhoScored": "International - FIFA Women's World Cup",
        "season_code": "single-year",
    },
    "POR-Primeira Liga": {
        "FBref": "Primeira Liga",
        "WhoScored": "Portugal - Liga Portugal",
        "Understat": "Liga Portugal",
        "FotMob": "POR-Primeira Liga",
        "season_start": "Aug",
        "season_end": "May",
    },
    "NED-Eredivisie": {
        "FBref": "Eredivisie",
        "WhoScored": "Netherlands - Eredivisie",
        "FotMob": "NED-Eredivisie",
        "season_start": "Aug",
        "season_end": "May",
    },
    "BEL-Pro League": {
        "FBref": "Belgian Pro League",
        "WhoScored": "Belgium - Pro League",
        "FotMob": "BEL-Pro League",
        "season_start": "Aug",
        "season_end": "May",
    },
    "TUR-Süper Lig": {
        "FBref": "Süper Lig",
        "WhoScored": "Turkey - Super Lig",
        "FotMob": "TUR-Super Lig",
        "season_start": "Aug",
        "season_end": "May",
    },
    "ARG-Primera División": {
        "FBref": "Liga Profesional de Fútbol Argentina",
        "WhoScored": "Argentina - Primera División",
        "FotMob": "ARG-Primera Division",
        "season_start": "Jan",
        "season_end": "Dec",
    },
    "BRA-Serie A": {
        "FBref": "Campeonato Brasileiro Série A",
        "WhoScored": "Brazil - Brasileirão",
        "FotMob": "BRA-Serie A",
        "season_start": "Apr",
        "season_end": "Dec",
    },
    "MEX-Liga MX": {
        "FBref": "Liga MX",
        "WhoScored": "Mexico - Liga MX",
        "FotMob": "MEX-Liga MX",
        "season_start": "Jan",
        "season_end": "Dec",
    },
}
_f_custom_league_dict = CONFIG_DIR / "league_dict.json"
if _f_custom_league_dict.is_file():
    with _f_custom_league_dict.open(encoding="utf8") as json_file:
        LEAGUE_DICT = {**LEAGUE_DICT, **json.load(json_file)}
    logger.debug("Custom league dict loaded from %s", _f_custom_league_dict.name)
else:
    logger.debug(
        "Custom league dict config not found at %s",
        _f_custom_league_dict.name,
    )