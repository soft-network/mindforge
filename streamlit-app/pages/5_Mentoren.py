"""Mentoren — KPI-Strip + Auslastungs-/Spezialisierungs-Charts + Liste mit Edit-Modal.

Pattern parallel zu pages/2_Leads.py: Liste pro Zeile mit ✏️ öffnet ein
st.dialog-Modal für die Stamm-Daten-Bearbeitung.

Mentor-Performance-Daten (Aktive Kunden, Avg NPS) werden Python-side in
integrations.airtable_helpers.load_mentoren() durch Joins über Sessions+Kunden
berechnet — die Airtable Meta-API erlaubt kein Anlegen von Count/Rollup-Feldern.
"""

from __future__ import annotations

import pathlib
import sys

import pandas as pd
import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from components.mentor_capacity_chart import render_mentor_capacity  # noqa: E402
from components.mentor_kpi_row import render_mentor_kpi_row  # noqa: E402
from components.specialization_chart import render_specialization  # noqa: E402
from integrations.airtable_helpers import load_mentoren, update_mentor  # noqa: E402
from integrations.auth import require_tool_access  # noqa: E402
from lib.filters import (  # noqa: E402
    filter_mentoren,
    unique_options,
    unique_specializations,
)
from lib.kpis import compute_mentor_kpis  # noqa: E402


STATUS_OPTIONS = ["Active", "Inactive", "On Leave"]
SPEZ_OPTIONS   = ["Business", "Sales", "Mindset", "Marketing", "Operations", "Finance"]


# -----------------------------------------------------------------------------
# Modal — Mentor bearbeiten
# -----------------------------------------------------------------------------

@st.dialog("Mentor bearbeiten", width="large")
def edit_mentor_modal(mentor: pd.Series) -> None:
    """Modal-Overlay mit den editierbaren Stamm-Feldern eines Mentors."""
    st.subheader(f"✏️ {mentor['Name'] or '—'}")
    st.caption(
        f"📧 {mentor.get('E-Mail', '—') or '—'}  ·  "
        f"📍 {mentor.get('Stadt', '—') or '—'}"
    )
    st.markdown("---")

    # Performance-Snapshot (read-only) — zeigt warum man den Mentor evtl. anpassen will
    pcols = st.columns(3)
    pcols[0].metric("Aktive Kunden",  mentor.get("Aktive Kunden", 0))
    pcols[1].metric("Sessions",       mentor.get("Sessions Count", 0))
    nps = mentor.get("Avg NPS")
    pcols[2].metric("⌀ NPS",          f"{nps:.1f}" if pd.notna(nps) else "—")

    st.markdown("---")

    # Editierbare Felder
    col1, col2 = st.columns(2)
    cur_status = mentor["Status"] if mentor["Status"] in STATUS_OPTIONS else "Active"
    new_status = col1.selectbox(
        "Status",
        STATUS_OPTIONS,
        index=STATUS_OPTIONS.index(cur_status),
        key=f"mentor_status_{mentor['id']}",
    )
    new_cap = col2.slider(
        "Kapazität pro Woche",
        0, 30,
        value=int(mentor.get("Kapazität") or 0),
        key=f"mentor_cap_{mentor['id']}",
    )

    cur_spez = mentor.get("Spezialisierung") or []
    if not isinstance(cur_spez, list):
        cur_spez = []
    new_spez = st.multiselect(
        "Spezialisierung",
        SPEZ_OPTIONS,
        default=[s for s in cur_spez if s in SPEZ_OPTIONS],
        key=f"mentor_spez_{mentor['id']}",
    )

    col3, col4 = st.columns(2)
    new_stadt = col3.text_input(
        "Stadt",
        value=mentor.get("Stadt") or "",
        key=f"mentor_stadt_{mentor['id']}",
    )
    new_email = col4.text_input(
        "E-Mail",
        value=mentor.get("E-Mail") or "",
        key=f"mentor_email_{mentor['id']}",
    )

    st.markdown("---")
    bcol1, bcol2 = st.columns(2)
    if bcol1.button(
        "💾 Speichern",
        type="primary",
        use_container_width=True,
        key=f"mentor_save_{mentor['id']}",
    ):
        patch: dict = {
            "Status":              new_status,
            "Kapazität pro Woche": int(new_cap),
            "Spezialisierung":     new_spez,
            "Stadt":               new_stadt,
            "E-Mail":              new_email,
        }
        try:
            update_mentor(mentor["id"], patch)
            st.success("Aktualisiert.")
            st.rerun()
        except Exception as e:
            st.error(f"Fehler: {e}")

    if bcol2.button(
        "Abbrechen",
        use_container_width=True,
        key=f"mentor_cancel_{mentor['id']}",
    ):
        st.rerun()


# -----------------------------------------------------------------------------
# Hilfsfunktion: Status-Badge
# -----------------------------------------------------------------------------

