"""Lovelifepassport — Entry-Point.

Setup:
    1. Globale Page-Config (Title, Icon, Layout)
    2. Login-Gate (Email + Passwort gegen Airtable.Benutzer)
    3. Google-OAuth-Callback abfangen (für Setter-Daily-Calendar)
    4. st.navigation() registriert alle Pages für Streamlit-Routing
    5. Custom-Sidebar via sidebar.render_sidebar() (Brand · Material-Icons · User-Footer)
    6. Die Default-Streamlit-Nav wird per CSS ausgeblendet — Routing macht
       aber weiterhin st.navigation()

Lokal starten:
    uv run streamlit run app.py

Cloud Deployment: siehe README.md
"""

from __future__ import annotations

import streamlit as st

from integrations import google_calendar as gcal
from integrations.auth import current_user, render_login_gate
from sidebar import render_sidebar
from sidebar_helpers import load_material_icons_font


# -----------------------------------------------------------------------------
# Globale Page-Config — page_icon = Material-Symbol "favorite" (rotes Herz)
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Lovelifepassport",
    page_icon=":material/favorite:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Material-Icons-Font einmal global laden — alle Pages und Sidebar profitieren
load_material_icons_font()


# -----------------------------------------------------------------------------
# Login-Gate (Email + Passwort gegen Airtable.Benutzer, bcrypt-Hash)
# -----------------------------------------------------------------------------

if not render_login_gate():
    st.stop()


# Rolle + Name aus current_user nach st.session_state spiegeln — sodass die
# Custom-Sidebar beide Quellen kennt (Test-Mode kann session_state vorher setzen)
_user = current_user() or {}
if _user:
    st.session_state.setdefault("user_role", _user.get("rolle", ""))
    st.session_state.setdefault("user_name", _user.get("name", ""))


# -----------------------------------------------------------------------------
# Google-OAuth-Callback (wenn ?code=... in URL nach Google-Login zurückkommt)
# -----------------------------------------------------------------------------

if "code" in st.query_params:
    if gcal.handle_oauth_callback():
        st.balloons()
        st.toast(
            f"✅ Eingeloggt als {gcal.current_user_email()}",
            icon="🔑",
        )
    else:
        st.error("OAuth-Login fehlgeschlagen. Schau ins Terminal für Details.")


# -----------------------------------------------------------------------------
# Page-Registry für st.navigation() — wir bestimmen die Default-Page (Landing)
# je nach Rolle: Hauptadmin → Dashboard, Sales → Sales-Cockpit, Mentor → Cockpit
# -----------------------------------------------------------------------------

_role = (current_user() or {}).get("rolle", "")
_default_for_role: dict[str, str] = {
    "Hauptadmin": "pages/1_Dashboard.py",
    "Sales":      "pages/sales_cockpit.py",
    "Mentor":     "pages/mentor_cockpit.py",
}
_default_path = _default_for_role.get(_role, "pages/1_Dashboard.py")


def _page(path: str, title: str, icon: str) -> "st.Page":
    """st.Page mit default=True nur für die rollenspezifische Landing-Page."""
    return st.Page(path, title=title, icon=icon, default=(path == _default_path))


pg = st.navigation([
    # Admin
    _page("pages/1_Dashboard.py",        "Dashboard",         "📊"),
    _page("pages/2_Leads.py",            "Leads",             "📋"),
    _page("pages/3_Setter_Daily.py",     "Setter Daily",      "📞"),
    _page("pages/4_Programme.py",        "Programme",         "📦"),
    _page("pages/5_Mentoren.py",         "Mentoren",          "👥"),
    _page("pages/6_Customer_Success.py", "Customer Success",  "🤝"),
    _page("pages/7_Benutzer.py",         "Benutzer",          "👤"),
    _page("pages/admin_pipeline.py",     "Pipeline",          "📊"),
    _page("pages/admin_performance.py",  "Performance",       "🏆"),
    _page("pages/mentor_analytics.py",   "Mentor-Analytics",  "📈"),
    _page("pages/cs_analytics.py",       "CS-Analytics",      "💗"),
    # Sales
    _page("pages/sales_cockpit.py",              "Sales-Cockpit",       "📊"),
    _page("pages/sales_strategiegespraeche.py",  "Strategiegespräche",  "🎯"),
    _page("pages/sales_meine_leads.py",          "Meine Pipeline",      "📋"),
    _page("pages/sales_conversions.py",          "Meine Conversions",   "🤝"),
    # Mentor
    _page("pages/mentor_cockpit.py",     "Mentor-Cockpit",  "🎯"),
    _page("pages/mentor_mentees.py",     "Meine Mentees",   "🧑‍🎓"),
    _page("pages/mentor_sessions.py",    "Meine Sessions",  "📅"),
    _page("pages/mentor_aufgaben.py",    "Aufgaben",        "✅"),
    _page("pages/mentor_engagements.py", "Engagements",     "🤝"),
    _page("pages/mentor_profil.py",      "Mein Profil",     "👤"),
])


# -----------------------------------------------------------------------------
# Custom-Sidebar (Brand · Sektionen mit Material-Icons · User-Footer)
# -----------------------------------------------------------------------------

render_sidebar()


# -----------------------------------------------------------------------------
# Page rendern
# -----------------------------------------------------------------------------

pg.run()
