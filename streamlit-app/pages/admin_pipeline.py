"""Pipeline — Lead-Funnel als Kanban-View (Admin-only).

Spalten = Lead-Status-Stages. Pro Spalte vertikaler Stack von Lead-Cards
mit Score-Tier + Name + Setter + Termin.
"""

from __future__ import annotations

import pathlib
import sys

import pandas as pd
import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from components import render_empty_state  # noqa: E402
from integrations.airtable_helpers import load_leads  # noqa: E402
from integrations.auth import require_tool_access  # noqa: E402
from lib.tz import TZ_BERLIN  # noqa: E402


require_tool_access("dashboard", "read")


STAGES = ["New", "Qualified", "Contacted", "Converted", "Lost"]
STAGE_COLORS = {
    "New":       "#dbeafe",  # blau pastell
    "Qualified": "#fef3c7",  # gelb pastell
    "Contacted": "#fed7aa",  # orange pastell
    "Converted": "#dcfce7",  # grün pastell
    "Lost":      "#fee2e2",  # rot pastell
}


def tier_emoji(score: int) -> str:
    if score >= 85: return "🔥"
    if score >= 70: return "🌶️"
    if score >= 40: return "💧"
    return "❄️"


st.title(":material/view_kanban: Pipeline")
st.caption("Lead-Funnel als Kanban. Spalten = Status-Stages. Sortierung: höchster Score zuerst.")


df = load_leads()
if df.empty:
    render_empty_state("Keine Leads in der Datenbank.", icon="📋")
    st.stop()


# Globale Filter
fcols = st.columns(4)
source_filter = fcols[0].selectbox(
    "Source",
    ["Alle"] + sorted(df["Source"].dropna().unique().tolist()),
)
setter_filter = fcols[1].selectbox(
    "Setter",
    ["Alle"] + sorted([s for s in df["Setter"].dropna().unique() if s]),
)
min_score = fcols[2].slider("Min Score", 0, 100, 0)
search = fcols[3].text_input("Suche (Name)", "")

filtered = df.copy()
if source_filter != "Alle":
    filtered = filtered[filtered["Source"] == source_filter]
if setter_filter != "Alle":
    filtered = filtered[filtered["Setter"] == setter_filter]
if min_score > 0:
    filtered = filtered[filtered["Lead Score"] >= min_score]
if search:
    filtered = filtered[filtered["Name"].str.contains(search, case=False, na=False)]


st.markdown("---")


# Kanban-Spalten
cols = st.columns(len(STAGES))
for col, stage in zip(cols, STAGES):
    stage_df = filtered[filtered["Status"] == stage].sort_values("Lead Score", ascending=False)
    bg = STAGE_COLORS.get(stage, "#e5e7eb")
    with col:
        st.markdown(
            f"""
            <div style='background:{bg}; padding:8px 10px; border-radius:6px;
                        text-align:center; margin-bottom:8px;'>
              <div style='font-size:11px; text-transform:uppercase; letter-spacing:1px;
                          color:#374151;'>{stage}</div>
              <div style='font-size:24px; font-weight:600; color:#111;'>{len(stage_df)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if stage_df.empty:
            st.caption("—")
            continue
        for _, lead in stage_df.iterrows():
            score = int(lead.get("Lead Score") or 0)
            termin = lead.get("Termin am")
            termin_str = (
                termin.tz_convert(TZ_BERLIN).strftime("%d.%m. %H:%M")
                if pd.notna(termin) else ""
            )
            with st.container(border=True):
                st.markdown(f"{tier_emoji(score)} **{lead['Name'] or '—'}**  `{score}`")
                if lead.get("Source"):
                    st.caption(f"📡 {lead['Source']}")
                if lead.get("Setter"):
                    st.caption(f"👤 {lead['Setter']}")
                if termin_str:
                    st.caption(f"🕐 {termin_str}")
