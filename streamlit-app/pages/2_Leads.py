"""Leads — Liste mit Edit-Modal pro Zeile + Zeitfilter."""

from __future__ import annotations

import pathlib
import sys
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from integrations.airtable_helpers import (  # noqa: E402
    load_leads, load_mentor_lookup, update_lead,
)
from integrations.auth import require_tool_access  # noqa: E402
from lib.filters import (  # noqa: E402
    DATE_RANGE_OPTIONS,
    filter_by_date_range,
    filter_leads,
    unique_options,
)
from lib.tz import TZ_BERLIN  # noqa: E402

# Permission-Gate
require_tool_access("leads", "read")


STATUS_OPTIONS = ["New", "Qualified", "Contacted", "Converted", "Lost"]
MENTOR_NONE   = "— (nicht zugewiesen)"


# -----------------------------------------------------------------------------
# Modal — Lead bearbeiten
# -----------------------------------------------------------------------------

@st.dialog("Lead bearbeiten", width="large")
def edit_lead_modal(lead: pd.Series) -> None:
    """Modal-Overlay mit allen editierbaren Feldern eines Leads."""
    st.subheader(f"✏️ {lead['Name'] or '—'}")
    st.caption(
        f"📧 {lead.get('E-Mail', '—')}  ·  "
        f"📞 `{lead.get('Telefon', '—') or '—'}`  ·  "
        f"🌍 {lead.get('Land', '—') or '—'}"
    )
    st.markdown("---")

    # Quiz-Snapshot (read-only) — zur Erinnerung warum dieser Lead Score hat
    if lead.get("Branche") or lead.get("Monatsumsatz"):
        with st.expander("Quiz-Antworten", expanded=False):
            st.write(
                f"**Branche:** {lead.get('Branche') or '—'}  ·  "
                f"**Umsatz:** {lead.get('Monatsumsatz') or '—'}  ·  "
                f"**Wunsch:** {lead.get('Hauptwunsch') or '—'}  ·  "
                f"**Zeitbudget:** {lead.get('Zeitbudget') or '—'}"
            )

    # Editierbare Felder
    col1, col2 = st.columns(2)
    cur_status = lead["Status"] if lead["Status"] in STATUS_OPTIONS else "New"
    new_status = col1.selectbox(
        "Status",
        STATUS_OPTIONS,
        index=STATUS_OPTIONS.index(cur_status),
        key=f"modal_status_{lead['id']}",
    )
    new_score = col2.slider(
        "Lead Score",
        0, 100,
        value=int(lead.get("Lead Score") or 0),
        key=f"modal_score_{lead['id']}",
    )

    # Mentor-Zuweisung — wird beim Convert zu Kunde übernommen (Sales→CS-Handover)
    mentor_lookup = load_mentor_lookup()  # {rec_id: name}
    mentor_options = [MENTOR_NONE] + sorted(mentor_lookup.values())
    cur_mentor_name = lead.get("Mentor Name") or MENTOR_NONE
    if cur_mentor_name not in mentor_options:
        cur_mentor_name = MENTOR_NONE
    new_mentor_name = st.selectbox(
        "Mentor zuweisen",
        mentor_options,
        index=mentor_options.index(cur_mentor_name),
        key=f"modal_mentor_{lead['id']}",
        help="Optional. Wird beim Lead→Kunde-Convert in Customer Success übernommen.",
    )

    new_note = st.text_area(
        "Notiz anhängen (optional)",
        placeholder="Wird mit Timestamp an die bestehenden Notizen angehängt",
        key=f"modal_note_{lead['id']}",
    )

    # Bestehende Notizen als Read-only Hinweis
    if lead.get("Notizen"):
        with st.expander("Bestehende Notizen", expanded=False):
            st.text(lead["Notizen"])

    st.markdown("---")

    bcol1, bcol2 = st.columns(2)
    if bcol1.button(
        "💾 Speichern",
        type="primary",
        use_container_width=True,
        key=f"modal_save_{lead['id']}",
    ):
        patch: dict = {"Status": new_status, "Quiz Score": int(new_score)}
        # Mentor-Patch: leere Liste = un-assign, sonst RecordId-Liste
        if new_mentor_name == MENTOR_NONE:
            patch["Mentor"] = []
        else:
            mentor_id = next(
                (mid for mid, name in mentor_lookup.items() if name == new_mentor_name),
                None,
            )
            if mentor_id:
                patch["Mentor"] = [mentor_id]
        if new_note.strip():
            existing = lead.get("Notizen") or ""
            ts = datetime.now(TZ_BERLIN).strftime("%Y-%m-%d %H:%M")
            patch["Notizen"] = (existing + f"\n[{ts}] {new_note.strip()}").strip()
        try:
            update_lead(lead["id"], patch)
            st.success("Aktualisiert.")
            st.rerun()
        except Exception as e:
            st.error(f"Speichern fehlgeschlagen: {type(e).__name__}: {e}")

    if bcol2.button(
        "Abbrechen",
        use_container_width=True,
        key=f"modal_cancel_{lead['id']}",
    ):
        st.rerun()


