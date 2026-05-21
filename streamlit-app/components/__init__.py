"""Wiederverwendbare Streamlit-UI-Bausteine.

Diese Schicht kombiniert lib/-Berechnungen mit Streamlit-Rendering. Wird
von pages/ konsumiert.

Module:
    kpi_row              — Top-KPI-Strip mit st.metric (Dashboard)
    funnel_chart         — Plotly-Funnel des Lead-Status
    source_chart         — Plotly-Bar mit Conversion pro Source
    lead_card            — Lead-Karte (Expander) — wiederverwendbar
    mentor_kpi_row       — KPI-Strip für Mentoren-Page
    mentor_capacity_chart — Bar mit Auslastung % pro Mentor
    specialization_chart — Bar mit Mentor-Anzahl pro Spezialisierung
    cs_kpi_row           — KPI-Strip für Customer-Success-Page
    onboarding_funnel    — Plotly-Funnel der Onboarding-Stages
    health_distribution  — Plotly-Bar der Health-Tier-Verteilung
    mrr_chart            — Plotly-Bar MRR pro Programm

    common               — Helper: render_empty_state(), confirm_save_buttons()
"""

from __future__ import annotations

import streamlit as st


def render_empty_state(message: str, icon: str = "ℹ️") -> None:
    """Einheitlicher Empty-State für alle Pages.

    Wird gerufen wenn ein DataFrame leer ist oder ein Filter keine Treffer
    liefert. Konsistente Darstellung über alle Pages.
    """
    st.info(f"{icon}  {message}")


def confirm_save_buttons(
    save_label: str = "💾 Speichern",
    cancel_label: str = "Abbrechen",
    key_prefix: str = "",
) -> tuple[bool, bool]:
    """Standardisierte Speichern/Abbrechen-Buttonreihe für Edit-Modals.

    Returns:
        (save_clicked, cancel_clicked)
    """
    bcol1, bcol2 = st.columns(2)
    save = bcol1.button(
        save_label,
        type="primary",
        use_container_width=True,
        key=f"{key_prefix}_save",
    )
    cancel = bcol2.button(
        cancel_label,
        use_container_width=True,
        key=f"{key_prefix}_cancel",
    )
    return save, cancel
