# Scenario #1 — Quiz Submit

**Trigger:** Custom Webhook
**Auslöser:** Quiz-Frontend POST mit JSON-Payload
**Ops pro Run:** ~6 (siehe `README.md`)

---

## Module (in Reihenfolge)

### 1. Custom Webhook
- Add **Webhooks → Custom webhook**
- Name: `quiz_submit_webhook`
- Data structure: aus Sample-Payload generieren (siehe `sample-payloads/01-quiz-submit.json`)
- URL aus dem Webhook-Modul kopieren → in `quiz-frontend/config.js`

### 2. Router
- Vier Pfade: HubSpot · Airtable · Pixels · Slack

### 3a. Pfad „HubSpot": Search Contact by Email
- Module: **HubSpot → Search Contacts**
- Filter:
  - `properties.email` = `{{1.contact.email}}`
- Limit: 1
- *(Wenn nicht gefunden → Aggregator gibt leere Liste zurück)*

### 3b. Pfad „HubSpot": Router (existiert / existiert nicht)

#### Existiert (Contact-ID vorhanden):
**HubSpot → Update a contact**
- Object ID: `{{output of step 3a}}`
- Properties: alle 12 Quiz-Properties (Mapping siehe `field-mapping.md`)
  - `quiz_business_status`, `quiz_years_self_employed`, `quiz_business_field`, …
  - `quiz_score`
  - `quiz_completed_at = {{1.meta.submitted_at}}`
  - `lead_source_subdomain = {{parseURL(1.meta.source_url).hostname}}`

#### Existiert nicht:
**HubSpot → Create a contact**
- E-Mail: `{{1.contact.email}}`
- First name: `{{1.contact.first_name}}`
- Last name: `{{1.contact.last_name}}`
- Phone: `{{1.contact.phone}}`
- Country/Region: `{{1.contact.country}}`
- + alle 12 Quiz-Properties
- `lifecyclestage = lead`
- `hs_lead_status = NEW`

### 4. Pfad „Airtable": Search Records
- Module: **Airtable → Search Records**
- Base: `MindForge CRM`
- Table: `Leads`
- Formula: `{Email} = "{{1.contact.email}}"`
- Max records: 1

### 4b. Pfad „Airtable": Update vs Create

#### Wenn Record existiert:
**Airtable → Update a Record**
- Record ID: `{{output of step 4}}`
- Felder updaten gemäß Mapping (siehe `field-mapping.md`)

#### Wenn nicht:
**Airtable → Create a Record**
- Base: `MindForge CRM`, Table: `Leads`
- Alle Felder aus Payload mappen

### 5. Pfad „Slack": Filter + Post
- Filter: nur weiter wenn `{{1.quiz.tier}} = "hot"` oder `"warm"`
- Module: **Slack → Create a Message**
- Channel: `#sales-hot-leads` (Hot) bzw. `#sales-warm-leads` (Warm)
- Text (Blocks):
  ```
  🔥 *{{1.quiz.tier | upper}} Lead* — Score {{1.quiz.score}}
  *Name:* {{1.contact.first_name}} {{1.contact.last_name}}
  *E-Mail:* {{1.contact.email}}
  *Telefon:* {{1.contact.phone}}
  *Branche:* {{1.quiz.business_field}}
  *Umsatz:* {{1.quiz.monthly_revenue}}
  *Wunsch:* {{1.quiz.main_wish}}
  *Zeit:* {{1.quiz.time_budget}}
  *Lücken:* {{1.quiz.gap}}

  🔗 <https://app-eu1.hubspot.com/contacts/{{HUBSPOT_PORTAL_ID}}/contact/{{3b.id}}|In HubSpot öffnen>
  🔗 <https://airtable.com/{{AIRTABLE_BASE_ID}}/tbl{{LEADS_TABLE}}/{{4b.id}}|In Airtable öffnen>
  ```

### 6. Pfad „Pixels": Drei HTTP-Module

