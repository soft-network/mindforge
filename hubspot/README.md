# HubSpot Free CRM — Setup für Phase E

HubSpot fungiert in Phase E als **paralleles CRM neben Airtable** —
identisch zur realen LLP-Architektur (Account `26317639`, EU-Region).
HubSpot übernimmt die Marketing- und Sales-Pipeline; Airtable bleibt
die Operations-Datenbank (Mentoren, Programme, Sessions).

---

## 1. Account anlegen

1. Auf `app.hubspot.com/signup` registrieren mit `net24.twork@gmail.com`.
2. Beim Onboarding-Wizard:
   - Firmenname: **MindForge Demo**
   - Branche: *Education / Coaching*
   - Rolle: *Operations*
   - Mitarbeiterzahl: *1–4*
3. **Wichtig — Region prüfen:** Beim ersten Login zeigt HubSpot dir links
   unten den Account-Bereich. Wenn unter dem Avatar `Hub-ID: nnnn` und
   nicht `app-eu1.hubspot.com` in der URL steht, ist der Account **US-East**.
   Für LLP-Realismus willst du **EU (Frankfurt)** — beim Signup-Schritt
   "Where will you primarily use HubSpot?" → *Germany* wählen.

**Was du nach Schritt 3 in der Hand hast:**
- HubSpot Portal-URL: `https://app-eu1.hubspot.com/contacts/<portal-id>/...`
- Portal-ID (= „Hub-ID") — notieren in deinem `.env`

---

## 2. Custom Contact Properties anlegen

Die folgenden 12 Properties bilden die Quiz-Antworten 1:1 ab. Anlegen
unter **Settings → Properties → Contact properties → Create property**.

Property-Group: **„Quiz Lead Data"** (selbst anlegen, einmalig)

| Label im UI | Internal Name | Type | Field type | Options / Notes |
|---|---|---|---|---|
| Quiz · Business Status | `quiz_business_status` | Single-line text | Single-line text | Werte: `ja`, `nein` |
| Quiz · Years Self-Employed | `quiz_years_self_employed` | Single-line text | Single-line text | Werte: `lt_1`, `1_3`, `gt_3` |
| Quiz · Business Field | `quiz_business_field` | Single-line text | Single-line text | Werte: `coach`, `services`, `digital`, `ecommerce`, `network`, `other` |
| Quiz · Visibility | `quiz_visibility` | Single-line text | Single-line text | Werte: `lt_1k`, `lt_10k`, `gt_10k` |
| Quiz · Team Setup | `quiz_team_setup` | Single-line text | Single-line text | Werte: `solo`, `lt_10`, `gt_10` |
| Quiz · Monthly Revenue | `quiz_monthly_revenue` | Single-line text | Single-line text | Werte: `zero`, `lt_5k`, `lt_10k`, `lt_100k`, `gt_100k` |
| Quiz · Main Wish | `quiz_main_wish` | Single-line text | Single-line text | Werte: `stable`, `quit_job`, `brand`, `freedom`, `5fig` |
| Quiz · Gap (Multi) | `quiz_gap` | Multi-line text | Multi-line text | Komma-separierte Liste der Werte aus Frage 8 |
| Quiz · Time Budget | `quiz_time_budget` | Single-line text | Single-line text | Werte: `lt_1h`, `2_5h`, `5_10h`, `gt_10h` |
| Quiz · Score | `quiz_score` | Number | Number | Range 0–100 |
| Quiz · Completed At | `quiz_completed_at` | Date picker | DateTime | UTC ISO |
| Lead Source · Subdomain | `lead_source_subdomain` | Single-line text | Single-line text | z.B. `quiz.mindforge.demo` |

**Schneller Import via API:** siehe [`properties-export.json`](properties-export.json) —
HubSpot Properties API akzeptiert Bulk-Create. Aufruf-Beispiel:

```bash
curl -X POST "https://api.hubapi.com/crm/v3/properties/contacts/batch/create" \
  -H "Authorization: Bearer $HUBSPOT_PRIVATE_APP_TOKEN" \
  -H "Content-Type: application/json" \
  --data @hubspot/properties-export.json
```

---

## 3. Private App + API-Token erstellen

1. **Settings → Integrations → Private Apps → Create a private app**
2. Name: `MindForge Make Bridge`
3. **Scopes** (minimal):
   - `crm.objects.contacts.read`
   - `crm.objects.contacts.write`
   - `crm.schemas.contacts.read`
   - `crm.objects.deals.read`
   - `crm.objects.deals.write`
   - `automation` (für Workflow-Trigger-Webhooks)
4. **Create app** → Token kopieren (zeigt sich nur **einmal**)
5. Token in `.env` ablegen:
   ```env
   HUBSPOT_PRIVATE_APP_TOKEN=pat-eu1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   HUBSPOT_PORTAL_ID=12345678
   ```

**Token nie ins Git committen** — `.env` ist in `.gitignore`.

---

## 4. Workflow „Hot Lead Routing"

Ziel: Wenn `quiz_score ≥ 50`, soll der Lead automatisch
- als **Marketing Qualified Lead** markiert,
- dem Setter-Owner zugewiesen,
- in einer **Slack-Notification** angekündigt werden.

**Anlegen:** *Automations → Workflows → Create workflow → From scratch
→ Contact-based*

**Trigger:** *Contact enrollment trigger*
- **„Quiz · Score is greater than or equal to 50"**
- AND **„Quiz · Completed At is known"**

**Schritte:**

| # | Aktion | Konfiguration |
|---|---|---|
| 1 | Set property value | `Lifecycle stage = marketingqualifiedlead` |
| 2 | Set property value | `HubSpot owner = Setter-Owner` (Demo: dein eigener User) |
| 3 | Send internal email | An Setter-Mail; Subject: `🔥 Hot Quiz Lead: {{contact.firstname}} ({{contact.quiz_score}})` |
| 4 | Webhook (POST) | URL: Make-Webhook für „HubSpot → Slack-Bridge" (siehe `make-bridge/02-hubspot-to-airtable.md`) |
| 5 | Create task | „Quiz-Lead innerhalb 24h anrufen", fällig in 24h |

**Test:** Manuell Kontakt anlegen mit `quiz_score = 75` → Workflow sollte
sofort triggern. History prüfen unter **Automations → Workflows → Enrollment history**.

Details als Step-by-Step-Walkthrough mit Klick-Pfaden:
[`workflow-design.md`](workflow-design.md).

---

## 5. HubSpot Tracking-Code (optional aber empfohlen)

Wenn du den HubSpot-Tracking-Code zusätzlich zum GTM ins Quiz-Frontend
einbaust, wird genau das simuliert, was LLP live macht: `js-eu1.hs-scripts.com/<portal-id>.js`.

**Nicht nötig für Phase E**, weil der GTM-Container die wichtigsten
Pixel deckt, aber für Realismus empfohlen.

Embed-Snippet (in `quiz-frontend/index.html` vor `</body>`):

```html
<!-- HubSpot Embed Code (optional) -->
<script
  type="text/javascript"
  id="hs-script-loader"
  async defer
  src="//js-eu1.hs-scripts.com/<HUBSPOT_PORTAL_ID>.js"
></script>
```

---

## 6. Free-Tier-Limits

| Limit | Wert | Phase-E-Bedarf | Risiko |
|---|---|---|---|
| Contacts | 1 Mio | < 100 (Demo) | – |
| Custom Properties | 1.000 | 12 | – |
| Workflows | 1 (Free Tier) | 1 | gerade ausreichend |
| API Calls | 100 / 10s (Burst) | < 10/min | – |
| Private Apps | unlimited | 1 | – |
| Forms | 1 (Free) | 0 (Quiz ist eigener Hook) | – |

**Engpass:** Free-Tier erlaubt nur **1 Workflow**. Falls du später
Welle E2 (Sales-Pipeline-Owner-Wechsel) bauen willst, brauchst du
HubSpot Starter (~ 15 €/Monat) oder simulierst weitere Logik im
Make-Szenario.

---

## 7. Nächste Schritte

Nach Setup hier → weiter mit:
1. [`make-bridge/`](../make-bridge/README.md) — Quiz-Webhook → HubSpot + Airtable
2. [`tracking-full/`](../tracking-full/README.md) — GTM + Pixel-Stack
3. [`powerbi-cross-source/`](../powerbi-cross-source/README.md) — HubSpot + Airtable im Dashboard
