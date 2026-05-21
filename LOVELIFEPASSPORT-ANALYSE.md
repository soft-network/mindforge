# Love Life Passport — Geschäfts- und Funnel-Analyse

**Zweck dieses Dokuments:** Technischer Hintergrund-Kontext für das
Demo-Projekt `MindForge Coaching Pipeline`. Die Architektur des Demos
ist an einem realen High-Ticket-Coaching-Funnel (Love Life Passport)
orientiert. Dieses Dokument hält fest:

1. wie Love Life Passport als Geschäft funktioniert,
2. wie der reale Funnel (analyse.lovelifepassport.com → Strategiegespräch → Inner Circle) aufgebaut ist,
3. welche Tools im Stack live verifizierbar sind und welche das Demo zusätzlich abbildet.

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

**Schlüsselbeobachtung:** Live-Inspektion (Mai 2026) zeigt einen
HubSpot-zentrierten Marketing-/Sales-Stack mit OnePage.io-Funnel-Builder
für Quiz-Frontends, ClickFunnels für Webinar-Funnels, Hotjar für
Session-Recording und Aircall für Setter-Telefonie. Eine
Operations-Datenbank (Airtable/Make/Power BI) und interne Tools
(Streamlit/GCP) sind extern nicht beobachtbar — diese Schicht bildet
das Demo zusätzlich ab.

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
| Free 2 | Strategiegespräch auf `strategie.lovelifepassport.com` | 1:1 Call (Setter bucht Termin manuell im Aircall-Telefonat — Self-Service-Booking ist nicht beobachtbar) | Lead-Qualifizierung, Sales |
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

**Implikation für die Architektur:** Conversion-Tracking, Pixel-Setup
und Funnel-Auswertung müssen pro Subdomain konsistent aufgesetzt sein —
inklusive serverseitiger Conversion-API für iOS-14.5-Robustheit.

### 2.4 Customer Journey (rekonstruiert)

```
Awareness
  Meta-/Google-Ads, Instagram-Reels, Buch „Escape & Arrive", Bestseller-PR
            │
            ▼
Interesse
  Landing Page → Quiz auf analyse.lovelifepassport.com (2 Min, „dein CEO Alex
  meldet sich persönlich mit deinen nächsten Schritten zu 100k")
            │  E-Mail/Telefon-Capture, Quiz-Score-Logik
            ▼
Consideration
  Automatischer Lead-Eintrag im CRM → Setter-Anruf via Aircall
  Lead wird qualifiziert (Branche, Umsatz, Wunschumsatz, Hauptproblem)
            │
            ▼
Decision
  Setter vereinbart Termin manuell im Aircall-Telefonat → 60-Min-Strategiegespräch beim Closer
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
| Land-Flags | aus `onecdn.io/country-flag/default/` (Telefonnummer-Picker) |

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
  │     ├─ Properties: First-/Lastname, E-Mail, Telefon, Land
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

**Konsequenz für die Demo-Architektur:** Airtable läuft **neben**
HubSpot, nicht als Ersatz. HubSpot bleibt Marketing-/Sales-CRM,
Airtable übernimmt Operations-Use-Cases (Mentor-Zuordnung, interne
Tools, Programme, Sessions). Die Brücke dazwischen ist eine
**Make-Bridge HubSpot ↔ Airtable**, plus **Power BI über beide
Quellen** für Cross-Source-Reporting.

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
  Leadhunter   CRM & Auto. Mgr.   Low Code       Account Mgr    ─ Bea Vogt      Recruiter
  Setter       Funnel & Conv.     Frontend       Praktikant     ─ Finn Weiner   Praktikant
  Closer       Content & Social   Webentw.                      ─ Jonas Sp.     Controller
               Creative Producer                                ─ Sam Guezel
               Copywriter                                       ─ Oguzhan Ü.
               (3x Praktikanten)                                ─ Tina Eckert
                                                                ─ Mischa D.
                                                                ─ Jimmy Künzli
```

