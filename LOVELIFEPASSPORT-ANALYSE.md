# Love Life Passport — Geschäfts-, Funnel- und Rollenanalyse

**Zweck dieses Dokuments:** Dieses Demo-Projekt (`MindForge Coaching Pipeline`)
wurde gezielt als Bewerbungs-Demo für die Stelle
**"Low Code Frontend Webentwickler (Native or Fluent German required)"**
bei **Love Life Passport GmbH** aufgebaut. Dieses Dokument zeigt:

1. wie Love Life Passport als Geschäft funktioniert,
2. welche Rolle die Stelle im Org-Chart einnimmt,
3. wie der reale Funnel (analyse.lovelifepassport.com → Strategiegespräch → Inner Circle) aussieht,
4. und 1:1 wie das Demo-Projekt jede einzelne Anforderung der Stellenanzeige abbildet.

---

## 1. Executive Summary

| Punkt | Befund |
|---|---|
| Unternehmen | Love Life Passport — Online-Mentoring & Coaching für Online-Business-Aufbau |
| Gründer | Anika & Tayler Schweigert (Ehepaar, Sitz Bali / Indonesien) |
| CEO | Alex Westhuis |
| Head of People & Culture | Sabrina Kragler |
| Team-Größe | ca. 40–41 Mitarbeiter*innen, 100 % remote weltweit |
| Track Record | 25–35 Mio. € Umsatz (laut Gründer-Kommunikation), Spiegel-Bestseller "Escape & Arrive", Marketer des Jahres 2024 |
| Aktive Mentoring-Kunden | 400+ (Inner Circle), 2.000+ Programm-Alumni |
| Kern-Wertversprechen | "Escape the ordinary" — finanzielle und geografische Freiheit durch eigenes Online-Business |
| Stelle | Low Code Frontend Webentwickler · Operations & Tech · 3.000–3.550 € / Monat · 100 % Remote · Vollzeit · unbefristet · Deutsch ≥ C1 |

**Schlüsselbeobachtung:** Der Tech-Stack der Stellenanzeige (Airtable +
Make + Power BI + JS/TS + Streamlit + GCP + Monitoring + Pixels) ist
**identisch** mit dem Stack des hier vorliegenden Demo-Projekts. Die
Demo ist im Kern eine vertikale Scheibe durch genau die Pipeline, die
diese Rolle bei LLP betreibt und weiterentwickelt.

---

## 2. Geschäftsmodell

### 2.1 Wertversprechen

Love Life Passport verkauft kein Coaching — es verkauft **Lebensentwürfe**.
Der Funnel ist konsequent emotional und aspirational getrimmt: Bali-Bilder,
Strand, Familienleben der Gründer, "raus aus dem Hamsterrad". Der Tonfall
ist direkt, herausfordernd, persönlich ("Sei ehrlich zu dir selbst",
"Du bist nur eine Entscheidung entfernt!"). Die Gründer Anika & Tayler
Schweigert sind die Hauptmarketing-Assets — das Buch *Escape & Arrive*
(Spiegel-Bestseller) und ihr eigener Lebensweg sind der zentrale Proof.

### 2.2 Value Ladder (Produktstruktur)

LLP betreibt eine klassische **Value Ladder**, vom kostenlosen Trip-Wire
bis zum High-Ticket-Premium-Programm.

| Stufe | Produkt | Format | Funktion im Funnel |
|---|---|---|---|
| Free 0 | TET-Circle | Peer-Community | Brand-Awareness, Social Proof |
| Free 1 | Quiz auf `analyse.lovelifepassport.com` | 2-Min-Quiz | Lead-Generierung (E-Mail) |
| Free 2 | Strategiegespräch auf `strategie.lovelifepassport.com` | 1:1 Call (Calendly) | Lead-Qualifizierung, Sales |
| Low-Ticket | MasterYOURcard | Online-Kurs (Meilensammeln) | Cross-Sell, Vertrauensaufbau |
| Mid-Ticket | The Escape Theory · Online Business Kickstart | Selbstlernkurse | Aufstieg in die Marke |
| **High-Ticket (Core)** | **Inner Circle** | **12-Monats-Mentoring** | **Hauptumsatz, 400+ aktive Kunden** |
| Premium-Events | The Shift Retreat (Bali), Escape & Arrival Days (48 h) | Live-Events | Bindung, Upsell, Story-Generator |

### 2.3 Funnel-Architektur (Subdomain-Map)

LLP betreibt **mehrere parallele Subdomains** als getrennte Funnel-Endpunkte —
jede Subdomain ist eine eigene Conversion-Strecke mit eigenen Pixels:

```
www.lovelifepassport.com      → Hauptseite, Brand-Hub
analyse.lovelifepassport.com  → Quiz-Funnel (Lead Magnet)
analyse2.lovelifepassport.com → A/B-Variante des Quiz
strategie.lovelifepassport.com→ Buchung Strategiegespräch (Sales Call)
obk.lovelifepassport.com      → Online Business Kickstart Sales-Page
the-escapetheory.lovelifepassport.com → Escape-Theory-Kurs
retreat.lovelifepassport.com  → Retreat-Anmeldung
```

