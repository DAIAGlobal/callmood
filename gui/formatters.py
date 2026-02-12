"""Formatting helpers for DAIA GUI.
Backend computes metrics; UI only displays.
"""
from typing import Optional, Union

Number = Union[int, float]


def format_percentage(value: Optional[Number], decimals: int = 2) -> str:
    """Render percentages (value already in 0-100)."""
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.{decimals}f}%"
    except (TypeError, ValueError):
        return "N/A"


def format_seconds(value: Optional[Number]) -> str:
    """Render seconds as mm:ss or N/A."""
    if value is None:
        return "N/A"
    try:
        total = float(value)
    except (TypeError, ValueError):
        return "N/A"
    if total < 0:
        return "N/A"
    minutes, seconds = divmod(int(total), 60)
    return f"{minutes:02d}:{seconds:02d}"


def format_words(value: Optional[Number]) -> str:
    """Render word counts with thousand separator."""
    if value is None:
        return "N/A"
    try:
        return f"{int(value):,}".replace(",", ".")
    except (TypeError, ValueError):
        return "N/A"
