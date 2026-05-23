"""Rollenbasierte Sidebar mit Material-Symbols + st.page_link.

Public:
    render_sidebar()  — zeichnet je nach Rolle des aktuellen Users die richtige
                        Sidebar. Im app.py einmal nach dem Login-Gate aufrufen.

Private:
    _render_sales_sidebar()
    _render_mentor_sidebar()
    _render_admin_sidebar()
    _page_link()      — sicheres Wrapper um st.page_link(), das bei fehlender
                        Page nicht crasht.

Quelle der Rolle:
    1. st.session_state['user_role']    (Test-/Dev-Mode-Override)
    2. integrations.auth.current_user()['rolle']    (Production)
Erste hat Priorität.
"""

from __future__ import annotations

import streamlit as st

from sidebar_helpers import (
    brand_header,
    hide_default_streamlit_nav,
    load_material_icons_font,
    normalize_role,
    section_header,
    user_avatar,
)


# -----------------------------------------------------------------------------
# Internes — sicheres page_link mit Fallback
# -----------------------------------------------------------------------------

def _page_link(page: str, label: str, icon: str) -> None:
    """st.page_link mit Try-Except — fehlende Pages werden still übersprungen.

    Args:
        page:  Relativer Pfad zur Page (z. B. 'pages/2_Leads.py')
        label: Anzeigename im Nav-Item
        icon:  Material-Symbol-Name (ohne ':material/:'-Prefix)
    """
    try:
        st.sidebar.page_link(page, label=label, icon=f":material/{icon}:")
    except Exception:
        # Page existiert (noch) nicht oder ist nicht im Page-Registry —
        # elegantes Skip, kein Crash der ganzen Sidebar.
        pass


# -----------------------------------------------------------------------------
# Rolle-Resolver
# -----------------------------------------------------------------------------

def _resolve_user() -> tuple[str, str]:
    """Bestimmt (role, name) aus session_state oder current_user(). Beide leer = niemand eingeloggt."""
    role = st.session_state.get("user_role")
    name = st.session_state.get("user_name")

    if not role:
        # Fallback auf den Auth-User (Production)
        try:
            from integrations.auth import current_user
            cu = current_user()
            if cu:
                role = cu.get("rolle", "")
                name = cu.get("name", "")
        except Exception:  # noqa: BLE001
            # auth.py noch nicht geladen oder Fehler — Sidebar einfach skippen
            pass

    return (role or "", name or "—")


# -----------------------------------------------------------------------------
# Public — die einzige Funktion die app.py aufruft
# -----------------------------------------------------------------------------

def render_sidebar() -> None:
    """Zeichnet die komplette Sidebar (Brand · Nav-Sektionen · User-Footer).

    Liest die Rolle aus session_state / current_user. Bei unbekannter Rolle:
    rendert nur Brand + 'Bitte einloggen'-Hinweis.
    """
    # Font + CSS einmal pro Render
    load_material_icons_font()
    hide_default_streamlit_nav()

    role, name = _resolve_user()
    role_key   = normalize_role(role)

    # Brand-Header (Logo + Rolle-Badge)
    brand_header(role_key)

    if role_key == "sales":
        _render_sales_sidebar()
    elif role_key == "mentor":
        _render_mentor_sidebar()
    elif role_key == "admin":
        _render_admin_sidebar()
    else:
        st.sidebar.caption("Bitte einloggen, um zu navigieren.")
        return

    # User-Footer ganz unten
    user_avatar(name, role_key)


# -----------------------------------------------------------------------------
# Rolle-spezifische Nav — folgt dem Briefing
# -----------------------------------------------------------------------------

def _render_sales_sidebar() -> None:
    section_header("today", "Mein Tag")
    _page_link("pages/sales_cockpit.py",            "Cockpit",            "space_dashboard")
    _page_link("pages/3_Setter_Daily.py",           "Setter Daily",       "phone_in_talk")
    _page_link("pages/sales_strategiegespraeche.py", "Strategiegespräche", "flag")

    section_header("format_list_bulleted", "Meine Leads")
    _page_link("pages/sales_meine_leads.py",  "Meine Pipeline",    "view_kanban")
    _page_link("pages/sales_conversions.py",  "Meine Conversions", "trending_up")

    section_header("info", "Info")
    _page_link("pages/4_Programme.py", "Programme", "inventory_2")
    _page_link("pages/5_Mentoren.py",  "Mentoren",  "school")


def _render_mentor_sidebar() -> None:
    section_header("today", "Mein Tag")
    _page_link("pages/mentor_cockpit.py",   "Cockpit",         "space_dashboard")
    _page_link("pages/mentor_sessions.py",  "Meine Sessions",  "event")
    _page_link("pages/mentor_aufgaben.py",  "Aufgaben",        "task_alt")

    section_header("groups", "Meine Mentees")
    _page_link("pages/mentor_mentees.py",     "Meine Mentees", "person")
    _page_link("pages/mentor_engagements.py", "Engagements",   "handshake")

    section_header("account_circle", "Mein Profil")
    _page_link("pages/mentor_profil.py", "Mein Profil", "account_circle")

    section_header("info", "Info")
    _page_link("pages/4_Programme.py", "Programme", "inventory_2")


def _render_admin_sidebar() -> None:
    # Strikte Trennung: alles Read-only/Analytisch unter Insights,
    # alles Schreibend/Verwaltung unter Administration.
    section_header("insights", "Insights")
    _page_link("pages/1_Dashboard.py",        "Dashboard",       "space_dashboard")
    _page_link("pages/admin_pipeline.py",     "Pipeline",        "view_kanban")
    _page_link("pages/admin_performance.py",  "Performance",     "leaderboard")
    _page_link("pages/mentor_analytics.py",   "Mentor-Analytics", "school")
    _page_link("pages/cs_analytics.py",       "CS-Analytics",    "handshake")

    section_header("settings", "Administration")
    _page_link("pages/2_Leads.py",            "Leads",            "format_list_bulleted")
    _page_link("pages/5_Mentoren.py",         "Mentoren",         "school")
    _page_link("pages/6_Customer_Success.py", "Customer Success", "handshake")
    _page_link("pages/4_Programme.py",        "Programme",        "inventory_2")

    section_header("phone_in_talk", "Monitoring")
    _page_link("pages/3_Setter_Daily.py", "Setter Daily", "phone_in_talk")

    section_header("build", "System")
    _page_link("pages/7_Benutzer.py", "Benutzer", "manage_accounts")