def status_badge(status: str) -> str:
    return {
        "Active":   "🟢",
        "Inactive": "⚫",
        "On Leave": "🟡",
    }.get(status, "❔")


# -----------------------------------------------------------------------------
# Page
# -----------------------------------------------------------------------------

# Permission-Gate
require_tool_access("mentoren", "read")

df = load_mentoren()
if df.empty:
    st.title("👥 Mentoren")
    st.info("Keine Mentoren vorhanden.")
    st.stop()


st.title(f"👥 Mentoren ({len(df)})")
st.caption(
    "Performance · Auslastung · Spezialisierungen — Klick auf ✏️ öffnet das Edit-Modal"
)


# -----------------------------------------------------------------------------
# Tabs: Übersicht (KPIs+Charts) | Verwaltung (Filter+Liste+Edit)
# -----------------------------------------------------------------------------

tab_overview, tab_mgmt = st.tabs(["📊 Übersicht", "📋 Verwaltung"])


# ----- TAB ÜBERSICHT ---------------------------------------------------------

with tab_overview:
    render_mentor_kpi_row(compute_mentor_kpis(df))
    st.markdown("---")
    ccols = st.columns(2)
    with ccols[0]:
        render_mentor_capacity(df)
    with ccols[1]:
        render_specialization(df)


# ----- TAB VERWALTUNG --------------------------------------------------------

with tab_mgmt:
    # Filter-Row (5 Spalten)
    fcols = st.columns(5)
    status_filter = fcols[0].selectbox("Status",         ["Alle"] + STATUS_OPTIONS)
    spez_filter   = fcols[1].selectbox("Spezialisierung", unique_specializations(df))
    stadt_filter  = fcols[2].selectbox("Stadt",           unique_options(df, "Stadt"))
    search        = fcols[3].text_input("Suche (Name/E-Mail)", "")
    sort_by       = fcols[4].selectbox(
        "Sortieren nach",
        ["⌀ NPS (hoch → niedrig)", "Aktive Kunden", "Kapazität", "Name (A–Z)"],
    )

    # Filter + Sort
    filtered = filter_mentoren(
        df,
        status=status_filter, spezialisierung=spez_filter,
        stadt=stadt_filter, search=search,
    ).reset_index(drop=True)

    if sort_by == "⌀ NPS (hoch → niedrig)":
        filtered = filtered.sort_values("Avg NPS", ascending=False, na_position="last")
    elif sort_by == "Aktive Kunden":
        filtered = filtered.sort_values("Aktive Kunden", ascending=False)
    elif sort_by == "Kapazität":
        filtered = filtered.sort_values("Kapazität", ascending=False)
    elif sort_by == "Name (A–Z)":
        filtered = filtered.sort_values("Name", ascending=True)
    filtered = filtered.reset_index(drop=True)

    st.write(f"**{len(filtered)} Mentoren** gefunden")

    if filtered.empty:
        st.caption("Keine Mentoren im aktuellen Filter.")
        st.stop()


    # Mentor-Liste mit Edit-Button
    hcols = st.columns([0.5, 2.5, 1.5, 2, 1.2, 1, 1.2, 1, 0.8])
    hcols[0].markdown("**●**")
    hcols[1].markdown("**Name**")
    hcols[2].markdown("**Stadt**")
    hcols[3].markdown("**Spezialisierung**")
    hcols[4].markdown("**Status**")
    hcols[5].markdown("**Kap.**")
    hcols[6].markdown("**Kunden**")
    hcols[7].markdown("**NPS**")
    hcols[8].markdown("**Edit**")
    st.markdown(
        "<hr style='margin-top:0; margin-bottom:0.5rem'>",
        unsafe_allow_html=True,
    )

    for _, mentor in filtered.iterrows():
        cols = st.columns([0.5, 2.5, 1.5, 2, 1.2, 1, 1.2, 1, 0.8])
        cols[0].markdown(status_badge(mentor["Status"]))
        cols[1].markdown(f"**{mentor['Name'] or '—'}**")
        cols[2].caption(mentor.get("Stadt") or "—")

        specs = mentor.get("Spezialisierung") or []
        cols[3].caption(", ".join(specs) if isinstance(specs, list) and specs else "—")

        cols[4].markdown(f"`{mentor['Status'] or '—'}`")
        cols[5].markdown(f"`{int(mentor['Kapazität'] or 0)}`")
        cols[6].markdown(f"`{int(mentor['Aktive Kunden'] or 0)}`")

        nps = mentor.get("Avg NPS")
        cols[7].markdown(f"`{nps:.1f}`" if pd.notna(nps) else "`—`")

        if cols[8].button(
            "✏️",
            key=f"edit_mentor_btn_{mentor['id']}",
            help="Mentor bearbeiten",
        ):
            edit_mentor_modal(mentor)
