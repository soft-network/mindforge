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

@st.cache_data(ttl=120)
def load_mentor_lookup() -> dict[str, str]:
    """Mentor-RecordId → Name lookup, zentral genutzt von load_leads + load_kunden.

    Eigener Cache (TTL 120s) damit nicht jeder Loader die Mentoren-Tabelle pullt.
    """
    return {
        r["id"]: r["fields"].get("Name", "—")
        for r in _api().table(_base_id(), "Mentoren").all()
    }


@st.cache_data(ttl=60)
def load_leads() -> pd.DataFrame:
    """Alle Leads ohne Filter — für Dashboard- und Leads-Page.

    Inkl. Mentor-Zuweisung (optional): `Mentor` enthält die Airtable-RecordIds,
    `Mentor Name` ist der aufgelöste Name fürs UI.
    """
    records = _api().table(_base_id(), "Leads").all()
    mentor_names = load_mentor_lookup()
    rows = []
    for rec in records:
        f = rec["fields"]
        mref = f.get("Mentor", [])
        mid  = mref[0] if isinstance(mref, list) and mref else None
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
            "Mentor":       mref,
            "Mentor Name":  mentor_names.get(mid, "—") if mid else "—",
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df["Erstellt am"] = pd.to_datetime(df["Erstellt am"], errors="coerce", utc=True)
        df["Termin am"]   = pd.to_datetime(df["Termin am"],   errors="coerce", utc=True)
    return df


@st.cache_data(ttl=300)
def load_programs() -> pd.DataFrame:
    """Alle Programme — für Programme-Page und Convert-Workflow.

    Inkl. Mentor-Pool (Multi-Link) und aufgelöste Namen für die UI.
    """
    records = _api().table(_base_id(), "Programme").all()
    mentor_names = load_mentor_lookup()
    rows = []
    for rec in records:
        f = rec["fields"]
        mentor_pool = f.get("Mentoren", []) or []
        rows.append({
            "id":                 rec["id"],
            "Name":                f.get("Name", ""),
            "Category":            f.get("Category", ""),
            "Price (EUR)":         f.get("Price (EUR)", 0),
            "Lead Count":          f.get("Lead Count", 0),
            "Converted Kunden":    f.get("Converted Clients", 0) or f.get("Converted Kunden", 0),
            "Mentoren":            mentor_pool,
            "Mentor-Pool-Namen":   [mentor_names.get(mid, "?") for mid in mentor_pool],
        })
    return pd.DataFrame(rows)


def update_programm(programm_id: str, fields: dict) -> None:
    """Generic Programm-Update — primär für Mentor-Pool-Zuweisung."""
    _api().table(_base_id(), "Programme").update(programm_id, fields, typecast=True)
    load_programs.clear()


# -----------------------------------------------------------------------------
# Convert-Workflow — Lead → Kunde mit Auto-Mentor-Routing
# Wird von der Sales-Strategiegespräche-Page benutzt.
# -----------------------------------------------------------------------------

def pick_least_loaded_mentor(pool_ids: list[str]) -> Optional[str]:
    """Wählt aus einem Mentor-Pool den Mentor mit niedrigster Auslastung.

    Auslastung = aktive_kunden / kapazität. Berücksichtigt nur Active-Status.
    Bei Gleichstand: alphabetisch deterministisch.
    """
    if not pool_ids:
        return None

    df_mentoren = load_mentoren()
    if df_mentoren.empty:
        return None

    pool_df = df_mentoren[df_mentoren["id"].isin(pool_ids)]
    pool_df = pool_df[pool_df["Status"] == "Active"]
    if pool_df.empty:
        return None

    pool_df = pool_df.copy()
    pool_df["Auslastung"] = pool_df.apply(
        lambda r: (r["Aktive Kunden"] / r["Kapazität"]) if r["Kapazität"] else 1.0,
        axis=1,
    )
    pool_df = pool_df.sort_values(["Auslastung", "Name"], ascending=[True, True])
    return pool_df.iloc[0]["id"]


