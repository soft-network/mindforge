# Architecture & Implementation Phases

The MindForge demo is built in four phases, each one independently usable
and adding a clean layer of functionality.

**Design principle:** every tool has a clear job. No "let's also throw this in
because it looks fancy" decisions.

---

## Architecture v2

```
┌────────────────────────────────────────────────────────────────┐
│                          PUBLIC                                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  [HTML Landing Page]               [Statuspage]                │
│  GitHub Pages                       status.mindforge.demo      │
│  + Meta Pixel                                                  │
│  + Google Tag Manager                                          │
│        │                                                       │
│        │ POST                                                  │
│        ▼                                                       │
│  ┌─────────────────────────────────────────┐                   │
│  │       Make Webhook Pipeline              │                  │
│  │  ├─ Validate                             │                  │
│  │  ├─ Duplicate Check                      │                  │
│  │  ├─ E-Mail Enrichment (GCP Function)      │                  │
│  │  ├─ Create in Airtable                   │                  │
│  │  ├─ Compute Lead Score                   │                  │
│  │  ├─ Send Meta CAPI Event                 │                  │
│  │  └─ Slack Notify (Hot Leads)             │                  │
│  └────────────────────┬────────────────────┘                   │
│                       │                                        │
└───────────────────────┼────────────────────────────────────────┘
                        │
┌───────────────────────┼────────────────────────────────────────┐
│                     INTERNAL                                   │
├───────────────────────┼────────────────────────────────────────┤
│                       ▼                                        │
│  ┌────────────────────────┐    ┌─────────────────────────────┐ │
│  │     Airtable CRM       │    │  Streamlit Coach Admin      │ │
│  │  4 Tables + JS Script  │◄───┤  (on GCP Cloud Run)         │ │
│  └─────────┬──────────────┘    └─────────────────────────────┘ │
│            │                                                   │
│            ▼ CSV/API                                           │
│  ┌────────────────────────┐    ┌─────────────────────────────┐ │
│  │   Power BI Dashboard   │    │   GCP Cloud Function        │ │
│  │  Funnel · Sources      │    │   E-Mail-Domain-Enrichment   │ │
│  │  Program Revenue       │    │   (serverless helper)       │ │
│  └────────────────────────┘    └─────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────┼────────────────────────────────────────┐
│                    MONITORING                                  │
├───────────────────────┼────────────────────────────────────────┤
│                                                                │
│  [UptimeRobot] ─ping every 5min─► all services                 │
│       └─ on failure ─► Slack Alert + Statuspage Update         │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Component responsibilities

### 1. Streamlit Coach Admin Dashboard

**Role:** Internal tool for the coach team to manage leads.

- Password-gated login
- Filterable list of all leads (status, source, score)
- Lead detail view with notes editor
- Quick action: change status, override lead score
- KPI block: new leads today, hot leads this week, conversion rate
- Plotly charts as BI alternative for users without Power BI access

**Tech:** Python + Streamlit + `pyairtable` + Plotly. Hosted on Streamlit Cloud
(simple) or GCP Cloud Run (preferred for production).

### 2. GCP (Cloud Run + Cloud Functions)

**Why GCP over Azure for this demo:**

| Criterion | GCP | Azure |
|---|---|---|
| Free tier generosity | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Developer experience | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Streamlit deploy time | 15 min | 30+ min |
| EU/DACH presence | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

→ GCP for the demo; Azure remains a documented alternative for
DSGVO-sensitive production setups.

**Use cases:**

- **Cloud Run** hosts the Streamlit app. Container-based, auto-scales,
  HTTPS included, custom domains possible.
- **Cloud Function** performs a focused task: email-domain enrichment.
  Make calls it for every new lead; it returns whether the email is
  personal (gmail/yahoo/etc.) or business, plus a score adjustment.

### 3. Monitoring (UptimeRobot + Statuspage)

**Role:** Reliability layer. The system surfaces outages before users notice.

- **UptimeRobot** pings the Make webhook, landing page, and Streamlit app
  every 5 minutes. On failure, it fires Slack alerts and email.
- **Statuspage** is the public face: a clean status URL with a live
  component health view and incident history.

### 4. Meta Pixel + CAPI

**Role:** Marketing attribution that survives iOS 14.5+ tracking limits.

- **Meta Pixel (client-side)** fires `PageView` on load and `Lead` on submit,
  with a generated `event_id` for deduplication.
- **CAPI (server-side)** is fired from Make after Airtable creation, with
  SHA-256 hashed PII (email, phone) and the matching `event_id`. Meta
  deduplicates the two events server-side.
- **Google Tag Manager** wraps both, plus Google Ads / TikTok / LinkedIn
  pixels can be added centrally without changing the landing page code.

---

## Phases and sequencing

### Phase 1 — Core pipeline (~10h)

| Step | Doc |
|---|---|
| Airtable schema and sample data | [02-airtable-schema.md](02-airtable-schema.md) |
| Lead scoring JS script | [03-airtable-script.md](03-airtable-script.md) |
| Make webhook pipeline | [04-make-scenario.md](04-make-scenario.md) |
| Power BI dashboard | [05-powerbi-dashboard.md](05-powerbi-dashboard.md) |

### Phase A — Quick wins (~4h)

| Step | Doc |
|---|---|
| HTML landing page | [04a-landing-page-html.md](04a-landing-page-html.md) |
| UptimeRobot monitoring | [09-monitoring.md](09-monitoring.md) |
| Meta Pixel on landing page | [10-meta-capi-tracking.md](10-meta-capi-tracking.md) |

### Phase B — Mid effort (~5h)

| Step | Doc |
|---|---|
| Meta CAPI server-side in Make | [10-meta-capi-tracking.md](10-meta-capi-tracking.md) |
| Public Statuspage | [09-monitoring.md](09-monitoring.md) |
| Google Tag Manager container | [10-meta-capi-tracking.md](10-meta-capi-tracking.md) |

### Phase C — Streamlit admin (~5h)

| Step | Doc |
|---|---|
| Coach admin dashboard | [07-streamlit-admin.md](07-streamlit-admin.md) |

### Phase D — GCP deployment (~5h)

| Step | Doc |
|---|---|
| Streamlit on Cloud Run | [08-gcp-deployment.md](08-gcp-deployment.md) |
| E-Mail enrichment Cloud Function | [08-gcp-deployment.md](08-gcp-deployment.md) |

---

## Total effort

| Phase | Hours |
|---|---|
| Core pipeline | 10 |
| Phase A | 4 |
| Phase B | 5 |
| Phase C | 5 |
| Phase D | 5 |
| **Total** | **~29h** |

Realistic over 2-3 weekends.

---

## Choices deliberately not made

| Skipped | Reason |
|---|---|
| Azure alongside GCP | One cloud provider is enough to demonstrate the pattern |
| Retool alongside Streamlit | Overlapping use cases, Streamlit is more portable |
| Postgres/SQL database | Airtable as data store is sufficient at this scope |
| Custom mobile app | Out of scope for a pipeline demo |
| TikTok + LinkedIn pixels | Meta Pixel covers the pattern; others would be additive |

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| GCP account setup fails (credit card region) | Medium | Fall back to Streamlit Cloud, keep GCP as documented future state |
| Meta Business Manager setup friction | Medium | Run pixel-only without backend CAPI; document CAPI in Make |
| Streamlit app scope creep | Low | Strict feature freeze: login + list + 1 edit action |
| CAPI event matching fails | Medium | Use Test Event Code, validate in Events Manager |
