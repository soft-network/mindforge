"""Health-Score-Verteilung — Plotly-Bar mit 5 Tiers."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from lib.kpis import health_distribution


TIER_COLORS = {
    "Engaged":    "#16a34a",  # grün
    "Active":     "#65a30d",  # hellgrün
    "At Risk":    "#eab308",  # gelb
    "Churn Risk": "#f97316",  # orange
    "Churned":    "#dc2626",  # rot
}


def render_health_distribution(
    df_kunden: pd.DataFrame,
    title: str = "Health-Score-Verteilung",
) -> None:
    """Bar-Chart der Kunden-Anzahl pro Health-Tier (Engaged → Churned)."""
    if df_kunden.empty:
        st.caption("Keine Kunden im aktuellen Filter.")
        return

    grp = health_distribution(df_kunden)
    fig = px.bar(
        grp,
        x="Tier",
        y="Count",
        color="Tier",
        color_discrete_map=TIER_COLORS,
        title=title,
        text="Count",
        category_orders={"Tier": list(TIER_COLORS.keys())},
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
        xaxis_title=None,
        yaxis_title="Kunden",
    )
    st.plotly_chart(fig, use_container_width=True)
