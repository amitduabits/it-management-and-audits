"""
Risk Module - Weighted risk calculation and visualization.

Provides risk quantification through:
    - RiskEngine: Weighted risk scoring across 6 categories
    - RiskMatrix: 5x5 risk matrix with color-coded output
"""

from src.risk.risk_engine import RiskEngine
from src.risk.risk_matrix import RiskMatrix

__all__ = ["RiskEngine", "RiskMatrix"]
