"""Mentor-Auslastung als Plotly-Bar — Aktive Kunden ÷ Kapazität × 100 %."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from lib.kpis import mentor_capacity_usage


def render_mentor_capacity(
    df_mentoren: pd.DataFrame,
    title: str = "Auslastung pro Mentor (%)",
) -> None:
    """Horizontaler Bar-Chart der Auslastung % pro Mentor.

    Auslastung = Aktive Kunden / Kapazität pro Woche × 100.
    Farb-Skala RdYlGn: rot=ungenutzt, grün=hoch ausgelastet.
    """
    if df_mentoren.empty:
        st.info("Keine Mentoren vorhanden.")
        return

    grp = mentor_capacity_usage(df_mentoren)
    if grp.empty:
        return

    fig = px.bar(
        grp,
        y="Name",
        x="Auslastung %",
        color="Auslastung %",
        color_continuous_scale="RdYlGn",
        orientation="h",
        title=title,
        text="Auslastung %",
        hover_data=["Aktive Kunden", "Kapazität", "Status"],
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=40, b=20),
        yaxis=dict(categoryorder="total ascending"),
    )
    st.plotly_chart(fig, use_container_width=True)
