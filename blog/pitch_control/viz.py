"""
viz - Voronoi, superficies PPCF y plots de comparacion.

Estilo visual del repo FD:
    Fondo: #313332, Atacante: deepskyblue, Defensor: tomato, Portero: negro
    Colormap PPCF: rojo oscuro -> gris -> azul oscuro (DEF -> neutro -> ATT)
    Voronoi: poligonos rellenos con colores de equipo

Coordenadas en metros centradas en (0,0). Campo 105m x 68m.
"""

from typing import Dict, List, Optional, Tuple

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.colors import LinearSegmentedColormap, to_rgba
from scipy.spatial import Voronoi

from blog.pitch_control.pitch_control import PITCH_LENGTH, PITCH_WIDTH


# ── ESTILO ─────────────────────────────────────────────────────────────

BG = "#313332"
WHITE = "white"
FONT = "DejaVu Sans"
ATT = "deepskyblue"     # color atacante
DEF = "tomato"          # color defensor
GK = "black"            # color portero
BALL_COLOR = WHITE

plt.style.use("default")
plt.rcParams.update({
    "font.family": FONT, "font.size": 10,
    "figure.dpi": 100, "savefig.dpi": 400, "savefig.bbox": "tight",
    "axes.facecolor": BG, "figure.facecolor": BG,
    "text.color": WHITE, "axes.labelcolor": WHITE,
    "xtick.color": WHITE, "ytick.color": WHITE,
})

# Efecto de contorno para textos
PE = [pe.withStroke(linewidth=1.5, foreground="black"), pe.Normal()]
MS = 14  # tamano de marcador

# Colormap PPCF: rojo (defensor) -> gris (neutro) -> azul (atacante)
PPCF_CMAP = LinearSegmentedColormap.from_list("ppcf", ["#8B0000", "#777777", "#004D98"])


# ── DIBUJAR CAMPO ─────────────────────────────────────────────────────

def draw_pitch(
    ax: plt.Axes,
    pitch_length: float = PITCH_LENGTH,
    pitch_width: float = PITCH_WIDTH,
    color: str = WHITE,
    lw: float = 1.0,
):
    """Dibujar campo de futbol centrado en (0,0)."""
    L, W = pitch_length / 2, pitch_width / 2

    # Rectangulo exterior
    ax.plot([-L, L, L, -L, -L], [-W, -W, W, W, -W], color=color, lw=lw, zorder=2)
    # Linea central + circulo central
    ax.plot([0, 0], [-W, W], color=color, lw=lw, zorder=2)
    circle = plt.Circle((0, 0), 9.15, fill=False, ec=color, lw=lw, zorder=2)
    ax.add_patch(circle)
    ax.plot(0, 0, "o", ms=3, color=color, zorder=2)

    # Areas (16.5m desde linea de gol, 40.32m de ancho)
    pa_w = 20.16  # mitad del ancho del area
    pa_d = 16.5   # profundidad
    for sign in [-1, 1]:
        x0 = sign * L
        x1 = sign * (L - pa_d)
        ax.plot([x0, x1, x1, x0], [-pa_w, -pa_w, pa_w, pa_w], color=color, lw=lw, zorder=2)
        # Area pequena (5.5m desde linea de gol, 18.32m de ancho)
        ga_w = 9.16
        ga_d = 5.5
        x2 = sign * (L - ga_d)
        ax.plot([x0, x2, x2, x0], [-ga_w, -ga_w, ga_w, ga_w], color=color, lw=lw, zorder=2)
        # Punto de penalti
        ax.plot(sign * (L - 11), 0, "o", ms=3, color=color, zorder=2)
        # Arco de penalti (solo la parte que sale fuera del area)
        theta = np.linspace(-np.pi/2, np.pi/2, 50)
        arc_x = sign * (L - 11) + 9.15 * np.cos(theta) * sign
        arc_y = 9.15 * np.sin(theta)
        inside_pa = np.abs(arc_x) > (L - pa_d)
        arc_x[inside_pa] = np.nan
        ax.plot(arc_x, arc_y, color=color, lw=lw, zorder=2)

    # Porterias
    for sign in [-1, 1]:
        ax.plot([sign * L, sign * (L + 1.5)], [-3.66, -3.66], color=color, lw=lw * 1.5, zorder=2)
        ax.plot([sign * L, sign * (L + 1.5)], [3.66, 3.66], color=color, lw=lw * 1.5, zorder=2)
        ax.plot([sign * (L + 1.5), sign * (L + 1.5)], [-3.66, 3.66], color=color, lw=lw * 1.5, zorder=2)

    ax.set_xlim(-L - 3, L + 3)
    ax.set_ylim(-W - 3, W + 3)
    ax.set_aspect("equal")
    ax.axis("off")


