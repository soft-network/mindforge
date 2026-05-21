"""Conversion-Rate-pro-Source als Plotly-Bar."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from lib.kpis import conversion_per_source


def render_source_performance(
    df_leads: pd.DataFrame,
    title: str = "Conversion Rate per Source",
) -> None:
    """Horizontaler Bar-Chart der Conversion-Rate pro Source."""
    if df_leads.empty:
        return

    grp = conversion_per_source(df_leads)
    if grp.empty:
        st.info("Keine Source-Daten verfügbar.")
        return

    fig = px.bar(
        grp,
        x="Source",
        y="Conversion %",
        color="Conversion %",
        color_continuous_scale="RdYlGn",
        title=title,
        text="Conversion %",
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)
