"""Engagements — Vertragssicht pro eigenem Mentee (read-only).

Ein Engagement = die Beziehung Mentee × Programm × Mentor × MRR × Start-Datum.
Aktuell aus Kunden-Tabelle abgeleitet — wenn später eine eigene Engagements-
Tabelle kommt, ist das hier der Plug-Point.
"""

from __future__ import annotations

import pathlib
import sys

import pandas as pd
import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from components import render_empty_state  # noqa: E402
from integrations.airtable_helpers import for_mentor, load_kunden  # noqa: E402
from integrations.auth import require_tool_access  # noqa: E402


user = require_tool_access("engagements", "read")
mentor_id = user.get("mentor_id")
if not mentor_id:
    st.error("Account ohne Mentor-Link. Bitte beim Admin melden.")
    st.stop()


st.title("🤝 Engagements")
st.caption("Deine Mentee-Verträge — read-only. Änderungen über Admin/Customer-Success.")

my_engagements = for_mentor(load_kunden(), mentor_id, link_col="Mentor").reset_index(drop=True)

if my_engagements.empty:
    render_empty_state("Aktuell keine aktiven Engagements.", icon="🤝")
    st.stop()


# Mini-KPIs
kcols = st.columns(3)
kcols[0].metric("Aktive Engagements", len(my_engagements))
total_mrr = float(my_engagements["MRR (EUR)"].sum())
kcols[1].metric("MRR gesamt (deine)", f"€ {total_mrr:,.0f}")
total_ltv = float(my_engagements["LTV"].sum())
kcols[2].metric("LTV gesamt", f"€ {total_ltv:,.0f}")

st.markdown("---")

# Card-Layout statt Tabelle — Engagements sind "fett" pro Mentee
for _, eng in my_engagements.iterrows():
    with st.container(border=True):
        cols = st.columns([3, 2, 1.5, 1.5])
        cols[0].markdown(
            f"**{eng.get('Health Emoji', '●')} {eng['Lead']}**"
        )
        cols[0].caption(f"Status: {eng.get('Status', '—')}  ·  Onboarding: {eng['Onboarding Status']}")

        cols[1].markdown(f"📦 **{eng.get('Program') or '—'}**")
        start = eng.get("Start Date")
        if pd.notna(start):
            cols[1].caption(f"seit {start.strftime('%d.%m.%Y')}")

        cols[2].metric("MRR", f"€ {int(eng.get('MRR (EUR)') or 0)}", label_visibility="visible")
        cols[3].metric("Health", f"{int(eng.get('Health Score') or 0)}",
                       eng.get("Health Tier", ""))
