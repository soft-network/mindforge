# Schritt 4 — Make Scenario bauen (Webhook → Airtable → Slack)

**Ziel:** Eingehender Webhook von Landing-Page-Formular → validiert → Lead in Airtable angelegt → bei Hot Lead Slack-Notification.

**Schwerpunkte:** robuste Validierung und Error-Handling.

---

## Architektur des Szenarios

```
[1] Webhook Trigger
        │
        ▼
[2] Tools: Validate & Transform   ← Custom JS für Cleanup
        │
        ▼
[3] Router
   ├──► [3a] Filter: E-Mail valid?      ──► [4] Airtable: Search existing
   │                                              │
   │                                              ▼
   │                                       [5] Filter: kein Duplikat
   │                                              │
   │                                              ▼
   │                                       [6] Airtable: Create Lead
   │                                              │
   │                                              ▼
   │                                       [7] Filter: score ≥ 70?
   │                                              │
   │                                              ▼
   │                                       [8] Slack: Notify channel
   │
   └──► [3b] Else: Webhook Response 400 (invalid)
```

---

## Step-by-Step Build

### 1. Webhook erstellen

- Make → **Create a new scenario**
- Add module: **Webhooks → Custom webhook**
- Click **Add** → Name: `mindforge-leads`
- **Kopiere die Webhook-URL** — wir testen damit gleich

### 1.5. Uptime-Check-Filter (für UptimeRobot)

UptimeRobot pingt den Webhook alle 5 Min mit einem `_uptime_check: true`-Flag
(siehe [09-monitoring.md](09-monitoring.md)). Filtere ihn früh aus, damit keine
Fake-Leads in Airtable landen.

Direkt nach Step 1 einbauen:

- Add module: **Webhooks → Webhook response**
- Status: `200`
- Body: `{"status":"uptime_ok"}`
- **Filter direkt davor:** `{{1._uptime_check}}` ist `true`
- Direkt danach: **Flow Control → Commit / Stop** (Make terminiert den Pfad nach Response)

→ Echte Leads passieren den Filter, Uptime-Pings stoppen hier mit 200 OK.

### 2. Test-Payload schicken

In einem Terminal (oder Postman):

```bash
curl -X POST <DEINE_WEBHOOK_URL> \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Anna Müller",
    "email": "anna.mueller@example.com",
    "phone": "+49 170 1234567",
    "source": "Google Ads",
    "interest_program": "Career Boost",
    "notes": "Möchte in 6 Monaten den Job wechseln, interessiert an Kompaktkurs."
  }'
```

→ Im Make-Scenario klick **Determine data structure** — das Sample wird empfangen.

### 3. Validate Module — Tools

- Add module: **Tools → Set multiple variables**
- Variablen:
  - `valid_email`: `{{contains(1.email; "@")}}` (Boolean)
  - `clean_phone`: `{{replace(1.phone; " "; "")}}`
  - `source_clean`: `{{if(length(1.source) > 0; 1.source; "Other")}}`

### 4. Router

- Add module: **Flow Control → Router**

**Route A (valid):**
- Filter: `valid_email` = `true`

**Route B (invalid):**
- Filter: `valid_email` = `false`
- Add: **Webhooks → Webhook response**
- Status: `400`
- Body: `{"error": "Invalid email"}`

### 5. Duplikat-Check (auf Route A)

- Add: **Airtable → Search records**
- Base: MindForge CRM
- Table: Leads
- Formula: `{E-Mail} = "{{1.email}}"`
- Limit: 1

### 6. Filter: kein Duplikat

- Add filter zwischen Search und Create:
- Condition: `Total number of bundles` = `0`

### 7. Create Lead in Airtable

- Add: **Airtable → Create a record**
- Table: Leads
- Felder mappen:
  - `Name` ← `1.name`
  - `E-Mail` ← `1.email`
  - `Telefon` ← `clean_phone`
  - `Source` ← `source_clean`
  - `Interesse` ← Suche per Linked-Field-Lookup mit `1.interest_program`
  - `Status` ← `New`
  - `Notizen` ← `1.notes`

### 8. Score-Lead Cloud Function aufrufen

