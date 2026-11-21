"""Five-day/three-hour forecast access and local-time conversion."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from .api_client import WeatherAPIError, request_json

FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


@dataclass(frozen=True)
class ForecastPoint:
    """One three-hour forecast point expressed in the location's UTC offset."""

    local_time: datetime
    temperature: float | None
    humidity: float | None
    wind_speed: float | None


@dataclass(frozen=True)
class ForecastData:
    """Forecast points plus the UTC offset reported for the selected city."""

    points: list[ForecastPoint]
    timezone_offset_seconds: int


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def parse_forecast(payload: Any) -> ForecastData:
    """Parse forecast rows and convert Unix UTC timestamps to local time."""
    if not isinstance(payload, dict) or not isinstance(payload.get("list"), list):
        raise WeatherAPIError("OpenWeather returned an invalid forecast response.")

    city = payload.get("city") if isinstance(payload.get("city"), dict) else {}
    try:
        offset_seconds = int(city.get("timezone", 0))
    except (TypeError, ValueError):
        offset_seconds = 0

    # datetime.timezone only accepts offsets strictly within 24 hours.
    if not -86399 <= offset_seconds <= 86399:
        offset_seconds = 0
    location_timezone = timezone(timedelta(seconds=offset_seconds))

    points: list[ForecastPoint] = []
    for item in payload["list"]:
        if not isinstance(item, dict) or not isinstance(item.get("dt"), (int, float)):
            continue
        main = item.get("main") if isinstance(item.get("main"), dict) else {}
        wind = item.get("wind") if isinstance(item.get("wind"), dict) else {}
        local_time = datetime.fromtimestamp(item["dt"], tz=timezone.utc).astimezone(
            location_timezone
        )
        points.append(
            ForecastPoint(
                local_time=local_time,
                temperature=_number(main.get("temp")),
                humidity=_number(main.get("humidity")),
                wind_speed=_number(wind.get("speed")),
            )
        )

    if not points:
        raise WeatherAPIError("No usable forecast points are available for this location.")
    return ForecastData(points=points, timezone_offset_seconds=offset_seconds)


def get_forecast(latitude: float, longitude: float, api_key: str) -> ForecastData:
    """Fetch the free 5-day/3-hour metric forecast."""
    payload = request_json(
        FORECAST_URL,
        {
            "lat": latitude,
            "lon": longitude,
            "appid": api_key,
            "units": "metric",
        },
    )
    return parse_forecast(payload)


__all__ = ["ForecastData", "ForecastPoint", "get_forecast", "parse_forecast"]
