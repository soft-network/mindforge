# Phase E — Realitäts-Bridge zu Love Life Passport

**Status:** Plan · noch nicht implementiert
**Aufwand:** ~10 h (E1 + Quer-Welle)
**Voraussetzung:** Phasen 1, A, B, C, D des Demo-Projekts laufen oder sind dokumentiert
**Ziel:** Das Demo-Projekt um genau die zwei Bausteine erweitern, die durch
die Live-Analyse des Quiz `analyse.lovelifepassport.com` als reale LLP-Praxis
verifiziert wurden — **HubSpot als zweites CRM neben Airtable** und ein
**mehrstufiges Quiz mit komplettem Pixel-Stack** (Meta + GA4 + TikTok + GTM).

---

## 1. Executive Summary

| Punkt | Befund |
|---|---|
| Warum Phase E? | Live-Analyse hat gezeigt: LLP nutzt **HubSpot (EU, Account 26317639) als primäres CRM** und Tracking-Layer + ein mehrstufiges Quiz mit 13 Schritten und 4 parallelen Pixeln. Die Stellenanzeige listet HubSpot *nicht* explizit — dieses Wissen aus der Recherche zu zeigen ist der Bewerbungs-Hebel. |
| Architektur-Entscheidung | **Parallel, nicht Ersatz.** HubSpot übernimmt die Marketing-/Sales-Pipeline; Airtable bleibt die Operations-DB (Programme, Sessions, Mentoren, internes Reporting). Make ist der Bridge-Layer. Power BI konsolidiert beide. |
| Markenneutralität | Demo bleibt unter dem fiktiven Namen **MindForge**. Alle IDs, Konten und Daten sind synthetisch. Nichts wird unter LLPs Namen abgesendet. |
| Free-Tier-Strategie | HubSpot Free CRM, Make Free (1.000 Ops/Monat), Power BI Desktop, GCP Free Tier — kein Geldeinsatz nötig. Limits dokumentiert in §7. |
| Was bleibt unverändert | Die Phasen 1–D bleiben technisch und inhaltlich gleich; Phase E erweitert sie additiv. Keine bestehende Datei wird umgeschrieben — nur ergänzt. |

---

## 2. Ziel-Architektur (nach Phase E)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                PUBLIC                                    │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌──────────────────────────────────────┐                               │
│   │  Quiz-Frontend (9 Schritte)          │   ┌─────────────────────┐     │
│   │  HTML + Vanilla JS + Skip-Logic      │   │  GTM Container      │     │
│   │  Mobile-first, mit Score-Berechnung  │──▶│  GTM-XXXXXX (DEMO)  │     │
│   │  Hosted auf GitHub Pages             │   │   ├─ Meta Pixel     │     │
│   └─────────────────┬────────────────────┘   │   ├─ GA4 Stream A   │     │
│                     │                        │   ├─ GA4 Stream B   │     │
│                     │ POST (JSON)            │   └─ TikTok Pixel   │     │
│                     ▼                        └─────────────────────┘     │
│   ┌──────────────────────────────────────────────────────────────────┐   │
│   │                  Make Scenario "Quiz Submit"                     │   │
│   │  1. Validate fields                                              │   │
│   │  2. Compute Lead Score (existing JS, Phase 1)                    │   │
│   │  3. ─▶ Branch A: Airtable upsert (Leads-Table, Operations-View) │   │
│   │  4. ─▶ Branch B: HubSpot upsert (Contact + Custom Properties)   │   │
│   │  5. ─▶ Branch C: Pixels server-side                             │   │
│   │        ├─ Meta CAPI (Test Event Code)                            │   │
│   │        ├─ GA4 Measurement Protocol                               │   │
│   │        └─ TikTok Events API                                      │   │
│   │  6. ─▶ Branch D: Slack hot-lead ping                            │   │
│   └────────────┬─────────────────────────────────────────────────────┘   │
│                │                                                         │
└────────────────┼─────────────────────────────────────────────────────────┘
                 │
