"""Sales-Cockpit — Landing-Page für die Sales-Rolle.

Pipeline-Snapshot + heutige To-Dos für Setter+Closer kombiniert.
Filter auf Setter==self_email (Self-Scope).
"""

from __future__ import annotations

import pathlib
import sys
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from components import render_empty_state  # noqa: E402
from integrations.airtable_helpers import load_kunden, load_leads  # noqa: E402
from integrations.auth import require_tool_access  # noqa: E402
from lib.tz import TZ_BERLIN  # noqa: E402


user = require_tool_access("hot_leads", "read")
my_email = user.get("email", "")


st.title(":material/space_dashboard: Sales-Cockpit")
st.caption(f"👋 Hallo {user.get('name', 'Sales')}")

df_leads  = load_leads()
df_kunden = load_kunden()

# Self-Scope: nur eigene Leads (Setter-Feld == eigene Email)
mine = df_leads[df_leads["Setter"].str.lower() == my_email.lower()] if not df_leads.empty else df_leads


# KPI-Strip
now = pd.Timestamp.now(tz="UTC")
today_start = now.normalize()
week_start  = today_start - pd.Timedelta(days=7)

# Heute gebucht
booked_today = mine[mine["Termin am"] >= today_start] if not mine.empty else mine
# Conversions diese Woche — Kunden via Setter (über Lead-Match auf Name)
if not mine.empty and not df_kunden.empty:
    my_lead_names = set(mine["Name"].dropna().tolist())
    conv_week = df_kunden[df_kunden["Lead"].isin(my_lead_names)]
    if not conv_week.empty and "Start Date" in conv_week.columns:
        conv_week = conv_week[conv_week["Start Date"] >= week_start]
else:
    conv_week = pd.DataFrame()

pipeline_open = mine[mine["Status"].isin(["New", "Qualified", "Contacted"])] if not mine.empty else mine
hot_leads     = mine[mine["Lead Score"] >= 70] if not mine.empty else mine

cols = st.columns(5)
cols[0].metric("Meine Leads",        len(mine))
cols[1].metric("Hot Leads (Score≥70)", len(hot_leads))
cols[2].metric("Calls heute",        len(booked_today))
cols[3].metric("Conversions Woche",  len(conv_week))
cols[4].metric("Pipeline offen",     len(pipeline_open))


# Empty-Hinweis
if mine.empty:
    st.markdown("---")
    render_empty_state(
        "Aktuell keine Leads dir zugeordnet (Setter-Feld). "
        "Admin muss dich auf Leads setzen.",
        icon="📋",
    )
    st.stop()


st.markdown("---")


# Heutige Calls — wichtigster Action-Block
st.subheader(":material/phone_in_talk: Calls heute")
if booked_today.empty:
    st.caption("Heute keine Calls gebucht.")
else:
    for _, lead in booked_today.iterrows():
        with st.container(border=True):
            cols = st.columns([3, 2, 2, 1])
            cols[0].markdown(f"**{lead['Name']}**")
            cols[0].caption(f"{lead.get('E-Mail', '')}  ·  Score {int(lead.get('Lead Score') or 0)}")
            termin = lead.get("Termin am")
            if pd.notna(termin):
                cols[1].markdown(f"🕐 {termin.tz_convert(TZ_BERLIN).strftime('%H:%M Uhr')}")
            cols[2].caption(f"Status: {lead.get('Status', '—')}")
            link = lead.get("Meet-Link")
            if link:
                cols[3].markdown(f"[Meet ↗]({link})")


st.markdown("---")


# Pipeline-Snippet
st.subheader(":material/view_kanban: Pipeline-Snapshot")
pipeline_counts = mine["Status"].value_counts() if not mine.empty else pd.Series(dtype=int)
pcols = st.columns(5)
for i, status in enumerate(["New", "Qualified", "Contacted", "Converted", "Lost"]):
    pcols[i].metric(status, int(pipeline_counts.get(status, 0)))
