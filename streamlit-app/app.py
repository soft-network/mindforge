"""MindForge Coach Admin — Navigation Hub.

app.py ist der Entry-Point. Hier wird:
    - die globale Page-Config gesetzt (Tab-Title, Layout, etc.)
    - das MindForge-Logo in der Sidebar gerendert
    - der Passwort-Gate ausgeführt
    - der Google-OAuth-Callback abgefangen (wenn ?code=... in der URL)
    - die Multi-Page-Navigation via st.navigation() definiert
    - die ausgewählte Page über pg.run() gerendert

Pages liegen in pages/* und werden über st.navigation() explizit registriert.
Die Auto-Sidebar-Discovery ist via .streamlit/config.toml deaktiviert.

Lokal starten:
    streamlit run app.py

Cloud Run Deployment: siehe ../08-gcp-deployment.md
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from integrations.auth import (
    current_user,
    render_login_gate,
    render_sidebar_user_footer,
)
from integrations import google_calendar as gcal


# -----------------------------------------------------------------------------
# Assets-Pfade — absolute relativ zu app.py (funktioniert lokal UND auf
# Streamlit Cloud, wo cwd != streamlit-app/).
# -----------------------------------------------------------------------------

APP_DIR = Path(__file__).resolve().parent
LOGO_WIDE = str(APP_DIR / "assets" / "logo.svg")
LOGO_ICON = str(APP_DIR / "assets" / "logo_icon.svg")


# -----------------------------------------------------------------------------
# Globale Page-Config (gilt für alle Pages über st.navigation)
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="MindForge Coach",
    page_icon=LOGO_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------------------------------------------------------
# Logo oben in der Sidebar (statt Streamlit-Default)
# -----------------------------------------------------------------------------

st.logo(
    image=LOGO_WIDE,          # Wide-Version mit "MindForge"-Schriftzug
    icon_image=LOGO_ICON,     # Kompakt-Icon für collapsed sidebar
)

# CSS-Override für größere Logo-Darstellung
# (st.logo size-Parameter kommt erst in Streamlit 1.45+, wir sind auf 1.40)
st.markdown(
    """
    <style>
    [data-testid="stSidebarHeader"] img,
    [data-testid="stLogo"] {
        height: 3.2rem !important;
        max-height: 3.2rem !important;
        max-width: 100% !important;
        margin: 0.5rem 0 !important;
    }
    [data-testid="stSidebarHeader"] {
        padding-bottom: 0.5rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Login-Gate — Email + Passwort gegen Airtable.Benutzer (bcrypt)
# Bootstrap-Hauptadmin aus secrets.toml für den allerersten Login.
# -----------------------------------------------------------------------------

if not render_login_gate():
    st.stop()


# -----------------------------------------------------------------------------
# Google-OAuth-Callback abfangen — Google leitet zu /?code=...&state=...
# zurück. Code austauschen, Token in Session.
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
# Navigation — Pages pro Rolle unterschiedlich gruppiert
#
# Welle 2 (jetzt) zeigt eine bewusste ÜBERGANGS-Sicht: bestehende Pages
# werden auf die Rollen verteilt, basierend auf der Permission-Matrix.
# Rollen-spezifische Pages (Mentor-Cockpit, Sales-Strategiegespräche etc.)
# kommen in Welle 4+5 und werden dann hier dazugesteckt.
# -----------------------------------------------------------------------------

dashboard_page = st.Page(
    "pages/1_Dashboard.py", title="Dashboard", icon="📊", default=True,
)
leads_page = st.Page(
    "pages/2_Leads.py", title="Leads", icon="📋",
)
setter_page = st.Page(
    "pages/3_Setter_Daily.py", title="Setter Daily", icon="📞",
)
programme_page = st.Page(
    "pages/4_Programme.py", title="Programme", icon="📦",
)
mentoren_page = st.Page(
    "pages/5_Mentoren.py", title="Mentoren", icon="👥",
)
cs_page = st.Page(
    "pages/6_Customer_Success.py", title="Customer Success", icon="🤝",
)
benutzer_page = st.Page(
    "pages/7_Benutzer.py", title="Benutzer", icon="👤",
)
pipeline_page = st.Page(
    "pages/admin_pipeline.py", title="Pipeline", icon="📊",
)
performance_page = st.Page(
    "pages/admin_performance.py", title="Performance", icon="🏆",
)


# Rolle aus dem eingeloggten User auslesen — Login-Gate hat schon geprüft
# dass current_user existiert.
_role = (current_user() or {}).get("rolle", "")

if _role == "Hauptadmin":
    pg = st.navigation({
        "📊 Übersicht":       [dashboard_page, pipeline_page],
        "⚙️ Administration":  [leads_page, mentoren_page, cs_page, programme_page],
        "🏆 Analytics":       [performance_page],
        "📞 Monitoring":      [setter_page],
        "🔧 System":          [benutzer_page],
    })

elif _role == "Sales":
    sales_cockpit_page = st.Page(
        "pages/sales_cockpit.py", title="Cockpit", icon="📊", default=True,
    )
    sales_strategie_page = st.Page(
        "pages/sales_strategiegespraeche.py", title="Strategiegespräche", icon="🎯",
    )
    sales_meine_leads_page = st.Page(
        "pages/sales_meine_leads.py", title="Meine Pipeline", icon="📋",
    )
    sales_conversions_page = st.Page(
        "pages/sales_conversions.py", title="Meine Conversions", icon="🤝",
    )
    pg = st.navigation({
        "📊 Mein Tag":       [sales_cockpit_page, setter_page, sales_strategie_page],
        "📋 Meine Leads":    [sales_meine_leads_page, sales_conversions_page],
        "ℹ️ Info":            [programme_page, mentoren_page],
    })

elif _role == "Mentor":
    mentor_cockpit_page = st.Page(
        "pages/mentor_cockpit.py", title="Cockpit", icon="🎯", default=True,
    )
    mentor_mentees_page = st.Page(
        "pages/mentor_mentees.py", title="Meine Mentees", icon="🧑‍🎓",
    )
    mentor_sessions_page = st.Page(
        "pages/mentor_sessions.py", title="Meine Sessions", icon="📅",
    )
    mentor_aufgaben_page = st.Page(
        "pages/mentor_aufgaben.py", title="Aufgaben", icon="✅",
    )
    mentor_engagements_page = st.Page(
        "pages/mentor_engagements.py", title="Engagements", icon="🤝",
    )
    mentor_profil_page = st.Page(
        "pages/mentor_profil.py", title="Mein Profil", icon="👤",
    )
    pg = st.navigation({
        "🎯 Mein Tag":        [mentor_cockpit_page, mentor_sessions_page, mentor_aufgaben_page],
        "🧑‍🎓 Meine Mentees": [mentor_mentees_page, mentor_engagements_page],
        "👤 Mein Profil":     [mentor_profil_page],
        "ℹ️ Info":             [programme_page],
    })

else:
    # Unbekannte Rolle → kein Zugriff (sollte nicht passieren da Login-Check)
    st.error(f"Unbekannte Rolle: {_role!r}. Bitte beim Admin melden.")
    st.stop()


# -----------------------------------------------------------------------------
# Sidebar-User-Footer (Avatar · Name · Rolle · Logout)
# Nach st.navigation() gerendert, erscheint unten in der Sidebar.
# -----------------------------------------------------------------------------

render_sidebar_user_footer()


# -----------------------------------------------------------------------------
# Page rendern (lädt die aktuell aktive Page)
# -----------------------------------------------------------------------------

pg.run()
