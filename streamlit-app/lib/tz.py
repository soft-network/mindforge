"""Zeitzone — Europe/Berlin zentral.

Airtable-ISO-Timestamps kommen als UTC im Transit. KPI-Berechnungen
und Display-Werte müssen aber in Berliner Zeit erfolgen, sonst sind
'heute' und 'diese Woche' off-by-up-to-2h.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


TZ_BERLIN = ZoneInfo("Europe/Berlin")


def now_berlin() -> datetime:
    """Aktuelle Berliner Zeit als tz-aware datetime."""
    return datetime.now(TZ_BERLIN)


def today_start_berlin() -> datetime:
    """Anfang des heutigen Tages in Berliner Zeit (00:00:00)."""
    return now_berlin().replace(hour=0, minute=0, second=0, microsecond=0)


def week_start_berlin(days: int = 7) -> datetime:
    """Anfang vor N Tagen, beginnend bei heute 00:00 Berliner Zeit."""
    return today_start_berlin() - timedelta(days=days)


def format_hm(dt: datetime | None = None) -> str:
    """HH:MM in Berliner Zeit. None = jetzt."""
    return (dt or now_berlin()).astimezone(TZ_BERLIN).strftime("%H:%M:%S")
