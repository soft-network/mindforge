# Power BI — Cross-Source Dashboard

Power-BI-Workspace, das **HubSpot** (Marketing/Sales) und **Airtable**
(Operations) zu einem gemeinsamen Customer-Lifecycle-Dashboard joint.

Erweitert das Phase-1-Dashboard (`05-powerbi-dashboard.md`), das nur
Airtable nutzt.

---

## 1. Architektur

```
                ┌───────────────────┐
                │  HubSpot CRM      │
                │  (Contacts +      │
                │   Deals)          │
                └─────────┬─────────┘
                          │ REST API (Bearer Token)
                          │ via Web.Contents
                          ▼
                ┌───────────────────┐       ┌───────────────────┐
                │  Power BI Desktop │◀──────│   Airtable Base   │
                │  (Power Query M)  │ REST  │   (4 Tables +     │
                │                   │       │    Mentoren)       │
                └─────────┬─────────┘       └───────────────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ Data Model (Star) │
                │   - fact tables   │
                │   - dim tables    │
                │   - DAX Measures  │
                └─────────┬─────────┘
                          │
                          ▼
                ┌───────────────────┐
                │ 4 Reports         │
                │  - Marketing      │
                │  - Sales Pipeline │
                │  - Mentor Util.   │
                │  - Customer Health│
                └───────────────────┘
```

---

## 2. Files

| Datei | Inhalt |
|---|---|
| [`data-model.md`](data-model.md) | Tabellen, Beziehungen, Power-Query-M-Code |
| [`dax-measures.md`](dax-measures.md) | Alle DAX-Maße mit Erklärung |
| [`reports/`](reports/) | Screenshots der 4 fertigen Reports |
| `pbix-source.txt` | Hinweis: `.pbix` liegt außerhalb von Git (siehe `.gitignore`) |

---

## 3. Setup

### 3.1 Connections

**HubSpot:**
- Get Data → **Web** → URL: `https://api.hubapi.com/crm/v3/objects/contacts?limit=100&properties=email,firstname,lastname,phone,country,lifecyclestage,hs_lead_status,quiz_score,quiz_tier,quiz_business_field,quiz_monthly_revenue,quiz_completed_at,mentor_id,program,ltv,nps`
- Authentication: **Bearer Token** (Private App Token aus `hubspot/README.md`)
- Pagination: Power Query M Loop bis `paging.next.after` leer

**Airtable:**
- Get Data → **Web** → URL: `https://api.airtable.com/v0/{BASE_ID}/Kunden?pageSize=100`
- Authentication: **Bearer Token** (Personal Access Token)
- Pagination: ähnlich, mit `offset`-Parameter

### 3.2 Power Query Transformations

Pro Quelle:
- Records flach klopfen (`Table.ExpandRecordColumn`)
- Datentypen casten (Date, Number, Text)
- Normalisierte Spaltennamen (`E-Mail`, `LifecycleStage`, `QuizScore`, …)
- E-Mail-Spalte als Primary-Key markieren

### 3.3 Beziehungen

| Source | Target | Type | Cardinality |
|---|---|---|---|
| `hubspot_contacts[E-Mail]` | `airtable_leads[E-Mail]` | Many-to-One | 1:1 (Bridge) |
| `airtable_leads[E-Mail]` | `airtable_sessions[E-Mail]` | One-to-Many | 1:n |
| `airtable_leads[Mentor]` | `airtable_mentors[MentorID]` | Many-to-One | n:1 |
| `airtable_leads[Program]` | `airtable_programs[ProgramID]` | Many-to-One | n:1 |

---

## 4. Die vier Reports

### Report 1 — Marketing Funnel (HubSpot-only)
- Lead Volume per Source / Campaign / Date
- Conversion Rate Quiz Submit → MQL → SQL → Customer
- Cost per Hot Lead (wenn Ad-Spend-Daten verbunden)
- Drill-Down auf `quiz_business_field` und `quiz_monthly_revenue`

### Report 2 — Sales Pipeline (HubSpot Deals)
- Open Deals / Stage / Owner
- Average Time-to-Close pro Stage
- Quiz-Score-Verteilung in Won vs Lost
- Top-Performer Closer-Leaderboard

### Report 3 — Mentor Utilization (Airtable)
- Sessions per Mentor per Week
- Average NPS per Mentor
- Customer Load (active customers / mentor)
- Mentor-Auslastung in % der Kapazität

### Report 4 — Customer Health (Joined HubSpot + Airtable)
- Customer Health Score Verteilung (Heatmap)
- Last-Session-Date Distribution (Drop-off-Risk)
- LTV per Quiz-Tier (Hot Leads → höchster LTV?)
- Churn-Risiko basierend auf Engagement-Drop

---

## 5. Deployment

Phase-E-Scope: nur **Power BI Desktop**. Workspace-Publish auf
Power-BI-Service ist mit Free-Lizenz möglich, aber RLS braucht Pro
(~ 10 €/Monat).

Für die Demo reicht Desktop + Screenshots in
[`reports/`](reports/).

Falls Workspace-Publish gewünscht: separate Phase E.5 als „nächster
Schritt" dokumentiert.

---

## 6. Refresh-Strategie

Phase-E-Setup: manuell via „Refresh"-Button im Power BI Desktop.

Produktions-Setup (out-of-scope):
- Power BI Gateway zu beiden APIs
- Scheduled Refresh alle 4h
- Incremental Refresh über `Last Modified Time` (Power BI Premium)

---

## 7. Demo-Datensatz

Für eine sinnvolle Demo brauchen wir ~50 Test-Records in beiden Systemen.
Setup:

1. **Quiz mehrfach durchspielen** mit verschiedenen Antworten (~ 20 Leads)
2. **In HubSpot manuell** weitere 30 Contacts anlegen mit verschiedenen
   `lifecyclestage`-Werten (über CSV-Import)
3. **In Airtable** zugehörige Sessions + Mentor-Zuordnungen anlegen
4. **Make-Szenario #3** triggert Sync → Power BI hat End-to-End-Records

---

## 8. Business-Wert

Power-BI-Cross-Source zeigt das zentrale Wertversprechen dieser Phase:
ein Dashboard, das HubSpot-Marketing-Daten und
Airtable-Operations-Daten in einem Funnel-Bild zusammenführt. Damit
sind Fragen wie *„welche Quiz-Antwort-Kombinationen bringen den
höchsten LTV?"* beantwortbar — etwas, das mit nur einem der beiden
Systeme nicht geht.