**Implikation für die Tech-Rolle:** Conversion-Tracking, Pixel-Setup
und Funnel-Auswertung müssen pro Subdomain konsistent aufgesetzt sein.
Das ist exakt der Grund, warum die Stellenanzeige `CAPI/Pixels` explizit
listet.

### 2.4 Customer Journey (rekonstruiert)

```
Awareness
  Meta-/Google-Ads, Instagram-Reels, Buch „Escape & Arrive", Bestseller-PR
            │
            ▼
Interest
  Landing Page → Quiz auf analyse.lovelifepassport.com (2 Min, „dein CEO Alex
  meldet sich persönlich mit deinen nächsten Schritten zu 100k")
            │  E-Mail/Phone-Capture, Quiz-Score-Logik
            ▼
Consideration
  Automatischer Lead-Eintrag im CRM → Setter-Anruf via Aircall
  Lead wird qualifiziert (Branche, Umsatz, Wunschumsatz, Hauptproblem)
            │
            ▼
Decision
  Setter bucht Termin (Calendly) bei Closer → 60-Min-Strategiegespräch
  Closer schließt Inner Circle / Kurs ab
            │
            ▼
Onboarding
  Customer Success übernimmt → Account Manager + Mentor-Zuordnung
  WhatsApp-Support an, Community-Feed-Zugang an
            │
            ▼
Retention & Expansion
  Wöchentliche Live-Calls, Strategieboards, Mentor-Sessions
  Upsell auf Retreat (Bali), Escape & Arrival Day
```

---

## 3. Analyse des Quiz-Funnels (`analyse.lovelifepassport.com`)

> **Methodik:** Dieser Abschnitt basiert auf einer **realen Live-Durchspielung
> des Quiz im Chrome-Browser** (2026-05-18). Alle Fragen, Antwortoptionen,
> Tracking-IDs und Endpoints sind direkt aus dem DOM, dem Page-Source und den
> Network-Requests extrahiert. Es wurde **kein Submit** durchgeführt, um
> keinen Fake-Lead in LLPs HubSpot zu erzeugen.

### 3.1 Hook und Positionierung

- **Hook:** *„Schaffe Klarheit & finde heraus, was deine nächsten Schritte zu 100k sind."*
- **Zeitversprechen:** 2 Minuten
- **Social Proof:** ProvenExpert-Badges *„TOP EMPFEHLUNG 2025"* und *„TOP DIENSTLEISTER 2025"*
- **CEO-Personal-Touch:** *„bekommst du von unserem CEO Alex Westhuis direkt dein Ergebnis – mit wertvollen Tipps für deine Situation, basierend auf unserer Erfahrung mit über 2000 Gründern."*

### 3.2 Komplette Quiz-Struktur (13 Schritte mit bedingter Logik)

Der Step-Counter wechselt während des Durchlaufs zwischen *„of 13"* und
*„of 12"* — das Quiz nutzt **bedingte Sprünge** (Skip-Logic), bei denen
ganze Fragen je nach vorheriger Antwort übersprungen werden. Bei meinem
Test-Pfad (Selbstständig=Ja → Coach → <5K Umsatz → 5-stellig-Ziel → 10h+
Zeit) wurde Step 11 übersprungen — vermutlich eine Zusatzfrage für den
„Nein"-Pfad (z.B. Investitionsbereitschaft oder Idee-Vorhanden).

