# Phase E — Master-Plan (Reihenfolge · Abhängigkeiten · Wer macht was)

**Zweck dieses Dokuments:** High-Level-Steuerung über alle Wellen von
Phase E. Die ausführlichen Schritt-für-Schritt-Anweisungen pro Welle
liegen in [`PHASE-E-PLAN.md`](PHASE-E-PLAN.md), [`hubspot/`](hubspot/),
[`make-bridge/`](make-bridge/), [`tracking-full/`](tracking-full/),
[`powerbi-cross-source/`](powerbi-cross-source/) und
[`02b-airtable-phase-e-extension.md`](02b-airtable-phase-e-extension.md).

Hier wird **nur** geplant — nichts wird in diesem Dokument implementiert.

---

## 1. Status-Snapshot (Stand 2026-05-20)

**Update:** Accounts sind bereits erstellt, IDs liegen in `.env`.
Damit ist der Account-Setup-Sprint **abgeschlossen** — offen sind nur
noch UI-Konfiguration (Properties anlegen, Szenarien zusammenklicken,
Tags konfigurieren) und Live-Tests.

| Welle | Code im Repo | Doku im Repo | Account | Konfig (UI) | Live getestet |
|---|---|---|---|---|---|
| **E1.1** Quiz-Frontend (9 Schritte + Skip-Logic) | ✅ fertig | ✅ fertig | – | – | ⏳ pending |
| **E1.2** HubSpot Free CRM (Properties + Workflow) | ⚙️ JSON-Import | ✅ fertig | ✅ existiert | ⏳ Properties + Workflow anlegen | ⏳ pending |
| **E1.3** Make-Bridge (3 Szenarien) | ⚙️ Sample-Payloads | ✅ fertig | ✅ existiert | ⏳ 3 Szenarien klicken | ⏳ pending |
| **E1.4** Power BI Cross-Source (HubSpot + Airtable) | ⚙️ DAX-Snippets | ✅ fertig | – (PBI Desktop, lokal) | ⏳ Connections + DAX + Reports bauen | ⏳ pending |
| **E2** Setter-Daily Streamlit + Google Calendar | ❌ noch zu bauen | ✅ fertig | ✅ GCP + Workspace-Trial | ⏳ Service-Account-JSON in secrets.toml | ⏳ pending |
| **Quer-Welle** Tracking-Stack (GTM + 4 Pixel + CAPI) | ⚙️ Bootstrap-JS | ✅ fertig | ✅ Meta + GA4 + GTM + TikTok | ⏳ GTM-Tags konfigurieren | ⏳ pending |
| **Airtable-Schema-Erweiterung** | ⚙️ Setup-Script + Doku | ✅ fertig | ✅ existiert | ⏳ Script ausführen | ⏳ pending |

Legende:
- ✅ fertig / existiert: lauffähig, vollständig dokumentiert oder Account vorhanden
- ⚙️ Snippets: Code-Templates oder Daten-Strukturen da, aber kein lauffähiges Modul (z.B. Claude muss noch E2-Streamlit-Page bauen, DAX-Snippets müssen in eine .pbix-Datei integriert werden)
- ⏳ pending: UI-Klick-Konfiguration oder Live-Test offen

---

## 2. Wellen-Topologie (Abhängigkeits-Graph)