### 4.2 Stakeholder-Map des Operations-&-Tech-Teams

Das zentrale Tooling-Team **Operations & Tech** wird von allen anderen
Abteilungen parallel beansprucht. Diese Stakeholder-Map ist die
Grundlage für die im Demo gebauten Komponenten:

| Stakeholder | Anforderung an Operations & Tech |
|---|---|
| **Marketing (CRM & Auto Mgr., Funnel Spec.)** | Quiz-Webhooks, Pixel-Setup, CAPI, Conversion-Reports, Funnel-Dashboards |
| **Sales (Leadhunter / Setter / Closer)** | CRM-Daten, Lead-Routing, Aircall-Integration, Pipeline-Views, Slack-Hot-Lead-Pings |
| **Customer Success** | Onboarding-Workflows, Account-Boards, Churn-Tracking |
| **Mentoring** | Mentor-Kunden-Zuordnung, Session-Tracking, NPS-Erhebung, Auslastungs-Dashboard |
| **HR / People** | Onboarding-Automatisierung neuer Mitarbeiter, Slack/Google-Workspace-Admin |
| **Finance / Controller** | Power-BI-Umsatz-Reports, Programm-Wirtschaftlichkeit |
| **CEO** | OKR-Dashboard, Monatsreport |

### 4.3 Aufwands-Verteilung in Operations & Tech (Schätzung)

- **40 %** Airtable: Schemas pflegen, Lookups/Rollups fixen, Interfaces für Setter/Closer/Mentoren bauen, Skripte (JS) für Score-Berechnung, Daten-Migrations-Skripte
- **20 %** Make / Zapier: Quiz-Hook → CRM, Stripe → Onboarding-Mail → Slack, Google Cal → Lead-Update, Aircall-Logs → Airtable
- **15 %** Power BI: Sales-Funnel-Dashboard, Marketing-Performance, Customer-Health-Score, Mentor-Auslastung
- **10 %** Tracking & Marketing-Ops: Meta CAPI, Pixel-Diagnose, GA4, UTM-Hygiene, Cross-Subdomain-Attribution
- **10 %** Interne Tools: kleine Streamlit-/Retool-Apps für Sales-Daily, Quartals-Reviews, Onboarding-Checks
- **5 %** Monitoring & Admin: Statuspage, UptimeRobot, Slack/Google-Workspace-Admin

---

## 5. Wie das Demo-Projekt LLPs reales Geschäft nachbildet

Die `MindForge`-Pipeline ist absichtlich strukturell isomorph zur
LLP-Realität — nur mit fiktivem Markennamen, um keine Markenrechte zu
berühren. Die Live-Inspektion (Stand 2026-05-19) hat verifiziert, dass
LLP heute **HubSpot (EU, Account 26317639) als zentrales CRM** betreibt.
Airtable, Make, Power BI, Streamlit und GCP sind im Live-DOM nicht
beobachtbar — sie kommen im Demo als **additive Operations-Schicht
parallel zu HubSpot** hinzu. Spalte 3 kategorisiert jede Komponente als
`Verifikation` (im Demo dasselbe wie bei LLP) oder `Erweiterung` (im Demo
zusätzlich gebaut).

