"""Dashboard — KPI-Strip + Funnel + Source-Performance."""

from __future__ import annotations

import pathlib
import sys

import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from integrations.airtable_helpers import load_leads  # noqa: E402
from integrations.auth import require_tool_access  # noqa: E402
from lib.kpis import compute_funnel_kpis  # noqa: E402
from components.kpi_row import render_kpi_row  # noqa: E402
from components.funnel_chart import render_funnel  # noqa: E402
from components.source_chart import render_source_performance  # noqa: E402


# Permission-Gate (Login wird in app.py geprüft, hier nur Tool-Access)
require_tool_access("dashboard", "read")

st.title("📊 Dashboard")
st.caption("KPIs · Funnel · Source-Performance")

df = load_leads()

# KPI-Strip oben
render_kpi_row(compute_funnel_kpis(df))

st.markdown("---")

# Funnel + Source-Chart nebeneinander
c1, c2 = st.columns(2)
with c1:
    render_funnel(df)
with c2:
    render_source_performance(df)
