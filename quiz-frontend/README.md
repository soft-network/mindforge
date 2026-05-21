# Quiz Frontend

Mehrstufiges Lead-Quiz mit Skip-Logic, Score-Berechnung und DataLayer-Tracking.
Vanilla JS, kein Build-Step. Nachgebaut nach dem Strukturmuster des
[`analyse.lovelifepassport.com`](../LOVELIFEPASSPORT-ANALYSE.md#3-analyse-des-quiz-funnels-analyselovelifepassportcom)-Funnels.

---

## Aufbau

| Datei | Rolle |
|---|---|
| `index.html` | 9 Frage-Sektionen + Kontaktformular + Thank-You |
| `styles.css` | Dark-Theme, responsive, Karten-Optionen, Progress-Bar |
| `score-engine.js` | Score-Berechnung pro Frage, Tier-Klassifizierung (hot / warm / cold / unqualified) |
| `quiz-engine.js` | State in `sessionStorage`, Skip-Logic, Navigation, Form-Validation |
| `submit-engine.js` | Webhook-POST an Make, DataLayer `quiz_submit`-Event |
| `tracking/gtm-bootstrap.js` | Lädt GTM-Container, setzt Default-Einwilligung auf `denied` |
| `tracking/consent.js` | Minimaler DSGVO-Banner, Cookie `mf_consent={granted\|denied}` |
| `config.example.js` | Template — kopiere zu `config.js` (in `.gitignore`) |

---

## Setup

```bash
# 1. Konfig anlegen
copy config.example.js config.js     # Windows
cp    config.example.js config.js    # Linux/Mac

# 2. config.js bearbeiten:
#    - window.MF_GTM_ID = "GTM-..."
#    - window.MF_CONFIG.webhookUrl = "https://hook.eu2.make.com/..."

# 3. lokal testen
python -m http.server 8000
# → http://localhost:8000/quiz-frontend/
```

---

## Score-Modell

| Step | Frage | Gewicht (max 100) |
|---|---|---|
| 1 | Selbstständig? | 5 |
| 2 | Wie lange selbstständig? | 10 |
| 3 | Bereich | 10 |
| 4 | Sichtbarkeit | 10 |
| 5 | Team-Aufstellung | 10 |
| 6 | Monatsumsatz | **20** ← stärkster Qualifier |
| 7 | Wunsch | 10 |
| 8 | Was fehlt? (multi) | 10 |
| 9 | Zeitbudget | **15** ← Commit-Indikator |

**Tier-Klassifizierung:**

| Score | Tier | Handlung |
|---|---|---|
| ≥ 70 | `hot` | Setter ruft sofort an |
| 50–69 | `warm` | Setter kontaktiert innerhalb 24h |
| 30–49 | `cold` | Nurture-Sequenz |
| < 30 | `unqualified` | Drip-E-Mail |

---

## Skip-Logic

| Wenn Frage… | Antwort… | Springt zu |
|---|---|---|
| 1 (Selbstständig?) | Nein | Step 3 (Bereich) — überspringt Frage „Wie lange selbstständig?" |

Replizierbar durch `data-skip-to`-Attribut an `.opt`-Buttons.

---

## DataLayer-Events

Alle Events landen in `window.dataLayer`, sind also über GTM ansprechbar.

| Event | Payload-Felder |
|---|---|
| `quiz_start` | `event_id` |
| `quiz_step_answered` | `step`, `key`, `value`, `score` |
| `quiz_submit` | `event_id`, `score`, `tier`, `email_plain` (für GTM-seitiges Hashing), `value`, `currency` |
| `quiz_submit_ready` | `event_id`, `score` (nach Webhook-Success) |
| `consent_granted` / `consent_denied` | – |

---

## Dry-Run-Modus

Wenn `window.MF_CONFIG.webhookUrl` nicht gesetzt ist (z. B. weil keine
`config.js` existiert), läuft der Submit lokal im **Dry-Run**:

- Payload wird in der Browser-Console geloggt
- DataLayer-Events feuern normal
- Thank-You-Seite wird trotzdem angezeigt

Ideal für lokale Entwicklung und Demos ohne Make-Account.

---

## Tests im Browser

```js
// Console: aktueller Quiz-State
JSON.parse(sessionStorage.getItem("mf_quiz_state"))

// Console: Payload, der an Make geschickt würde
window.MindForgeSubmit.buildPayload(JSON.parse(sessionStorage.getItem("mf_quiz_state")))

// Console: DataLayer einsehen
window.dataLayer
```
