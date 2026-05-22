"""KPI-Strip — vier st.metric-Karten."""

from __future__ import annotations

import streamlit as st

from lib.kpis import FunnelKpis


def render_kpi_row(kpis: FunnelKpis) -> None:
    """Vier KPI-Karten oben auf dem Dashboard.

    Nimmt das Result von lib.kpis.compute_funnel_kpis().
    """
    cols = st.columns(4)
    cols[0].metric("Neue Leads heute",   kpis["leads_today"])
    cols[1].metric("Leads diese Woche",  kpis["leads_week"])
    cols[2].metric("Hot Leads (Woche)",  kpis["hot_leads_week"])
    cols[3].metric("Conversion-Rate",    f"{kpis['conv_rate_pct']:.1f} %")
