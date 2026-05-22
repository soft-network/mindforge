"""Benutzer-Verwaltung — Hauptadmin-only.

User-Lifecycle:
    - Liste aller User mit Filter (Rolle, Status, Suche)
    - + Neuer Benutzer Modal (Name, Email, Passwort, Rolle, Mentor-Link)
    - Edit pro User: Name/Rolle/Status ändern, Passwort zurücksetzen
    - Mentor-Link wird Pflicht wenn Rolle=Mentor

Wichtig: Passwörter werden hier IMMER als plaintext eingegeben, das Hashen
passiert in airtable_helpers.create_benutzer/reset_user_password vor dem
Airtable-Write. Im DataFrame ist der Hash NIE sichtbar.
"""

from __future__ import annotations

import pathlib
import sys

import pandas as pd
import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from components import confirm_save_buttons, render_empty_state  # noqa: E402
from integrations.airtable_helpers import (  # noqa: E402
    create_benutzer,
    load_benutzer,
    load_mentor_lookup,
    reset_user_password,
    update_benutzer,
)
from integrations.auth import current_user, require_tool_access  # noqa: E402


# Permission-Gate — nur Hauptadmin darf hier rein
require_tool_access("benutzer", "write")

ROLE_OPTIONS   = ["Hauptadmin", "Sales", "Mentor"]
STATUS_OPTIONS = ["Active", "Inactive"]
MENTOR_NONE    = "— (kein Mentor)"


# -----------------------------------------------------------------------------
# Modal — Neuer Benutzer
# -----------------------------------------------------------------------------

