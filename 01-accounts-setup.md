# Schritt 1 — Accounts erstellen

> ⚠️ Alle Accounts musst du selbst erstellen. Ich darf das aus Sicherheitsgründen nicht für dich machen.

Alle hier benötigten Tools haben einen **kostenlosen Tier**, der für die Demo komplett ausreicht.

---

## Pflicht-Accounts (Phase 1: Kern-Pipeline)

### 1. Airtable

- **Link:** https://airtable.com/signup
- **Plan:** Free (bis 1.000 Datensätze pro Base — reicht locker)
- **Was du brauchst:** E-Mail-Adresse
- **Nach Signup:** Klicke "Start from scratch" → Base wird automatisch erstellt
- **Notiere dir:** `BASE_ID` (steht in der URL: `airtable.com/appXXXXXXX/...`) und `API_TOKEN` aus https://airtable.com/create/tokens

### 2. Make (ehemals Integromat)

- **Link:** https://www.make.com/en/register
- **Plan:** Free (1.000 Operations/Monat — Demo braucht ~50)
- **Was du brauchst:** E-Mail-Adresse
- **Tipp:** Google-Account-Login spart Zeit

### 3. Power BI Desktop

- **Link:** https://powerbi.microsoft.com/en-us/desktop/
- **Plan:** Desktop ist kostenlos, kein Microsoft-Account zum Installieren nötig
- **Wichtig:** Nur die **Desktop-Version** — der Cloud-Service kostet
- **Größe:** ~500 MB Download, Windows-only

### 4. Slack

- **Link:** https://slack.com/get-started#/createnew
- **Plan:** Free
- **Workspace:** `mindforge-demo`
- **Channels anlegen:**
  - `#mindforge-leads` (Hot-Lead-Notifications)
  - `#mindforge-alerts` (UptimeRobot-Alerts)

### 5. GitHub

- **Link:** https://github.com/signup
- **Repo:** Erstelle öffentliches Repo `mindforge-pipeline-demo`
- **Zweck:** Code + Doku + GitHub Pages Hosting für Landing Page

---

## Phase A Accounts (Schnelle Wins)

### 6. UptimeRobot

- **Link:** https://uptimerobot.com/signUp
- **Plan:** Free (50 Monitors, 5-Min-Intervall)
- **Was du brauchst:** Email-Adresse
- **Nach Signup:** Email-Verifikation, dann direkt loslegen

### 7. Meta Business Manager (für Pixel)

- **Link:** https://business.facebook.com
- **Plan:** Kostenlos
- **Was du brauchst:** Facebook-Account (kann Test-Account sein)
- **Nach Signup:**
  - Business erstellen: `MindForge Demo`
  - Events Manager öffnen → Pixel anlegen → **Pixel-ID notieren**
- **Tipp:** Falls keine Facebook-Identität: erstelle einen FB-Account speziell für Test-Zwecke

### 8. Google Tag Manager (optional, für Phase B)

- **Link:** https://tagmanager.google.com
- **Plan:** Kostenlos
- **Was du brauchst:** Google-Account
- **Container:** `MindForge` (Type: Web) → **Container-ID notieren** (`GTM-XXXXXXX`)

---

## Phase B Accounts

### 9. Statuspage by Atlassian

- **Link:** https://www.atlassian.com/software/statuspage
- **Plan:** Free (2 Pages, 100 Subscribers)
- **Was du brauchst:** Atlassian-Account (kostenlos)
- **Page:** `mindforge-demo.statuspage.io`

### 10. Meta Conversion API Access Token

- Eigentlich Teil von Meta Business Manager
- **In Events Manager** → Pixel → **Settings** → **Conversions API** → **Set up manually** → **Generate Token**
- **Token sicher speichern** (geht nicht zurück abrufbar!)

---

## Phase C Accounts (Streamlit)

### 11. Streamlit Cloud (optional, Free Tier)

