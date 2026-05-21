"""
MindForge — Lead Scoring Cloud Function
=========================================
HTTP-triggered Cloud Function that computes a lead score (0-100) and writes
it back to Airtable. Called by Make after lead creation.

Score components (identical to airtable-scripts/lead-scoring.js):
  - Source weight       (max 30)
  - Program price       (max 30, linear 0-5000 EUR)
  - Telefon present       (15)
  - Notizen >20 chars     (5)
  - Recency             (max 20)

If score >= HOT_LEAD_THRESHOLD (70), Status is set to "Qualified".

Request:
    POST /
    Content-Type: application/json
    Body: {"lead_id": "recXXXXXXXXXXXXXX"}

Response:
    200 OK
    {
        "lead_id": "recXXXXXX",
        "score": 78,
        "breakdown": {"source": 20, "program": 15, "phone": 15, "notes": 5, "recency": 20},
        "status": "Qualified"
    }

Deploy:
    bash ../deploy-score-function.sh
"""

import os
from datetime import datetime, timezone

import functions_framework
from pyairtable import Api


LEADS_TABLE = "Leads"
PROGRAMS_TABLE = "Programme"
HOT_LEAD_THRESHOLD = 70

SOURCE_WEIGHTS = {
    "Referral":   30,
    "Organic":    25,
    "Google Ads": 20,
    "Facebook":   15,
    "Instagram":  12,
    "Other":       5,
}

PHONE_BONUS = 15
NOTES_BONUS = 5


def _score_source(source):
    return SOURCE_WEIGHTS.get(source or "", 0)


def _score_program(price):
    if not price:
        return 0
    return min(30, round(float(price) / 5000 * 30))


def _score_phone(phone):
    return PHONE_BONUS if phone and phone.strip() else 0


def _score_notes(notes):
    return NOTES_BONUS if notes and len(notes.strip()) > 20 else 0


def _score_recency(created_iso):
    if not created_iso:
        return 0
    try:
        created = datetime.fromisoformat(created_iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return 0
    hours = (datetime.now(timezone.utc) - created).total_seconds() / 3600
    if hours < 24:
        return 20
    if hours < 72:
        return 10
    if hours < 168:
        return 5
    return 0


def compute_score(lead_fields, program_price=0):
    """Pure scoring function. No I/O. Easy to test."""
    breakdown = {
        "source":  _score_source(lead_fields.get("Source")),
        "program": _score_program(program_price),
        "phone":   _score_phone(lead_fields.get("Telefon")),
        "notes":   _score_notes(lead_fields.get("Notizen")),
        "recency": _score_recency(lead_fields.get("Erstellt am")),
    }
    total = min(100, sum(breakdown.values()))
    return {"total": total, "breakdown": breakdown}


@functions_framework.http
def score_lead(request):
    """HTTP entry point. Body: {"lead_id": "recXXXX"}."""
    if request.method != "POST":
        return ({"error": "Method not allowed"}, 405)

    body = request.get_json(silent=True) or {}
    lead_id = body.get("lead_id")
    if not lead_id:
        return ({"error": "Missing lead_id"}, 400)

    token = os.environ.get("AIRTABLE_API_TOKEN")
    base_id = os.environ.get("AIRTABLE_BASE_ID")
    if not token or not base_id:
        return ({"error": "Server misconfigured (missing Airtable env)"}, 500)

    api = Api(token)
    leads = api.table(base_id, LEADS_TABLE)
    programs = api.table(base_id, PROGRAMS_TABLE)

    try:
        lead = leads.get(lead_id)
    except Exception as e:
        return ({"error": f"Lead not found: {e}"}, 404)

    fields = lead["fields"]

    program_price = 0
    interest_links = fields.get("Interesse", [])
    if interest_links:
        try:
            program = programs.get(interest_links[0])
            program_price = float(program["fields"].get("Price (EUR)") or 0)
        except Exception:
            program_price = 0

    result = compute_score(fields, program_price)

    update = {"Lead Score": result["total"]}
    new_status = fields.get("Status", "New")
    if result["total"] >= HOT_LEAD_THRESHOLD:
        new_status = "Qualified"
        update["Status"] = new_status

    leads.update(lead_id, update)

    return ({
        "lead_id": lead_id,
        "score": result["total"],
        "breakdown": result["breakdown"],
        "status": new_status,
    }, 200)