def convert_lead_to_kunde(
    lead_id: str,
    lead_name: str,
    programm_name: str,
    mentor_id: Optional[str] = None,
    mrr_eur: float = 0.0,
    converted_by_email: Optional[str] = None,
) -> tuple[dict, str]:
    """Konvertiert einen Lead in einen Kunden-Record.

    Wenn `mentor_id` None ist, wird automatisch der am wenigsten ausgelastete
    Mentor aus `Programme.Mentoren` gewählt.

    Returns:
        (kunde_record, gewaehlter_mentor_id) — beide auch wenn Mentor leer

    Side-Effects:
        - Lead.Status = 'Converted'
        - Caches invalidiert (Leads, Kunden, Mentoren)
    """
    from datetime import date

    if not lead_id or not lead_name:
        raise ValueError("lead_id und lead_name sind Pflicht.")
    if not programm_name:
        raise ValueError("Programm muss gewählt werden.")

    # Falls Mentor nicht gegeben: Auto-Routing aus Programm-Pool
    chosen_mentor_id = mentor_id
    if not chosen_mentor_id:
        # Programm-Record finden
        df_prog = load_programs()
        match = df_prog[df_prog["Name"] == programm_name]
        if not match.empty:
            pool = match.iloc[0]["Mentoren"] or []
            chosen_mentor_id = pick_least_loaded_mentor(pool)

    # Kunden-Record anlegen
    kunde_fields = {
        "Lead":              lead_name,
        "Program":           programm_name,
        "Start Date":        date.today().isoformat(),
        "MRR (EUR)":         float(mrr_eur),
        "LTV":               0.0,
        "Status":            "Active",
        "Onboarding Status": "Pending",
    }
    if chosen_mentor_id:
        kunde_fields["Mentor"] = [chosen_mentor_id]

    kunde_rec = _api().table(_base_id(), "Kunden").create(
        kunde_fields, typecast=True,
    )

    # Lead-Status auf Converted setzen
    lead_patch = {"Status": "Converted"}
    if chosen_mentor_id:
        lead_patch["Mentor"] = [chosen_mentor_id]
    _api().table(_base_id(), "Leads").update(lead_id, lead_patch, typecast=True)

    # Caches invalidieren — alle drei betroffen
    load_leads.clear()
    load_kunden.clear()
    load_mentoren.clear()

    return kunde_rec, chosen_mentor_id or ""


def update_lead(lead_id: str, fields: dict) -> None:
    """Generic Lead-Update für die Leads-Page Edit-Funktion.

    typecast=True für robustes Schreiben — z.B. wenn Mentor-Zuweisung als
    String-Name statt RecordId reinkommt (Airtable löst dann selbst auf).
    """
    _api().table(_base_id(), "Leads").update(lead_id, fields, typecast=True)
    load_leads.clear()  # gezielte Invalidation statt globalem clear()


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


# -----------------------------------------------------------------------------
# Kunden (Customer Success Page)
#
# Joins:
#   Letzte Session  = max(Sessions.Date)  where Sessions.Lead == Kunden.Lead
#   Health Score    = lib.health.compute_health_score(Letzte Session)
#   Mentor Name     = Mentoren.Name lookup über Kunden.Mentor (Link)
#
# Sessions↔Kunden über Lead-Text-Feld gejoint, weil weder Sessions noch Kunden
# einen direkten Link untereinander haben. Sessions.Lead und Kunden.Lead sind
# beide Text. Funktioniert sauber, solange Lead-Namen eindeutig sind (Demo-OK).
# -----------------------------------------------------------------------------

