"""Meine Mentees — Mentor sieht nur eigene Mentees mit limitiertem Edit.

Pattern wie pages/6_Customer_Success.py, aber:
    - Filter: nur Mentees mit Mentor == self
    - Edit-Modal: nur Onboarding-Status + Notiz (nicht MRR/LTV/Status)
"""

from __future__ import annotations

import pathlib
import sys

import pandas as pd
import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from components import confirm_save_buttons, render_empty_state  # noqa: E402
from integrations.airtable_helpers import (  # noqa: E402
    for_mentor, load_kunden, update_kunde,
)
from integrations.auth import current_user, require_tool_access  # noqa: E402
from lib.filters import HEALTH_TIER_OPTIONS  # noqa: E402
from lib.kpis import ONBOARDING_STAGES  # noqa: E402


user = require_tool_access("mentees", "write")
mentor_id = user.get("mentor_id")

if not mentor_id:
    st.error("Account ohne Mentor-Link. Bitte beim Admin melden.")
    st.stop()


# -----------------------------------------------------------------------------
# Modal — Mentee bearbeiten (LIMITED EDIT: nur Onboarding + Notiz)
# -----------------------------------------------------------------------------

@st.dialog("Mentee bearbeiten", width="large")
def edit_mentee_modal(mentee: pd.Series) -> None:
    st.subheader(f":material/edit: {mentee['Lead']}")
    st.caption(
        f"📦 {mentee.get('Program', '—')}  ·  "
        f"Health {int(mentee.get('Health Score') or 0)} ({mentee.get('Health Tier', '—')})"
    )
    st.markdown("---")

    # Read-only Snapshot
    pcols = st.columns(3)
    pcols[0].metric("MRR", f"€ {int(mentee.get('MRR (EUR)') or 0)}")
    last = mentee.get("Letzte Session")
    if pd.notna(last):
        days_ago = (pd.Timestamp.now(tz="UTC") - last).days
        pcols[1].metric("Letzte Session", f"vor {days_ago} d")
    else:
        pcols[1].metric("Letzte Session", "—")
    pcols[2].metric("Status", mentee.get("Status", "—"))

    st.info(
        "Mentor-Rechte: du darfst Onboarding-Stage updaten und Notizen anfügen. "
        "MRR, LTV und Status werden vom Admin verwaltet."
    )

    # Editierbare Felder
    cur_onb = mentee["Onboarding Status"] if mentee["Onboarding Status"] in ONBOARDING_STAGES else "Pending"
    new_onb = st.selectbox(
        "Onboarding-Stage",
        ONBOARDING_STAGES,
        index=ONBOARDING_STAGES.index(cur_onb),
        key=f"mt_onb_{mentee['id']}",
    )
    notiz = st.text_area(
        "Notiz anhängen (optional)",
        placeholder="Wird mit Timestamp und deinem Namen vermerkt",
        key=f"mt_note_{mentee['id']}",
    )

    st.markdown("---")
    save, cancel = confirm_save_buttons(key_prefix=f"mt_modal_{mentee['id']}")
    if save:
        patch: dict = {"Onboarding Status": new_onb}
        # Notiz an Notizen-Spalte anhängen (wenn vorhanden)
        # Wir versuchen es; existiert das Feld in Kunden nicht, ignorieren wir den Notiz-Patch.
        if notiz.strip():
            from datetime import datetime
            from lib.tz import TZ_BERLIN
            ts = datetime.now(TZ_BERLIN).strftime("%Y-%m-%d %H:%M")
            patch["Notizen"] = f"[{ts} · {user.get('name','Mentor')}] {notiz.strip()}"
        try:
            update_kunde(mentee["id"], patch)
            st.success("Aktualisiert.")
            st.rerun()
        except Exception as e:  # noqa: BLE001
            st.error(f"Speichern fehlgeschlagen: {type(e).__name__}: {e}")
    if cancel:
        st.rerun()


# -----------------------------------------------------------------------------
# Page
# -----------------------------------------------------------------------------

st.title(":material/person: Meine Mentees")
st.caption(f"Nur Mentees, die dir zugewiesen sind. ✏️ öffnet das limitierte Edit-Modal.")

all_mentees = load_kunden()
my_mentees  = for_mentor(all_mentees, mentor_id, link_col="Mentor").reset_index(drop=True)

if my_mentees.empty:
    render_empty_state(
        "Du hast aktuell keine Mentees zugewiesen.",
        icon="🧑‍🎓",
    )
    st.stop()

# Mini-KPI-Strip
kcols = st.columns(3)
kcols[0].metric("Meine Mentees", len(my_mentees))
activated = int((my_mentees["Onboarding Status"] == "Activated").sum())
kcols[1].metric("Davon Activated", activated)
churn_risk = int((my_mentees["Health Score"] < 50).sum())
kcols[2].metric("Davon Churn-Risk", churn_risk, help="Health Score < 50")

st.markdown("---")


# Filter
fcols = st.columns(4)
onb_filter    = fcols[0].selectbox("Onboarding", ["Alle"] + ONBOARDING_STAGES)
health_filter = fcols[1].selectbox("Health-Tier", HEALTH_TIER_OPTIONS)
search        = fcols[2].text_input("Suche (Lead)", "")
fcols[3].markdown(f"<div style='padding-top:1.8rem'>{len(my_mentees)} eigene Mentees</div>",
                  unsafe_allow_html=True)

filtered = my_mentees.copy()
if onb_filter != "Alle":
    filtered = filtered[filtered["Onboarding Status"] == onb_filter]
if health_filter != "Alle":
    filtered = filtered[filtered["Health Tier"] == health_filter]
if search:
    filtered = filtered[filtered["Lead"].str.contains(search, case=False, na=False)]
filtered = filtered.sort_values(["Health Score", "Letzte Session"], ascending=[True, True],
                                na_position="first").reset_index(drop=True)


# Liste
COLS = [0.4, 2.5, 2, 1.5, 1.2, 1.5, 1.5, 0.8]
hcols = st.columns(COLS)
hcols[0].markdown("**●**")
hcols[1].markdown("**Lead**")
hcols[2].markdown("**Programm**")
hcols[3].markdown("**Onboarding**")
hcols[4].markdown("**MRR**")
hcols[5].markdown("**Letzte Session**")
hcols[6].markdown("**Health**")
hcols[7].markdown("**Edit**")
st.markdown("<hr style='margin-top:0; margin-bottom:0.5rem'>", unsafe_allow_html=True)

for _, mentee in filtered.iterrows():
    cols = st.columns(COLS)
    cols[0].markdown(mentee.get("Health Emoji", "●"))
    cols[1].markdown(f"**{mentee['Lead']}**")
    cols[2].caption(mentee.get("Program") or "—")
    cols[3].markdown(f"`{mentee['Onboarding Status']}`")
    cols[4].markdown(f"`€ {int(mentee.get('MRR (EUR)') or 0)}`")
    last = mentee.get("Letzte Session")
    if pd.notna(last):
        cols[5].caption(f"vor {(pd.Timestamp.now(tz='UTC')-last).days} d")
    else:
        cols[5].caption("—")
    cols[6].markdown(f"`{int(mentee.get('Health Score') or 0)}` {mentee.get('Health Tier', '')}")
    if cols[7].button("✏️", key=f"em_btn_{mentee['id']}"):
        edit_mentee_modal(mentee)