def make_pitch(
    figsize: Tuple[float, float] = (16, 10.4),
    ax: Optional[plt.Axes] = None,
) -> Tuple[plt.Figure, plt.Axes]:
    """Crear figura con campo dibujado. Devuelve (fig, ax)."""
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
        fig.set_facecolor(BG)
    else:
        fig = ax.get_figure()
    draw_pitch(ax)
    return fig, ax


# ── JUGADORES ──────────────────────────────────────────────────────────

def plot_players(
    ax: plt.Axes,
    frame_data: pd.DataFrame,
    att_team_id: str,
    gk_ids: Optional[set] = None,
    names: Optional[Dict[str, str]] = None,
    show_names: bool = False,
    ms: int = MS,
):
    """Pintar jugadores, porteros, balon y flechas de velocidad."""
    players = frame_data[~frame_data["is_ball"]]
    ball = frame_data[frame_data["is_ball"]]
    att = players[players["team_id"] == att_team_id]
    def_ = players[players["team_id"] != att_team_id]

    if gk_ids is None:
        gk_ids = set()

    # Separar porteros del resto
    att_field = att[~att["person_id"].isin(gk_ids)]
    def_field = def_[~def_["person_id"].isin(gk_ids)]
    gks = players[players["person_id"].isin(gk_ids)]

    # Pintar jugadores de campo
    for df, color in [(def_field, DEF), (att_field, ATT)]:
        if not df.empty:
            ax.plot(
                df["x"].values, df["y"].values,
                "o", ms=ms, color=color, markeredgecolor=WHITE,
                markeredgewidth=1, alpha=0.9, zorder=5, linestyle="None",
            )
    # Porteros en negro
    if not gks.empty:
        ax.plot(
            gks["x"].values, gks["y"].values,
            "o", ms=ms, color=GK, markeredgecolor=WHITE,
            markeredgewidth=1, alpha=0.9, zorder=5, linestyle="None",
        )

    # Balon en blanco
    if not ball.empty:
        ax.plot(
            ball["x"].values, ball["y"].values,
            "o", ms=9, color=BALL_COLOR, markeredgecolor="black",
            markeredgewidth=0.8, zorder=7, linestyle="None",
        )

    # Flechas de velocidad
    if "vx" in players.columns:
        for df, color in [(att, ATT), (def_, DEF)]:
            valid = df.dropna(subset=["vx", "vy"])
            valid = valid[valid["speed"] > 0.5]  # ignorar parados
            if not valid.empty:
                ax.quiver(
                    valid["x"].values, valid["y"].values,
                    valid["vx"].values, valid["vy"].values,
                    color=color, scale=120, scale_units="width",
                    width=0.003, headwidth=3.5, headlength=4, headaxislength=3.5,
                    alpha=0.55, zorder=3,
                )

    # Nombres (apellido)
    if show_names and names:
        for _, row in players.iterrows():
            name = names.get(row["person_id"], "")
            if name:
                ax.text(
                    row["x"], row["y"] - 2.5, name.split()[-1],
                    fontsize=7, ha="center", color=WHITE,
                    fontweight="bold", path_effects=PE, zorder=8,
                )


