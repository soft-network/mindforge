# TikTok Pixel + Events API

Client-side Pixel via GTM + server-side Events API via Make.
Replikat des LLP-Setups (POSTs an `analytics.tiktok.com/api/v2/pixel/{inter,act}`).

---

## 1. TikTok Business Account

1. `ads.tiktok.com` → **Sign up** (kostenlos)
2. Beim Onboarding-Wizard:
   - Business Type: Coaching/Education
   - Country: Germany
3. **Tools → Events → Web Events → Manage**
4. **Set up Web Events → Manually install pixel**
5. Pixel-Name: `MindForge Quiz Pixel`
6. Domain: GitHub-Pages-URL
7. Pixel-ID notieren — Format `CXXXXXXXXXXXXXXXXX`

**Access Token für Events API:**
- Pixel → **Settings → Conversions API → Generate Access Token**
- Token kopieren → in `.env`:
  ```env
  TIKTOK_PIXEL_ID=CXXXXXXXXXXXXXXXXX
  TIKTOK_ACCESS_TOKEN=abcdef...
  TIKTOK_TEST_EVENT_CODE=TEST_XXXX
  ```

---

## 2. Client-Side Pixel (in GTM)

→ `01-gtm-container.md` §5.6 + §5.7

**Tag 5.6 — Base (alle Seiten):**

```html
<script>
!function (w, d, t) {
  w.TiktokAnalyticsObject=t;var ttq=w[t]=w[t]||[];ttq.methods=["page","track","identify","instances","debug","on","off","once","ready","alias","group","enableCookie","disableCookie"];
  ttq.setAndDefer=function(t,e){t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}};
  for(var i=0;i<ttq.methods.length;i++)ttq.setAndDefer(ttq,ttq.methods[i]);
  ttq.instance=function(t){for(var e=ttq._i[t]||[],n=0;n<ttq.methods.length;n++)ttq.setAndDefer(e,ttq.methods[n]);return e};
  ttq.load=function(e,n){var r="https://analytics.tiktok.com/i18n/pixel/events.js";ttq._i=ttq._i||{},ttq._i[e]=[],ttq._i[e]._u=r,ttq._t=ttq._t||{},ttq._t[e]=+new Date,ttq._o=ttq._o||{},ttq._o[e]=n||{};
  var o=document.createElement("script");o.type="text/javascript",o.async=!0,o.src=r+"?sdkid="+e+"&lib="+t;var a=document.getElementsByTagName("script")[0];a.parentNode.insertBefore(o,a)};

  ttq.load('{{TIKTOK_PIXEL_ID}}');
  ttq.page();
}(window, document, 'ttq');
</script>
```

**Tag 5.7 — Lead-Event (auf `quiz_submit`):**

```html
<script>
ttq.track('CompleteRegistration', {
  value: 0,
  currency: 'EUR',
  content_id: 'quiz_submit',
  content_type: 'lead'
}, {
  event_id: {{DLV - event_id}}
});
</script>
```

---

## 3. Server-Side Events API (in Make)

→ siehe `make-bridge/01-quiz-submit-scenario.md` §6, Sub-Section **TikTok**.

- Endpoint: `https://business-api.tiktok.com/open_api/v1.3/event/track/`
- Headers: `Access-Token: {{TIKTOK_ACCESS_TOKEN}}`
- Body: gehashte `email` + `phone` (SHA-256, lowercased)
- `event_id` identisch zum client-side Call → Deduplizierung

---

## 4. Validierung

**TikTok Events Manager → Pixel → Test Event:**
1. Test-Browser starten mit Test-Event-Code
2. Quiz durchspielen
3. Erwartet:
   - `Pageview` (Pixel-Base)
   - `CompleteRegistration` (client-side, mit `event_id=X`)
   - `CompleteRegistration` (server-side, mit `event_id=X`) → **Deduplicated ✓**

---

## 5. Event-Schema

TikTok hat ein striktes Event-Schema. Für „Lead" hat sich `CompleteRegistration`
durchgesetzt (kein offizieller „Lead"-Event). Bei Kampagnen-Setup darauf
optimieren:

- Custom-Conversion auf `CompleteRegistration` mit Filter `content_type = "lead"`
- Optional: zweite Conversion auf `CompleteRegistration` mit Filter
  `lead_score >= 70` für „Hot Lead"-Optimization
