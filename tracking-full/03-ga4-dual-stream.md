# GA4 — Zwei parallele Streams

Repliziert LLPs Setup mit zwei GA4 Streams (`G-WJ6VFGWJKX` + `G-04CBYNE97V`),
gefeuert durch denselben GTM-Container.

---

## Warum zwei Streams?

Bei LLP vermutlich:
- **Stream A** = „alle Subdomains" (cross-domain aggregate)
- **Stream B** = „nur Quiz-Funnel" (isoliertes Conversion-Reporting)

In der Demo bauen wir das gleiche Pattern, um zu zeigen:
- Verständnis für Cross-Stream-Reporting
- Awareness für Sampling-Differenzen (jeder Stream hat sein eigenes
  Daten-Volumen und damit eigene Sampling-Schwelle)

---

## 1. Property + Streams anlegen

1. `analytics.google.com` → **Admin → Create Property**
2. Property-Name: `MindForge Demo`
3. Time Zone: `Europe/Berlin`, Currency: `EUR`

**Stream A — Aggregate:**
- Platform: Web
- Stream-Name: `mindforge-all`
- URL: `https://mindforge.demo` (oder GitHub-Pages-URL)
- Stream-ID notieren

**Stream B — Quiz Only:**
- Platform: Web
- Stream-Name: `mindforge-quiz`
- URL: `https://quiz.mindforge.demo`
- Stream-ID notieren

**API Secret pro Stream:** Stream → **Measurement Protocol API secrets → Create**.
In `.env`:
```env
GA4_MEASUREMENT_ID_A=G-XXXXX1
GA4_API_SECRET_A=abcdef...
GA4_MEASUREMENT_ID_B=G-XXXXX2
GA4_API_SECRET_B=ghijkl...
```

---

## 2. Custom Dimensions anlegen

Beide Streams: **Admin → Custom definitions → Create custom dimension**

| Dimension Name | Scope | User-property / Event-parameter |
|---|---|---|
| `lead_tier` | Event | event-param `lead_tier` |
| `lead_score` | Event | event-param `lead_score` (numeric) |
| `event_id` | Event | event-param `event_id` |
| `business_field` | Event | event-param `quiz_business_field` |

---

## 3. Conversion Events markieren

In beiden Streams unter **Configure → Events**:
- `generate_lead` → Toggle **Mark as conversion: ON**
- `quiz_start` → optional als Conversion markieren (Funnel-Step)

---

## 4. Client-Side: GTM-Tags

Siehe `01-gtm-container.md` §5.3, §5.4, §5.5 — zwei GA4-Config-Tags
und je Event-Tag mit beiden als Config-Reference.

---

## 5. Server-Side: Measurement Protocol (in Make)

→ siehe `make-bridge/01-quiz-submit-scenario.md` §6, Sub-Section **GA4 MP**.

Zwei HTTP-Calls aus Make, einer pro Stream:
- `https://www.google-analytics.com/mp/collect?api_secret={A}&measurement_id={A}`
- `https://www.google-analytics.com/mp/collect?api_secret={B}&measurement_id={B}`

**Wichtig — Deduplizierung:**
- GA4 dedupliziert nicht automatisch zwischen client- und server-side
- Workaround: client-side feuert `generate_lead` mit `event_id=X`,
  server-side feuert dasselbe Event nur dann, wenn die client-side
  Pixel-Anfrage fehlgeschlagen ist (über CAPI-Equivalent: ein extra
  Header `X-Mindforge-CS-Failed: 1` aus dem Frontend würde das anzeigen)
- Pragmatischer für die Demo: nur server-side feuern, client-side
  weglassen — dann gibt es nie Dubletten. Phase-E-Empfehlung: nur SS.

---

## 6. Validierung

**GA4 DebugView:**
- DevTools → Console: `gtag('config', '{ID}', { debug_mode: true })` (oder GA Debugger Extension)
- DebugView öffnen pro Stream
- Quiz durchspielen → `quiz_start` und `generate_lead`-Events sollten in beiden Streams erscheinen, mit gleichem `event_id`

**Realtime Report:**
- Beide Streams → Reports → Realtime
- Erwartet: identische User-Counts (bei reiner Demo-Anfrage)

---

## 7. Reporting

In **Explore → Free form**:
- Dimensions: `Event name`, `lead_tier`, `business_field`
- Metrics: `Event count`, `Conversions`
- Filter: `Event name = generate_lead`

Erlaubt das Cross-Cutting:
- Welche `business_field`-Branche bringt am meisten Conversions?
- Welche `lead_tier`-Verteilung ergibt sich aus Quiz-Submits?

Diese Insights gehen dann in Power BI (siehe `powerbi-cross-source/`).
