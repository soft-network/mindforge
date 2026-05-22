"""Meine Leads — Pipeline-View (Sales).

Filter auf Setter == self_email. Edit-Modal limitiert: nur Status + Notiz.
Andere Lead-Operationen (Score, Mentor-Override) sind Admin-Rechte.
"""

from __future__ import annotations

import pathlib
import sys
from datetime import datetime

import pandas as pd
import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from components import confirm_save_buttons, render_empty_state  # noqa: E402
from integrations.airtable_helpers import load_leads, update_lead  # noqa: E402
from integrations.auth import require_tool_access  # noqa: E402
from lib.filters import DATE_RANGE_OPTIONS, filter_by_date_range  # noqa: E402
from lib.tz import TZ_BERLIN  # noqa: E402


user = require_tool_access("leads", "write")
my_email = user.get("email", "")

STATUS_OPTIONS = ["New", "Qualified", "Contacted", "Converted", "Lost"]


@st.dialog("Lead bearbeiten (Sales)", width="large")
def edit_lead_sales(lead: pd.Series) -> None:
    """Sales darf Status ändern + Notiz anhängen. Score, Mentor-Override = Admin."""
    st.subheader(f":material/edit: {lead['Name']}")
    st.caption(f"📧 {lead.get('E-Mail', '—')}  ·  Score `{int(lead.get('Lead Score') or 0)}`")

    cur_status = lead["Status"] if lead["Status"] in STATUS_OPTIONS else "New"
    new_status = st.selectbox(
        "Status",
        STATUS_OPTIONS,
        index=STATUS_OPTIONS.index(cur_status),
        key=f"sl_status_{lead['id']}",
    )

    notiz = st.text_area(
        "Notiz anfügen (optional)",
        placeholder="Wird mit Timestamp + deinem Namen vermerkt",
        key=f"sl_note_{lead['id']}",
    )

    if lead.get("Notizen"):
        with st.expander("Bisherige Notizen", expanded=False):
            st.text(lead["Notizen"])

    st.info(
        "💡 Hinweis: Lead → Kunde Convert macht man in **🎯 Strategiegespräche** "
        "(nach dem Call). Score und Mentor-Override sind Admin-Funktionen."
    )

    save, cancel = confirm_save_buttons(key_prefix=f"sl_modal_{lead['id']}")
    if save:
        patch: dict = {"Status": new_status}
        if notiz.strip():
            existing = lead.get("Notizen") or ""
            ts = datetime.now(TZ_BERLIN).strftime("%Y-%m-%d %H:%M")
            patch["Notizen"] = (existing + f"\n[{ts} · {user.get('name','Sales')}] {notiz.strip()}").strip()
        try:
            update_lead(lead["id"], patch)
            st.success("Aktualisiert.")
            st.rerun()
        except Exception as e:  # noqa: BLE001
            st.error(f"Speichern fehlgeschlagen: {type(e).__name__}: {e}")
    if cancel:
        st.rerun()


st.title(":material/view_kanban: Meine Pipeline")
st.caption(f"Nur Leads, die dir als Setter zugewiesen sind ({my_email}).")

df_all = load_leads()
mine = df_all[df_all["Setter"].str.lower() == my_email.lower()].reset_index(drop=True)

if mine.empty:
    render_empty_state(
        "Aktuell keine Leads dir als Setter zugeordnet. "
        "Admin muss dich auf Leads setzen.",
        icon="📋",
    )
    st.stop()


# Mini-KPI-Strip
status_counts = mine["Status"].value_counts()
kcols = st.columns(5)
for i, s in enumerate(STATUS_OPTIONS):
    kcols[i].metric(s, int(status_counts.get(s, 0)))


st.markdown("---")


# Filter
fcols = st.columns(4)
status_filter = fcols[0].selectbox("Status",   ["Alle"] + STATUS_OPTIONS)
date_range    = fcols[1].selectbox("Zeitraum", DATE_RANGE_OPTIONS)
min_score     = fcols[2].slider("Min Score", 0, 100, 0)
search        = fcols[3].text_input("Suche (Name/Email)", "")

filtered = mine.copy()
if status_filter != "Alle":
    filtered = filtered[filtered["Status"] == status_filter]
if min_score > 0:
    filtered = filtered[filtered["Lead Score"] >= min_score]
if search:
    mask = (
        filtered["Name"].str.contains(search, case=False, na=False)
        | filtered["E-Mail"].str.contains(search, case=False, na=False)
    )
    filtered = filtered[mask]
filtered = filter_by_date_range(filtered, range_name=date_range).reset_index(drop=True)
filtered = filtered.sort_values(["Lead Score", "Erstellt am"], ascending=[False, False]).reset_index(drop=True)


# Liste
st.write(f"**{len(filtered)} Leads** gefunden")
COLS = [0.4, 2.5, 2.5, 1, 1.4, 1.6, 0.8]
hcols = st.columns(COLS)
hcols[0].markdown("**🎯**")
hcols[1].markdown("**Name**")
hcols[2].markdown("**E-Mail**")
hcols[3].markdown("**Score**")
hcols[4].markdown("**Status**")
hcols[5].markdown("**Termin**")
hcols[6].markdown("**Edit**")
st.markdown("<hr style='margin-top:0; margin-bottom:0.5rem'>", unsafe_allow_html=True)

def tier_emoji(score: int) -> str:
    if score >= 85: return "🔥"
    if score >= 70: return "🌶️"
    if score >= 40: return "💧"
    return "❄️"

for _, lead in filtered.iterrows():
    cols = st.columns(COLS)
    score = int(lead.get("Lead Score") or 0)
    cols[0].markdown(tier_emoji(score))
    cols[1].markdown(f"**{lead['Name']}**")
    cols[2].caption(lead.get("E-Mail") or "—")
    cols[3].markdown(f"`{score}`")
    cols[4].markdown(f"`{lead.get('Status', 'New')}`")
    termin = lead.get("Termin am")
    if pd.notna(termin):
        cols[5].caption(termin.tz_convert(TZ_BERLIN).strftime("%d.%m. %H:%M"))
    else:
        cols[5].caption("—")
    if cols[6].button("✏️", key=f"sl_btn_{lead['id']}"):
        edit_lead_sales(lead)