- Add: **HTTP → Make a request**
- **URL:** Output von `bash deploy-score-function.sh` (z.B. `https://score-lead-XXXX-ew.a.run.app`)
- **Method:** POST
- **Body type:** Raw → JSON
- **Headers:** `Content-Type: application/json`
- **Request content:**
  ```json
  {"lead_id": "{{7.id}}"}
  ```
- **Parse response:** Yes

Die Cloud Function liest den Lead aus Airtable, sucht das verlinkte Programm
samt Preis, berechnet den vollen Score (inkl. Programm-Faktor und Recency)
und schreibt `Lead Score` + `Status` direkt zurück. Die Response enthält
`{score, breakdown, status}` für die folgenden Module.

Setup der Function: siehe [08-gcp-deployment.md](08-gcp-deployment.md).

### 9. (optional) E-Mail-Domain-Enrichment

Erweiterung nach `score-lead`: zweite Cloud Function (`enrich-email`)
klassifiziert die E-Mail-Domain als business vs. personal und liefert einen
Score-Bonus/-Malus. Setup: [08-gcp-deployment.md](08-gcp-deployment.md).

**Step 9a — Function aufrufen:**

- Add module: **HTTP → Make a request**
- URL: Output von `bash deploy-function.sh` (z.B. `https://enrich-email-XXXX-ew.a.run.app`)
- Method: POST
- Body Raw JSON: `{"email": "{{1.email}}"}`
- Parse response: Yes
- Response enthält: `{type, is_business, is_high_value, score_adjustment}`

**Step 9b — Adjustment in Airtable schreiben:**

- Add module: **Airtable → Update a record**
- Record ID: `{{7.id}}`
- Lead Score: `{{8.score + 9a.score_adjustment}}` (Base aus Step 8 + Bonus/Malus aus 9a)
- Optional Notizen-Anhang: `"E-Mail type: " + {{9a.type}}`

> **Hinweis zum Hot-Lead-Filter unten:** Step 10 nutzt standardmäßig
> `{{8.score}}`. Wenn du Step 9 aktivierst, ersetze dort durch den
> adjustierten Wert: `{{8.score + 9a.score_adjustment}}`.

### 10. Hot Lead Notification

- Add filter: `{{8.score}}` ≥ `70` (Score aus der HTTP-Response von Step 8)
- Add module: **Slack → Create a message**
- Channel: `#mindforge-leads`
- Message:
  ```
  Neuer Hot Lead! ({{8.score}}/100)

  Name: {{1.name}}
  E-Mail: {{1.email}}
  Telefon: {{clean_phone}}
  Interesse: {{1.interest_program}}
  Source: {{source_clean}}

  Notizen: {{1.notes}}

  → Airtable: https://airtable.com/<base>/<table>/{{7.id}}
  ```

### 11. Webhook Response

- Add am Ende: **Webhooks → Webhook response**
- Status: `200`
- Body: `{"status": "ok", "lead_id": "{{7.id}}", "score": {{8.score}}}`

### 12. Error Handler

- Auf dem Airtable-Create-Modul: Rechtsklick → **Add error handler** → **Resume**
- Logge Fehler in einem Google Sheet oder per E-Mail an dich selbst

### 13. Scheduling

- Bottom-left: Toggle auf **ON**
- Schedule: **Immediately as data arrives**

---

## Test-Cases

| Input | Erwartetes Verhalten |
|---|---|
| Vollständiger Lead, Score 80 | Airtable Record + Slack-Message + 200 Response |
| Vollständiger Lead, Score 40 | Airtable Record + 200 Response (keine Slack) |
| E-Mail = "abc" (kein @) | 400 Response, kein Airtable Record |
| Doppelter Lead | 200 Response, kein neues Record |

---

## Technische Eigenschaften

| Aspekt | Umsetzung |
|---|---|
| Workflow-Orchestrierung | Komplettes Make-Scenario mit Router |
| Webhooks (REST) | Webhook In + strukturiertes Out |
| Datenvalidierung | E-Mail-Check, Telefon-Cleanup |
| Error Handling | Resume-Handler auf Airtable-Modul |
| Business Logic | Pre-Score-Berechnung mit Make-Formulae |
| Integration | Airtable + Slack |

---

## Zeitaufwand: ~2 Stunden (inkl. Testen)

**Nächster Schritt:** [05-powerbi-dashboard.md](05-powerbi-dashboard.md) — BI-Reporting
