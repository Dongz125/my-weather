"""OpenWeather air-pollution access and AQI interpretation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .api_client import WeatherAPIError, request_json

AIR_POLLUTION_URL = "https://api.openweathermap.org/data/2.5/air_pollution"
AQI_LABELS = {
    1: "Good",
    2: "Fair",
    3: "Moderate",
    4: "Poor",
    5: "Very Poor",
}
POLLUTANT_KEYS = ("pm2_5", "pm10", "co", "no2", "o3", "so2", "no", "nh3")


@dataclass(frozen=True)
class AirQuality:
    """OpenWeather AQI and pollutant concentrations in micrograms per m³."""

    aqi: int
    label: str
    components: dict[str, float | None] = field(default_factory=dict)
    observed_at: int | None = None


def aqi_label(aqi: int) -> str:
    """Return the official label for OpenWeather's 1–5 AQI scale."""
    return AQI_LABELS.get(aqi, "Unknown")


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def parse_air_quality(payload: Any) -> AirQuality:
    """Parse the latest Air Pollution API item and its concentrations."""
    if not isinstance(payload, dict) or not isinstance(payload.get("list"), list):
        raise WeatherAPIError("OpenWeather returned an invalid air-quality response.")
    if not payload["list"]:
        raise WeatherAPIError("No air-quality data is available for this location.")

    item = payload["list"][0]
    if not isinstance(item, dict):
        raise WeatherAPIError("OpenWeather returned an invalid air-quality response.")
    main = item.get("main") if isinstance(item.get("main"), dict) else {}
    components = (
        item.get("components") if isinstance(item.get("components"), dict) else {}
    )

    try:
        aqi = int(main.get("aqi"))
    except (TypeError, ValueError) as exc:
        raise WeatherAPIError("The air-quality response does not include a valid AQI.") from exc

    observed_at = item.get("dt")
    return AirQuality(
        aqi=aqi,
        label=aqi_label(aqi),
        components={key: _number(components.get(key)) for key in POLLUTANT_KEYS},
        observed_at=int(observed_at) if isinstance(observed_at, (int, float)) else None,
    )


def get_air_quality(latitude: float, longitude: float, api_key: str) -> AirQuality:
    """Fetch current OpenWeather air-quality data for coordinates."""
    payload = request_json(
        AIR_POLLUTION_URL,
        {"lat": latitude, "lon": longitude, "appid": api_key},
    )
    return parse_air_quality(payload)


__all__ = [
    "AQI_LABELS",
    "AirQuality",
    "WeatherAPIError",
    "aqi_label",
    "get_air_quality",
    "parse_air_quality",
]
