"""Mentor-Cockpit — Landing-Page für die Mentor-Rolle.

KPI-Strip + Warn-Boxen + NPS-Trend + Top-Mentees. Nur eigene Daten.
"""

from __future__ import annotations

import pathlib
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from integrations.airtable_helpers import (  # noqa: E402
    for_mentor, get_mentor_record, load_kunden, load_sessions,
)
from integrations.auth import current_user, require_tool_access  # noqa: E402
from lib.kpis import compute_mentor_self_kpis  # noqa: E402


user = require_tool_access("mentees", "read")
mentor_id   = user.get("mentor_id")
mentor_name = user.get("name", "Mentor")

if not mentor_id:
    st.error(
        "Dein Account hat keinen Mentor-Link. Bitte beim Admin melden, "
        "damit dein User mit einem Mentor-Record verknüpft wird."
    )
    st.stop()

# Stamm-Daten + Joins
mentor_rec = get_mentor_record(mentor_id)
kapazitaet = int(mentor_rec["fields"].get("Kapazität pro Woche", 0)) if mentor_rec else 0

all_mentees  = load_kunden()
all_sessions = load_sessions()
my_mentees   = for_mentor(all_mentees,  mentor_id, link_col="Mentor")
my_sessions  = for_mentor(all_sessions, mentor_id, link_col="Mentor")

kpis = compute_mentor_self_kpis(my_mentees, my_sessions, kapazitaet)


# ----- Header -----------------------------------------------------------------

st.title(f"🎯 Cockpit")
st.caption(f"👋 Hallo {mentor_name}")


# ----- KPI-Strip (5 Karten) ---------------------------------------------------

cols = st.columns(5)
cols[0].metric(
    "Aktive Mentees",
    f"{kpis['aktive_mentees']} / {kpis['kapazitaet_pro_woche']}",
    f"{kpis['auslastung_pct']:.0f} % Auslastung",
)
cols[1].metric("⌀ NPS", f"{kpis['avg_nps']:.1f}")
cols[2].metric("Sessions diese Woche", kpis["sessions_diese_woche"])
cols[3].metric("Sessions 30 Tage", kpis["sessions_30_tage"])
cols[4].metric(
    "Churn-Risk",
    kpis["churn_risk_mentees"],
    help="Mentees mit Health Score < 50",
)


# ----- Warnungen / Backlog ----------------------------------------------------

st.markdown("---")

if kpis["onboarding_offen"] > 0:
    st.warning(
        f"⚠️  **{kpis['onboarding_offen']} Mentee(s) noch nicht Activated** — "
        f"siehe Aufgaben/Meine Mentees"
    )

if kpis["churn_risk_mentees"] > 0:
    risk_mentees = my_mentees[my_mentees["Health Score"] < 50]
    names = ", ".join(risk_mentees["Lead"].head(5).tolist())
    st.error(
        f"🔴 **{kpis['churn_risk_mentees']} Churn-Risk-Mentee(s)** — {names} — "
        f"Health < 50 (lange keine Session?). Bitte Kontakt aufnehmen."
    )

if kpis["onboarding_offen"] == 0 and kpis["churn_risk_mentees"] == 0:
    st.success("🟢 Alles im grünen Bereich.")


# ----- Charts: NPS-Trend + Top-Mentees ----------------------------------------

st.markdown("---")
chart_col, top_col = st.columns([2, 1])

with chart_col:
    st.subheader("NPS-Trend (eigene Sessions)")
    if my_sessions.empty:
        st.caption("Noch keine Sessions eingetragen.")
    else:
        chart_df = my_sessions.dropna(subset=["NPS"]).sort_values("Date")
        if chart_df.empty:
            st.caption("Sessions vorhanden, aber noch keine NPS-Werte.")
        else:
            fig = px.line(
                chart_df, x="Date", y="NPS",
                markers=True, range_y=[0, 10],
            )
            fig.update_layout(
                height=320,
                margin=dict(l=20, r=20, t=20, b=20),
                yaxis_title="NPS",
                xaxis_title="",
            )
            st.plotly_chart(fig, use_container_width=True)

with top_col:
    st.subheader("Top-Mentees")
    if my_mentees.empty:
        st.caption("Noch keine Mentees zugewiesen.")
    else:
        top = my_mentees.sort_values("Health Score", ascending=False).head(3)
        for _, m in top.iterrows():
            st.markdown(
                f"{m.get('Health Emoji', '●')} **{m['Lead']}**  \n"
                f"<small>Health {int(m.get('Health Score') or 0)} · "
                f"MRR € {int(m.get('MRR (EUR)') or 0)}</small>",
                unsafe_allow_html=True,
            )
