# Schritt 6 — Airtable Interfaces einrichten

**Ziel:** Ein klick-und-fertiges UI direkt in Airtable, mit dem das Sales-Team
neue Leads schnell triagieren kann — ohne separates Frontend.

**Warum hier und nicht nur im Streamlit-Dashboard:** Airtable Interfaces sind in
5–10 Min. gebaut, brauchen kein Deployment und sind perfekt für das *operative*
Lead-Handling (durchklicken, Status setzen, Notizen ergänzen). Die Streamlit-App in
[07-streamlit-admin.md](07-streamlit-admin.md) ergänzt das um Analytics-Sicht
und KPIs, ist aber nicht für die tägliche Sales-Routine optimiert.

---

## Interface 1: Lead Triage

Zweck: Sales öffnet morgens das Interface, sieht alle neuen Leads sortiert nach
Score, klickt sich durch und entscheidet → Qualified / Contacted / Lost.

### Bau-Schritte

1. In Airtable: oben rechts auf **Interfaces** → **Start building**
2. Layout: **Record Review**
3. Source Table: `Leads`
4. **Filter:** `Status = "New"` **OR** `Status = "Qualified"`
5. **Sort:** `Lead Score` absteigend (Hot Leads zuerst)
6. Sichtbare Felder im Preview:
   - Name, E-Mail, Telefon
   - Source, Interesse (Programm)
   - Lead Score (mit Color-Coding via Conditional Formatting)
   - Notizen
   - Status (editierbar)
7. **Action Buttons** hinzufügen:
   - "Qualifizieren" → setzt Status = Qualified
   - "Kontaktiert" → setzt Status = Contacted
   - "Verloren" → setzt Status = Lost

→ Interface speichern als **Lead Triage**.

---

## Interface 2: Pipeline Overview (optional)

Zweck: KPI-Übersicht für den Coach selbst — was steht aktuell in der Pipeline?

### Bau-Schritte

1. **+ New Page** → Layout: **Dashboard**
2. Number-Widgets oben:
   - "Neue Leads diese Woche" — Filter: `Erstellt am` letzten 7 Tage
   - "Hot Leads offen" — Filter: `Lead Score >= 70 AND Status IN (New, Qualified)`
   - "Conversion Rate" — via Rollup-Formel
3. Chart-Widget:
   - Bar Chart: Leads grouped by Source, Value = Count
4. Record-List-Widget:
   - Leads-Tabelle, Filter: `Status = Qualified`, Sort: `Lead Score` desc

→ Interface speichern als **Pipeline Overview**.

---

## Zugriff für Coaches

1. Im Interface-Builder oben rechts: **Share Interface**
2. **Add collaborators:** Coach-Emails einladen
3. **Permission:** Read + Comment + Edit (für Status-Updates)

→ Coaches loggen sich mit ihrer Airtable-E-Mail ein und sehen nur das Interface,
nicht die Roh-Tabellen.

---

## Vergleich mit Streamlit-App

| Aspekt | Airtable Interface | Streamlit App ([07](07-streamlit-admin.md)) |
|---|---|---|
| Setup-Zeit | 5–10 Min | ~5 h |
| Hosting | Airtable (inklusive) | Streamlit Cloud / GCP Cloud Run |
| Auth | Airtable-Account | Passwort-Gate / OAuth |
| Edit-Operations | Native, direkt aufs Record | API via pyairtable |
| Custom Charts | Eingeschränkt | Plotly (frei) |
| Filter-Logik | UI-basiert | Beliebig in Python |
| Use-Case | Daily Sales Triage | Manager-Übersicht + Analytics |

→ Beide ergänzen sich: Airtable Interface = täglicher Sales-Workflow,
Streamlit = Reporting und Multi-View-Analyse für die Coach-Leitung.

---

## Technische Eigenschaften

| Aspekt | Umsetzung |
|---|---|
| Low-Code UI | Airtable Interface Designer |
| Filtered Views | Native Airtable-Filter + Sort |
| Action-Buttons | Status-Updates ohne Custom Code |
| Access Control | Airtable-Workspace-Permissions |

---

## Zeitaufwand: ~30 Minuten (beide Interfaces zusammen)

**Nächster Schritt:** [07-streamlit-admin.md](07-streamlit-admin.md) — Streamlit Coach Dashboard
