"""Reusable Streamlit presentation functions for the MyWeather dashboard."""

from __future__ import annotations

from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

from core.formatting import display_value
from services.air_quality_service import AirQuality
from services.forecast_service import ForecastData
from services.geocoding_service import LocationInfo
from services.weather_service import CurrentWeather


def configure_page() -> None:
    """Configure the page and apply lightweight dashboard styling."""
    st.set_page_config(page_title="MyWeather", page_icon="🌦️", layout="wide")
    st.markdown(
        """
        <style>
        .block-container {padding-top: 2rem; padding-bottom: 3rem;}
        .hero {padding: 1.1rem 1.3rem; border-radius: 16px;
               background: linear-gradient(120deg, #0b5ea8, #28a6c7); color: white;}
        .hero h1 {margin: 0; font-size: 2.25rem;}
        .hero p {margin: .35rem 0 0; opacity: .92;}
        [data-testid="stMetric"] {background: rgba(120, 150, 180, .09);
                                  border-radius: 12px; padding: .8rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """<div class="hero"><h1>🌦️ MyWeather</h1>
        <p>Current weather, map layers, air quality, and a five-day forecast.</p></div>""",
        unsafe_allow_html=True,
    )


def render_coordinate_help() -> None:
    """Explain how to copy coordinates from Google Maps."""
    with st.expander("How to get latitude and longitude from Google Maps"):
        st.markdown(
            "1. Open Google Maps and find your location.\n"
            "2. Right-click the exact point (or press and hold on mobile).\n"
            "3. Click the coordinate pair to copy it.\n"
            "4. Paste the first number as latitude and the second as longitude.\n\n"
            "No Google Maps API key is needed; you submit the copied coordinates directly."
        )


def render_location(data: dict[str, object]) -> str:
    """Render the resolved location or a coordinate fallback."""
    location = data.get("location")
    if isinstance(location, LocationInfo):
        st.success(f"Resolved location: **{location.label}**")
        return location.label
    if "location" not in data.get("errors", {}):
        st.warning("Reverse geocoding returned no location for these coordinates.")
    return f"{data['latitude']:.4f}, {data['longitude']:.4f}"


def render_current_weather(weather: CurrentWeather | None) -> None:
    """Render current weather metrics and the provider icon."""
    st.subheader("Current weather")
    if weather is None:
        return
    left, right = st.columns([1, 5])
    with left:
        if weather.icon:
            st.image(
                f"https://openweathermap.org/img/wn/{weather.icon}@2x.png",
                width=100,
                caption=weather.description.capitalize(),
            )
        else:
            st.caption(weather.description.capitalize())
    with right:
        columns = st.columns(4)
        columns[0].metric("Temperature", display_value(weather.temperature, " °C"))
        columns[1].metric("Feels like", display_value(weather.feels_like, " °C"))
        columns[2].metric("Humidity", display_value(weather.humidity, " %", 0))
        columns[3].metric("Wind speed", display_value(weather.wind_speed, " m/s"))


def render_custom_widget(weather: CurrentWeather | None, location_label: str) -> None:
    """Render a safe coordinate-friendly alternative to the official widget."""
    st.subheader("Weather summary widget")
    if weather is None:
        return
    safe_location = escape(location_label)
    safe_description = escape(weather.description.capitalize())
    temperature = escape(display_value(weather.temperature, " °C"))
    humidity = escape(display_value(weather.humidity, " %", 0))
    widget_html = f"""
        <div style="font-family:Arial,sans-serif;border-radius:18px;padding:22px;
          color:white;background:linear-gradient(135deg,#153d69,#1f98b5);">
          <div style="font-size:14px;opacity:.78">CUSTOM WEATHER SUMMARY</div>
          <div style="font-size:25px;font-weight:700;margin-top:5px">{safe_location}</div>
          <div style="display:flex;gap:30px;align-items:end;margin-top:14px">
            <span style="font-size:44px;font-weight:700">{temperature}</span>
            <span style="font-size:18px;padding-bottom:7px">{safe_description}</span>
          </div>
          <div style="margin-top:10px;opacity:.9">Humidity: {humidity}</div>
        </div>
        """
    st.iframe(
        widget_html,
        width="stretch",
        height=190,
        alt=f"Weather summary for {location_label}",
    )
    st.caption(
        "Equivalent custom summary—not the official OpenWeather widget. "
        "It avoids embedding a third-party script and works directly with coordinates."
    )


def render_air_quality(air_quality: AirQuality | None) -> None:
    """Render OpenWeather AQI and pollutant concentrations."""
    st.subheader("Air quality")
    if air_quality is None:
        return
    st.metric("OpenWeather AQI", f"{air_quality.aqi} · {air_quality.label}")
    st.info(
        "This is OpenWeather's 1–5 AQI scale (Good to Very Poor), not the US EPA AQI."
    )
    labels = {
        "pm2_5": "PM2.5",
        "pm10": "PM10",
        "co": "CO",
        "no2": "NO₂",
        "o3": "O₃",
        "so2": "SO₂",
        "no": "NO (optional)",
        "nh3": "NH₃ (optional)",
    }
    columns = st.columns(4)
    for index, (key, label) in enumerate(labels.items()):
        columns[index % 4].metric(
            label, display_value(air_quality.components.get(key), " µg/m³")
        )


def render_forecast(forecast: ForecastData | None) -> None:
    """Render interactive temperature, humidity, and wind forecast charts."""
    st.subheader("5-day / 3-hour forecast")
    if forecast is None:
        return
    rows = [
        {
            "Local time": point.local_time,
            "Temperature (°C)": point.temperature,
            "Humidity (%)": point.humidity,
            "Wind speed (m/s)": point.wind_speed,
        }
        for point in forecast.points
    ]
    frame = pd.DataFrame(rows)
    offset_hours = forecast.timezone_offset_seconds / 3600
    st.caption(f"Time axis uses the location offset supplied by OpenWeather (UTC{offset_hours:+g}).")
    tabs = st.tabs(["Temperature", "Humidity", "Wind speed"])
    chart_specs = [
        ("Temperature (°C)", "#ef6c57"),
        ("Humidity (%)", "#1f77b4"),
        ("Wind speed (m/s)", "#28a071"),
    ]
    for tab, (column, color) in zip(tabs, chart_specs):
        with tab:
            figure = px.line(
                frame,
                x="Local time",
                y=column,
                markers=True,
                color_discrete_sequence=[color],
            )
            figure.update_layout(
                hovermode="x unified", margin=dict(l=10, r=10, t=20, b=10)
            )
            st.plotly_chart(figure, width="stretch")


def render_errors(errors: dict[str, str]) -> None:
    """Render feature-specific safe error messages."""
    labels = {
        "location": "Location",
        "weather": "Current weather",
        "air_quality": "Air quality",
        "forecast": "Forecast",
    }
    for key, message in errors.items():
        st.error(f"{labels.get(key, key)}: {message}")


__all__ = [
    "configure_page",
    "render_air_quality",
    "render_coordinate_help",
    "render_current_weather",
    "render_custom_widget",
    "render_errors",
    "render_forecast",
    "render_location",
]
