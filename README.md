# MindForge Coaching Pipeline

End-to-end demo of a marketing-to-CRM pipeline for an online coaching business.
Built as a reference implementation combining low-code automation with light
custom code, modern marketing-tech, and serverless cloud deployment.

> **Bewerbungs-Kontext:** Dieses Demo-Projekt ist gezielt als Portfolio-Stück
> für die Stelle *Low Code Frontend Webentwickler* bei **Love Life Passport**
> aufgesetzt. Die ausführliche Geschäfts-, Funnel- und Rollenanalyse,
> das Tech-Stack-Mapping zur Stellenanzeige und der Bewerbungs-Pitch
> liegen in [`LOVELIFEPASSPORT-ANALYSE.md`](LOVELIFEPASSPORT-ANALYSE.md).
>
> Die geplante **Phase E** (Quiz-Frontend + HubSpot-Bridge + voller Pixel-Stack —
> abgeleitet aus der Live-Analyse des LLP-Quiz) ist beschrieben in
> [`PHASE-E-PLAN.md`](PHASE-E-PLAN.md).

---

## Use case

MindForge is a fictional online coaching company offering programs in Career,
Life, Health, and Business. The platform needs to:

- Capture leads from marketing landing pages
- Validate and deduplicate incoming submissions
- Score and qualify leads automatically
- Notify the sales team in real time when hot leads arrive
- Attribute conversions back to ad platforms (Meta Pixel + Conversion API)
- Offer the coach team an internal dashboard for lead management
- Report on funnel performance and program ROI
- Monitor system health and surface outages publicly

This repository implements that pipeline end-to-end.

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                          PUBLIC                                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  [HTML Landing Page]               [Statuspage]                │
│  GitHub Pages                       Atlassian                  │
│  + Meta Pixel                       Public System-Status       │
│  + Google Tag Manager                                          │
│        │                                                       │
│        │ POST                                                  │
│        ▼                                                       │
│  ┌─────────────────────────────────────────┐                   │
│  │       Make Webhook Pipeline              │                  │
│  │  ├─ Validate                             │                  │
│  │  ├─ Duplicate Check                      │                  │
│  │  ├─ Enrich (GCP Cloud Function)          │                  │
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
│  │  (Master Data)         │API │  Login + Lead Management    │ │
│  └─────────┬──────────────┘    └─────────────────────────────┘ │
│            │                                                   │
│            ▼ CSV/API                                           │
│  ┌────────────────────────┐                                    │
│  │   Power BI Dashboard   │                                    │
│  │   Funnel · Sources     │                                    │
│  │   Program Revenue      │                                    │
│  └────────────────────────┘                                    │
│                                                                │
└────────────────────────────────────────────────────────────────┘
                        │
┌───────────────────────┼────────────────────────────────────────┐
│                    MONITORING                                  │
├───────────────────────┼────────────────────────────────────────┤
│                                                                │
│  [UptimeRobot] ─ping every 5min─► all 3 services               │
│       └─ on failure ─► Slack Alert + Statuspage Incident       │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Stack

| Layer | Tool |
|---|---|
| Landing page | HTML / CSS / JavaScript, GitHub Pages |
| Tag management | Google Tag Manager |
| Conversion tracking | Meta Pixel + Server-Side Conversion API |
| Workflow orchestration | Make |
| CRM database | Airtable |
| Lead scoring | JavaScript (Airtable Scripting API) |
| BI reporting | Power BI (Desktop) |
| Internal admin UI | Streamlit (Python) |
| App hosting | GCP Cloud Run |
| Serverless helper | GCP Cloud Functions (Python) |
| Monitoring | UptimeRobot |
| Public status | Atlassian Statuspage |
| Notifications | Slack |

---

## Repository layout

