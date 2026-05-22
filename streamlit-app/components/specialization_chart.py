"""Spezialisierungs-Verteilung als Plotly-Bar — Mentor-Anzahl pro Skill."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from lib.kpis import mentor_specialization_counts


def render_specialization(
    df_mentoren: pd.DataFrame,
    title: str = "Mentoren pro Spezialisierung",
) -> None:
    """Vertikaler Bar-Chart der Mentor-Anzahl pro Skill.

    Multi-Select expandiert — ein Mentor mit ['Business', 'Sales'] zählt in
    beide Buckets.
    """
    if df_mentoren.empty:
        return

    counts = mentor_specialization_counts(df_mentoren)
    if counts.empty:
        st.caption("Keine Spezialisierungen erfasst.")
        return

    plot_df = counts.reset_index()
    plot_df.columns = ["Spezialisierung", "Mentor-Anzahl"]

    fig = px.bar(
        plot_df,
        x="Spezialisierung",
        y="Mentor-Anzahl",
        color="Mentor-Anzahl",
        color_continuous_scale="Blues",
        title=title,
        text="Mentor-Anzahl",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
