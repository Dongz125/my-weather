"""Streamlit controls for saving, loading, and deleting account locations."""

from __future__ import annotations

import streamlit as st

from data.database import DatabasePath
from services.auth_service import User
from services.geocoding_service import LocationInfo
from services.saved_location_service import (
    SavedLocation,
    SavedLocationError,
    delete_saved_location,
    list_saved_locations,
    save_location,
)
from views.account import SESSION_NOTICE


def render_saved_locations_sidebar(
    user: User, database_path: DatabasePath
) -> SavedLocation | None:
    """Render the current user's locations and return one selected for lookup."""
    locations = list_saved_locations(user.id, database_path)
    selected: SavedLocation | None = None
    with st.sidebar:
        st.subheader("Saved locations")
        if not locations:
            st.caption("No saved locations yet.")
        for location in locations:
            st.markdown(f"**{location.label}**")
            load_column, delete_column = st.columns(2)
            if load_column.button(
                "Load", key=f"load_location_{location.id}", width="stretch"
            ):
                selected = location
            if delete_column.button(
                "Delete", key=f"delete_location_{location.id}", width="stretch"
            ):
                delete_saved_location(user.id, location.id, database_path)
                st.session_state[SESSION_NOTICE] = f"Removed {location.label}."
                st.rerun()
    return selected


def render_save_location(
    user: User | None, data: dict[str, object], database_path: DatabasePath
) -> None:
    """Offer to save a successfully resolved location for the signed-in user."""
    location = data.get("location")
    if user is None:
        st.caption("Sign in to save this location to your account.")
        return
    if not isinstance(location, LocationInfo):
        return

    if st.button(
        f"Save {location.name}",
        key=f"save_location_{data['latitude']}_{data['longitude']}",
        icon=":material/bookmark_add:",
    ):
        try:
            save_location(
                user.id,
                location.name,
                location.state,
                location.country,
                float(data["latitude"]),
                float(data["longitude"]),
                database_path,
            )
        except SavedLocationError as exc:
            st.warning(str(exc))
        else:
            st.session_state[SESSION_NOTICE] = f"Saved {location.label}."
            st.rerun()


__all__ = ["render_save_location", "render_saved_locations_sidebar"]
