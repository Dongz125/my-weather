"""Framework-independent input validation for MyWeather."""

from __future__ import annotations

import math
from typing import Any


class CoordinateValidationError(ValueError):
    """Raised when latitude or longitude cannot be validated."""


def validate_coordinates(latitude: Any, longitude: Any) -> tuple[float, float]:
    """Convert coordinate values to floats and enforce geographic bounds."""
    if latitude is None or longitude is None:
        raise CoordinateValidationError("Latitude and longitude are required.")
    if isinstance(latitude, bool) or isinstance(longitude, bool):
        raise CoordinateValidationError("Coordinates must be numeric values.")

    try:
        lat = float(str(latitude).strip())
        lon = float(str(longitude).strip())
    except (TypeError, ValueError) as exc:
        raise CoordinateValidationError("Coordinates must be numeric values.") from exc

    if not math.isfinite(lat) or not math.isfinite(lon):
        raise CoordinateValidationError("Coordinates must be finite numbers.")
    if not (-90.0 <= lat <= 90.0):
        raise CoordinateValidationError("Latitude must be between -90 and 90.")
    if not (-180.0 <= lon <= 180.0):
        raise CoordinateValidationError("Longitude must be between -180 and 180.")

    return lat, lon


__all__ = ["CoordinateValidationError", "validate_coordinates"]
