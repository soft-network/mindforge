# Make Bridge HubSpot ↔ Airtable

Drei Make-Szenarien, die in Phase E die Datenflüsse zwischen Quiz-Frontend,
HubSpot (Marketing/Sales-CRM) und Airtable (Operations-DB) orchestrieren.

| # | Szenario | Trigger | Datei |
|---|---|---|---|
| 1 | **Quiz Submit** | Webhook (Frontend) | [`01-quiz-submit-scenario.md`](01-quiz-submit-scenario.md) |
| 2 | **HubSpot → Airtable + Slack** | Webhook (HubSpot Workflow) | [`02-hubspot-to-airtable.md`](02-hubspot-to-airtable.md) |
| 3 | **Airtable → HubSpot** | Airtable Automation | [`03-airtable-to-hubspot.md`](03-airtable-to-hubspot.md) |

Ergänzend:
- [`field-mapping.md`](field-mapping.md) — Master-Mapping HubSpot ↔ Airtable
- [`sample-payloads/`](sample-payloads/) — JSON-Beispiele aller drei Flows

---

## Architektur

```
                    [Quiz-Frontend]
                          │
                          │ POST /webhook/quiz_submit
                          ▼
                   ┌─────────────────────┐
                   │ Make Scenario #1    │
                   │ Quiz Submit         │
                   │                     │
                   │ Webhook → Validate  │
                   │   → Score-Check     │
                   │   → Branch:         │
                   │     ├─ HubSpot upsert (Contact + 12 Properties)
                   │     ├─ Airtable upsert (Leads-Tabelle)
                   │     ├─ Slack hot-lead ping
                   │     └─ Pixel server-side
                   │         ├─ Meta CAPI
                   │         ├─ GA4 Measurement Protocol
                   │         └─ TikTok Events API
                   └─────────────────────┘

                    [HubSpot Workflow]
                          │
                          │ POST /webhook/hubspot_status
                          ▼
                   ┌─────────────────────┐
                   │ Make Scenario #2    │
                   │ HubSpot → Airtable  │
                   │                     │
                   │ Webhook → Match by  │
                   │   email → Update    │
                   │   Airtable-Lead     │
                   │   (Stage, Owner)    │
                   └─────────────────────┘

                    [Airtable Automation]
                          │
                          │ POST /webhook/airtable_change
                          ▼
                   ┌─────────────────────┐
                   │ Make Scenario #3    │
                   │ Airtable → HubSpot  │
                   │                     │
                   │ Webhook → Match by  │
                   │   email → Update    │
                   │   HubSpot Contact   │
                   │   (Mentor, Onboard) │
                   └─────────────────────┘
```

---

## Make-Account-Setup

1. Account auf `make.com` (Free-Tier, 1.000 Ops/Monat — reicht).
2. Connections anlegen unter **Connections → Add**:
   - **HubSpot** → Private App Token (aus `hubspot/README.md` §3)
   - **Airtable** → Personal Access Token (Airtable → Builder Hub → Personal Access Tokens)
   - **Slack** → OAuth via Slack-Workspace
   - **HTTP** → für Meta CAPI, GA4 MP, TikTok Events API
3. Drei Webhooks vorab anlegen, URLs notieren in `.env`:
   ```env
   MAKE_WEBHOOK_QUIZ_SUBMIT=https://hook.eu2.make.com/abc...
   MAKE_WEBHOOK_HUBSPOT_STATUS=https://hook.eu2.make.com/def...
   MAKE_WEBHOOK_AIRTABLE_CHANGE=https://hook.eu2.make.com/ghi...
   ```

---

## Conflict-Resolution-Strategie

Eines der häufigsten Bugs bei Bi-Sync ist die **Ping-Pong-Schleife**:
Make schreibt nach HubSpot → HubSpot-Workflow triggert Make → Make
schreibt nach Airtable → Airtable-Automation triggert Make → Make
schreibt wieder nach HubSpot → …

**Drei Maßnahmen verhindern das:**

| Maßnahme | Implementierung |
|---|---|
| **Source-Tagging im Payload** | Jeder Sync-Event trägt ein `_source`-Feld: `quiz`, `hubspot-workflow`, `airtable-automation`. Make-Szenarien prüfen `_source` und brechen ab, wenn die Aktualisierung von sich selbst kommt. |
| **Field-Ownership-Matrix** | Jedes Feld hat genau **eine** Source-of-Truth (siehe `field-mapping.md`). Andere Systeme dürfen es nur _lesen_, nicht schreiben. |
| **Last-Updated-Compare** | Vor jedem Update: HubSpot `hs_lastmodifieddate` vs. Airtable `last_modified` vergleichen. Älterer Wert verliert. |

---

## Op-Counts (Free-Tier-Budget)

Pro Quiz-Submit:

| Szenario-Schritt | Ops |
|---|---|
| Webhook receive | 1 |
| Validate / Filter | 0 (Filter kosten 0 Ops) |
| HubSpot upsert | 1 |
| Airtable upsert | 1 |
| Slack post (nur Hot Leads, ~30%) | 0,3 |
| Meta CAPI HTTP | 1 |
| GA4 MP HTTP | 1 |
| TikTok HTTP | 1 |
| **Summe pro Submit** | **~6,3 Ops** |

**Budget:** 1.000 Ops / Monat ÷ 6,3 ≈ **158 Submits / Monat**.

Reicht für die Demo-Volumina (deutlich weniger Traffic erwartet).
Bei Skalierung: Make Core (~ 9 €/Monat = 10.000 Ops) oder Workato-Migration.

---

## Test-Strategie

Jedes Szenario hat einen **Test-Mode**, in dem das Payload-Feld
`meta.testMode = true` ist. In diesem Fall:

- Slack-Post geht in einen separaten `#test-leads`-Channel
- HubSpot-Contact bekommt zusätzliches Tag `test_lead = true`
- Airtable-Insert geht in eine separate View „Test Leads"
- Pixel-Calls werden mit `test_event_code` versendet

Aktivierbar im Frontend via `window.MF_CONFIG.testMode = true`.

---

## Reihenfolge der Implementierung

1. **Szenario #1 zuerst** — Quiz-Submit muss fließen, sonst keine Daten
2. **Szenario #2 zweitens** — Sobald HubSpot-Workflow live ist
3. **Szenario #3 zuletzt** — Reverse-Sync ist Polish, nicht Core
