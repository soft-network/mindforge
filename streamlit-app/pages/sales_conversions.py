"""Meine Conversions — read-only Erfolgsliste für die Sales-Rolle.

Aus df_kunden gefiltert: Kunden, deren Lead-Name in den eigenen Leads vorkommt.
Macht den Convert-Erfolg sichtbar (Motivation + Statistik).
"""

from __future__ import annotations

import pathlib
import sys

import pandas as pd
import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from components import render_empty_state  # noqa: E402
from integrations.airtable_helpers import load_kunden, load_leads  # noqa: E402
from integrations.auth import require_tool_access  # noqa: E402


user = require_tool_access("engagements", "read")
my_email = user.get("email", "")


st.title(":material/handshake: Meine Conversions")
st.caption("Mentees, die aus deinen Leads konvertiert wurden.")

df_leads  = load_leads()
df_kunden = load_kunden()

mine = df_leads[df_leads["Setter"].str.lower() == my_email.lower()] if not df_leads.empty else df_leads
my_lead_names = set(mine["Name"].dropna().tolist())

my_conversions = df_kunden[df_kunden["Lead"].isin(my_lead_names)].reset_index(drop=True) if not df_kunden.empty else df_kunden

if my_conversions.empty:
    render_empty_state(
        "Noch keine eigenen Conversions. Konvertier deinen ersten Lead in "
        "🎯 Strategiegespräche.",
        icon="🤝",
    )
    st.stop()


# Mini-KPI-Strip
kcols = st.columns(4)
kcols[0].metric("Conversions gesamt", len(my_conversions))
total_mrr = float(my_conversions["MRR (EUR)"].sum())
kcols[1].metric("MRR generiert",      f"€ {total_mrr:,.0f}")
total_ltv = float(my_conversions["LTV"].sum())
kcols[2].metric("LTV gesamt",         f"€ {total_ltv:,.0f}")
activated = int((my_conversions["Onboarding Status"] == "Activated").sum())
kcols[3].metric("Davon Activated",    activated)

st.markdown("---")


# Card-Layout
for _, c in my_conversions.iterrows():
    with st.container(border=True):
        cols = st.columns([3, 2, 1.5, 1.5, 1.5])
        cols[0].markdown(f"**{c.get('Health Emoji', '●')} {c['Lead']}**")
        cols[0].caption(f"Status: {c.get('Status', '—')}  ·  Onboarding: {c['Onboarding Status']}")

        cols[1].markdown(f"📦 **{c.get('Program') or '—'}**")
        cols[1].caption(f"Mentor: {c.get('Mentor Name', '—')}")

        start = c.get("Start Date")
        if pd.notna(start):
            cols[2].caption(f"seit {start.strftime('%d.%m.%Y')}")

        cols[3].metric("MRR", f"€ {int(c.get('MRR (EUR)') or 0)}")
        cols[4].metric("Health", f"{int(c.get('Health Score') or 0)}", c.get("Health Tier", ""))