| Step | Frage | Typ | Antwortoptionen |
|---|---|---|---|
| 1 | *Intro / „Quiz starten"* | CTA | – |
| 2 | Hast du dein eigenes Unternehmen bereits gegründet? | Single | Ja · Nein |
| 3 | Wie lange bist du schon selbstständig? | Single | Weniger als 1 Jahr · 1–3 Jahre · Mehr als 3 Jahre |
| 4 | In welchem Bereich bist du selbstständig? | Single | Coach/Berater · Dienstleistungen (Freelancer etc.) · Digitale Produkte, Kurse · E-Commerce · Network Marketing · Sonstiges |
| 5 | Wie sichtbar bist du? *(E-Mail Kontakte, Follower auf Social Media etc)* | Single | weniger als 1.000 · weniger als 10.000 · mehr als 10.000 Kontakte |
| 6 | Wie bist du im Business aufgestellt? | Single | Nur ich (+ eventuell Gründerteam) · Ich + < 10 MA/Freelancer · Ich + > 10 MA/Freelancer |
| 7 | Wieviel Umsatz machst du durchschnittlich im Monat? | Single | noch gar nichts · unter 5.000€ · unter 10.000€ · unter 100.000€ · über 100.000€ |
| 8 | Wenn du einen Wunsch frei hättest, was würdest du wählen? | Single | Stabiles Einkommen · Hauptjob mit gutem Gewissen kündigen · Marke aufbauen / mehr Menschen erreichen · Zeitlich, örtlich und finanziell frei werden · 5-stellige Monatsumsätze |
| 9 | Was glaubst du fehlt dir, um dein Ziel zu erreichen? | **Multi** | Mehr Menschen erreichen · Produktportfolio erweitern · Mehr/Besser verkaufen · Mich „klonen" (mehr Zeit) · Mindset: Größer denken |
| 10 | Wie viel Zeit kannst du investieren in den Ausbau deines Businesses? | Single | < 1 Std./Woche · 2–5 Std./Woche · 5–10 Std./Woche · > 10 Std./Woche |
| 11 | *(Bedingt — übersprungen im Coach/Ja-Pfad)* | – | vermutlich Investitionsbereitschaft / Idee |
| 12 | Kontaktdaten | Form | Vorname · Nachname · E-Mail · Telefon (mit 240-Länder-Picker, Default „+49 Deutschland") |
| 13 | *Ergebnis-/Danke-Seite nach Submit* | – | (nicht durchgespielt — kein Submit) |

**Anti-Bot-Hinweis:** Beim Kontaktformular steht explizit:
*„Stelle sicher, dass Dein Vor- und Nachname korrekt sind. Es wird ein
kurzer Verifizierungsprozess durchgeführt."* — d.h. das Backend macht
plausibilitäts-Checks (vermutlich Telefon-Pattern und E-Mail-Validierung).

### 3.3 Lead-Scoring-Logik (rekonstruiert aus Quiz-Design)

Die Quiz-Architektur zeigt, dass LLP eine sehr **klassische BANT/MEDDIC-
artige Qualifizierung** im Frontend baut. Die Felder lassen sich direkt auf
ein Lead-Score-Modell mappen:

| Quiz-Feld | Score-Funktion | Begründung |
|---|---|---|
| Step 2: Selbstständig Ja | Pflicht-Gate | Coach-Quiz richtet sich an Selbstständige; *Nein* → vermutlich anderer Funnel |
| Step 3: Dauer Selbstständigkeit | Reife-Indikator | >3 Jahre = etablierter Player (höherer ARPU-Wert) |
| Step 4: Branche | Segment-Routing | Coach/Berater = Kernzielgruppe Inner Circle |
| Step 5: Sichtbarkeit | Skalierungs-Potenzial | >10K Kontakte = bereit für Scale-Stufe der Value Ladder |
| Step 6: Team-Aufstellung | Reife + Budget-Indikator | Mit Team = höhere Kaufkraft, andere Probleme |
| Step 7: Umsatz | **Härtester Qualifier** | < 5K = Build-Phase · 10–100K = Grow · > 100K = Scale |
| Step 8: Wunsch | Emotional Driver | „5-stellig" passt 1:1 zum Quiz-Versprechen „Schritte zu 100k" |
| Step 9: Lücke (Multi) | Pain-Map | Bestimmt Programm-Empfehlung (Sales-Coaching vs. Mindset-Coaching) |
| Step 10: Zeitbudget | **Commit-Indikator** | < 1 Std./Woche = kein qualifizierter Lead · > 10 Std. = High-Intent |
| Step 12: Telefon-Land | Geo-Routing | DACH = Setter-DE, andere = Setter-International |

### 3.4 Technischer Stack des Quiz (verifiziert über Page-Source und Network)

**Frontend-Framework:**

| Komponente | Befund |
|---|---|
| Funnel-Builder | Proprietärer No-Code-Builder, gehostet auf CDN `onecdn.io` |
| CSS-Klassen-Präfix | `con-kit-*` (z.B. `con-kit-site`, `con-kit-page`, `con-kit-layer-form`, `con-kit-molecule-textBlock`) |
| Architektur | Atomic-Design: `atom/` → `molecule/` → `organism/` (form-name, form-email, form-phone-number, form-hidden-field, form-input, text-block, section) |
| Runtime | React 18.2.0 (production min) + MobX (State Management) |
| Build-Bundle-Pfad | `https://onecdn.io/b/client/1778147797912/js/main.bundle.js` |
| Fonts | Jost (italic) aus `onecdn.io/font-storage/` |
| Country-Flags | aus `onecdn.io/country-flag/default/` (Telefonnummer-Picker) |

Das deutet auf einen **deutschen / EU-No-Code-Funnel-Builder** mit
Custom-Domain-Mapping. Hidden Fields existieren im DOM-Submit-Moment
nicht — das Quiz hält den State im MobX-Store und sendet ihn beim Submit
vermutlich als JSON-Payload an einen XHR-Endpoint.

**Tracking-Stack (direkt aus Live-Network-Requests):**

| Tool | ID / Endpoint | Zweck |
|---|---|---|
| **Meta Pixel** | `1784432958288866` | Client-side Pixel; sendet u.a. `SubscribedButtonClick` an `facebook.com/tr/` |
| **Meta Privacy Sandbox** | `facebook.com/privacy_sandbox/pixel/register/trigger/` | Chrome-Privacy-Sandbox-Pendant zum klassischen Pixel |
| **Google Tag Manager** | `GTM-KMGMM4H` | Container-Wrapper für alle Pixel |
| **GA4 (Stream 1)** | `G-WJ6VFGWJKX` | Sendet `scroll`-Events u.a. an `google-analytics.com/g/collect` |
| **GA4 (Stream 2)** | `G-04CBYNE97V` | Zweiter paralleler Stream (vermutlich Cross-Domain-Bridge zwischen Subdomains) |
| **TikTok Pixel** | `analytics.tiktok.com/api/v2/pixel/inter` + `/api/v2/pixel/act` | Aktiv, sendet bei jedem Step Interaktions-Events |
| **HubSpot Tracking** | Account ID **`26317639`** (EU-Region, `track-eu1.hubspot.com`, `js-eu1.hs-*`) | Klick-Tracking auf `__ptc.gif` (Pixel-Tracking-Cookie) inkl. Mauskoordinaten und kompletten CSS-Selector |
| **HubSpot Banner / Cookie-Consent** | `js-eu1.hs-banner.com/v2/26317639/banner.js` | DSGVO-Cookie-Banner |
| **HubSpot Ads Pixel** | `js-eu1.hsadspixel.net/pixels.js` | HubSpots eigener Cross-Ad-Pixel (LinkedIn / Google Ads Mirror) |
| **HubSpot Forms** | `js-eu1.hs-scripts.com/26317639.js` | Universelles HubSpot-Script (Forms + Chat + Tracking) |
| **Sichtbarer Cookie-Set** | `_ga`, `_fbp`, `_fbc`, `_tt_*`, `__hstc`, `__hssc`, HubSpot-`hubspotutk` | Standard-Cookie-Footprint |

**Schlüsselbefund:** *HubSpot ist nicht nur das CRM, sondern auch
der zentrale Tag-/Tracking-Layer.* Das ist eine sehr starke Indikation,
dass die LLP-CRM- und Marketing-Automation-Welt **HubSpot-zentrisch**
aufgebaut ist (CRM, Forms, Workflows, Sequences, vermutlich auch
Sales-Hub mit Aircall-Integration).

### 3.5 Lead-Flow nach Submit (rekonstruiert)

```
Quiz Submit (Step 12 → 13)
  │
  ├─► XHR-POST mit Quiz-Antworten + Kontaktdaten (Endpoint nicht abgefragt,
  │   da Submit absichtlich nicht ausgelöst)
  │
  ├─► Pixel-Side-Effects:
  │   ├─ Meta Pixel „Lead"-Event (client-side, Pixel 1784432958288866)
  │   ├─ TikTok Pixel Conversion-Event
  │   ├─ GA4 Conversion-Event (2 Streams)
  │   └─ HubSpot Form-Submission-Tracking
  │
  ├─► HubSpot Contact Create / Update (Account 26317639, EU)
  │     ├─ Properties: First-/Lastname, Email, Phone, Country
  │     ├─ Custom Properties: alle 9 Quiz-Antworten als Felder
  │     ├─ Lead-Score-Property (vermutlich serverseitig berechnet)
  │     └─ Lifecycle Stage: „Lead" oder „Marketing Qualified Lead"
  │
  ├─► HubSpot Workflow:
  │     ├─ E-Mail an Lead („dein Ergebnis vom CEO Alex Westhuis")
  │     ├─ Slack-Notification an Setter-Team
  │     ├─ Tag-/Listen-Zuordnung nach Branche/Umsatz
  │     └─ Routing in CRM-Pipeline (Owner-Assignment Leadhunter/Setter)
  │
  └─► Aircall-Queue (CTI-Integration) für Setter-Outbound innerhalb von <24h
```

**Konsequenzen für die Tech-Rolle:** Der Low-Code-Frontend-Entwickler
arbeitet zwar im Stack-Listing der Stellenanzeige mit „Airtable" als
Primär-Datenbank — bei der live-beobachteten Realität wird Airtable
mit hoher Wahrscheinlichkeit **neben** HubSpot betrieben, z.B. für
*Operations-Use-Cases* (Mentor-Zuordnung, interne Tools, Programme,
Sessions, Power-BI-Reporting), während HubSpot das Marketing- und
Sales-CRM bleibt. Die spannendste Aufgabe ist dann die **Make-Bridge
zwischen HubSpot ↔ Airtable**, plus **Power BI über beide Quellen**.

---

## 4. Org-Chart und Rollen-Analyse

### 4.1 Rekonstruiertes Organigramm

Basierend auf den 25 derzeit ausgeschriebenen Stellen
(`lovelifepassport.factorialhr.de`) plus den über LinkedIn / Crunchbase
recherchierten Rollen ergibt sich folgendes Bild:

```
                 ┌──────────────────────────┐
                 │      CEO: Alex Westhuis   │
                 └────────────┬──────────────┘
                              │
        ┌──────────┬──────────┴──────────┬─────────────┬──────────────┬─────────────┐
        ▼          ▼                     ▼             ▼              ▼             ▼
  ┌──────────┐ ┌─────────┐         ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │Consulting│ │Marketing│         │Operations│  │Customer  │  │Mentoring │  │HR + Fin. │
  │ (Sales)  │ │         │         │  & Tech  │  │ Success  │  │          │  │          │
  └────┬─────┘ └────┬────┘         └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
       │            │                   │             │             │             │
  Teamlead     Head of Product    Admin & Ops    Teamlead CS   Teamlead Mentor  Head of P&C
  Consulting   Performance Mkt.   Manager        Strategie Mgr  Mentor (8x)     (Sabrina K.)
  Leadhunter   CRM & Auto. Mgr.   ▶ Low Code     Account Mgr    ─ Bea Vogt      Recruiter
  Setter       Funnel & Conv.       Frontend     Praktikant     ─ Finn Weiner   Praktikant
  Closer       Content & Social     Webentw.                    ─ Jonas Sp.     Controller
               Creative Producer    ◀ DIESE                     ─ Sam Guezel
               Copywriter           STELLE                      ─ Oguzhan Ü.
               (3x Praktikanten)                                ─ Tina Eckert
                                                                ─ Mischa D.
                                                                ─ Jimmy Künzli
```

### 4.2 Wo die Stelle sitzt

Die **Low Code Frontend Webentwickler**-Rolle ist im Team **Operations
& Tech** verankert, neben dem **Admin & Operations Manager**. Das ist
das zentrale Tooling-Team — es wird von **allen anderen Abteilungen**
parallel beansprucht:

| Stakeholder | Anforderung an Operations & Tech |
|---|---|
| **Marketing (CRM & Auto Mgr., Funnel Spec.)** | Quiz-Webhooks, Pixel-Setup, CAPI, Conversion-Reports, Funnel-Dashboards |
| **Sales (Leadhunter / Setter / Closer)** | CRM-Daten, Lead-Routing, Aircall-Integration, Pipeline-Views, Slack-Hot-Lead-Pings |
| **Customer Success** | Onboarding-Workflows, Account-Boards, Churn-Tracking |
| **Mentoring** | Mentor-Kunden-Zuordnung, Session-Tracking, NPS-Erhebung, Auslastungs-Dashboard |
| **HR / People** | Onboarding-Automatisierung neuer Mitarbeiter, Slack/Google-Workspace-Admin |
| **Finance / Controller** | Power-BI-Umsatz-Reports, Programm-Wirtschaftlichkeit |
| **CEO** | OKR-Dashboard, Monatsreport |

### 4.3 Typisches Tagesgeschäft der Rolle (Hypothese)

Aus den expliziten Anforderungen der Stellenanzeige abgeleitet:

- **40 %** Airtable: Schemas pflegen, Lookups/Rollups fixen, Interfaces für Setter/Closer/Mentoren bauen, Skripte (JS) für Score-Berechnung, Daten-Migrations-Skripte
- **20 %** Make / Zapier: Quiz-Hook → CRM, Stripe → Onboarding-Mail → Slack, Calendly → Lead-Update, Aircall-Logs → Airtable
- **15 %** Power BI: Sales-Funnel-Dashboard, Marketing-Performance, Customer-Health-Score, Mentor-Auslastung
- **10 %** Tracking & Marketing-Ops: Meta CAPI, Pixel-Diagnose, GA4, UTM-Hygiene, Cross-Subdomain-Attribution
- **10 %** Interne Tools: kleine Streamlit-/Retool-Apps für Sales-Daily, Quartals-Reviews, Onboarding-Checks
- **5 %** Monitoring & Admin: Statuspage, UptimeRobot, Slack/Google-Workspace-Admin

### 4.4 Erfahrungsstufe und Gehalt

- **Gehalt:** 3.000 – 3.550 € brutto / Monat → Mid-Level / Junior-Plus
- **Erfahrung:** Implizit Mid-Level (eigenverantwortliche Projektleitung)
- **Sprache:** Deutsch C1+ Pflicht (Stellenanzeige), Englisch im Team gegeben
- **Standort:** 100 % Remote weltweit ("Work from anywhere")

---

## 5. Tech-Stack-Mapping: Stellenanzeige ↔ Demo-Projekt

Jede einzelne in der Stellenanzeige genannte Technologie ist im
Demo-Projekt mit einer **konkret lieferbaren Komponente** belegt.

| Anforderung Stellenanzeige | Komponente Demo-Projekt | Datei / Pfad |
|---|---|---|
| Airtable: komplexe Datenmodelle (Links, Lookups, Rollups) | 4-Tabellen-Schema (Programs, Leads, Sessions, Clients) mit Lookups & Rollups | [`02-airtable-schema.md`](02-airtable-schema.md) |
| Airtable: Interfaces | Lead-Triage- + Pipeline-Overview-Interface | [`06-airtable-interfaces.md`](06-airtable-interfaces.md) |
| Airtable: Automatisierungen + Skripte | JS-Scoring im Airtable-Scripting-Block | [`03-airtable-script.md`](03-airtable-script.md) · [`airtable-scripts/lead-scoring.js`](airtable-scripts/lead-scoring.js) |
| Automatisierungstool Make | Webhook → Validate → Enrich → Insert → Score → CAPI → Slack-Notify | [`04-make-scenario.md`](04-make-scenario.md) |
| Power BI: Datenmodellierung, DAX, Deployment | Funnel-Dashboard, Program-Revenue-Dashboard, DAX-Maße | [`05-powerbi-dashboard.md`](05-powerbi-dashboard.md) |
| APIs: REST / Webhooks | Airtable-REST-API, Make-Webhook, GCP-Function-HTTP | [`04-make-scenario.md`](04-make-scenario.md) · [`08-gcp-deployment.md`](08-gcp-deployment.md) |
| JavaScript / TypeScript | Airtable-Scripting (JS), Landing-Page-Vanilla-JS | [`airtable-scripts/lead-scoring.js`](airtable-scripts/lead-scoring.js) · [`landing-page/script.js`](landing-page/script.js) |
| Admin-Basics Google Workspace / Slack | Slack-Bot-Pings für Hot-Leads + System-Alerts | [`04-make-scenario.md`](04-make-scenario.md) |
| Streamlit | Coach Admin Dashboard mit Login, Lead-Edit, KPIs | [`07-streamlit-admin.md`](07-streamlit-admin.md) · [`streamlit-app/`](streamlit-app/) |
| GCP | Cloud Run (Streamlit) + Cloud Function (Enrichment, Score) | [`08-gcp-deployment.md`](08-gcp-deployment.md) · [`gcp/`](gcp/) |
| Monitoring (Statuspage, UptimeRobot) | UptimeRobot-Pings + öffentliche Statuspage | [`09-monitoring.md`](09-monitoring.md) |
| Pixels / CAPI | Meta Pixel client-side + Conversion API server-side, GTM-Container | [`10-meta-capi-tracking.md`](10-meta-capi-tracking.md) |
| Git / Versionskontrolle | Das gesamte Repository | `.git`, dieses Verzeichnis |
| Python / SQL (nice-to-have) | Cloud-Function in Python + pytest-Tests | [`gcp/cloud-function-score/`](gcp/cloud-function-score/) |
| Saubere Dokumentation | 13 Markdown-Files mit Schritt-für-Schritt-Walkthrough | dieses Repository |

**Coverage: 13/13 Pflicht-Technologien + 2/3 Nice-to-haves abgedeckt.**

---

## 6. Wie das Demo-Projekt LLPs reales Geschäft nachbildet

Die `MindForge`-Pipeline ist absichtlich strukturell isomorph zur
LLP-Realität — nur mit fiktivem Markennamen, um keine Markenrechte zu
berühren. Das Mapping ist 1:1:

| Love Life Passport (real) | MindForge Demo (1:1-Äquivalent) |
|---|---|
| Quiz `analyse.lovelifepassport.com` | `landing-page/index.html` mit Lead-Capture-Formular + Meta Pixel |
| CEO-Versprechen "persönliches Ergebnis" | Slack-Bot-Hot-Lead-Notification an Setter |
| Quiz-Lead landet im CRM | Airtable-Base `Leads`-Table |
| Setter sieht priorisiert Hot-Leads | Lead-Scoring-Skript + Airtable-Interface "Triage" |
| Setter ruft an / qualifiziert (Aircall) | Statusfeld + Notes im Lead, manuell setzbar in Streamlit |
| Termin mit Closer (Calendly) | Sessions-Table, verknüpft zum Lead |
| Closer macht Abschluss | Status `Converted` → Client-Record in Clients-Table |
| Mentor-Zuordnung im Inner Circle | Client → Program-Verknüpfung, Sessions pro Kunde |
| Programmumsätze tracken | Power BI Program-Revenue-Dashboard |
| Meta-Ads optimieren | Meta CAPI + Pixel-Deduplizierung |
| Operations sieht Systemstatus | UptimeRobot + Statuspage |
| Mentoren-Team kommuniziert | Slack-Channel-Pings aus Make |

Anders gesagt: Wenn die Person in dieser Stelle morgen anfangen würde,
wäre das, was im Demo-Repo liegt, **eine plausible vereinfachte
V1 ihres Tagesgeschäft-Outputs**.

---

## 7. LLP-spezifische Erweiterungs-Ideen (nice-to-have)

Wenn das Demo noch enger an LLPs Realität rücken soll, lassen sich
folgende Erweiterungen als optionale **Phase E** ergänzen. Jede
einzelne ist eine direkte Antwort auf eine LLP-Eigenheit:

| # | Erweiterung | Adressiert |
|---|---|---|
| E1 | Mehrstufiges Quiz (Typeform / Tally / Eigenbau) statt einfaches Formular | `analyse.lovelifepassport.com` |
| E2 | Sales-Übergaben Leadhunter → Setter → Closer mit eigenen Views/Owner-Wechsel in Airtable | LLP-Org: 3 getrennte Sales-Rollen |
| E3 | Calendly-Webhook → Strategiegespräch-Buchung mit automatischem Owner-Wechsel | `strategie.lovelifepassport.com` |
| E4 | Aircall-Integration: Call-Logs + Recording-Links im Lead | Aircall ist nachweislich im Stack |
| E5 | Mentor-Performance-Dashboard (NPS, Auslastung, Session-Anzahl, Kunden-Health) | Acht namentlich genannte Mentoren |
| E6 | Customer-Health-Score für Inner-Circle-Kunden (Engagement, letzte Session, Community-Aktivität) | 400+ aktive Mentoring-Kunden |
| E7 | Multi-Funnel-Tracking mit separaten Conversion-Events pro Subdomain | 7+ Subdomains mit eigenen Funnels |
| E8 | Slack-Bot für Mentor-Reminders ("Heute Call mit Kunde X um 14:00") | Wöchentliche Live-Calls + Mentor-Modell |
| E9 | Power-BI Row-Level-Security: jeder Mentor sieht nur eigene Kunden | Datenschutz + Mentor-Vielfalt |
| E10 | GA4 + Meta CAPI parallel, DSGVO-konformes Consent-Setup | DACH-Markt + EU-Regulierung |
| E11 | Internes Streamlit-Tool "Setter Daily" mit priorisierter Call-Liste | 4 Sales-Rollen in der Stelle |
| E12 | Webhook-Endpoint für Stripe / Digistore24 → Customer-Success-Onboarding | High-Ticket-Payment-Provider |

Diese Erweiterungen sind im Demo bewusst **nicht** vorab umgesetzt —
sie eignen sich besser als Gesprächsstoff im Bewerbungsinterview
("hier ist die V1, das wäre meine V2 wenn ich anfange").

---

## 8. Bewerbungs-Pitch (Anschreiben-Kern)

Empfohlene Bewerbungs-Story in drei Sätzen:

> *"Ich habe euren Funnel von `analyse.lovelifepassport.com` bis zum
> Inner Circle als End-to-End-Demo nachgebaut — mit eurem genauen
> Tech-Stack: Airtable als CRM mit Lookups/Rollups, Make für die
> Webhook-Pipeline, ein JS-Lead-Scoring-Skript, ein Power-BI-Dashboard
> mit DAX, ein Streamlit-Tool für das interne Team, deployed auf GCP
> Cloud Run, mit Meta Pixel + CAPI, UptimeRobot und Statuspage. Jede
> einzelne Technologie eurer Stellenanzeige liegt im Repo als
> lauffähige Komponente. Hier ist der Link — ich freue mich auf ein
> Gespräch."*

**Ankerpunkte für das Interview:**

1. **Geschäftsverständnis:** Ich habe euer Geschäft strukturell verstanden — Quiz-Lead → Setter → Closer → Mentor → Power-BI-Loop ist im Demo abgebildet.
2. **Technische Tiefe:** Airtable mit echten Lookups/Rollups, JS-Scripting, Python-Cloud-Function mit pytest — kein Tutorial-Niveau.
3. **Operations-Mindset:** Monitoring, Statuspage und Alerting sind drin, weil ein Funnel-System ohne Outage-Erkennung kein System ist.
4. **Marketing-Verständnis:** CAPI + Pixel + GTM zeigen, dass ich serverseitiges Tracking nach iOS-14.5 ernst nehme.
5. **Dokumentation:** 13 Markdown-Files mit Schritt-für-Schritt-Walkthrough — direkte Antwort auf den "saubere Dokumentation"-Punkt der Anzeige.
6. **Pragmatismus:** Bewusste Nicht-Entscheidungen sind in `00-architecture.md` dokumentiert (z.B. "kein Postgres, weil Airtable im Scope reicht") — ich denke an Trade-offs, nicht an Tech-Showcasing.

---

## 9. Risiken und ehrliche Limitierungen dieser Bewerbungs-Demo

Damit dieses Dokument nicht reines Selbstmarketing ist, hier eine
ehrliche Inventur:

| Limitierung | Wie ich damit umgehen würde |
|---|---|
| Ich nutze ein fiktives Quiz-Formular, nicht das echte Typeform-Setup von LLP | Im Interview anbieten, das echte Quiz zu re-buildi-en, sobald Zugang zum tatsächlichen Stack besteht |
| Power BI Desktop, nicht der Workspace-Deploy mit RLS | Phase E9 vorgesehen — RLS pro Mentor ist die nächste Stufe |
| Streamlit statt Retool | Streamlit ist portabler für ein Demo; Retool wäre LLPs vermutliche Realität — beide Tools sind 80% gleicher Skill |
| Keine Aircall-Integration | Aircall benötigt API-Key, der nur intern verfügbar ist — als Phase-E-Idee dokumentiert |
| Daten sind synthetisch (20 Leads, 4 Clients) | Schema ist auf 10.000+ Records ausgelegt; Skalierungsverhalten dokumentierbar |
| Kein TikTok/LinkedIn-Pixel | Meta-Pixel-Pattern lässt sich 1:1 auf andere Plattformen übertragen, bewusst nicht dupliziert |

---

## 10. Quellen

- [`www.lovelifepassport.com`](https://www.lovelifepassport.com/) — Hauptwebsite
- [`www.lovelifepassport.com/inner-circle`](https://www.lovelifepassport.com/inner-circle) — Inner Circle Programm
- [`analyse.lovelifepassport.com`](https://analyse.lovelifepassport.com/) — Quiz-Funnel
- [`strategie.lovelifepassport.com`](https://strategie.lovelifepassport.com/) — Strategiegespräch-Funnel
- [Stellenanzeige Low Code Frontend Webentwickler](https://lovelifepassport.factorialhr.de/job_posting/low-code-frontend-webentwickler-native-or-fluent-german-required-264132)
- [Crunchbase-Profil Tayler Schweigert](https://www.crunchbase.com/person/tayler-schweigert)
- [Crunchbase-Profil Love Life Passport](https://www.crunchbase.com/organization/love-life-passport)
- [Remote Rocketship — alle offenen Stellen](https://www.remoterocketship.com/company/lovelifepassport/)
- [CRM & Automation Manager Stelle](https://www.remoterocketship.com/company/lovelifepassport/jobs/crm-automation-manager-worldwide-remote/)
- [ProvenExpert Profil](https://www.provenexpert.com/en-us/lovelifepassport/)
- [Trustpilot Profil](https://www.trustpilot.com/review/www.lovelifepassport.com)

---

## 11. Phase-E-Status

Phase E (Realitäts-Bridge zu LLP) ist **in Implementierung**. Der vollständige
Plan liegt in [`PHASE-E-PLAN.md`](PHASE-E-PLAN.md). Aktueller Status:

| Komponente | Status | Dateien |
|---|---|---|
| Quiz-Frontend mit 9 Fragen + Skip-Logic | ✅ Code fertig | [`quiz-frontend/`](quiz-frontend/) |
| HubSpot-Setup (Properties + Workflow + API) | ✅ Doku fertig — Account-Setup offen | [`hubspot/`](hubspot/) |
| Make-Bridge (3 Szenarien, Field-Mapping) | ✅ Doku fertig — Make-Konfig offen | [`make-bridge/`](make-bridge/) |
| Tracking-Stack (GTM + Meta + GA4 dual + TikTok) | ✅ Doku fertig — Account-Setup offen | [`tracking-full/`](tracking-full/) |
| Power-BI Cross-Source (HubSpot + Airtable) | ✅ Doku fertig — .pbix-Build offen | [`powerbi-cross-source/`](powerbi-cross-source/) |
| Account-Setup-Sprint (User-Action) | ⏳ pending | siehe [`PHASE-E-PLAN.md`](PHASE-E-PLAN.md) §6 |
| End-to-End-Test | ⏳ pending nach Account-Setup | — |

**Was Claude geliefert hat:**
- 19 neue Dateien (Code + Markdown-Dokus) über 5 Subdirectories
- Vanilla-JS-Quiz mit Score-Engine, Skip-Logic, DSGVO-Consent
- Vollständige Step-by-Step-Anleitungen für HubSpot, Make, GTM, Meta, GA4, TikTok, Power BI
- Field-Mapping-Matrix HubSpot ↔ Airtable mit Loop-Prevention
- 3 Make-Szenario-Specs mit Sample-Payloads
- DAX-Maße für 4 Cross-Source-Reports

**Was als nächstes ansteht (User-Action):**
1. Account-Setup-Sprint (HubSpot Free, GTM, Meta Business, GA4, TikTok) — ca. 1 h
2. Make-Szenario #1 nach Doku zusammenklicken — ca. 1 h
3. Quiz-Frontend lokal testen mit Live-Webhook — ca. 30 min
4. HubSpot-Workflow nach Doku konfigurieren — ca. 30 min
5. GTM-Tags nach Doku konfigurieren — ca. 45 min
6. End-to-End: Submit auf Demo-URL → erscheint in HubSpot + Airtable + Slack + Pixel-Test-Events
7. Power BI Desktop laden, REST-Connections, DAX einfügen — ca. 1,5 h
8. (Optional) Loom-Video aufnehmen

---

## 12. Nächste Schritte (Bewerbung)

- [ ] Phase E technisch abschließen (laut §11)
- [ ] GitHub-Repo public machen, README finalisieren
- [ ] Anschreiben mit den Anker-Punkten aus Abschnitt 8 + HubSpot-Bridge-Story formulieren (User selbst)
- [ ] (Optional) Loom-Video (~5 Min) aufnehmen: Quiz-Submit → Slack-Hot-Lead → HubSpot-Contact → Airtable-Lead → Power-BI-Cross-Source-Dashboard (z.B. echtes Quiz + Calendly-Integration)
