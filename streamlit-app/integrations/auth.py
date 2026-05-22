"""Auth — Email+Passwort-Login mit bcrypt + Airtable-User-Storage.

Hauptfunktionen:
    render_login_gate()  — zeigt Login-Form, blockt App bis Login OK
    current_user()       — gibt das gerade eingeloggte User-Dict zurück
    logout()             — Session-State löschen
    check_password()     — Legacy-Compat-Stub (alte ADMIN_PASSWORD-Gate, deprecated)

Login-Flow:
    1. User gibt Email + Passwort ein
    2. Lookup gegen Airtable.Benutzer (gecached, TTL 60s)
    3. Wenn nicht gefunden ABER Email == BOOTSTRAP_ADMIN_EMAIL → Bootstrap-Hauptadmin
       (für den allerersten Login bevor die Tabelle befüllt ist)
    4. Bei Erfolg: User-Dict in st.session_state["current_user"]
    5. Letzte-Anmeldung-Timestamp in Airtable updaten

Session-Daten:
    st.session_state["current_user"] = {
        "id":           str | None,       # Airtable rec-id (None bei Bootstrap)
        "name":         str,
        "email":        str,
        "rolle":        "Hauptadmin" | "Sales" | "Mentor",
        "mentor_id":    str | None,       # nur wenn Rolle=Mentor
        "is_bootstrap": bool,             # nur True wenn Bootstrap-Admin
    }
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional, TypedDict

import streamlit as st
from pyairtable import Api

from lib.auth_security import verify_password
from lib.tz import TZ_BERLIN


# -----------------------------------------------------------------------------
# Konfig
# -----------------------------------------------------------------------------

VALID_ROLES = ("Hauptadmin", "Sales", "Mentor")


class UserDict(TypedDict, total=False):
    id:           Optional[str]
    name:         str
    email:        str
    rolle:        str
    mentor_id:    Optional[str]
    is_bootstrap: bool


def _bootstrap_admin_email() -> Optional[str]:
    """Bootstrap-Admin-Email aus secrets oder env — für den allerersten Login."""
    val = st.secrets.get("BOOTSTRAP_ADMIN_EMAIL") or os.environ.get("BOOTSTRAP_ADMIN_EMAIL")
    return val.strip().lower() if val else None


def _bootstrap_admin_password() -> Optional[str]:
    """Bootstrap-Admin-Passwort (plaintext, nur für Initial-Login)."""
    return st.secrets.get("BOOTSTRAP_ADMIN_PASSWORD") or os.environ.get("BOOTSTRAP_ADMIN_PASSWORD")


# -----------------------------------------------------------------------------
# Airtable-Lookups (eigene API-Instanz, da der airtable_helpers-Cache
# evt. st.secrets noch nicht initialisiert hat)
# -----------------------------------------------------------------------------

@st.cache_resource
def _api() -> Api:
    token = st.secrets.get("AIRTABLE_API_TOKEN") or os.environ.get("AIRTABLE_API_TOKEN")
    if not token:
        st.error("AIRTABLE_API_TOKEN fehlt. Siehe .streamlit/secrets.toml")
        st.stop()
    return Api(token)


def _base_id() -> str:
    base = st.secrets.get("AIRTABLE_BASE_ID") or os.environ.get("AIRTABLE_BASE_ID")
    if not base:
        st.error("AIRTABLE_BASE_ID fehlt.")
        st.stop()
    return base


@st.cache_data(ttl=60)
def _load_users() -> list[dict]:
    """Alle User aus Airtable.Benutzer — gecached für 60s.

    Nach update_last_login() oder User-Anlage muss _load_users.clear() gerufen
    werden.
    """
    return _api().table(_base_id(), "Benutzer").all()


def find_user_by_email(email: str) -> Optional[dict]:
    """Findet den Benutzer-Record per Email (case-insensitive)."""
    email_lower = email.strip().lower()
    for rec in _load_users():
        rec_email = (rec["fields"].get("E-Mail") or "").strip().lower()
        if rec_email == email_lower:
            return rec
    return None


def _airtable_record_to_userdict(rec: dict) -> UserDict:
    f = rec["fields"]
    mentor_link = f.get("Mentor-Link", [])
    return UserDict(
        id           = rec["id"],
        name         = f.get("Name", ""),
        email        = (f.get("E-Mail") or "").strip().lower(),
        rolle        = f.get("Rolle", ""),
        mentor_id    = mentor_link[0] if mentor_link else None,
        is_bootstrap = False,
    )


def _update_last_login(user_id: str) -> None:
    """Setzt Letzte Anmeldung — best-effort, schlägt nicht laut fehl."""
    try:
        _api().table(_base_id(), "Benutzer").update(
            user_id,
            {"Letzte Anmeldung": datetime.now(TZ_BERLIN).isoformat()},
        )
        _load_users.clear()
    except Exception:  # noqa: BLE001
        pass  # Login funktioniert auch ohne LastSeen-Update


# -----------------------------------------------------------------------------
# Login-Flow
# -----------------------------------------------------------------------------

def _try_login(email: str, password: str) -> tuple[bool, Optional[UserDict], str]:
    """Versucht Login. Returns (success, user_dict, error_message).

    Reihenfolge:
        1. Match gegen Airtable.Benutzer (Email + Hash-Verify + Status=Active)
        2. Match gegen Bootstrap-Admin (Email + Plain-Compare aus secrets)
    """
    email = email.strip().lower()

    if not email or not password:
        return False, None, "Email und Passwort sind Pflichtfelder."

    # 1) Airtable-Lookup
    rec = find_user_by_email(email)
    if rec is not None:
        f = rec["fields"]
        if f.get("Status") != "Active":
            return False, None, "Dein Account ist deaktiviert. Bitte beim Admin melden."

        hashed = f.get("Passwort-Hash", "")
        if verify_password(password, hashed):
            user = _airtable_record_to_userdict(rec)
            _update_last_login(rec["id"])
            return True, user, ""
        # falscher Pwd — wir fallen DURCH zum Bootstrap-Check (falls Bootstrap-Email == diese)

    # 2) Bootstrap-Admin (für Initial-Login bevor die Tabelle befüllt ist)
    bootstrap_email = _bootstrap_admin_email()
    bootstrap_pwd   = _bootstrap_admin_password()
    if (
        bootstrap_email and bootstrap_pwd
        and email == bootstrap_email
        and password == bootstrap_pwd
    ):
        return True, UserDict(
            id           = None,
            name         = "Bootstrap-Hauptadmin",
            email        = bootstrap_email,
            rolle        = "Hauptadmin",
            mentor_id    = None,
            is_bootstrap = True,
        ), ""

    return False, None, "Email oder Passwort falsch."


def render_login_gate() -> bool:
    """Zeigt Login-Form falls noch nicht eingeloggt. Returns True wenn Login OK.

    Verwendung in app.py:
        if not render_login_gate():
            st.stop()
    """
    if "current_user" in st.session_state:
        return True

    # Login-Form
    with st.container():
        st.title("🔥 MindForge Coach")
        st.caption("Bitte mit deiner Email und Passwort einloggen.")

        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("E-Mail", autocomplete="email")
            password = st.text_input("Passwort", type="password", autocomplete="current-password")
            submit = st.form_submit_button("Einloggen", type="primary", use_container_width=True)

        if submit:
            ok, user, err = _try_login(email, password)
            if ok and user is not None:
                st.session_state["current_user"] = user
                st.rerun()
            else:
                st.error(err)

        st.caption(
            "Kein Zugang? → Hauptadmin anfragen. "
            "Passwort vergessen? → Hauptadmin setzt es zurück."
        )

    return False


# -----------------------------------------------------------------------------
# Public Helpers — werden von Pages konsumiert
# -----------------------------------------------------------------------------

def current_user() -> Optional[UserDict]:
    """Gibt den gerade eingeloggten User zurück, oder None."""
    return st.session_state.get("current_user")


def logout() -> None:
    """Session-Daten löschen + Rerun."""
    keys_to_clear = ["current_user", "authenticated"]
    for k in keys_to_clear:
        st.session_state.pop(k, None)
    _load_users.clear()
    st.rerun()


def render_sidebar_user_footer() -> None:
    """Avatar + Name + Rolle + Logout-Button in der Sidebar — wird von app.py
    nach der st.navigation gerendert.
    """
    user = current_user()
    if not user:
        return

    initials = "".join(part[0].upper() for part in (user.get("name") or "?").split()[:2])
    rolle    = user.get("rolle") or "—"
    name     = user.get("name") or "—"

    # Custom-Avatar via HTML (Streamlit hat keine native Avatar-Komponente)
    color_by_role = {
        "Hauptadmin": "#fee2e2",  # rot-pastell
        "Sales":      "#dbeafe",  # blau-pastell
        "Mentor":     "#dcfce7",  # grün-pastell
    }
    text_color_by_role = {
        "Hauptadmin": "#b91c1c",
        "Sales":      "#1d4ed8",
        "Mentor":     "#15803d",
    }
    bg = color_by_role.get(rolle, "#e5e7eb")
    fg = text_color_by_role.get(rolle, "#374151")

    st.sidebar.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:8px;
                    padding:8px 4px; margin-top:12px;
                    border-top:1px solid #e5e7eb;">
          <div style="width:32px; height:32px; border-radius:50%;
                      background:{bg}; color:{fg};
                      display:flex; align-items:center; justify-content:center;
                      font-size:12px; font-weight:600;">{initials}</div>
          <div style="flex:1; min-width:0;">
            <div style="font-size:13px; font-weight:500;
                        white-space:nowrap; overflow:hidden;
                        text-overflow:ellipsis;">{name}</div>
            <div style="font-size:11px; color:#6b7280;">{rolle}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.sidebar.button("Logout", use_container_width=True, key="sidebar_logout_btn"):
        logout()


# -----------------------------------------------------------------------------
# Legacy-Compat — alte Pages die noch `check_password()` rufen
# -----------------------------------------------------------------------------

def check_password() -> bool:
    """Legacy-Wrapper. Neuer Pfad ist render_login_gate() in app.py.

    Wenn current_user existiert → True. Sonst Login-Gate zeigen.
    """
    if current_user():
        return True
    return render_login_gate()
