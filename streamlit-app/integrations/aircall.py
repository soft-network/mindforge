"""Aircall Click-to-Call Integration — DOKUMENTIERTER STUB.

Dieses Modul ist absichtlich ein Stub. Aircall hat keinen Free-Tier
(~30 €/Setter/Monat), daher läuft das Demo nicht gegen einen echten
Account. Die Streamlit-Setter-Daily-Page fällt auf `tel:`-Links zurück,
solange dieser Stub aktiv ist — der UX-Flow wird trotzdem demonstriert.

Aktivierung
-----------
1. Datei umbenennen `aircall.py.stub` → `aircall.py` und `requests` zu
   pyproject.toml hinzufügen.
2. Secrets in `.streamlit/secrets.toml`:

       [aircall]
       api_id    = "..."
       api_token = "..."

3. Aircall user_id pro Setter einmal über die Users-API auslesen und
   z.B. auf dem Mentoren/Setter-Airtable-Datensatz speichern.

API-Referenz
------------
- Anruf an Nummer vom Softphone eines Setters starten:
    POST https://api.aircall.io/v1/users/{user_id}/dial
    Body: {"to": "+49170…"}
- Der Aircall-Softphone-Client des Setters klingelt, dann wird die
  Nummer gewählt.

Webhooks (call.created / call.answered / call.hungup / call.ended)
können nicht direkt von Streamlit empfangen werden. Die produktive
Verkabelung wäre:
    Aircall webhook → Make-Szenario → Airtable-Update (Termin am, Dauer, Aufnahme-URL)

Quellen
-------
- https://developer.aircall.io/api-references/#dial-a-phone-number
- https://developer.aircall.io/api-references/#users
"""

from __future__ import annotations


def dial(user_id: int, to: str) -> dict:
    """Stub. Produktiv: POST /v1/users/{user_id}/dial mit JSON {"to": ...}.

    Liefert eine Fake-Response, damit die Streamlit-Page den Happy-Path
    ohne echten Aircall-Account demonstrieren kann.
    """
    return {
        "status":  "stub",
        "user_id": user_id,
        "to":      to,
        "note":    "Aircall ist nicht konfiguriert — siehe aircall.py.stub zur Aktivierung.",
    }


def is_configured() -> bool:
    """False, weil dieser Stub niemals verkabelt ist."""
    return False
