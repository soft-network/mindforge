"""Google Calendar Integration für die Setter-Daily-Page — User-OAuth-Flow.

Statt Service Account + Domain-wide Delegation: der Setter loggt sich
persönlich mit seinem Google-Account ein. App nutzt OAuth-Access-Token,
schreibt Events direkt auf den User-Kalender. Kein Workspace nötig,
kein Server-Side-Key.

Setup (siehe secrets.toml.example)
----------------------------------
GCP Console → APIs & Services → Credentials → OAuth client ID
    Application type: Web application
    Authorized redirect URIs: http://localhost:8501/oauth/callback
→ Client-ID + Client-Secret in .streamlit/secrets.toml:

    [google_oauth]
    client_id     = "...apps.googleusercontent.com"
    client_secret = "..."
    redirect_uri  = "http://localhost:8501/oauth/callback"

Scopes
------
    https://www.googleapis.com/auth/calendar.events
    openid email profile        (für Anzeige der eingeloggten Mail)

Streamlit + OAuth — wie es funktioniert
---------------------------------------
1. Beim Page-Load: handle_oauth_callback() liest ?code= aus den
   Query-Params, tauscht ihn gegen Tokens, speichert in Session-State.
2. Wenn keine Tokens da: ensure_authenticated() rendert Login-Button.
3. Sonst: normale Calendar-API-Calls mit User-Credentials.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional

import streamlit as st
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# Kanonische Scope-URLs verwenden — Google normalisiert "email"/"profile"
# automatisch zu den vollen URLs, was google-auth-oauthlib sonst als
# "Scope has changed" Mismatch erkennt und einen Fehler wirft.
SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]
DEFAULT_TZ = "Europe/Berlin"
DEFAULT_DURATION_MIN = 60

# Session-State Keys
_TOKEN_KEY = "google_creds"
_USER_EMAIL_KEY = "google_user_email"
_OAUTH_STATE_KEY = "_oauth_state"


# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

def _config() -> dict:
    """Read [google_oauth] from secrets.toml (or env)."""
    cfg = st.secrets.get("google_oauth")
    if cfg:
        return dict(cfg)
    # Env fallback (für Cloud Run etc.)
    cid = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    cse = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    rdu = os.environ.get("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8501/oauth/callback")
    if not (cid and cse):
        raise RuntimeError(
            "Kein Google OAuth Setup gefunden. "
            "Lege [google_oauth] in .streamlit/secrets.toml an "
            "(client_id, client_secret, redirect_uri)."
        )
    return {"client_id": cid, "client_secret": cse, "redirect_uri": rdu}


def _flow() -> Flow:
    """Build a google_auth_oauthlib Flow from config."""
    c = _config()
    return Flow.from_client_config(
        {
            "web": {
                "client_id":     c["client_id"],
                "client_secret": c["client_secret"],
                "redirect_uris": [c["redirect_uri"]],
                "auth_uri":      "https://accounts.google.com/o/oauth2/auth",
                "token_uri":     "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=c["redirect_uri"],
    )


# -----------------------------------------------------------------------------
# Auth flow
# -----------------------------------------------------------------------------

def handle_oauth_callback() -> bool:
    """Beim Page-Load: liest ?code= aus URL und tauscht es gegen Tokens.

    Rückgabe: True wenn Callback verarbeitet wurde (Session ist jetzt
    eingeloggt). False wenn kein Callback in den Query-Params war.
    """
    qp = st.query_params
    code = qp.get("code")
    if not code:
        return False

    # State-Check (CSRF-Schutz). Wenn State im Session-State liegt: vergleichen.
    expected_state = st.session_state.get(_OAUTH_STATE_KEY)
    received_state = qp.get("state")
    if expected_state and received_state and expected_state != received_state:
        st.error("OAuth state mismatch — möglicherweise CSRF. Bitte erneut einloggen.")
        st.query_params.clear()
        return False

    try:
        flow = _flow()
        flow.fetch_token(code=code)
        creds = flow.credentials
        st.session_state[_TOKEN_KEY] = _creds_to_dict(creds)
        # User-E-Mail aus ID-Token oder via userinfo holen
        st.session_state[_USER_EMAIL_KEY] = _fetch_user_email(creds)
        # Query-Params säubern, damit Refresh nicht erneut den Code feuert
        st.query_params.clear()
        return True
    except Exception as e:
        st.error(f"OAuth-Code-Exchange fehlgeschlagen: {e}")
        st.query_params.clear()
        return False


def ensure_authenticated() -> bool:
    """Falls noch kein Token: Login-Button rendern und False zurückgeben.

    Falls Token da: True zurückgeben, Caller darf weiter rendern.
    """
    if _TOKEN_KEY in st.session_state:
        return True

    flow = _flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",  # Refresh-Token sicherstellen
    )
    st.session_state[_OAUTH_STATE_KEY] = state

    st.info(
        "Bevor du Termine buchen kannst, musst du dich einmal mit deinem "
        "Google-Account einloggen."
    )
    # HTML-Link mit target="_self" — Login passiert im GLEICHEN Tab, damit
    # der OAuth-Callback wieder hier landet (Streamlit-Session bleibt erhalten).
    st.markdown(
        f"""
        <a href="{auth_url}" target="_self"
           style="display:inline-block; padding:10px 24px;
                  background-color:#FF4B4B; color:white;
                  text-decoration:none; border-radius:6px;
                  font-weight:600; font-size:16px;">
           🔑 Mit Google einloggen
        </a>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        "Du wirst zur Google-Consent-Seite weitergeleitet und kommst "
        "danach automatisch zu Streamlit zurück."
    )
    return False


