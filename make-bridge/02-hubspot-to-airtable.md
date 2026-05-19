# Scenario #2 — HubSpot → Airtable + Slack

**Trigger:** Custom Webhook (gefeuert vom HubSpot-Workflow)
**Auslöser:** Lead-Status-Änderung in HubSpot (Lifecycle, Owner, etc.)
**Ops pro Run:** ~3

---

## Zweck

HubSpot ist die Source-of-Truth für Marketing/Sales-Daten. Wenn dort
ein Lead-Status sich ändert (z.B. Lifecycle: Lead → MQL → SQL → Customer,
oder Owner-Wechsel Setter → Closer), muss das in Airtable propagiert
werden, damit Operations-Reports konsistent sind.

---

## Module

### 1. Custom Webhook
- Name: `hubspot_status_webhook`
- URL aus dem HubSpot-Workflow (Aktion „Webhook") referenzieren

### 2. Iterator (HubSpot sendet Properties als Array)
- Source: `properties` Array vom HubSpot-Payload

### 3. Set Variable (Source-Tag)
- Variable: `_source = "hubspot-workflow"`
- Zweck: Verhindert dass Szenario #3 (Airtable→HubSpot) später triggert

### 4. Airtable — Search Records
- Base: `MindForge CRM`
- Table: `Leads`
- Formula: `{Email} = "{{1.contact.email}}"`
- Max records: 1

### 5. Router

#### 5a. Wenn Record gefunden:
**Airtable → Update a Record**
- Record-ID: `{{4.id}}`
- Felder:
  - `Lifecycle Stage` = `{{1.properties.lifecyclestage.value}}`
  - `Owner` = `{{1.properties.hubspot_owner_id.value}}`
  - `Lead Status` = `{{1.properties.hs_lead_status.value}}`
  - `Last Modified by HubSpot` = `{{now()}}`
  - `_source` = `hubspot-workflow`

#### 5b. Wenn nicht gefunden:
- Log warning → Slack `#bridge-warnings`
- Webhook Response: `{ "ok": false, "reason": "lead-not-in-airtable" }`

### 6. Slack — Notify (Konditional)
- Filter: nur wenn `{{1.properties.lifecyclestage.value}} = "customer"`
- Channel: `#sales-wins`
- Message: `🎉 New customer: {{1.contact.first_name}} {{1.contact.last_name}} — closed by {{1.properties.hubspot_owner_id.value}}`

### 7. Webhook Response
- `{ "ok": true, "airtable_updated": "{{5a.id}}" }`

---

## Idempotency

Wenn der HubSpot-Workflow mehrfach feuert (z.B. weil zwei Properties
gleichzeitig geändert wurden), darf das Airtable-Update nicht doppelt
laufen.

**Lösung:** Vor dem Update prüfen, ob `Lifecycle Stage` in Airtable
bereits dem neuen Wert entspricht — wenn ja, skip.

```
Filter: {{4.fields.lifecycleStage}} ≠ {{1.properties.lifecyclestage.value}}
```

---

## Field-Mapping

| HubSpot Property | Airtable Field | Source-of-Truth |
|---|---|---|
| `lifecyclestage` | `Lifecycle Stage` | **HubSpot** |
| `hubspot_owner_id` | `Owner` | **HubSpot** |
| `hs_lead_status` | `Lead Status` | **HubSpot** |
| `email` | `Email` | shared (immutable Dedup-Key) |
| `phone` | `Phone` | **HubSpot** |
| `quiz_score` | `Quiz Score` | shared (in Scenario #1 berechnet) |

Vollständige Tabelle siehe `field-mapping.md`.
