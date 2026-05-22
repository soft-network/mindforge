"""MRR pro Programm — Plotly-Bar."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from lib.kpis import mrr_per_program


def render_mrr_chart(
    df_kunden: pd.DataFrame,
    title: str = "MRR pro Programm",
) -> None:
    """Bar-Chart der MRR-Summe pro Programm mit Kunden-Anzahl im Hover."""
    if df_kunden.empty:
        st.caption("Keine Kunden im aktuellen Filter.")
        return

    grp = mrr_per_program(df_kunden)
    if grp.empty:
        return

    fig = px.bar(
        grp,
        x="Program",
        y="MRR (EUR)",
        color="MRR (EUR)",
        color_continuous_scale="Blues",
        title=title,
        text="MRR (EUR)",
        hover_data=["Kunden", "MRR pro Kunde"],
    )
    fig.update_traces(texttemplate="€ %{text:,.0f}", textposition="outside")
    fig.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
        xaxis_title=None,
    )
    st.plotly_chart(fig, use_container_width=True)