@st.cache_data(ttl=120)
def load_kunden() -> pd.DataFrame:
    """Lade Kunden mit Joins für Letzte Session, Health Score, Mentor-Name."""
    from lib.health import compute_health_score, health_tier, health_emoji

    base = _base_id()
    kunden_recs   = _api().table(base, "Kunden").all()
    sessions_recs = _api().table(base, "Sessions").all()

    if not kunden_recs:
        return pd.DataFrame(columns=[
            "id", "Lead", "Program", "Status", "Onboarding Status",
            "MRR (EUR)", "LTV", "Start Date", "Mentor", "Mentor Name",
            "Letzte Session", "Health Score", "Health Tier", "Health Emoji",
        ])

    # Mentor-Name-Lookup über zentralen Helper (cached, geteilt mit load_leads)
    mentor_name_by_id = load_mentor_lookup()

    # Sessions: Lead-Text → Liste von Dates
    sessions_by_lead: dict[str, list[pd.Timestamp]] = {}
    for r in sessions_recs:
        lead = r["fields"].get("Lead")
        date = r["fields"].get("Date")
        if lead and date:
            ts = pd.to_datetime(date, errors="coerce", utc=True)
            if pd.notna(ts):
                sessions_by_lead.setdefault(lead, []).append(ts)

    now = pd.Timestamp.now(tz="UTC")
    rows = []
    for rec in kunden_recs:
        f = rec["fields"]
        mref = f.get("Mentor", [])
        mid  = mref[0] if isinstance(mref, list) and mref else None
        lead = f.get("Lead", "")

        last_sess_list = sessions_by_lead.get(lead, [])
        last_session = max(last_sess_list) if last_sess_list else pd.NaT
        score = compute_health_score(last_session, now=now)

        rows.append({
            "id":                rec["id"],
            "Lead":              lead,
            "Program":           f.get("Program", ""),
            "Status":            f.get("Status", "Active"),
            "Onboarding Status": f.get("Onboarding Status", "Pending"),
            "MRR (EUR)":         f.get("MRR (EUR)", 0) or 0,
            "LTV":               f.get("LTV", 0) or 0,
            "Start Date":        f.get("Start Date"),
            "Mentor":            mref,
            "Mentor Name":       mentor_name_by_id.get(mid, "—") if mid else "—",
            "Letzte Session":    last_session,
            "Health Score":      score,
            "Health Tier":       health_tier(score),
            "Health Emoji":      health_emoji(score),
        })
    df = pd.DataFrame(rows)
    df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce")
    return df


def update_kunde(kunde_id: str, fields: dict) -> None:
    """Generic Kunde-Update für die Customer-Success-Page Edit-Funktion.

    Nutzt typecast=True damit Airtable fehlende Select-Werte (z.B. neue
    Status-Options wie 'Paused', 'Churned') beim ersten Schreiben automatisch
    anlegt — die Meta-API erlaubt kein PATCH von Select-Choices, dieser
    Weg ist der saubere Workaround.
    """
    _api().table(_base_id(), "Kunden").update(kunde_id, fields, typecast=True)
    load_kunden.clear()  # gezielte Cache-Invalidation statt globalem clear()


# -----------------------------------------------------------------------------
# Benutzer-Verwaltung (Hauptadmin-Page)
# Wichtig: Passwörter werden NIE im Klartext gespeichert — immer durch
# lib.auth_security.hash_password() laufen lassen vor dem Schreiben.
# -----------------------------------------------------------------------------

@st.cache_data(ttl=60)
def load_benutzer() -> pd.DataFrame:
    """Alle Benutzer für die Admin-Verwaltungsseite.

    Auflösung: Mentor-Link (RecordId) → Mentor-Name über load_mentor_lookup().
    Passwort-Hash wird NICHT in den DataFrame geladen (Sicherheits-Hygiene).
    """
    records = _api().table(_base_id(), "Benutzer").all()
    if not records:
        return pd.DataFrame(columns=[
            "id", "Name", "E-Mail", "Rolle", "Status",
            "Mentor-Link", "Mentor Name",
            "Letzte Anmeldung", "Angelegt am", "Angelegt von",
        ])

    mentor_names = load_mentor_lookup()
    rows = []
    for rec in records:
        f = rec["fields"]
        mref = f.get("Mentor-Link", [])
        mid  = mref[0] if isinstance(mref, list) and mref else None
        rows.append({
            "id":               rec["id"],
            "Name":             f.get("Name", ""),
            "E-Mail":           f.get("E-Mail", ""),
            "Rolle":            f.get("Rolle", ""),
            "Status":           f.get("Status", "Active"),
            "Mentor-Link":      mref,
            "Mentor Name":      mentor_names.get(mid, "—") if mid else "—",
            "Letzte Anmeldung": f.get("Letzte Anmeldung"),
            "Angelegt am":      f.get("Angelegt am"),
            "Angelegt von":     f.get("Angelegt von", ""),
        })
    df = pd.DataFrame(rows)
    df["Letzte Anmeldung"] = pd.to_datetime(df["Letzte Anmeldung"], errors="coerce", utc=True)
    df["Angelegt am"]      = pd.to_datetime(df["Angelegt am"],      errors="coerce")
    return df


