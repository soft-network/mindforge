"""Leads — filterbare Browse-View mit direkter Edit-in-Tabelle."""

from __future__ import annotations

import pathlib
import sys
from datetime import date, datetime, timedelta

import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from integrations.airtable_helpers import load_leads, update_lead  # noqa: E402
from lib.filters import (  # noqa: E402
    DATE_RANGE_OPTIONS,
    filter_by_date_range,
    filter_leads,
    unique_options,
)


# Page-Config + Passwort-Gate werden in app.py zentral gesetzt.

st.title("📋 Leads")
st.caption(
    "Filter · Zeitraum · direkte Inline-Bearbeitung von Status und Lead Score"
)

df = load_leads()

if df.empty:
    st.info("Keine Leads vorhanden.")
    st.stop()


# -----------------------------------------------------------------------------
# Filter-Row (5 Spalten + ggf. Date-Range bei Custom)
# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------
# Filter anwenden
# -----------------------------------------------------------------------------

filtered = filter_leads(
    df,
    status=status_filter,
    source=source_filter,
    min_score=min_score,
    search=search,
)
filtered = filter_by_date_range(
    filtered,
    range_name=date_range,
    custom_start=custom_start,
    custom_end=custom_end,
).reset_index(drop=True)

st.write(f"**{len(filtered)} Leads** gefunden")

if filtered.empty:
    st.caption("Keine Leads im aktuellen Filter.")
    st.stop()


# -----------------------------------------------------------------------------
# Editable Tabelle (st.data_editor) — Status + Lead Score in-place editierbar
# -----------------------------------------------------------------------------

EDITOR_KEY = "leads_table_editor"
STATUS_OPTIONS = ["New", "Qualified", "Contacted", "Converted", "Lost"]

# Spalten + Reihenfolge im Display. id muss drin sein (versteckt) damit wir
# nach Edit den Record finden.
display_df = filtered[
    ["id", "Name", "E-Mail", "Source", "Lead Score", "Status", "Erstellt am"]
].copy()

# Status sanitisieren: leere oder unbekannte Werte → "New" damit der
# Selectbox-Editor sie als gültige Auswahl erkennt.
display_df["Status"] = display_df["Status"].apply(
    lambda s: s if s in STATUS_OPTIONS else "New"
)

edited = st.data_editor(
    display_df,
    column_config={
        "id": None,  # versteckt
        "Name":        st.column_config.TextColumn("Name",        disabled=True),
        "E-Mail":      st.column_config.TextColumn("E-Mail",      disabled=True),
        "Source":      st.column_config.TextColumn("Source",      disabled=True),
        "Erstellt am": st.column_config.DatetimeColumn(
            "Erstellt am", disabled=True, format="DD.MM.YYYY HH:mm",
        ),
        "Lead Score":  st.column_config.NumberColumn(
            "Lead Score ✏️", min_value=0, max_value=100, step=1,
            help="Direkt in der Zelle editieren",
        ),
        "Status": st.column_config.SelectboxColumn(
            "Status ✏️", options=STATUS_OPTIONS, required=True,
            help="Direkt in der Zelle editieren",
        ),
    },
    hide_index=True,
    use_container_width=True,
    key=EDITOR_KEY,
    num_rows="fixed",
)


# -----------------------------------------------------------------------------
# Save-Button — Batch-Update nach Airtable
# -----------------------------------------------------------------------------

state = st.session_state.get(EDITOR_KEY, {})
edited_rows: dict[int, dict] = state.get("edited_rows", {}) if state else {}

scol1, scol2 = st.columns([1, 4])
with scol1:
    save_clicked = st.button(
        "💾 Änderungen speichern",
        type="primary",
        disabled=not edited_rows,
    )
with scol2:
    if edited_rows:
        st.caption(f"⚠️ {len(edited_rows)} Zeile(n) bearbeitet — noch nicht gespeichert.")
    else:
        st.caption("Keine ungespeicherten Änderungen.")

if save_clicked and edited_rows:
    success_count = 0
    error_count = 0
    for row_idx, changes in edited_rows.items():
        try:
            lead_id = filtered.iloc[row_idx]["id"]
        except (IndexError, KeyError):
            error_count += 1
            continue

        # UI-Spaltennamen → Airtable-Feldnamen
        patch = {}
        if "Status" in changes:
            patch["Status"] = changes["Status"]
        if "Lead Score" in changes:
            patch["Quiz Score"] = int(changes["Lead Score"])

        if not patch:
            continue

        try:
            update_lead(lead_id, patch)
            success_count += 1
        except Exception as e:
            error_count += 1
            st.error(f"Fehler bei Lead {lead_id}: {e}")

    if success_count:
        st.success(f"✅ {success_count} Lead(s) aktualisiert.")
    if error_count:
        st.warning(f"⚠️ {error_count} Update(s) fehlgeschlagen.")
    st.rerun()
