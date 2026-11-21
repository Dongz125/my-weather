"""Tests for SQLite accounts and ownership-safe saved locations."""

from __future__ import annotations

import sqlite3

import pytest

from data.database import connect_database, initialize_database
from services.auth_service import (
    AccountValidationError,
    AuthenticationError,
    UsernameTakenError,
    authenticate_user,
    register_user,
)
from services.saved_location_service import (
    DuplicateLocationError,
    SavedLocationError,
    delete_saved_location,
    list_saved_locations,
    save_location,
)


@pytest.fixture
def database_path(tmp_path):
    path = tmp_path / "test_myweather.db"
    initialize_database(path)
    return path


def test_registration_stores_argon2_hash_not_plaintext(database_path) -> None:
    user = register_user("weather_user", "Forecast123", "Forecast123", database_path)

    with connect_database(database_path) as connection:
        row = connection.execute(
            "SELECT password_hash FROM users WHERE id = ?", (user.id,)
        ).fetchone()

    assert row is not None
    assert row["password_hash"] != "Forecast123"
    assert row["password_hash"].startswith("$argon2id$")


def test_authentication_is_case_insensitive_for_username(database_path) -> None:
    registered = register_user("WeatherUser", "Forecast123", "Forecast123", database_path)
    authenticated = authenticate_user("weatheruser", "Forecast123", database_path)
    assert authenticated == registered


def test_duplicate_username_is_case_insensitive(database_path) -> None:
    register_user("WeatherUser", "Forecast123", "Forecast123", database_path)
    with pytest.raises(UsernameTakenError):
        register_user("weatheruser", "Different456", "Different456", database_path)


@pytest.mark.parametrize(
    ("username", "password", "confirmation", "message"),
    [
        ("ab", "Forecast123", "Forecast123", "3 to 32"),
        ("bad user", "Forecast123", "Forecast123", "may contain"),
        ("valid_user", "short1", "short1", "8 to 128"),
        ("valid_user", "onlyletters", "onlyletters", "number"),
        ("valid_user", "12345678", "12345678", "letter"),
        ("valid_user", "Forecast123", "Mismatch123", "does not match"),
    ],
)
def test_registration_validation(
    database_path, username, password, confirmation, message
) -> None:
    with pytest.raises(AccountValidationError, match=message):
        register_user(username, password, confirmation, database_path)


@pytest.mark.parametrize(
    ("username", "password"),
    [("weather_user", "WrongPassword1"), ("missing_user", "Forecast123")],
)
def test_invalid_credentials_use_same_generic_error(
    database_path, username, password
) -> None:
    register_user("weather_user", "Forecast123", "Forecast123", database_path)
    with pytest.raises(AuthenticationError, match="Invalid username or password"):
        authenticate_user(username, password, database_path)


def test_user_can_save_and_list_a_location(database_path) -> None:
    user = register_user("weather_user", "Forecast123", "Forecast123", database_path)
    saved = save_location(
        user.id,
        "Ho Chi Minh City",
        "Ho Chi Minh City",
        "vn",
        10.8231001,
        106.6297001,
        database_path,
    )

    assert saved.country == "VN"
    assert saved.latitude == 10.8231
    assert list_saved_locations(user.id, database_path) == [saved]


def test_duplicate_normalized_coordinates_are_rejected(database_path) -> None:
    user = register_user("weather_user", "Forecast123", "Forecast123", database_path)
    save_location(user.id, "Hanoi", None, "VN", 21.028511, 105.804817, database_path)

    with pytest.raises(DuplicateLocationError):
        save_location(
            user.id, "Hanoi", None, "VN", 21.0285114, 105.8048174, database_path
        )


def test_location_queries_are_isolated_by_owner(database_path) -> None:
    first = register_user("first_user", "Forecast123", "Forecast123", database_path)
    second = register_user("second_user", "Forecast123", "Forecast123", database_path)
    saved = save_location(first.id, "Hanoi", None, "VN", 21.0285, 105.8542, database_path)

    assert list_saved_locations(second.id, database_path) == []
    assert delete_saved_location(second.id, saved.id, database_path) is False
    assert list_saved_locations(first.id, database_path) == [saved]


def test_owner_can_delete_saved_location(database_path) -> None:
    user = register_user("weather_user", "Forecast123", "Forecast123", database_path)
    saved = save_location(user.id, "Hanoi", None, "VN", 21.0285, 105.8542, database_path)
    assert delete_saved_location(user.id, saved.id, database_path) is True
    assert list_saved_locations(user.id, database_path) == []


def test_foreign_key_rejects_unknown_user(database_path) -> None:
    with pytest.raises(SavedLocationError):
        save_location(999, "Hanoi", None, "VN", 21.0285, 105.8542, database_path)


def test_deleting_user_cascades_saved_locations(database_path) -> None:
    user = register_user("weather_user", "Forecast123", "Forecast123", database_path)
    save_location(user.id, "Hanoi", None, "VN", 21.0285, 105.8542, database_path)

    with connect_database(database_path) as connection:
        connection.execute("DELETE FROM users WHERE id = ?", (user.id,))

    assert list_saved_locations(user.id, database_path) == []


def test_schema_can_be_initialized_repeatedly(database_path) -> None:
    initialize_database(database_path)
    initialize_database(database_path)
    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert {"users", "saved_locations"}.issubset(tables)
