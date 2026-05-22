"""Meine Sessions — Liste eigener Sessions + Neue-Session-Modal."""

from __future__ import annotations

import pathlib
import sys
from datetime import datetime, time

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from components import confirm_save_buttons, render_empty_state  # noqa: E402
from integrations.airtable_helpers import (  # noqa: E402
    add_session, for_mentor, load_kunden, load_sessions, update_session,
)
from integrations.auth import require_tool_access  # noqa: E402
from lib.tz import TZ_BERLIN  # noqa: E402


user = require_tool_access("sessions", "write")
mentor_id = user.get("mentor_id")
if not mentor_id:
    st.error("Account ohne Mentor-Link. Bitte beim Admin melden.")
    st.stop()


OUTCOME_OPTIONS = ["Erfolg", "Folgetermin", "Eskalation", "No Show", "Other"]


# -----------------------------------------------------------------------------
# Modal — Neue Session eintragen
# -----------------------------------------------------------------------------

@st.dialog("Neue Session eintragen", width="large")
def add_session_modal(my_mentee_names: list[str]) -> None:
    if not my_mentee_names:
        st.error("Du hast aktuell keine Mentees. Frag den Admin nach einer Zuweisung.")
        return

    with st.form("new_session_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        mentee = col1.selectbox("Mentee *", my_mentee_names)
        sess_date = col2.date_input(
            "Datum *", value=datetime.now(TZ_BERLIN).date(),
        )
        col3, col4 = st.columns(2)
        sess_time = col3.time_input("Uhrzeit", value=time(14, 0))
        dauer = col4.number_input("Dauer (Min) *", min_value=5, max_value=240, value=45, step=5)

        col5, col6 = st.columns(2)
        outcome = col5.selectbox("Outcome *", OUTCOME_OPTIONS)
        nps = col6.slider("NPS (0=schlecht, 10=top)", 0, 10, 8)

        notiz = st.text_area(
            "Notiz (Themen, Hausaufgaben, Beobachtungen)",
            placeholder="Worüber haben wir gesprochen? Was sind die nächsten Schritte?",
        )
        recording_url = st.text_input(
            "Recording-URL (optional)", placeholder="https://...",
        )

        submit = st.form_submit_button(
            "💾 Session eintragen", type="primary", use_container_width=True,
        )

    if submit:
        # Date + Time → ISO mit TZ
        dt = datetime.combine(sess_date, sess_time).replace(tzinfo=TZ_BERLIN)
        try:
            add_session(
                mentor_id    = mentor_id,
                lead_name    = mentee,
                date_iso     = dt.isoformat(),
                dauer_min    = int(dauer),
                outcome      = outcome,
                notiz        = notiz,
                nps          = int(nps),
                aufnahme_url = recording_url,
            )
            st.success(f"✅ Session mit {mentee} eingetragen.")
            st.rerun()
        except (ValueError, RuntimeError) as e:
            st.error(f"{e}")
        except Exception as e:  # noqa: BLE001
            st.error(f"Unerwarteter Fehler: {type(e).__name__}: {e}")


# -----------------------------------------------------------------------------
# Page
# -----------------------------------------------------------------------------

st.title("📅 Meine Sessions")

# Lade eigene Sessions + Mentees
all_sessions = load_sessions()
all_mentees  = load_kunden()
my_sessions  = for_mentor(all_sessions, mentor_id, link_col="Mentor").reset_index(drop=True)
my_mentees   = for_mentor(all_mentees, mentor_id, link_col="Mentor")
my_mentee_names = sorted(my_mentees["Lead"].dropna().tolist()) if not my_mentees.empty else []

# Top-Row: Caption + Add-Button
col_a, col_b = st.columns([4, 1.5])
col_a.caption(f"Liste aller Sessions, die dir zugeordnet sind. Klick rechts um eine neue einzutragen.")
if col_b.button("➕ Neue Session", type="primary", use_container_width=True):
    add_session_modal(my_mentee_names)


# Mini-KPIs
now = pd.Timestamp.now(tz="UTC")
week_ago = now - pd.Timedelta(days=7)
this_week = my_sessions[my_sessions["Date"] >= week_ago] if not my_sessions.empty else pd.DataFrame()
backlog   = my_sessions[my_sessions["NPS"].isna()] if not my_sessions.empty else pd.DataFrame()

kcols = st.columns(4)
kcols[0].metric("Sessions gesamt",       len(my_sessions))
kcols[1].metric("Diese Woche",           len(this_week))
nps_mean = my_sessions["NPS"].dropna().mean() if not my_sessions.empty else float("nan")
kcols[2].metric("⌀ NPS",                 f"{nps_mean:.1f}" if pd.notna(nps_mean) else "—")
kcols[3].metric("Backlog (ohne NPS)",    len(backlog), help="Sessions, bei denen du noch keinen NPS-Wert eingetragen hast")

if my_sessions.empty:
    st.markdown("---")
    render_empty_state(
        'Noch keine Sessions eingetragen. Klick rechts oben "➕ Neue Session" um deine erste anzulegen.',
        icon="📅",
    )
    st.stop()

st.markdown("---")


# NPS-Trend Chart
st.subheader("NPS-Trend")
chart_df = my_sessions.dropna(subset=["NPS"]).sort_values("Date")
if chart_df.empty:
    st.caption("Sessions vorhanden, aber noch keine NPS-Werte.")
else:
    fig = px.line(
        chart_df, x="Date", y="NPS",
        markers=True, range_y=[0, 10],
        hover_data=["Lead", "Outcome"],
    )
    fig.update_layout(
        height=280, margin=dict(l=20, r=20, t=20, b=20),
        yaxis_title="NPS", xaxis_title="",
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")


# Liste
st.subheader("Verlauf")
filtered = my_sessions.sort_values("Date", ascending=False).reset_index(drop=True)

COLS = [1.6, 2.5, 1, 1.5, 1.5, 0.8]
hcols = st.columns(COLS)
hcols[0].markdown("**Datum**")
hcols[1].markdown("**Mentee**")
hcols[2].markdown("**Dauer**")
hcols[3].markdown("**Outcome**")
hcols[4].markdown("**NPS**")
hcols[5].markdown("**Notiz**")
st.markdown("<hr style='margin-top:0; margin-bottom:0.5rem'>", unsafe_allow_html=True)

for _, sess in filtered.iterrows():
    cols = st.columns(COLS)
    dt = sess["Date"]
    if pd.notna(dt):
        cols[0].caption(dt.tz_convert(TZ_BERLIN).strftime("%d.%m.%y %H:%M") if dt.tz else dt.strftime("%d.%m.%y %H:%M"))
    else:
        cols[0].caption("—")
    cols[1].markdown(f"**{sess.get('Lead', '—')}**")
    cols[2].caption(f"{int(sess.get('Dauer (min)') or 0)} min")
    cols[3].markdown(f"`{sess.get('Outcome', '—')}`")
    nps = sess.get("NPS")
    cols[4].markdown(f"`{int(nps)}/10`" if pd.notna(nps) else "`—`")
    notiz = sess.get("Notizen") or ""
    cols[5].caption(notiz[:60] + "..." if len(notiz) > 60 else (notiz or "—"))