def create_benutzer(
    name: str,
    email: str,
    password: str,
    rolle: str,
    mentor_id: Optional[str] = None,
    angelegt_von: Optional[str] = None,
) -> dict:
    """Legt einen neuen Benutzer-Record in Airtable an.

    Validiert minimal:
        - Email nicht leer
        - Passwort nicht leer
        - Rolle in {Hauptadmin, Sales, Mentor}
        - Wenn Rolle=Mentor: mentor_id Pflicht

    Wirft ValueError bei Validierungs-Fehlern.
    Wirft RuntimeError wenn Email bereits existiert.
    """
    from datetime import date
    from lib.auth_security import hash_password

    email = email.strip().lower()
    name  = name.strip()
    if not name:
        raise ValueError("Name darf nicht leer sein.")
    if not email:
        raise ValueError("Email darf nicht leer sein.")
    if not password:
        raise ValueError("Passwort darf nicht leer sein.")
    if rolle not in ("Hauptadmin", "Sales", "Mentor"):
        raise ValueError(f"Ungültige Rolle: {rolle!r}.")
    if rolle == "Mentor" and not mentor_id:
        raise ValueError("Für Rolle 'Mentor' ist ein Mentor-Link Pflicht.")

    # Email-Eindeutigkeit prüfen
    tbl = _api().table(_base_id(), "Benutzer")
    existing = tbl.all(formula=f"LOWER({{E-Mail}})='{email}'")
    if existing:
        raise RuntimeError(f"Email {email!r} ist bereits vergeben.")

    fields: dict = {
        "Name":          name,
        "E-Mail":        email,
        "Passwort-Hash": hash_password(password),
        "Rolle":         rolle,
        "Status":        "Active",
        "Angelegt am":   date.today().isoformat(),
        "Angelegt von":  (angelegt_von or "").strip().lower(),
    }
    if mentor_id:
        fields["Mentor-Link"] = [mentor_id]

    rec = tbl.create(fields)
    load_benutzer.clear()
    return rec


def update_benutzer(user_id: str, fields: dict) -> None:
    """Generic User-Update (Name, Rolle, Status, Mentor-Link).

    Passwort wird über reset_user_password() gesetzt (separater Pfad —
    der ruft hash_password vor dem Schreiben auf).
    """
    if "Passwort-Hash" in fields:
        raise ValueError(
            "Passwort-Hash niemals direkt setzen — reset_user_password() benutzen."
        )
    _api().table(_base_id(), "Benutzer").update(user_id, fields, typecast=True)
    load_benutzer.clear()


def reset_user_password(user_id: str, new_password: str) -> None:
    """Setzt das Passwort eines Benutzers neu. Hashed bevor geschrieben wird."""
    from lib.auth_security import hash_password

    if not new_password:
        raise ValueError("Passwort darf nicht leer sein.")
    _api().table(_base_id(), "Benutzer").update(
        user_id,
        {"Passwort-Hash": hash_password(new_password)},
    )
    load_benutzer.clear()


# -----------------------------------------------------------------------------
# Sessions — Loader + Writer für Mentor-Sessions-Page
# -----------------------------------------------------------------------------

@st.cache_data(ttl=60)
def load_sessions() -> pd.DataFrame:
    """Alle Sessions mit Mentor-Name-Lookup.

    Mentor-Filter passiert clientside in der Mentor-Page via for_mentor().
    """
    records = _api().table(_base_id(), "Sessions").all()
    if not records:
        return pd.DataFrame(columns=[
            "id", "Session ID", "Lead", "Date", "Outcome", "Notizen",
            "Dauer (min)", "NPS", "Aufnahme-URL", "Mentor", "Mentor Name",
        ])

    mentor_names = load_mentor_lookup()
    rows = []
    for rec in records:
        f = rec["fields"]
        mref = f.get("Mentor", [])
        mid  = mref[0] if isinstance(mref, list) and mref else None
        rows.append({
            "id":           rec["id"],
            "Session ID":   f.get("Session ID"),
            "Lead":         f.get("Lead", ""),
            "Date":         f.get("Date"),
            "Outcome":      f.get("Outcome", ""),
            "Notizen":      f.get("Notizen", ""),
            "Dauer (min)":  f.get("Dauer (min)", 0) or 0,
            "NPS":          f.get("NPS"),
            "Aufnahme-URL": f.get("Aufnahme-URL", ""),
            "Mentor":       mref,
            "Mentor Name":  mentor_names.get(mid, "—") if mid else "—",
        })
    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce", utc=True)
    return df