```
demo/
├── README.md                       This file
├── LOVELIFEPASSPORT-ANALYSE.md     Business + role analysis · stack mapping · pitch
├── PHASE-E-PLAN.md                 Realitäts-Bridge: Quiz + HubSpot + Tracking + Cross-Source PBI
├── 00-architecture.md              Detailed architecture & extension plan
├── 01-accounts-setup.md            Tools and accounts needed
├── 02-airtable-schema.md           Airtable base design
├── 03-airtable-script.md           Lead scoring JS script (optional / manual)
├── 04-make-scenario.md             Webhook pipeline blueprint
├── 04a-landing-page-html.md        Landing page deployment
├── 05-powerbi-dashboard.md         Power BI dashboards + DAX measures
├── 06-airtable-interfaces.md       Lead Triage + Pipeline Overview UI
├── 07-streamlit-admin.md           Streamlit coach admin app
├── 08-gcp-deployment.md            Cloud Run + Cloud Functions deployment
├── 09-monitoring.md                UptimeRobot + Statuspage setup
├── 10-meta-capi-tracking.md        Meta Pixel + CAPI integration
│
├── airtable-scripts/
│   └── lead-scoring.js             Legacy: manual re-scoring tool (optional)
│
├── landing-page/
│   ├── index.html                  Landing page markup with Pixel + GTM
│   ├── styles.css                  Stylesheet (mobile-first)
│   └── script.js                   UTM capture, validation, webhook submit
│
├── streamlit-app/
│   ├── app.py                      Coach admin dashboard
│   ├── requirements.txt
│   ├── Dockerfile                  Cloud Run container build
│   └── .streamlit/
│       ├── config.toml
│       └── secrets.toml.example
│
├── quiz-frontend/                  Phase E: Mehrstufiges Quiz (Replikat des LLP-Funnels)
├── hubspot/                        Phase E: HubSpot Free CRM Setup + Properties + Workflow
├── make-bridge/                    Phase E: HubSpot ↔ Airtable Sync-Szenarien
├── tracking-full/                  Phase E: GTM + Meta + GA4 dual + TikTok
├── powerbi-cross-source/           Phase E: Cross-Source Dashboard HubSpot + Airtable
│
├── gcp/
│   ├── cloud-function/             Email-domain enrichment
│   │   ├── main.py
│   │   └── requirements.txt
│   ├── cloud-function-score/       Lead scoring (Python, called by Make)
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── test_main.py            pytest unit tests
│   ├── deploy-streamlit.sh         Deploy Streamlit to Cloud Run
│   ├── deploy-function.sh          Deploy enrichment function
│   └── deploy-score-function.sh    Deploy score-lead function
│
├── sample-data/
│   ├── programs.csv
│   ├── leads.csv
│   ├── sessions.csv
│   └── clients.csv
│
└── docs/
    └── screenshots/                PBI exports + UI screenshots
```

---

## Getting started

### Prerequisites

Free-tier accounts for the services you want to use. See
[`01-accounts-setup.md`](01-accounts-setup.md) for the full list and signup links.

The minimum set to run the core pipeline:

- Airtable
- Make
- Power BI Desktop
- Slack workspace
- GitHub

Optional extensions add:

- UptimeRobot and Atlassian Statuspage for monitoring
- Meta Business Manager and Google Tag Manager for tracking
- GCP project for Cloud Run + Cloud Functions

### Setup order

Grouped by the phases from [`00-architecture.md`](00-architecture.md):

**Phase 1 — Core pipeline**
1. Create accounts ([`01-accounts-setup.md`](01-accounts-setup.md))
2. Build the Airtable schema ([`02-airtable-schema.md`](02-airtable-schema.md))
3. Deploy the `score-lead` Cloud Function ([`08-gcp-deployment.md`](08-gcp-deployment.md) — function part only; required before Make)
4. Build the Make scenario ([`04-make-scenario.md`](04-make-scenario.md))
5. Build the Power BI dashboard ([`05-powerbi-dashboard.md`](05-powerbi-dashboard.md))
6. *(Optional)* Install the manual JS scoring tool ([`03-airtable-script.md`](03-airtable-script.md))
7. *(Optional)* Build Airtable interfaces for the sales team ([`06-airtable-interfaces.md`](06-airtable-interfaces.md))

**Phase A — Quick wins**
8. Deploy the landing page ([`04a-landing-page-html.md`](04a-landing-page-html.md))
9. Add monitoring ([`09-monitoring.md`](09-monitoring.md))
10. Add Meta Pixel ([`10-meta-capi-tracking.md`](10-meta-capi-tracking.md))

**Phase B — Mid effort**
11. Add server-side CAPI + Statuspage + GTM ([`10-meta-capi-tracking.md`](10-meta-capi-tracking.md), [`09-monitoring.md`](09-monitoring.md))

**Phase C — Streamlit admin**
12. Run the Streamlit coach dashboard locally ([`07-streamlit-admin.md`](07-streamlit-admin.md))

**Phase D — Full GCP deployment**
13. Deploy Streamlit on Cloud Run + email enrichment function ([`08-gcp-deployment.md`](08-gcp-deployment.md))

### Run the Streamlit app locally

```bash
cd streamlit-app
python -m venv .venv
.venv\Scripts\activate           # Windows
pip install -r requirements.txt

# configure secrets
copy .streamlit\secrets.toml.example .streamlit\secrets.toml
# edit secrets.toml with your Airtable token + base id

streamlit run app.py
```

### Deploy the landing page

```bash
# locally test
cd landing-page
python -m http.server 8000

# deploy to GitHub Pages
# Settings → Pages → Source: main branch /landing-page
```

### Deploy to GCP

```bash
cd gcp
bash deploy-function.sh
bash deploy-streamlit.sh
```

---

## Sample data

`sample-data/` contains realistic test data for 5 programs, 20 leads,
13 sessions, and 4 converted clients. Import the CSVs into Airtable
to get a working dataset immediately.

---

## License

This is a portfolio reference implementation. Code is provided as-is for
educational purposes. The "MindForge" brand and copy are fictional.
