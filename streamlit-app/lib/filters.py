"""Filter-Predicates für Lead/Customer-DataFrames — pure Python."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

import pandas as pd

from lib.tz import TZ_BERLIN


# Vordefinierte Zeit-Range-Optionen für UI-Selectbox
DATE_RANGE_OPTIONS = [
    "Alle",
    "Heute",
    "Diese Woche",
    "Letzte Woche",
    "Diesen Monat",
    "Letzten Monat",
    "Letzte 3 Monate",
    "Letzte 6 Monate",
    "Dieses Jahr",
    "Letztes Jahr",
    "Custom (Kalender)",
]


def filter_leads(
    df: pd.DataFrame,
    status: str = "Alle",
    source: str = "Alle",
    min_score: int = 0,
    search: str = "",
) -> pd.DataFrame:
    """Filterkette für die Leads-Page.

    Args:
        df:        Volle Leads-DataFrame
        status:    "Alle" oder konkreter Status-Wert
        source:    "Alle" oder konkrete Source
        min_score: Minimum Lead Score (inklusiv)
        search:    Substring-Suche in Name/E-Mail (case-insensitive)

    Returns:
        Gefilterter DataFrame (Original bleibt unangetastet).
    """
    if df.empty:
        return df

    out = df.copy()

    if status != "Alle":
        out = out[out["Status"] == status]
    if source != "Alle":
        out = out[out["Source"] == source]
    if min_score > 0:
        out = out[out["Lead Score"] >= min_score]
    if search:
        mask = (
            out["Name"].str.contains(search, case=False, na=False)
            | out["E-Mail"].str.contains(search, case=False, na=False)
        )
        out = out[mask]

    return out


def unique_options(df: pd.DataFrame, col: str) -> list[str]:
    """Sortierte Liste der einzigartigen Werte einer Spalte, prefixed mit 'Alle'.

    Für Streamlit-Dropdown-Filter.
    """
    if df.empty or col not in df.columns:
        return ["Alle"]
    return ["Alle"] + sorted(df[col].dropna().unique().tolist())


# -----------------------------------------------------------------------------
# Mentoren-Filter
# -----------------------------------------------------------------------------

def filter_mentoren(
    df: pd.DataFrame,
    status: str = "Alle",
    spezialisierung: str = "Alle",
    stadt: str = "Alle",
    search: str = "",
) -> pd.DataFrame:
    """Filterkette für die Mentoren-Page.

    Spezialisierung filtert über Multi-Select-Listen (Mentor mit ['Business',
    'Sales'] matched 'Business' UND 'Sales').
    """
    if df.empty:
        return df
    out = df.copy()
    if status != "Alle":
        out = out[out["Status"] == status]
    if spezialisierung != "Alle":
        mask = out["Spezialisierung"].apply(
            lambda x: spezialisierung in x if isinstance(x, list) else False
        )
        out = out[mask]
    if stadt != "Alle":
        out = out[out["Stadt"] == stadt]
    if search:
        mask = (
            out["Name"].str.contains(search, case=False, na=False)
            | out["E-Mail"].str.contains(search, case=False, na=False)
        )
        out = out[mask]
    return out


def unique_specializations(df: pd.DataFrame) -> list[str]:
    """Sortierte Liste aller Spezialisierungen (Multi-Select expandiert),
    prefixed mit 'Alle' — für Filter-Dropdown.
    """
    if df.empty or "Spezialisierung" not in df.columns:
        return ["Alle"]
    all_specs: set[str] = set()
    for specs in df["Spezialisierung"].dropna():
        if isinstance(specs, list):
            all_specs.update(specs)
    return ["Alle"] + sorted(all_specs)


# -----------------------------------------------------------------------------
# Kunden-Filter (Customer Success Page)
# -----------------------------------------------------------------------------

HEALTH_TIER_OPTIONS = ["Alle", "Engaged", "Active", "At Risk", "Churn Risk", "Churned"]


def filter_kunden(
    df: pd.DataFrame,
    status: str = "Alle",
    onboarding: str = "Alle",
    programm: str = "Alle",
    mentor: str = "Alle",
    health_tier: str = "Alle",
    search: str = "",
) -> pd.DataFrame:
    """Filterkette für die Customer-Success-Page.

    Args:
        df:           Volle Kunden-DataFrame
        status:       "Alle" oder Kunden-Status (Active/Onboarding/Paused/Churned)
        onboarding:   "Alle" oder Onboarding-Stage
        programm:     "Alle" oder Programm-Name
        mentor:       "Alle" oder Mentor-Name (gefiltert über `Mentor Name` Lookup)
        health_tier:  "Alle" oder Health-Tier (Engaged/Active/At Risk/...)
        search:       Substring-Suche in Lead-Name (case-insensitive)
    """
    if df.empty:
        return df
    out = df.copy()
    if status != "Alle":
        out = out[out["Status"] == status]
    if onboarding != "Alle":
        out = out[out["Onboarding Status"] == onboarding]
    if programm != "Alle":
        out = out[out["Program"] == programm]
    if mentor != "Alle":
        out = out[out["Mentor Name"] == mentor]
    if health_tier != "Alle":
        out = out[out["Health Tier"] == health_tier]
    if search:
        out = out[out["Lead"].str.contains(search, case=False, na=False)]
    return out


# -----------------------------------------------------------------------------
# Date-Range-Filter
# -----------------------------------------------------------------------------

def get_date_range(
    range_name: str,
    custom_start: Optional[date] = None,
    custom_end: Optional[date] = None,
) -> tuple[Optional[datetime], Optional[datetime]]:
    """Berechnet (start, end) tz-aware Berlin-Datetimes für eine benannte Range.

    Rückgabe (None, None) heißt: kein Filter anwenden (z.B. "Alle").
    end ist exklusiv (`<`), start ist inklusiv (`>=`).
    """
    now = datetime.now(TZ_BERLIN)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if range_name in ("Alle", None, ""):
        return (None, None)

    if range_name == "Heute":
        return (today_start, today_start + timedelta(days=1))

    if range_name == "Diese Woche":
        # weekday(): Mo=0, So=6 — wir starten am Montag
        days_since_monday = today_start.weekday()
        start = today_start - timedelta(days=days_since_monday)
        return (start, start + timedelta(days=7))

    if range_name == "Letzte Woche":
        days_since_monday = today_start.weekday()
        this_week_start = today_start - timedelta(days=days_since_monday)
        return (this_week_start - timedelta(days=7), this_week_start)

    if range_name == "Diesen Monat":
        start = today_start.replace(day=1)
        end = (
            start.replace(year=start.year + 1, month=1)
            if start.month == 12
            else start.replace(month=start.month + 1)
        )
        return (start, end)

    if range_name == "Letzten Monat":
        first_of_this_month = today_start.replace(day=1)
        last_month_start = (
            first_of_this_month.replace(year=first_of_this_month.year - 1, month=12)
            if first_of_this_month.month == 1
            else first_of_this_month.replace(month=first_of_this_month.month - 1)
        )
        return (last_month_start, first_of_this_month)

    if range_name == "Letzte 3 Monate":
        return (today_start - timedelta(days=90), today_start + timedelta(days=1))

    if range_name == "Letzte 6 Monate":
        return (today_start - timedelta(days=180), today_start + timedelta(days=1))

    if range_name == "Dieses Jahr":
        start = today_start.replace(month=1, day=1)
        return (start, start.replace(year=start.year + 1))

    if range_name == "Letztes Jahr":
        this_year_start = today_start.replace(month=1, day=1)
        return (
            this_year_start.replace(year=this_year_start.year - 1),
            this_year_start,
        )

    if range_name.startswith("Custom") and custom_start and custom_end:
        start_dt = datetime.combine(custom_start, datetime.min.time(), tzinfo=TZ_BERLIN)
        end_dt = (
            datetime.combine(custom_end, datetime.min.time(), tzinfo=TZ_BERLIN)
            + timedelta(days=1)  # end-of-day inclusive
        )
        return (start_dt, end_dt)

    return (None, None)


def filter_by_date_range(
    df: pd.DataFrame,
    range_name: str,
    custom_start: Optional[date] = None,
    custom_end: Optional[date] = None,
    date_column: str = "Erstellt am",
) -> pd.DataFrame:
    """Filtert ein DataFrame nach einer Date-Spalte anhand einer benannten Range.

    Erwartet `df[date_column]` als tz-aware Series (typischerweise UTC).
    Pandas vergleicht intern korrekt mit Berlin-aware Datetimes.
    """
    if df.empty or date_column not in df.columns:
        return df

    start, end = get_date_range(range_name, custom_start, custom_end)
    if start is None:
        return df

    return df[(df[date_column] >= start) & (df[date_column] < end)]
