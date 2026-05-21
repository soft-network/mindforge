"""Onboarding-Funnel — Plotly-Funnel der vier Onboarding-Stages."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib.kpis import onboarding_funnel_counts


def render_onboarding_funnel(
    df_kunden: pd.DataFrame,
    title: str = "Onboarding-Funnel",
) -> None:
    """Plotly-Funnel mit den 4 Stages: Pending → Welcome → Onboarding → Activated.

    Stages bleiben in fester Reihenfolge auch bei Count=0, damit die Story der
    Page über die Zeit konsistent bleibt.
    """
    if df_kunden.empty:
        st.caption("Keine Kunden im aktuellen Filter.")
        return

    grp = onboarding_funnel_counts(df_kunden)
    fig = go.Figure(go.Funnel(
        y=grp["Stage"],
        x=grp["Count"],
        textposition="inside",
        textinfo="value+percent initial",
        marker={"color": ["#fde68a", "#a7f3d0", "#86efac", "#22c55e"]},
    ))
    fig.update_layout(
        title=title,
        height=380,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)
