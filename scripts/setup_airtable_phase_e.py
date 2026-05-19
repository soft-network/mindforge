"""
Phase-E Airtable Setup
======================

Erweitert das Phase-1-Schema um Phase-E-Felder + Mentor-Tabelle + Sample-Daten.

Idempotent: kann mehrfach ausgeführt werden, bereits existierende Felder
werden übersprungen.

Aufruf:
    cd C:\\Users\\msi\\Desktop\\demoprojekt
    python scripts/setup_airtable_phase_e.py

Erwartete Env-Variablen (aus .env):
    AIRTABLE_PERSONAL_ACCESS_TOKEN
    AIRTABLE_BASE_ID
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib import request, error


# --- Env laden -------------------------------------------------------------

def load_env(path: Path) -> dict[str, str]:
    env = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


root = Path(__file__).resolve().parent.parent
env = load_env(root / ".env")

TOKEN = env.get("AIRTABLE_PERSONAL_ACCESS_TOKEN")
BASE_ID = env.get("AIRTABLE_BASE_ID")

if not TOKEN or not BASE_ID:
    sys.exit("ERROR: AIRTABLE_PERSONAL_ACCESS_TOKEN or AIRTABLE_BASE_ID missing in .env")

BASE_URL = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}"
DATA_URL = f"https://api.airtable.com/v0/{BASE_ID}"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}


# --- HTTP Helpers ----------------------------------------------------------

def http(method: str, url: str, body: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(body).encode("utf-8") if body else None
    req = request.Request(url, data=data, method=method, headers=HEADERS)
    try:
        with request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "{}")
    except error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8") or "{}")


def get_schema() -> dict:
    code, body = http("GET", f"{BASE_URL}/tables")
    if code != 200:
        sys.exit(f"Schema read failed: {code} {body}")
    return body


# --- Field- & Tabellen-Definitionen ---------------------------------------

# Zu Phase-1-Leads-Tabelle hinzuzufügende Felder
LEADS_FIELDS = [
    # 1a — Kontakt-Felder
    {"name": "First Name", "type": "singleLineText"},
    {"name": "Last Name",  "type": "singleLineText"},
    {"name": "Country", "type": "singleSelect", "options": {"choices": [
        {"name": "DE"}, {"name": "AT"}, {"name": "CH"}, {"name": "OTHER"},
    ]}},
    {"name": "Consent", "type": "checkbox", "options": {"icon": "check", "color": "greenBright"}},

    # 1b — 12 Quiz-Properties (einheitlich gepunktete Naming-Convention)
    {"name": "Quiz · Business Status", "type": "singleSelect", "options": {"choices": [
        {"name": "ja"}, {"name": "nein"},
    ]}},
    {"name": "Quiz · Years Self-Employed", "type": "singleSelect", "options": {"choices": [
        {"name": "lt_1"}, {"name": "1_3"}, {"name": "gt_3"},
    ]}},
    {"name": "Quiz · Business Field", "type": "singleSelect", "options": {"choices": [
        {"name": "coach"}, {"name": "services"}, {"name": "digital"},
        {"name": "ecommerce"}, {"name": "network"}, {"name": "other"},
    ]}},
    {"name": "Quiz · Visibility", "type": "singleSelect", "options": {"choices": [
        {"name": "lt_1k"}, {"name": "lt_10k"}, {"name": "gt_10k"},
    ]}},
    {"name": "Quiz · Team Setup", "type": "singleSelect", "options": {"choices": [
        {"name": "solo"}, {"name": "lt_10"}, {"name": "gt_10"},
    ]}},
    {"name": "Quiz · Monthly Revenue", "type": "singleSelect", "options": {"choices": [
        {"name": "zero"}, {"name": "lt_5k"}, {"name": "lt_10k"},
        {"name": "lt_100k"}, {"name": "gt_100k"},
    ]}},
    {"name": "Quiz · Main Wish", "type": "singleSelect", "options": {"choices": [
        {"name": "stable"}, {"name": "quit_job"}, {"name": "brand"},
        {"name": "freedom"}, {"name": "5fig"},
    ]}},
    {"name": "Quiz · Gap", "type": "multipleSelects", "options": {"choices": [
        {"name": "reach"}, {"name": "portfolio"}, {"name": "sales"},
        {"name": "clone"}, {"name": "mindset"},
    ]}},
    {"name": "Quiz · Time Budget", "type": "singleSelect", "options": {"choices": [
        {"name": "lt_1h"}, {"name": "2_5h"}, {"name": "5_10h"}, {"name": "gt_10h"},
    ]}},
    {"name": "Quiz Tier", "type": "singleSelect", "options": {"choices": [
        {"name": "hot",  "color": "redBright"},
        {"name": "warm", "color": "orangeBright"},
        {"name": "cold", "color": "blueBright"},
        {"name": "unqualified", "color": "grayBright"},
    ]}},
    {"name": "Quiz Completed At", "type": "dateTime",
     "options": {"timeZone": "Europe/Berlin",
                 "dateFormat": {"name": "iso"},
                 "timeFormat": {"name": "24hour"}}},

    # 1c — Tracking
    {"name": "Source Subdomain", "type": "singleLineText"},
    {"name": "Event ID", "type": "singleLineText"},
    {"name": "UTM Source", "type": "singleLineText"},
    {"name": "UTM Medium", "type": "singleLineText"},
    {"name": "UTM Campaign", "type": "singleLineText"},

    # 1d — HubSpot-Sync-Felder
    {"name": "Lifecycle Stage", "type": "singleSelect", "options": {"choices": [
        {"name": "lead"}, {"name": "marketingqualifiedlead"},
        {"name": "salesqualifiedlead"}, {"name": "opportunity"},
        {"name": "customer"}, {"name": "evangelist"}, {"name": "other"},
    ]}},
    {"name": "Lead Status", "type": "singleSelect", "options": {"choices": [
        {"name": "NEW"}, {"name": "OPEN"}, {"name": "IN_PROGRESS"},
        {"name": "OPEN_DEAL"}, {"name": "UNQUALIFIED"},
        {"name": "CONNECTED"}, {"name": "BAD_TIMING"},
    ]}},
    {"name": "HubSpot Owner", "type": "singleLineText"},
    {"name": "HubSpot Contact ID", "type": "singleLineText"},
    {"name": "HS Last Modified", "type": "dateTime",
     "options": {"timeZone": "Europe/Berlin",
                 "dateFormat": {"name": "iso"},
                 "timeFormat": {"name": "24hour"}}},

    # 1e — Conflict-Resolution
    {"name": "_source", "type": "singleLineText",
     "description": "quiz | hubspot-workflow | airtable-automation — verhindert Sync-Loops"},
]

# Sessions-Erweiterungen
SESSIONS_FIELDS = [
    {"name": "Duration (min)", "type": "number", "options": {"precision": 0}},
    {"name": "NPS", "type": "number", "options": {"precision": 0}},
    {"name": "Recording URL", "type": "url"},
]

# Clients-Erweiterungen
CLIENTS_FIELDS = [
    {"name": "Onboarding Status", "type": "singleSelect", "options": {"choices": [
        {"name": "Pending"}, {"name": "Welcome Pack Sent"},
        {"name": "Onboarding Call Done"}, {"name": "Activated"},
    ]}},
    {"name": "LTV", "type": "currency", "options": {"precision": 2, "symbol": "€"}},
]

# Mentors-Tabelle
MENTORS_TABLE = {
    "name": "Mentors",
    "description": "Inner-Circle-Mentoren mit Kapazität und Speciality",
    "fields": [
        {"name": "Name", "type": "singleLineText"},
        {"name": "Email", "type": "email"},
        {"name": "City", "type": "singleLineText"},
        {"name": "Capacity per Week", "type": "number", "options": {"precision": 0}},
        {"name": "Speciality", "type": "multipleSelects", "options": {"choices": [
            {"name": "Business"}, {"name": "Sales"}, {"name": "Mindset"},
            {"name": "Marketing"}, {"name": "Operations"}, {"name": "Finance"},
        ]}},
        {"name": "Status", "type": "singleSelect", "options": {"choices": [
            {"name": "Active", "color": "greenBright"},
            {"name": "Inactive", "color": "grayBright"},
            {"name": "On Leave", "color": "yellowBright"},
        ]}},
    ],
}

# Sample-Mentoren
MENTOR_RECORDS = [
    {"Name": "Bea Vogt",        "Email": "bea@mindforge.demo",     "City": "Stuttgart",  "Capacity per Week": 12, "Speciality": ["Business", "Sales"], "Status": "Active"},
    {"Name": "Finn Weiner",     "Email": "finn@mindforge.demo",    "City": "Berlin",     "Capacity per Week": 10, "Speciality": ["Marketing"],          "Status": "Active"},
    {"Name": "Jonas Spießbach", "Email": "jonas@mindforge.demo",   "City": "Hamburg",    "Capacity per Week": 10, "Speciality": ["Operations"],         "Status": "Active"},
    {"Name": "Sam Guezel",      "Email": "sam@mindforge.demo",     "City": "München",    "Capacity per Week": 12, "Speciality": ["Mindset"],            "Status": "Active"},
    {"Name": "Oguzhan Ünal",    "Email": "oguzhan@mindforge.demo", "City": "Köln",       "Capacity per Week": 8,  "Speciality": ["Sales"],              "Status": "Active"},
    {"Name": "Tina Eckert",     "Email": "tina@mindforge.demo",    "City": "Frankfurt",  "Capacity per Week": 10, "Speciality": ["Business"],           "Status": "Active"},
    {"Name": "Mischa Dieterle", "Email": "mischa@mindforge.demo",  "City": "Düsseldorf", "Capacity per Week": 8,  "Speciality": ["Marketing"],          "Status": "On Leave"},
    {"Name": "Jimmy Künzli",    "Email": "jimmy@mindforge.demo",   "City": "Zürich",     "Capacity per Week": 10, "Speciality": ["Finance"],            "Status": "Active"},
]


# --- Setup-Logik ----------------------------------------------------------

def ensure_field(table_id: str, table_name: str, field_def: dict, existing: set[str]) -> str:
    """Add a field if it doesn't already exist. Returns 'created' | 'exists'."""
    if field_def["name"] in existing:
        return "exists"
    code, body = http("POST", f"{BASE_URL}/tables/{table_id}/fields", field_def)
    if code in (200, 201):
        existing.add(field_def["name"])
        return "created"
    print(f"  !! Failed to create '{field_def['name']}' on {table_name}: HTTP {code} — {body.get('error', body)}")
    return "error"