**Meta CAPI:**
- HTTP → Make a request
- POST `https://graph.facebook.com/v18.0/{META_PIXEL_ID}/events`
- Headers: `Content-Type: application/json`
- Body (JSON):
  ```json
  {
    "data": [{
      "event_name": "Lead",
      "event_time": "{{toUnix(1.meta.submitted_at)}}",
      "event_id": "{{1.meta.event_id}}",
      "event_source_url": "{{1.meta.source_url}}",
      "action_source": "website",
      "user_data": {
        "em": ["{{sha256(lower(1.contact.email))}}"],
        "ph": ["{{sha256(normalize_phone(1.contact.phone))}}"],
        "fn": ["{{sha256(lower(1.contact.first_name))}}"],
        "ln": ["{{sha256(lower(1.contact.last_name))}}"],
        "country": ["{{sha256(lower(1.contact.country))}}"],
        "client_user_agent": "{{1.meta.user_agent}}"
      },
      "custom_data": {
        "currency": "EUR",
        "value": 0,
        "lead_score": "{{1.quiz.score}}",
        "lead_tier": "{{1.quiz.tier}}"
      }
    }],
    "test_event_code": "{{if(1.meta.testMode; 'TEST12345'; null)}}",
    "access_token": "{{META_ACCESS_TOKEN}}"
  }
  ```

**GA4 Measurement Protocol:**
- POST `https://www.google-analytics.com/mp/collect?api_secret={{GA4_API_SECRET}}&measurement_id={{GA4_MEASUREMENT_ID_A}}`
- Body:
  ```json
  {
    "client_id": "{{1.meta.event_id}}",
    "events": [{
      "name": "generate_lead",
      "params": {
        "value": 0,
        "currency": "EUR",
        "lead_score": "{{1.quiz.score}}",
        "lead_tier": "{{1.quiz.tier}}",
        "event_id": "{{1.meta.event_id}}",
        "engagement_time_msec": 1
      }
    }]
  }
  ```
- (Stream B identisch mit `GA4_MEASUREMENT_ID_B`)

**TikTok Events API:**
- POST `https://business-api.tiktok.com/open_api/v1.3/event/track/`
- Headers: `Access-Token: {{TIKTOK_ACCESS_TOKEN}}`
- Body:
  ```json
  {
    "event_source": "web",
    "event_source_id": "{{TIKTOK_PIXEL_ID}}",
    "data": [{
      "event": "CompleteRegistration",
      "event_time": "{{toUnix(1.meta.submitted_at)}}",
      "event_id": "{{1.meta.event_id}}",
      "user": {
        "email": "{{sha256(lower(1.contact.email))}}",
        "phone": "{{sha256(normalize_phone(1.contact.phone))}}"
      },
      "page": { "url": "{{1.meta.source_url}}" },
      "properties": {
        "value": 0, "currency": "EUR",
        "content_name": "Quiz Submit",
        "content_type": "lead"
      }
    }],
    "test_event_code": "{{if(1.meta.testMode; 'TEST'; null)}}"
  }
  ```

### 7. Webhook Response
- HTTP-Status: `200`
- Body:
  ```json
  {
    "ok": true,
    "event_id": "{{1.meta.event_id}}",
    "hubspot_contact_id": "{{coalesce(3b.id; 3c.id)}}",
    "airtable_record_id": "{{coalesce(4b.id; 4c.id)}}",
    "score": "{{1.quiz.score}}",
    "tier": "{{1.quiz.tier}}"
  }
  ```

---

## Error-Handling

- **Try/Catch-Route** an HubSpot und Airtable-Steps anhängen
- Bei Fehler: Webhook Response mit `ok=false` + `error_code`
- Frontend zeigt dem User „Übermittlung fehlgeschlagen, bitte erneut versuchen"
- Make sendet zusätzlich Slack-DM an Operations-Channel mit Stack-Trace

---

## Was der Webhook **nicht** macht

- E-Mail an den Lead → übernimmt HubSpot-Workflow (siehe `hubspot/workflow-design.md`)
- Owner-Zuordnung → ebenfalls HubSpot-Workflow
- Mentor-Zuordnung → erst nach Closer-Abschluss, dann via Szenario #3