```
                          ┌─────────────────────────┐
                          │   Account-Setup-Sprint  │  ← User · ~1h
                          │ HubSpot · Make · GCP ·  │
                          │ Google Workspace · Meta │
                          │ GA4 · GTM · TikTok      │
                          └────────────┬────────────┘
                                       │
                                       ▼
                          ┌─────────────────────────┐
                          │ Airtable-Schema erweitern│  ← User-Script · ~1min run
                          │ (E1.2 + E2-Felder)      │     (Claude: Doku done)
                          └────────────┬────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
   ┌──────────────────┐    ┌──────────────────────┐    ┌──────────────────┐
   │ E1.2 HubSpot     │    │ E1.1 Quiz-Frontend   │    │ Quer-Welle GTM   │
   │ Properties +     │    │ lokal testen         │    │ Container + 4    │
   │ Workflow         │    │                      │    │ Pixel + Bootstrap│
   │ ~30min User      │    │ ~30min User          │    │ ~90min User      │
   └────────┬─────────┘    └──────────┬───────────┘    └────────┬─────────┘
            │                         │                         │
            └─────────────────────────┼─────────────────────────┘
                                      ▼
                          ┌─────────────────────────┐
                          │ E1.3a Make-Szenario #1  │
                          │ Quiz Submit → HubSpot + │
                          │ Airtable + Pixels       │
                          │ ~60min User             │
                          └────────────┬────────────┘
                                       │
                                       ▼
                          ┌─────────────────────────┐
                          │ End-to-End-Test V1      │  Demo zeigt:
                          │ Quiz-Submit fließt      │  Submit → HubSpot +
                          │ (Hauptmeilenstein)      │  Airtable + Slack
                          └────────────┬────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
   ┌──────────────────┐    ┌──────────────────────┐    ┌──────────────────┐
   │ E1.3b/c Bidi-    │    │ E2 Setter-Daily      │    │ E1.4 Power BI    │
   │ Sync Szenarien   │    │ (Claude: Code-Bau)   │    │ Cross-Source     │
   │ ~60min User      │    │ ~3h Claude           │    │ ~90min User      │
   │                  │    │ → dann User-Setup    │    │                  │
   │                  │    │   GCP + 25min Test   │    │                  │
   └──────────────────┘    └──────────────────────┘    └──────────────────┘
                                       │
                                       ▼
                          ┌─────────────────────────┐
                          │ End-to-End-Test V2      │  Demo zeigt:
                          │                         │  Submit → CRM →
                          └─────────────────────────┘  Setter-Daily →
                                                       Termin-Buchung →
                                                       Cross-Source-PBI
```

**Kritischer Pfad:**
`Account-Sprint → Airtable-Schema → E1.2 → E1.3a → End-to-End-Test V1`

Alles danach (E1.3b/c, E2, E1.4) ist parallelisierbar.

---

## 3. Was Claude macht vs. was User macht

### Claude-Aktionen (Code- und Doku-Lieferungen)

| Aktion | Status | Aufwand |
|---|---|---|
| Quiz-Frontend Vanilla-JS (9 Schritte, Skip-Logic, Score) | ✅ fertig | ~3h |
| HubSpot Properties als JSON-Import-Datei | ✅ fertig | – |
| HubSpot Workflow-Design-Doku | ✅ fertig | – |
| Make-Szenario-Specs (3 Stück) mit Sample-Payloads | ✅ fertig | – |
| Field-Mapping-Matrix HubSpot ↔ Airtable | ✅ fertig | – |
| GTM-Container-Doku + Bootstrap-JS | ✅ fertig | – |
| CAPI Server-Side-Snippets für Meta, GA4 MP, TikTok | ✅ fertig | – |
| Power BI DAX-Maße + Cross-Source-Datenmodell-Doku | ✅ fertig | – |
| Airtable Setup-Skript für E1-Schema + Mentoren-Tabelle | ✅ fertig | – |
| **E2 Streamlit-Code (integrations/, pages/2_Setter_Daily.py)** | ❌ noch zu bauen | ~3-4h |
| **Airtable Setup-Skript um E2-Felder erweitern** | ❌ noch zu bauen | ~10min |

### User-Aktionen (Account-Setup + UI-Klicks)

