# Schritt 2 — Airtable Schema aufsetzen

**Ziel:** 4 verlinkte Tabellen mit Lookups und Rollups, die das Coaching-Geschäft abbilden.

**Base umbenennen:** Klicke oben links auf "Untitled Base" → Rename → `MindForge CRM`

---

## Tabelle 1: `Programs`

Das sind die Kurse/Coachings, die MindForge anbietet. **Diese Tabelle zuerst erstellen**, weil Leads darauf verlinken.

| Feldname | Typ | Optionen / Formel |
|---|---|---|
| `Name` | Single line text | Primary field |
| `Category` | Single select | Career, Life, Health, Business |
| `Price (EUR)` | Currency | EUR, 2 decimals |
| `Duration (Weeks)` | Number | Integer |
| `Description` | Long text | – |
| `Leads` | Link to `Leads` | (wird automatisch erstellt nach Tabelle 2) |
| `Lead Count` | Count | Counts `Leads` |
| `Converted Clients` | Count | Counts `Clients` (nach Tabelle 4) |
| `Conversion Rate` | Formula | `IF({Lead Count}=0, 0, {Converted Clients}/{Lead Count})` — Format: Percent |

### Sample-Daten für `Programs`

Lass die Tabelle erstmal leer — wir importieren später per CSV.

---

## Tabelle 2: `Leads`

Hier landen alle Webhook-Submissions vom Landing-Page-Formular.

| Feldname | Typ | Optionen / Formel |
|---|---|---|
| `Name` | Single line text | Primary field |
| `Email` | Email | – |
| `Phone` | Phone number | – |
| `Source` | Single select | Google Ads, Facebook, Instagram, Referral, Organic, Other |
| `Interest` | Link to `Programs` | Single record |
| `Created` | Created time | Auto |
| `Lead Score` | Number | Integer, 0-100. Wird vom Script gesetzt. |
| `Status` | Single select | New, Qualified, Contacted, Converted, Lost |
| `Program Price` | Lookup | Lookup `Price (EUR)` aus `Interest` |
| `Notes` | Long text | – |

### Wichtig
- `Lead Score` bleibt manuell editierbar, wird aber vom Script automatisch berechnet.
- `Status` standardmäßig: New.

---

## Tabelle 3: `Sessions`

Discovery Calls / Beratungstermine pro Lead.

| Feldname | Typ | Optionen / Formel |
|---|---|---|
| `Session ID` | Autonumber | Primary field |
| `Lead` | Link to `Leads` | Single record |
| `Date` | Date with time | – |
| `Outcome` | Single select | No Show, Not Interested, Interested, Booked |
| `Lead Name` | Lookup | Lookup `Name` aus `Lead` |
| `Notes` | Long text | – |

---

## Tabelle 4: `Clients`

Konvertierte Leads (zahlende Kunden).

| Feldname | Typ | Optionen / Formel |
|---|---|---|
| `Client ID` | Autonumber | Primary field |
| `Lead` | Link to `Leads` | Single record |
| `Program` | Link to `Programs` | Single record |
| `Start Date` | Date | – |
| `MRR (EUR)` | Currency | EUR |
| `Status` | Single select | Active, Cancelled, Completed |
| `Client Name` | Lookup | Lookup `Name` aus `Lead` |
| `Program Name` | Lookup | Lookup `Name` aus `Program` |

---

## Verknüpfungen — visuell

```
Programs ◄────────── Leads ◄────────── Sessions
   ▲                    ▲
   │                    │
   └──── Clients ───────┘
```

- 1 Lead → max. 1 Interest (Program)
- 1 Lead → viele Sessions
- 1 Lead → max. 1 Client (nach Konvertierung)
- 1 Program → viele Leads, viele Clients

---

## Interface bauen

Nach Schema-Anlage:

1. Klick oben rechts auf **Interfaces** → **Start building**
2. Wähle Layout: **Record Review**
3. Source Table: `Leads`
4. Filter: `Status = "New"`
5. Felder anzeigen: Name, Email, Phone, Source, Interest, Lead Score, Status

→ Das Sales-Team öffnet das Interface, sieht alle neuen Leads und kann sie nacheinander durchgehen.

---

## Was das Schema demonstriert

| Eigenschaft | Umsetzung |
|---|---|
| Komplexe Datenmodelle (Links, Lookups, Rollups) | 4 Tabellen, 3 Links, 4 Lookups, 1 Formula-Rollup |
| Interfaces | Lead-Review-Interface |
| Sauberes Datenmanagement | Single-Selects statt Freitext, Phone-Validation |

---

## Zeitaufwand: ~45 Minuten

**Nächster Schritt:** [03-airtable-script.md](03-airtable-script.md) — JS-Script für Lead Scoring
