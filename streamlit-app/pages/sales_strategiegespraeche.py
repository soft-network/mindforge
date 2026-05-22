"""Strategiegespräche — heutige Closer-Calls + Convert-Workflow.

Workflow:
    1. Sales-Mitarbeiter sieht heute anstehende Strategiegespräche (Termin am = heute)
    2. Vor dem Call: Klick auf Lead → sieht Quiz-Antworten + bisherige Notizen
    3. Nach dem Call: "Convert"-Button öffnet Modal mit:
         - Programm-Auswahl (Pflicht)
         - Mentor: Auto-Vorschlag aus Programm.Mentoren (niedrigste Auslastung)
                   oder manuell override
         - MRR-Start setzen
    4. Klick Convert → Lead.Status = Converted, Kunde-Record entsteht,
       Mentor wird automatisch zugewiesen, Caches invalidiert
"""

from __future__ import annotations

import pathlib
import sys

import pandas as pd
import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from components import confirm_save_buttons, render_empty_state  # noqa: E402
from integrations.airtable_helpers import (  # noqa: E402
    convert_lead_to_kunde,
    load_leads,
    load_mentor_lookup,
    load_programs,
    pick_least_loaded_mentor,
)
from integrations.auth import require_tool_access  # noqa: E402
from lib.tz import TZ_BERLIN  # noqa: E402


user = require_tool_access("strategie", "write")
my_email = user.get("email", "")


# -----------------------------------------------------------------------------
# Convert-Modal
# -----------------------------------------------------------------------------

@st.dialog("Lead konvertieren → Kunde", width="large")
def convert_modal(lead: pd.Series) -> None:
    st.subheader(f"🎯 {lead['Name']}")
    st.caption(
        f"📧 {lead.get('E-Mail', '—')}  ·  "
        f"📦 Interesse: {', '.join(lead.get('Interesse') or []) or '—'}"
    )

    # Quiz-Snapshot
    if lead.get("Branche") or lead.get("Monatsumsatz"):
        with st.expander("Quiz-Antworten", expanded=False):
            st.write(
                f"**Branche:** {lead.get('Branche') or '—'}  ·  "
                f"**Umsatz:** {lead.get('Monatsumsatz') or '—'}  ·  "
                f"**Wunsch:** {lead.get('Hauptwunsch') or '—'}"
            )

    st.markdown("---")

    # Programm-Auswahl
    df_prog = load_programs()
    if df_prog.empty:
        st.error("Keine Programme verfügbar — bitte Admin kontaktieren.")
        return

    prog_names = sorted(df_prog["Name"].dropna().tolist())
    chosen_prog = st.selectbox(
        "Programm *",
        prog_names,
        key=f"conv_prog_{lead['id']}",
    )

    # Mentor-Pool aus Programm + Auto-Suggest
    mentor_lookup = load_mentor_lookup()
    prog_row = df_prog[df_prog["Name"] == chosen_prog].iloc[0]
    pool_ids   = prog_row["Mentoren"] or []
    pool_names = prog_row["Mentor-Pool-Namen"] or []

    if pool_ids:
        suggested_id = pick_least_loaded_mentor(pool_ids)
        suggested_name = mentor_lookup.get(suggested_id, "?") if suggested_id else None
        st.info(
            f"💡 **Mentor-Pool für {chosen_prog}:** {', '.join(pool_names)}  \n"
            f"**Auto-Vorschlag** (niedrigste Auslastung): **{suggested_name}**"
        )
        # Manueller Override
        OVERRIDE_AUTO = f"⚡ Auto: {suggested_name}"
        mentor_choice = st.selectbox(
            "Mentor zuweisen",
            [OVERRIDE_AUTO] + sorted(pool_names),
            key=f"conv_mentor_{lead['id']}",
            help="Auto-Vorschlag basiert auf aktueller Auslastung. Du kannst manuell überschreiben.",
        )
        if mentor_choice == OVERRIDE_AUTO:
            chosen_mentor_id = suggested_id
        else:
            chosen_mentor_id = next(
                (mid for mid, n in mentor_lookup.items() if n == mentor_choice),
                None,
            )
    else:
        st.warning(
            f"⚠️ Kein Mentor-Pool für {chosen_prog} hinterlegt. "
            f"Admin muss Pool in Programm-Verwaltung pflegen. "
            f"Du kannst jetzt manuell zuweisen:"
        )
        manual_names = ["— (kein Mentor)"] + sorted(mentor_lookup.values())
        manual_choice = st.selectbox(
            "Mentor manuell wählen",
            manual_names,
            key=f"conv_mentor_manual_{lead['id']}",
        )
        chosen_mentor_id = None
        if manual_choice != "— (kein Mentor)":
            chosen_mentor_id = next(
                (mid for mid, n in mentor_lookup.items() if n == manual_choice),
                None,
            )

    st.markdown("---")
    mrr = st.number_input(
        "MRR-Start (EUR/Monat)",
        min_value=0.0, step=50.0,
        value=float(prog_row.get("Price (EUR)") or 0),
        help="Default = Programm-Preis. Anpassbar bei Discounts/Vereinbarungen.",
        key=f"conv_mrr_{lead['id']}",
    )

    st.markdown("---")
    save, cancel = confirm_save_buttons(
        save_label="✅ Konvertieren",
        key_prefix=f"conv_modal_{lead['id']}",
    )
    if save:
        try:
            kunde_rec, used_mentor_id = convert_lead_to_kunde(
                lead_id=lead["id"],
                lead_name=lead["Name"],
                programm_name=chosen_prog,
                mentor_id=chosen_mentor_id,
                mrr_eur=mrr,
                converted_by_email=my_email,
            )
            mentor_name = mentor_lookup.get(used_mentor_id, "—") if used_mentor_id else "—"
            st.success(
                f"✅ {lead['Name']} ist jetzt Kunde · "
                f"Programm: {chosen_prog} · Mentor: {mentor_name} · "
                f"MRR: € {mrr:.0f}"
            )
            st.balloons()
            st.rerun()
        except (ValueError, RuntimeError) as e:
            st.error(f"{e}")
        except Exception as e:  # noqa: BLE001
            st.error(f"Convert fehlgeschlagen: {type(e).__name__}: {e}")
    if cancel:
        st.rerun()


