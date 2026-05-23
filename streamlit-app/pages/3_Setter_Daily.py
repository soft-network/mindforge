"""Setter Daily — Hot-Lead-Queue + Termin-Buchung mit Google Meet (User-OAuth).

Workflow:
    1. Setter loggt sich ins Admin ein (Passwort-Gate aus integrations.auth)
    2. Wechselt zur Seite "Setter Daily" über die Streamlit-Sidebar
    3. Erst-Aufruf: "Mit Google einloggen" → Browser-Consent-Screen → zurück
    4. Sieht priorisierte Hot-Lead-Queue (Score >= 70, Status New/Qualified)
    5. Pro Lead:
        - Click-to-Call (Aircall-Stub oder tel:-Fallback)
        - Datum/Uhrzeit picken → "Termin buchen + Meet-Link"
        - Status quick-update + Notiz mit Timestamp

Side effects pro Termin-Buchung:
    - Google-Calendar-Event auf dem Kalender des eingeloggten Users
      (Meet-Link auto-generiert, Lead bekommt Invite-Mail)
    - Airtable-Lead-Update: Status="Contacted", Termin am, Meet-Link, Setter
"""

from __future__ import annotations

import pathlib
import sys
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from integrations import airtable_helpers as at  # noqa: E402
from integrations import google_calendar as gcal  # noqa: E402
from integrations import aircall  # noqa: E402
from integrations.auth import require_tool_access  # noqa: E402
from components.lead_card import tier_badge, render_lead_summary  # noqa: E402


TZ = ZoneInfo("Europe/Berlin")

# Permission-Gate (Sales hat full, Hauptadmin nur read — wir lassen Page öffnen,
# Edit-/Buchungs-Buttons werden in der Page selbst rolle-abhängig getoggled)
require_tool_access("hot_leads", "read")


st.title(":material/phone_in_talk: Setter Daily")
st.caption(
    "Hot-Lead-Queue · Click-to-Call · Termin-Buchung mit Google Meet · "
    "Status-Updates und Notizen synchron in Airtable"
)


# -----------------------------------------------------------------------------
# Google-Account + Filter — direkt in der Page (statt Sidebar)
# -----------------------------------------------------------------------------

with st.container(border=True):
    cols = st.columns([2, 2, 2])

    # Google-Account-Status
    with cols[0]:
        st.markdown("**:material/account_circle: Google-Account**")
        if gcal.current_user_email():
            st.success(f"Eingeloggt als\n**{gcal.current_user_email()}**")
            if st.button("Google-Logout", key="gcal_logout_btn"):
                gcal.logout()
                st.rerun()
        else:
            st.caption("Noch nicht verbunden — siehe Login-Button unten.")

    # Filter-Block
    with cols[1]:
        st.markdown("**:material/filter_alt: Min Score**")
        min_score = st.slider("Quiz Score (min)", 50, 100, 70, step=5,
                              label_visibility="collapsed")

    with cols[2]:
        st.markdown("**:material/list: Status-Filter**")
        statuses = st.multiselect(
            "Status",
            ["New", "Qualified", "Contacted"],
            default=["New", "Qualified"],
            label_visibility="collapsed",
        )
        if not statuses:
            statuses = ["New", "Qualified"]


# -----------------------------------------------------------------------------
# OAuth Login Gate — kein Calendar-Zugriff ohne Login
# -----------------------------------------------------------------------------

if not gcal.ensure_authenticated():
    # ensure_authenticated rendert den "Mit Google einloggen"-Button.
    # Restliche Page erst nach Login zeigen.
    st.stop()


# -----------------------------------------------------------------------------
# KPI strip
# -----------------------------------------------------------------------------

setter_email = gcal.current_user_email() or ""
if setter_email:
    kpis = at.get_setter_today_kpis(setter_email)
    k1, k2, k3 = st.columns(3)
    k1.metric("Heute gebucht", kpis["calls_booked_today"])
    k2.metric("In Pipeline",   kpis["calls_pending"])
    k3.metric("Open Hot Leads", "—", help="siehe Liste unten")

st.markdown("---")


# -----------------------------------------------------------------------------
# Lead queue
# -----------------------------------------------------------------------------

df = at.get_hot_leads(min_score=min_score, statuses=tuple(statuses))

if df.empty:
    st.success("🎉 Keine offenen Hot-Leads. Lehn dich kurz zurück.")
    st.stop()

st.write(f"**{len(df)} Hot-Lead(s)** in der Queue")
df = df.sort_values(["Quiz Score", "Erstellt am"], ascending=[False, True]).reset_index(drop=True)



# -----------------------------------------------------------------------------
# Render jeden Lead als expandable Karte (Lead-Summary über shared Component)
# -----------------------------------------------------------------------------

