"""
MindForge Email-Domain-Enrichment Function
============================================
HTTP-triggered Cloud Function that classifies an email address as either
personal (gmail, yahoo, etc.) or business (custom domain).

Make calls this function after lead creation to enrich the lead record.

Request:
    POST /
    Content-Type: application/json
    Body: {"email": "alice@acme.com"}

Response:
    200 OK
    {
        "email": "alice@acme.com",
        "domain": "acme.com",
        "is_business": true,
        "type": "business",
        "score_adjustment": 10
    }

Deploy:
    gcloud functions deploy enrich-email \
        --gen2 --runtime python312 --region europe-west1 \
        --source . --entry-point enrich_email --trigger-http \
        --allow-unauthenticated
"""

import functions_framework

# Common personal/free email providers
PERSONAL_DOMAINS = {
    # Worldwide
    "gmail.com", "googlemail.com",
    "yahoo.com", "yahoo.de", "yahoo.fr", "yahoo.co.uk",
    "outlook.com", "outlook.de", "hotmail.com", "hotmail.de",
    "live.com", "live.de", "msn.com",
    "icloud.com", "me.com", "mac.com",
    "aol.com", "aol.de",
    "proton.me", "protonmail.com", "tutanota.com",
    # DACH-specific
    "web.de", "gmx.de", "gmx.net", "gmx.at", "gmx.ch", "freenet.de", "t-online.de",
    "arcor.de", "1und1.de", "online.de", "mail.de",
    # FR
    "orange.fr", "wanadoo.fr", "free.fr", "laposte.net", "sfr.fr",
    # Disposable / temporary
    "mailinator.com", "guerrillamail.com", "10minutemail.com", "tempmail.com",
}

# Known business domains worth flagging extra (large companies, agencies)
HIGH_VALUE_DOMAINS = {
    "google.com", "microsoft.com", "apple.com", "amazon.com",
    "meta.com", "facebook.com",
}


def classify_email(email):
    """Pure classification. Expects an already-normalized (lowercase, stripped) email.
    Returns dict on success, None on invalid input. No I/O — easy to unit-test."""
    if not email or "@" not in email:
        return None

    domain = email.split("@", 1)[1]

    is_personal = domain in PERSONAL_DOMAINS
    is_high_value = domain in HIGH_VALUE_DOMAINS
    is_business = not is_personal

    # Score adjustment heuristic:
    #   - Personal email: -5 (lower lead quality)
    #   - Standard business email: +10
    #   - High-value business: +20
    if is_personal:
        score_adjustment = -5
    elif is_high_value:
        score_adjustment = 20
    else:
        score_adjustment = 10

    return {
        "email": email,
        "domain": domain,
        "is_business": is_business,
        "is_personal": is_personal,
        "is_high_value": is_high_value,
        "type": "business" if is_business else "personal",
        "score_adjustment": score_adjustment,
    }


@functions_framework.http
def enrich_email(request):
    """HTTP Cloud Function entry point."""
    if request.method != "POST":
        return ({"error": "Method not allowed"}, 405)

    try:
        body = request.get_json(silent=True) or {}
    except Exception:
        return ({"error": "Invalid JSON"}, 400)

    email = (body.get("email") or "").strip().lower()
    result = classify_email(email)
    if result is None:
        return ({"error": "Invalid email", "received": email}, 400)

    return (result, 200)
