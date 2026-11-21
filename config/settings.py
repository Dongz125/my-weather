"""Application defaults and secure OpenWeather key loading."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

DEFAULT_LATITUDE = "10.8231"
DEFAULT_LONGITUDE = "106.6297"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "data" / "myweather.db"


def load_api_key(streamlit_secrets: Any | None = None) -> str | None:
    """Load the API key from Streamlit secrets or an environment variable."""
    if streamlit_secrets is not None:
        try:
            value = streamlit_secrets.get("OPENWEATHER_API_KEY")
            if value and str(value).strip():
                return str(value).strip()
        except Exception:
            # Streamlit raises its own exception when no secrets file exists.
            pass

    value = os.getenv("OPENWEATHER_API_KEY", "").strip()
    return value or None


__all__ = [
    "DATABASE_PATH",
    "DEFAULT_LATITUDE",
    "DEFAULT_LONGITUDE",
    "PROJECT_ROOT",
    "load_api_key",
]
