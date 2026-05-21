# Airtable Schema — Phase-E-Erweiterung

Erweitert das Phase-1-Schema (4 Tabellen Programme/Leads/Sessions/Kunden) um die
Phase-E-Bedürfnisse: Quiz-Antworten als strukturierte Felder + Mentor-Tabelle
+ HubSpot-Sync-Felder + Conflict-Resolution-Metadaten.

> **Voraussetzung:** Phase-1-Schema aus [`02-airtable-schema.md`](02-airtable-schema.md) ist angelegt.

---

## Schritt 1 — `Leads`-Tabelle erweitern

Öffne die Base `MindForge CRM` → Tabelle `Leads` → **+** (neues Feld) für jedes
unten gelistete Feld. Die Phase-1-Felder bleiben unverändert.

### 1a. Kontakt-Felder (Quiz-Submit liefert First/Last separat)

| Feldname | Typ | Optionen |
|---|---|---|
| `Vorname` | Single line text | – |
| `Nachname` | Single line text | – |
| `Land` | Single select | `DE` · `AT` · `CH` · `OTHER` |
| `Einwilligung` | Checkbox | – |

*(Das bestehende `Name`-Feld bleibt als Primary Field. Make füllt es als
`{Vorname} {Nachname}` beim Insert.)*

### 1b. Die 12 Quiz-Properties (eins zu eins zu HubSpot)

| Feldname | Typ | Optionen |
|---|---|---|
| `Quiz · Selbstständig` | Single select | `ja` · `nein` |
| `Quiz · Dauer Selbstständigkeit` | Single select | `lt_1` · `1_3` · `gt_3` |
| `Quiz · Branche` | Single select | `coach` · `services` · `digital` · `ecommerce` · `network` · `other` |
| `Quiz · Sichtbarkeit` | Single select | `lt_1k` · `lt_10k` · `gt_10k` |
| `Quiz · Team` | Single select | `solo` · `lt_10` · `gt_10` |
| `Quiz · Monatsumsatz` | Single select | `zero` · `lt_5k` · `lt_10k` · `lt_100k` · `gt_100k` |
| `Quiz · Hauptwunsch` | Single select | `stable` · `quit_job` · `brand` · `freedom` · `5fig` |
| `Quiz · Lücke` | Multiple select | `reach` · `portfolio` · `sales` · `clone` · `mindset` |
| `Quiz · Zeitbudget` | Single select | `lt_1h` · `2_5h` · `5_10h` · `gt_10h` |
| `Quiz Score` | Number (Integer, 0–100) | *Achtung: Phase 1 hatte schon `Lead Score`. Wir nutzen das alte Feld weiter — kein neues Feld, sondern Phase-1-`Lead Score` umbenennen zu `Quiz Score`.* |
| `Quiz Tier` | Single select | `hot` · `warm` · `cold` · `unqualified` |
| `Quiz Abgeschlossen am` | Date (include time) | Europe/Berlin ISO |

### 1c. Tracking / Identity / Meta

| Feldname | Typ | Optionen |
|---|---|---|
| `Source Subdomain` | Single line text | z. B. `quiz.mindforge.demo` |
| `Event ID` | Single line text | UUID, dient als Idempotency-Key |
| `UTM Source` | Single line text | – |
| `UTM Medium` | Single line text | – |
| `UTM Campaign` | Single line text | – |

### 1d. HubSpot-Sync-Felder (Source-of-Truth: HubSpot)

| Feldname | Typ | Optionen |
|---|---|---|
| `Lifecycle Stage` | Single select | `lead` · `marketingqualifiedlead` · `salesqualifiedlead` · `opportunity` · `customer` · `evangelist` · `other` |
| `Lead Status` | Single select | `NEW` · `OPEN` · `IN_PROGRESS` · `OPEN_DEAL` · `UNQUALIFIED` · `CONNECTED` · `BAD_TIMING` |
| `HubSpot Owner` | Single line text | HubSpot Owner-ID |
| `HubSpot Contact ID` | Single line text | für Rück-Sync |
| `HS Zuletzt geändert` | Date (include time) | für Conflict-Resolution (Last-Wins) |

### 1e. Conflict-Resolution-Meta

| Feldname | Typ | Optionen |
|---|---|---|
| `_source` | Single line text | `quiz` · `hubspot-workflow` · `airtable-automation` — verhindert Sync-Loops |

---

## Schritt 2 — Phase-1-Feld umbenennen

Auf der `Leads`-Tabelle:

1. Rechtsklick auf `Lead Score` → **Edit field** → Name ändern zu `Quiz Score`.
   (Vorhandene Daten bleiben erhalten, das Phase-1-Script aus `03-airtable-script.md`
   schreibt weiterhin in dasselbe Feld — kein Bruch.)

Das `Status`-Feld aus Phase 1 wird durch das neue `Lifecycle Stage` ersetzt:

2. Behalte `Status` für Phase-1-Kompatibilität, aber:
   - Make-Szenario schreibt sowohl `Status` (Mapping: lead→New, mql→Qualified, sql→Contacted, customer→Converted, lost→Lost) **als auch** das neue `Lifecycle Stage`.
   - Für Phase E gilt `Lifecycle Stage` als SoT. `Status` wird nur synchron gehalten, damit das Phase-1-Interface aus `06-airtable-interfaces.md` weiterhin funktioniert.

---