| Aktion | Welle | Aufwand |
|---|---|---|
| HubSpot Free Account anlegen, EU-Region wählen | E1.2 | 10min |
| HubSpot 12 Custom Properties (via JSON-Import oder UI) | E1.2 | 10min |
| HubSpot Workflow konfigurieren | E1.2 | 10min |
| Make.com Account + Workspace anlegen | E1.3 | 5min |
| Make-Szenario #1 (Quiz Submit) zusammenklicken | E1.3a | 60min |
| Make-Szenario #2 (HubSpot → Airtable) zusammenklicken | E1.3b | 30min |
| Make-Szenario #3 (Airtable → HubSpot) zusammenklicken | E1.3c | 30min |
| Meta Business Manager + Pixel + Test Event Code | Quer | 15min |
| GA4 Property + 2 Streams anlegen | Quer | 10min |
| GTM Container anlegen | Quer | 5min |
| TikTok Business Account + Pixel | Quer | 10min |
| GTM Tags konfigurieren (4 Pixel + Triggers) | Quer | 45min |
| GCP Projekt + Calendar API enabled + Service Account JSON | E2 | 10min |
| Google Workspace Domain-wide Delegation aktivieren | E2 | 5min |
| `python scripts/setup_airtable_phase_e.py` ausführen | Airtable | 1min |
| Quiz-Frontend lokal testen (npm-frei, file://) | E1.1 | 30min |
| Streamlit-Setter-Daily lokal starten (`streamlit run app.py`) | E2 | 5min |
| Test-Booking + Calendar-Event verifizieren | E2 | 15min |
| Power BI Desktop installieren | E1.4 | 5min |
| HubSpot + Airtable REST-Connections in PBI konfigurieren | E1.4 | 20min |
| DAX-Maße aus Doku einfügen + 4 Reports bauen | E1.4 | 60min |
| End-to-End-Test (Submit → Pipeline → PBI) | – | 30min |

---

## 4. Empfohlene Reihenfolge nach Zeitbudget

### Wenn du **2 Stunden** Zeit hast (1 Abend)
- Airtable-Schema-Erweiterung über Setup-Script (5min)
- E1.2 HubSpot Properties + Workflow (30min)
- E1.3a Make-Szenario #1 — Quiz Submit (60min)
- Quiz-Frontend lokal testen mit echtem Webhook (30min)
- → **Hauptmeilenstein:** Quiz-Submit fließt End-to-End. Submit auf Demo-URL erscheint in HubSpot + Airtable + Slack-Notification + Meta Test Event.

### Wenn du **ein Wochenende** Zeit hast (~7-8h)
- Tag 1 (2h, Abend): 2-Stunden-Pfad oben
- Tag 2 Vormittag (~3h, parallel-Block):
  - E1.3b/c Bidi-Sync Szenarien (60min) **und parallel:**
  - Quer-Welle GTM-Container + 4 Pixel (90min)
- Tag 2 Nachmittag (~3h):
  - Claude baut E2-Streamlit-Code (~3h Claude-Zeit, parallel zum nächsten User-Schritt)
  - Service-Account-JSON in `.streamlit/secrets.toml` einfügen (5min User)
  - E2 Live-Test (25min User)
- Tag 3 (Abend, ~2h):
  - E1.4 Power BI Cross-Source (90min User)
  - End-to-End-Test V2 (30min)

---

## 5. Risiken und Stolpersteine

| Risiko | Auswirkung | Mitigation |
|---|---|---|
| HubSpot Free wählt versehentlich US-Region statt EU | Demo-Setup nicht-DSGVO-konform | Bei Signup explizit EU-Hosting in Auswahl klicken |
| Make Free-Tier hat 1.000 Ops/Monat | Pro Quiz-Submit ~6 Ops → 158 Submits/Monat | Reicht für Demo, bei Skalierung Make Core (~9 €) |
| Google Workspace ohne Domain-wide Delegation | E2 Service Account kann nicht auf Setter-Kalender impersonieren | Free Workspace Trial nutzen oder Demo-Domain wie `demo.example` registrieren |
| Meta Business Manager KYC-Reibung | Pixel kann angelegt werden, Ad-Spend braucht KYC | Für Demo nicht relevant — Test Event Code funktioniert ohne KYC |
| GTM Container ohne verifizierte Domain | GTM lädt auf GitHub-Pages-URL trotzdem | OK für Demo |
| Aircall hat keinen Free-Tier (~30 €/Setter/Monat) | E2 Click-to-Call nicht produktiv testbar | Stub mit `tel:`-Fallback wird dokumentiert |
| HubSpot ↔ Airtable Sync-Loops (Ping-Pong) | Endlosschleife möglich | `_source`-Feld als Loop-Prevention (Doku in `make-bridge/field-mapping.md`) |
| Quiz-Frontend braucht Live-Webhook zum Testen | Lokales `file://` kann nicht mit Make verbinden, sobald CORS strikt ist | Erst Make-Webhook fertig, dann Quiz-Frontend |
| `.streamlit/secrets.toml` aus Versehen committed | Service-Account-JSON in Git → SA-Compromise | `.gitignore` enthält `**/secrets.toml`; Pre-Commit-Hook empfohlen |
| Power BI Desktop nur auf Windows | macOS-User braucht VM oder Cloud-Workspace | Workspace-Variante in `powerbi-cross-source/README.md` dokumentiert |

---

## 6. Definition-of-Done für Phase E

Phase E gilt als abgeschlossen, wenn:

- [ ] **Quiz-Submit auf Demo-URL** legt Datensatz in HubSpot **und** Airtable an (identische E-Mail + Score)
- [ ] **HubSpot-Workflow** feuert bei `quiz_score ≥ 50` (sichtbar in Workflow-History)
- [ ] **Meta Events Manager** zeigt `Lead`-Event client- und server-side mit derselben `event_id` (dedupliziert)
- [ ] **GA4 DebugView** zeigt `quiz_submit`-Events auf beiden Streams
- [ ] **TikTok Events Manager** zeigt mindestens 1 Lead-Test-Event
- [ ] **Setter-Daily-Streamlit** zeigt Hot-Lead-Queue, Test-Termin wird gebucht, Event landet im Demo-Kalender mit Meet-Link
- [ ] **Airtable-Lead** nach Buchung hat `Status="Contacted"`, `Termin am`, `Meet-Link`, `Setter` gesetzt
- [ ] **Power BI Desktop** lädt beide Datenquellen, Cross-Source-Dashboard zeigt ≥5 Test-Leads mit gejointen Mentor-Sessions

---

## 7. Getroffene Entscheidungen (Stand 2026-05-20)

| Frage | Entscheidung | Begründung |
|---|---|---|
| Account-Setup-Sprint | ✅ **erledigt** — IDs liegen in `.env` | – |
| Workspace-Domain für E2 | **Google-Workspace-Trial** | Schnellster Pfad zu Domain-wide Delegation ohne neue Domain registrieren zu müssen |
| Loom-Video | **nicht gewünscht** | Plan und Doku reichen aus |
| Reihenfolge Quer-Welle vs. E1.4 Power BI | **Quer-Welle parallel zu E1.3b/c, Power BI als Finalisierungs-Schritt am Ende** | siehe unten |

### Reihenfolge-Entscheidung — Begründung

**Quer-Welle (GTM + 4 Pixel) läuft parallel zu E1.3b/c (Bidi-Sync), Power BI kommt zuletzt.** Drei Gründe:

1. **Werkzeug-Trennung:** Quer-Welle wird in der GTM-UI konfiguriert, E1.3b/c in der Make-UI. Kein Tool-Konflikt, kein Context-Switching innerhalb derselben Plattform.
2. **Schnelles Feedback bei Pixel-Setup:** Meta Test Events Manager + GA4 DebugView + TikTok Events Manager zeigen sofort, ob ein Tag korrekt feuert. Das ist motivierend und entdeckt Fehler in Minuten statt erst beim End-to-End-Test.
3. **Power BI ist downstream:** PBI joint HubSpot- und Airtable-Daten. Sinnvoll erst wenn beide Datenflüsse stabil sind — also nach E1.3a (Quiz-Submit fließt) **und** E1.3b/c (Bidi-Sync läuft). PBI vor Quer-Welle würde nichts beschleunigen, weil PBI keine Pixel-Daten konsumiert.

Die Auswirkung im Wochenend-Plan (siehe §4): Tag 2 Vormittag ist Parallel-Block (E1.3b/c + Quer-Welle), Tag 3 Abend ist E1.4 + End-to-End-Test.

---

## 8. Bereit für Build-Sprint

Alle Vorklärungen sind durch. Der Build-Sprint kann gestartet werden,
sobald ein konkretes Zeitfenster (2h, Wochenende) gewählt wird. Der
nächste Schritt im 2-Stunden-Pfad ist der Setup-Script-Run gegen die
Airtable-Base — siehe [`02b-airtable-phase-e-extension.md`](02b-airtable-phase-e-extension.md)
und [`scripts/setup_airtable_phase_e.py`](scripts/setup_airtable_phase_e.py).
