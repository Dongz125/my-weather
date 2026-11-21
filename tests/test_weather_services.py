"""Mocked tests for API response parsing and HTTP failure handling."""

from __future__ import annotations

from datetime import timedelta

import pytest
import requests

from services import api_client
from services.air_quality_service import parse_air_quality
from services.api_client import WeatherAPIError, request_json
from services.forecast_service import parse_forecast
from services.geocoding_service import parse_reverse_geocoding, reverse_geocode
from services.weather_service import get_current_weather, parse_current_weather


class FakeResponse:
    def __init__(self, status_code: int = 200, payload=None, json_error: bool = False):
        self.status_code = status_code
        self.payload = payload
        self.json_error = json_error

    def json(self):
        if self.json_error:
            raise ValueError("invalid JSON")
        return self.payload


def test_empty_geocoding_response_returns_none() -> None:
    assert parse_reverse_geocoding([]) is None


def test_reverse_geocoding_parses_optional_state() -> None:
    location = parse_reverse_geocoding(
        [{"name": "Ho Chi Minh City", "country": "VN", "state": "HCMC"}]
    )
    assert location is not None
    assert location.label == "Ho Chi Minh City, HCMC, VN"


def test_reverse_geocode_sends_limit_one(monkeypatch) -> None:
    captured = {}

    def fake_get(url, params, timeout):
        captured.update({"url": url, "params": params, "timeout": timeout})
        return FakeResponse(200, [{"name": "Hanoi", "country": "VN"}])

    monkeypatch.setattr(api_client.requests, "get", fake_get)
    result = reverse_geocode(21.0285, 105.8542, "test-key")
    assert result is not None and result.country == "VN"
    assert captured["params"]["limit"] == 1
    assert captured["params"]["appid"] == "test-key"


def test_successful_current_weather_parsing() -> None:
    weather = parse_current_weather(
        {
            "main": {"temp": 31.2, "feels_like": 35.0, "humidity": 70},
            "wind": {"speed": 3.4},
            "weather": [{"description": "mây rải rác", "icon": "03d"}],
            "dt": 1710000000,
        }
    )
    assert weather.temperature == 31.2
    assert weather.feels_like == 35.0
    assert weather.humidity == 70.0
    assert weather.wind_speed == 3.4
    assert weather.description == "mây rải rác"
    assert weather.icon == "03d"


def test_current_weather_missing_optional_data_is_safe() -> None:
    weather = parse_current_weather({"main": {"temp": 20}, "weather": []})
    assert weather.temperature == 20.0
    assert weather.feels_like is None
    assert weather.humidity is None
    assert weather.wind_speed is None
    assert weather.icon is None


def test_current_weather_request_parameters(monkeypatch) -> None:
    captured = {}

    def fake_get(url, params, timeout):
        captured.update(params)
        return FakeResponse(200, {"main": {}, "weather": []})

    monkeypatch.setattr(api_client.requests, "get", fake_get)
    get_current_weather(10.0, 20.0, "test-key")
    assert captured["units"] == "metric"
    assert captured["lang"] == "vi"


def test_air_quality_parsing_includes_optional_pollutants() -> None:
    air = parse_air_quality(
        {
            "list": [
                {
                    "dt": 1710000000,
                    "main": {"aqi": 2},
                    "components": {
                        "pm2_5": 12.3,
                        "pm10": 18.2,
                        "co": 220.1,
                        "no2": 8.0,
                        "o3": 45.0,
                        "so2": 3.0,
                        "no": 1.2,
                        "nh3": 0.8,
                    },
                }
            ]
        }
    )
    assert air.aqi == 2
    assert air.label == "Fair"
    assert air.components["pm2_5"] == 12.3
    assert air.components["nh3"] == 0.8


def test_empty_air_quality_data_raises() -> None:
    with pytest.raises(WeatherAPIError, match="No air-quality"):
        parse_air_quality({"list": []})


def test_forecast_uses_location_timezone() -> None:
    forecast = parse_forecast(
        {
            "city": {"timezone": 7 * 3600},
            "list": [
                {
                    "dt": 0,
                    "main": {"temp": 25, "humidity": 80},
                    "wind": {"speed": 2.5},
                }
            ],
        }
    )
    assert forecast.points[0].local_time.utcoffset() == timedelta(hours=7)
    assert forecast.points[0].local_time.hour == 7


@pytest.mark.parametrize(
    ("status", "message"),
    [(401, "API key"), (404, "did not find"), (429, "rate limit"), (503, "unavailable")],
)
def test_http_failures_have_safe_messages(monkeypatch, status, message) -> None:
    monkeypatch.setattr(
        api_client.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(status, {"message": "secret server detail"}),
    )
    with pytest.raises(WeatherAPIError, match=message) as caught:
        request_json("https://example.invalid", {"appid": "super-secret"})
    assert "super-secret" not in str(caught.value)
    assert "secret server detail" not in str(caught.value)


def test_timeout_is_converted_to_user_safe_error(monkeypatch) -> None:
    def timeout(*args, **kwargs):
        raise requests.Timeout("request URL contains appid=secret")

    monkeypatch.setattr(api_client.requests, "get", timeout)
    with pytest.raises(WeatherAPIError, match="timed out") as caught:
        request_json("https://example.invalid", {"appid": "secret"})
    assert "secret" not in str(caught.value)


def test_invalid_json_is_reported(monkeypatch) -> None:
    monkeypatch.setattr(
        api_client.requests, "get", lambda *args, **kwargs: FakeResponse(200, json_error=True)
    )
    with pytest.raises(WeatherAPIError, match="invalid JSON"):
        request_json("https://example.invalid", {})
