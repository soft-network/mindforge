"""Customer-Success-Analytics — KPIs · Onboarding · Health · MRR (read-only).

Reine Analyse-Sicht. Edit-Funktionen liegen separat in der CS-Verwaltungs-
Page (pages/6_Customer_Success.py).
"""

from __future__ import annotations

import pathlib
import sys

import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from components.cs_kpi_row import render_cs_kpi_row  # noqa: E402
from components.health_distribution import render_health_distribution  # noqa: E402
from components.mrr_chart import render_mrr_chart  # noqa: E402
from components.onboarding_funnel import render_onboarding_funnel  # noqa: E402
from integrations.airtable_helpers import load_kunden  # noqa: E402
from integrations.auth import require_tool_access  # noqa: E402
from lib.kpis import compute_cs_kpis  # noqa: E402


require_tool_access("mentees", "read")

df = load_kunden()
if df.empty:
    st.title(":material/insights: CS-Analytics")
    st.info("Keine Kunden vorhanden.")
    st.stop()

st.title(f":material/insights: CS-Analytics ({len(df)})")
st.caption("Onboarding · Health · MRR — read-only.")

render_cs_kpi_row(compute_cs_kpis(df))

st.markdown("---")

ccols = st.columns(2)
with ccols[0]:
    render_onboarding_funnel(df)
with ccols[1]:
    render_health_distribution(df)

render_mrr_chart(df)
