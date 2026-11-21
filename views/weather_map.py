"""Folium map construction for location and OpenWeather tile overlays."""

from __future__ import annotations

from urllib.parse import quote

import folium

# Identifiers documented by OpenWeather Weather Maps 1.0.
WEATHER_LAYERS = {
    "Temperature": "temp_new",
    "Wind speed": "wind_new",
    "Clouds": "clouds_new",
    "Precipitation": "precipitation_new",
}


def create_weather_map(
    latitude: float,
    longitude: float,
    api_key: str,
    layer_label: str = "Temperature",
    location_label: str = "Selected location",
) -> folium.Map:
    """Create an interactive map with one selectable OpenWeather overlay.

    OpenWeather Weather Maps 1.0 authenticates tile requests in the URL. The
    URL is therefore delivered to the browser by Folium; see README security
    notes for production mitigations.
    """
    if layer_label not in WEATHER_LAYERS:
        raise ValueError(f"Unsupported weather layer: {layer_label}")

    weather_map = folium.Map(
        location=[latitude, longitude],
        zoom_start=8,
        tiles="OpenStreetMap",
        control_scale=True,
    )
    folium.Marker(
        [latitude, longitude],
        tooltip=location_label,
        popup=f"{location_label}<br>{latitude:.5f}, {longitude:.5f}",
        icon=folium.Icon(color="blue", icon="cloud"),
    ).add_to(weather_map)

    layer_id = WEATHER_LAYERS[layer_label]
    safe_key = quote(api_key, safe="")
    tile_url = (
        f"https://tile.openweathermap.org/map/{layer_id}/"
        f"{{z}}/{{x}}/{{y}}.png?appid={safe_key}"
    )
    folium.TileLayer(
        tiles=tile_url,
        name=f"OpenWeather · {layer_label}",
        attr="OpenWeather",
        overlay=True,
        control=True,
        opacity=0.65,
        show=True,
    ).add_to(weather_map)
    folium.LayerControl(collapsed=False).add_to(weather_map)
    return weather_map


__all__ = ["WEATHER_LAYERS", "create_weather_map"]
