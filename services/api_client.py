"""Small, reusable HTTP client for OpenWeather JSON endpoints."""

from __future__ import annotations

from typing import Any, Mapping

import requests

DEFAULT_TIMEOUT = 10


class WeatherAPIError(RuntimeError):
    """A safe, user-facing API error that never includes request secrets."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def request_json(
    url: str,
    params: Mapping[str, Any],
    *,
    timeout: int = DEFAULT_TIMEOUT,
) -> Any:
    """Request JSON from OpenWeather with bounded time and safe errors."""
    try:
        response = requests.get(url, params=dict(params), timeout=timeout)
    except requests.Timeout as exc:
        raise WeatherAPIError("OpenWeather timed out. Please try again shortly.") from exc
    except requests.ConnectionError as exc:
        raise WeatherAPIError(
            "Could not connect to OpenWeather. Check your internet connection."
        ) from exc
    except requests.RequestException as exc:
        raise WeatherAPIError("The OpenWeather request could not be completed.") from exc

    status = response.status_code
    if status == 401:
        raise WeatherAPIError(
            "OpenWeather rejected the API key. Check the key or wait for activation.",
            status,
        )
    if status == 404:
        raise WeatherAPIError("OpenWeather did not find data for this request.", status)
    if status == 429:
        raise WeatherAPIError(
            "OpenWeather rate limit reached. Please wait before trying again.", status
        )
    if 500 <= status <= 599:
        raise WeatherAPIError(
            "OpenWeather is temporarily unavailable. Please try again later.", status
        )
    if not 200 <= status <= 299:
        raise WeatherAPIError(
            f"OpenWeather returned an unexpected HTTP {status} response.", status
        )

    try:
        return response.json()
    except (ValueError, requests.JSONDecodeError) as exc:
        raise WeatherAPIError("OpenWeather returned an invalid JSON response.") from exc