┌────────────────┼─────────────────────────────────────────────────────────┐
│             INTERNAL                                                     │
├────────────────┼─────────────────────────────────────────────────────────┤
│                ▼                                                         │
│   ┌────────────────────┐      ┌────────────────────┐                     │
│   │   HubSpot Free CRM │◀────▶│   Airtable Base    │                     │
│   │   Account: demo    │      │   4 Tables (Phase 1)│                    │
│   │   Marketing+Sales  │ Make │   + Mentor-Tabelle  │                    │
│   │   Pipeline + Quiz- │  bi- │   (neu)             │                    │
│   │   Properties       │ direc│                     │                    │
│   └─────────┬──────────┘      └─────────┬───────────┘                    │
│             │                           │                                │
│             ▼ OData/REST                ▼ REST                           │
│   ┌──────────────────────────────────────────────────────┐               │
│   │              Power BI Cross-Source                   │               │
│   │  - Marketing-Funnel (HubSpot)                        │               │
│   │  - Sales-Pipeline (HubSpot Deals)                    │               │
│   │  - Mentoring-Operations (Airtable)                   │               │
│   │  - Joined: Lead → Customer → Mentor-Sessions         │               │
│   └──────────────────────────────────────────────────────┘               │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Welle E1 — Realität spiegeln

### 3.1 Realistisches Quiz-Frontend

**Was:** Ersetzt das simple Lead-Capture-Formular aus Phase A durch ein
mehrstufiges Quiz mit 9 Fragen (LLPs Realstruktur), Score-Berechnung im
Client und konditionellen Sprüngen.

**Wo:** Neuer Ordner `quiz-frontend/` parallel zu `landing-page/`. Phase A
bleibt unangetastet als „Baseline-Demo".

**Spec:**

| Frage | Typ | Score-Beitrag |
|---|---|---|
| 1. Hast du bereits ein Unternehmen? | Single | Ja=10, Nein=0 |
| 2. Wie lange selbstständig? | Single (cond.) | < 1J = 2, 1–3J = 6, > 3J = 10 |
| 3. In welchem Bereich? | Single | Coach=10, Dienstl=8, Digital=8, E-Comm=6, Network=4, Sonst=2 |
| 4. Wie sichtbar? | Single | < 1K = 2, < 10K = 6, > 10K = 10 |
| 5. Team-Aufstellung? | Single | Solo=4, +<10 = 8, +>10 = 10 |
| 6. Monatsumsatz? | Single | 0=0, <5K=2, <10K=6, <100K=10, >100K=10 |
| 7. Wunsch frei? | Single | weighting: Freiheit=8, 5-stellig=10, Marke=6, kündigen=4, Stabilität=2 |
| 8. Was fehlt dir? | **Multi** | je Auswahl +2 |
| 9. Zeitbudget pro Woche | Single | <1h=0, 2-5h=4, 5-10h=8, >10h=10 |
| Kontaktdaten | Form | Vorname, Nachname, E-Mail, Telefon, Land |

**Skip-Logic:** Wenn Frage 1 = "Nein", überspringt Frage 2 und ersetzt
Frage 3-6 mit "Hast du eine Geschäftsidee?" + "Welcher Bereich interessiert
dich?". Damit replizieren wir LLPs "of 12 / of 13"-Verhalten.

**Tech:**
- Vanilla JS (kein React-Build-Setup nötig — bleibt portabel)
- State-Object `quiz = { step, answers, score }` in `sessionStorage`
- 9 versteckte `<section>`-Blöcke, sichtbar via `.active`-Class
- Score-Berechnung beim Verlassen jeder Frage
- Submit-Button erst bei vollständigen Kontaktdaten aktiv

**Files:**
```
quiz-frontend/
├── index.html        # Markup mit allen 9 Sections + Kontakt-Section
├── styles.css        # Responsive, dark-theme (wie LLP-Original)
├── quiz-engine.js    # State, Navigation, Skip-Logic
├── score-engine.js   # Berechnungslogik
├── submit-engine.js  # Submit zu Make Webhook + Pixel-Calls
└── tracking/
    ├── gtm-bootstrap.js   # GTM Container Loader
    └── consent.js         # Cookie-Consent (DSGVO-konform, minimal)
```

