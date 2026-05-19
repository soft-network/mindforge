# Schritt 3 — Airtable Scripting App einrichten (optional)

> **Hinweis:** Seit dem Python-Refactor liegt die Produktiv-Scoring-Logik in
> [gcp/cloud-function-score/main.py](gcp/cloud-function-score/main.py) und
> wird automatisch von Make nach jedem Lead-Create aufgerufen — Setup siehe
> [08-gcp-deployment.md](08-gcp-deployment.md) und Aufruf in
> [04-make-scenario.md](04-make-scenario.md). Dieser Schritt ist **optional**
> und installiert das ursprüngliche JS-Script als manuelles Re-Scoring-Tool
> direkt in Airtable. Die Score-Logik beider Varianten ist identisch.

**Ziel:** Ein JavaScript-Script in Airtable, das einen Lead-Score berechnet und den Lead-Status setzt.

---

## Was das Script kann

Berechnet einen Score (0-100) basierend auf:

| Kriterium | Max Punkte | Logik |
|---|---|---|
| Source | 30 | Referral=30, Organic=25, Google Ads=20, FB=15, IG=12, Other=5 |
| Programm-Preis | 30 | Premium-Programme = höherer Intent (linear bis 5000 EUR) |
| Phone vorhanden | 15 | Telefonnummer angegeben |
| Notes vorhanden | 5 | Mehr als 20 Zeichen Notiz |
| Recency | 20 | <24h=20, <72h=10, <168h=5, älter=0 |

Wenn Score ≥ 70 → Status wird automatisch auf "Qualified" gesetzt → Hot Lead.

---

## Einbau in Airtable

1. In Airtable: Öffne die Base `MindForge CRM`
2. Klicke oben **Extensions** → **Add an extension** → **Scripting**
3. Benenne es: `Lead Scoring`
4. Lösche den Beispiel-Code
5. Kopiere den kompletten Inhalt aus [airtable-scripts/lead-scoring.js](airtable-scripts/lead-scoring.js) hinein
6. Klick **Save**

## Testen

1. Klick **Run** im Script-Panel
2. Wähle einen Lead aus der Dropdown
3. Es erscheint eine Punkte-Tabelle und ein Bestätigungs-Button
4. Klick **Ja, speichern** → der Score wird ins Feld geschrieben

---

## Technische Notizen

Das Lead-Scoring-Script läuft direkt in der Airtable Scripting API mit der nativen
`input`/`output`-Library. Es nutzt async-Operationen für Cross-Table-Lookups
(Programs), gewichtete Source-Bewertung und Status-Update via `updateRecordAsync`.
Der Score wird transparent als Tabelle visualisiert, damit das Sales-Team die
Logik nachvollziehen kann.

| Technik | Im Script |
|---|---|
| JavaScript ES2020+ | Komplettes File |
| Cross-Table Lookup | Leads → Programs via `selectRecordAsync` |
| Async/Await | Saubere asynchrone API-Calls |
| Interactive Input | `input.recordAsync`, `input.buttonsAsync` |
| Strukturiertes UI | Tabellen-Output, Bestätigungs-Dialog |

---

## Zeitaufwand: ~30 Minuten (Einbau + Test)

**Nächster Schritt:** [04-make-scenario.md](04-make-scenario.md) — Webhook-Pipeline
