"""Mein Profil — Read-only Mentor-Stamm-Daten.

Mentor sieht seine eigenen Stamm-Daten, kann sie aber nicht editieren —
Änderungen über den Admin-Kontakt.
"""

from __future__ import annotations

import pathlib
import sys

import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from integrations.airtable_helpers import get_mentor_record  # noqa: E402
from integrations.auth import current_user, require_tool_access  # noqa: E402


user = require_tool_access("profil", "read")
mentor_id = user.get("mentor_id")
if not mentor_id:
    st.error("Account ohne Mentor-Link. Bitte beim Admin melden.")
    st.stop()


st.title("👤 Mein Profil")
st.caption("Read-only — Änderungen über den Admin-Kontakt.")

rec = get_mentor_record(mentor_id)
if not rec:
    st.error("Mentor-Record konnte nicht geladen werden.")
    st.stop()

f = rec["fields"]
spez = f.get("Spezialisierung") or []
spez_text = ", ".join(spez) if isinstance(spez, list) else "—"
status = f.get("Status", "—")
status_emoji = {"Active": "🟢", "On Leave": "🟡", "Inactive": "⚫"}.get(status, "❔")

with st.container(border=True):
    cols = st.columns([1.5, 4])
    # Initialen-Avatar
    initials = "".join(part[0].upper() for part in (f.get("Name") or "?").split()[:2])
    cols[0].markdown(
        f"""
        <div style="width:96px; height:96px; border-radius:50%;
                    background:#dcfce7; color:#15803d;
                    display:flex; align-items:center; justify-content:center;
                    font-size:36px; font-weight:600; margin: 8px auto;">{initials}</div>
        """,
        unsafe_allow_html=True,
    )
    cols[1].markdown(f"### {f.get('Name', '—')}")
    cols[1].markdown(f"**E-Mail:** {f.get('E-Mail') or '—'}")
    cols[1].markdown(f"**Login-Email:** `{user.get('email')}`")
    cols[1].markdown(f"**Stadt:** {f.get('Stadt') or '—'}")

st.markdown("---")

icols = st.columns(3)
icols[0].metric("Status",          f"{status_emoji} {status}")
icols[1].metric("Kapazität/Woche", f.get("Kapazität pro Woche", 0))
icols[2].metric("Spezialisierung",  spez_text if spez_text != "—" else "—")

st.markdown("---")
st.info(
    "💡 Wenn sich deine Stamm-Daten ändern (E-Mail, Stadt, Kapazität, "
    "Spezialisierung), schreibe deinem Admin-Kontakt — er pflegt das im "
    "Hintergrund."
)