def logout() -> None:
    """Token und User-Info aus der Session löschen."""
    for k in (_TOKEN_KEY, _USER_EMAIL_KEY, _OAUTH_STATE_KEY):
        st.session_state.pop(k, None)


def current_user_email() -> Optional[str]:
    return st.session_state.get(_USER_EMAIL_KEY)


# -----------------------------------------------------------------------------
# Credentials helpers
# -----------------------------------------------------------------------------

def _creds_to_dict(creds: Credentials) -> dict:
    return {
        "token":         creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri":     creds.token_uri,
        "client_id":     creds.client_id,
        "client_secret": creds.client_secret,
        "scopes":        list(creds.scopes or []),
        "expiry":        creds.expiry.isoformat() if creds.expiry else None,
    }


def _creds_from_dict(d: dict) -> Credentials:
    creds = Credentials(
        token=d.get("token"),
        refresh_token=d.get("refresh_token"),
        token_uri=d.get("token_uri"),
        client_id=d.get("client_id"),
        client_secret=d.get("client_secret"),
        scopes=d.get("scopes") or SCOPES,
    )
    return creds


def _get_creds() -> Credentials:
    """Hole Credentials aus Session, refreshe wenn nötig, persistiere."""
    d = st.session_state.get(_TOKEN_KEY)
    if not d:
        raise RuntimeError("Nicht eingeloggt — ensure_authenticated() vergessen?")
    creds = _creds_from_dict(d)
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        st.session_state[_TOKEN_KEY] = _creds_to_dict(creds)
    return creds


def _service():
    return build("calendar", "v3", credentials=_get_creds(), cache_discovery=False)


def _fetch_user_email(creds: Credentials) -> str:
    """Aus dem OAuth-Token via OpenID-Userinfo-Endpoint die E-Mail holen."""
    import urllib.request
    import json
    req = urllib.request.Request(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {creds.token}"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        info = json.loads(resp.read().decode("utf-8"))
        return info.get("email", "unknown@example.com")
    except Exception:
        return "unknown@example.com"


# -----------------------------------------------------------------------------
# Public API — Calendar operations
# -----------------------------------------------------------------------------

def create_strategy_call(
    lead_email: str,
    lead_name: str,
    when: datetime,
    duration_min: int = DEFAULT_DURATION_MIN,
    summary_template: str = "Strategiegespräch — {lead}",
    timezone: str = DEFAULT_TZ,
) -> dict:
    """Erstellt ein Calendar-Event mit auto-generiertem Meet-Link
    auf dem Kalender des eingeloggten Users (Setter).

    Rückgabe-Dict: event_id, meet_link, html_link, start, end.
    """
    if when.tzinfo is None:
        raise ValueError(
            "create_strategy_call braucht ein tz-aware datetime. "
            "Bspw.: datetime.now(ZoneInfo('Europe/Berlin'))."
        )

    setter_email = current_user_email() or "primary"
    service = _service()

    start = when
    end = when + timedelta(minutes=duration_min)
    event_body = {
        "summary": summary_template.format(lead=lead_name or lead_email),
        "description": (
            "Strategiegespräch aus MindForge Setter-Daily gebucht.\n"
            f"Lead: {lead_name} <{lead_email}>\n"
            f"Dauer: {duration_min} Minuten"
        ),
        "start": {"dateTime": start.isoformat(), "timeZone": timezone},
        "end":   {"dateTime": end.isoformat(),   "timeZone": timezone},
        "attendees": [{"email": lead_email, "responseStatus": "needsAction"}],
        "conferenceData": {
            "createRequest": {
                "requestId": f"mf-{setter_email}-{int(start.timestamp())}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 60},
                {"method": "popup", "minutes": 10},
            ],
        },
    }

    try:
        event = service.events().insert(
            calendarId="primary",
            body=event_body,
            conferenceDataVersion=1,
            sendUpdates="all",
        ).execute()
    except HttpError as e:
        raise RuntimeError(f"Google Calendar Event-Erstellung fehlgeschlagen: {e}") from e

    meet_link = event.get("hangoutLink") or _extract_meet_from_conference(event)
    return {
        "event_id":  event["id"],
        "meet_link": meet_link,
        "html_link": event.get("htmlLink"),
        "start":     event["start"]["dateTime"],
        "end":       event["end"]["dateTime"],
    }


def cancel_event(event_id: str) -> None:
    """Löscht ein Event auf dem User-Kalender. Lead bekommt Absage-Mail."""
    _service().events().delete(
        calendarId="primary",
        eventId=event_id,
        sendUpdates="all",
    ).execute()


def check_busy(start: datetime, end: datetime, timezone: str = DEFAULT_TZ) -> bool:
    """True wenn der primary calendar des Users im Slot busy ist."""
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("check_busy braucht tz-aware datetimes.")
    body = {
        "timeMin":  start.isoformat(),
        "timeMax":  end.isoformat(),
        "timeZone": timezone,
        "items":    [{"id": "primary"}],
    }
    result = _service().freebusy().query(body=body).execute()
    busy = result.get("calendars", {}).get("primary", {}).get("busy", [])
    return len(busy) > 0


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _extract_meet_from_conference(event: dict) -> Optional[str]:
    """Fallback für die Meet-URL falls `hangoutLink` fehlt."""
    for entry in event.get("conferenceData", {}).get("entryPoints", []):
        if entry.get("entryPointType") == "video":
            return entry.get("uri")
    return None
