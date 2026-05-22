"""Programme — Read-only Liste der Coaching-Programme."""

from __future__ import annotations

import pathlib
import sys

import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from integrations.airtable_helpers import load_programs  # noqa: E402
from integrations.auth import require_tool_access  # noqa: E402


# Permission-Gate
require_tool_access("programme", "read")

st.title("📦 Programme")
st.caption("Coaching-Angebote · Lead Count · Converted Kunden")

df_programs = load_programs()

if df_programs.empty:
    st.info("Keine Programme vorhanden.")
else:
    st.dataframe(df_programs, use_container_width=True, hide_index=True)
