"""Programme — Karten-Grid mit Mentor-Pool-Edit (Admin-Sicht).

Layout: Cards mit Programm-Snapshot (Lead-Count, Converted, MRR, Mentor-Pool).
Klick auf ✏️ → Edit-Modal: Mentor-Pool (Multi-Select) verwalten.
"""

from __future__ import annotations

import pathlib
import sys

import pandas as pd
import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from components import confirm_save_buttons, render_empty_state  # noqa: E402
from integrations.airtable_helpers import (  # noqa: E402
    load_mentor_lookup, load_programs, update_programm,
)
from integrations.auth import current_user, require_tool_access  # noqa: E402
from lib.permissions import can  # noqa: E402


require_tool_access("programme", "read")
user = current_user() or {}
can_edit = can(user.get("rolle", ""), "programme", "write")


@st.dialog("Mentor-Pool bearbeiten", width="large")
def edit_pool_modal(prog: pd.Series) -> None:
    """Multi-Select für die Mentor-Pool-Zuweisung."""
    st.subheader(f":material/inventory_2: {prog['Name']}")
    st.caption("Lege fest, welche Mentoren beim Convert-Workflow automatisch zugewiesen werden können.")
    st.markdown("---")

    mentor_lookup = load_mentor_lookup()
    all_mentor_names = sorted(mentor_lookup.values())
    cur_names = prog.get("Mentor-Pool-Namen") or []

    new_pool = st.multiselect(
        "Mentor-Pool",
        all_mentor_names,
        default=[n for n in cur_names if n in all_mentor_names],
        key=f"prog_pool_{prog['id']}",
        help="Mentoren in diesem Pool werden beim Convert-Workflow nach niedrigster Auslastung gewählt.",
    )

    st.markdown("---")
    save, cancel = confirm_save_buttons(key_prefix=f"prog_modal_{prog['id']}")
    if save:
        # Namen → RecordIds rückwärts mappen
        name_to_id = {n: mid for mid, n in mentor_lookup.items()}
        new_pool_ids = [name_to_id[n] for n in new_pool if n in name_to_id]
        try:
            update_programm(prog["id"], {"Mentoren": new_pool_ids})
            st.success(f"Pool aktualisiert ({len(new_pool_ids)} Mentor(en)).")
            st.rerun()
        except Exception as e:  # noqa: BLE001
            st.error(f"Speichern fehlgeschlagen: {type(e).__name__}: {e}")
    if cancel:
        st.rerun()


st.title(":material/inventory_2: Programme")
st.caption("Coaching-Angebote · Mentor-Pool-Zuweisung · Conversion-Snapshot")

df = load_programs()
if df.empty:
    render_empty_state("Keine Programme angelegt.", icon="🏆")
    st.stop()


# KPI-Strip
kcols = st.columns(4)
kcols[0].metric("Programme",   len(df))
kcols[1].metric("Mit Pool",    int(df["Mentoren"].apply(lambda x: bool(x)).sum()))
kcols[2].metric("Leads gesamt", int(df["Lead Count"].fillna(0).sum()))
kcols[3].metric("Converted",   int(df["Converted Kunden"].fillna(0).sum()))

st.markdown("---")


# Card-Grid (3 pro Reihe)
df = df.sort_values("Name").reset_index(drop=True)
for i in range(0, len(df), 3):
    cols = st.columns(3)
    for j, col in enumerate(cols):
        if i + j >= len(df):
            continue
        prog = df.iloc[i + j]
        with col:
            with st.container(border=True):
                st.markdown(f"### 🏆 {prog['Name']}")
                if prog.get("Category"):
                    st.caption(f"📂 {prog['Category']}")

                # Snapshot
                price = int(prog.get("Price (EUR)") or 0)
                lead_count = int(prog.get("Lead Count") or 0)
                converted  = int(prog.get("Converted Kunden") or 0)
                conv_rate  = (converted / lead_count * 100) if lead_count else 0.0

                mc = st.columns(2)
                mc[0].metric("€/Monat", f"{price}")
                mc[1].metric("Conv %", f"{conv_rate:.0f}", f"{converted} / {lead_count}")

                st.markdown("**👥 Mentor-Pool**")
                pool_names = prog.get("Mentor-Pool-Namen") or []
                if pool_names:
                    st.caption(" · ".join(pool_names))
                else:
                    st.caption("⚠️ Kein Pool — Auto-Routing nicht möglich")

                if can_edit:
                    if st.button(
                        "✏️ Pool bearbeiten",
                        key=f"edit_pool_btn_{prog['id']}",
                        use_container_width=True,
                    ):
                        edit_pool_modal(prog)
