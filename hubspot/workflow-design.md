# HubSpot Workflow: „Hot Lead Routing"

Step-by-step-Walkthrough zum Anlegen des Phase-E-Workflows in der
HubSpot-UI. Free-Tier erlaubt exakt 1 Workflow — wir nutzen ihn für
die Hot-Lead-Eskalation.

---

## Trigger

**Settings → Workflows → Create workflow → Start from scratch**

- Type: **Contact-based**
- Name: `Hot Quiz Lead Routing v1`
- Enrollment criteria — **Filter group 1** (alle Kriterien AND-verknüpft):
  - Contact property → `Quiz · Score` → *is greater than or equal to* → `50`
  - AND `Quiz · Completed At` → *is known*
  - AND `Lifecycle stage` → *is none of* → `customer`, `evangelist`
- Re-enrollment: **off** (jeder Lead durchläuft den Workflow nur 1×)

---

## Aktionen

### Aktion 1 — Set property value

- Property: `Lifecycle stage`
- Value: `marketingqualifiedlead`

### Aktion 2 — Branch (If/Then)

Bedingung:
- `Quiz · Score is greater than or equal to 70` → **Hot Branch**
- Else → **Warm Branch**

### Hot Branch

**2a — Set property value**
- `HS Lead Status = NEW`
- `HubSpot owner = <Setter-User-DE>` (Free-Tier: dein eigener User)

**2b — Send internal email**
- To: `setter-de@mindforge.demo` (oder dein E-Mail-Alias)
- Subject: `🔥 HOT Quiz Lead: {{contact.firstname}} {{contact.lastname}} (Score {{contact.quiz_score}})`
- Body:
  ```
  Hot-Lead via Quiz-Funnel.

  Name: {{contact.firstname}} {{contact.lastname}}
  E-Mail: {{contact.email}}
  Telefon: {{contact.phone}}
  Land: {{contact.country}}

  Score: {{contact.quiz_score}} / 100
  Branche: {{contact.quiz_business_field}}
  Umsatz: {{contact.quiz_monthly_revenue}}
  Wunsch: {{contact.quiz_main_wish}}
  Lücken: {{contact.quiz_gap}}
  Zeit: {{contact.quiz_time_budget}}

  → HubSpot: https://app-eu1.hubspot.com/contacts/{{portal_id}}/contact/{{contact.vid}}
  ```

**2c — Webhook**
- Method: `POST`
- URL: `https://hook.eu2.make.com/<HOT_LEAD_WEBHOOK_ID>` (siehe `make-bridge/02-hubspot-to-airtable.md`)
- Authentication: none (Webhook-URL ist das Secret)
- Payload includes: All contact properties
- Note: Make-Szenario übernimmt Slack-Posting + Airtable-Update

**2d — Create task**
- Title: `Quiz-Lead innerhalb 24h anrufen — {{contact.firstname}}`
- Due in: `1 day`
- Assigned to: HubSpot owner
- Type: Call

### Warm Branch

**3a — Set property value**
- `HS Lead Status = NEW`

**3b — Delay**
- 2 hours

**3c — Webhook** (analog Hot, andere Make-URL)

**3d — Create task**
- Title: `Quiz-Lead nachfassen — {{contact.firstname}}`
- Due in: `2 days`
- Type: E-Mail

---

## Goal (optional)

Setze ein Goal für den Workflow:
- Goal property: `Lifecycle stage`
- Value: `salesqualifiedlead`

So siehst du in den Workflow-Performance-Reports, wie viele Hot-Leads
tatsächlich vom Setter zum SQL aufgewertet werden.

---

## Test

1. Manuell Contact anlegen mit:
   - First name: `Test`, Last name: `Hot`
   - E-Mail: `test+hot@example.com`
   - `quiz_score = 75`, `quiz_completed_at = now()`
2. Erwartet: Workflow triggert sofort, History zeigt 4 Aktionen ausgeführt
3. Slack-Channel sollte eine Nachricht erhalten (sofern Make-Webhook live)
4. Task ist in HubSpot Sales → Tasks angelegt

---

## Limits

Free-Tier:
- 1 Workflow erlaubt
- 5 Aktionen pro Workflow (mit Verzweigungen kommt man schnell ans Limit)
- Workflow-Performance-Reports nur mit Marketing Hub Starter (~ 18 €/Monat)

Falls Limits sprengen: Logik nach Make verschieben — Make-Szenario
zieht alle 5 Min neue Hot-Leads via HubSpot REST API und macht die
Aktionen selbst. Demo-Setup nutzt aber den Free-Tier-Workflow für
Realitätsbezug.
