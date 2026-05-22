"""Seed-Skript für den allerersten Hauptadmin in der Benutzer-Tabelle.

Henne-Ei-Problem: Vor dem ersten Login ist die Tabelle leer. Dieses Skript
legt einen Initial-Hauptadmin an, mit dem du dich anschließend per UI
einloggen kannst. Danach läuft die User-Verwaltung über die Admin-Page.

Verwendung (einmalig, aus streamlit-app/):
    python scripts/seed_first_admin.py \
        --name "Chaouki" \
        --email "net24.twork@gmail.com" \
        --password "DeinSicheresPasswort"

Idempotent: läuft das Skript ein zweites Mal mit derselben Email,
wird nichts überschrieben (Schutz vor versehentlichem Reset).
"""

from __future__ import annotations

import argparse
import os
import sys
import tomllib
from datetime import date, datetime
from pathlib import Path

# In Repo-Root suchen damit lib/ importierbar ist
THIS_DIR = Path(__file__).resolve().parent
APP_DIR  = THIS_DIR.parent
sys.path.insert(0, str(APP_DIR))

from pyairtable import Api

from lib.auth_security import hash_password


def load_secrets() -> dict:
    """Lädt .streamlit/secrets.toml für AIRTABLE-Creds."""
    secrets_path = APP_DIR / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        print(f"  FEHLER: {secrets_path} nicht gefunden.")
        sys.exit(1)
    with secrets_path.open("rb") as f:
        return tomllib.load(f)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Initial-Hauptadmin in Airtable.Benutzer")
    parser.add_argument("--name",     required=True, help="Anzeigename, z.B. 'Chaouki'")
    parser.add_argument("--email",    required=True, help="Login-Email, z.B. 'net24.twork@gmail.com'")
    parser.add_argument("--password", required=True, help="Initial-Passwort (User soll es später ändern)")
    args = parser.parse_args()

    secrets = load_secrets()
    token = secrets.get("AIRTABLE_API_TOKEN") or os.environ.get("AIRTABLE_API_TOKEN")
    base  = secrets.get("AIRTABLE_BASE_ID")   or os.environ.get("AIRTABLE_BASE_ID")
    if not token or not base:
        print("  FEHLER: AIRTABLE_API_TOKEN / AIRTABLE_BASE_ID fehlen in secrets.toml")
        sys.exit(1)

    api = Api(token)
    tbl = api.table(base, "Benutzer")
    email_norm = args.email.strip().lower()

    # Idempotenz-Check
    existing = tbl.all(formula=f"LOWER({{E-Mail}})='{email_norm}'")
    if existing:
        print(f"  Hinweis: User mit Email {email_norm!r} existiert bereits.")
        print(f"  Record-ID: {existing[0]['id']}")
        print("  Skript bricht ab. Passwort-Reset über die Streamlit-UI machen.")
        sys.exit(0)

    print(f"  Hash Passwort (bcrypt cost=12) ...")
    pwd_hash = hash_password(args.password)

    print(f"  Lege Hauptadmin an: {args.name} <{email_norm}>")
    rec = tbl.create({
        "Name":          args.name,
        "E-Mail":        args.email,
        "Passwort-Hash": pwd_hash,
        "Rolle":         "Hauptadmin",
        "Status":        "Active",
        "Angelegt am":   date.today().isoformat(),
        "Angelegt von":  "seed-script",
    })
    print(f"  OK — Record-ID: {rec['id']}")
    print()
    print(f"  Du kannst dich jetzt einloggen:")
    print(f"     Email:    {args.email}")
    print(f"     Passwort: (das gerade übergebene)")
    print()
    print(f"  Wichtig: Wechsel das Passwort sobald die Benutzer-Page läuft.")


if __name__ == "__main__":
    main()
