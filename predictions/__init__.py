"""World Cup 2026 prediction model.

Hybrid ensemble: Dixon-Coles (statistical core) + Squad Power Index
(player aggregation) + GradientBoosting (match context), combined via
calibrated weighted average. Monte Carlo tournament simulation (100K runs).
"""

__version__ = "0.1.0"
