"""Performance — Drei Tabs: Sales · Mentor · Programm (Admin-only).

Konsolidiert die KPIs aus drei Domänen auf einer Page mit Tabs.
Reine Analyse-Sicht, kein Edit.
"""

from __future__ import annotations

import pathlib
import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from components import render_empty_state  # noqa: E402
from components.mentor_capacity_chart import render_mentor_capacity  # noqa: E402
from components.specialization_chart import render_specialization  # noqa: E402
from integrations.airtable_helpers import (  # noqa: E402
    load_kunden, load_leads, load_mentoren, load_programs,
)
from integrations.auth import require_tool_access  # noqa: E402
from lib.kpis import (  # noqa: E402
    compute_mentor_kpis,
    programm_performance,
    sales_performance,
)


require_tool_access("performance", "read")


st.title("🏆 Performance")
st.caption("Read-only Analytics über Sales · Mentor · Programm")

df_leads    = load_leads()
df_kunden   = load_kunden()
df_mentoren = load_mentoren()
df_programs = load_programs()


tab_sales, tab_mentor, tab_prog = st.tabs(["📞 Sales", "👥 Mentor", "🏆 Programm"])


# -----------------------------------------------------------------------------
# Tab Sales — Setter-Leaderboard + Conversion-Rates
# -----------------------------------------------------------------------------
with tab_sales:
    sp = sales_performance(df_leads)
    if sp.empty:
        render_empty_state(
            "Keine Setter-Zuweisungen in Leads. "
            "Admin muss Setter-Feld auf Leads pflegen.",
            icon="📞",
        )
    else:
        k = st.columns(4)
        k[0].metric("Aktive Setter", len(sp))
        k[1].metric("Leads gesamt", int(sp["Leads"].sum()))
        k[2].metric("Conversions", int(sp["Converted"].sum()))
        avg_conv = float(sp["Conversion %"].mean())
        k[3].metric("⌀ Conversion-Rate", f"{avg_conv:.1f} %")

        st.markdown("---")
        st.subheader("Setter-Leaderboard")
        fig = px.bar(
            sp, x="Setter", y="Conversion %",
            color="Conversion %", color_continuous_scale="RdYlGn",
            text="Conversion %",
            hover_data=["Leads", "Hot", "Booked", "Converted"],
        )
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(height=340, margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(sp, use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------
# Tab Mentor — NPS-Ranking + Auslastung + Spezialisierung
# -----------------------------------------------------------------------------
with tab_mentor:
    if df_mentoren.empty:
        render_empty_state("Keine Mentoren angelegt.", icon="👥")
    else:
        mk = compute_mentor_kpis(df_mentoren)
        k = st.columns(4)
        k[0].metric("Mentoren aktiv",       mk["aktiv"], f"{mk['total']} gesamt")
        k[1].metric("Aktive Mentees",       mk["total_aktive_kunden"])
        k[2].metric("⌀ Kapazität / Woche",  f"{mk['avg_capacity']:.1f}")
        k[3].metric("⌀ NPS",                 f"{mk['avg_nps']:.1f}")

        st.markdown("---")

        ranked = df_mentoren.sort_values("Avg NPS", ascending=False, na_position="last")
        if not ranked["Avg NPS"].dropna().empty:
            st.subheader("NPS-Ranking")
            fig = px.bar(
                ranked.dropna(subset=["Avg NPS"]),
                x="Name", y="Avg NPS",
                color="Avg NPS", color_continuous_scale="RdYlGn",
                text="Avg NPS", range_y=[0, 10],
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(height=340, margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        c = st.columns(2)
        with c[0]:
            render_mentor_capacity(df_mentoren)
        with c[1]:
            render_specialization(df_mentoren)


# -----------------------------------------------------------------------------
# Tab Programm — Lead-Reach + Conversion + MRR-Total
# -----------------------------------------------------------------------------
with tab_prog:
    pp = programm_performance(df_leads, df_kunden, df_programs)
    if pp.empty:
        render_empty_state("Keine Programm-Daten.", icon="🏆")
    else:
        k = st.columns(4)
        k[0].metric("Programme",        len(pp))
        k[1].metric("Lead-Reach gesamt", int(pp["Lead-Count"].sum()))
        k[2].metric("Conversions",      int(pp["Converted"].sum()))
        k[3].metric("MRR gesamt (€)",   f"{int(pp['MRR-Total'].sum()):,}")

        st.markdown("---")
        st.subheader("Programm-Übersicht")

        cc = st.columns(2)
        with cc[0]:
            fig = px.bar(
                pp, x="Programm", y="MRR-Total",
                color="MRR-Total", color_continuous_scale="Blues",
                text="MRR-Total", title="MRR-Total pro Programm",
            )
            fig.update_traces(texttemplate="€ %{text:,.0f}", textposition="outside")
            fig.update_layout(height=340, margin=dict(l=20, r=20, t=40, b=20), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with cc[1]:
            fig = px.bar(
                pp, x="Programm", y="Conversion %",
                color="Conversion %", color_continuous_scale="RdYlGn",
                text="Conversion %", title="Conversion-Rate pro Programm",
            )
            fig.update_traces(texttemplate="%{text}%", textposition="outside")
            fig.update_layout(height=340, margin=dict(l=20, r=20, t=40, b=20), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        st.dataframe(pp, use_container_width=True, hide_index=True)
