# Schritt 5 — Power BI Dashboard

**Ziel:** 3 Reports mit DAX-Measures, verbunden mit Airtable.

**Schwerpunkt:** Funnel-Analyse mit selbstgeschriebenen DAX-Measures.

---

## Datenanbindung Airtable → Power BI

Power BI hat keinen nativen Airtable-Connector. Zwei Optionen:

### Option A (empfohlen für Demo): CSV Export
1. In Airtable: Jede Tabelle einmal als CSV exportieren (View → Download CSV)
2. Speichere als `Leads.csv`, `Programs.csv`, `Sessions.csv`, `Clients.csv` in `C:\Users\msi\analyse\demo\sample-data\`
3. In Power BI: **Get Data → Text/CSV** → alle 4 importieren

### Option B (für echte Anwendung): Airtable Web API
1. In Power BI: **Get Data → Web** → Advanced
2. URL: `https://api.airtable.com/v0/<BASE_ID>/Leads`
3. HTTP Header: `Authorization: Bearer <YOUR_TOKEN>`
4. Wiederhole für alle Tabellen, **Json-Response per Power Query parsen**

→ Für die Erstinbetriebnahme: Option A nehmen. Option B ist die Produktions-Variante.

---

## Beziehungen anlegen (Model View)

Im Modell-View die Verknüpfungen ziehen:

| Von | Nach | Cardinality |
|---|---|---|
| `Leads[Interest]` | `Programs[Name]` | many-to-one |
| `Sessions[Lead]` | `Leads[Name]` | many-to-one |
| `Clients[Lead]` | `Leads[Name]` | one-to-one |
| `Clients[Program]` | `Programs[Name]` | many-to-one |

---

## DAX Measures

Erstelle eine neue Tabelle namens `Measures` (über **Enter data** mit nur einer Dummy-Spalte) und füge folgende Measures hinzu:

```dax
Total Leads = COUNTROWS(Leads)

Qualified Leads =
CALCULATE(
    COUNTROWS(Leads),
    Leads[Status] IN { "Qualified", "Contacted", "Converted" }
)

Converted Leads =
CALCULATE(
    COUNTROWS(Leads),
    Leads[Status] = "Converted"
)

Lead-to-Qualified Rate =
DIVIDE([Qualified Leads], [Total Leads], 0)

Qualified-to-Converted Rate =
DIVIDE([Converted Leads], [Qualified Leads], 0)

Overall Conversion Rate =
DIVIDE([Converted Leads], [Total Leads], 0)

Avg Lead Score = AVERAGE(Leads[Lead Score])

Total MRR = SUM(Clients[MRR (EUR)])

Avg Revenue Per Lead =
DIVIDE([Total MRR], [Total Leads], 0)

Avg Days to Convert =
AVERAGEX(
    FILTER(Clients, NOT(ISBLANK(Clients[Start Date]))),
    DATEDIFF(
        RELATED(Leads[Created]),
        Clients[Start Date],
        DAY
    )
)
```

---

## Report 1: Lead Funnel

Zweck: zeigt Trichter von Lead → Qualified → Converted.

- **Visual:** "Funnel chart"
- **Daten:**
  - Group: `Status` (Custom order: New, Qualified, Contacted, Converted)
  - Values: `Total Leads`
- **Cards oben:**
  - Total Leads
  - Lead-to-Qualified Rate
  - Overall Conversion Rate
  - Avg Days to Convert

## Report 2: Source Performance

Zweck: welche Marketing-Kanäle bringen die besten Leads?

- **Visual 1:** Clustered Column Chart
  - X-Axis: `Source`
  - Y-Axis: `Total Leads`, `Converted Leads`
- **Visual 2:** Matrix
  - Rows: `Source`
  - Values: `Total Leads`, `Overall Conversion Rate`, `Avg Lead Score`, `Avg Revenue Per Lead`
- **Sortierung:** Nach Conversion Rate absteigend
- **Conditional Formatting:** Conversion Rate als Heatmap (rot < 5%, grün > 20%)

## Report 3: Program Popularity & Revenue

Zweck: welche Programme verdienen Geld, welche nur Aufmerksamkeit?

- **Visual 1:** Scatter Plot
  - X-Axis: Lead Count (per Program)
  - Y-Axis: Conversion Rate
  - Bubble Size: Total MRR
  - Legend: Category
- **Visual 2:** Bar Chart
  - Programs by Total MRR (Top 5)
- **Slicer:** Category (Career, Life, Health, Business)

---

## Themes & Polish

- **Theme:** View → Themes → wähle "Innovate" oder erstelle eigenes
- **Title pro Page:** Groß, fett, links oben
- **Logo:** MindForge-Logo als PNG einfügen (z.B. via DALL-E generieren oder einfaches Text-Logo)
- **Tooltip:** Hover-Info mit Lead-Liste pro Source

---

## Datei speichern

`mindforge-dashboard.pbix` im `demo/` Ordner ablegen.

> Die `.pbix`-Datei ist gitignored (binär, groß, kein sinnvolles Diff).
> Für Portfolio-Zwecke statt der Datei **PNG-Exports** der drei Report-Pages
> in [`docs/screenshots/`](docs/screenshots/) ablegen und von dort verlinken.

---

## Technische Eigenschaften

| Aspekt | Umsetzung |
|---|---|
| Power BI Dashboards | 3 Reports |
| Data Modeling | Beziehungen zwischen 4 Tabellen |
| DAX | 10 Measures (inkl. CALCULATE, AVERAGEX, DATEDIFF) |
| Reporting | KPI Cards, Funnel, Heatmap |

---

## Zeitaufwand: ~3 Stunden

**Nächster Schritt:** [09-monitoring.md](09-monitoring.md) — UptimeRobot + Statuspage
