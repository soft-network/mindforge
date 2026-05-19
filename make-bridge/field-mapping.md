# Field Mapping HubSpot ↔ Airtable

Master-Übersicht, welches Feld in welchem System Source-of-Truth ist
und welche Make-Scenarien es schreiben.

**Legende:**
- **HS** = HubSpot Source-of-Truth
- **AT** = Airtable Source-of-Truth
- **Shared** = beide Seiten können schreiben (gefährlich, mit Last-Modified-Compare absichern)
- **Immutable** = wird nur einmal beim Anlegen gesetzt

---

## Identity & Contact (Quelle: Quiz Submit → beide)

| Logisches Feld | HubSpot Property | Airtable Field | SoT | Geschrieben von |
|---|---|---|---|---|
| Email | `email` | `Email` | Immutable | Scenario #1 |
| Vorname | `firstname` | `First Name` | HS | Scenario #1, später ggf. Workflow |
| Nachname | `lastname` | `Last Name` | HS | Scenario #1 |
| Telefon | `phone` | `Phone` | HS | Scenario #1 |
| Land | `country` | `Country` | HS | Scenario #1 |

---

## Quiz Data (Quelle: Quiz Submit, dann immutable)

| Logisches Feld | HubSpot Property | Airtable Field | SoT | Geschrieben von |
|---|---|---|---|---|
| Business Status | `quiz_business_status` | `Quiz · Business Status` | Immutable | Scenario #1 |
| Years Self-Empl. | `quiz_years_self_employed` | `Quiz · Years Self-Employed` | Immutable | Scenario #1 |
| Branche | `quiz_business_field` | `Quiz · Field` | Immutable | Scenario #1 |
| Sichtbarkeit | `quiz_visibility` | `Quiz · Visibility` | Immutable | Scenario #1 |
| Team-Aufstellung | `quiz_team_setup` | `Quiz · Team` | Immutable | Scenario #1 |
| Monatsumsatz | `quiz_monthly_revenue` | `Quiz · Revenue` | Immutable | Scenario #1 |
| Wunsch | `quiz_main_wish` | `Quiz · Wish` | Immutable | Scenario #1 |
| Lücken (Multi) | `quiz_gap` | `Quiz · Gap` (Multi-Select) | Immutable | Scenario #1 |
| Zeitbudget | `quiz_time_budget` | `Quiz · Time Budget` | Immutable | Scenario #1 |
| Score | `quiz_score` | `Quiz Score` | Immutable | Scenario #1 |
| Completed At | `quiz_completed_at` | `Quiz Completed` | Immutable | Scenario #1 |
| Source-Subdomain | `lead_source_subdomain` | `Source Subdomain` | Immutable | Scenario #1 |

---

## Sales & Marketing (Quelle: HubSpot, Sync nach Airtable)

| Logisches Feld | HubSpot Property | Airtable Field | SoT | Geschrieben von |
|---|---|---|---|---|
| Lifecycle Stage | `lifecyclestage` | `Lifecycle Stage` | **HS** | Scenario #2 |
| Lead Status | `hs_lead_status` | `Lead Status` | **HS** | Scenario #2 |
| Owner | `hubspot_owner_id` | `Owner` | **HS** | Scenario #2 |
| Deal-Stage | `dealstage` (am Deal) | `Deal Stage` (in Leads) | **HS** | Scenario #2 (Deal-Hook) |
| Closed-Won-Date | `closedate` | `Closed Date` | **HS** | Scenario #2 |
| Deal-Value | `amount` | `Deal Value` | **HS** | Scenario #2 |

---

## Operations & Customer Success (Quelle: Airtable, Sync nach HubSpot)

| Logisches Feld | HubSpot Property | Airtable Field | SoT | Geschrieben von |
|---|---|---|---|---|
| Mentor-ID | `mentor_id` | `Mentor (link to Mentors table)` | **AT** | Scenario #3 |
| Mentor-Name | `mentor_name` | `Mentor Name (Lookup)` | **AT** | Scenario #3 |
| Onboarding-Status | `onboarding_status` | `Onboarding Status` (Select) | **AT** | Scenario #3 |
| Programm | `program` | `Program (link to Programs)` | **AT** | Scenario #3 |
| Programm-Start | `program_start` | `Program Start Date` | **AT** | Scenario #3 |
| Last Session | `last_session_date` | `Last Session Date` (Rollup) | **AT** | Scenario #3 |
| NPS | `nps` | `NPS` (avg Rollup) | **AT** | Scenario #3 |
| LTV | `ltv` | `LTV` (Sum of Deals) | **AT** | Scenario #3 |
| Customer Health | `customer_health` | `Customer Health Score` (Formula) | **AT** | Scenario #3 |

---

## Meta-Felder (für Conflict-Resolution)

| Logisches Feld | HubSpot Property | Airtable Field | SoT | Zweck |
|---|---|---|---|---|
| Last Source | `_last_source` | `_last_source` | wird vom schreibenden Szenario gesetzt | Loop-Prevention |
| HubSpot Last-Mod | `hs_lastmodifieddate` | `HS Last Modified` (synced) | HS | Last-Wins-Tie-Breaker |
| Airtable Last-Mod | `at_last_modified` (synced) | `Last Modified Time` | AT | Last-Wins-Tie-Breaker |

---

## Disjunkte Field-Sets (Loop-Prevention)

Damit Szenarien #2 und #3 sich nicht gegenseitig triggern:

| Szenario | schreibt | liest |
|---|---|---|
| #1 (Quiz Submit) | Quiz-Felder + Contact-Identity (in beide Systeme) | – |
| #2 (HubSpot→Airtable) | nur Sales/Marketing-Felder in Airtable | HubSpot |
| #3 (Airtable→HubSpot) | nur Operations-Felder in HubSpot | Airtable |

Da die Field-Sets disjunkt sind, kann kein Szenario sein eigenes
Trigger-Feld schreiben — kein Loop.

---

## DSGVO-Hinweis

- Bei Löschung des Kontakts in HubSpot → manueller Cleanup in Airtable nötig (kein Auto-Sync vorgesehen, weil Operations-Daten ggf. archiviert werden müssen)
- Beim Right-to-Be-Forgotten-Request: Email als Lookup nutzen → manuelle Anonymisierung in beiden Systemen
- E-Mail-Hash für Tracking (CAPI, GA4 MP, TikTok) hat keine Personenbezug-Pflicht, weil pseudonymisiert
