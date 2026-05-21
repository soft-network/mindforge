"""Lead-Karte als Streamlit-Expander — wiederverwendbar.

Wird in Leads-Page (Browse-Modus) und Setter-Daily (Action-Modus) benutzt.
Aktionen sind über `actions=`-Callbacks anpassbar — die Komponente selbst
kennt keine Airtable-Schreibvorgänge.
"""

from __future__ import annotations

from typing import Callable, Optional

import pandas as pd
import streamlit as st


def tier_badge(score: int) -> str:
    """Emoji-Badge je nach Score-Tier — wiederverwendbar in Setter Daily + Leads."""
    if score >= 85:
        return "🔥 HOT"
    if score >= 70:
        return "🌶️ WARM-HOT"
    if score >= 40:
        return "💧 WARM"
    return "❄️ COLD"


def render_lead_summary(lead: pd.Series) -> None:
    """Read-only Lead-Header — Name, E-Mail, Telefon, Land, Quiz-Antworten."""
    st.markdown(
        f"**📧** {lead.get('E-Mail', '—')}  &nbsp;·&nbsp;  "
        f"**📞** `{lead.get('Telefon', '—') or '—'}`  &nbsp;·&nbsp;  "
        f"**🌍** {lead.get('Land', '—') or '—'}"
    )
    if any(lead.get(k) for k in ("Branche", "Monatsumsatz", "Hauptwunsch", "Zeitbudget")):
        st.markdown(
            f"**Branche:** {lead.get('Branche', '—') or '—'}  &nbsp;·&nbsp;  "
            f"**Umsatz:** {lead.get('Monatsumsatz', '—') or '—'}  &nbsp;·&nbsp;  "
            f"**Wunsch:** {lead.get('Hauptwunsch', '—') or '—'}  &nbsp;·&nbsp;  "
            f"**Zeit:** {lead.get('Zeitbudget', '—') or '—'}"
        )
    if lead.get("Source"):
        st.caption(f"Quelle: {lead['Source']}")


def render_lead_card(
    lead: pd.Series,
    *,
    expanded: bool = False,
    on_action: Optional[Callable[[str, dict], None]] = None,
) -> None:
    """Lead als ausklappbare Karte.

    Args:
        lead:       Eine Zeile aus dem Lead-DataFrame (pd.Series).
        expanded:   Karte standardmäßig ausgeklappt?
        on_action:  Optional. Callback (action_name, payload) → None.
                    Wird vom Aufrufer angegeben um Schreibvorgänge zu handhaben.
                    Beispiel actions: "status_update", "book_call", "add_note".
    """
    score = int(lead.get("Lead Score") or lead.get("Quiz Score", 0))
    name = lead.get("Name", "Unbekannt")
    branche = lead.get("Branche") or lead.get("Quiz · Branche") or "—"
    umsatz  = lead.get("Monatsumsatz") or lead.get("Quiz · Monatsumsatz") or "—"

    label = f"{tier_badge(score)} · Score {score} · {name} · {branche} · {umsatz}"

    with st.expander(label, expanded=expanded):
        render_lead_summary(lead)

        if lead.get("Notizen"):
            st.text_area(
                "Notizen",
                value=lead["Notizen"],
                height=80,
                disabled=True,
                key=f"notes_{lead['id']}",
            )

        if lead.get("Termin am") is not None and str(lead.get("Termin am")) != "NaT":
            st.success(f"📅 Termin: {lead['Termin am']}")
            if lead.get("Meet-Link"):
                st.markdown(f"🎥 [Meet öffnen]({lead['Meet-Link']})")

        if on_action is not None:
            # Aufrufer rendert seine eigene Action-Sektion (Status-Update,
            # Termin-Buchung, etc.) durch Aufruf von on_action.
            on_action("render_actions", {"lead": lead})
