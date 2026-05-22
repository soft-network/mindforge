"""Lead-Funnel als Plotly-Chart."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from lib.kpis import status_counts


def render_funnel(df_leads: pd.DataFrame, title: str = "Lead Funnel") -> None:
    """Rendert einen horizontalen Funnel über den Lead-Status."""
    if df_leads.empty:
        st.info("Noch keine Leads in der Datenbank.")
        return

    counts = status_counts(df_leads)
    fig = px.funnel(x=counts.values, y=counts.index, title=title)
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)