- **Link:** https://share.streamlit.io
- **Plan:** Community (kostenlos, 1 App pro Account, max 1 GB RAM)
- **Login:** GitHub-Account
- **Hinweis:** Wenn du Phase D (GCP) machst, brauchst du Streamlit Cloud nicht — Cloud Run ist die bessere Wahl

---

## Phase D Accounts (GCP)

### 12. Google Cloud Platform

- **Link:** https://cloud.google.com/free
- **Plan:** Free Tier + $300 Probe-Credit für 90 Tage
- **Was du brauchst:**
  - Google-Account
  - **Kreditkarte zur Verifikation** (wird NICHT belastet, solange du im Free Tier bleibst)
- **Projekt:** `mindforge-demo`

⚠️ **Wichtig für Tunesien:** GCP akzeptiert tunesische Kreditkarten meist, aber Visa/Mastercard von tunesischen Banken sind manchmal blockiert. Plan B:
- Wise-Karte (Multi-Currency-Karte, funktioniert global)
- Revolut-Karte
- Falls keine Karte verfügbar: **Skip Phase D**, erwähne GCP nur als geplante Erweiterung

---

## Komplette Checkliste

### Phase 1 — Pflicht (~30 min)
- [ ] Airtable Account + Token
- [ ] Make Account
- [ ] Power BI Desktop installiert
- [ ] Slack Workspace + 2 Channels
- [ ] GitHub Account + Repo `mindforge-pipeline-demo`

### Phase A — Schnelle Wins (~15 min)
- [ ] UptimeRobot Account
- [ ] Meta Business Manager + Pixel-ID
- [ ] Google Tag Manager Container (optional)

### Phase B — Mittel (~10 min)
- [ ] Statuspage by Atlassian
- [ ] Meta CAPI Access Token

### Phase C — Streamlit (~5 min, falls ohne GCP)
- [ ] Streamlit Cloud (nur wenn kein GCP)

### Phase D — GCP (~20 min)
- [ ] GCP Account mit Kreditkarte verifiziert
- [ ] gcloud CLI lokal installiert: https://cloud.google.com/sdk/docs/install

---

## Secrets-Übersicht (was du dir sicher speichern musst)

| Secret | Wo verwendet | Wie sicher speichern? |
|---|---|---|
| `AIRTABLE_API_TOKEN` | Streamlit, Make HTTP-Modul | Passwort-Manager |
| `AIRTABLE_BASE_ID` | Streamlit, Make | OK in Code (nicht sensibel) |
| `META_PIXEL_ID` | Landing Page, GTM | OK in Code (sichtbar im DOM) |
| `META_CAPI_ACCESS_TOKEN` | Make HTTP-Modul | Passwort-Manager — **streng geheim** |
| `META_TEST_EVENT_CODE` | Make (nur in Test-Phase) | Nicht sensibel |
| `SLACK_WEBHOOK_URL` | Make, UptimeRobot | Passwort-Manager |
| `MAKE_WEBHOOK_URL` | Landing Page, UptimeRobot | OK öffentlich (Make hat eigene Rate-Limits) |
| `GCP_PROJECT_ID` | gcloud CLI | OK in Code |
| `STREAMLIT_AUTH_PASSWORD` | Streamlit-App | Streamlit Secrets / GCP Secret Manager |

→ **Empfehlung:** Nutze Bitwarden (kostenlos) oder 1Password als Passwort-Manager.

---

## Zeitaufwand Gesamt

| Phase | Zeit |
|---|---|
| Phase 1 (Pflicht) | 30 min |
| Phase A | 15 min |
| Phase B | 10 min |
| Phase C | 5 min |
| Phase D | 20 min |
| **Gesamt alles** | **~80 min** |

**Sobald die Pflicht-Accounts (Phase 1) stehen, kannst du mit [02-airtable-schema.md](02-airtable-schema.md) starten.**
