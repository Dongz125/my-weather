"""Current-weather access and defensive response parsing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .api_client import WeatherAPIError, request_json

CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


@dataclass(frozen=True)
class CurrentWeather:
    """Fields displayed by the current-weather user interface."""

    temperature: float | None
    feels_like: float | None
    humidity: float | None
    wind_speed: float | None
    description: str
    icon: str | None
    observed_at: int | None = None


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def parse_current_weather(payload: Any) -> CurrentWeather:
    """Extract display fields and tolerate optional or missing keys."""
    if not isinstance(payload, dict):
        raise WeatherAPIError("OpenWeather returned an invalid weather response.")

    main = payload.get("main") if isinstance(payload.get("main"), dict) else {}
    wind = payload.get("wind") if isinstance(payload.get("wind"), dict) else {}
    weather_items = payload.get("weather")
    weather = (
        weather_items[0]
        if isinstance(weather_items, list)
        and weather_items
        and isinstance(weather_items[0], dict)
        else {}
    )

    description = str(weather.get("description") or "No description available")
    icon = weather.get("icon")
    observed_at = payload.get("dt")

    return CurrentWeather(
        temperature=_number(main.get("temp")),
        feels_like=_number(main.get("feels_like")),
        humidity=_number(main.get("humidity")),
        wind_speed=_number(wind.get("speed")),
        description=description,
        icon=str(icon) if icon else None,
        observed_at=int(observed_at) if isinstance(observed_at, (int, float)) else None,
    )


def get_current_weather(latitude: float, longitude: float, api_key: str) -> CurrentWeather:
    """Fetch current weather in metric units with Vietnamese descriptions."""
    payload = request_json(
        CURRENT_WEATHER_URL,
        {
            "lat": latitude,
            "lon": longitude,
            "appid": api_key,
            "units": "metric",
            "lang": "vi",
        },
    )
    return parse_current_weather(payload)


__all__ = ["CurrentWeather", "WeatherAPIError", "get_current_weather", "parse_current_weather"]
