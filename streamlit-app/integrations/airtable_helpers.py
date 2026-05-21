"""Airtable-Helpers für die Setter-Daily-Page (und app.py-Wiederverwendung).

Loader sind streamlit-cached; Writer invalidieren den Cache, damit die UI
beim nächsten Render den neuen State sieht.

Wichtig: Alle Feld-Namen sind die **deutschen Spaltennamen** aus der
Live-Airtable-Base (Stand 2026-05-20 — siehe `02b-airtable-phase-e-extension.md`).
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st
from pyairtable import Api


# -----------------------------------------------------------------------------
# Config (mirrors app.py so this module is import-safe outside the main app)
# -----------------------------------------------------------------------------

@st.cache_resource
def _api() -> Api:
    token = st.secrets.get("AIRTABLE_API_TOKEN") or os.environ.get("AIRTABLE_API_TOKEN")
    if not token:
        st.error("AIRTABLE_API_TOKEN nicht gesetzt. Siehe .streamlit/secrets.toml")
        st.stop()
    return Api(token)


def _base_id() -> str:
    base = st.secrets.get("AIRTABLE_BASE_ID") or os.environ.get("AIRTABLE_BASE_ID")
    if not base:
        st.error("AIRTABLE_BASE_ID nicht gesetzt. Siehe .streamlit/secrets.toml")
        st.stop()
    return base


# -----------------------------------------------------------------------------
# Readers
# -----------------------------------------------------------------------------

@st.cache_data(ttl=30)
def get_hot_leads(
    min_score: int = 70,
    statuses: tuple[str, ...] = ("New", "Qualified"),
    limit: int = 50,
) -> pd.DataFrame:
    """Hot-Lead-Queue für die Setter-Daily-UI.

    Filter via Airtable-Formula damit wir nicht alle Records pullen.
    Sortierung: Quiz Score desc, dann Erstellt am asc (oldest hot first).
    """
    status_or = ", ".join(f'{{Status}}="{s}"' for s in statuses)
    formula = f"AND({{Quiz Score}} >= {min_score}, OR({status_or}))"

    records = _api().table(_base_id(), "Leads").all(
        formula=formula,
        sort=["-Quiz Score", "Erstellt am"],
        max_records=limit,
    )

    rows = []
    for rec in records:
        f = rec["fields"]
        rows.append({
            "id":             rec["id"],
            "Name":           f.get("Name", ""),
            "Vorname":        f.get("Vorname", ""),
            "Nachname":       f.get("Nachname", ""),
            "E-Mail":         f.get("E-Mail", ""),
            "Telefon":        f.get("Telefon", ""),
            "Land":           f.get("Land", ""),
            "Source":         f.get("Source", ""),
            "Status":         f.get("Status", "New"),
            "Quiz Score":     f.get("Quiz Score", 0),
            "Quiz Tier":      f.get("Quiz Tier", ""),
            "Branche":        f.get("Quiz · Branche", ""),
            "Monatsumsatz":   f.get("Quiz · Monatsumsatz", ""),
            "Hauptwunsch":    f.get("Quiz · Hauptwunsch", ""),
            "Zeitbudget":     f.get("Quiz · Zeitbudget", ""),
            "Notizen":        f.get("Notizen", ""),
            "Erstellt am":    f.get("Erstellt am"),
            "Termin am":      f.get("Termin am"),
            "Meet-Link":      f.get("Meet-Link"),
            "Setter":         f.get("Setter", ""),
        })
    df = pd.DataFrame(rows)
    if not df.empty and "Erstellt am" in df.columns:
        df["Erstellt am"] = pd.to_datetime(df["Erstellt am"], errors="coerce")
        df["Termin am"]   = pd.to_datetime(df["Termin am"], errors="coerce")
    return df


@st.cache_data(ttl=120)
def get_setter_today_kpis(setter_email: str) -> dict:
    """KPI-Snapshot für die Sidebar von Setter-Daily — heute gebuchte + offene Calls."""
    formula = (
        f'AND({{Setter}}="{setter_email}", '
        f'IS_AFTER({{Termin am}}, DATEADD(NOW(), -1, \'days\')))'
    )
    records = _api().table(_base_id(), "Leads").all(formula=formula)
    today = datetime.utcnow().date()

    booked_today = 0
    for rec in records:
        ts = rec["fields"].get("Termin am")
        if not ts:
            continue
        try:
            d = datetime.fromisoformat(ts.replace("Z", "+00:00")).date()
            if d == today:
                booked_today += 1
        except ValueError:
            continue

    return {
        "calls_booked_today": booked_today,
        "calls_pending":      len(records),
    }


# -----------------------------------------------------------------------------
# Writers
# -----------------------------------------------------------------------------

def update_lead_booking(
    lead_id: str,
    call_at: datetime,
    meet_link: str,
    setter_owner: str,
    new_status: str = "Contacted",
) -> None:
    """Schreibt die Buchung zurück nach Airtable + invalidiert Cache."""
    _api().table(_base_id(), "Leads").update(lead_id, {
        "Status":    new_status,
        "Termin am": call_at.isoformat(),
        "Meet-Link": meet_link,
        "Setter":    setter_owner,
    })
    st.cache_data.clear()


def update_lead_status(
    lead_id: str,
    new_status: str,
    notes_append: Optional[str] = None,
) -> None:
    """Quick-Action: Status updaten, optional Notiz mit Timestamp anhängen."""
    table = _api().table(_base_id(), "Leads")
    patch = {"Status": new_status}
    if notes_append:
        existing = table.get(lead_id)["fields"].get("Notizen", "")
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        patch["Notizen"] = (existing + f"\n[{ts}] {notes_append}").strip()
    table.update(lead_id, patch)
    st.cache_data.clear()


# -----------------------------------------------------------------------------
# Cross-Page Loaders — werden von Dashboard, Leads, Programme genutzt
# -----------------------------------------------------------------------------

@st.cache_data(ttl=60)
def load_leads() -> pd.DataFrame:
    """Alle Leads ohne Filter — für Dashboard- und Leads-Page."""
    records = _api().table(_base_id(), "Leads").all()
    rows = []
    for rec in records:
        f = rec["fields"]
        rows.append({
            "id":           rec["id"],
            "Name":         f.get("Name", ""),
            "Vorname":      f.get("Vorname", ""),
            "Nachname":     f.get("Nachname", ""),
            "E-Mail":       f.get("E-Mail", ""),
            "Telefon":      f.get("Telefon", ""),
            "Land":         f.get("Land", ""),
            "Source":       f.get("Source", ""),
            "Status":       f.get("Status", "New"),
            "Lead Score":   f.get("Quiz Score", f.get("Lead Score", 0)),
            "Quiz Score":   f.get("Quiz Score", 0),
            "Quiz Tier":    f.get("Quiz Tier", ""),
            "Branche":      f.get("Quiz · Branche", ""),
            "Monatsumsatz": f.get("Quiz · Monatsumsatz", ""),
            "Hauptwunsch":  f.get("Quiz · Hauptwunsch", ""),
            "Zeitbudget":   f.get("Quiz · Zeitbudget", ""),
            "Notizen":      f.get("Notizen", ""),
            "Interesse":    f.get("Interesse", []),
            "Erstellt am":  f.get("Erstellt am"),
            "Termin am":    f.get("Termin am"),
            "Meet-Link":    f.get("Meet-Link"),
            "Setter":       f.get("Setter", ""),
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        # tz-aware UTC, pandas konvertiert beim Vergleich automatisch in
        # Berliner Zeit wenn TZ_BERLIN-Datetime auf der anderen Seite steht.
        df["Erstellt am"] = pd.to_datetime(df["Erstellt am"], errors="coerce", utc=True)
        df["Termin am"]   = pd.to_datetime(df["Termin am"],   errors="coerce", utc=True)
    return df


@st.cache_data(ttl=300)
def load_programs() -> pd.DataFrame:
    """Alle Programme — für Programme-Page."""
    records = _api().table(_base_id(), "Programme").all()
    rows = []
    for rec in records:
        f = rec["fields"]
        rows.append({
            "id":               rec["id"],
            "Name":             f.get("Name", ""),
            "Category":         f.get("Category", ""),
            "Price (EUR)":      f.get("Price (EUR)", 0),
            "Lead Count":       f.get("Lead Count", 0),
            "Converted Kunden": f.get("Converted Kunden", 0),
        })
    return pd.DataFrame(rows)


def update_lead(lead_id: str, fields: dict) -> None:
    """Generic Lead-Update für die Leads-Page Edit-Funktion."""
    _api().table(_base_id(), "Leads").update(lead_id, fields)
    st.cache_data.clear()


# -----------------------------------------------------------------------------
# Mentoren — Stammdaten + Python-side Joins für Aktive Kunden + Avg NPS
# (Airtable Meta-API erlaubt kein Anlegen von Count/Rollup-Feldern, daher
# berechnen wir die zwei Performance-Spalten hier durch Joins über
# Sessions.Mentor und Kunden.Mentor.)
# -----------------------------------------------------------------------------

@st.cache_data(ttl=120)
def load_mentoren() -> pd.DataFrame:
    """Lade Mentoren-Tabelle und reichere sie mit Joins an.

    Zusätzliche Spalten:
        Aktive Kunden  — Count distinct Kunden.Mentor == this mentor
        Sessions Count — Anzahl Sessions die diesem Mentor zugeordnet sind
        Avg NPS        — Durchschnitt aus Sessions.NPS für diesen Mentor
    """
    base = _base_id()
    mentoren_recs = _api().table(base, "Mentoren").all()
    sessions_recs = _api().table(base, "Sessions").all()
    kunden_recs   = _api().table(base, "Kunden").all()

    # Index Sessions → NPS-Liste pro Mentor-Rec-ID
    sessions_by_mentor: dict[str, list[int]] = {}
    for r in sessions_recs:
        mref = r["fields"].get("Mentor", [])
        nps  = r["fields"].get("NPS")
        if mref and nps is not None:
            sessions_by_mentor.setdefault(mref[0], []).append(nps)

    # Index Kunden → Count pro Mentor-Rec-ID
    kunden_count: dict[str, int] = {}
    for r in kunden_recs:
        mref = r["fields"].get("Mentor", [])
        if mref:
            kunden_count[mref[0]] = kunden_count.get(mref[0], 0) + 1

    rows = []
    for r in mentoren_recs:
        f = r["fields"]
        nps_list = sessions_by_mentor.get(r["id"], [])
        avg_nps  = round(sum(nps_list) / len(nps_list), 1) if nps_list else None
        rows.append({
            "id":              r["id"],
            "Name":            f.get("Name", ""),
            "E-Mail":          f.get("E-Mail", ""),
            "Stadt":           f.get("Stadt", ""),
            "Status":          f.get("Status", ""),
            "Spezialisierung": f.get("Spezialisierung", []),
            "Kapazität":       f.get("Kapazität pro Woche", 0),
            "Aktive Kunden":   kunden_count.get(r["id"], 0),
            "Sessions Count":  len(nps_list),
            "Avg NPS":         avg_nps,
        })
    return pd.DataFrame(rows)


def update_mentor(mentor_id: str, fields: dict) -> None:
    """Generic Mentor-Update für die Mentoren-Page Edit-Funktion."""
    _api().table(_base_id(), "Mentoren").update(mentor_id, fields)
    st.cache_data.clear()
