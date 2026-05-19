"""
Seed 12 realistic test leads into Airtable + HubSpot.

Score-Verteilung:  3 hot · 4 warm · 3 cold · 2 unqualified
E-Mails:           `*@example.test` (RFC 6761 reserved — niemals echte Mailbox)
Idempotent:        wenn E-Mail bereits in einem System existiert, wird übersprungen

Aufruf:
    cd C:\\Users\\msi\\Desktop\\demoprojekt
    PYTHONIOENCODING=utf-8 python scripts/seed_test_leads.py
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
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

AT_TOKEN  = env.get("AIRTABLE_PERSONAL_ACCESS_TOKEN")
AT_BASE   = env.get("AIRTABLE_BASE_ID")
HS_TOKEN  = env.get("HUBSPOT_PRIVATE_APP_TOKEN")

if not (AT_TOKEN and AT_BASE and HS_TOKEN):
    sys.exit("ERROR: missing tokens in .env")


def http(method: str, url: str, headers: dict, body: dict | None = None) -> tuple[int, dict]:
    data = json.dumps(body).encode("utf-8") if body else None
    req = request.Request(url, data=data, method=method, headers=headers)
    try:
        with request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "{}")
    except error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8") or "{}")


# --- Score-Modell (1:1 wie quiz-frontend/score-engine.js) -----------------

WEIGHTS = {1: 5, 2: 10, 3: 10, 4: 10, 5: 10, 6: 20, 7: 10, 8: 10, 9: 15}

RAW_SCORES = {
    1: {"ja": 10, "nein": 0},
    2: {"lt_1": 2, "1_3": 6, "gt_3": 10},
    3: {"coach": 10, "services": 8, "digital": 8, "ecommerce": 6, "network": 4, "other": 2},
    4: {"lt_1k": 2, "lt_10k": 6, "gt_10k": 10},
    5: {"solo": 4, "lt_10": 8, "gt_10": 10},
    6: {"zero": 0, "lt_5k": 2, "lt_10k": 6, "lt_100k": 10, "gt_100k": 10},
    7: {"stable": 2, "quit_job": 4, "brand": 6, "freedom": 8, "5fig": 10},
    8: {"reach": 2, "portfolio": 2, "sales": 2, "clone": 2, "mindset": 2},  # multi
    9: {"lt_1h": 0, "2_5h": 4, "5_10h": 8, "gt_10h": 10},
}


def compute_score(a: dict) -> int:
    total = 0
    for step, weight in WEIGHTS.items():
        key_map = {
            1: "business_status", 2: "years_self_employed", 3: "business_field",
            4: "visibility", 5: "team_setup", 6: "monthly_revenue",
            7: "main_wish", 8: "gap", 9: "time_budget",
        }
        val = a[key_map[step]]
        if step == 8:
            raw = min(10, sum(RAW_SCORES[8].get(g, 0) for g in val))
        else:
            raw = RAW_SCORES[step].get(val, 0)
        total += raw / 10 * weight
    return round(min(100, total))


def tier_from_score(s: int) -> str:
    if s >= 70: return "hot"
    if s >= 50: return "warm"
    if s >= 30: return "cold"
    return "unqualified"


# --- 12 Test-Profile -------------------------------------------------------

PROFILES = [
    # 3 HOT (etablierte Coaches/Consultants mit High Commitment)
    {"fn": "Anna",  "ln": "Müller",   "country": "DE", "answers": {
        "business_status": "ja", "years_self_employed": "gt_3", "business_field": "coach",
        "visibility": "gt_10k", "team_setup": "lt_10", "monthly_revenue": "lt_10k",
        "main_wish": "5fig", "gap": ["reach", "sales"], "time_budget": "gt_10h",
    }, "utm": {"source": "facebook", "medium": "cpc", "campaign": "coach_q2"}},
    {"fn": "Lukas", "ln": "Bauer",    "country": "AT", "answers": {
        "business_status": "ja", "years_self_employed": "1_3", "business_field": "services",
        "visibility": "lt_10k", "team_setup": "solo", "monthly_revenue": "lt_100k",
        "main_wish": "freedom", "gap": ["clone", "mindset"], "time_budget": "gt_10h",
    }, "utm": {"source": "instagram", "medium": "organic", "campaign": "reels_apr"}},
    {"fn": "Sofia", "ln": "Schmidt",  "country": "DE", "answers": {
        "business_status": "ja", "years_self_employed": "gt_3", "business_field": "digital",
        "visibility": "gt_10k", "team_setup": "lt_10", "monthly_revenue": "lt_100k",
        "main_wish": "5fig", "gap": ["sales"], "time_budget": "gt_10h",
    }, "utm": {"source": "google", "medium": "cpc", "campaign": "search_brand"}},

    # 4 WARM (Wachstumsphase, Commitment vorhanden)
    {"fn": "Markus","ln": "Weber",    "country": "DE", "answers": {
        "business_status": "ja", "years_self_employed": "1_3", "business_field": "coach",
        "visibility": "lt_10k", "team_setup": "solo", "monthly_revenue": "lt_5k",
        "main_wish": "5fig", "gap": ["reach", "sales", "mindset"], "time_budget": "gt_10h",
    }, "utm": {"source": "facebook", "medium": "cpc", "campaign": "coach_q2"}},
    {"fn": "Julia", "ln": "Hoffmann", "country": "CH", "answers": {
        "business_status": "ja", "years_self_employed": "gt_3", "business_field": "services",
        "visibility": "lt_10k", "team_setup": "solo", "monthly_revenue": "lt_5k",
        "main_wish": "freedom", "gap": ["reach"], "time_budget": "5_10h",
    }, "utm": {"source": "linkedin", "medium": "social", "campaign": "thought_lead"}},
    {"fn": "Felix", "ln": "Lehmann",  "country": "DE", "answers": {
        "business_status": "ja", "years_self_employed": "lt_1", "business_field": "digital",
        "visibility": "lt_10k", "team_setup": "solo", "monthly_revenue": "lt_10k",
        "main_wish": "5fig", "gap": ["portfolio", "sales"], "time_budget": "gt_10h",
    }, "utm": {"source": "tiktok", "medium": "cpc", "campaign": "founder_story"}},
    {"fn": "Hannah","ln": "Wagner",   "country": "DE", "answers": {
        "business_status": "ja", "years_self_employed": "1_3", "business_field": "coach",
        "visibility": "lt_10k", "team_setup": "solo", "monthly_revenue": "lt_5k",
        "main_wish": "freedom", "gap": ["reach", "mindset"], "time_budget": "5_10h",
    }, "utm": {"source": "facebook", "medium": "cpc", "campaign": "coach_q2"}},

    # 3 COLD (Anfänger / wenig Commitment)
    {"fn": "Tobias","ln": "Becker",   "country": "DE", "answers": {
        "business_status": "ja", "years_self_employed": "lt_1", "business_field": "ecommerce",
        "visibility": "lt_1k", "team_setup": "solo", "monthly_revenue": "zero",
        "main_wish": "stable", "gap": ["reach", "mindset"], "time_budget": "2_5h",
    }, "utm": {"source": "facebook", "medium": "organic", "campaign": "broad_q1"}},
    {"fn": "Mira",  "ln": "Fischer",  "country": "DE", "answers": {
        "business_status": "nein", "years_self_employed": "lt_1", "business_field": "other",
        "visibility": "lt_1k", "team_setup": "solo", "monthly_revenue": "zero",
        "main_wish": "quit_job", "gap": ["mindset"], "time_budget": "5_10h",
    }, "utm": {"source": "instagram", "medium": "organic", "campaign": "reels_apr"}},
    {"fn": "Niklas","ln": "Schulz",   "country": "AT", "answers": {
        "business_status": "ja", "years_self_employed": "lt_1", "business_field": "network",
        "visibility": "lt_1k", "team_setup": "solo", "monthly_revenue": "lt_5k",
        "main_wish": "stable", "gap": ["sales"], "time_budget": "2_5h",
    }, "utm": {"source": "google", "medium": "cpc", "campaign": "search_broad"}},

    # 2 UNQUALIFIED (kein/kaum Commitment, geringe Reife)
    {"fn": "Paula", "ln": "Keller",   "country": "DE", "answers": {
        "business_status": "nein", "years_self_employed": "lt_1", "business_field": "other",
        "visibility": "lt_1k", "team_setup": "solo", "monthly_revenue": "zero",
        "main_wish": "stable", "gap": ["mindset"], "time_budget": "lt_1h",
    }, "utm": {"source": "facebook", "medium": "organic", "campaign": "broad_q1"}},
    {"fn": "David", "ln": "Hartmann", "country": "OTHER", "answers": {
        "business_status": "nein", "years_self_employed": "lt_1", "business_field": "other",
        "visibility": "lt_1k", "team_setup": "solo", "monthly_revenue": "zero",
        "main_wish": "stable", "gap": ["mindset"], "time_budget": "lt_1h",
    }, "utm": {"source": "tiktok", "medium": "organic", "campaign": "broad_q1"}},
]


def email_for(p: dict) -> str:
    # example.com is RFC 2606 reserved for documentation — HubSpot accepts it, .test is rejected (no MX)
    raw = f"demo-{p['fn'].lower()}-{p['ln'].lower()}@example.com"
    return raw.replace("ü", "ue").replace("ö", "oe").replace("ä", "ae").replace("ß", "ss")


def phone_for(country: str) -> str:
    return {"DE": "+49 170 ", "AT": "+43 660 ", "CH": "+41 79 ", "OTHER": "+1 415 "}.get(country, "+49 170 ") \
        + str(uuid.uuid4().int)[:7]


# --- Airtable Insert -------------------------------------------------------

def get_airtable_schema():
    code, body = http("GET", f"https://api.airtable.com/v0/meta/bases/{AT_BASE}/tables",
                      {"Authorization": f"Bearer {AT_TOKEN}"})
    if code != 200:
        sys.exit(f"Airtable schema read failed: {code} {body}")
    return body


def airtable_record(p: dict, score: int, tier: str, completed_at: str, event_id: str) -> dict:
    a = p["answers"]
    return {
        "Name": f"{p['fn']} {p['ln']}",
        "First Name": p["fn"], "Last Name": p["ln"],
        "Email": email_for(p), "Phone": phone_for(p["country"]),
        "Country": p["country"], "Consent": True,
        "Source": "Facebook" if p["utm"]["source"] == "facebook" else
                  "Instagram" if p["utm"]["source"] == "instagram" else
                  "Google Ads" if p["utm"]["source"] == "google" else "Other",
        "Status": "New",
        "Quiz Score": score,
        "Quiz Tier": tier,
        "Quiz · Business Status": a["business_status"],
        "Quiz · Years Self-Employed": a["years_self_employed"],
        "Quiz · Business Field": a["business_field"],
        "Quiz · Visibility": a["visibility"],
        "Quiz · Team Setup": a["team_setup"],
        "Quiz · Monthly Revenue": a["monthly_revenue"],
        "Quiz · Main Wish": a["main_wish"],
        "Quiz · Gap": a["gap"],
        "Quiz · Time Budget": a["time_budget"],
        "Quiz Completed At": completed_at,
        "Source Subdomain": "quiz.mindforge.demo",
        "Event ID": event_id,
        "UTM Source":   p["utm"]["source"],
        "UTM Medium":   p["utm"]["medium"],
        "UTM Campaign": p["utm"]["campaign"],
        "Lifecycle Stage": "marketingqualifiedlead" if tier in ("hot", "warm") else "lead",
        "Lead Status": "NEW",
        "_source": "seed-script",
    }


def airtable_upsert(table_id: str, records: list[dict]) -> int:
    headers = {"Authorization": f"Bearer {AT_TOKEN}", "Content-Type": "application/json"}
    n = 0
    for i in range(0, len(records), 10):
        chunk = records[i:i + 10]
        # Idempotency via upsert on Email field
        body = {
            "records": [{"fields": r} for r in chunk],
            "performUpsert": {"fieldsToMergeOn": ["Email"]},
        }
        code, resp = http("PATCH", f"https://api.airtable.com/v0/{AT_BASE}/{table_id}",
                          headers, body)
        if code in (200, 201):
            n += len(resp.get("records", []))
        else:
            print(f"  !! Airtable upsert failed: {code} — {resp.get('error', resp)}")
    return n


# --- HubSpot Insert --------------------------------------------------------

def hubspot_upsert(records: list[dict]) -> int:
    headers = {"Authorization": f"Bearer {HS_TOKEN}", "Content-Type": "application/json"}
    n = 0
    for r in records:
        body = {"properties": r}
        # Try update by email first
        code, _ = http("PATCH",
                       f"https://api.hubapi.com/crm/v3/objects/contacts/{r['email']}?idProperty=email",
                       headers, body)
        if code == 200:
            n += 1
            continue
        # Else create
        code, resp = http("POST",
                          "https://api.hubapi.com/crm/v3/objects/contacts",
                          headers, body)
        if code in (200, 201):
            n += 1
        else:
            print(f"  !! HubSpot upsert failed for {r['email']}: {code} — {resp}")
        time.sleep(0.1)
    return n


def hubspot_record(p: dict, score: int, tier: str, completed_at: str) -> dict:
    a = p["answers"]
    return {
        "email": email_for(p),
        "firstname": p["fn"], "lastname": p["ln"],
        "phone": phone_for(p["country"]),
        "country": p["country"],
        "lifecyclestage": "marketingqualifiedlead" if tier in ("hot", "warm") else "lead",
        "hs_lead_status": "NEW",
        "quiz_score": str(score),
        "quiz_business_status": a["business_status"],
        "quiz_years_self_employed": a["years_self_employed"],
        "quiz_business_field": a["business_field"],
        "quiz_visibility": a["visibility"],
        "quiz_team_setup": a["team_setup"],
        "quiz_monthly_revenue": a["monthly_revenue"],
        "quiz_main_wish": a["main_wish"],
        "quiz_gap": ",".join(a["gap"]),
        "quiz_time_budget": a["time_budget"],
        "quiz_completed_at": completed_at,
        "lead_source_subdomain": "quiz.mindforge.demo",
    }


# --- Main ------------------------------------------------------------------

def main() -> None:
    print("=" * 70)
    print("Phase E · Seed 12 Test Leads")
    print("=" * 70)

    # Airtable Schema → Tabellen-IDs
    schema = get_airtable_schema()
    leads_tbl = next((t for t in schema["tables"] if t["name"] == "Leads"), None)
    if not leads_tbl:
        sys.exit("ERROR: 'Leads' table not found")

    at_records = []
    hs_records = []
    rows = []
    now = datetime.now(timezone.utc)

    for i, p in enumerate(PROFILES):
        score = compute_score(p["answers"])
        tier = tier_from_score(score)
        completed = (now - timedelta(days=i * 3, hours=i * 2)).isoformat(timespec="seconds")
        eid = str(uuid.uuid4())
        at_records.append(airtable_record(p, score, tier, completed, eid))
        hs_records.append(hubspot_record(p, score, tier, completed))
        rows.append((p["fn"], p["ln"], email_for(p), score, tier))
        print(f"  {p['fn']:8s} {p['ln']:10s} score={score:3d}  tier={tier}")

    print("\n[Airtable] Upserting to Leads…")
    n_at = airtable_upsert(leads_tbl["id"], at_records)
    print(f"  → {n_at} records upserted")

    print("\n[HubSpot] Upserting to Contacts…")
    n_hs = hubspot_upsert(hs_records)
    print(f"  → {n_hs} contacts upserted")

    print("\n" + "=" * 70)
    print(f"Seeded {len(PROFILES)} leads (Airtable: {n_at}, HubSpot: {n_hs})")
    print("=" * 70)


if __name__ == "__main__":
    main()