def ensure_table(table_def: dict, schema: dict) -> tuple[str, str]:
    """Create table if it doesn't exist. Returns (table_id, status)."""
    for t in schema["tables"]:
        if t["name"] == table_def["name"]:
            return t["id"], "exists"
    code, body = http("POST", f"{BASE_URL}/tables", table_def)
    if code in (200, 201):
        return body["id"], "created"
    print(f"  !! Failed to create table '{table_def['name']}': HTTP {code} — {body.get('error', body)}")
    return "", "error"


def create_records(table_id: str, table_name: str, records: list[dict]) -> int:
    """Bulk-create records (max 10 per call). Returns count created."""
    total = 0
    for i in range(0, len(records), 10):
        chunk = records[i:i + 10]
        body = {"records": [{"fields": r} for r in chunk]}
        code, resp = http("POST", f"{DATA_URL}/{table_id}", body)
        if code in (200, 201):
            total += len(resp.get("records", []))
        else:
            print(f"  !! Failed to insert into {table_name}: HTTP {code} — {resp.get('error', resp)}")
    return total


def rename_field(table_id: str, table_name: str, old_name: str, new_name: str, schema: dict) -> str:
    field = next((f for f in next(t for t in schema["tables"] if t["id"] == table_id)["fields"] if f["name"] == old_name), None)
    if not field:
        return "absent"
    code, body = http("PATCH", f"{BASE_URL}/tables/{table_id}/fields/{field['id']}", {"name": new_name})
    if code in (200, 201):
        return "renamed"
    print(f"  !! Failed to rename {old_name} -> {new_name}: HTTP {code} — {body.get('error', body)}")
    return "error"


