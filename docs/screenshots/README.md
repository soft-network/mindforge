# Screenshots

Build-Artefakte, die nicht direkt in der Versionskontrolle liegen sollen,
aber den Portfolio-Wert erhöhen.

## Power BI Dashboard

Die `.pbix`-Datei ist per `.gitignore` ausgeschlossen (groß, binär, kein
sinnvolles Diff). Nach Build des Dashboards in Power BI Desktop hier die
PNG-Exporte ablegen:

| Datei | Zeigt |
|---|---|
| `pbi-funnel.png` | Report 1 — Lead Funnel + KPI-Cards |
| `pbi-sources.png` | Report 2 — Source Performance + Heatmap |
| `pbi-programs.png` | Report 3 — Program Popularity & Revenue |

**Export aus Power BI:**

1. Report-Page in PBI Desktop öffnen
2. **File → Export → Export to PDF** (oder einzelne Pages als PNG via Screenshot-Tool)
3. Hier ablegen
4. In [`../../05-powerbi-dashboard.md`](../../05-powerbi-dashboard.md) verlinken

## Andere Screenshots

- `landing-page.png` — Hero + Form der Landing Page (für README)
- `streamlit-dashboard.png` — Dashboard-Seite der Coach-App
- `airtable-interface.png` — Lead Triage Interface aus [`../../06-airtable-interfaces.md`](../../06-airtable-interfaces.md)
- `statuspage.png` — Öffentliche Statuspage aus [`../../09-monitoring.md`](../../09-monitoring.md)

→ Alle als PNG, max. 1600px Breite (für Github-Rendering optimal).