**Zeit:** ~3 h

---

### 3.2 HubSpot Free CRM Setup

**Was:** HubSpot Free CRM einrichten als zweites CRM neben Airtable, mit
Custom-Properties für die Quiz-Antworten — analog zu LLPs Setup.

**Schritt-für-Schritt:**

1. HubSpot Free Account anlegen unter `app.hubspot.com/signup` (kostenlos,
   keine Kreditkarte nötig). Region: **EU (Frankfurt)** — entspricht LLP.
2. Im Demo-Account 12 Custom-Properties auf dem Contact-Objekt anlegen:

| Property Name | Type | Group |
|---|---|---|
| `quiz_business_status` | Single-line | Quiz Lead Data |
| `quiz_years_self_employed` | Single-line | Quiz Lead Data |
| `quiz_business_field` | Single-line | Quiz Lead Data |
| `quiz_visibility` | Single-line | Quiz Lead Data |
| `quiz_team_setup` | Single-line | Quiz Lead Data |
| `quiz_monthly_revenue` | Single-line | Quiz Lead Data |
| `quiz_main_wish` | Single-line | Quiz Lead Data |
| `quiz_gap` | Multi-line | Quiz Lead Data |
| `quiz_time_budget` | Single-line | Quiz Lead Data |
| `quiz_score` | Number | Quiz Lead Data |
| `quiz_completed_at` | Datetime | Quiz Lead Data |
| `lead_source_subdomain` | Single-line | Quiz Lead Data |

3. Private App in HubSpot anlegen → API-Token generieren mit Scopes
   `crm.objects.contacts.read/write` und `crm.objects.deals.read/write`.
4. Token in Make hinterlegen (Connection-Setup).
5. Sample-Workflow in HubSpot anlegen:
   *„Quiz-Lead eingegangen → Hot wenn quiz_score ≥ 50 → E-Mail an Setter"*
   (manuell konfiguriert, dokumentiert mit Screenshots).

**Files:**
```
hubspot/
├── README.md                    # Setup-Anleitung mit Screenshots
├── properties-export.json       # Custom-Properties als Import-fähiges JSON
└── workflow-design.md           # Workflow-Schritte für manuelle Replikation
```

**Zeit:** ~1,5 h

---

### 3.3 Make-Bridge HubSpot ↔ Airtable

**Was:** Bidirektionale Sync-Bridge zwischen den beiden Systemen, mit
HubSpot als Source-of-Truth für Marketing/Sales-Daten und Airtable als
Source-of-Truth für Operations.

**Drei Make-Szenarien:**

| # | Trigger | Aktion | Zweck |
|---|---|---|---|
| 1 | Quiz Webhook | Insert HubSpot Contact + Insert Airtable Lead | **Initial-Sync beim Submit** |
| 2 | HubSpot Workflow → Make Webhook | Update Airtable-Lead (Status, Owner, Stage) | **Sales-Pipeline → Operations** |
| 3 | Airtable Automation → Make Webhook | Update HubSpot-Contact (z.B. Mentor-Zuordnung, Onboarding-Status) | **Operations → Marketing** (für Re-Targeting / Lookalike-Audiences) |

