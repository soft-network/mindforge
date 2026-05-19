"""
MindForge Coach Admin Dashboard
=================================
Internal Streamlit app for Coach team to manage leads, view KPIs, and trigger
manual actions on the CRM.

Data source: Airtable via REST API (pyairtable)
Auth: streamlit-authenticator (simple username/password)

Run locally:
    streamlit run app.py

Deploy to GCP Cloud Run:
    See ../08-gcp-deployment.md
"""

import os
from datetime import datetime, timedelta, timezone

import pandas as pd
import plotly.express as px
import streamlit as st
from pyairtable import Api


# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="MindForge Coach Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def get_airtable_api():
    """Lazy-init Airtable API client with token from secrets."""
    token = st.secrets.get("AIRTABLE_API_TOKEN") or os.environ.get("AIRTABLE_API_TOKEN")
    if not token:
        st.error("AIRTABLE_API_TOKEN nicht gesetzt. Siehe .streamlit/secrets.toml")
        st.stop()
    return Api(token)


def get_base_id():
    return st.secrets.get("AIRTABLE_BASE_ID") or os.environ.get("AIRTABLE_BASE_ID")


# -----------------------------------------------------------------------------
# AUTH (Simple Password Gate)
# -----------------------------------------------------------------------------

def check_password():
    """Lightweight password gate. For production: use streamlit-authenticator."""
    expected = st.secrets.get("ADMIN_PASSWORD") or os.environ.get("ADMIN_PASSWORD")

    if not expected:
        # Dev mode: no password required
        return True

    if st.session_state.get("authenticated"):
        return True

    st.title("MindForge Coach Login")
    pwd = st.text_input("Passwort", type="password")
    if st.button("Einloggen"):
        if pwd == expected:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Falsches Passwort.")
    return False


# -----------------------------------------------------------------------------
# DATA LOADING
# -----------------------------------------------------------------------------

@st.cache_data(ttl=60)
def load_leads():
    api = get_airtable_api()
    table = api.table(get_base_id(), "Leads")
    records = table.all()
    rows = []
    for rec in records:
        f = rec["fields"]
        rows.append({
            "id": rec["id"],
            "Name": f.get("Name", ""),
            "Email": f.get("Email", ""),
            "Phone": f.get("Phone", ""),
            "Source": f.get("Source", ""),
            "Status": f.get("Status", "New"),
            "Lead Score": f.get("Lead Score", 0),
            "Created": f.get("Created"),
            "Notes": f.get("Notes", ""),
            "Interest": f.get("Interest", []),
        })
    df = pd.DataFrame(rows)
    if not df.empty and "Created" in df.columns:
        df["Created"] = pd.to_datetime(df["Created"], errors="coerce")
    return df


@st.cache_data(ttl=300)
def load_programs():
    api = get_airtable_api()
    table = api.table(get_base_id(), "Programs")
    records = table.all()
    rows = []
    for rec in records:
        f = rec["fields"]
        rows.append({
            "id": rec["id"],
            "Name": f.get("Name", ""),
            "Category": f.get("Category", ""),
            "Price (EUR)": f.get("Price (EUR)", 0),
            "Lead Count": f.get("Lead Count", 0),
            "Converted Clients": f.get("Converted Clients", 0),
        })
    return pd.DataFrame(rows)


def update_lead(lead_id: str, fields: dict):
    api = get_airtable_api()
    table = api.table(get_base_id(), "Leads")
    table.update(lead_id, fields)
    st.cache_data.clear()


# -----------------------------------------------------------------------------
# VIEWS
# -----------------------------------------------------------------------------

