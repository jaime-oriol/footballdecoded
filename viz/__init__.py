"""
Visualization module for FootballDecoded.

Pipeline: match_data/match_data_v2 generate 5 CSVs from raw events,
then plot modules (pass_network, shot_xg, etc.) consume those CSVs
to produce professional match analysis figures.

Design system: background #313332, colormap deepskyblue->tomato,
font DejaVu Sans, Opta coordinate system (0-100).
"""

__all__ = [
    "extract_match_complete",
    "plot_pass_network",
    "plot_pass_flow",
    "plot_pass_hull",
    "plot_shot_xg",
    "plot_shot_report",
    "create_player_analysis_complete",
]
