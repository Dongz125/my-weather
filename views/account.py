"""Streamlit account registration, sign-in, and logout controls."""

from __future__ import annotations

import streamlit as st

from data.database import DatabasePath
from services.auth_service import (
    AccountValidationError,
    AuthenticationError,
    User,
    authenticate_user,
    get_user_by_id,
    register_user,
)

SESSION_USER_ID = "authenticated_user_id"
SESSION_NOTICE = "account_notice"


def render_account_sidebar(database_path: DatabasePath) -> User | None:
    """Render account controls and return the authenticated user, if any."""
    with st.sidebar:
        st.header("Account")
        notice = st.session_state.pop(SESSION_NOTICE, None)
        if notice:
            st.success(notice)

        user = _session_user(database_path)
        if user is not None:
            st.write(f"Signed in as **{user.username}**")
            if st.button("Sign out", width="stretch"):
                st.session_state.pop(SESSION_USER_ID, None)
                st.rerun()
            return user

        sign_in_tab, register_tab = st.tabs(["Sign in", "Register"])
        with sign_in_tab:
            with st.form("sign_in_form"):
                username = st.text_input("Username", key="sign_in_username")
                password = st.text_input(
                    "Password", type="password", key="sign_in_password"
                )
                submitted = st.form_submit_button("Sign in", type="primary")
            if submitted:
                try:
                    user = authenticate_user(username, password, database_path)
                except AuthenticationError as exc:
                    st.error(str(exc))
                else:
                    st.session_state[SESSION_USER_ID] = user.id
                    st.session_state[SESSION_NOTICE] = "Signed in successfully."
                    st.rerun()

        with register_tab:
            with st.form("register_form"):
                username = st.text_input("Username", key="register_username")
                password = st.text_input(
                    "Password", type="password", key="register_password"
                )
                confirmation = st.text_input(
                    "Confirm password", type="password", key="register_confirmation"
                )
                submitted = st.form_submit_button("Create account", type="primary")
            if submitted:
                try:
                    user = register_user(
                        username, password, confirmation, database_path
                    )
                except AccountValidationError as exc:
                    st.error(str(exc))
                else:
                    st.session_state[SESSION_USER_ID] = user.id
                    st.session_state[SESSION_NOTICE] = "Account created successfully."
                    st.rerun()

        st.caption("Sign in to save locations. Weather lookup remains available to guests.")
        return None


def _session_user(database_path: DatabasePath) -> User | None:
    user_id = st.session_state.get(SESSION_USER_ID)
    if not isinstance(user_id, int):
        return None
    user = get_user_by_id(user_id, database_path)
    if user is None:
        st.session_state.pop(SESSION_USER_ID, None)
    return user


__all__ = ["SESSION_NOTICE", "SESSION_USER_ID", "render_account_sidebar"]