## Schritt 3 — Neue Tabelle `Mentoren`

Erstellen über **+ Add or import** → **Create empty table** → Name: `Mentoren`.

| Feldname | Typ | Optionen |
|---|---|---|
| `Name` | Single line text | Primary field |
| `E-Mail` | E-Mail | – |
| `Stadt` | Single line text | – |
| `Kapazität pro Woche` | Number (Integer) | Soll-Sessions pro Woche (z. B. 10) |
| `Spezialisierung` | Multiple select | `Business` · `Sales` · `Mindset` · `Marketing` · `Operations` · `Finance` |
| `Status` | Single select | `Active` · `Inactive` · `On Leave` |
| `Sessions` | Link to `Sessions` | (wird in Schritt 4 verlinkt) |
| `Aktive Kunden` | Count | Counts linked `Kunden` (nach Schritt 5 verlinkt) |
| `Avg NPS` | Rollup | `AVERAGE({Sessions::NPS})` |

Sample-Daten (manuell anlegen, 8 Datensätze, frei nach LLP-Vorbild):

| Name | Stadt | Capacity | Spezialisierung |
|---|---|---|---|
| Bea Vogt | Stuttgart | 12 | Business, Sales |
| Finn Weiner | Berlin | 10 | Marketing |
| Jonas Spießbach | Hamburg | 10 | Operations |
| Sam Guezel | München | 12 | Mindset |
| Oguzhan Ünal | Köln | 8 | Sales |
| Tina Eckert | Frankfurt | 10 | Business |
| Mischa Dieterle | Düsseldorf | 8 | Marketing |
| Jimmy Künzli | Zürich | 10 | Finance |

---

## Schritt 4 — `Sessions`-Tabelle erweitern

Auf der bestehenden `Sessions`-Tabelle die folgenden Felder ergänzen:

| Feldname | Typ | Optionen |
|---|---|---|
| `Mentor` | Link to `Mentoren` | Single record |
| `Mentor Name` | Lookup | `Name` aus `Mentor` |
| `Dauer (min)` | Number | Integer |
| `NPS` | Number (Integer, 0–10) | NPS-Score vom Kunden |
| `Aufnahme-URL` | URL | – |

---

## Schritt 5 — `Kunden`-Tabelle erweitern

Auf der bestehenden `Kunden`-Tabelle die folgenden Felder ergänzen:

| Feldname | Typ | Optionen |
|---|---|---|
| `Mentor` | Link to `Mentoren` | Single record |
| `Onboarding Status` | Single select | `Pending` · `Welcome Pack Sent` · `Onboarding Call Done` · `Activated` |
| `Letzte Session` | Rollup | `MAX(values)` aus `Sessions::Date` (über Lead → Sessions) |
| `LTV` | Currency (EUR) | manuelle Summe der MRR über Monate, oder Formula: `{MRR (EUR)} * Months Since Start` |
| `Customer Health Score` | Formula | siehe unten |

**Customer Health Score Formula:**

```
SWITCH(
  TRUE(),
  DATETIME_DIFF(NOW(), {Letzte Session}, 'days') <= 7,  100,
  DATETIME_DIFF(NOW(), {Letzte Session}, 'days') <= 14, 75,
  DATETIME_DIFF(NOW(), {Letzte Session}, 'days') <= 30, 50,
  DATETIME_DIFF(NOW(), {Letzte Session}, 'days') <= 60, 25,
  0
)
```

---

## Schritt 6 — `Mentoren`-Tabelle mit `Sessions` verlinken

Nachdem `Sessions` das Feld `Mentor` (Link to Mentoren) bekommen hat, erscheint
auf der `Mentoren`-Tabelle automatisch das Feld `Sessions` (Reverse-Link). Die
Rollups `Aktive Kunden` und `Avg NPS` aus Schritt 3 funktionieren erst
nach dieser Verlinkung.

---

## Schritt 7 — Interface „Mentor Dashboard" (optional, Phase-E-Polish)

Unter **Interfaces → Start building → Dashboard**:

- Source Table: `Mentoren`
- Widgets:
  - List: Mentoren mit Filter `Status = Active`, sortiert nach `Avg NPS desc`
  - Chart: `Kapazität pro Woche` vs. `Sessions Count (this week)` als Bar Chart
  - Number: `SUM({Aktive Kunden})` als KPI „Aktiv betreute Kunden"

---

## Ergebnis

Nach Schritt 1–7 ist die Airtable-Base bereit für:
- Quiz-Submits (Make-Szenario #1 schreibt alle 12 Properties)
- Bidirektionale Sync mit HubSpot (Szenarien #2 + #3)
- Mentor-Performance-Reports in Power BI

---

## Zeitaufwand

| Schritt | Zeit |
|---|---|
| 1a–1e | 25 min (~24 neue Felder, je 30–60s) |
| 2 (Umbenennung) | 1 min |
| 3 (Mentoren-Tabelle + Sample-Daten) | 10 min |
| 4–5 (Sessions + Kunden erweitern) | 10 min |
| 6 (Verlinkung Check) | 2 min |
| 7 (Mentor-Dashboard Interface) | 10 min optional |
| **Gesamt** | **~50 min** |

---

## Nächster Schritt

Nach Airtable-Erweiterung → [`hubspot/README.md`](hubspot/README.md) §2 (Custom Properties in HubSpot anlegen).
