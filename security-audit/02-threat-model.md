# 02 · Threat Model — LLP Funnel-Architektur

STRIDE-Threat-Model auf die rekonstruierte Architektur von Love Life Passport.
Modell basiert auf:

- Live-Inspektion des Quiz-Funnels (2026-05-18, dokumentiert in `LOVELIFEPASSPORT-ANALYSE.md` §3)
- Stellenanzeigen (verifiziert über `lovelifepassport.factorialhr.de`)
- DNS-/Header-Analyse (siehe [`01-external-assessment.md`](01-external-assessment.md))

---

## 1. Data-Flow-Diagram (rekonstruiert)

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                       LLP-Funnel — End-to-End-Datenfluss                       │
└────────────────────────────────────────────────────────────────────────────────┘

  ┌──────────┐
  │  User    │ ─── Browser ───┐
  │ (Lead)   │                │
  └──────────┘                ▼
                      ┌────────────────────┐
                      │  analyse.llp.com    │ ◄── Funnel-Builder (onecdn.io)
                      │  Quiz-Frontend      │     React 18 + MobX
                      │  (no CSP, HSTS-)    │
                      └─────────┬──────────┘
                                │  XHR-POST (Quiz-Answers + Contact)
                                │  + client-side Pixel-Fires
                                ▼
        ┌───────────────────────┴───────────────────────┐
        │                                               │
        ▼                                               ▼
  ┌──────────────┐                            ┌────────────────────┐
  │ Tracking-Layer│                            │  Backend / Webhook │
  │ ────────────  │                            │  ───────────────── │
  │ Meta Pixel    │ ─► facebook.com/tr/        │  ggf. Make-Webhook │
  │ GTM           │                            │  + HubSpot Form-API│
  │ GA4 #1, #2    │ ─► google-analytics.com    │                    │
  │ TikTok Pixel  │ ─► analytics.tiktok.com    └─────────┬──────────┘
  │ HubSpot       │ ─► track-eu1.hubspot.com             │
  │  __ptc.gif    │    (mit Mauskoordinaten, CSS-Sel.)   │
  └──────────────┘                                       │
                                                         ▼
                                            ┌────────────────────┐
                                            │      HubSpot CRM   │
                                            │   (Account 26317639│
                                            │    Region: EU)     │
                                            │                    │
                                            │  - Contact         │
                                            │  - Lead-Score      │
                                            │  - 9× Quiz-Answers │
                                            │  - Lifecycle Stage │
                                            └─────────┬──────────┘
                                                      │
                          ┌───────────────────────────┼──────────────────────┐
                          ▼                           ▼                      ▼
                  ┌──────────────┐          ┌───────────────┐      ┌─────────────────┐
                  │ HubSpot      │          │ Aircall       │      │ Make-Bridge     │
                  │ Workflows    │          │ Setter-Queue  │      │ HubSpot↔Airtable│
                  │ - Mail an    │          │ (CTI Phone)   │      │ Field-Sync      │
                  │   Lead       │          └───────┬───────┘      └─────────┬───────┘
                  │ - Slack-Ping │                  │                        │
                  │   Setter     │                  ▼                        ▼
                  └──────────────┘          ┌───────────────┐      ┌─────────────────┐
                                            │ Setter bucht  │      │ Airtable        │
                                            │ Termin manuell│      │ Ops-Datenbank   │
                                            │ (Aircall+GCal)│      │ (Programme,      │
                                            └───────┬───────┘      │  Sessions,      │
                                                    │              │  Mentor-Map)    │
                                                    ▼              └─────────┬───────┘
                                            ┌───────────────┐                │
                                            │ Closer        │                │
                                            │ Strategie-    │                ▼
                                            │ gespraech     │      ┌─────────────────┐
                                            └───────┬───────┘      │   Power BI       │
                                                    │              │   Cross-Source   │
                                                    ▼              │   Reporting      │
                                            ┌───────────────┐      └──────────────────┘
                                            │ Inner Circle  │
                                            │ Mentor-Match  │
                                            └───────────────┘
