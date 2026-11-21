"""Display formatting helpers shared by Streamlit views."""

from __future__ import annotations

from typing import Any


def display_value(value: Any, unit: str = "", decimals: int = 1) -> str:
    """Return a friendly display value while safely handling missing data."""
    if value is None:
        return "N/A"
    if isinstance(value, (int, float)):
        return f"{value:.{decimals}f}{unit}"
    return f"{value}{unit}"


__all__ = ["display_value"]