# --- Main -----------------------------------------------------------------

def main() -> None:
    print("=" * 70)
    print("Phase E · Airtable Schema Setup")
    print("=" * 70)

    schema = get_schema()
    tables_by_name = {t["name"]: t for t in schema["tables"]}

    # --- Leads erweitern ---
    leads = tables_by_name.get("Leads")
    if not leads:
        sys.exit("ERROR: 'Leads' table not found — Phase-1-Schema fehlt")
    leads_id = leads["id"]
    leads_existing = {f["name"] for f in leads["fields"]}

    # Phase-1-Feld 'Lead Score' umbenennen, bevor wir Quiz-Felder anlegen
    if "Lead Score" in leads_existing and "Quiz Score" not in leads_existing:
        print("\n[Leads] Renaming 'Lead Score' → 'Quiz Score'")
        result = rename_field(leads_id, "Leads", "Lead Score", "Quiz Score", schema)
        print(f"  -> {result}")
        if result == "renamed":
            leads_existing.discard("Lead Score")
            leads_existing.add("Quiz Score")

    # Wenn 'Quiz Score' weder als alter noch neuer Name da ist, hinzufügen
    if "Quiz Score" not in leads_existing:
        LEADS_FIELDS.append({
            "name": "Quiz Score",
            "type": "number",
            "options": {"precision": 0},
            "description": "Score 0-100 aus Quiz-Submit",
        })

    print(f"\n[Leads] Adding {len(LEADS_FIELDS)} fields…")
    counts = {"created": 0, "exists": 0, "error": 0}
    for f in LEADS_FIELDS:
        status = ensure_field(leads_id, "Leads", f, leads_existing)
        counts[status] += 1
        print(f"  {status:8s} {f['name']}")
        time.sleep(0.15)  # gentle rate-limit
    print(f"  → Leads: {counts['created']} created, {counts['exists']} already existed, {counts['error']} errors")

    # --- Sessions erweitern ---
    sessions = tables_by_name.get("Sessions")
    if sessions:
        sess_id = sessions["id"]
        sess_existing = {f["name"] for f in sessions["fields"]}
        print(f"\n[Sessions] Adding {len(SESSIONS_FIELDS)} fields…")
        counts = {"created": 0, "exists": 0, "error": 0}
        for f in SESSIONS_FIELDS:
            status = ensure_field(sess_id, "Sessions", f, sess_existing)
            counts[status] += 1
            print(f"  {status:8s} {f['name']}")
            time.sleep(0.15)
        print(f"  → Sessions: {counts['created']} created, {counts['exists']} already existed, {counts['error']} errors")

    # --- Clients erweitern ---
    clients = tables_by_name.get("Clients")
    if clients:
        cli_id = clients["id"]
        cli_existing = {f["name"] for f in clients["fields"]}
        print(f"\n[Clients] Adding {len(CLIENTS_FIELDS)} fields…")
        counts = {"created": 0, "exists": 0, "error": 0}
        for f in CLIENTS_FIELDS:
            status = ensure_field(cli_id, "Clients", f, cli_existing)
            counts[status] += 1
            print(f"  {status:8s} {f['name']}")
            time.sleep(0.15)
        print(f"  → Clients: {counts['created']} created, {counts['exists']} already existed, {counts['error']} errors")

    # --- Mentors-Tabelle ---
    print(f"\n[Mentors] Creating table…")
    mentors_id, status = ensure_table(MENTORS_TABLE, schema)
    print(f"  -> {status} (id={mentors_id})")
    if status == "exists":
        # nachladen
        schema2 = get_schema()
        mentors = next((t for t in schema2["tables"] if t["id"] == mentors_id), None)
        existing = {f["name"] for f in (mentors or {}).get("fields", [])}
        for f in MENTORS_TABLE["fields"]:
            if f["name"] not in existing:
                ensure_field(mentors_id, "Mentors", f, existing)

    # Sample-Mentoren einfügen, wenn Tabelle leer
    if mentors_id:
        code, resp = http("GET", f"{DATA_URL}/{mentors_id}?maxRecords=1")
        if code == 200 and not resp.get("records"):
            print(f"  Inserting {len(MENTOR_RECORDS)} sample mentors…")
            n = create_records(mentors_id, "Mentors", MENTOR_RECORDS)
            print(f"  → {n} mentors inserted")
        else:
            print(f"  Mentors table already has records — skipping seed")

    print("\n" + "=" * 70)
    print("Phase E Airtable Setup · DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