| Love Life Passport (real) | MindForge Demo (Äquivalent) | Verhältnis zu LLP-Live-Stack |
|---|---|---|
| Quiz `analyse.lovelifepassport.com` (OnePage.io + HubSpot Forms) | `quiz-frontend/index.html` mit 9-Schritt-Quiz, Skip-Logic, Score | Erweiterung: portable Quiz-Variante; HubSpot-Forms-Pfad als E1.2 dokumentiert |
| HubSpot CRM mit Custom-Properties + Workflows | Phase E: HubSpot Free-Account mit denselben 12 Quiz-Properties + Workflow | Verifikation |
| CEO-Versprechen "persönliches Ergebnis" | Slack-Bot-Hot-Lead-Notification an Setter | Erweiterung |
| Quiz-Lead landet im CRM (HubSpot) | Make-Bridge synchronisiert HubSpot ↔ Airtable-`Leads`-Table | Erweiterung: Operations-DB zusätzlich zu HubSpot |
| Setter sieht priorisiert Hot-Leads | Lead-Scoring-Skript + Airtable-Interface "Triage" | Erweiterung |
| Setter ruft an / qualifiziert (Aircall) | Statusfeld + Notizen im Lead, manuell setzbar in Streamlit | Erweiterung |
| Termin mit Closer (vom Setter manuell vereinbart) | Streamlit-Setter-Daily-Tool bucht Termin im Google Calendar mit auto-generiertem Meet-Link, schreibt `call_at` + `meet_link` zurück nach Airtable | Erweiterung: Welle E2 (siehe `PHASE-E-PLAN.md` §3.5) |
| Closer macht Abschluss | Status `Converted` → Client-Record in Kunden-Table | Erweiterung |
| Mentor-Zuordnung im Inner Circle (400+ Kunden × 8 Mentoren) | Client → Program-Verknüpfung, Sessions pro Kunde | Erweiterung: M:N-Mentor-Allocation — in HubSpot strukturell nicht abbildbar |
| Programmumsätze tracken | Power BI Program-Revenue-Dashboard | Erweiterung: Cross-Source-Reporting über HubSpot + Airtable |
| Meta-Ads optimieren | Meta CAPI + Pixel-Deduplizierung | Verifikation: LLP betreibt 4 parallele Pixel; Demo zeigt das Pattern an einem |
| Operations sieht Systemstatus | UptimeRobot + Statuspage | Erweiterung |
| Mentoren-Team kommuniziert | Slack-Channel-Pings aus Make | Verifikation: Slack ist im DNS bestätigt (`slack-domain-verification`) |

Die Demo ist damit eine **portable, vollständig dokumentierte
Operations-Schicht**, die sich gegen ein bestehendes HubSpot-CRM
andocken lässt: HubSpot bleibt Marketing-/Sales-Source-of-Truth,
Airtable übernimmt Mentor-/Session-/Programm-Operations, Make
synchronisiert beide Richtungen, Power BI joint die Quellen für
Reporting, und Streamlit liefert das interne UI für CS- und
Mentoren-Workflows.

---

## 6. LLP-spezifische Erweiterungs-Ideen (nice-to-have)

Wenn das Demo noch enger an LLPs Realität rücken soll, lassen sich
folgende Erweiterungen als optionale **Phase E** ergänzen. Jede
einzelne ist eine direkte Antwort auf eine LLP-Eigenheit:

| # | Erweiterung | Adressiert |
|---|---|---|
| E1 | Mehrstufiges Quiz (Typeform / Tally / Eigenbau) statt einfaches Formular | `analyse.lovelifepassport.com` |
| E2 | Sales-Übergaben Leadhunter → Setter → Closer mit eigenen Views/Owner-Wechsel in Airtable | LLP-Org: 3 getrennte Sales-Rollen |
| E3 | Setter-Daily-Streamlit-Tool + Google-Calendar-Integration (Meet-Link automatisch) — bewusst kein Self-Service-Booking, weil LLP-Live-Inspektion verifiziert hat, dass kein Calendly/HubSpot-Meetings eingesetzt wird | `strategie.lovelifepassport.com` |
| E4 | Aircall-Integration: Call-Logs + Recording-Links im Lead | Aircall ist nachweislich im Stack |
| E5 | Mentor-Performance-Dashboard (NPS, Auslastung, Session-Anzahl, Kunden-Health) | Acht namentlich genannte Mentoren |
| E6 | Customer-Health-Score für Inner-Circle-Kunden (Engagement, letzte Session, Community-Aktivität) | 400+ aktive Mentoring-Kunden |
| E7 | Multi-Funnel-Tracking mit separaten Conversion-Events pro Subdomain | 7+ Subdomains mit eigenen Funnels |
| E8 | Slack-Bot für Mentor-Reminders ("Heute Call mit Kunde X um 14:00") | Wöchentliche Live-Calls + Mentor-Modell |
| E9 | Power-BI Row-Level-Security: jeder Mentor sieht nur eigene Kunden | Datenschutz + Mentor-Vielfalt |
| E10 | GA4 + Meta CAPI parallel, DSGVO-konformes Einwilligung-Setup | DACH-Markt + EU-Regulierung |
| E11 | Internes Streamlit-Tool "Setter Daily" mit priorisierter Call-Liste | 4 Sales-Rollen in der Stelle |
| E12 | Webhook-Endpoint für Stripe / Digistore24 → Customer-Success-Onboarding | High-Ticket-Payment-Provider |