@st.dialog("Neuer Benutzer", width="large")
def new_user_modal() -> None:
    """Modal-Form für die Anlage eines neuen Users."""
    st.caption("Felder mit * sind Pflicht. Bei Rolle 'Mentor' muss ein Mentor-Link gewählt werden.")

    with st.form("new_user_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        new_name  = col1.text_input("Name *", placeholder="z.B. Max Mustermann")
        new_email = col2.text_input("E-Mail *", placeholder="max@firma.de")

        col3, col4 = st.columns(2)
        new_role  = col3.selectbox("Rolle *", ROLE_OPTIONS, index=1)  # Default: Sales

        # Mentor-Lookup für Selectbox (nur relevant wenn Rolle=Mentor)
        mentor_lookup = load_mentor_lookup()
        mentor_options = [MENTOR_NONE] + sorted(mentor_lookup.values())
        new_mentor_name = col4.selectbox(
            "Mentor-Link",
            mentor_options,
            help="Pflicht wenn Rolle = Mentor. Verknüpft den Login mit dem Mentor-Record.",
        )

        new_password = st.text_input(
            "Initial-Passwort *",
            type="password",
            help="Wird gehashed gespeichert. Gib dem User mit, er soll es ändern.",
        )

        submit = st.form_submit_button(
            "💾 Anlegen", type="primary", use_container_width=True,
        )

    if submit:
        # Mentor-Name → mentor_id auflösen
        mentor_id = None
        if new_mentor_name != MENTOR_NONE:
            mentor_id = next(
                (mid for mid, n in mentor_lookup.items() if n == new_mentor_name),
                None,
            )

        try:
            cu = current_user()
            create_benutzer(
                name=new_name,
                email=new_email,
                password=new_password,
                rolle=new_role,
                mentor_id=mentor_id,
                angelegt_von=cu.get("email") if cu else None,
            )
            st.success(f"✅ Benutzer {new_email} angelegt.")
            st.rerun()
        except (ValueError, RuntimeError) as e:
            st.error(f"{e}")
        except Exception as e:  # noqa: BLE001
            st.error(f"Unerwarteter Fehler: {type(e).__name__}: {e}")


# -----------------------------------------------------------------------------
# Modal — Benutzer bearbeiten
# -----------------------------------------------------------------------------

@st.dialog("Benutzer bearbeiten", width="large")
def edit_user_modal(user: pd.Series) -> None:
    """Bearbeitet Stamm-Daten + optional Passwort-Reset."""
    st.subheader(f"✏️ {user['Name']}")
    st.caption(f"📧 {user['E-Mail']}")
    st.markdown("---")

    col1, col2 = st.columns(2)
    new_name = col1.text_input(
        "Name", value=user["Name"], key=f"u_name_{user['id']}",
    )

    cur_role = user["Rolle"] if user["Rolle"] in ROLE_OPTIONS else "Sales"
    new_role = col2.selectbox(
        "Rolle",
        ROLE_OPTIONS,
        index=ROLE_OPTIONS.index(cur_role),
        key=f"u_role_{user['id']}",
    )

    col3, col4 = st.columns(2)
    cur_status = user["Status"] if user["Status"] in STATUS_OPTIONS else "Active"
    new_status = col3.selectbox(
        "Status",
        STATUS_OPTIONS,
        index=STATUS_OPTIONS.index(cur_status),
        key=f"u_status_{user['id']}",
    )

    mentor_lookup  = load_mentor_lookup()
    mentor_options = [MENTOR_NONE] + sorted(mentor_lookup.values())
    cur_mentor_name = user.get("Mentor Name") or MENTOR_NONE
    if cur_mentor_name not in mentor_options:
        cur_mentor_name = MENTOR_NONE
    new_mentor_name = col4.selectbox(
        "Mentor-Link",
        mentor_options,
        index=mentor_options.index(cur_mentor_name),
        key=f"u_mentor_{user['id']}",
    )

    st.markdown("---")
    with st.expander("🔐 Passwort zurücksetzen (optional)", expanded=False):
        st.caption("Lass leer um das aktuelle Passwort zu behalten.")
        reset_pwd = st.text_input(
            "Neues Passwort", type="password", key=f"u_pwd_{user['id']}",
        )

    st.markdown("---")
    save, cancel = confirm_save_buttons(key_prefix=f"u_modal_{user['id']}")

    if save:
        # Mentor-Name → mentor_id auflösen
        mentor_id = None
        if new_mentor_name != MENTOR_NONE:
            mentor_id = next(
                (mid for mid, n in mentor_lookup.items() if n == new_mentor_name),
                None,
            )

        # Validierung: Mentor-Rolle ohne Link blockieren
        if new_role == "Mentor" and not mentor_id:
            st.error("Für Rolle 'Mentor' muss ein Mentor-Link gewählt werden.")
            return

        patch: dict = {
            "Name":        new_name.strip(),
            "Rolle":       new_role,
            "Status":      new_status,
            "Mentor-Link": [mentor_id] if mentor_id else [],
        }
        try:
            update_benutzer(user["id"], patch)
            if reset_pwd.strip():
                reset_user_password(user["id"], reset_pwd.strip())
                st.success("Aktualisiert + Passwort zurückgesetzt.")
            else:
                st.success("Aktualisiert.")
            st.rerun()
        except (ValueError, RuntimeError) as e:
            st.error(f"{e}")
        except Exception as e:  # noqa: BLE001
            st.error(f"Speichern fehlgeschlagen: {type(e).__name__}: {e}")

    if cancel:
        st.rerun()


# -----------------------------------------------------------------------------
# Hilfsfunktion: Rolle-Badge
# -----------------------------------------------------------------------------

def role_badge(rolle: str) -> str:
    return {
        "Hauptadmin": "🔴",
        "Sales":      "🔵",
        "Mentor":     "🟢",
    }.get(rolle, "⚫")


def status_badge(status: str) -> str:
    return "🟢" if status == "Active" else "⚫"


# -----------------------------------------------------------------------------
# Page
# -----------------------------------------------------------------------------

df = load_benutzer()

st.title(f"👤 Benutzer ({len(df)})")
st.caption("User-Lifecycle · Rollen · Status · Passwort-Reset")

col_a, col_b = st.columns([4, 1])
col_a.markdown("Verwalte hier alle Login-Konten und ihre Rollen.")
if col_b.button("➕ Neuer Benutzer", type="primary", use_container_width=True):
    new_user_modal()

if df.empty:
    render_empty_state("Noch keine Benutzer angelegt.", icon="👤")
    st.stop()


# ----- Filter-Row -------------------------------------------------------------

fcols = st.columns(4)
role_filter   = fcols[0].selectbox("Rolle",   ["Alle"] + ROLE_OPTIONS)
status_filter = fcols[1].selectbox("Status",  ["Alle"] + STATUS_OPTIONS)
search        = fcols[2].text_input("Suche (Name/Email)", "")
fcols[3].markdown(f"<div style='padding-top:1.8rem'>{len(df)} Benutzer gesamt</div>",
                  unsafe_allow_html=True)

filtered = df.copy()
if role_filter != "Alle":
    filtered = filtered[filtered["Rolle"] == role_filter]
if status_filter != "Alle":
    filtered = filtered[filtered["Status"] == status_filter]
if search:
    mask = (
        filtered["Name"].str.contains(search, case=False, na=False)
        | filtered["E-Mail"].str.contains(search, case=False, na=False)
    )
    filtered = filtered[mask]
filtered = filtered.sort_values(["Status", "Rolle", "Name"]).reset_index(drop=True)


# ----- Liste ------------------------------------------------------------------

COLS = [0.4, 2.5, 3, 1.4, 1, 2, 1.6, 0.8]
hcols = st.columns(COLS)
hcols[0].markdown("**●**")
hcols[1].markdown("**Name**")
hcols[2].markdown("**E-Mail**")
hcols[3].markdown("**Rolle**")
hcols[4].markdown("**Status**")
hcols[5].markdown("**Mentor**")
hcols[6].markdown("**Letzte Anm.**")
hcols[7].markdown("**Edit**")
st.markdown(
    "<hr style='margin-top:0; margin-bottom:0.5rem'>",
    unsafe_allow_html=True,
)

for _, user in filtered.iterrows():
    cols = st.columns(COLS)
    cols[0].markdown(role_badge(user["Rolle"]))
    cols[1].markdown(f"**{user['Name'] or '—'}**")
    cols[2].caption(user["E-Mail"] or "—")
    cols[3].markdown(f"`{user['Rolle']}`")
    cols[4].markdown(f"{status_badge(user['Status'])} {user['Status']}")
    cols[5].caption(user.get("Mentor Name") or "—")

    last = user.get("Letzte Anmeldung")
    if pd.notna(last):
        cols[6].caption(last.strftime("%d.%m.%y %H:%M"))
    else:
        cols[6].caption("noch nie")

    if cols[7].button("✏️", key=f"edit_user_btn_{user['id']}", help="Bearbeiten"):
        edit_user_modal(user)
