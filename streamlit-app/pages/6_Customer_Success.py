"""Customer Success — Onboarding-Funnel · Health-Score · MRR + Edit-Modal.

Operations-Sicht für den Account-Manager / CS-Lead:
    Wer hängt im Onboarding?
    Wer ist Churn-Risk (Health < 50)?
    Welcher Mentor betreut welchen Kunden?
    Wie verteilt sich der MRR auf die Programme?

Edit-Modal aktualisiert Onboarding-Stage, Status, MRR und LTV in Airtable.
Status nutzt `typecast=True` damit fehlende Select-Werte (Onboarding/Paused/
Churned) beim ersten Klick automatisch angelegt werden.

Pattern parallel zu pages/2_Leads.py und pages/5_Mentoren.py.
"""

from __future__ import annotations

import pathlib
import sys
from datetime import datetime

import pandas as pd
import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from components import confirm_save_buttons, render_empty_state  # noqa: E402
from components.cs_kpi_row import render_cs_kpi_row  # noqa: E402
from components.health_distribution import render_health_distribution  # noqa: E402
from components.mrr_chart import render_mrr_chart  # noqa: E402
from components.onboarding_funnel import render_onboarding_funnel  # noqa: E402
from integrations.airtable_helpers import load_kunden, update_kunde  # noqa: E402
from lib.filters import HEALTH_TIER_OPTIONS, filter_kunden, unique_options  # noqa: E402
from lib.kpis import ONBOARDING_STAGES, compute_cs_kpis  # noqa: E402


STATUS_OPTIONS = ["Active", "Onboarding", "Paused", "Churned"]


# -----------------------------------------------------------------------------
# Modal — Kunde bearbeiten
# -----------------------------------------------------------------------------

@st.dialog("Kunde bearbeiten", width="large")
def edit_kunde_modal(kunde: pd.Series) -> None:
    """Modal mit den wichtigsten editierbaren Feldern eines Kunden."""
    st.subheader(f"✏️ {kunde['Lead'] or '—'}")
    st.caption(
        f"📦 {kunde.get('Program', '—') or '—'}  ·  "
        f"👤 Mentor: {kunde.get('Mentor Name', '—') or '—'}"
    )
    st.markdown("---")

    # Performance-Snapshot (read-only) — warum man den Kunden anfasst
    pcols = st.columns(3)
    health = int(kunde.get("Health Score") or 0)
    pcols[0].metric(
        "Health Score",
        f"{kunde.get('Health Emoji', '')} {health}",
        kunde.get("Health Tier", "—"),
    )
    last = kunde.get("Letzte Session")
    if pd.notna(last):
        days_ago = (pd.Timestamp.now(tz="UTC") - last).days
        pcols[1].metric("Letzte Session", f"vor {days_ago} d")
    else:
        pcols[1].metric("Letzte Session", "—")
    start = kunde.get("Start Date")
    if pd.notna(start):
        pcols[2].metric("Start", start.strftime("%d.%m.%Y"))
    else:
        pcols[2].metric("Start", "—")

    st.markdown("---")

    # Editierbare Felder
    col1, col2 = st.columns(2)
    cur_onb = kunde["Onboarding Status"] if kunde["Onboarding Status"] in ONBOARDING_STAGES else "Pending"
    new_onb = col1.selectbox(
        "Onboarding-Stage",
        ONBOARDING_STAGES,
        index=ONBOARDING_STAGES.index(cur_onb),
        key=f"kunde_onb_{kunde['id']}",
    )
    cur_status = kunde["Status"] if kunde["Status"] in STATUS_OPTIONS else "Active"
    new_status = col2.selectbox(
        "Status",
        STATUS_OPTIONS,
        index=STATUS_OPTIONS.index(cur_status),
        key=f"kunde_status_{kunde['id']}",
        help="Neue Optionen (Onboarding/Paused/Churned) werden bei Speichern in Airtable angelegt",
    )

    col3, col4 = st.columns(2)
    new_mrr = col3.number_input(
        "MRR (EUR)",
        min_value=0.0, step=10.0,
        value=float(kunde.get("MRR (EUR)") or 0),
        key=f"kunde_mrr_{kunde['id']}",
    )
    new_ltv = col4.number_input(
        "LTV (EUR)",
        min_value=0.0, step=100.0,
        value=float(kunde.get("LTV") or 0),
        key=f"kunde_ltv_{kunde['id']}",
    )

    st.markdown("---")

    save, cancel = confirm_save_buttons(key_prefix=f"kunde_modal_{kunde['id']}")
    if save:
        patch: dict = {
            "Onboarding Status": new_onb,
            "Status":            new_status,
            "MRR (EUR)":         float(new_mrr),
            "LTV":               float(new_ltv),
        }
        try:
            update_kunde(kunde["id"], patch)
            st.success("Aktualisiert.")
            st.rerun()
        except Exception as e:
            st.error(f"Speichern fehlgeschlagen: {type(e).__name__}: {e}")
    if cancel:
        st.rerun()


