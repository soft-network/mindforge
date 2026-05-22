"""Customer-Success-KPI-Strip — fünf st.metric-Karten."""

from __future__ import annotations

import streamlit as st

from lib.kpis import CSKpis


def render_cs_kpi_row(kpis: CSKpis) -> None:
    """KPI-Strip oben auf der Customer-Success-Page.

    Nimmt das Result von lib.kpis.compute_cs_kpis().
    """
    cols = st.columns(5)
    cols[0].metric(
        "Kunden gesamt",
        kpis["total_kunden"],
        f"{kpis['activated']} activated",
    )
    cols[1].metric(
        "Onboarding offen",
        kpis["onboarding_pending"],
        help="Kunden, die noch nicht den Status 'Activated' haben",
    )
    cols[2].metric(
        "Churn-Risk",
        kpis["churn_risk"],
        help="Health Score < 50 (At Risk / Churn Risk / Churned)",
    )
    cols[3].metric(
        "MRR (€)",
        f"{kpis['total_mrr']:,.0f}",
    )
    cols[4].metric(
        "⌀ Health Score",
        f"{kpis['avg_health']:.1f}",
    )
