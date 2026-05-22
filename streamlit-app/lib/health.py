"""Customer Health Score — pure Python.

Bildet die in `02b-airtable-phase-e-extension.md` dokumentierte Airtable-
Formel 1:1 in Python ab, damit wir keinen Rollup im Schema brauchen:

    SWITCH(
      TRUE(),
      days_since_last_session <= 7,  100,
      days_since_last_session <= 14,  75,
      days_since_last_session <= 30,  50,
      days_since_last_session <= 60,  25,
      0
    )

Keine Streamlit-Imports — die Funktionen sind unit-testbar ohne UI-Setup.
"""

from __future__ import annotations

from typing import Literal, Optional

import pandas as pd


# Schwellen in Tagen → Score-Wert (in absteigender Reihenfolge ausgewertet)
HEALTH_THRESHOLDS: list[tuple[int, int]] = [
    (7,   100),
    (14,   75),
    (30,   50),
    (60,   25),
]
HEALTH_FALLBACK = 0


HealthTier = Literal["Engaged", "Active", "At Risk", "Churn Risk", "Churned"]


def compute_health_score(
    last_session: Optional[pd.Timestamp],
    now: Optional[pd.Timestamp] = None,
) -> int:
    """Score von 0–100 anhand Tagen seit letzter Session.

    Args:
        last_session: tz-naive oder tz-aware Timestamp der letzten Session.
                      Bei None/NaT → Score 0 (nie eine Session gehabt = Churn-Risk).
        now:          Optional, default = pd.Timestamp.now(). Für Tests.
    """
    if last_session is None or pd.isna(last_session):
        return HEALTH_FALLBACK

    now = now if now is not None else pd.Timestamp.now()

    # tz-Normalisierung: wenn eine Seite tz-aware ist, die andere auch machen
    if last_session.tzinfo is not None and now.tzinfo is None:
        now = now.tz_localize(last_session.tzinfo)
    elif last_session.tzinfo is None and now.tzinfo is not None:
        last_session = last_session.tz_localize(now.tzinfo)

    days = (now - last_session).days
    if days < 0:  # last_session liegt in der Zukunft → behandeln als "frisch"
        return HEALTH_THRESHOLDS[0][1]

    for threshold_days, score in HEALTH_THRESHOLDS:
        if days <= threshold_days:
            return score
    return HEALTH_FALLBACK


def health_tier(score: int) -> HealthTier:
    """Mappt Score → menschenlesbaren Tier-Namen."""
    if score >= 100: return "Engaged"
    if score >= 75:  return "Active"
    if score >= 50:  return "At Risk"
    if score >= 25:  return "Churn Risk"
    return "Churned"


def health_emoji(score: int) -> str:
    """Mappt Score → Ampel-Emoji für Listen-Anzeige."""
    if score >= 100: return "🟢"
    if score >= 75:  return "🟢"
    if score >= 50:  return "🟡"
    if score >= 25:  return "🟠"
    return "🔴"
