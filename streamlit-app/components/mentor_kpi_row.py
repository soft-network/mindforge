"""Mentoren-KPI-Strip — vier st.metric-Karten oben auf der Page."""

from __future__ import annotations

import streamlit as st

from lib.kpis import MentorKpis


def render_mentor_kpi_row(kpis: MentorKpis) -> None:
    """Vier KPI-Karten für die Mentoren-Page.

    Nimmt das Result von lib.kpis.compute_mentor_kpis().
    """
    cols = st.columns(4)
    cols[0].metric(
        "Mentoren aktiv",
        kpis["aktiv"],
        f"{kpis['total']} insgesamt",
    )
    cols[1].metric(
        "Aktive Kunden (Inner Circle)",
        kpis["total_aktive_kunden"],
    )
    cols[2].metric(
        "⌀ Kapazität / Woche",
        f"{kpis['avg_capacity']:.1f}",
    )
    cols[3].metric(
        "⌀ NPS",
        f"{kpis['avg_nps']:.1f}",
    )