for _, lead in df.iterrows():
    label = (
        f"{tier_badge(int(lead['Quiz Score']))} · "
        f"Score {int(lead['Quiz Score'])} · "
        f"{lead['Name']} · {lead['Branche'] or '—'} · "
        f"{lead['Monatsumsatz'] or '—'}"
    )
    with st.expander(label, expanded=False):
        # --- Lead facts (shared component) -------------------------------
        c1, c2 = st.columns([3, 2])
        with c1:
            render_lead_summary(lead)
            if lead.get("Notizen"):
                st.text_area(
                    "Notizen (Vorschau, read-only)",
                    value=lead["Notizen"],
                    height=80,
                    disabled=True,
                    key=f"notes_view_{lead['id']}",
                )
        with c2:
            if lead.get("Termin am") is not None and str(lead.get("Termin am")) != "NaT":
                st.success(f"📅 Termin: {lead['Termin am']}")
                if lead.get("Meet-Link"):
                    st.markdown(f"🎥 [Meet öffnen]({lead['Meet-Link']})")

        st.markdown("---")

        # --- Actions ------------------------------------------------------
        a1, a2 = st.columns(2)

        # ---- A) Click-to-Call -------------------------------------------
        with a1:
            st.markdown("##### 📞 Anrufen")
            if aircall.is_configured() and lead.get("Telefon"):
                if st.button("Aircall-Klingeln", key=f"call_{lead['id']}"):
                    result = aircall.dial(user_id=0, to=str(lead["Telefon"]))
                    if result.get("status") == "stub":
                        st.warning(result["note"])
                    else:
                        st.success("Klingelt auf deinem Headset.")
            elif lead.get("Telefon"):
                phone = str(lead["Telefon"]).replace(" ", "")
                st.markdown(
                    f"[📞 `{lead['Telefon']}` anrufen (tel:)]"
                    f"(tel:{phone})"
                )
                st.caption("Aircall nicht konfiguriert — tel:-Fallback aktiv.")
            else:
                st.caption("Keine Telefonnummer hinterlegt.")

        # ---- B) Status + Notizen ----------------------------------------
        with a2:
            st.markdown("##### 🎚️ Status-Update")
            options = ["New", "Qualified", "Contacted", "Not interested", "Wrong fit", "Converted"]
            cur = lead["Status"] if lead["Status"] in options else "New"
            new_status = st.selectbox(
                "Neuer Status",
                options,
                index=options.index(cur),
                key=f"status_{lead['id']}",
            )
            note = st.text_input(
                "Notiz anhängen (optional)",
                key=f"note_{lead['id']}",
                placeholder="z. B. 'Setter Call 14:30 — wirkt offen, will Mid-Ticket'",
            )
            if st.button("Speichern", key=f"savestat_{lead['id']}"):
                at.update_lead_status(lead["id"], new_status, note or None)
                st.toast("Aktualisiert.", icon="✅")
                st.rerun()

        st.markdown("---")

        # ---- C) Termin buchen mit Google Meet ---------------------------
        st.markdown("##### 📅 Strategiegespräch + Meet-Link buchen")

        bcol1, bcol2, bcol3 = st.columns([2, 1, 1])
        tomorrow = (datetime.now(TZ) + timedelta(days=1)).date()
        date = bcol1.date_input(
            "Datum",
            value=tomorrow,
            min_value=datetime.now(TZ).date(),
            key=f"date_{lead['id']}",
        )
        hour = bcol2.selectbox(
            "Uhrzeit",
            list(range(9, 20)),
            index=5,  # 14:00 default
            format_func=lambda h: f"{h:02d}:00",
            key=f"hour_{lead['id']}",
        )
        duration = bcol3.selectbox(
            "Dauer (min)",
            [30, 45, 60, 75, 90],
            index=2,
            key=f"dur_{lead['id']}",
        )

        when = datetime.combine(date, time(hour=int(hour)), tzinfo=TZ)
        end_when = when + timedelta(minutes=int(duration))

        if st.checkbox("Kalender-Konflikt prüfen", key=f"chk_{lead['id']}"):
            try:
                if gcal.check_busy(when, end_when):
                    st.warning(
                        "⚠️ Dein Kalender hat in diesem Slot schon einen Termin. "
                        "Buche trotzdem oder wähle eine andere Uhrzeit."
                    )
                else:
                    st.success("Slot ist frei.")
            except Exception as e:
                st.caption(f"Konflikt-Check fehlgeschlagen: {e}")

        if st.button(
            "📅 Termin buchen + Meet-Link erzeugen",
            key=f"book_{lead['id']}",
            type="primary",
        ):
            try:
                event = gcal.create_strategy_call(
                    lead_email=lead["E-Mail"],
                    lead_name=lead["Name"],
                    when=when,
                    duration_min=int(duration),
                )
                at.update_lead_booking(
                    lead_id=lead["id"],
                    call_at=when,
                    meet_link=event["meet_link"],
                    setter_owner=setter_email,
                    new_status="Contacted",
                )
                st.success(
                    f"✅ Termin gebucht für {when.strftime('%a %d.%m. %H:%M')} — "
                    f"[Meet öffnen]({event['meet_link']}) · "
                    f"[Im Calendar öffnen]({event['html_link']})"
                )
                st.toast("Termin gebucht + Lead-Status auf Contacted.", icon="📅")
            except Exception as e:
                st.error(f"Termin-Buchung fehlgeschlagen: {e}")
