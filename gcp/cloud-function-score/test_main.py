"""
Unit tests for compute_score — pure logic, no Airtable I/O.

Run from inside cloud-function-score/:
    pip install pytest
    pytest -v
"""

from datetime import datetime, timedelta, timezone

from main import compute_score


def _hours_ago(h):
    return (datetime.now(timezone.utc) - timedelta(hours=h)).isoformat()


def test_full_hot_lead_caps_at_100():
    fields = {
        "Source": "Referral",
        "Phone": "+49 170 1234567",
        "Notes": "Sehr konkretes Anliegen, will Karrierewechsel in Q3.",
        "Created": _hours_ago(1),
    }
    result = compute_score(fields, program_price=5000)
    assert result["total"] == 100
    assert result["breakdown"] == {
        "source": 30, "program": 30, "phone": 15, "notes": 5, "recency": 20
    }


def test_cold_lead_minimal():
    fields = {
        "Source": "Other",
        "Phone": "",
        "Notes": "",
        "Created": _hours_ago(200),
    }
    result = compute_score(fields, program_price=0)
    assert result["total"] == 5  # only Source=Other (5)
    assert result["breakdown"]["recency"] == 0
    assert result["breakdown"]["phone"] == 0
    assert result["breakdown"]["notes"] == 0


def test_unknown_source_scores_zero():
    fields = {"Source": "Mystery", "Created": _hours_ago(1)}
    result = compute_score(fields, 0)
    assert result["breakdown"]["source"] == 0


def test_program_price_linear_and_capped():
    fields = {"Source": "Organic", "Created": _hours_ago(1)}
    assert compute_score(fields, 2500)["breakdown"]["program"] == 15
    assert compute_score(fields, 5000)["breakdown"]["program"] == 30
    assert compute_score(fields, 10000)["breakdown"]["program"] == 30
    assert compute_score(fields, 0)["breakdown"]["program"] == 0


def test_recency_thresholds():
    base = {"Source": "Other"}
    assert compute_score({**base, "Created": _hours_ago(1)},   0)["breakdown"]["recency"] == 20
    assert compute_score({**base, "Created": _hours_ago(48)},  0)["breakdown"]["recency"] == 10
    assert compute_score({**base, "Created": _hours_ago(100)}, 0)["breakdown"]["recency"] == 5
    assert compute_score({**base, "Created": _hours_ago(200)}, 0)["breakdown"]["recency"] == 0


def test_short_notes_no_bonus():
    fields = {"Source": "Other", "Notes": "Kurz."}
    assert compute_score(fields, 0)["breakdown"]["notes"] == 0


def test_phone_whitespace_only_no_bonus():
    fields = {"Source": "Other", "Phone": "   "}
    assert compute_score(fields, 0)["breakdown"]["phone"] == 0


def test_missing_fields_default_to_zero():
    assert compute_score({}, 0)["total"] == 0


def test_hot_lead_threshold_at_70():
    """Anna-Müller-style realistic lead, Google Ads + Career Boost + phone + recent."""
    fields = {
        "Source": "Google Ads",  # 20
        "Phone": "+49 170 1234567",  # 15
        "Notes": "Möchte in 6 Monaten den Job wechseln.",  # >20 chars -> 5
        "Created": _hours_ago(2),  # 20
    }
    # Career Boost = 2490 EUR -> round(2490/5000*30) = 15
    result = compute_score(fields, program_price=2490)
    assert result["total"] == 20 + 15 + 15 + 5 + 20  # = 75
    assert result["total"] >= 70  # qualifies as hot
