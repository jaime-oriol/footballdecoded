"""
pitch_control - PPCF de Spearman 2018 adaptado a tracking DFL Bundesliga.

Implementacion vectorizada con numpy: todos los puntos de la rejilla
se calculan a la vez usando broadcasting. Matematicamente identico
a las ecuaciones 2-4 de Spearman 2018.

El tracking DFL da coordenadas en metros centradas en (0,0) con
velocidad (m/s) y direccion (grados). Las componentes vx, vy se
derivan de speed + direction, sin necesidad de suavizado.

Referencia: Spearman 2018 "Beyond Expected Goals"
"""

from typing import Optional, Tuple

import numpy as np
import pandas as pd


# ── CONSTANTES ─────────────────────────────────────────────────────────

PITCH_LENGTH = 105.0  # metros
PITCH_WIDTH = 68.0    # metros


# ── PARAMETROS DEL MODELO ──────────────────────────────────────────────

def default_model_params(time_to_control_veto: int = 3) -> dict:
    """Parametros por defecto del PPCF (Spearman 2018).

    time_to_control_veto: ignora jugadores con prob de control < 10^-veto.
    """
    params = {
        "max_player_speed": 5.0,       # m/s
        "reaction_time": 0.7,          # segundos
        "tti_sigma": 0.45,             # incertidumbre en tiempo de llegada (s)
        "kappa_def": 1.0,              # ventaja defensiva
        "lambda_att": 4.3,             # tasa de control atacante
        "average_ball_speed": 15.0,    # m/s
        "int_dt": 0.04,                # paso de integracion (s)
        "max_int_time": 10.0,          # tiempo max de integracion (s)
        "model_converge_tol": 0.01,    # convergencia cuando PPCF > 0.99
    }
    params["lambda_def"] = params["lambda_att"] * params["kappa_def"]
    params["lambda_gk"] = params["lambda_def"] * 3.0

    # Umbral de tiempo para el veto de Spearman
    sigma_term = np.sqrt(3) * params["tti_sigma"] / np.pi
    params["time_to_control_att"] = (
        time_to_control_veto * np.log(10) * (sigma_term + 1 / params["lambda_att"])
    )
    params["time_to_control_def"] = (
        time_to_control_veto * np.log(10) * (sigma_term + 1 / params["lambda_def"])
    )
    return params


# ── CALCULO DE VELOCIDADES ─────────────────────────────────────────────

def compute_velocities(tracking_df: pd.DataFrame) -> pd.DataFrame:
    """Derivar vx, vy a partir de speed + direction del tracking DFL.

    La direccion DFL va en grados (0-360). 0 = eje X positivo (derecha).
    """
    df = tracking_df.copy()
    rad = np.deg2rad(df["direction"].values)
    speed = df["speed"].values

    # Descomponer en componentes x, y
    df["vx"] = speed * np.cos(rad)
    df["vy"] = speed * np.sin(rad)

    # Limitar velocidades irreales de jugadores (>12 m/s = dato raro)
    too_fast = (~df["is_ball"]) & (df["speed"] > 12.0)
    df.loc[too_fast, ["vx", "vy"]] = 0.0

    return df


# ── PPCF VECTORIZADO (Spearman 2018) ──────────────────────────────────

