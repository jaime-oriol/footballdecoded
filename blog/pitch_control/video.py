"""
video - Videos animados de PPCF / Voronoi sobre tracking DFL.

Renderiza mp4 mostrando la evolucion del control espacial frame a frame.
Tres modos:
    - ppcf: superficie de pitch control (heatmap azul/rojo)
    - voronoi: diagrama de Voronoi (poligonos rellenos)
    - split: lado a lado Voronoi | PPCF

Usa un dict pre-calculado de PPCF (frame -> superficie) con bisect
para buscar el frame mas cercano. Necesita ffmpeg para guardar.
"""

from bisect import bisect_left
from typing import Dict, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import animation
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.colors import to_rgba

from blog.pitch_control.pitch_control import PITCH_LENGTH, PITCH_WIDTH
from blog.pitch_control.viz import (
    ATT, BG, BALL_COLOR, DEF, GK, MS, PE, PPCF_CMAP, WHITE,
    draw_pitch, compute_voronoi_polygons,
)


def render_ppcf_video(
    tracking_df: pd.DataFrame,
    att_team_id: str,
    ppcf_dict: Dict[int, np.ndarray],
    frame_range: Tuple[int, int],
    gk_ids: Optional[set] = None,
    names: Optional[Dict[str, str]] = None,
    title: Optional[str] = None,
    mode: str = "ppcf",
    fps: int = 25,
    save_path: Optional[str] = None,
) -> animation.FuncAnimation:
    """Renderiza video animado de pitch control o Voronoi.

    tracking_df: tracking completo con velocidades (vx, vy).
    att_team_id: ID del equipo atacante.
    ppcf_dict: superficies PPCF pre-calculadas {num_frame: ndarray}.
    frame_range: (frame_inicio, frame_fin) inclusivo.
    gk_ids: person_ids de los porteros.
    names: diccionario person_id -> nombre.
    title: titulo superpuesto en el video.
    mode: "ppcf", "voronoi" o "split".
    fps: frames por segundo de reproduccion.
    save_path: ruta para guardar mp4 (necesita ffmpeg).

    Devuelve objeto FuncAnimation.
    """
    if gk_ids is None:
        gk_ids = set()

    # Frames disponibles en el rango pedido
    frames = sorted(tracking_df["frame"].unique())
    frames = [f for f in frames if frame_range[0] <= f <= frame_range[1]]
    if not frames:
        return None

    # Pre-agrupar tracking por frame para lookup O(1)
    window = tracking_df[
        (tracking_df["frame"] >= frame_range[0])
        & (tracking_df["frame"] <= frame_range[1])
    ]
    frame_data = {fc: grp for fc, grp in window.groupby("frame")}
    empty = pd.DataFrame(columns=tracking_df.columns)

    # Busqueda del PPCF mas cercano por bisect
    ppcf_keys = sorted(ppcf_dict.keys()) if ppcf_dict else []

    def _get_ppcf(fc):
        """Devuelve la superficie PPCF del frame mas cercano."""
        if not ppcf_keys:
            return None
        idx = bisect_left(ppcf_keys, fc)
        if idx >= len(ppcf_keys):
            idx = len(ppcf_keys) - 1
        elif idx > 0 and abs(ppcf_keys[idx - 1] - fc) <= abs(ppcf_keys[idx] - fc):
            idx -= 1
        return ppcf_dict[ppcf_keys[idx]]

    # ── Montar la figura ──────────────────────────────────────────
    L, W = PITCH_LENGTH / 2, PITCH_WIDTH / 2

    if mode == "split":
        # Dos campos lado a lado
        fig, (ax_vor, ax_ppcf) = plt.subplots(1, 2, figsize=(24, 10.4))
        axes = [ax_vor, ax_ppcf]
        for ax in axes:
            draw_pitch(ax)
        ax_vor.set_title("Voronoi", color=WHITE, fontsize=13, fontweight="bold")
        ax_ppcf.set_title("Pitch Control (PPCF)", color=WHITE, fontsize=13, fontweight="bold")
    else:
        # Un solo campo
        fig, ax = plt.subplots(figsize=(16, 10.4))
        draw_pitch(ax)
        axes = [ax]

    fig.set_facecolor(BG)

    # Imagen persistente para el heatmap PPCF (se actualiza cada frame)
    if mode in ("ppcf", "split"):
        target_ax = axes[-1] if mode == "split" else axes[0]
        im = target_ax.imshow(
            np.full((32, 50), 0.5), extent=[-L, L, -W, W], origin="lower",
            interpolation="spline36", cmap=PPCF_CMAP, alpha=0.0,
            vmin=0, vmax=1, zorder=1, aspect="auto",
        )

    # Texto del reloj (minuto:segundo)
    time_txt = axes[0].text(
        -L + 2, W - 3, "", fontsize=12, color=WHITE,
        fontweight="bold", path_effects=PE, zorder=10,
    )
    # Titulo opcional arriba del campo
    if title:
        axes[0].text(
            0, W + 1, title, fontsize=14, color=WHITE, ha="center",
            fontweight="bold", path_effects=PE, zorder=10,
        )

    # ── Artistas dinamicos (se borran y redibujan cada frame) ─────
    _dynamic = []

    def _clear():
        """Borra todos los artistas dinamicos del frame anterior."""
        for a in _dynamic:
            try:
                a.remove()
            except Exception:
                pass
        _dynamic.clear()

    def _draw_players(ax, fdata):
        """Dibuja jugadores + balon + flechas de velocidad."""
        players = fdata[~fdata["is_ball"]]
        ball = fdata[fdata["is_ball"]]
        att_pl = players[players["team_id"] == att_team_id]
        def_pl = players[players["team_id"] != att_team_id]

        # Separar porteros del resto
        att_field = att_pl[~att_pl["person_id"].isin(gk_ids)]
        def_field = def_pl[~def_pl["person_id"].isin(gk_ids)]
        gks = players[players["person_id"].isin(gk_ids)]

        # Jugadores de campo (defensores primero, atacantes encima)
        for df, color in [(def_field, DEF), (att_field, ATT)]:
            if not df.empty:
                obj, = ax.plot(
                    df["x"].values, df["y"].values,
                    "o", ms=MS, color=color, markeredgecolor=WHITE,
                    markeredgewidth=1, alpha=0.9, zorder=5, linestyle="None",
                )
                _dynamic.append(obj)

        # Porteros en negro
        if not gks.empty:
            obj, = ax.plot(
                gks["x"].values, gks["y"].values,
                "o", ms=MS, color=GK, markeredgecolor=WHITE,
                markeredgewidth=1, alpha=0.9, zorder=5, linestyle="None",
            )
            _dynamic.append(obj)

        # Balon
        if not ball.empty:
            obj, = ax.plot(
                ball["x"].values, ball["y"].values,
                "o", ms=9, color=BALL_COLOR, markeredgecolor="black",
                markeredgewidth=0.8, zorder=7, linestyle="None",
            )
            _dynamic.append(obj)

        # Flechas de velocidad (solo jugadores con speed > 0.5 m/s)
        if "vx" in players.columns:
            for df, color in [(att_pl, ATT), (def_pl, DEF)]:
                valid = df.dropna(subset=["vx", "vy"])
                valid = valid[valid["speed"] > 0.5]
                if not valid.empty:
                    q = ax.quiver(
                        valid["x"].values, valid["y"].values,
                        valid["vx"].values, valid["vy"].values,
                        color=color, scale=120, scale_units="width",
                        width=0.003, headwidth=3.5, headlength=4,
                        headaxislength=3.5, alpha=0.55, zorder=3,
                    )
                    _dynamic.append(q)

    def _draw_voronoi(ax, fdata):
        """Dibuja poligonos de Voronoi coloreados por equipo."""
        polygons, teams = compute_voronoi_polygons(fdata, att_team_id)
        for poly, tid in zip(polygons, teams):
            color = ATT if tid == att_team_id else DEF
            # Poligono relleno semitransparente
            p = ax.fill(poly[:, 0], poly[:, 1], color=color, alpha=0.3, zorder=1)
            _dynamic.extend(p)
            # Borde blanco fino
            ln, = ax.plot(
                np.append(poly[:, 0], poly[0, 0]),
                np.append(poly[:, 1], poly[0, 1]),
                color=WHITE, lw=0.5, alpha=0.6, zorder=2,
            )
            _dynamic.append(ln)

    # ── Funcion de actualizacion (se llama cada frame) ────────────
    def _update(i):
        _clear()
        fc = frames[i]
        fdata = frame_data.get(fc, empty)

        # Mostrar el reloj
        if "time_s" in fdata.columns and not fdata.empty:
            t = float(fdata["time_s"].iloc[0])
            time_txt.set_text(f"{int(t // 60):02d}:{t % 60:04.1f}")

        if mode == "voronoi":
            _draw_voronoi(axes[0], fdata)
            _draw_players(axes[0], fdata)

        elif mode == "ppcf":
            # Actualizar heatmap PPCF
            ppcf_surf = _get_ppcf(fc)
            if ppcf_surf is not None:
                im.set_alpha(0.5)
                im.set_data(ppcf_surf)
            else:
                im.set_alpha(0.0)
            _draw_players(axes[0], fdata)

        elif mode == "split":
            # Izquierda: Voronoi
            _draw_voronoi(ax_vor, fdata)
            _draw_players(ax_vor, fdata)
            # Derecha: PPCF
            ppcf_surf = _get_ppcf(fc)
            if ppcf_surf is not None:
                im.set_alpha(0.5)
                im.set_data(ppcf_surf)
            else:
                im.set_alpha(0.0)
            _draw_players(ax_ppcf, fdata)

        return []

    # ── Crear y guardar la animacion ──────────────────────────────
    anim = animation.FuncAnimation(
        fig, _update, frames=len(frames), interval=1000 // fps, blit=False,
    )
    if save_path:
        anim.save(
            save_path, writer="ffmpeg", fps=fps, dpi=150,
            savefig_kwargs={"facecolor": BG},
        )
    return anim
