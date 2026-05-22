"""Demo-Daten Seed-Skript — reproduzierbar.

Setzt die aktuellen Demo-Daten so, wie sie für die Welle-4/5/6-Showcases
gebraucht werden. Idempotent: einzelne Records werden nur aktualisiert
wenn nötig.

Inhalt:
    1. Sessions: Mentor-Refs + NPS auf die 13 vorhandenen Records
    2. Kunden:   Mentor-Zuweisung auf 4 vorhandene Records
    3. Programme.Mentoren: Pool-Mapping (Spezialisierungs-basiert)

Was NICHT angelegt wird:
    - Mentoren-Stamm (8 Records — manuell in Airtable angelegt)
    - Leads (46 Records — kommen über Quiz-Funnel rein)
    - Programme (5 Records — manuell angelegt)
    - Benutzer (Hauptadmin per scripts/seed_first_admin.py,
      Sales/Mentor per UI)

Verwendung (aus streamlit-app/):
    uv run python scripts/seed_demo.py

Wirft Exception bei Connection-Issues oder fehlender Tabelle.
"""

from __future__ import annotations

import os
import sys
import tomllib
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
APP_DIR  = THIS_DIR.parent
sys.path.insert(0, str(APP_DIR))

from pyairtable import Api


# -----------------------------------------------------------------------------
# Mentor-Map (Stamm-IDs in Airtable) — bewusst hier hardcoded, weil die
# Records seit Setup stabil sind. Wenn du die Mentoren-Tabelle reinitialisierst,
# dann diese IDs aus Airtable neu kopieren.
# -----------------------------------------------------------------------------

MENTORS = {
    "Bea":     "recjqV5TsYmj9NDrR",  # Business, Sales — Top-Performer
    "Tina":    "rec8JRtnOJ7KV9lAF",  # Business
    "Sam":     "recA8XYeMwHLLD1xY",  # Mindset
    "Finn":    "rec2K3HBd8aEqycWM",  # Marketing
    "Jonas":   "recXLt8SFsJREreXn",  # Operations
    "Oguzhan": "rec6QcrmdtZIJADUU",  # Sales
    "Jimmy":   "rec2qOFVKS6S4DfjG",  # Finance
    "Mischa":  "recnPFzgX5eV4hHhr",  # Marketing — On Leave (Demo-Story)
}


# Demo-Story: Bea = Top-Performer (3 Sessions, NPS 9.7),
# Sam/Tina = stark (NPS 9.5/8.5), Mischa = On Leave (1 Session, NPS 7)
SESSION_PLAN: list[tuple[str, int]] = [
    ("Bea",     10),
    ("Bea",      9),
    ("Bea",     10),
    ("Tina",     9),
    ("Tina",     8),
    ("Sam",     10),
    ("Sam",      9),
    ("Finn",     7),
    ("Oguzhan",  8),
    ("Oguzhan",  8),
    ("Jonas",    8),
    ("Jimmy",    9),
    ("Mischa",   7),
]

# Kunden → Mentor (Lead-Name als Match-Key)
KUNDEN_PLAN: list[tuple[str, str]] = [
    ("Tobias Schmidt", "Bea"),
    ("Markus Fischer", "Tina"),
    ("Anna Müller",    "Sam"),
    ("Felix Bauer",    "Oguzhan"),
]

# Mentor-Pool pro Programm — nach Spezialisierung
PROGRAM_POOLS: dict[str, list[str]] = {
    "Business Accelerator": ["Bea", "Tina", "Oguzhan"],  # Business + Sales
    "Mindful Leadership":   ["Sam"],                     # Mindset
    "Career Boost":         ["Finn", "Jonas", "Jimmy"],  # Marketing/Ops/Finance
    # Health Reset + Life Compass werden bewusst leer gelassen — Admin
    # kann sie über die UI-Programme-Page zuweisen, wenn er möchte.
}


