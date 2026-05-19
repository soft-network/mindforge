# Schritt 9 — Monitoring (UptimeRobot + Statuspage)

**Ziel:** Production-Mindset zeigen — wenn der Webhook stirbt, **weißt du es vor den Kunden**.

**Schwerpunkt:** Reliability statt nur Features.

---

## Architektur

```
[Make Webhook URL]   ◄─── ping every 5min ───  [UptimeRobot]
[Landing Page URL]   ◄─── ping every 5min ───        │
[Streamlit App URL]  ◄─── ping every 5min ───        │
                                                     │
                              on failure ─────────►  ├─► Slack Webhook
                                                     ├─► Email
                                                     └─► Statuspage Update
                                                              │
                                                              ▼
                                              [status.mindforge.demo]
                                              public incident timeline
```

---

## Tool 1: UptimeRobot

### Account erstellen

1. https://uptimerobot.com/signUp
2. Free Plan: 50 Monitors, 5-Min-Intervall, unbegrenzt Alerts
3. Verifikations-Email bestätigen

### Monitor 1: Make Webhook

1. **+ Add New Monitor** → Type: **HTTP(s)**
2. **Friendly Name:** `MindForge Make Webhook`
3. **URL:** `https://hook.eu2.make.com/YOUR_WEBHOOK_TOKEN`
4. **Monitoring Interval:** 5 Minuten
5. **Monitor Timeout:** 30 Sekunden
6. **Advanced Settings:**
   - HTTP Method: **POST**
   - Custom HTTP Headers: `Content-Type: application/json`
   - POST Value (raw JSON):
     ```json
     {"_uptime_check": true, "name": "uptimerobot", "email": "monitor@uptimerobot.com"}
     ```
   - Custom HTTP Status: `200, 201, 202`
7. **Save**

→ Wichtig: In Make musst du `_uptime_check === true` filtern, sonst landen Monitor-Calls als Fake-Leads in Airtable.

#### Make-Anpassung für Uptime-Check

Im Make-Scenario direkt nach Webhook:
- Filter: `{{1._uptime_check}}` ist nicht `true`
- → echte Leads laufen weiter, Uptime-Pings werden 200-OK beantwortet aber nicht verarbeitet

### Monitor 2: Landing Page

1. Type: **HTTP(s)** (Default GET)
2. **URL:** `https://<dein-user>.github.io/mindforge-pipeline-demo/`
3. **Interval:** 5 Min
4. **Alert Contacts:** Slack + Email
5. Save

### Monitor 3: Streamlit Coach Admin (später, Phase C)

1. Type: **HTTP(s)** (Default GET)
2. **URL:** `https://mindforge-coach-XXX.run.app/healthz` (GCP Cloud Run später)
3. Save

### Alert Contacts einrichten

1. **My Settings** → **Alert Contacts** → **+ Add Alert Contact**
2. Type: **Email** → deine Email + Test
3. Type: **Slack** → folge der Slack-Webhook-Anleitung von UptimeRobot
   - In Slack: App "Incoming Webhooks" hinzufügen, Channel `#mindforge-alerts`, Webhook-URL kopieren
   - In UptimeRobot: Slack Webhook URL einfügen
4. **Test** klicken — du solltest sofort eine Slack-Message bekommen

### Notification-Settings

Pro Monitor:
- **Notify when monitor goes down:** ✅
- **Notify when monitor returns up:** ✅
- **Send notification after X failed checks:** 2 (vermeidet False Positives)

---

## Tool 2: Statuspage by Atlassian

### Account erstellen

1. https://www.atlassian.com/software/statuspage
2. Free Plan: 2 Pages, 100 Subscribers, unbegrenzt Components
3. Workspace: `MindForge`

### Page Setup

1. **Page name:** MindForge System Status
2. **Page URL:** `mindforge-demo.statuspage.io` (oder Custom Domain)
3. **Page description:** "Live-Status aller MindForge Services"

### Components anlegen

1. **+ Add Component**
2. Erstelle 3 Components:
   - `Landing Page` (Group: Customer-Facing)
   - `Lead Webhook` (Group: Backend)
   - `Coach Admin Dashboard` (Group: Internal)

### Automatische Updates via UptimeRobot

UptimeRobot ↔ Statuspage haben offizielle Integration:

1. In Statuspage: **Components** → **Edit** → **Integrations** → **Webhooks**
2. Generate Webhook URL für jede Component
3. In UptimeRobot pro Monitor: **Alert Contacts** → Add Webhook Type
4. URL einfügen + JSON Payload Template:
   ```json
   {
     "component_id": "STATUSPAGE_COMPONENT_ID",
     "status": "*alertType*"
   }
   ```

→ Down auf UptimeRobot → automatisches Incident in Statuspage → Public Page aktualisiert.

### Manuelle Incident-Posts (für ehrliche Kommunikation)

Bei größeren Vorfällen ergänzt du manuell:
- **Incident Name:** "Lead Webhook Delays — Investigating"
- **Status:** Investigating / Identified / Monitoring / Resolved
- **Message:** Was los ist, was du tust, ETA
- **Affected Components:** Lead Webhook

---

## Setup-Checkliste

- [ ] UptimeRobot Account erstellt
- [ ] Monitor 1 (Make Webhook) eingerichtet, POST mit `_uptime_check`
- [ ] Monitor 2 (Landing Page) eingerichtet
- [ ] Slack Alert Contact eingerichtet und getestet
- [ ] Email Alert Contact eingerichtet und getestet
- [ ] Make-Scenario filtert `_uptime_check === true` aus
- [ ] Statuspage Account erstellt
- [ ] 3 Components angelegt
- [ ] UptimeRobot ↔ Statuspage Webhook-Integration konfiguriert
- [ ] Test: Make-Scenario deaktivieren → 10 Min warten → Slack-Alert + Statuspage-Update kommt

---

## Technische Eigenschaften

| Aspekt | Umsetzung |
|---|---|
| Monitoring | UptimeRobot Multi-Monitor Setup (5-Min-Intervall) |
| System-Integration | UptimeRobot ↔ Statuspage via Webhook |
| Reliability | Automatisches Alert-Routing (Slack + Email) |
| Stakeholder-Kommunikation | Öffentliche Statuspage als Single Source of Truth |

---

## Zeitaufwand: ~1 Stunde

**Nächster Schritt:** [10-meta-capi-tracking.md](10-meta-capi-tracking.md) — Meta Pixel + CAPI
