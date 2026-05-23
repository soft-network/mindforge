"""Mentor-Analytics — KPIs · Auslastung · Spezialisierung (read-only).

Reine Analyse-Sicht. Edit-Funktionen liegen separat in der
Mentoren-Verwaltungs-Page (pages/5_Mentoren.py).
"""

from __future__ import annotations

import pathlib
import sys

import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from components.mentor_capacity_chart import render_mentor_capacity  # noqa: E402
from components.mentor_kpi_row import render_mentor_kpi_row  # noqa: E402
from components.specialization_chart import render_specialization  # noqa: E402
from integrations.airtable_helpers import load_mentoren  # noqa: E402
from integrations.auth import require_tool_access  # noqa: E402
from lib.kpis import compute_mentor_kpis  # noqa: E402


require_tool_access("mentoren", "read")

df = load_mentoren()
if df.empty:
    st.title(":material/insights: Mentor-Analytics")
    st.info("Keine Mentoren vorhanden.")
    st.stop()

st.title(f":material/insights: Mentor-Analytics ({len(df)})")
st.caption("Auslastung · NPS · Spezialisierungs-Verteilung — read-only.")

render_mentor_kpi_row(compute_mentor_kpis(df))

st.markdown("---")

ccols = st.columns(2)
with ccols[0]:
    render_mentor_capacity(df)
with ccols[1]:
    render_specialization(df)