```

**Daten-Sensitivität pro Element:**

| Element | Daten-Klassifikation | PII? |
|---|---|---|
| Quiz-Antworten | Business-PII (Branche, Umsatz, Zeitbudget) | ja (in Kombination identifizierbar) |
| Kontaktdaten | PII (Name, E-Mail, Telefon, Land) | ja |
| HubSpot CRM | PII + Profilbild + Mauskoordinaten via `__ptc.gif` | ja, granular |
| Aircall Calls | PII + ggf. Call-Recording (Audio) | ja, Art. 9 DSGVO-relevant je nach Inhalt |
| Airtable | PII + Programm-/Session-Daten | ja |
| Make-Webhooks | PII in Transit | ja |
| Power BI | PII + Umsatz-Aggregate | ja |

---

## 2. STRIDE-Analyse

### S — Spoofing

| # | Threat | Komponente | Wahrscheinlichkeit | Impact | Bemerkung |
|---|---|---|---|---|---|
| S1 | **E-Mail-Spoofing** als `noreply@lovelifepassport.com` / `alex.westhuis@…` möglich | DNS / SMTP | **HOCH** | hoch | DMARC `p=none` — siehe F1 |
| S2 | **CEO-Fraud** via gespoofte Mail an Setter/Closer ("Bitte überweise X an Konto Y") | E-Mail + Sales-Team | mittel | sehr hoch | direkte Konsequenz von S1 |
| S3 | **Phishing gegen Leads** mit gefälschter "Dein Quiz-Ergebnis vom CEO" Mail | E-Mail + Lead-Datenbank | mittel | hoch | Lead-Liste leakbar? Wenn ja → gezielter Spear-Phish |
| S4 | **Fake-Lead-Injection** via geleakte Make-Webhook-URL | Make.com / Webhook | mittel | mittel | Webhook-URL ist Secret — sollte rotierbar sein |
| S5 | **HubSpot-Form-Spam** auf öffentliche Embed-Form-IDs | HubSpot Forms | hoch | gering | jeder kann öffentliche Form-IDs missbrauchen |

### T — Tampering

| # | Threat | Komponente | Wahrscheinlichkeit | Impact | Bemerkung |
|---|---|---|---|---|---|
| T1 | **XSS-Injection** in Quiz-Antwortfeld (Name/Telefon) → reflected im Backend-E-Mail-Template | Frontend / HubSpot-Workflow | mittel | hoch | Kein CSP zur Mitigation (F2). HubSpot escaped normalerweise, aber Custom-Templates können broken sein |
| T2 | **MITM auf Subdomain-Hijack** ohne HSTS-`includeSubDomains` | TLS-Schicht | gering | hoch | F4 |
| T3 | **Manipulation der Quiz-Score-Logik** im Frontend (MobX-Store editieren) → Self-Inflated-Lead-Score | Frontend | hoch | gering | Score sollte serverseitig berechnet werden, falls nicht der Fall |
| T4 | **HTML-Injection in HubSpot-Form-Fields** → Stored XSS für Setter/Closer im CRM-UI | HubSpot | gering | mittel | HubSpot escaped, aber Custom-Properties-Views könnten unsichere Renderings haben |

### R — Repudiation

| # | Threat | Komponente | Wahrscheinlichkeit | Impact | Bemerkung |
|---|---|---|---|---|---|
| R1 | **Lead bestreitet Quiz-Submission** (z.B. wegen Aircall-Belästigung) ohne Server-Log | Backend | mittel | mittel | DSGVO Art. 7(1) — LLP muss Einwilligung nachweisen können |
| R2 | **Make-Run-History wird nach 30 Tagen gelöscht** (Standard-Plan) → keine Audit-Trail älter als 30d | Make.com | hoch | mittel | Compliance-Risiko |
| R3 | **HubSpot-Property-Edit ohne Audit-Log** in der Free/Starter-Plan-Variante | HubSpot | hoch | mittel | Sales-Hub Pro hat Audit-Log, Free nicht |

### I — Information Disclosure

| # | Threat | Komponente | Wahrscheinlichkeit | Impact | Bemerkung |
|---|---|---|---|---|---|
| I1 | **Webflow Backend-Details geleakt** via `x-lambda-id`, `x-wf-region`, `surrogate-key` | Webflow | gering | gering | F7 |
| I2 | **HubSpot Account-ID `26317639` öffentlich** im HTML und DNS-DKIM-Selektor | HubSpot | hoch | gering | Phishing-Vektor: Angreifer kann LLP-Branding in HubSpot-Form-Klonen nachbauen |
| I3 | **Lead-Daten in JS-State** während Quiz-Durchgang (MobX-Store) | Frontend | mittel | mittel | Bei XSS abgreifbar → sensitive Daten im Browser-Memory |
| I4 | **Cross-Customer-Cookie auf `Domain=clickfunnels.com`** | ClickFunnels | hoch | mittel | Cookie wird mit anderen CF-Kunden geteilt |
| I5 | **Schrems-II: Webflow hostet in `us-east-1`** | Webflow | hoch | mittel | LLP-Brand-Domain läuft über US-Server → Datenfluss USA |
| I6 | **HubSpot `__ptc.gif` Behavioral-Tracking** mit Maus-Koordinaten + CSS-Selectoren | HubSpot | hoch | mittel | Sehr granulares Tracking, möglicherweise nicht-konform mit Art. 5(1)(c) DSGVO (Datenminimierung) |
| I7 | **Tracking-Skripte lädt vor Consent-Decision** | Frontend / GTM | hoch | mittel | TTDSG § 25 — Pre-Consent-Loading von HubSpot-Scripts ist kontrovers |

### D — Denial of Service

| # | Threat | Komponente | Wahrscheinlichkeit | Impact | Bemerkung |
|---|---|---|---|---|---|
| D1 | **Form-Spam-Flood** auf Quiz-Submit → HubSpot Operations-Quota erschöpft | HubSpot | mittel | mittel | Rate-Limiting im Funnel-Builder vorhanden? Unklar |
| D2 | **Make-Operations-Quota erschöpft** durch Spam-Submits | Make.com | mittel | hoch | Plan-Limit greift, Webhook-Queue staut, echte Leads kommen nicht durch |
| D3 | **Aircall-Anrufflut** durch automatisierte Fake-Leads | Aircall + Setter-Team | mittel | hoch | Setter wird mit Bot-Leads zugemüllt |
| D4 | **GA4/Meta-Pixel-Rate-Limit** bei Bot-Traffic | Tracking | gering | gering | wirkt nur auf Reporting-Genauigkeit |

### E — Elevation of Privilege

| # | Threat | Komponente | Wahrscheinlichkeit | Impact | Bemerkung |
|---|---|---|---|---|---|
| E1 | **HubSpot-Mitarbeiter-Account-Übernahme** via Phishing (kein 2FA-Mandat sichtbar) | HubSpot User-Mgmt | mittel | sehr hoch | bei Übernahme: Vollzugriff auf alle 2000+ Leads |
| E2 | **Airtable-Token-Leak** in einem Make-Szenario-Export oder GitHub-Repo | Airtable + Make | gering | sehr hoch | Tokens haben Personal-Access-Scope |
| E3 | **Factorial-HR-Bewerber-Daten-Leak** via Account-Übernahme von Recruiter | Factorial | gering | hoch | PII der Bewerber + ggf. interne Personaldaten |
| E4 | **GCP-IAM-Misconfiguration** auf eigenem Backend (sofern LLP eigenes Backend betreibt) | GCP | gering | sehr hoch | nicht beobachtbar von außen |

---

## 3. Top-10-Risiken (priorisiert)

Priorisierung = Wahrscheinlichkeit × Impact × Detektierbarkeit:

1. **S1: E-Mail-Spoofing** (DMARC p=none) → konkret, von außen testbar, hoher Schaden
2. **S2: CEO-Fraud** via S1 → direkter Sales-Damage
3. **I7: Pre-Consent-Loading** → DSGVO-Bußgeld-Risiko, abmahnfähig
4. **D2/D3: Webhook-Flood** → Sales-Pipeline-Disruption
5. **I5: Schrems-II Webflow US-Hosting** → DSGVO-Risiko auf Brand-Domain
6. **E1: HubSpot-Account-Übernahme** → 2000+ Leads betroffen
7. **T1: XSS-Mitigation fehlt** → Defense-in-Depth-Lücke
8. **I6: HubSpot-Behavioral-Tracking** → Datenminimierungs-Verstoß
9. **S5: HubSpot-Form-Spam** → Operations-Kosten + Setter-Verärgerung
10. **R2: Make-Audit-Trail nur 30d** → Compliance-Lücke

---

## 4. Quick-Wins (Top 5 für die nächste Sprint)

| # | Maßnahme | Aufwand | Risiko-Reduktion |
|---|---|---|---|
| 1 | DMARC auf `p=quarantine; rua=mailto:dmarc@lovelifepassport.com;` setzen + DMARC-Reports einrichten (z.B. Postmark, dmarcian) | 1h | sehr hoch |
| 2 | DMARC schrittweise auf `p=reject` ramen (4 Wochen nach `quarantine`) | 0h (Reporting beobachten) | sehr hoch |
| 3 | `/.well-known/security.txt` anlegen (Webflow Custom Code) | 30 min | gering, aber Compliance |
| 4 | Funnel-Builder-CSP-Header erweitern: `script-src 'self' onecdn.io track-eu1.hubspot.com googletagmanager.com ...` | 2h (Test über alle Subdomains) | mittel |
| 5 | Google-DKIM-Key rotieren auf 2048-bit (Google Admin Console: 2 Klicks) | 15 min | mittel |

---

## 5. Was diese Analyse **nicht** abdeckt (Out-of-Scope)

Diese Analyse ist passiv und kann **nicht** beurteilen:

- Authentication-Strength im HubSpot-Mitarbeiter-Login (2FA-Pflicht?)
- Airtable-API-Token-Hygiene (sind PATs scoped?)
- Make-Webhook-URL-Rotation-Praxis
- GCP-IAM-Setup auf eigenen Cloud-Functions (sofern LLP welche betreibt)
- Penetration-Testing-Findings (würde aktive Permission brauchen)
- Source-Code-Review (Repos sind privat)
- Endpoint-Security der Mitarbeiter-Laptops (Remote-Workforce!)
- Incident-Response-Plan-Reife

Diese Themen würden ein **internes Security-Audit** mit `LoA` (Letter of
Authorization) erfordern. Ein realistischer Scope-of-Work-Vorschlag dazu
liegt in [`04-disclosure-mail.md`](04-disclosure-mail.md).
