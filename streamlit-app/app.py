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

import streamlit as st

from integrations.auth import check_password
from integrations import google_calendar as gcal


# -----------------------------------------------------------------------------
# Globale Page-Config (gilt für alle Pages über st.navigation)
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="MindForge Coach",
    page_icon="assets/logo_icon.svg",
    layout="wide",
    initial_sidebar_state="expanded",
)


# -----------------------------------------------------------------------------
# Logo oben in der Sidebar (statt Streamlit-Default)
# -----------------------------------------------------------------------------

st.logo(
    image="assets/logo.svg",          # Wide-Version mit "MindForge"-Schriftzug
    icon_image="assets/logo_icon.svg",  # Kompakt-Icon für collapsed sidebar
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
# Passwort-Gate (optional, abhängig von ADMIN_PASSWORD in secrets.toml)
# -----------------------------------------------------------------------------

if not check_password():
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
# Navigation — Pages explizit definiert
# Dashboard ist die Startseite (default=True).
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

pg = st.navigation([
    dashboard_page,
    leads_page,
    setter_page,
    programme_page,
])


# -----------------------------------------------------------------------------
# Page rendern (lädt die aktuell aktive Page)
# -----------------------------------------------------------------------------

pg.run()
