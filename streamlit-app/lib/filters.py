"""Filter-Predicates für Lead/Customer-DataFrames — pure Python."""

from __future__ import annotations

import pandas as pd


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
