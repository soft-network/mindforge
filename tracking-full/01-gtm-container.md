# GTM Container — „MindForge Demo"

Aufbau des Google Tag Manager Containers, der Meta + GA4 + TikTok
zentral verwaltet. Replikat des LLP-Setups mit Container `GTM-KMGMM4H`.

---

## 1. Account & Container anlegen

1. `tagmanager.google.com` → **Account erstellen**
2. Account-Name: `MindForge Demo`
3. Container-Name: `quiz.mindforge.demo`
4. Target Platform: **Web**
5. Container-ID notieren (Format `GTM-XXXXXXX`) → in `quiz-frontend/config.js`:
   ```js
   window.MF_GTM_ID = "GTM-XXXXXXX";
   ```

---

## 2. Built-in Variables aktivieren

**Variables → Built-in → Configure** — folgende anhaken:
- `Click Element`, `Click Text`, `Click URL`
- `Form Element`, `Form Text`
- `Page URL`, `Page Path`, `Page Hostname`
- `Referrer`
- `Event` (für CE-Trigger)

---

## 3. Custom Variables (User-Defined)

| Name | Type | Source |
|---|---|---|
| `DLV - event_id` | Data Layer Variable | `event_id` |
| `DLV - score` | Data Layer Variable | `score` |
| `DLV - tier` | Data Layer Variable | `tier` |
| `DLV - email_plain` | Data Layer Variable | `email_plain` |
| `DLV - quiz_business_field` | Data Layer Variable | `quiz.business_field` |
| `DLV - quiz_monthly_revenue` | Data Layer Variable | `quiz.monthly_revenue` |
| `Custom JS - email_sha256` | Custom JavaScript | siehe unten |

**`Custom JS - email_sha256`** (für Pixel-AAM client-side):
```js
function() {
  var email = {{DLV - email_plain}};
  if (!email) return '';
  // SHA-256 sync via SubtleCrypto (ist async — daher hier ein simplerer Hash via TextEncoder).
  // Empfehlung: SHA-Hashing serverseitig in Make. Frontend nur als Fallback.
  return email.toLowerCase().trim();
}
```

---

## 4. Triggers

| Name | Type | Filter |
|---|---|---|
| `All Pages` | Page View | – (built-in) |
| `CE quiz_start` | Custom Event | Event name = `quiz_start` |
| `CE quiz_step_answered` | Custom Event | Event name = `quiz_step_answered` |
| `CE quiz_submit` | Custom Event | Event name = `quiz_submit` |
| `CE consent_granted` | Custom Event | Event name = `consent_granted` |

---

## 5. Tags

### 5.1 Meta Pixel Base
- Tag Type: **Custom HTML**
- Trigger: `All Pages`
- Code:
  ```html
  <script>
  !function(f,b,e,v,n,t,s)
  {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
  n.callMethod.apply(n,arguments):n.queue.push(arguments)};
  if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
  n.queue=[];t=b.createElement(e);t.async=!0;
  t.src=v;s=b.getElementsByTagName(e)[0];
  s.parentNode.insertBefore(t,s)}(window, document,'script',
  'https://connect.facebook.net/en_US/fbevents.js');
  fbq('init', '{{META_PIXEL_ID}}');
  fbq('track', 'PageView');
  </script>
  ```
- Einwilligung settings: `ad_storage`, `ad_user_data`, `ad_personalization`

### 5.2 Meta Pixel - Lead Event
- Tag Type: **Custom HTML**
- Trigger: `CE quiz_submit`
- Code:
  ```html
  <script>
  fbq('track', 'Lead', {
    value: 0,
    currency: 'EUR',
    content_name: 'Quiz Submit',
    lead_score: {{DLV - score}}
  }, { eventID: {{DLV - event_id}} });
  </script>
  ```

### 5.3 GA4 — Stream A Config
- Tag Type: **Google Tag**
- Tag-ID: `{{GA4_MEASUREMENT_ID_A}}` (z.B. `G-XXXX1`)
- Trigger: `All Pages`

### 5.4 GA4 — Stream B Config
- Wie 5.3, aber `{{GA4_MEASUREMENT_ID_B}}`

### 5.5 GA4 — Quiz Submit Event (beide Streams)
- Tag Type: **GA4 Event**
- Configuration Tag: Stream A
- Event Name: `generate_lead`
- Parameters:
  - `value` = `0`
  - `currency` = `EUR`
  - `lead_score` = `{{DLV - score}}`
  - `lead_tier` = `{{DLV - tier}}`
  - `event_id` = `{{DLV - event_id}}` (für Server-Side-Dedup mit MP)
- Trigger: `CE quiz_submit`
- *(Zweites Tag identisch mit Stream B als Config-Tag)*

### 5.6 TikTok Pixel Base
- Tag Type: **Custom HTML**
- Trigger: `All Pages`
- Code: siehe `04-tiktok-pixel.md`

### 5.7 TikTok Pixel - Lead Event
- Tag Type: **Custom HTML**
- Trigger: `CE quiz_submit`
- Code: siehe `04-tiktok-pixel.md`

---

## 6. Consent Mode v2

Alle Tags markieren mit:
- **Required additional consent**: `ad_storage`, `ad_user_data`, `ad_personalization`, `analytics_storage`

Im `consent.js` (Quiz-Frontend) wird `gtag('consent', 'update', ...)`
gefeuert. GTM hält Tags zurück, bis Einwilligung granted.

---

## 7. Publish

1. **Submit** → Version-Name: `v1 — Phase E launch`
2. **Publish**
3. **Preview-Mode** anwerfen, Quiz durchspielen, prüfen:
   - Page-View feuert auf Meta + GA4 (×2) + TikTok
   - `quiz_submit` triggert 4 Tag-Calls (Meta Lead, GA4 Stream A, GA4 Stream B, TikTok)

---

## 8. Validierung

| Tool | Was prüfen |
|---|---|
| **GTM Preview-Mode** | Tag-Reihenfolge, Variablen-Werte, Trigger-Hits |
| **Meta Events Manager → Test Events** | Pixel + CAPI feuern beide, dedupliziert auf `event_id` |
| **GA4 DebugView** | `generate_lead`-Event auf beiden Streams |
| **TikTok Events Manager → Test Events** | `CompleteRegistration` mit `event_id` |
| **Chrome DevTools → Network** | `connect.facebook.net`, `google-analytics.com/g/collect`, `analytics.tiktok.com/api/v2/pixel` |
