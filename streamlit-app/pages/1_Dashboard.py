"""Admin Dashboard — Cross-Source Executive View.

Drei Sektionen für die drei Operations-Domänen:
    1. SALES — Lead-Funnel + Source-Performance
    2. OPERATIONS — Mentor-Auslastung + Onboarding-Funnel
    3. BUSINESS — MRR pro Programm + Cross-KPIs
"""

from __future__ import annotations

import pathlib
import sys

import pandas as pd
import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from components.funnel_chart import render_funnel  # noqa: E402
from components.health_distribution import render_health_distribution  # noqa: E402
from components.mentor_capacity_chart import render_mentor_capacity  # noqa: E402
from components.mrr_chart import render_mrr_chart  # noqa: E402
from components.onboarding_funnel import render_onboarding_funnel  # noqa: E402
from components.source_chart import render_source_performance  # noqa: E402
from integrations.airtable_helpers import (  # noqa: E402
    load_kunden, load_leads, load_mentoren,
)
from integrations.auth import require_tool_access  # noqa: E402
from lib.kpis import (  # noqa: E402
    compute_cs_kpis,
    compute_funnel_kpis,
    compute_mentor_kpis,
)


# Permission-Gate (Login wird in app.py geprüft, hier nur Tool-Access)
require_tool_access("dashboard", "read")


st.title(":material/space_dashboard: Executive Dashboard")
st.caption("Cross-Source-KPIs · Sales · Operations · Business")

df_leads    = load_leads()
df_kunden   = load_kunden()
df_mentoren = load_mentoren()


# -----------------------------------------------------------------------------
# Hero-KPI-Strip: 5 wichtigste Cross-Source-Zahlen auf einen Blick
# -----------------------------------------------------------------------------

lead_kpis   = compute_funnel_kpis(df_leads)
mentor_kpis = compute_mentor_kpis(df_mentoren)
cs_kpis     = compute_cs_kpis(df_kunden)

hcols = st.columns(5)
hcols[0].metric(
    "Neue Leads heute",
    lead_kpis["leads_today"],
    f"{lead_kpis['leads_week']} diese Woche",
)
hcols[1].metric(
    "Hot Leads (Woche)",
    lead_kpis["hot_leads_week"],
    f"Conv {lead_kpis['conv_rate_pct']:.0f} %",
)
hcols[2].metric(
    "Aktive Mentees",
    cs_kpis["total_kunden"],
    f"{cs_kpis['churn_risk']} Churn-Risk",
    delta_color="inverse",
)
hcols[3].metric(
    "MRR (€/Monat)",
    f"{cs_kpis['total_mrr']:,.0f}",
)
hcols[4].metric(
    "Mentoren aktiv",
    mentor_kpis["aktiv"],
    f"⌀ NPS {mentor_kpis['avg_nps']}",
)


# -----------------------------------------------------------------------------
# Sektion 1: SALES
# -----------------------------------------------------------------------------

st.markdown("---")
st.subheader(":material/phone_in_talk: Sales")

s_cols = st.columns(2)
with s_cols[0]:
    render_funnel(df_leads)
with s_cols[1]:
    render_source_performance(df_leads)


# -----------------------------------------------------------------------------
# Sektion 2: OPERATIONS (Mentor + CS-Onboarding)
# -----------------------------------------------------------------------------

st.markdown("---")
st.subheader(":material/settings: Operations")

o_cols = st.columns(2)
with o_cols[0]:
    render_mentor_capacity(df_mentoren, title="Mentor-Auslastung (%)")
with o_cols[1]:
    render_onboarding_funnel(df_kunden, title="Kunden-Onboarding")


# -----------------------------------------------------------------------------
# Sektion 3: BUSINESS (MRR + Health-Verteilung)
# -----------------------------------------------------------------------------

st.markdown("---")
st.subheader(":material/payments: Business")

b_cols = st.columns(2)
with b_cols[0]:
    render_mrr_chart(df_kunden, title="MRR pro Programm")
with b_cols[1]:
    render_health_distribution(df_kunden, title="Kunden-Health-Verteilung")
