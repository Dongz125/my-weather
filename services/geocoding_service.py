"""Reverse-geocoding access and response parsing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .api_client import WeatherAPIError, request_json

REVERSE_GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/reverse"


@dataclass(frozen=True)
class LocationInfo:
    """A resolved geographic place returned by OpenWeather."""

    name: str
    country: str
    state: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    @property
    def label(self) -> str:
        """Build a readable city/state/country label."""
        parts = [self.name]
        if self.state:
            parts.append(self.state)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)


def parse_reverse_geocoding(payload: Any) -> LocationInfo | None:
    """Parse the first reverse-geocoding result, or return ``None``."""
    if not isinstance(payload, list) or not payload:
        return None

    item = payload[0]
    if not isinstance(item, dict):
        return None

    name = str(item.get("name") or "Unknown location")
    country = str(item.get("country") or "")
    state = item.get("state")
    return LocationInfo(
        name=name,
        state=str(state) if state else None,
        country=country,
        latitude=_optional_float(item.get("lat")),
        longitude=_optional_float(item.get("lon")),
    )


def reverse_geocode(latitude: float, longitude: float, api_key: str) -> LocationInfo | None:
    """Resolve coordinates to one nearby place using OpenWeather Geocoding."""
    payload = request_json(
        REVERSE_GEOCODING_URL,
        {
            "lat": latitude,
            "lon": longitude,
            "limit": 1,
            "appid": api_key,
        },
    )
    return parse_reverse_geocoding(payload)


def _optional_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


__all__ = ["LocationInfo", "WeatherAPIError", "parse_reverse_geocoding", "reverse_geocode"]
