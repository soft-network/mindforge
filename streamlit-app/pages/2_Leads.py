"""Leads — filterbare Browse-View mit Edit-Aktion pro Lead."""

from __future__ import annotations

import pathlib
import sys

import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from integrations.airtable_helpers import load_leads, update_lead  # noqa: E402
from lib.filters import filter_leads, unique_options  # noqa: E402


# Page-Config + Passwort-Gate werden in app.py zentral gesetzt.

st.title("📋 Leads")
st.caption("Browse · Filter · Quick-Edit (Status + Score)")

df = load_leads()

if df.empty:
    st.info("Keine Leads vorhanden.")
    st.stop()


# -----------------------------------------------------------------------------
# Filter-Row
# -----------------------------------------------------------------------------

fcols = st.columns(4)
status_filter = fcols[0].selectbox("Status", unique_options(df, "Status"))
source_filter = fcols[1].selectbox("Source", unique_options(df, "Source"))
min_score     = fcols[2].slider("Min Lead Score", 0, 100, 0)
search        = fcols[3].text_input("Suche (Name/E-Mail)", "")

filtered = filter_leads(
    df,
    status=status_filter,
    source=source_filter,
    min_score=min_score,
    search=search,
)

st.write(f"**{len(filtered)} Leads** gefunden")


# -----------------------------------------------------------------------------
# Liste
# -----------------------------------------------------------------------------

display_cols = ["Name", "E-Mail", "Source", "Lead Score", "Status", "Erstellt am"]
st.dataframe(
    filtered[display_cols].sort_values("Erstellt am", ascending=False),
    use_container_width=True,
    hide_index=True,
)


# -----------------------------------------------------------------------------
# Quick-Edit
# -----------------------------------------------------------------------------

st.markdown("### Lead bearbeiten")

if len(filtered) == 0:
    st.caption("Keine Leads im aktuellen Filter zum Bearbeiten.")
    st.stop()

selected = st.selectbox(
    "Lead auswählen",
    filtered["id"].tolist(),
    format_func=lambda lid: filtered.loc[filtered["id"] == lid, "Name"].values[0],
)

if selected:
    row = filtered[filtered["id"] == selected].iloc[0]
    status_options = ["New", "Qualified", "Contacted", "Converted", "Lost"]
    cur_status = row["Status"] if row["Status"] in status_options else "New"

    ecols = st.columns(2)
    new_status = ecols[0].selectbox(
        "Status",
        status_options,
        index=status_options.index(cur_status),
    )
    new_score = ecols[1].slider(
        "Lead Score", 0, 100, int(row["Lead Score"] or 0)
    )

    if st.button("Speichern", type="primary"):
        update_lead(selected, {"Status": new_status, "Quiz Score": new_score})
        st.success("Aktualisiert.")
        st.rerun()