def render_kpis(df_leads: pd.DataFrame):
    """Top KPI row: today, this week, conversion."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    leads_today = df_leads[df_leads["Created"] >= today_start] if not df_leads.empty else df_leads
    leads_week = df_leads[df_leads["Created"] >= week_start] if not df_leads.empty else df_leads
    hot_leads_week = leads_week[leads_week["Lead Score"] >= 70] if not leads_week.empty else leads_week

    total = len(df_leads)
    converted = len(df_leads[df_leads["Status"] == "Converted"]) if not df_leads.empty else 0
    conv_rate = (converted / total * 100) if total else 0

    cols = st.columns(4)
    cols[0].metric("Neue Leads heute", len(leads_today))
    cols[1].metric("Leads diese Woche", len(leads_week))
    cols[2].metric("Hot Leads (Woche)", len(hot_leads_week))
    cols[3].metric("Conversion-Rate", f"{conv_rate:.1f} %")


def render_funnel_chart(df_leads: pd.DataFrame):
    """Lead status funnel."""
    if df_leads.empty:
        st.info("Noch keine Leads in der Datenbank.")
        return

    status_order = ["New", "Qualified", "Contacted", "Converted"]
    counts = df_leads["Status"].value_counts().reindex(status_order, fill_value=0)

    fig = px.funnel(
        x=counts.values,
        y=counts.index,
        title="Lead Funnel"
    )
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)


def render_source_chart(df_leads: pd.DataFrame):
    """Conversion rate by source."""
    if df_leads.empty:
        return

    grp = df_leads.groupby("Source").agg(
        Total=("id", "count"),
        Converted=("Status", lambda x: (x == "Converted").sum()),
    ).reset_index()
    grp["Conversion %"] = (grp["Converted"] / grp["Total"] * 100).round(1)
    grp = grp.sort_values("Conversion %", ascending=False)

    fig = px.bar(
        grp,
        x="Source",
        y="Conversion %",
        color="Conversion %",
        color_continuous_scale="RdYlGn",
        title="Conversion Rate per Source",
        text="Conversion %"
    )
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)


def render_lead_list(df_leads: pd.DataFrame):
    """Filterable lead list with click-to-edit."""
    st.subheader("Lead-Verwaltung")

    if df_leads.empty:
        st.info("Keine Leads vorhanden.")
        return

    # Filters
    fcols = st.columns(4)
    statuses = ["Alle"] + sorted(df_leads["Status"].dropna().unique().tolist())
    sources = ["Alle"] + sorted(df_leads["Source"].dropna().unique().tolist())

    status_filter = fcols[0].selectbox("Status", statuses)
    source_filter = fcols[1].selectbox("Source", sources)
    min_score = fcols[2].slider("Min Lead Score", 0, 100, 0)
    search = fcols[3].text_input("Suche (Name/Email)", "")

    filtered = df_leads.copy()
    if status_filter != "Alle":
        filtered = filtered[filtered["Status"] == status_filter]
    if source_filter != "Alle":
        filtered = filtered[filtered["Source"] == source_filter]
    filtered = filtered[filtered["Lead Score"] >= min_score]
    if search:
        mask = (
            filtered["Name"].str.contains(search, case=False, na=False)
            | filtered["Email"].str.contains(search, case=False, na=False)
        )
        filtered = filtered[mask]

    st.write(f"**{len(filtered)} Leads** gefunden")

    # Display
    display_cols = ["Name", "Email", "Source", "Lead Score", "Status", "Created"]
    st.dataframe(
        filtered[display_cols].sort_values("Created", ascending=False),
        use_container_width=True,
        hide_index=True
    )

    # Quick action: edit single lead
    st.markdown("### Lead bearbeiten")
    if len(filtered) > 0:
        selected = st.selectbox(
            "Lead auswählen",
            filtered["id"].tolist(),
            format_func=lambda lid: filtered.loc[filtered["id"] == lid, "Name"].values[0]
        )

        if selected:
            row = filtered[filtered["id"] == selected].iloc[0]

            ecols = st.columns(2)
            new_status = ecols[0].selectbox(
                "Status",
                ["New", "Qualified", "Contacted", "Converted", "Lost"],
                index=["New", "Qualified", "Contacted", "Converted", "Lost"].index(row["Status"])
            )
            new_score = ecols[1].slider("Lead Score", 0, 100, int(row["Lead Score"]))

            if st.button("Speichern", type="primary"):
                update_lead(selected, {
                    "Status": new_status,
                    "Lead Score": new_score
                })
                st.success("Aktualisiert.")
                st.rerun()


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------

def main():
    if not check_password():
        return

    st.sidebar.title("MindForge Coach")
    st.sidebar.markdown("Internes Lead-Management Dashboard")

    page = st.sidebar.radio("Navigation", ["Dashboard", "Leads", "Programme"])

    if st.sidebar.button("Cache leeren / Neu laden"):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Letztes Update: {datetime.now().strftime('%H:%M:%S')}")

    df_leads = load_leads()

    if page == "Dashboard":
        st.title("Dashboard")
        render_kpis(df_leads)
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            render_funnel_chart(df_leads)
        with c2:
            render_source_chart(df_leads)

    elif page == "Leads":
        st.title("Leads")
        render_lead_list(df_leads)

    elif page == "Programme":
        st.title("Programme")
        df_programs = load_programs()
        if df_programs.empty:
            st.info("Keine Programme vorhanden.")
        else:
            st.dataframe(df_programs, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
