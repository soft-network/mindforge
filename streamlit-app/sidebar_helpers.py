"""Sidebar-Helper — Brand-Header, Sektions-Header, Rolle-Badge, User-Avatar.

Renders über Streamlit native `st.sidebar.markdown(..., unsafe_allow_html=True)`
+ Google Material Symbols Outlined Font. Pages selbst nutzen
`st.page_link(..., icon=":material/<name>:")` für die Nav-Items — Streamlit
1.36+ rendert Material Symbols nativ.
"""

from __future__ import annotations

import streamlit as st


# -----------------------------------------------------------------------------
# Rolle-Farbcodierung (deckt sich mit dem HTML-Mockup)
# -----------------------------------------------------------------------------

ROLE_COLORS: dict[str, dict[str, str]] = {
    "sales":  {"bg": "#FAEEDA", "fg": "#854F0B"},
    "mentor": {"bg": "#E6F1FB", "fg": "#0C447C"},
    "admin":  {"bg": "#FCEBEB", "fg": "#791F1F"},
}

# Wie die Rolle im Badge angezeigt wird (Versalschrift)
ROLE_BADGE_LABEL: dict[str, str] = {
    "sales":  "SALES",
    "mentor": "MENTOR",
    "admin":  "ADMIN",
}

# Wie die Rolle im User-Footer angezeigt wird (mit korrekter Groß-/Kleinschreibung)
ROLE_FOOTER_LABEL: dict[str, str] = {
    "sales":  "Sales",
    "mentor": "Mentor",
    "admin":  "Hauptadmin",
}


def normalize_role(rolle: str | None) -> str:
    """Mappt verschiedene Schreibweisen auf die kanonischen Keys 'admin'/'sales'/'mentor'.

    Toleriert 'Hauptadmin' (aus Airtable.Benutzer.Rolle) sowie kleingeschriebene
    Varianten. Unbekannt → leerer String.
    """
    r = (rolle or "").strip().lower()
    if r == "hauptadmin":
        return "admin"
    if r in {"sales", "mentor", "admin"}:
        return r
    return ""


# -----------------------------------------------------------------------------
# Font-Loader — Material Symbols Outlined von Google Fonts.
# Streamlit lädt für :material/icon_name: in st.page_link() die Font selbst.
# Wir laden sie zusätzlich für eigene HTML-Spans (Sektions-Header, Avatar etc.).
# -----------------------------------------------------------------------------

def load_material_icons_font() -> None:
    """Lädt die Material-Symbols-Outlined Font.

    Idempotent — wenn die Page-Markdowns mehrfach gerendert werden, fügt der
    Browser den `<link>` einfach dedupliziert ein.
    """
    st.markdown(
        '<link href="https://fonts.googleapis.com/css2?'
        'family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" '
        'rel="stylesheet">',
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# UI-Bausteine — jeweils HTML-Snippets in die Sidebar geschrieben
# -----------------------------------------------------------------------------

def role_badge_html(role: str) -> str:
    """Gibt das HTML für das Rolle-Badge im Brand-Header zurück."""
    key = normalize_role(role)
    colors = ROLE_COLORS.get(key, {"bg": "#E5E7EB", "fg": "#374151"})
    label  = ROLE_BADGE_LABEL.get(key, key.upper() or "—")
    return (
        f'<span style="background:{colors["bg"]}; color:{colors["fg"]};'
        f'             font-size:10px; padding:3px 8px; border-radius:6px;'
        f'             font-weight:600; letter-spacing:0.3px;">{label}</span>'
    )


def brand_header(role: str) -> None:
    """Brand-Header oben in der Sidebar: 🤍 Lovelifepassport + Rollen-Badge."""
    st.sidebar.markdown(
        f"""
        <div style="display:flex; align-items:center; justify-content:space-between;
                    padding: 6px 4px 0 4px;">
          <div style="display:flex; align-items:center; gap:6px;">
            <span class="material-symbols-outlined"
                  style="color:#FF4B4B; font-size:22px;
                         font-variation-settings: 'FILL' 1, 'wght' 500;">favorite</span>
            <span style="font-size:16px; font-weight:500; color:#262730;">Lovelifepassport</span>
          </div>
          {role_badge_html(role)}
        </div>
        <hr style="height:1px; background:#D1D5DB; border:none;
                   margin: 12px 0 0 0;">
        """,
        unsafe_allow_html=True,
    )


def section_header(icon: str, label: str) -> None:
    """Sektions-Header: kleines Material-Symbol + graue Versalschrift.

    Args:
        icon:  Material-Symbols-Name (z. B. 'today', 'info', 'settings')
        label: Anzeigetext (z. B. 'Mein Tag', 'Administration')
    """
    st.sidebar.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:6px;
                    padding: 12px 0 4px 4px;
                    font-size:11px; font-weight:500;
                    color:#888780; letter-spacing:0.5px;
                    text-transform:uppercase;">
          <span class="material-symbols-outlined"
                style="font-size:13px; color:#888780;">{icon}</span>
          <span>{label}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def user_avatar(name: str, role: str) -> None:
    """User-Avatar + Logout-Button unten in der Sidebar.

    Initialen-Kreis in Rollen-Farbe + Name + Rolle, darunter ein dezenter
    Logout-Button. Trennlinie darüber.
    """
    key = normalize_role(role)
    colors = ROLE_COLORS.get(key, {"bg": "#E5E7EB", "fg": "#374151"})
    role_label = ROLE_FOOTER_LABEL.get(key, role or "—")
    initials = "".join(p[0].upper() for p in (name or "?").split()[:2]) or "?"

    st.sidebar.markdown(
        f"""
        <hr style="height:1px; background:#D1D5DB; border:none;
                   margin: 18px 0 10px 0;">
        <div style="display:flex; align-items:center; gap:10px; padding: 0 4px 8px 4px;">
          <div style="width:32px; height:32px; border-radius:50%;
                      background:{colors["bg"]}; color:{colors["fg"]};
                      display:flex; align-items:center; justify-content:center;
                      font-size:12px; font-weight:600; flex-shrink:0;">{initials}</div>
          <div style="min-width:0; flex:1;">
            <div style="font-size:13px; font-weight:500; color:#262730;
                        white-space:nowrap; overflow:hidden;
                        text-overflow:ellipsis;">{name or "—"}</div>
            <div style="font-size:11px; color:#586069;">{role_label}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Logout-Button als echte Streamlit-Komponente — nutzt das Theme automatisch
    if st.sidebar.button(
        "Logout", key="sidebar_logout_btn", use_container_width=True,
    ):
        # Lazy-Import um Circular-Import zu vermeiden
        from integrations.auth import logout
        logout()


# -----------------------------------------------------------------------------
# CSS-Override: Streamlit's eingebaute Sidebar-Nav verstecken,
# unsere Custom-Sidebar dafür sichtbar machen + Spacing fein justieren.
# -----------------------------------------------------------------------------

def hide_default_streamlit_nav() -> None:
    """Versteckt die Default-Streamlit-Nav (st.navigation rendert sie automatisch).

    Wir bauen unsere eigene Nav via render_sidebar()/st.page_link(); die
    Default-Nav würde sonst doppelt erscheinen.
    """
    st.markdown(
        """
        <style>
        /* Default-Nav von st.navigation() — komplett verstecken */
        [data-testid="stSidebarNav"] { display: none !important; }

        /* st.page_link-Items kompakter (passt zum HTML-Mockup) */
        [data-testid="stSidebar"] [data-testid="stPageLink"] {
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 13px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