**Conflict-Handling:**
- Single Source of Truth pro Feld dokumentiert (z.B. „Lead-Score wird in
  Make berechnet und in beide geschrieben; bei Konflikt gewinnt HubSpot")
- Updated-Timestamp pro Side mitgeführt
- Dedup-Key: E-Mail (normalisiert lowercase, getrimmt)

**Files:**
```
make-bridge/
├── README.md                       # Architektur + Conflict-Resolution
├── 01-quiz-submit-scenario.md      # Visueller Scenario-Aufbau (Schritte)
├── 02-hubspot-to-airtable.md       # Webhook-Trigger + Mapping
├── 03-airtable-to-hubspot.md       # Reverse-Direction
├── field-mapping.md                # Tabelle: HubSpot ↔ Airtable Feld-Mapping
└── sample-payloads/
    ├── quiz-submit.json
    ├── hubspot-deal-update.json
    └── airtable-mentor-assign.json
```

**Zeit:** ~2,5 h (Make-Szenarien sind GUI-basiert; größtenteils
Dokumentation + Mapping)

---

### 3.4 Cross-Source Power BI

**Was:** Power BI Desktop Workspace mit zwei Datenquellen (HubSpot via
REST-API, Airtable via REST-API), gejoined zu einem Customer-Lifecycle-Dashboard.

**Datenmodell (Star-Schema):**

```
                ┌───────────────────┐
                │  fact_quiz_leads  │ ← aus HubSpot Contacts
                │  - contact_id     │
                │  - quiz_score     │
                │  - quiz_completed │
                │  - source_utm     │
                └─────────┬─────────┘
                          │
        ┌─────────────────┼───────────────────┐
        ▼                 ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│dim_program   │  │dim_mentor    │  │fact_sessions     │
│(Airtable)    │  │(Airtable)    │  │(Airtable)        │
│- program_id  │  │- mentor_id   │  │- session_id      │
│- name        │  │- name        │  │- contact_id (FK) │
│- price       │  │- specialty   │  │- mentor_id (FK)  │
└──────────────┘  └──────────────┘  │- date            │
                                    │- nps             │
                                    └──────────────────┘
```

**Berichte:**
1. **Marketing-Funnel** — Quiz-Submits → Hot-Leads → Sales-Calls → Conversions (HubSpot only)
2. **Mentor-Auslastung** — Sessions pro Mentor/Woche (Airtable only)
3. **Customer-Health-Score** — gejoined: HubSpot Lifecycle Stage × Airtable Last-Session-Date × NPS
4. **Quiz-Pfad-Analyse** — welche Quiz-Antwort-Kombinationen zu höchster Conversion führen (HubSpot only, mit DAX-Slicer)

**DAX-Maße (Beispiele):**
```dax
Hot Lead Rate =
DIVIDE(
    CALCULATE(COUNTROWS(fact_quiz_leads), fact_quiz_leads[quiz_score] >= 50),
    COUNTROWS(fact_quiz_leads)
)

Avg Sessions per Customer =
AVERAGEX(
    VALUES(fact_quiz_leads[contact_id]),
    CALCULATE(COUNTROWS(fact_sessions))
)

Mentor Utilization =
DIVIDE(
    [Avg Sessions per Customer],
    [Capacity per Mentor per Week]
)
```

**Files:**
```
powerbi-cross-source/
├── README.md                  # Setup + Connection-Strings (anonymisiert)
├── data-model.md              # Schema + Beziehungen
├── dax-measures.md            # Alle DAX-Maße mit Erklärung
├── reports/
│   ├── marketing-funnel.png   # Export-Screenshot
│   ├── mentor-utilization.png
│   └── customer-health.png
└── pbix-source.txt            # Hinweis wo die .pbix-Datei liegt (zu groß für Git)
```

**Zeit:** ~1,5 h

---

## 4. Quer-Welle — Tracking-Realität

**Was:** Der bestehende Phase-A/B-Tracking-Stack (Meta Pixel + CAPI) wird
ersetzt durch das **vollständige LLP-Setup**: GTM-Container als Wrapper,
darin 4 parallele Pixel.

**Komponenten:**

| Pixel | Demo-ID-Strategie | Test-Methode |
|---|---|---|
| Meta Pixel | Echte Test-Pixel-ID aus Meta Business Manager (Free) | Meta Events Manager → Test Events |
| GA4 Stream A | Neuer Stream im GA4-Account (Free) | GA4 DebugView |
| GA4 Stream B | Zweiter Stream, identisch konfiguriert (für Cross-Subdomain-Bridge-Demo) | DebugView |
| TikTok Pixel | TikTok Business Account (Free), Test Pixel | TikTok Events Manager → Test |
| HubSpot | bereits über §3.2 abgedeckt | HubSpot Tracking-Code |

**GTM-Container-Design:**

```
GTM-XXXXXX
├── Tags:
│   ├── Meta Pixel — Base                (Trigger: All Pages)
│   ├── Meta Pixel — Quiz Start          (Trigger: CE quiz_start)
│   ├── Meta Pixel — Quiz Submit (Lead)  (Trigger: CE quiz_submit)
│   ├── GA4 — Stream A Config            (Trigger: All Pages)
│   ├── GA4 — Stream B Config            (Trigger: All Pages)
│   ├── GA4 — Quiz Start Event           (Trigger: CE quiz_start)
│   ├── GA4 — Quiz Submit Event          (Trigger: CE quiz_submit)
│   ├── TikTok Pixel — Base              (Trigger: All Pages)
│   └── TikTok Pixel — Lead              (Trigger: CE quiz_submit)
├── Triggers:
│   ├── All Pages (built-in)
│   ├── CE quiz_start                    (Custom Event)
│   └── CE quiz_submit                   (Custom Event)
└── Variables:
    ├── DLV - quiz_score
    ├── DLV - quiz_business_field
    └── DLV - lead_email_hashed
```

**Server-Side-CAPI:**
- Meta CAPI im Make-Webhook (bereits Phase B)
- GA4 Measurement Protocol im selben Webhook
- TikTok Events API im selben Webhook
- Alle drei mit identischer `event_id` für Deduplizierung

**Files:**
```
tracking-full/
├── README.md                       # Stack-Übersicht
├── 01-gtm-container.md             # Container-Setup mit Screenshots
├── 02-meta-pixel-capi.md           # Pixel + CAPI (erweitert Phase B)
├── 03-ga4-dual-stream.md           # 2 Streams konfigurieren
├── 04-tiktok-pixel.md              # Setup + Test
├── 05-consent-and-dsgvo.md         # Cookie-Consent-Logic + DSGVO-Notes
└── dataLayer-spec.md               # Welche Events mit welchen Properties
```

**Zeit:** ~3 h

---

## 5. Abhängigkeits-Graph

```
              [E1.2 HubSpot Setup]      [Quer GTM Container]
                      │                          │
                      ▼                          │
              [E1.3 Make Bridge]                 │
                      │                          │
   ┌──────────────────┴───────┐                  │
   │                          │                  │
   ▼                          ▼                  ▼
[E1.1 Quiz-Frontend] ◀── (DataLayer-Events) ──── ┘
   │
   ▼
[E1.4 Power BI Cross-Source]
```

**Reihenfolge der Implementierung:**

1. **HubSpot-Account anlegen + Properties anlegen** (kein Code, ~30 min) — blockiert E1.3 + E1.4
2. **GTM-Account anlegen + leeren Container** (kein Code, ~15 min) — blockiert Tracking-Tests
3. **Quiz-Frontend bauen** (~3 h, Vanilla JS) — parallelisierbar
4. **Make-Bridge konfigurieren** (~2,5 h) — braucht 1 + 3
5. **GTM-Container mit allen Tags konfigurieren** (~1,5 h) — braucht 2 + 3
6. **Server-Side-Pixel im Make-Webhook** (~1,5 h) — braucht 4 + 5
7. **Power-BI-Workspace** (~1,5 h) — braucht 1 + 4 (Datenfluss muss live sein)

**Kritischer Pfad:** Schritte 1 → 4 → 7 (∑ ~4,5 h). Alles andere parallelisierbar.

---

## 6. Account-Setup-Checkliste

| Konto | Free-Tier-Limit | Was wir brauchen | Link |
|---|---|---|---|
| HubSpot Free CRM | 1 Mio Contacts, 5 User | Custom Properties, 1 Workflow, 1 Form | app.hubspot.com/signup |
| Meta Business Manager | Free | 1 Pixel, Events Manager, Test Event Code | business.facebook.com |
| Google Analytics 4 | Free | 2 Properties (1 Account, 2 Streams) | analytics.google.com |
| Google Tag Manager | Free | 1 Container | tagmanager.google.com |
| TikTok for Business | Free | 1 Pixel, Test Events | ads.tiktok.com |
| Make | 1.000 Ops/Monat | 3 Szenarien | make.com (existiert bereits) |
| Airtable | Free | Existiert bereits aus Phase 1 | airtable.com |
| Power BI Desktop | Free | Existiert bereits aus Phase 1 | powerbi.microsoft.com |
| GitHub Pages | Free | Existiert bereits | github.com |

**Reihenfolge der Setup-Schritte (~1 h gesamt vor dem ersten Code):**

1. HubSpot Free CRM Account anlegen → Properties über UI oder Import
2. Meta Business Manager → Test-Pixel anlegen → Test Event Code notieren
3. GA4 → 1 Property, 2 Streams (Web) → Measurement-IDs notieren
4. GTM → leerer Container → Container-ID notieren
5. TikTok Business → Pixel anlegen → Pixel-ID + Access-Token notieren
6. Alle IDs in `phase-e-secrets.example.env` notieren (Template, kein
   Commit von echten Werten)

---

## 7. Risiken und Mitigations

| Risiko | Wahrscheinlichkeit | Mitigation |
|---|---|---|
| HubSpot-API-Rate-Limits (100 calls / 10s im Free-Tier) | Niedrig | Bei Demo-Volumen unkritisch; bei Bedarf Batch-Endpoint nutzen |
| Make Free-Tier Ops-Limit (1.000/Monat) | Mittel | Pro Quiz-Submit ~5 Ops → 200 Submits/Monat möglich. Reicht für Demo. |
| GTM-Account-Verification ohne Domain | Niedrig | GitHub-Pages-Domain reicht für Demo-Zwecke |
| Meta Business Manager Setup-Reibung (KYC) | Mittel | Test-Pixel funktioniert ohne KYC; KYC nur für Ad-Spend nötig |
| HubSpot ↔ Airtable Sync-Loops (infinite ping-pong) | Mittel | Pro Szenario nur in *eine* Richtung syncen + Owner-Flag im Payload |
| Quiz-Frontend funktioniert nicht ohne Build-Step | Niedrig | Bewusst Vanilla JS, keine Bundler-Abhängigkeit |
| GA4 Cross-Stream-Sync verwirrt Konfiguration | Mittel | Klar dokumentieren: Stream A = "alle Subdomains", Stream B = "nur Quiz" |
| Datenschutz: Demo speichert PII? | Niedrig | Demo-Submits nur mit klar synthetischen Daten (`demo+test@example.com`) |

---

## 8. Was bewusst nicht in Phase E ist

| Skipped | Grund |
|---|---|
| Wellen E2 (Sales-Pipeline mit Leadhunter/Setter/Closer) | Wurde nicht gewählt |
| Welle E3 (Mentor-Performance, RLS, Customer-Health) | Wurde nicht gewählt |
| Aircall-Integration | Braucht kostenpflichtigen Aircall-Trial |
| Calendly-Webhook | Calendly Free-Tier hat keine Webhooks; Substitution mit Make-Cal-Connector möglich, aber nicht im Scope |
| Salesforce / Pipedrive | HubSpot reicht zur Demonstration des Patterns |
| Replizierung des originalen LLP-Funnel-Builders (`con-kit`) | Proprietäres Tool, keine Public-API. Vanilla-JS ist portabler. |
| Echte LinkedIn-Pixel | Meta + GA4 + TikTok zeigen das Pattern bereits |
| Identity-Resolution (Server-Side User-ID) | Über Hashed-E-Mail in CAPI bereits abgedeckt |

---

## 9. Erfolgs-Kriterien

Phase E ist „done" wenn:

- [ ] Quiz-Submit auf der Demo-URL fliegt durch und legt einen Datensatz in HubSpot **und** in Airtable an, mit identischer E-Mail und Score-Property
- [ ] HubSpot-Workflow feuert auf `quiz_score ≥ 50` (sichtbar in HubSpot-Workflow-History)
- [ ] Im Meta Events Manager erscheint der „Lead"-Event sowohl client- als auch server-side mit derselben `event_id` (dedupliziert in den Diagnostics)
- [ ] GA4 DebugView zeigt `quiz_submit`-Events auf beiden Streams parallel
- [ ] TikTok Events Manager zeigt mindestens einen „Lead"-Test-Event
- [ ] Power BI Desktop lädt beide Datenquellen, das Cross-Source-Dashboard zeigt mindestens 5 Test-Leads mit gejointen Mentor-Sessions
- [ ] `LOVELIFEPASSPORT-ANALYSE.md` ist um einen Abschnitt „Phase-E-Status" ergänzt mit Verweisen auf alle neuen Files
- [ ] Bewerbungs-Pitch (Abschnitt 8 der Master-Analyse) ist um die HubSpot-Bridge-Story erweitert

---

## 10. Zeitplan (~10 h gesamt)

| Block | Dauer | Voraussetzung | Output |
|---|---|---|---|
| Account-Setup-Sprint | 1 h | – | Alle IDs in `.env.example` |
| Quiz-Frontend HTML + Skip-Logic | 1,5 h | – | `quiz-frontend/index.html` + Engine |
| Quiz-Frontend Submit + DataLayer | 1 h | Frontend-Markup | DataLayer-Events feuern |
| HubSpot Properties + Workflow | 1 h | Account | Properties live, Workflow als Markdown |
| Make-Szenario E1.3a (Quiz → HubSpot+Airtable) | 1,5 h | HubSpot + Frontend | Make läuft, Test-Submit fließt |
| Make-Szenarien E1.3b/c (Bidi-Sync) | 1 h | E1.3a | Sync in beide Richtungen |
| GTM-Container + alle Tags | 1,5 h | GTM-Account | Pixel feuern auf Quiz-Events |
| Power-BI Cross-Source | 1,5 h | HubSpot + Airtable mit Daten | `.pbix` mit 4 Reports |

**Realistisch über ein langes Wochenende oder zwei Abende + ein Wochenende.**

---

## 11. Getroffene Entscheidungen vor Implementierungsstart

| Frage | Entscheidung |
|---|---|
| HubSpot-Account-Mail | `net24.twork@gmail.com` (Hauptmail) |
| GTM-Container-Name | "MindForge Demo" |
| GitHub-Repo | sofort public ab Phase E |
| Loom-Video | offen, Klick-Pfade werden beim Bauen dokumentiert, damit beides möglich bleibt |
| Pitch-Update / Anschreiben | macht User selbst, Claude liefert nur Code + Setup-Doku |

---

## 12. Nach Phase E

Mit E1 + Quer-Welle erreicht das Demo eine Tiefe, die folgendes belegt:

- **Geschäftsverständnis:** Quiz-Pfad, Lead-Score, Sales-Pipeline 1:1 nachgebaut
- **Tool-Beherrschung:** Airtable + HubSpot + Make + Power BI im Verbund (statt nur Airtable wie in der Stellenanzeige)
- **Tracking-Reife:** GTM + 4 Pixel + CAPI + Privacy-Sandbox-Awareness
- **Operations-Reife:** Bidirektionaler Sync mit Conflict-Resolution

Optional in einer späteren Welle: E2 (Sales-Pipeline) und E3 (Mentoring),
wenn Zeit bis zur Bewerbung bleibt.

---

**Review-Erwartung:** Bitte Plan durchgehen, offene Fragen aus §11
beantworten oder per AskUserQuestion-Folgerunde abklären. Danach starte
ich mit dem Account-Setup-Sprint und dem Quiz-Frontend.