# -----------------------------------------------------------------------------
# Page
# -----------------------------------------------------------------------------

st.title("🎯 Strategiegespräche")
st.caption("Heutige Closer-Calls + Convert-Workflow. Nach dem Gespräch → ✅ Konvertieren.")

df_leads = load_leads()
if df_leads.empty:
    render_empty_state("Keine Leads in der Datenbank.", icon="📋")
    st.stop()


# Self-Scope-Filter (Setter == eigene Email)
mine = df_leads[df_leads["Setter"].str.lower() == my_email.lower()]

# Nur Leads mit Termin
mine_with_termin = mine[mine["Termin am"].notna()] if not mine.empty else mine

if mine_with_termin.empty:
    render_empty_state(
        "Du hast aktuell keine gebuchten Strategiegespräche. "
        "Buch sie in Hot Leads (Setter Daily).",
        icon="🎯",
    )
    st.stop()


# Filter: heute vs. später
now = pd.Timestamp.now(tz="UTC")
today_start = now.normalize()
tomorrow_start = today_start + pd.Timedelta(days=1)

today_calls = mine_with_termin[
    (mine_with_termin["Termin am"] >= today_start) &
    (mine_with_termin["Termin am"] < tomorrow_start)
].sort_values("Termin am")

later_calls = mine_with_termin[mine_with_termin["Termin am"] >= tomorrow_start].sort_values("Termin am")
past_open_calls = mine_with_termin[
    (mine_with_termin["Termin am"] < today_start) &
    (mine_with_termin["Status"].isin(["New", "Qualified", "Contacted"]))
].sort_values("Termin am", ascending=False)


# KPI-Strip
kcols = st.columns(4)
kcols[0].metric("Heute",        len(today_calls))
kcols[1].metric("Kommende Tage", len(later_calls))
kcols[2].metric("Offen (Past)", len(past_open_calls), help="Termine in der Vergangenheit, Lead noch nicht abgeschlossen")
kcols[3].metric("Convert-Rate", f"{int((mine['Status']=='Converted').sum())} ·", help="Anzahl konvertierter Leads")


# Sections
def render_call_section(title: str, df: pd.DataFrame, show_convert: bool = True) -> None:
    """Render eine Section: heute / später / offen-past."""
    if df.empty:
        return
    st.markdown("---")
    st.subheader(title)
    for _, lead in df.iterrows():
        with st.container(border=True):
            cols = st.columns([2.5, 2, 2, 1.5, 1])
            cols[0].markdown(f"**{lead['Name']}**")
            cols[0].caption(f"{lead.get('E-Mail', '')}  ·  Score {int(lead.get('Lead Score') or 0)}")

            termin = lead.get("Termin am")
            if pd.notna(termin):
                cols[1].markdown(f"🕐 {termin.tz_convert(TZ_BERLIN).strftime('%d.%m. %H:%M')}")

            cols[2].caption(
                f"Interesse: {', '.join(lead.get('Interesse') or []) or '—'}"
            )
            cols[3].markdown(f"`{lead.get('Status', '—')}`")

            link = lead.get("Meet-Link")
            if link:
                cols[4].markdown(f"[Meet ↗]({link})")

            if show_convert and lead["Status"] != "Converted":
                if st.button(
                    "✅ Konvertieren",
                    key=f"conv_btn_{lead['id']}",
                    type="primary",
                ):
                    convert_modal(lead)


render_call_section("📅 Heute", today_calls)
render_call_section("🕓 Kommende Tage", later_calls, show_convert=False)
render_call_section("⚠️ Past – noch offen", past_open_calls)
