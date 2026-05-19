# Tracking-Stack (Quer-Welle)

Repliziert das vollständige Tracking-Setup, das auf
`analyse.lovelifepassport.com` live beobachtet wurde:

- **Google Tag Manager** als Container-Wrapper
- **Meta Pixel** (client) + **Conversion API** (server, in Make)
- **GA4** mit **zwei parallelen Streams**
- **TikTok Pixel** (client) + **Events API** (server, in Make)

---

## Dateien

| Datei | Inhalt |
|---|---|
| [`01-gtm-container.md`](01-gtm-container.md) | GTM-Setup, Tags, Trigger, Variablen |
| [`02-meta-pixel-capi.md`](02-meta-pixel-capi.md) | Meta Pixel + Conversion API mit Test Event Code |
| [`03-ga4-dual-stream.md`](03-ga4-dual-stream.md) | Zwei GA4-Streams parallel (wie LLP) |
| [`04-tiktok-pixel.md`](04-tiktok-pixel.md) | TikTok Pixel + Events API |
| [`05-consent-and-dsgvo.md`](05-consent-and-dsgvo.md) | Consent-Mode v2, DSGVO-Anforderungen |
| [`dataLayer-spec.md`](dataLayer-spec.md) | Welches Event mit welchen Properties feuert |

---

## Setup-Reihenfolge

1. **GTM-Account + leerer Container** (~ 10 min) — `01-gtm-container.md`
2. **Meta Business Manager** + Test-Pixel (~ 15 min) — `02-meta-pixel-capi.md`
3. **GA4-Property** mit 2 Streams (~ 10 min) — `03-ga4-dual-stream.md`
4. **TikTok-Business-Account** + Test-Pixel (~ 15 min) — `04-tiktok-pixel.md`
5. **GTM-Tags konfigurieren** (~ 30 min) — `01-gtm-container.md` §3
6. **Server-Side-Calls in Make** (~ 30 min) — bereits in `make-bridge/01-quiz-submit-scenario.md` §6

---

## Was vom LLP-Original nachgebaut wird

| LLP-Befund (live) | MindForge-Replikation |
|---|---|
| GTM-Container `GTM-KMGMM4H` als zentraler Loader | Demo-GTM-Container „MindForge Demo" |
| Meta Pixel `1784432958288866` mit Automatic Advanced Matching | Test-Pixel mit AAM aktiviert + CAPI mit Event-ID-Dedup |
| GA4 Streams `G-WJ6VFGWJKX` + `G-04CBYNE97V` parallel | Zwei Streams im gleichen Account, identische Events |
| TikTok Pixel mit `analytics.tiktok.com/api/v2/pixel/{inter,act}` | Pixel + Events API server-side mit Event-ID-Dedup |
| HubSpot Tracking + `__ptc.gif` Klick-Tracking | HubSpot Embed-Code (optional, siehe `hubspot/README.md` §5) |
| `SubscribedButtonClick`-Events mit External-ID-Hash | AAM aktiviert → Pixel sendet automatisch alle Klicks mit Email-Hash |

---

## Was bewusst weggelassen wird

- **LinkedIn Pixel** (nicht in LLP-Stack gesehen)
- **Pinterest Pixel** (nicht in LLP-Stack gesehen)
- **Hotjar / Microsoft Clarity** (LLP nutzt es nicht; im Bewerbungs-Pitch erwähnen, dass es einfach addbar wäre)
- **Server-Side-GTM** (echtes sGTM bräuchte App Engine / Cloud Run mit eigener Domain — zu großer Aufwand für die Demo; CAPI/MP/Events-API direkt aus Make liefert ~80% des Werts)
