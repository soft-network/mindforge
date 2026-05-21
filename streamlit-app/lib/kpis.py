"""KPI-Berechnungen über Lead-DataFrames — pure Python.

Erwartetes DataFrame-Schema (aus airtable_helpers.load_leads):
    id, Name, E-Mail, Telefon, Source, Status, Lead Score,
    Erstellt am (tz-aware datetime), Notizen, Interesse

Keine Streamlit-Aufrufe — alle Funktionen geben Dicts oder Skalare zurück.
"""

from __future__ import annotations

from typing import TypedDict

import pandas as pd

from lib.tz import today_start_berlin, week_start_berlin


class FunnelKpis(TypedDict):
    leads_today:    int
    leads_week:     int
    hot_leads_week: int
    total:          int
    converted:      int
    conv_rate_pct:  float


def compute_funnel_kpis(df_leads: pd.DataFrame, hot_threshold: int = 70) -> FunnelKpis:
    """KPI-Snapshot für die Top-Strip auf dem Dashboard.

    Tag-Grenzen nach Berliner Zeit (siehe lib.tz).
    """
    today_start = today_start_berlin()
    week_start  = week_start_berlin(7)

    if df_leads.empty:
        return FunnelKpis(
            leads_today=0, leads_week=0, hot_leads_week=0,
            total=0, converted=0, conv_rate_pct=0.0,
        )

    leads_today = df_leads[df_leads["Erstellt am"] >= today_start]
    leads_week  = df_leads[df_leads["Erstellt am"] >= week_start]
    hot_week    = leads_week[leads_week["Lead Score"] >= hot_threshold]

    total     = len(df_leads)
    converted = int((df_leads["Status"] == "Converted").sum())
    conv_rate = (converted / total * 100.0) if total else 0.0

    return FunnelKpis(
        leads_today    = len(leads_today),
        leads_week     = len(leads_week),
        hot_leads_week = len(hot_week),
        total          = total,
        converted      = converted,
        conv_rate_pct  = round(conv_rate, 1),
    )


def status_counts(df_leads: pd.DataFrame, status_order: list[str] | None = None) -> pd.Series:
    """Lead-Counts pro Status — für Funnel-Chart.

    status_order steuert die Reihenfolge im Funnel; fehlende Werte werden
    mit 0 aufgefüllt.
    """
    order = status_order or ["New", "Qualified", "Contacted", "Converted"]
    if df_leads.empty:
        return pd.Series([0] * len(order), index=order, name="count")
    return df_leads["Status"].value_counts().reindex(order, fill_value=0)


def conversion_per_source(df_leads: pd.DataFrame) -> pd.DataFrame:
    """Conversion-Rate pro Source — für Source-Performance-Chart.

    Spalten: Source, Total, Converted, Conversion %
    """
    if df_leads.empty:
        return pd.DataFrame(columns=["Source", "Total", "Converted", "Conversion %"])
    grp = df_leads.groupby("Source").agg(
        Total=("id", "count"),
        Converted=("Status", lambda x: int((x == "Converted").sum())),
    ).reset_index()
    grp["Conversion %"] = (grp["Converted"] / grp["Total"] * 100).round(1)
    return grp.sort_values("Conversion %", ascending=False)


# -----------------------------------------------------------------------------
# Mentoren-KPIs
# -----------------------------------------------------------------------------

class MentorKpis(TypedDict):
    total:               int
    aktiv:               int
    on_leave:            int
    avg_capacity:        float
    avg_nps:             float
    total_aktive_kunden: int


def compute_mentor_kpis(df_mentoren: pd.DataFrame) -> MentorKpis:
    """KPI-Snapshot für die Top-Strip auf der Mentoren-Page."""
    if df_mentoren.empty:
        return MentorKpis(
            total=0, aktiv=0, on_leave=0,
            avg_capacity=0.0, avg_nps=0.0, total_aktive_kunden=0,
        )
    total    = len(df_mentoren)
    aktiv    = int((df_mentoren["Status"] == "Active").sum())
    on_leave = int((df_mentoren["Status"] == "On Leave").sum())
    avg_cap  = float(df_mentoren["Kapazität"].mean())
    nps_clean = df_mentoren["Avg NPS"].dropna()
    avg_nps  = float(nps_clean.mean()) if not nps_clean.empty else 0.0
    return MentorKpis(
        total               = total,
        aktiv               = aktiv,
        on_leave            = on_leave,
        avg_capacity        = round(avg_cap, 1),
        avg_nps             = round(avg_nps, 1),
        total_aktive_kunden = int(df_mentoren["Aktive Kunden"].sum()),
    )


def mentor_capacity_usage(df_mentoren: pd.DataFrame) -> pd.DataFrame:
    """Auslastung pro Mentor — Aktive Kunden / Kapazität × 100.

    Sortiert absteigend nach Auslastung %. Inaktive Mentoren bleiben drin
    (zeigt den Datensatz vollständig).
    """
    if df_mentoren.empty:
        return pd.DataFrame(columns=["Name", "Aktive Kunden", "Kapazität", "Status", "Auslastung %"])
    out = df_mentoren[["Name", "Aktive Kunden", "Kapazität", "Status"]].copy()
    # Schutz vor Division durch 0
    out["Auslastung %"] = (
        (out["Aktive Kunden"] / out["Kapazität"].replace(0, pd.NA)) * 100
    ).round(1)
    return out.sort_values("Auslastung %", ascending=False, na_position="last")


