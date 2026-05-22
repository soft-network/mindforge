"""Aufgaben — Auto-generierte TODOs aus eigenen Mentees + Sessions.

Aktuell keine eigene Aufgaben-Tabelle in Airtable — die Aufgaben werden
deterministisch aus dem aktuellen Datenstand abgeleitet:

    1. Mentees mit Onboarding-Status != 'Activated'  → Onboarding voranbringen
    2. Mentees mit Health Score < 50                 → Kontakt aufnehmen
    3. Eigene Sessions ohne NPS-Wert                 → Feedback nachpflegen

Spätere Welle kann eine echte Tasks-Tabelle einführen.
"""

from __future__ import annotations

import pathlib
import sys

import pandas as pd
import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from components import render_empty_state  # noqa: E402
from integrations.airtable_helpers import (  # noqa: E402
    for_mentor, load_kunden, load_sessions,
)
from integrations.auth import require_tool_access  # noqa: E402


user = require_tool_access("aufgaben", "read")
mentor_id = user.get("mentor_id")
if not mentor_id:
    st.error("Account ohne Mentor-Link. Bitte beim Admin melden.")
    st.stop()


st.title("✅ Aufgaben")
st.caption("Auto-abgeleitet aus deinen Mentees und Sessions. Erledigt = Daten in Airtable korrigieren.")

my_mentees  = for_mentor(load_kunden(), mentor_id, link_col="Mentor")
my_sessions = for_mentor(load_sessions(), mentor_id, link_col="Mentor")

# Aufgaben generieren
tasks: list[dict] = []

# 1) Onboarding-Backlog
if not my_mentees.empty:
    onb_open = my_mentees[my_mentees["Onboarding Status"] != "Activated"]
    for _, m in onb_open.iterrows():
        tasks.append({
            "Priorität": "🟡 mittel",
            "Kategorie": "Onboarding",
            "Mentee":    m["Lead"],
            "Aktion":    f"Stage '{m['Onboarding Status']}' voranbringen",
            "Page":      "Meine Mentees",
        })

# 2) Churn-Risk
if not my_mentees.empty:
    churn = my_mentees[my_mentees["Health Score"] < 50]
    for _, m in churn.iterrows():
        tasks.append({
            "Priorität": "🔴 hoch",
            "Kategorie": "Retention",
            "Mentee":    m["Lead"],
            "Aktion":    f"Health {int(m['Health Score'])} ({m['Health Tier']}) — Kontakt aufnehmen",
            "Page":      "Meine Mentees",
        })

# 3) Sessions ohne NPS
if not my_sessions.empty:
    backlog = my_sessions[my_sessions["NPS"].isna()]
    for _, s in backlog.iterrows():
        dt = s.get("Date")
        date_str = dt.strftime("%d.%m") if pd.notna(dt) else "—"
        tasks.append({
            "Priorität": "🟢 niedrig",
            "Kategorie": "Nachpflege",
            "Mentee":    s["Lead"],
            "Aktion":    f"NPS-Wert für Session vom {date_str} eintragen",
            "Page":      "Meine Sessions",
        })


if not tasks:
    render_empty_state("🎉 Alle Aufgaben erledigt — kein Backlog.", icon="✅")
    st.stop()


# KPI-Strip
prio_counts = pd.Series([t["Priorität"] for t in tasks]).value_counts()
kcols = st.columns(4)
kcols[0].metric("Gesamt",     len(tasks))
kcols[1].metric("🔴 Hoch",    int(prio_counts.get("🔴 hoch", 0)))
kcols[2].metric("🟡 Mittel",  int(prio_counts.get("🟡 mittel", 0)))
kcols[3].metric("🟢 Niedrig", int(prio_counts.get("🟢 niedrig", 0)))

st.markdown("---")


# Filter
fcols = st.columns(3)
prio_filter = fcols[0].selectbox("Priorität", ["Alle", "🔴 hoch", "🟡 mittel", "🟢 niedrig"])
kat_filter  = fcols[1].selectbox("Kategorie", ["Alle"] + sorted({t["Kategorie"] for t in tasks}))
fcols[2].markdown(f"<div style='padding-top:1.8rem'>{len(tasks)} Aufgaben</div>",
                  unsafe_allow_html=True)

filtered = tasks
if prio_filter != "Alle":
    filtered = [t for t in filtered if t["Priorität"] == prio_filter]
if kat_filter != "Alle":
    filtered = [t for t in filtered if t["Kategorie"] == kat_filter]

# Sortierung: hoch → mittel → niedrig
prio_order = {"🔴 hoch": 0, "🟡 mittel": 1, "🟢 niedrig": 2}
filtered = sorted(filtered, key=lambda t: prio_order.get(t["Priorität"], 99))


# Liste
COLS = [1.2, 1.5, 2, 4, 1.5]
hcols = st.columns(COLS)
hcols[0].markdown("**Priorität**")
hcols[1].markdown("**Kategorie**")
hcols[2].markdown("**Mentee**")
hcols[3].markdown("**Aktion**")
hcols[4].markdown("**Wo**")
st.markdown("<hr style='margin-top:0; margin-bottom:0.5rem'>", unsafe_allow_html=True)

for t in filtered:
    cols = st.columns(COLS)
    cols[0].markdown(t["Priorität"])
    cols[1].caption(t["Kategorie"])
    cols[2].markdown(f"**{t['Mentee']}**")
    cols[3].markdown(t["Aktion"])
    cols[4].caption(f"→ {t['Page']}")
