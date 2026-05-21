"""Programme — Read-only Liste der Coaching-Programme."""

from __future__ import annotations

import pathlib
import sys

import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from integrations.airtable_helpers import load_programs  # noqa: E402


# Page-Config + Passwort-Gate werden in app.py zentral gesetzt.

st.title("📦 Programme")
st.caption("Coaching-Angebote · Lead Count · Converted Kunden")

df_programs = load_programs()

if df_programs.empty:
    st.info("Keine Programme vorhanden.")
else:
    st.dataframe(df_programs, use_container_width=True, hide_index=True)