def load_secrets() -> dict:
    secrets_path = APP_DIR / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        print(f"  FEHLER: {secrets_path} nicht gefunden.")
        sys.exit(1)
    with secrets_path.open("rb") as f:
        return tomllib.load(f)


def main() -> None:
    secrets = load_secrets()
    token = secrets.get("AIRTABLE_API_TOKEN") or os.environ.get("AIRTABLE_API_TOKEN")
    base  = secrets.get("AIRTABLE_BASE_ID")   or os.environ.get("AIRTABLE_BASE_ID")
    if not token or not base:
        print("  FEHLER: AIRTABLE_API_TOKEN / AIRTABLE_BASE_ID fehlen.")
        sys.exit(1)

    api = Api(token)

    # -------------------------------------------------------------------------
    # 1) Sessions
    # -------------------------------------------------------------------------
    print("=" * 60)
    print(" SESSIONS")
    print("=" * 60)
    sessions = api.table(base, "Sessions").all()
    print(f"  Found {len(sessions)} sessions in Airtable")
    if len(sessions) != len(SESSION_PLAN):
        print(f"  WARN: erwartet {len(SESSION_PLAN)} Sessions, gefunden {len(sessions)}.")
        print(f"  Skript verteilt nur auf die ersten {min(len(sessions), len(SESSION_PLAN))}.")
    tbl_s = api.table(base, "Sessions")
    for rec, (mentor_key, nps) in zip(sessions, SESSION_PLAN):
        cur_mentor = rec["fields"].get("Mentor", [])
        cur_nps    = rec["fields"].get("NPS")
        target_id  = MENTORS[mentor_key]
        if cur_mentor == [target_id] and cur_nps == nps:
            print(f"  skip   {rec['id']}  ({mentor_key:<8} NPS={nps}) — bereits gesetzt")
            continue
        tbl_s.update(rec["id"], {"Mentor": [target_id], "NPS": nps})
        print(f"  patch  {rec['id']}  -> {mentor_key:<8} NPS={nps}")

    # -------------------------------------------------------------------------
    # 2) Kunden
    # -------------------------------------------------------------------------
    print()
    print("=" * 60)
    print(" KUNDEN")
    print("=" * 60)
    kunden = api.table(base, "Kunden").all()
    plan_by_lead = dict(KUNDEN_PLAN)
    tbl_k = api.table(base, "Kunden")
    for rec in kunden:
        lead = rec["fields"].get("Lead", "")
        target_key = plan_by_lead.get(lead)
        if not target_key:
            print(f"  skip   {lead:<22} (nicht im Plan)")
            continue
        target_id = MENTORS[target_key]
        cur_mentor = rec["fields"].get("Mentor", [])
        if cur_mentor == [target_id]:
            print(f"  skip   {lead:<22} -> {target_key} (bereits gesetzt)")
            continue
        tbl_k.update(rec["id"], {"Mentor": [target_id]})
        print(f"  patch  {lead:<22} -> {target_key}")

    # -------------------------------------------------------------------------
    # 3) Programme.Mentoren (Pools)
    # -------------------------------------------------------------------------
    print()
    print("=" * 60)
    print(" PROGRAMME.MENTOREN (Pools)")
    print("=" * 60)
    programs = api.table(base, "Programme").all()
    tbl_p = api.table(base, "Programme")
    for p in programs:
        name = p["fields"].get("Name")
        pool_keys = PROGRAM_POOLS.get(name)
        if pool_keys is None:
            print(f"  skip   {name!r}  (kein Pool im Plan)")
            continue
        target_ids = [MENTORS[k] for k in pool_keys]
        cur_ids = p["fields"].get("Mentoren", [])
        if sorted(cur_ids) == sorted(target_ids):
            print(f"  skip   {name!r}  -> {pool_keys} (bereits gesetzt)")
            continue
        tbl_p.update(p["id"], {"Mentoren": target_ids})
        print(f"  patch  {name!r}  -> {pool_keys}")

    print()
    print("Done.")


if __name__ == "__main__":
    main()
