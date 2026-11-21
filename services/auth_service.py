"""Account registration and authentication with Argon2 password hashes."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from data.database import DatabasePath, connect_database

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
PASSWORD_HASHER = PasswordHasher(
    time_cost=2,
    memory_cost=19_456,
    parallelism=1,
    hash_len=32,
    salt_len=16,
)


class AccountValidationError(ValueError):
    """Raised when registration input does not meet account rules."""


class UsernameTakenError(AccountValidationError):
    """Raised when a case-insensitive username already exists."""


class AuthenticationError(ValueError):
    """Raised with a generic message when credentials are invalid."""


@dataclass(frozen=True)
class User:
    """Public account fields safe to store in Streamlit session state."""

    id: int
    username: str


def normalize_username(username: str) -> str:
    """Trim and validate a username without silently changing its case."""
    normalized = str(username).strip()
    if not 3 <= len(normalized) <= 32:
        raise AccountValidationError("Username must contain 3 to 32 characters.")
    if not USERNAME_PATTERN.fullmatch(normalized):
        raise AccountValidationError(
            "Username may contain letters, numbers, dots, hyphens, and underscores."
        )
    return normalized


def validate_password(password: str) -> None:
    """Enforce a small but clear password-strength baseline."""
    if not 8 <= len(password) <= 128:
        raise AccountValidationError("Password must contain 8 to 128 characters.")
    if not any(character.isalpha() for character in password):
        raise AccountValidationError("Password must include at least one letter.")
    if not any(character.isdigit() for character in password):
        raise AccountValidationError("Password must include at least one number.")


def register_user(
    username: str,
    password: str,
    password_confirmation: str,
    database_path: DatabasePath,
) -> User:
    """Create an account and store only its Argon2 password hash."""
    normalized = normalize_username(username)
    if password != password_confirmation:
        raise AccountValidationError("Password confirmation does not match.")
    validate_password(password)
    password_hash = PASSWORD_HASHER.hash(password)

    try:
        with connect_database(database_path) as connection:
            cursor = connection.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (normalized, password_hash),
            )
            user_id = int(cursor.lastrowid)
    except sqlite3.IntegrityError as exc:
        raise UsernameTakenError("That username is already registered.") from exc
    return User(id=user_id, username=normalized)


def authenticate_user(
    username: str, password: str, database_path: DatabasePath
) -> User:
    """Verify credentials and return the account without exposing lookup details."""
    generic_error = AuthenticationError("Invalid username or password.")
    normalized = str(username).strip()
    with connect_database(database_path) as connection:
        row = connection.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (normalized,),
        ).fetchone()
        if row is None:
            raise generic_error

        try:
            PASSWORD_HASHER.verify(row["password_hash"], password)
        except (VerificationError, InvalidHashError) as exc:
            raise generic_error from exc

        if PASSWORD_HASHER.check_needs_rehash(row["password_hash"]):
            connection.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (PASSWORD_HASHER.hash(password), row["id"]),
            )
        return User(id=int(row["id"]), username=str(row["username"]))


def get_user_by_id(user_id: int, database_path: DatabasePath) -> User | None:
    """Return an account by ID, or ``None`` if the session is stale."""
    with connect_database(database_path) as connection:
        row = connection.execute(
            "SELECT id, username FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if row is None:
        return None
    return User(id=int(row["id"]), username=str(row["username"]))


__all__ = [
    "AccountValidationError",
    "AuthenticationError",
    "User",
    "UsernameTakenError",
    "authenticate_user",
    "get_user_by_id",
    "normalize_username",
    "register_user",
    "validate_password",
]
