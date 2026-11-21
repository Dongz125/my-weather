"""Ownership-safe persistence for each user's saved weather locations."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from core.validation import validate_coordinates
from data.database import DatabasePath, connect_database

MAX_SAVED_LOCATIONS = 50


class SavedLocationError(ValueError):
    """Base exception for saved-location operations."""


class DuplicateLocationError(SavedLocationError):
    """Raised when a user saves the same normalized coordinates twice."""


class SavedLocationLimitError(SavedLocationError):
    """Raised when an account reaches its saved-location limit."""


@dataclass(frozen=True)
class SavedLocation:
    """A location associated with one authenticated account."""

    id: int
    user_id: int
    city: str
    state: str | None
    country: str
    latitude: float
    longitude: float

    @property
    def label(self) -> str:
        parts = [self.city]
        if self.state and self.state.casefold() != self.city.casefold():
            parts.append(self.state)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)


def save_location(
    user_id: int,
    city: str,
    state: str | None,
    country: str,
    latitude: float,
    longitude: float,
    database_path: DatabasePath,
) -> SavedLocation:
    """Save one normalized coordinate pair for an existing user."""
    lat, lon = validate_coordinates(latitude, longitude)
    lat, lon = round(lat, 6), round(lon, 6)
    normalized_city = str(city).strip() or "Unknown location"
    normalized_state = str(state).strip() if state else None
    normalized_country = str(country).strip().upper()

    try:
        with connect_database(database_path) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM saved_locations WHERE user_id = ?", (user_id,)
            ).fetchone()[0]
            if count >= MAX_SAVED_LOCATIONS:
                raise SavedLocationLimitError(
                    f"An account can save at most {MAX_SAVED_LOCATIONS} locations."
                )
            cursor = connection.execute(
                """
                INSERT INTO saved_locations
                    (user_id, city, state, country, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    normalized_city,
                    normalized_state,
                    normalized_country,
                    lat,
                    lon,
                ),
            )
            location_id = int(cursor.lastrowid)
    except sqlite3.IntegrityError as exc:
        message = str(exc).lower()
        if "unique" in message:
            raise DuplicateLocationError("This location is already saved.") from exc
        raise SavedLocationError("The location could not be saved.") from exc

    return SavedLocation(
        id=location_id,
        user_id=user_id,
        city=normalized_city,
        state=normalized_state,
        country=normalized_country,
        latitude=lat,
        longitude=lon,
    )


def list_saved_locations(
    user_id: int, database_path: DatabasePath
) -> list[SavedLocation]:
    """List only the locations owned by the supplied account."""
    with connect_database(database_path) as connection:
        rows = connection.execute(
            """
            SELECT id, user_id, city, state, country, latitude, longitude
            FROM saved_locations
            WHERE user_id = ?
            ORDER BY city COLLATE NOCASE, created_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [
        SavedLocation(
            id=int(row["id"]),
            user_id=int(row["user_id"]),
            city=str(row["city"]),
            state=str(row["state"]) if row["state"] else None,
            country=str(row["country"]),
            latitude=float(row["latitude"]),
            longitude=float(row["longitude"]),
        )
        for row in rows
    ]


def delete_saved_location(
    user_id: int, location_id: int, database_path: DatabasePath
) -> bool:
    """Delete by both location ID and owner ID to prevent cross-account access."""
    with connect_database(database_path) as connection:
        cursor = connection.execute(
            "DELETE FROM saved_locations WHERE id = ? AND user_id = ?",
            (location_id, user_id),
        )
    return cursor.rowcount == 1


__all__ = [
    "DuplicateLocationError",
    "MAX_SAVED_LOCATIONS",
    "SavedLocation",
    "SavedLocationError",
    "SavedLocationLimitError",
    "delete_saved_location",
    "list_saved_locations",
    "save_location",
]
