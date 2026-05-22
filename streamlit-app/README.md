# MindForge Coach Admin — Streamlit-App

Internes Dashboard mit Email+Passwort-Login, drei Rollen-Sichten
(Hauptadmin · Sales · Mentor) und Convert-Workflow (Lead → Mentee mit
Auto-Mentor-Routing). Datenquelle ist Airtable, Auth läuft über
bcrypt-gehashte Passwörter in einer eigenen `Benutzer`-Tabelle.

## Lokales Setup (5 Minuten)

### Voraussetzungen
- Python 3.12+
- [`uv`](https://docs.astral.sh/uv/) installiert
- Airtable-Base + Personal-Access-Token mit `data.records:read/write` + `schema.bases:read/write` Scopes

### Schritt-für-Schritt

```bash
# 1) ins App-Verzeichnis
cd streamlit-app

# 2) Dependencies installieren (legt .venv an)
uv sync

# 3) secrets.toml anlegen
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# → öffnen und befüllen:
#     AIRTABLE_API_TOKEN
#     AIRTABLE_BASE_ID
#     BOOTSTRAP_ADMIN_EMAIL    = "deine@email.de"
#     BOOTSTRAP_ADMIN_PASSWORD = "TempPasswort123"
#     [google_oauth] für Setter-Daily-Calendar (optional)

# 4) Initial-Hauptadmin in Airtable.Benutzer anlegen
uv run python scripts/seed_first_admin.py \
    --name "Dein Name" \
    --email "deine@email.de" \
    --password "TempPasswort123"

# 5) App starten
uv run streamlit run app.py
```

Browser öffnet auf `http://localhost:8501`. Login mit Email + Passwort
aus Schritt 4 → du landest mit Hauptadmin-Rolle im Dashboard.

## Deployment auf Streamlit Community Cloud

1. Repo nach GitHub pushen (Branch z. B. `phase-e-streamlit-mvp`)
2. In Streamlit Cloud neue App anlegen, Branch wählen, **Main file path = `streamlit-app/app.py`**
3. **Manage app → Secrets** → den Inhalt von `.streamlit/secrets.toml`
   reinkopieren (inkl. `BOOTSTRAP_ADMIN_EMAIL` + `BOOTSTRAP_ADMIN_PASSWORD`)
4. Auf der Cloud einmal `seed_first_admin.py` ausführen
   (lokal mit Cloud-Credentials, oder per Streamlit-Cell)
5. Bei Code-Updates mit neuen Files: **Manage app → Reboot**, weil
   der Worker-Python-Cache initialisierte Module sonst nicht neu lädt

## Rollen + Permissions

Drei Rollen, definiert in `lib/permissions.py` (`ROLE_MATRIX`):

| Rolle | Was sie macht |
|---|---|
| **Hauptadmin** | Volle Verwaltung: Leads, Mentoren, Programme (inkl. Mentor-Pool-Zuweisung), CS, Benutzer-Lifecycle. Sieht Cross-Source-Dashboard + Performance-Reports. |
| **Sales** | Setter+Closer kombiniert. Eigene Hot-Lead-Queue, Strategiegespräche, Convert-Workflow Lead→Mentee mit Auto-Mentor-Routing aus dem Programm-Pool. |
| **Mentor** | Eigene Mentees + Sessions. Trägt neue Sessions ein (Datum, Dauer, NPS), updatet Onboarding-Stages. Read-only Sicht auf eigene Stamm-Daten. |

Die Permission-Matrix kennt **13 Tools** × **3 Rollen**. Beispiele:
- Mentor darf `mentees` schreiben → aber `is_self_scoped(...) == True`, also
  filter im Loader auf eigene Mentees.
- Sales darf `hot_leads` voll, Hauptadmin nur lesend (Monitoring).
- Nur Hauptadmin darf `benutzer` und `programme` schreiben.

Jede Page beginnt mit `require_tool_access(tool, action)` — blockiert
Direkt-URL-Zugriff für nicht-berechtigte Rollen.

## Architektur

```
streamlit-app/
├── app.py                          ← Entry-Point: Page-Config, Login-Gate,
│                                     rolle-abhängige st.navigation,
│                                     Sidebar-User-Footer
│
├── lib/                            ← Pure Python (keine streamlit-Imports)
│   ├── auth_security.py            → bcrypt hash/verify
│   ├── permissions.py              → ROLE_MATRIX + can() + is_self_scoped()
│   ├── kpis.py                     → alle KPI-Berechnungen
│   ├── filters.py                  → DataFrame-Filter pro Domäne
│   ├── health.py                   → Customer-Health-Score (Doku-Formel)
│   └── tz.py                       → Europe/Berlin-Helper
│
├── integrations/                   ← Externes I/O
│   ├── auth.py                     → Login-Flow, current_user(),
│   │                                 require_tool_access(), Sidebar-Footer
│   ├── airtable_helpers.py         → Loader, Writer, Convert-Workflow
│   ├── google_calendar.py          → User-OAuth für Setter-Daily-Buchung
│   └── aircall.py                  → Click-to-Call-Stub (Demo)
│
├── components/                     ← Wiederverwendbare UI-Bausteine
│   ├── __init__.py                 → render_empty_state, confirm_save_buttons
│   ├── kpi_row, cs_kpi_row, mentor_kpi_row
│   ├── funnel_chart, source_chart
│   ├── mentor_capacity_chart, specialization_chart
│   ├── onboarding_funnel, health_distribution, mrr_chart
│   └── lead_card
│
├── pages/                          ← Streamlit-Pages
│   ├── 1_Dashboard.py              (Admin: Cross-Source-Bento)
│   ├── 2_Leads.py                  (Admin)
│   ├── 3_Setter_Daily.py           (Sales: Hot-Lead-Queue + Cal-Buchung)
│   ├── 4_Programme.py              (Admin: Card-Grid + Mentor-Pool-Edit)
│   ├── 5_Mentoren.py               (Admin: Tabs Übersicht/Verwaltung)
│   ├── 6_Customer_Success.py       (Admin: Tabs Übersicht/Verwaltung)
│   ├── 7_Benutzer.py               (Admin: User-Lifecycle)
│   ├── admin_pipeline.py           (Admin: Kanban-View Lead-Funnel)
│   ├── admin_performance.py        (Admin: 3 Tabs Sales/Mentor/Programm)
│   ├── mentor_cockpit.py
│   ├── mentor_mentees.py           (Mentor: nur eigene)
│   ├── mentor_sessions.py          (Mentor: + Neue Session)
│   ├── mentor_aufgaben.py          (Mentor: auto-generiert)
│   ├── mentor_engagements.py       (Mentor: Vertrags-Sicht)
│   ├── mentor_profil.py            (Mentor: read-only)
│   ├── sales_cockpit.py
│   ├── sales_strategiegespraeche.py (Sales: Convert-Modal)
│   ├── sales_meine_leads.py        (Sales: eigene Pipeline)
│   └── sales_conversions.py        (Sales: Erfolgsliste)
│
└── scripts/                        ← Einmalige Setup-Skripte
    ├── seed_first_admin.py         → Bootstrap-Hauptadmin in Airtable
    └── seed_demo.py                → Demo-Daten (Mentor-Pools, Sessions, …)
```

## Airtable-Schema

App nutzt diese Tabellen:

| Tabelle | Felder (Auswahl) |
|---|---|
| **Leads** | Name, E-Mail, Status, Quiz Score, Source, Setter, Mentor *(Override-Link)* |
| **Kunden** | Lead *(Text-Join)*, Program *(Text)*, Status, Onboarding Status, MRR (EUR), LTV, Mentor *(Link)* |
| **Mentoren** | Name, E-Mail, Stadt, Kapazität pro Woche, Spezialisierung, Status |
| **Sessions** | Date, Lead *(Text-Join)*, Outcome, NPS, Dauer (min), Mentor *(Link)* |
| **Programme** | Name, Category, Price (EUR), Mentoren *(Multi-Link → Pool für Auto-Routing)* |
| **Benutzer** | Name, E-Mail, Passwort-Hash *(bcrypt)*, Rolle, Status, Mentor-Link |

Joins werden teilweise Python-side gemacht (z. B. `Aktive Kunden`,
`Avg NPS`, `Customer Health Score`), weil die Airtable Meta-API keine
Count/Rollup-Felder via API anlegen kann.

## Workflows in der Demo

### Hauptadmin
- 👤 **Benutzer** → ➕ Neuer Benutzer (Sales oder Mentor anlegen)
- 🏆 **Programme** → ✏️ Mentor-Pool zuweisen (Multi-Select)
- 📊 **Dashboard** für Cross-Source-Übersicht
- 🏆 **Performance** für Tab-basierte Analytics (Sales/Mentor/Programm)

### Sales-Workflow (Lead → Mentee)
- 📞 **Setter Daily** → Hot Lead anrufen → Termin buchen (Google Cal)
- 🎯 **Strategiegespräche** → Call führen → ✅ Konvertieren
  - Programm wählen → Auto-Mentor-Vorschlag aus Pool (niedrigste Auslastung)
  - Override möglich → MRR-Start setzen → Confirm
  - Lead.Status → `Converted`, Kunde-Record entsteht mit Mentor-Link

### Mentor-Workflow (operativer Coach)
- 🎯 **Cockpit**: KPIs + Warnungen + NPS-Trend
- 📅 **Meine Sessions** → ➕ Neue Session (Mentee, Datum, NPS, Notiz)
- 🧑‍🎓 **Meine Mentees** → ✏️ Onboarding-Stage updaten
- ✅ **Aufgaben** → auto-generierte TODOs (Onboarding-Backlog,
  Churn-Risk, Sessions ohne NPS)

## Bekannte Limitationen

- **Demo-Daten sind klein**: 46 Leads, 4 Kunden, 13 Sessions, 8 Mentoren,
  5 Programme. Die Features sind aber auf beliebige Größen ausgelegt.
- **Mentor-Email-Match** kommt aus `Benutzer.E-Mail`, nicht aus `Mentoren.E-Mail`
  — der Mentor-Link in `Benutzer` ist die Authoritative Beziehung.
- **Audit-Trail**: `Angelegt von` ist in `Benutzer` auditiert. `Converted by`
  in Kunden ist als Phase-2 vorgesehen (Schema-Erweiterung nötig).
- **`Letzte Anmeldung`** wird per Best-Effort in `update_last_login()` gesetzt
  — wenn das Schreiben fehlschlägt (z. B. Airtable down), läuft Login trotzdem.
