# DataLayer Spec

Vollständige Liste der DataLayer-Events, die das Quiz-Frontend feuert,
plus die Properties pro Event. Diese Spec ist die Schnittstelle
zwischen Frontend (`quiz-engine.js` + `submit-engine.js`) und GTM-Tags.

---

## Event: `gtm.js` (built-in)

Wird automatisch von `gtm-bootstrap.js` gepusht.

| Property | Beispielwert |
|---|---|
| `gtm.start` | `1779127492651` (Unix ms) |
| `event` | `gtm.js` |
| `app` | `mindforge-quiz` |
| `version` | `1.0.0` |

---

## Event: `quiz_start`

Gefeuert beim Klick auf „Quiz starten".

| Property | Beispielwert |
|---|---|
| `event` | `quiz_start` |
| `event_id` | `0b6a3c7e-1c2d-4f5b-9e3a-8d7e4f2a1c33` |

GTM-Tags: optional als Conversion-Step zu markieren.

---

## Event: `quiz_step_answered`

Gefeuert nach jeder beantworteten Frage (Single + Multi).

| Property | Beispielwert |
|---|---|
| `event` | `quiz_step_answered` |
| `step` | `3` |
| `key` | `business_field` |
| `value` | `coach` (oder bei Multi: `"reach,sales"`) |
| `score` | `10` |

GTM-Tags: Step-Engagement-Tracking als GA4 `quiz_step_view`-Event.

---

## Event: `quiz_submit`

Gefeuert beim Klick auf „Antworten senden". **Vor** dem Webhook-Call,
damit Pixel direkt feuern können.

| Property | Beispielwert |
|---|---|
| `event` | `quiz_submit` |
| `event_id` | `0b6a3c7e-1c2d-4f5b-9e3a-8d7e4f2a1c33` |
| `score` | `72` |
| `tier` | `hot` |
| `email_plain` | `anna.mueller+demo@example.com` (wird in GTM-Variable gehashed) |
| `value` | `0` |
| `currency` | `EUR` |

GTM-Tags:
- Meta Pixel `Lead`
- GA4 `generate_lead` (×2 Streams)
- TikTok `CompleteRegistration`

---

## Event: `quiz_submit_ready`

Gefeuert **nach** erfolgreichem Webhook-Response.

| Property | Beispielwert |
|---|---|
| `event` | `quiz_submit_ready` |
| `event_id` | `0b6a3c7e-1c2d-4f5b-9e3a-8d7e4f2a1c33` |
| `score` | `72` |

GTM-Tags: optional Server-Side-Backup-Conversion (z. B. für Make-Outage-Fallback).

---

## Event: `consent_granted` / `consent_denied`

Gefeuert vom Consent-Banner.

| Property | Beispielwert |
|---|---|
| `event` | `consent_granted` |

GTM-Tags: keine direkten — wird vom Consent-Mode v2 automatisch verarbeitet.

---

## Globale Properties (in jedem Event verfügbar)

Stehen auf der `window`-Ebene zur Verfügung über `gtag` Custom Variables:

| Source | Variable |
|---|---|
| URL-Parameter | `utm_source`, `utm_medium`, `utm_campaign` |
| Browser | `user_agent`, `language`, `viewport_w`, `viewport_h` |
| Cookies | `_fbp`, `_fbc`, `_ga`, `__hstc`, `hubspotutk` |
| SessionStorage | `mf_quiz_state` (komplettes Quiz-State-Object) |

---

## Naming Convention

- **Events:** `snake_case`, Verb-basiert, ohne Prefix
- **Properties:** `snake_case`
- **Custom Dimensions in GA4:** `lead_*`, `quiz_*` für Klarheit
- **Pixel-Event-Namen:** offizielle Meta-/TikTok-Namen verwenden (`Lead`, `CompleteRegistration`), nicht eigene erfinden

---

## Debug Helper

Im Browser-Console:

```js
// Aktuellen DataLayer einsehen
copy(JSON.stringify(window.dataLayer, null, 2));

// Events pro Typ zählen
window.dataLayer.reduce((acc, e) => {
  acc[e.event] = (acc[e.event] || 0) + 1; return acc;
}, {});

// Letztes Quiz-Submit-Event
[...window.dataLayer].reverse().find(e => e.event === 'quiz_submit');
```
