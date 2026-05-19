# Scenario #3 — Airtable → HubSpot

**Trigger:** Custom Webhook (gefeuert von Airtable-Automation)
**Auslöser:** Operations-Daten ändern sich in Airtable (Mentor-Zuordnung, Onboarding-Status, Last-Session-Date)
**Ops pro Run:** ~3

---

## Zweck

Airtable ist Source-of-Truth für Operations-Daten:
- **Mentor-Zuordnung** (welcher Mentor betreut welchen Kunden)
- **Onboarding-Status** (Onboarding-Call-Datum, Welcome-Pack versendet)
- **Customer Health** (Last-Session-Date, NPS, Engagement-Score)
- **Programm-Zuordnung** (Inner Circle, OBK, Retreat)

Wenn sich diese Werte in Airtable ändern, sollen sie nach HubSpot
propagiert werden, damit:
- Marketing-Lookalike-Audiences korrekte Customer-Tags haben,
- HubSpot-Sales-Reports den vollen Customer-Lifecycle sehen,
- Account-Manager beim Customer-Anruf den aktuellen Status sehen.

---

## Airtable Automation (Source-Side)

In Airtable einrichten unter **Automations → Create Automation**:

**Trigger:** *When record matches conditions*
- Table: `Clients`
- Conditions:
  - `Mentor` is not empty, OR
  - `Onboarding Status` is not empty, OR
  - `Last Session Date` updated within 1 day

**Aktion:** *Send a webhook*
- URL: `https://hook.eu2.make.com/<MAKE_WEBHOOK_AIRTABLE_CHANGE>`
- Method: `POST`
- Headers: `Content-Type: application/json`
- Body:
  ```json
  {
    "_source": "airtable-automation",
    "record_id": "{{record_id}}",
    "email": "{{Email}}",
    "mentor_id": "{{Mentor}}",
    "mentor_name": "{{Mentor Name (Lookup)}}",
    "onboarding_status": "{{Onboarding Status}}",
    "last_session_date": "{{Last Session Date}}",
    "nps": "{{NPS}}",
    "program": "{{Program}}",
    "program_start": "{{Program Start Date}}",
    "lifetime_value": "{{LTV}}"
  }
  ```

---

## Make-Module

### 1. Custom Webhook
- Name: `airtable_change_webhook`

### 2. Search HubSpot Contact by Email
- HubSpot → Search Contacts
- Filter: `email = {{1.email}}`
- Limit: 1

### 3. Filter — Skip if not found
- Stop if `length({{2.results}}) = 0`
- Log warning → Slack `#bridge-warnings`

### 4. HubSpot — Update Contact
- Contact-ID: `{{2.results[0].id}}`
- Properties:
  - `mentor_id` = `{{1.mentor_id}}`
  - `mentor_name` = `{{1.mentor_name}}`
  - `onboarding_status` = `{{1.onboarding_status}}`
  - `last_session_date` = `{{1.last_session_date}}`
  - `nps` = `{{1.nps}}`
  - `program` = `{{1.program}}`
  - `program_start` = `{{1.program_start}}`
  - `ltv` = `{{1.lifetime_value}}`
- **Wichtig:** custom-Header oder Hidden-Property `_last_source = "airtable-automation"`
  setzen, damit Szenario #2 nicht wieder triggert (siehe `README.md` Conflict-Resolution).

### 5. Webhook Response
- `{ "ok": true, "hubspot_contact_id": "{{2.results[0].id}}" }`

---

## Custom Properties in HubSpot (zusätzlich zu Quiz-Properties)

Diese 8 Properties müssen in HubSpot vor dem Szenario angelegt werden
(zusätzlich zu den 12 Quiz-Properties aus `hubspot/properties-export.json`).
Group: **Customer Operations**.

| Internal Name | Type | Quelle |
|---|---|---|
| `mentor_id` | Single-line | Airtable `Clients.Mentor` |
| `mentor_name` | Single-line | Airtable `Clients.Mentor Name (Lookup)` |
| `onboarding_status` | Single-line | Airtable `Clients.Onboarding Status` |
| `last_session_date` | DateTime | Airtable `Clients.Last Session Date` |
| `nps` | Number | Airtable `Clients.NPS` |
| `program` | Single-line | Airtable `Clients.Program` |
| `program_start` | Date | Airtable `Clients.Program Start Date` |
| `ltv` | Number | Airtable `Clients.LTV` |

---

## Ping-Pong-Prevention

Da Szenario #2 (HubSpot→Airtable) und Szenario #3 (Airtable→HubSpot)
beide auf Updates reagieren könnten, gibt es theoretisch eine
Loop-Gefahr. Drei Schutz-Mechanismen:

1. **Source-Tagging**: Szenario #3 setzt in HubSpot `_last_source = "airtable-automation"`. Szenario #2 hat als ersten Filter:
   `Skip if hubspot.properties._last_source = "airtable-automation"`
2. **Field-Ownership-Matrix**: Szenario #3 schreibt **nur** Operations-Felder. Szenario #2 schreibt **nur** Sales/Marketing-Felder. Disjunkte Field-Sets.
3. **Debounce 30s**: Beide Szenarien haben eine `Sleep 30s`-Action am Anfang, die bei wiederholtem Trigger derselben Record-ID innerhalb von 30s den Lauf abbricht.

---

## Test-Plan

1. Manuell in Airtable: `Clients`-Record mit Email `test+ops@example.com` anlegen
2. `Mentor`-Feld auf einen bestehenden Wert setzen
3. Erwartet:
   - Make-Szenario läuft (sichtbar in Make → Scenarios → History)
   - HubSpot-Contact mit `email = test+ops@example.com` hat `mentor_id` gefüllt
   - Kein Loop — Szenario #2 läuft NICHT erneut