# ── VORONOI ────────────────────────────────────────────────────────────

def compute_voronoi_polygons(
    frame_data: pd.DataFrame,
    att_team_id: str,
    pitch_length: float = PITCH_LENGTH,
    pitch_width: float = PITCH_WIDTH,
) -> Tuple[List[np.ndarray], List[str]]:
    """Calcular poligonos Voronoi recortados al campo.

    Devuelve (poligonos, team_ids): listas de vertices y equipo de cada uno.
    """
    players = frame_data[~frame_data["is_ball"]]
    positions = players[["x", "y"]].values.astype(np.float64)
    team_ids = players["team_id"].values

    if len(positions) < 3:
        return [], []

    L, W = pitch_length / 2, pitch_width / 2

    # Puntos espejo lejos del campo para que todos los Voronoi sean finitos
    mirror = np.array([[-3 * L, 0], [3 * L, 0], [0, -3 * W], [0, 3 * W]])
    all_points = np.vstack([positions, mirror])

    vor = Voronoi(all_points)

    # Recortar cada poligono al rectangulo del campo
    polygons = []
    polygon_teams = []
    for i in range(len(positions)):
        region_idx = vor.point_region[i]
        region = vor.regions[region_idx]
        if -1 in region or len(region) == 0:
            continue
        verts = vor.vertices[region]
        clipped = _clip_polygon_to_rect(verts, -L, L, -W, W)
        if len(clipped) >= 3:
            polygons.append(clipped)
            polygon_teams.append(team_ids[i])

    return polygons, polygon_teams


def plot_voronoi(
    ax: plt.Axes,
    frame_data: pd.DataFrame,
    att_team_id: str,
    alpha: float = 0.3,
    edge_alpha: float = 0.6,
):
    """Pintar diagrama de Voronoi relleno. Atacante en azul, defensor en rojo."""
    polygons, teams = compute_voronoi_polygons(frame_data, att_team_id)

    for poly, tid in zip(polygons, teams):
        color = ATT if tid == att_team_id else DEF
        ax.fill(poly[:, 0], poly[:, 1], color=color, alpha=alpha, zorder=1)
        ax.plot(
            np.append(poly[:, 0], poly[0, 0]),
            np.append(poly[:, 1], poly[0, 1]),
            color=WHITE, lw=0.5, alpha=edge_alpha, zorder=2,
        )


def _clip_polygon_to_rect(
    verts: np.ndarray, xmin: float, xmax: float, ymin: float, ymax: float,
) -> np.ndarray:
    """Recorte Sutherland-Hodgman de poligono a rectangulo."""
    poly = list(verts)
    for edge in [
        (lambda p: p[0] >= xmin, lambda p, q: _intersect_x(p, q, xmin)),
        (lambda p: p[0] <= xmax, lambda p, q: _intersect_x(p, q, xmax)),
        (lambda p: p[1] >= ymin, lambda p, q: _intersect_y(p, q, ymin)),
        (lambda p: p[1] <= ymax, lambda p, q: _intersect_y(p, q, ymax)),
    ]:
        inside_fn, intersect_fn = edge
        if not poly:
            break
        new_poly = []
        for i in range(len(poly)):
            curr = poly[i]
            prev = poly[i - 1]
            if inside_fn(curr):
                if not inside_fn(prev):
                    new_poly.append(intersect_fn(prev, curr))
                new_poly.append(curr)
            elif inside_fn(prev):
                new_poly.append(intersect_fn(prev, curr))
        poly = new_poly
    return np.array(poly) if poly else np.empty((0, 2))


def _intersect_x(p, q, x):
    """Interseccion del segmento p-q con la recta vertical x."""
    t = (x - p[0]) / (q[0] - p[0] + 1e-12)
    return np.array([x, p[1] + t * (q[1] - p[1])])


def _intersect_y(p, q, y):
    """Interseccion del segmento p-q con la recta horizontal y."""
    t = (y - p[1]) / (q[1] - p[1] + 1e-12)
    return np.array([p[0] + t * (q[0] - p[0]), y])