def _ppcf_vectorized(
    targets: np.ndarray,
    att_pos: np.ndarray, att_vel: np.ndarray, att_gk: np.ndarray,
    def_pos: np.ndarray, def_vel: np.ndarray, def_gk: np.ndarray,
    ball_pos: np.ndarray,
    params: dict,
) -> np.ndarray:
    """PPCF vectorizado para N objetivos a la vez (Spearman 2018).

    Integracion de Euler procesando todas las posiciones de la rejilla
    en un solo paso con broadcasting de numpy.

    targets: posiciones objetivo en metros, shape (N, 2).
    Devuelve PPCF_att, shape (N,).
    """
    N = len(targets)
    vmax = params["max_player_speed"]
    rt = params["reaction_time"]
    sigma = params["tti_sigma"]
    lam_a = params["lambda_att"]
    lam_d = params["lambda_def"]
    lam_gk = params["lambda_gk"]
    dt = params["int_dt"]
    max_int = params["max_int_time"]
    tol = params["model_converge_tol"]
    tc_a = params["time_to_control_att"]
    tc_d = params["time_to_control_def"]
    sig_c = np.pi / np.sqrt(3.0) / sigma
    Pa, Pd = len(att_pos), len(def_pos)

    # Tiempo de viaje del balon a cada objetivo: (N,)
    if ball_pos is not None and not np.any(np.isnan(ball_pos)):
        ball_tt = np.linalg.norm(targets - ball_pos, axis=1) / params["average_ball_speed"]
    else:
        ball_tt = np.zeros(N)

    # Tiempo de llegada: jugadores x objetivos -> (P, N)
    # Posicion tras reaccion = pos + vel * t_reaccion
    att_r = att_pos + att_vel * rt                                     # (Pa, 2)
    att_tti = rt + np.linalg.norm(
        targets[None] - att_r[:, None], axis=2,
    ) / vmax                                                           # (Pa, N)
    def_r = def_pos + def_vel * rt                                     # (Pd, 2)
    def_tti = rt + np.linalg.norm(
        targets[None] - def_r[:, None], axis=2,
    ) / vmax                                                           # (Pd, N)

    # Minimo tiempo de llegada por equipo: (N,)
    att_min = att_tti.min(axis=0) if Pa else np.full(N, np.inf)
    def_min = def_tti.min(axis=0) if Pd else np.full(N, np.inf)

    # Atajo: si un equipo domina claramente, no hace falta integrar (veto de Spearman)
    result = np.full(N, np.nan)
    def_dom = (att_min - np.maximum(ball_tt, def_min)) >= tc_d
    att_dom = (def_min - np.maximum(ball_tt, att_min)) >= tc_a
    result[def_dom] = 0.0
    result[att_dom & ~def_dom] = 1.0

    # Indices de los objetivos que quedan por resolver (zonas disputadas)
    eidx = np.where(np.isnan(result))[0]
    if len(eidx) == 0:
        return result

    # --- Integracion de Euler para objetivos disputados ---
    M = len(eidx)
    e_btt = ball_tt[eidx]                                              # (M,)
    e_att = att_tti[:, eidx]                                           # (Pa, M)
    e_def = def_tti[:, eidx]                                           # (Pd, M)

    # Mascaras de jugadores activos por objetivo: (P, M)
    a_act = (e_att - att_min[eidx]) < tc_a
    d_act = (e_def - def_min[eidx]) < tc_d

    # Lambda del defensor (portero tiene tasa mas alta): (Pd, 1)
    d_lam = np.where(def_gk, lam_gk, lam_d)[:, None]

    # Integrar en tau = t - ball_tt (alineado por objetivo)
    tau_arr = np.arange(0, max_int, dt)
    att_tti_rel = e_att - e_btt[None, :]                               # (Pa, M)
    def_tti_rel = e_def - e_btt[None, :]                               # (Pd, M)

    # Acumuladores de probabilidad
    pa_cum = np.zeros((Pa, M))
    pd_cum = np.zeros((Pd, M))
    tot_a = np.zeros(M)
    tot_d = np.zeros(M)
    conv = np.zeros(M, dtype=bool)

    for tau in tau_arr:
        if conv.all():
            break
        live = ~conv                                                   # (M,)
        rem = 1.0 - tot_a - tot_d                                     # (M,)
        # Sigmoide: probabilidad de haber llegado en tau
        with np.errstate(over="ignore"):
            p_a = 1.0 / (1.0 + np.exp(-sig_c * (tau - att_tti_rel)))  # (Pa, M)
            p_d = 1.0 / (1.0 + np.exp(-sig_c * (tau - def_tti_rel)))  # (Pd, M)
        # Acumular control
        pa_cum += (rem * p_a * lam_a * a_act * live) * dt
        pd_cum += (rem * p_d * d_lam * d_act * live) * dt
        tot_a = pa_cum.sum(axis=0)
        tot_d = pd_cum.sum(axis=0)
        conv = (tot_a + tot_d) > (1.0 - tol)

    result[eidx] = tot_a
    return result


# ── EXTRACCION DE EQUIPOS ──────────────────────────────────────────────

def _extract_teams(
    frame_data: pd.DataFrame,
    att_team_id: str,
    gk_ids: Optional[set] = None,
) -> Tuple:
    """Sacar arrays (pos, vel, es_portero) para atacantes y defensores."""
    players = frame_data[~frame_data["is_ball"]]
    att = players[players["team_id"] == att_team_id]
    def_ = players[players["team_id"] != att_team_id]

    def _arrays(df):
        pos = df[["x", "y"]].values.astype(np.float64)
        if "vx" in df.columns and "vy" in df.columns:
            vel = df[["vx", "vy"]].fillna(0).values.astype(np.float64)
        else:
            vel = np.zeros_like(pos)
        if gk_ids:
            is_gk = df["person_id"].isin(gk_ids).values
        else:
            is_gk = np.zeros(len(df), dtype=bool)
        return pos, vel, is_gk

    return _arrays(att), _arrays(def_)