# -----------------------------------------------------------------------------
# Hilfsfunktion: Tier-Badge
# -----------------------------------------------------------------------------

def tier_emoji(score: int) -> str:
    if score >= 85:
        return "🔥"
    if score >= 70:
        return "🌶️"
    if score >= 40:
        return "💧"
    return "❄️"


# -----------------------------------------------------------------------------
# Page — Filter + Liste
# -----------------------------------------------------------------------------

df = load_leads()
if df.empty:
    st.title("📋 Leads")
    st.info("Keine Leads vorhanden.")
    st.stop()

st.title(f"📋 Leads ({len(df)})")
st.caption(
    "Filter · Zeitraum · Klick auf ✏️ neben einem Lead öffnet das Edit-Modal"
)


# ----- Filter-Row (5 Spalten) -------------------------------------------------

fcols = st.columns(5)
status_filter = fcols[0].selectbox("Status", unique_options(df, "Status"))
source_filter = fcols[1].selectbox("Source", unique_options(df, "Source"))
min_score = fcols[2].slider("Min Lead Score", 0, 100, 0)
search = fcols[3].text_input("Suche (Name/E-Mail)", "")
date_range = fcols[4].selectbox("Zeitraum", DATE_RANGE_OPTIONS)

custom_start: date | None = None
custom_end: date | None = None
if date_range.startswith("Custom"):
    dcols = st.columns(2)
    default_start = (datetime.now() - timedelta(days=30)).date()
    custom_start = dcols[0].date_input("Von", value=default_start)
    custom_end = dcols[1].date_input("Bis", value=datetime.now().date())


# ----- Filter anwenden -------------------------------------------------------

filtered = filter_leads(
    df, status=status_filter, source=source_filter,
    min_score=min_score, search=search,
)
filtered = filter_by_date_range(
    filtered, range_name=date_range,
    custom_start=custom_start, custom_end=custom_end,
).reset_index(drop=True)

# Sortierung: hot leads first, newest first
filtered = filtered.sort_values(
    ["Lead Score", "Erstellt am"], ascending=[False, False]
).reset_index(drop=True)

st.write(f"**{len(filtered)} Leads** gefunden")

if filtered.empty:
    st.caption("Keine Leads im aktuellen Filter.")
    st.stop()


# ----- Lead-Liste mit Edit-Buttons -------------------------------------------

# Header-Row
COLS = [0.5, 2.6, 2.6, 1, 1.4, 1.6, 1.4, 0.8]
hcols = st.columns(COLS)
hcols[0].markdown("**🎯**")
hcols[1].markdown("**Name**")
hcols[2].markdown("**E-Mail**")
hcols[3].markdown("**Score**")
hcols[4].markdown("**Status**")
hcols[5].markdown("**Mentor**")
hcols[6].markdown("**Erstellt**")
hcols[7].markdown("**Edit**")
st.markdown(
    "<hr style='margin-top:0; margin-bottom:0.5rem'>",
    unsafe_allow_html=True,
)

# Lead-Rows
for _, lead in filtered.iterrows():
    cols = st.columns(COLS)
    score = int(lead.get("Lead Score") or 0)

    cols[0].markdown(tier_emoji(score))
    cols[1].markdown(f"**{lead['Name'] or '—'}**")
    cols[2].caption(lead["E-Mail"] or "—")
    cols[3].markdown(f"`{score}`")
    cols[4].markdown(f"`{lead['Status'] or 'New'}`")

    mentor_name = lead.get("Mentor Name") or "—"
    cols[5].caption(mentor_name if mentor_name != "—" else "—")

    erstellt = lead.get("Erstellt am")
    if pd.notna(erstellt):
        cols[6].caption(erstellt.strftime("%d.%m.%y %H:%M"))
    else:
        cols[6].caption("—")

    if cols[7].button(
        "✏️",
        key=f"edit_btn_{lead['id']}",
        help="Lead bearbeiten",
    ):
        edit_lead_modal(lead)
