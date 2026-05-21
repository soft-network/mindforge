"""Shared auth helper for the main app and all pages/ sub-pages.

Lightweight password gate. For production use streamlit-authenticator.
"""

from __future__ import annotations

import os

import streamlit as st


def check_password() -> bool:
    """Return True if the user is authenticated (or no password is configured).

    Reads ADMIN_PASSWORD from st.secrets first, env var as fallback.
    Wenn weder noch gesetzt: dev-mode passes through without prompt.
    """
    expected = st.secrets.get("ADMIN_PASSWORD") or os.environ.get("ADMIN_PASSWORD")

    if not expected:
        return True

    if st.session_state.get("authenticated"):
        return True

    st.title("MindForge Coach Login")
    pwd = st.text_input("Passwort", type="password")
    if st.button("Einloggen"):
        if pwd == expected:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Falsches Passwort.")
    return False