def _get_ball_pos(frame_data: pd.DataFrame) -> Optional[np.ndarray]:
    """Sacar posicion del balon de un frame de tracking."""
    ball = frame_data[frame_data["is_ball"]]
    if ball.empty:
        return None
    return ball[["x", "y"]].values[0].astype(np.float64)


# ── SUPERFICIE PPCF ───────────────────────────────────────────────────

def compute_ppcf(
    frame_data: pd.DataFrame,
    att_team_id: str,
    ball_pos: Optional[np.ndarray] = None,
    params: Optional[dict] = None,
    gk_ids: Optional[set] = None,
    n_grid_x: int = 50,
    field_dimen: Tuple[float, float] = (PITCH_LENGTH, PITCH_WIDTH),
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Calcular superficie PPCF para un frame de tracking.

    Devuelve (ppcf_att, xgrid, ygrid). ppcf_att tiene shape (n_grid_y, n_grid_x).
    """
    if params is None:
        params = default_model_params()

    # Crear rejilla
    n_grid_y = int(n_grid_x * field_dimen[1] / field_dimen[0])
    dx = field_dimen[0] / n_grid_x
    dy = field_dimen[1] / n_grid_y
    xgrid = np.arange(n_grid_x) * dx - field_dimen[0] / 2.0 + dx / 2.0
    ygrid = np.arange(n_grid_y) * dy - field_dimen[1] / 2.0 + dy / 2.0

    if ball_pos is None:
        ball_pos = _get_ball_pos(frame_data)

    # Extraer datos de cada equipo
    (att_pos, att_vel, att_gk), (def_pos, def_vel, def_gk) = _extract_teams(
        frame_data, att_team_id, gk_ids
    )

    # Aplanar rejilla y calcular PPCF
    xx, yy = np.meshgrid(xgrid, ygrid)
    targets = np.column_stack([xx.ravel(), yy.ravel()])
    ppcf_att = _ppcf_vectorized(
        targets, att_pos, att_vel, att_gk,
        def_pos, def_vel, def_gk, ball_pos, params,
    ).reshape(n_grid_y, n_grid_x)

    return ppcf_att, xgrid, ygrid


def ppcf_at_targets(
    frame_data: pd.DataFrame,
    targets_meters: np.ndarray,
    att_team_id: str,
    ball_pos: Optional[np.ndarray] = None,
    params: Optional[dict] = None,
    gk_ids: Optional[set] = None,
) -> np.ndarray:
    """Calcular PPCF en posiciones concretas (sin rejilla).

    targets_meters: array (N, 2) con posiciones en metros.
    Devuelve array (N,) con PPCF_att en cada punto.
    """
    if params is None:
        params = default_model_params()
    if ball_pos is None:
        ball_pos = _get_ball_pos(frame_data)

    (att_pos, att_vel, att_gk), (def_pos, def_vel, def_gk) = _extract_teams(
        frame_data, att_team_id, gk_ids
    )

    return _ppcf_vectorized(
        targets_meters, att_pos, att_vel, att_gk,
        def_pos, def_vel, def_gk, ball_pos, params,
    )


# ── PPCF EN SECUENCIA ─────────────────────────────────────────────────

def compute_ppcf_sequence(
    tracking_df: pd.DataFrame,
    att_team_id: str,
    frame_range: Optional[Tuple[int, int]] = None,
    every_n: int = 1,
    params: Optional[dict] = None,
    gk_ids: Optional[set] = None,
    n_grid_x: int = 50,
) -> dict:
    """Calcular superficies PPCF para una secuencia de frames.

    Devuelve dict {frame_number: ppcf_att array}.
    """
    if params is None:
        params = default_model_params()

    frames = sorted(tracking_df["frame"].unique())
    if frame_range:
        frames = [f for f in frames if frame_range[0] <= f <= frame_range[1]]
    frames = frames[::every_n]

    ppcf_dict = {}
    for fc in frames:
        fdata = tracking_df[tracking_df["frame"] == fc]
        # Saltar frames con pocos jugadores (ej. entre partes)
        if fdata[~fdata["is_ball"]].shape[0] < 10:
            continue
        ppcf_att, _, _ = compute_ppcf(
            fdata, att_team_id, params=params, gk_ids=gk_ids, n_grid_x=n_grid_x,
        )
        ppcf_dict[fc] = ppcf_att

    return ppcf_dict