def add_session(
    mentor_id: str,
    lead_name: str,
    date_iso: str,
    dauer_min: int,
    outcome: str,
    notiz: str = "",
    nps: Optional[int] = None,
    aufnahme_url: str = "",
) -> dict:
    """Trägt eine neue Session ein.

    Args:
        mentor_id:   Airtable-RecordId des Mentors (z.B. 'rec...')
        lead_name:   Lead-Text-Wert (so wie er auch in Kunden.Lead steht)
        date_iso:    ISO-DateTime-String inkl. Timezone (z.B. '2026-05-22T14:30:00+02:00')
        dauer_min:   Session-Dauer in Minuten
        outcome:     Single-Select-Wert (z.B. 'Erfolg', 'Folgetermin', 'Eskalation')
        notiz:       optionale freie Notiz
        nps:         0-10, optional (wenn kein Feedback vorliegt)
        aufnahme_url: optionaler Recording-Link
    """
    if not mentor_id:
        raise ValueError("mentor_id ist Pflicht.")
    if not lead_name:
        raise ValueError("Lead-Name ist Pflicht (muss zu einem Mentee passen).")
    if dauer_min < 1:
        raise ValueError("Dauer muss positiv sein.")
    if nps is not None and not (0 <= nps <= 10):
        raise ValueError("NPS muss zwischen 0 und 10 sein.")

    fields: dict = {
        "Mentor":      [mentor_id],
        "Lead":        lead_name,
        "Date":        date_iso,
        "Dauer (min)": int(dauer_min),
        "Outcome":     outcome,
    }
    if notiz.strip():
        fields["Notizen"] = notiz.strip()
    if nps is not None:
        fields["NPS"] = int(nps)
    if aufnahme_url.strip():
        fields["Aufnahme-URL"] = aufnahme_url.strip()

    rec = _api().table(_base_id(), "Sessions").create(fields, typecast=True)
    # Cache invalidieren — Sessions, Kunden (Letzte Session ändert sich),
    # Mentoren (Avg NPS ändert sich)
    load_sessions.clear()
    load_kunden.clear()
    load_mentoren.clear()
    return rec


def update_session(session_id: str, fields: dict) -> None:
    """Korrigiert eine Session — typecast=True für Outcome-Werte."""
    _api().table(_base_id(), "Sessions").update(session_id, fields, typecast=True)
    load_sessions.clear()
    load_kunden.clear()
    load_mentoren.clear()


# -----------------------------------------------------------------------------
# Self-Scope-Helpers — werden von Mentor-/Sales-Pages konsumiert,
# um DataFrames auf die eigene Person zu filtern.
# -----------------------------------------------------------------------------

def for_mentor(df: pd.DataFrame, mentor_id: str, link_col: str = "Mentor") -> pd.DataFrame:
    """Filtert ein DataFrame auf Zeilen wo `link_col` den `mentor_id` enthält.

    `link_col` enthält Listen von RecordIds (Airtable Multi-Link), oder
    einzelne IDs. Beide Formen werden behandelt.
    """
    if df.empty or link_col not in df.columns:
        return df

    def has_id(val) -> bool:
        if isinstance(val, list):
            return mentor_id in val
        return val == mentor_id

    return df[df[link_col].apply(has_id)]


def get_mentor_record(mentor_id: str) -> Optional[dict]:
    """Lade einen einzelnen Mentor-Record direkt aus Airtable (uncached)."""
    if not mentor_id:
        return None
    try:
        return _api().table(_base_id(), "Mentoren").get(mentor_id)
    except Exception:  # noqa: BLE001
        return None
