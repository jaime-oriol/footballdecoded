"""
loader - Carga de datos DFL Bundesliga TRACAB.

Parsea 3 tipos de XML del dataset abierto DFL (Bassek et al. 2025):
  - Match information: equipos, jugadores, dimensiones, alineaciones
  - Events: acciones del partido con timestamp y coordenadas
  - Tracking (positions): posiciones 25Hz de jugadores + balon

Los XML de tracking pesan 350-420 MB. Usa iterparse para leerlos
en streaming sin cargar todo el arbol en memoria.

Coordenadas en metros centradas en (0,0). Velocidad en m/s.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

import numpy as np
import pandas as pd


# ── DIRECTORIO DE DATOS ────────────────────────────────────────────────
DFL_DIR = Path(__file__).resolve().parent.parent.parent / "public_data" / "dfl"

# ── IDS DE PARTIDOS ────────────────────────────────────────────────────
# 7 partidos: 2 de Bundesliga (COM-000001), 5 de 2.Bundesliga (COM-000002)
MATCH_IDS = [
    "DFL-MAT-J03WMX", "DFL-MAT-J03WN1",  # Bundesliga
    "DFL-MAT-J03WOH", "DFL-MAT-J03WOY", "DFL-MAT-J03WPY",
    "DFL-MAT-J03WQQ", "DFL-MAT-J03WR9",  # 2.Bundesliga
]


def _find_file(match_id: str, prefix: str) -> Path:
    """Busca un XML de la DFL por match_id y prefijo de tipo."""
    pattern = f"{prefix}*{match_id}.xml"
    hits = list(DFL_DIR.glob(pattern))
    if not hits:
        raise FileNotFoundError(f"No hay fichero {pattern} en {DFL_DIR}")
    return hits[0]


# ── INFO DEL PARTIDO ───────────────────────────────────────────────────

@dataclass
class PlayerInfo:
    person_id: str
    shirt_number: int
    short_name: str
    position: str


@dataclass
class TeamInfo:
    team_id: str
    team_name: str
    role: str           # "home" o "guest"
    lineup: str         # ej. "4-2-3-1"
    color_main: str
    color_secondary: str
    players: List[PlayerInfo] = field(default_factory=list)


@dataclass
class MatchInfo:
    match_id: str
    competition: str
    season: str
    match_day: str
    home_team: TeamInfo
    guest_team: TeamInfo
    result: str
    pitch_x: float      # metros
    pitch_y: float       # metros
    kickoff_time: str
    stadium: str


def load_match_info(match_id: str) -> MatchInfo:
    """Parsea el XML de info del partido. Devuelve equipos, jugadores, campo."""
    path = _find_file(match_id, "DFL_02_01_matchinformation")
    tree = ET.parse(path)
    root = tree.getroot()

    general = root.find(".//General")
    env = root.find(".//Environment")

    # Extraer equipos y sus jugadores
    teams = {}
    for team_el in root.findall(".//Team"):
        players = []
        for p in team_el.findall(".//Player"):
            players.append(PlayerInfo(
                person_id=p.get("PersonId"),
                shirt_number=int(p.get("ShirtNumber", 0)),
                short_name=p.get("Shortname", ""),
                position=p.get("Position", ""),
            ))
        ti = TeamInfo(
            team_id=team_el.get("TeamId"),
            team_name=team_el.get("TeamName"),
            role=team_el.get("Role"),
            lineup=team_el.get("LineUp", ""),
            color_main=team_el.get("PlayerShirtMainColor", ""),
            color_secondary=team_el.get("PlayerShirtSecondaryColor", ""),
            players=players,
        )
        teams[ti.role] = ti

    return MatchInfo(
        match_id=general.get("MatchId"),
        competition=general.get("CompetitionName", ""),
        season=general.get("Season", ""),
        match_day=general.get("MatchDay", ""),
        home_team=teams.get("home"),
        guest_team=teams.get("guest"),
        result=general.get("Result", ""),
        pitch_x=float(env.get("PitchX", 105.0)),
        pitch_y=float(env.get("PitchY", 68.0)),
        kickoff_time=general.get("KickoffTime", ""),
        stadium=env.get("StadiumName", ""),
    )


# ── EVENTOS ────────────────────────────────────────────────────────────

def load_events(match_id: str) -> pd.DataFrame:
    """Parsea el XML de eventos. Una fila por evento."""
    path = _find_file(match_id, "DFL_03_02_events_raw")
    rows = []

    for _, elem in ET.iterparse(path, events=["end"]):
        if elem.tag != "Event":
            continue

        base = {
            "event_id": elem.get("EventId"),
            "event_time": elem.get("EventTime"),
            "x": _float(elem.get("X-Position")),
            "y": _float(elem.get("Y-Position")),
            "calculated_frame": _int(elem.get("CalculatedFrame")),
        }

        # El primer hijo es el tipo de accion
        for child in elem:
            base["action_type"] = child.tag
            base["team"] = child.get("Team", child.get("TeamLeft", ""))
            base["player"] = child.get("Player", "")
            # Aplanar atributos extra
            for k, v in child.attrib.items():
                if k not in ("Team", "Player"):
                    base[f"attr_{k}"] = v
            break

        rows.append(base)
        elem.clear()

    df = pd.DataFrame(rows)
    if "event_time" in df.columns:
        df["event_time"] = pd.to_datetime(df["event_time"], utc=True)
    return df


# ── TRACKING ───────────────────────────────────────────────────────────

def load_tracking(
    match_id: str,
    game_section: str = "firstHalf",
    subsample: int = 1,
    float32: bool = True,
) -> pd.DataFrame:
    """Parsea el XML de tracking via iterparse (streaming, no revienta RAM).

    Devuelve DataFrame largo: una fila por jugador/balon por frame.
    subsample=1 da los 25Hz completos, subsample=5 da 5Hz.
    """
    path = _find_file(match_id, "DFL_04_03_positions_raw_observed")

    rows = []
    current_fs_meta = None
    skip_fs = False

    for event, elem in ET.iterparse(path, events=["start", "end"]):
        # Inicio de un FrameSet: metadata del jugador/balon
        if event == "start" and elem.tag == "FrameSet":
            fs_section = elem.get("GameSection")
            fs_team = elem.get("TeamId", "")

            # Saltar si no es la parte que queremos
            if game_section and fs_section != game_section:
                skip_fs = True
                continue
            # Saltar arbitros
            if "referee" in fs_team.lower():
                skip_fs = True
                continue
            skip_fs = False
            current_fs_meta = {
                "team_id": fs_team,
                "person_id": elem.get("PersonId", ""),
                "game_section": fs_section,
                "is_ball": fs_team == "" or fs_team.upper() == "BALL",
            }

        # Fin de un Frame: extraer posicion
        elif event == "end" and elem.tag == "Frame" and not skip_fs:
            if current_fs_meta is None:
                continue

            n = int(elem.get("N", 0))
            # Subsamplear si hace falta
            if subsample > 1 and n % subsample != 0:
                elem.clear()
                continue

            rows.append({
                "frame": n,
                "timestamp": elem.get("T"),
                "person_id": current_fs_meta["person_id"],
                "team_id": current_fs_meta["team_id"],
                "x": _float(elem.get("X")),
                "y": _float(elem.get("Y")),
                "speed": _float(elem.get("S")),
                "accel": _float(elem.get("A")),
                "direction": _float(elem.get("D")),
                "is_ball": current_fs_meta["is_ball"],
                "game_section": current_fs_meta["game_section"],
            })
            elem.clear()

        # Fin de FrameSet: limpiar metadata
        elif event == "end" and elem.tag == "FrameSet":
            current_fs_meta = None
            elem.clear()

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df["is_ball"] = df["is_ball"].astype(bool)

    # Parsear timestamps
    if "timestamp" in df.columns and not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    # Tiempo transcurrido desde el primer frame de cada parte
    for section in df["game_section"].unique():
        mask = df["game_section"] == section
        t0 = df.loc[mask, "timestamp"].min()
        df.loc[mask, "time_s"] = (
            df.loc[mask, "timestamp"] - t0
        ).dt.total_seconds()

    # Bajar a float32 para ahorrar RAM
    if float32:
        for col in ["x", "y", "speed", "accel", "direction", "time_s"]:
            if col in df.columns:
                df[col] = df[col].astype("float32")

    return df


def load_tracking_frame(tracking_df: pd.DataFrame, frame_number: int) -> pd.DataFrame:
    """Extraer un solo frame del tracking ya cargado."""
    return tracking_df[tracking_df["frame"] == frame_number].copy()


def get_frame_at_time(tracking_df: pd.DataFrame, time_s: float) -> int:
    """Buscar el frame mas cercano a un tiempo dado (en segundos)."""
    frame_times = tracking_df.groupby("frame")["time_s"].first()
    return int((frame_times - time_s).abs().idxmin())


# ── HELPERS ────────────────────────────────────────────────────────────

def get_player_lookup(match_info: MatchInfo) -> Dict[str, str]:
    """Diccionario person_id -> nombre corto."""
    lookup = {}
    for team in [match_info.home_team, match_info.guest_team]:
        if team:
            for p in team.players:
                lookup[p.person_id] = p.short_name
    return lookup


def get_team_lookup(match_info: MatchInfo) -> Dict[str, str]:
    """Diccionario team_id -> nombre equipo."""
    lookup = {}
    for team in [match_info.home_team, match_info.guest_team]:
        if team:
            lookup[team.team_id] = team.team_name
    return lookup


def get_goalkeeper_ids(
    match_info: MatchInfo,
    tracking_df: Optional[pd.DataFrame] = None,
) -> set:
    """Detectar porteros.

    Si hay tracking, pilla al jugador de cada equipo con mayor |x| medio
    en los primeros 100 frames (el mas pegado a su porteria).
    Si no, usa la heuristica del dorsal 1.
    """
    if tracking_df is not None and not tracking_df.empty:
        gk_ids = set()
        # Solo los primeros 100 frames
        early = tracking_df[
            (~tracking_df["is_ball"])
            & (tracking_df["frame"] <= tracking_df["frame"].min() + 100)
        ]
        for tid in early["team_id"].unique():
            team_data = early[early["team_id"] == tid]
            # Media de |x| por jugador: el portero esta mas lejos del centro
            mean_abs_x = team_data.groupby("person_id")["x"].apply(
                lambda s: s.abs().mean()
            )
            if not mean_abs_x.empty:
                gk_ids.add(mean_abs_x.idxmax())
        return gk_ids

    # Fallback: dorsal 1 o "keeper" en la posicion
    gk_ids = set()
    for team in [match_info.home_team, match_info.guest_team]:
        if team:
            for p in team.players:
                if p.shirt_number == 1 or "keeper" in p.position.lower():
                    gk_ids.add(p.person_id)
    return gk_ids


def _float(val) -> float:
    """Conversion segura a float."""
    if val is None:
        return np.nan
    try:
        return float(val)
    except (ValueError, TypeError):
        return np.nan


def _int(val) -> Optional[int]:
    """Conversion segura a int."""
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
