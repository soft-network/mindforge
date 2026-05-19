"""
Unit tests for enrich-email Cloud Function.

Run from inside cloud-function/:
    pip install pytest
    pytest -v
"""

from main import classify_email, enrich_email


# -----------------------------------------------------------------------------
# Pure classification logic
# -----------------------------------------------------------------------------

def test_gmail_is_personal():
    result = classify_email("alice@gmail.com")
    assert result["is_personal"] is True
    assert result["is_business"] is False
    assert result["type"] == "personal"
    assert result["score_adjustment"] == -5


def test_acme_is_business():
    result = classify_email("alice@acme.com")
    assert result["is_business"] is True
    assert result["is_personal"] is False
    assert result["is_high_value"] is False
    assert result["type"] == "business"
    assert result["score_adjustment"] == 10


def test_google_is_high_value():
    result = classify_email("alice@google.com")
    assert result["is_high_value"] is True
    assert result["is_business"] is True
    assert result["is_personal"] is False
    assert result["score_adjustment"] == 20


def test_dach_providers_are_personal():
    for addr in ["max@gmx.de", "anna@web.de", "paul@t-online.de", "lisa@freenet.de"]:
        result = classify_email(addr)
        assert result["is_personal"] is True, f"{addr} should be personal"
        assert result["score_adjustment"] == -5


def test_disposable_is_personal():
    """Disposable providers flagged personal (lowest quality)."""
    result = classify_email("test@mailinator.com")
    assert result["is_personal"] is True
    assert result["score_adjustment"] == -5


def test_french_providers_are_personal():
    for addr in ["marc@orange.fr", "claire@free.fr", "jean@laposte.net"]:
        assert classify_email(addr)["is_personal"] is True


def test_protonmail_is_personal():
    assert classify_email("anon@proton.me")["is_personal"] is True


def test_invalid_no_at_returns_none():
    assert classify_email("notanemail") is None


def test_invalid_empty_returns_none():
    assert classify_email("") is None
    assert classify_email(None) is None


def test_domain_extraction_with_multidot():
    result = classify_email("foo@sub.example.co.uk")
    assert result["domain"] == "sub.example.co.uk"
    assert result["is_business"] is True


# -----------------------------------------------------------------------------
# HTTP handler — with a minimal MockRequest
# -----------------------------------------------------------------------------

class MockRequest:
    def __init__(self, method="POST", json_body=None):
        self.method = method
        self._json = json_body

    def get_json(self, silent=False):
        return self._json


def test_http_post_valid_email():
    req = MockRequest("POST", {"email": "alice@acme.com"})
    body, status = enrich_email(req)
    assert status == 200
    assert body["is_business"] is True
    assert body["score_adjustment"] == 10


def test_http_get_rejected():
    req = MockRequest("GET")
    body, status = enrich_email(req)
    assert status == 405


def test_http_missing_email_body():
    req = MockRequest("POST", {})
    body, status = enrich_email(req)
    assert status == 400


def test_http_invalid_email_format():
    req = MockRequest("POST", {"email": "notanemail"})
    body, status = enrich_email(req)
    assert status == 400


def test_http_normalizes_whitespace_and_case():
    """Handler should lower + strip before classifying."""
    req = MockRequest("POST", {"email": "  Alice@ACME.com  "})
    body, status = enrich_email(req)
    assert status == 200
    assert body["domain"] == "acme.com"
    assert body["email"] == "alice@acme.com"


def test_http_null_body():
    req = MockRequest("POST", None)
    body, status = enrich_email(req)
    assert status == 400