# -----------------------------------------------------------------------------
# Page
# -----------------------------------------------------------------------------

st.title("🤝 Customer Success")
st.caption(
    "Onboarding · Health · MRR — Klick auf ✏️ neben einem Kunden öffnet das Edit-Modal"
)

df = load_kunden()
if df.empty:
    render_empty_state("Keine Kunden vorhanden.")
    st.stop()


# ----- KPI-Strip --------------------------------------------------------------

render_cs_kpi_row(compute_cs_kpis(df))

st.markdown("---")


# ----- Charts: Funnel + Health (Zeile 1)  |  MRR (Zeile 2)  -------------------

ccols = st.columns(2)
with ccols[0]:
    render_onboarding_funnel(df)
with ccols[1]:
    render_health_distribution(df)

render_mrr_chart(df)

st.markdown("---")


# ----- Filter-Row (6 Spalten) -------------------------------------------------

fcols = st.columns(6)
status_filter      = fcols[0].selectbox("Status",      ["Alle"] + STATUS_OPTIONS)
onboarding_filter  = fcols[1].selectbox("Onboarding",  ["Alle"] + ONBOARDING_STAGES)
program_filter     = fcols[2].selectbox("Programm",    unique_options(df, "Program"))
mentor_filter      = fcols[3].selectbox("Mentor",      unique_options(df, "Mentor Name"))
health_filter      = fcols[4].selectbox("Health-Tier", HEALTH_TIER_OPTIONS)
search             = fcols[5].text_input("Suche (Lead)", "")


# ----- Filter anwenden + Sort -------------------------------------------------

filtered = filter_kunden(
    df,
    status=status_filter, onboarding=onboarding_filter,
    programm=program_filter, mentor=mentor_filter,
    health_tier=health_filter, search=search,
).reset_index(drop=True)

# Sortierung: Churn-Risk first (niedrigster Health zuerst → CS-Aufmerksamkeit)
filtered = filtered.sort_values(
    ["Health Score", "Letzte Session"], ascending=[True, True], na_position="first",
).reset_index(drop=True)

st.write(f"**{len(filtered)} Kunden** gefunden")

if filtered.empty:
    render_empty_state("Keine Kunden im aktuellen Filter.", icon="🔍")
    st.stop()


# ----- Kunden-Liste -----------------------------------------------------------

hcols = st.columns([0.5, 2.5, 2, 1.8, 1.5, 1.2, 1.2, 1.2, 0.8])
hcols[0].markdown("**●**")
hcols[1].markdown("**Lead**")
hcols[2].markdown("**Programm**")
hcols[3].markdown("**Mentor**")
hcols[4].markdown("**Onboarding**")
hcols[5].markdown("**MRR**")
hcols[6].markdown("**Letzte Session**")
hcols[7].markdown("**Health**")
hcols[8].markdown("**Edit**")
st.markdown(
    "<hr style='margin-top:0; margin-bottom:0.5rem'>",
    unsafe_allow_html=True,
)

for _, kunde in filtered.iterrows():
    cols = st.columns([0.5, 2.5, 2, 1.8, 1.5, 1.2, 1.2, 1.2, 0.8])
    cols[0].markdown(kunde.get("Health Emoji", "●"))
    cols[1].markdown(f"**{kunde['Lead'] or '—'}**")
    cols[2].caption(kunde.get("Program") or "—")
    cols[3].caption(kunde.get("Mentor Name") or "—")
    cols[4].markdown(f"`{kunde['Onboarding Status'] or '—'}`")
    mrr = kunde.get("MRR (EUR)") or 0
    cols[5].markdown(f"`€ {mrr:,.0f}`")

    last = kunde.get("Letzte Session")
    if pd.notna(last):
        days_ago = (pd.Timestamp.now(tz="UTC") - last).days
        cols[6].caption(f"vor {days_ago} Tagen")
    else:
        cols[6].caption("—")

    score = int(kunde.get("Health Score") or 0)
    cols[7].markdown(f"`{score}`  {kunde.get('Health Tier', '')}")

    if cols[8].button(
        "✏️",
        key=f"edit_kunde_btn_{kunde['id']}",
        help="Kunde bearbeiten",
    ):
        edit_kunde_modal(kunde)