# ── SUPERFICIE PPCF ───────────────────────────────────────────────────

def plot_ppcf(
    ax: plt.Axes,
    ppcf: np.ndarray,
    xgrid: np.ndarray,
    ygrid: np.ndarray,
    alpha: float = 0.5,
    cmap=None,
):
    """Pintar superficie PPCF sobre el campo."""
    if cmap is None:
        cmap = PPCF_CMAP
    L, W = PITCH_LENGTH / 2, PITCH_WIDTH / 2
    ax.imshow(
        ppcf, extent=[-L, L, -W, W], origin="lower",
        interpolation="spline36", cmap=cmap, alpha=alpha,
        vmin=0, vmax=1, zorder=1, aspect="auto",
    )


# ── PLOTS COMPUESTOS ──────────────────────────────────────────────────

def plot_frame_voronoi(
    frame_data: pd.DataFrame,
    att_team_id: str,
    gk_ids: Optional[set] = None,
    names: Optional[Dict[str, str]] = None,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> Tuple[plt.Figure, plt.Axes]:
    """Frame completo: Voronoi + jugadores."""
    fig, ax = make_pitch()
    plot_voronoi(ax, frame_data, att_team_id)
    plot_players(ax, frame_data, att_team_id, gk_ids, names, show_names=True)
    if title:
        ax.set_title(title, color=WHITE, fontsize=14, fontweight="bold", pad=10)
    if save_path:
        fig.savefig(save_path, dpi=400, bbox_inches="tight", facecolor=BG)
    return fig, ax


def plot_frame_ppcf(
    frame_data: pd.DataFrame,
    ppcf: np.ndarray,
    xgrid: np.ndarray,
    ygrid: np.ndarray,
    att_team_id: str,
    gk_ids: Optional[set] = None,
    names: Optional[Dict[str, str]] = None,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> Tuple[plt.Figure, plt.Axes]:
    """Frame completo: superficie PPCF + jugadores."""
    fig, ax = make_pitch()
    plot_ppcf(ax, ppcf, xgrid, ygrid)
    plot_players(ax, frame_data, att_team_id, gk_ids, names, show_names=True)
    if title:
        ax.set_title(title, color=WHITE, fontsize=14, fontweight="bold", pad=10)
    if save_path:
        fig.savefig(save_path, dpi=400, bbox_inches="tight", facecolor=BG)
    return fig, ax


def plot_comparison(
    frame_data: pd.DataFrame,
    ppcf: np.ndarray,
    xgrid: np.ndarray,
    ygrid: np.ndarray,
    att_team_id: str,
    gk_ids: Optional[set] = None,
    names: Optional[Dict[str, str]] = None,
    title: Optional[str] = None,
    save_path: Optional[str] = None,
) -> Tuple[plt.Figure, np.ndarray]:
    """Comparativa lado a lado: Voronoi (izquierda) vs PPCF (derecha)."""
    fig, axes = plt.subplots(1, 2, figsize=(24, 10.4))
    fig.set_facecolor(BG)

    # Izquierda: Voronoi
    draw_pitch(axes[0])
    plot_voronoi(axes[0], frame_data, att_team_id)
    plot_players(axes[0], frame_data, att_team_id, gk_ids, names)
    axes[0].set_title("Diagrama de Voronoi", color=WHITE, fontsize=14,
                       fontweight="bold", pad=10)

    # Derecha: PPCF
    draw_pitch(axes[1])
    plot_ppcf(axes[1], ppcf, xgrid, ygrid)
    plot_players(axes[1], frame_data, att_team_id, gk_ids, names)
    axes[1].set_title("Pitch Control (PPCF)", color=WHITE, fontsize=14,
                       fontweight="bold", pad=10)

    if title:
        fig.suptitle(title, color=WHITE, fontsize=16, fontweight="bold", y=0.98)

    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=400, bbox_inches="tight", facecolor=BG)
    return fig, axes
