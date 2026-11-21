"""MyWeather Streamlit application entry point and workflow coordinator."""

from __future__ import annotations

import streamlit as st
from streamlit_folium import st_folium

from config.settings import (
    DATABASE_PATH,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    load_api_key,
)
from core.validation import CoordinateValidationError, validate_coordinates
from data.database import initialize_database
from services.air_quality_service import AirQuality, get_air_quality
from services.api_client import WeatherAPIError
from services.forecast_service import ForecastData, get_forecast
from services.geocoding_service import LocationInfo, reverse_geocode
from services.weather_service import CurrentWeather, get_current_weather
from views.dashboard import (
    configure_page,
    render_air_quality,
    render_coordinate_help,
    render_current_weather,
    render_custom_widget,
    render_errors,
    render_forecast,
    render_location,
)
from views.account import render_account_sidebar
from views.saved_locations import (
    render_save_location,
    render_saved_locations_sidebar,
)
from views.weather_map import WEATHER_LAYERS, create_weather_map


@st.cache_data(ttl=600, show_spinner=False)
def cached_reverse_geocode(
    latitude: float, longitude: float, _api_key: str
) -> LocationInfo | None:
    """Cache reverse-geocoding results for ten minutes."""
    return reverse_geocode(latitude, longitude, _api_key)


@st.cache_data(ttl=600, show_spinner=False)
def cached_current_weather(
    latitude: float, longitude: float, _api_key: str
) -> CurrentWeather:
    """Cache current weather for ten minutes."""
    return get_current_weather(latitude, longitude, _api_key)


@st.cache_data(ttl=600, show_spinner=False)
def cached_air_quality(latitude: float, longitude: float, _api_key: str) -> AirQuality:
    """Cache current air-quality data for ten minutes."""
    return get_air_quality(latitude, longitude, _api_key)


@st.cache_data(ttl=1800, show_spinner=False)
def cached_forecast(latitude: float, longitude: float, _api_key: str) -> ForecastData:
    """Cache forecast data for thirty minutes."""
    return get_forecast(latitude, longitude, _api_key)


def collect_data(latitude: float, longitude: float, api_key: str) -> dict[str, object]:
    """Fetch each feature independently so one failure does not hide all results."""
    result: dict[str, object] = {"latitude": latitude, "longitude": longitude}
    operations = {
        "location": cached_reverse_geocode,
        "weather": cached_current_weather,
        "air_quality": cached_air_quality,
        "forecast": cached_forecast,
    }
    errors: dict[str, str] = {}
    for name, operation in operations.items():
        try:
            result[name] = operation(latitude, longitude, api_key)
        except WeatherAPIError as exc:
            errors[name] = str(exc)
    result["errors"] = errors
    return result


def main() -> None:
    """Render the application and coordinate its data workflow."""
    configure_page()
    initialize_database(DATABASE_PATH)

    user = render_account_sidebar(DATABASE_PATH)
    selected_location = (
        render_saved_locations_sidebar(user, DATABASE_PATH) if user else None
    )

    st.session_state.setdefault("latitude_input", DEFAULT_LATITUDE)
    st.session_state.setdefault("longitude_input", DEFAULT_LONGITUDE)
    if selected_location is not None:
        st.session_state["latitude_input"] = str(selected_location.latitude)
        st.session_state["longitude_input"] = str(selected_location.longitude)

    st.write("")
    render_coordinate_help()

    with st.form("coordinate_form"):
        first, second = st.columns(2)
        latitude_text = first.text_input("Latitude", key="latitude_input")
        longitude_text = second.text_input("Longitude", key="longitude_input")
        submitted = st.form_submit_button("Look up weather", type="primary")

    api_key = load_api_key(st.secrets)
    if not api_key:
        st.warning(
            "Configure OPENWEATHER_API_KEY in `.streamlit/secrets.toml` or as an "
            "environment variable before looking up weather. See README.md for setup."
        )

    if selected_location is not None and api_key:
        with st.spinner(f"Loading {selected_location.label}…"):
            st.session_state["weather_result"] = collect_data(
                selected_location.latitude, selected_location.longitude, api_key
            )
    elif submitted:
        try:
            latitude, longitude = validate_coordinates(latitude_text, longitude_text)
        except CoordinateValidationError as exc:
            st.error(str(exc))
        else:
            if api_key:
                with st.spinner("Contacting OpenWeather…"):
                    st.session_state["weather_result"] = collect_data(
                        latitude, longitude, api_key
                    )

    data = st.session_state.get("weather_result")
    if not isinstance(data, dict):
        st.caption("Enter coordinates and select **Look up weather** to begin.")
        return

    errors = data.get("errors", {})
    if isinstance(errors, dict):
        render_errors(errors)
    location_label = render_location(data)
    render_save_location(user, data, DATABASE_PATH)
    weather = data.get("weather") if isinstance(data.get("weather"), CurrentWeather) else None
    air_quality = (
        data.get("air_quality") if isinstance(data.get("air_quality"), AirQuality) else None
    )
    forecast = data.get("forecast") if isinstance(data.get("forecast"), ForecastData) else None

    render_current_weather(weather)
    render_custom_widget(weather, location_label)

    st.subheader("Weather map")
    selected_layer = st.selectbox("Overlay", list(WEATHER_LAYERS))
    if api_key:
        weather_map = create_weather_map(
            data["latitude"], data["longitude"], api_key, selected_layer, location_label
        )
        st_folium(weather_map, use_container_width=True, height=500, returned_objects=[])
        st.caption(
            "OpenWeather Weather Maps 1.0 tiles. The provider requires the API key in "
            "browser tile URLs; read the README security note before production use."
        )

    render_air_quality(air_quality)
    render_forecast(forecast)


if __name__ == "__main__":
    main()