Diese Erweiterungen sind im Demo bewusst **nicht** vorab umgesetzt —
sie sind dokumentierter Ausblick auf eine V2 der Pipeline.

---

## 7. Bekannte Limitierungen des Demos

| Limitierung | Mitigation / nächster Schritt |
|---|---|
| Demo nutzt ein eigenes Vanilla-JS-Quiz statt eines OnePage.io-Funnels | OnePage.io ist proprietär und nicht selbst hostbar; portable Vanilla-Variante deckt das Skip-Logic-Pattern ab |
| Power BI Desktop, nicht der Workspace-Deploy mit RLS | Phase E9 vorgesehen — RLS pro Mentor ist die nächste Stufe |
| Streamlit statt Retool | Streamlit ist portabler für eine offene Demo; Retool wäre eine vergleichbare Wahl mit 80 % Skill-Overlap |
| Keine Aircall-Integration produktiv | Aircall hat keinen Free-Tier; Click-to-Call-Stub ist als Phase-E-Idee dokumentiert |
| Daten sind synthetisch (20 Leads, 4 Kunden) | Schema ist auf 10.000+ Records ausgelegt; Skalierungsverhalten dokumentierbar |
| Kein TikTok/LinkedIn-Pixel | Meta-Pixel-Pattern lässt sich 1:1 auf andere Plattformen übertragen, bewusst nicht dupliziert |

---

## 8. Quellen

- [`www.lovelifepassport.com`](https://www.lovelifepassport.com/) — Hauptwebsite
- [`www.lovelifepassport.com/inner-circle`](https://www.lovelifepassport.com/inner-circle) — Inner Circle Programm
- [`analyse.lovelifepassport.com`](https://analyse.lovelifepassport.com/) — Quiz-Funnel
- [`strategie.lovelifepassport.com`](https://strategie.lovelifepassport.com/) — Strategiegespräch-Funnel
- [LLP Karriere-Portal](https://lovelifepassport.factorialhr.de/) — Quelle für Org-Struktur und Team-Größe
- [Crunchbase-Profil Tayler Schweigert](https://www.crunchbase.com/person/tayler-schweigert)
- [Crunchbase-Profil Love Life Passport](https://www.crunchbase.com/organization/love-life-passport)
- [Remote Rocketship — alle offenen Stellen](https://www.remoterocketship.com/company/lovelifepassport/)
- [CRM & Automation Manager Stelle](https://www.remoterocketship.com/company/lovelifepassport/jobs/crm-automation-manager-worldwide-remote/)
- [ProvenExpert Profil](https://www.provenexpert.com/en-us/lovelifepassport/)
- [Trustpilot Profil](https://www.trustpilot.com/review/www.lovelifepassport.com)

---

## 9. Phase-E-Status

Phase E (HubSpot-Bridge + Setter-Daily) ist **in Implementierung**. Der
vollständige Plan liegt in [`PHASE-E-PLAN.md`](PHASE-E-PLAN.md).
Aktueller Status:

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
- Vanilla-JS-Quiz mit Score-Engine, Skip-Logic, DSGVO-Einwilligung
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

