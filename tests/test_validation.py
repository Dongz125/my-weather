"""Tests for coordinate validation and AQI labels."""

import math

import pytest

from core.validation import CoordinateValidationError, validate_coordinates
from services.air_quality_service import aqi_label


def test_valid_coordinate_strings_are_converted() -> None:
    assert validate_coordinates("10.8231", "106.6297") == (10.8231, 106.6297)


@pytest.mark.parametrize(
    ("latitude", "longitude", "message"),
    [
        ("north", "106", "numeric"),
        ("", "106", "numeric"),
        (91, 0, "Latitude"),
        (-91, 0, "Latitude"),
        (0, 181, "Longitude"),
        (0, -181, "Longitude"),
        (math.nan, 0, "finite"),
        (True, 0, "numeric"),
    ],
)
def test_invalid_coordinates_are_rejected(latitude, longitude, message) -> None:
    with pytest.raises(CoordinateValidationError, match=message):
        validate_coordinates(latitude, longitude)


@pytest.mark.parametrize(
    ("score", "label"),
    [(1, "Good"), (2, "Fair"), (3, "Moderate"), (4, "Poor"), (5, "Very Poor")],
)
def test_openweather_aqi_labels(score: int, label: str) -> None:
    assert aqi_label(score) == label


def test_unknown_aqi_label_is_safe() -> None:
    assert aqi_label(99) == "Unknown"