# -----------------------------------------------------------------------------
# Customer-Success-KPIs
# -----------------------------------------------------------------------------

ONBOARDING_STAGES = [
    "Pending",
    "Welcome Pack Sent",
    "Onboarding Call Done",
    "Activated",
]

HEALTH_TIERS = ["Engaged", "Active", "At Risk", "Churn Risk", "Churned"]


class CSKpis(TypedDict):
    total_kunden:        int
    activated:           int
    onboarding_pending:  int
    churn_risk:          int
    total_mrr:           float
    total_ltv:           float
    avg_health:          float


def compute_cs_kpis(df_kunden: pd.DataFrame) -> CSKpis:
    """KPI-Snapshot für die Customer-Success-Page Top-Strip."""
    if df_kunden.empty:
        return CSKpis(
            total_kunden=0, activated=0, onboarding_pending=0,
            churn_risk=0, total_mrr=0.0, total_ltv=0.0, avg_health=0.0,
        )
    total = len(df_kunden)
    activated = int((df_kunden["Onboarding Status"] == "Activated").sum())
    pending   = int((df_kunden["Onboarding Status"] != "Activated").sum())
    # Churn-Risk = Health Score < 50 (At Risk + Churn Risk + Churned)
    churn_risk = int((df_kunden["Health Score"] < 50).sum())
    total_mrr  = float(df_kunden["MRR (EUR)"].sum())
    total_ltv  = float(df_kunden["LTV"].sum())
    avg_health = float(df_kunden["Health Score"].mean())
    return CSKpis(
        total_kunden       = total,
        activated          = activated,
        onboarding_pending = pending,
        churn_risk         = churn_risk,
        total_mrr          = round(total_mrr, 2),
        total_ltv          = round(total_ltv, 2),
        avg_health         = round(avg_health, 1),
    )


def onboarding_funnel_counts(df_kunden: pd.DataFrame) -> pd.DataFrame:
    """Kunden-Counts pro Onboarding-Stage — für Funnel-Chart.

    Spalten: Stage, Count.  Stages in fester Reihenfolge (auch wenn Count=0).
    """
    if df_kunden.empty:
        return pd.DataFrame({"Stage": ONBOARDING_STAGES, "Count": [0] * len(ONBOARDING_STAGES)})
    counts = df_kunden["Onboarding Status"].value_counts()
    return pd.DataFrame({
        "Stage": ONBOARDING_STAGES,
        "Count": [int(counts.get(s, 0)) for s in ONBOARDING_STAGES],
    })


def health_distribution(df_kunden: pd.DataFrame) -> pd.DataFrame:
    """Kunden-Counts pro Health-Tier — für Verteilungs-Chart.

    Spalten: Tier, Count.  Tiers in fester Reihenfolge (auch wenn Count=0).
    """
    if df_kunden.empty:
        return pd.DataFrame({"Tier": HEALTH_TIERS, "Count": [0] * len(HEALTH_TIERS)})
    counts = df_kunden["Health Tier"].value_counts()
    return pd.DataFrame({
        "Tier":  HEALTH_TIERS,
        "Count": [int(counts.get(t, 0)) for t in HEALTH_TIERS],
    })


def mrr_per_program(df_kunden: pd.DataFrame) -> pd.DataFrame:
    """MRR-Summe + Kunden-Anzahl pro Programm — für MRR-Chart.

    Spalten: Program, Kunden, MRR (EUR), MRR pro Kunde
    Sortiert absteigend nach MRR.
    """
    if df_kunden.empty:
        return pd.DataFrame(columns=["Program", "Kunden", "MRR (EUR)", "MRR pro Kunde"])
    grp = df_kunden.groupby("Program").agg(
        Kunden=("id", "count"),
        **{"MRR (EUR)": ("MRR (EUR)", "sum")},
    ).reset_index()
    grp["MRR pro Kunde"] = (grp["MRR (EUR)"] / grp["Kunden"]).round(2)
    return grp.sort_values("MRR (EUR)", ascending=False)


def mentor_specialization_counts(df_mentoren: pd.DataFrame) -> pd.Series:
    """Wie viele Mentoren pro Spezialisierung (Multi-Select expandiert).

    Ein Mentor mit ['Business', 'Sales'] zählt in beide Buckets.
    """
    if df_mentoren.empty:
        return pd.Series(dtype=int, name="Mentor-Anzahl")
    all_specs: list[str] = []
    for specs in df_mentoren["Spezialisierung"].dropna():
        if isinstance(specs, list):
            all_specs.extend(specs)
    if not all_specs:
        return pd.Series(dtype=int, name="Mentor-Anzahl")
    return pd.Series(all_specs).value_counts().rename("Mentor-Anzahl")
