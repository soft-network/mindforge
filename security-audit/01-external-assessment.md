# 01 · External Assessment — Roh-Befunde

Roh-Daten der passiven Scans. Diese Datei enthält **keine Wertung** — nur Beobachtungen.
Bewertung mit CVSS-Score: siehe [`03-findings-report.md`](03-findings-report.md).

---

## 1. Subdomain-Inventar (Stand 2026-05-19)

Aus eigener Funnel-Analyse + Memory `reference_lovelifepassport_facts.md` bekannt:

| Subdomain | Plattform | Zweck |
|---|---|---|
| `www.lovelifepassport.com` | **Webflow** (CF + Lambda US-East-1) | Brand-Hub, Hauptseite |
| `analyse.lovelifepassport.com` | **Proprietärer Funnel-Builder** (onecdn.io, GCP-Hosting) | Quiz-Funnel |
| `analyse2.lovelifepassport.com` | (gleich) | A/B-Quiz-Variante |
| `strategie.lovelifepassport.com` | (gleich) | Strategiegespräch-Buchung |
| `obk.lovelifepassport.com` | (gleich) | Online Business Kickstart Sales |
| `the-escapetheory.lovelifepassport.com` | (gleich) | Escape-Theory-Kurs |
| `retreat.lovelifepassport.com` | (gleich) | Bali Retreat-Anmeldung |
| `lovelifepassport.factorialhr.de` | **Factorial HR** (SaaS) | Stellenportal/Bewerbungen |
| `ateschthing.clickfunnels.com/llp-webclass` | **ClickFunnels** (SaaS) | Webclass-Funnel |

**Implikation:** 3 verschiedene Funnel-Plattformen (Webflow, eigener Builder, ClickFunnels)
+ 1 HR-Plattform. Jede Plattform hat eigene Security-Posture und eigene Angriffsoberfläche.

---

## 2. HTTP-Response-Header

### 2.1 `analyse.lovelifepassport.com` (Funnel-Builder onecdn.io)

```
HTTP/1.1 200 OK
Content-Security-Policy: frame-ancestors 'self'
Permissions-Policy: camera=(), microphone=(), geolocation=()
Referrer-Policy: strict-origin-when-cross-origin
Strict-Transport-Security: max-age=31536000
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Via: 1.1 google
```

**Beobachtungen:**
- CSP nur `frame-ancestors` — **kein `default-src`, kein `script-src`** → keine XSS-Mitigation per CSP
- HSTS: `max-age` OK, aber **kein `includeSubDomains`, kein `preload`** → Subdomain-Hijacks könnten HTTPS umgehen
- `Via: 1.1 google` → Google Cloud Load Balancer / Cloud CDN
- Permissions-Policy, X-Content-Type-Options, X-Frame-Options gesetzt — gut

### 2.2 `www.lovelifepassport.com` (Webflow auf Cloudflare)

```
HTTP/1.1 200 OK
content-security-policy: frame-ancestors 'self'
Strict-Transport-Security: max-age=31536000
x-frame-options: SAMEORIGIN
x-lambda-id: 528f77b1-cf8b-4106-a529-e07fd028ee04
x-wf-region: us-east-1
surrogate-key: www.lovelifepassport.com 6666a6637c1ea611ee5871e8 ...
Server: cloudflare
set-cookie: _cfuvid=Ol1lEIl6...; HttpOnly; SameSite=None; Secure
```

**Beobachtungen:**
- `x-lambda-id`, `x-wf-region: us-east-1`, `surrogate-key` → **Information Disclosure** (Webflow-Backend-Details)
- `us-east-1` → **DSGVO/Schrems-II-Risiko** (Datenübermittlung in die USA)
- `_cfuvid` Cookie wird **VOR Cookie-Consent** gesetzt → TTDSG-Diskussion
- Selbe CSP-Schwäche wie analyse.*

### 2.3 `strategie.lovelifepassport.com`

Identische Konfiguration wie `analyse.lovelifepassport.com` (selber Funnel-Builder).

### 2.4 `obk.lovelifepassport.com` / `retreat.lovelifepassport.com`

Identische Konfiguration wie `analyse.lovelifepassport.com`. Konsistent über alle
Funnel-Builder-Subdomains → eine zentrale Builder-Konfiguration, die zentral
gefixt werden kann.

### 2.5 `ateschthing.clickfunnels.com/llp-webclass` (ClickFunnels)

```
HTTP/1.1 200 OK
Server: cloudflare
set-cookie: __cf_bm=...; Domain=clickfunnels.com
set-cookie: _cfuvid=...; Domain=clickfunnels.com
X-Content-Digest: ff4337fd57224a81e985c0cef3bc10911f781b07
X-Rack-Cache: miss, store
X-Request-Id: 7a5fa89a823f20355d8d47e7edac91a0
X-Runtime: 0.542318
```

**Beobachtungen:**
- ❗ **Keine einzige Security-Header gesetzt:** kein CSP, kein HSTS, kein X-Frame-Options, kein X-Content-Type-Options, kein Referrer-Policy, kein Permissions-Policy
- `X-Request-Id`, `X-Content-Digest`, `X-Runtime` → Information Disclosure
- Cookies auf `Domain=clickfunnels.com` → **shared mit allen ClickFunnels-Kunden!** (Cross-Customer-Tracking-Risiko)
- Plattform-Limitierung: LLP hat als ClickFunnels-Kunde nur begrenzten Einfluss

### 2.6 `lovelifepassport.factorialhr.de` (Factorial HR)

```
HTTP/1.1 200 OK
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: frame-ancestors 'self' https://dato-plugin-seven.vercel.app ...
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Referrer-Policy: strict-origin-when-cross-origin
expect-ct: max-age=86400, enforce
x-xss-protection: 1; mode=block
x-factorial-platform: aws-prod-eucentral1-glob01-blue
x-factorial-version: 4c4d381a146358da8fe0adca281bbe2c913d4bb9
x-amzn-trace-id: Root1-6a0c72b5-...
```

**Beobachtungen:**
- ✅ **HSTS korrekt mit `includeSubDomains; preload`** (Best Practice)
- ✅ EU-Hosting (`eucentral1`) → DSGVO-konform
- Trotzdem: `x-factorial-platform`, `x-factorial-version`, `x-amzn-trace-id` → Information Disclosure (low)
- Factorial macht es deutlich besser als der LLP-eigene Funnel-Builder

---

## 3. DNS / E-Mail-Authentifizierung

### 3.1 SPF

```
v=spf1 include:_spf.google.com include:mail.zendesk.com ~all
```

**Beobachtungen:**
- `include:_spf.google.com` → Google Workspace als Mail-Provider (matched mit MX)
- `include:mail.zendesk.com` → **Zendesk wird/wurde für Support-Mails genutzt** (nicht nur HubSpot)
- `~all` (Softfail) statt `-all` (Hardfail) → manche Mail-Server akzeptieren trotzdem gespoofte Mails

### 3.2 DMARC

```
_dmarc.lovelifepassport.com   v=DMARC1; p=none; pct=100;
```

**Beobachtungen:**
- ❗❗ **`p=none`** → Empfänger-Server quarantänieren/rejecten Spoofing-Mails **nicht**, sie loggen nur
- ❗ **Kein `rua=`/`ruf=` Reporting-Tag** → LLP bekommt keine Failure-Reports → blind gegen laufenden Missbrauch
- ❗ Kein `sp=` (Subdomain-Policy) → Subdomain-Spoofing nicht abgedeckt

### 3.3 DKIM-Selektoren (gefunden)

| Selektor | Anbieter | Key-Stärke |
|---|---|---|
| `google._domainkey` | Google Workspace | **1024-bit RSA** ⚠️ (Best Practice: ≥2048-bit) |
| `zendesk1._domainkey` | Zendesk (via CNAME) | 2048-bit RSA ✓ |
| `hs1-26317639._domainkey` | HubSpot (via CNAME) | 2048-bit RSA ✓ |

**Beobachtungen:**
- HubSpot-DKIM-Selektor **leakt HubSpot-Account-ID (`26317639`)** im DNS — das ist
  öffentlich, aber bedeutet: Jeder kann LLPs HubSpot-Account identifizieren (Phishing-Vektor)
- Google-DKIM mit nur 1024-bit ist kryptografisch schwach und sollte rotiert werden
  (Google bietet ein einfaches Re-Generate auf 2048-bit an)

### 3.4 MX

```
1   aspmx.l.google.com
5   alt1.aspmx.l.google.com
5   alt2.aspmx.l.google.com
10  alt3.aspmx.l.google.com
10  alt4.aspmx.l.google.com
```

Standard Google Workspace MX-Setup, keine Auffälligkeiten.

### 3.5 TXT-Records (sonstige Verifications)

```
clickfunnels-domain-verification=vyQgav
google-site-verification=2EY1KBv3J3zQ...
google-site-verification=Sz9WKG1KE3R6...
google-site-verification=XJ6l6aspt87k...
one-time-verification=07bc7cae-fd75-4729-a023-96cec011500f
slack-domain-verification=1lGGfkKsO8M...
facebook-domain-verification=v4xhb98i2co5y70uyt0987cacxq2x8
```

**Beobachtungen:**
- 3 parallele Google-Site-Verifications → vermutlich Altlasten aus Migrations
- ClickFunnels-Verification + Slack-Verification + Facebook-Verification bestätigen
  den 3rd-Party-Stack
- `one-time-verification` (vermutlich Notion oder ein anderer SaaS) → unklar welcher

---

## 4. `/.well-known/security.txt` (RFC 9116)

```
$ curl -I https://www.lovelifepassport.com/.well-known/security.txt
HTTP/1.1 404 Not Found
```

**Beobachtung:** Kein Disclosure-Channel definiert. Bug-Bounty-Hunter und
Sicherheitsforscher haben keine offizielle Adresse für Meldungen.

---

## 5. robots.txt + sitemap.xml

```
$ curl https://www.lovelifepassport.com/robots.txt
Sitemap: https://www.lovelifepassport.com/sitemap.xml
```

Sitemap-Inhalt (Auszug):
```
/rechtliches/impressum
/rechtliches/datenschutzerklarung
/rechtliches/agb-vae
/rechtliches/widerrufsbelehrung
/inner-circle
/kontakt/kostenloses-strategiegespraech
/kundenergebnisse
/ueber-uns
```

**Beobachtungen:**
- Kein `Disallow` in robots.txt — alles ist crawlbar (OK für Marketing-Site)
- Keine Hidden-Endpoints in der Sitemap → saubere Trennung Public/Interne Tools

---

## 6. Tracking-Stack (aus vorhergehender Live-Analyse, 2026-05-18)

Aus `LOVELIFEPASSPORT-ANALYSE.md` und dem `MEMORY.md`-Index bereits dokumentiert:

| Tool | ID/Endpoint | Sichtbarkeit |
|---|---|---|
| Meta Pixel | `1784432958288866` | Im HTML, öffentlich |
| GTM | `GTM-KMGMM4H` | Im HTML, öffentlich |
| GA4 #1 | `G-WJ6VFGWJKX` | Im HTML, öffentlich |
| GA4 #2 | `G-04CBYNE97V` | Im HTML, öffentlich |
| TikTok Pixel | (anonym im Endpoint) | Network-Tab, öffentlich |
| HubSpot | Account `26317639` (EU) | Im HTML + DNS |

**Beobachtung (relevant für DSGVO):** Im Quiz wird HubSpot-Tracking-Script
`js-eu1.hs-scripts.com/26317639.js` direkt im `<head>` geladen — **vor**
einer Cookie-Consent-Entscheidung. Selbst wenn Consent-Mode v2 angeschaltet
ist und Cookies nicht gesetzt werden, **wird der HubSpot-Server kontaktiert**
und IP-Adressen werden übertragen.

---

## 7. Wayback / Historische Snapshots

(nicht durchgeführt in dieser passiven Phase — Wayback-Machine ist passiv und
würde in einer Phase 2 historische Endpoints und alte JS-Bundles aufzeigen.
Mögliche Findings: alte Token in alten JS-Versionen, gelöschte Test-Endpoints,
Webhook-URLs in deprecated Bundles.)

---

## 8. JS-Bundle-Inspektion (Funnel-Builder)

**Bundle-URL:** `https://onecdn.io/b/client/1778147797912/js/main.bundle.js`

(Detaillierte Inspektion in Phase 2 — die statische Analyse des Builder-Bundles
würde XHR-Endpoints, Backend-API-Pfade und ggf. eingebettete Webhook-URLs offenlegen.
**Nicht durchgeführt** in dieser passiven Phase, weil das Bundle zwar öffentlich
abrufbar ist, eine systematische Reverse-Engineering-Analyse aber jenseits der
Linie für ein freiwilliges External Assessment liegt.)

---

## 9. Zusammenfassung

**Stark:**
- HubSpot EU-Region korrekt gewählt (`eu1` statt `na1`)
- Cookie-Consent-Banner über HubSpot vorhanden
- Permissions-Policy korrekt restriktiv
- Webflow-Datenschutzerklärung, Impressum, AGB, Widerruf an Standard-Pfaden

**Schwach:**
- DMARC `p=none` ohne Reporting → E-Mail-Spoofing-Vektor offen
- Keine echte CSP → keine XSS-Defense-in-Depth
- ClickFunnels-Webclass ohne jegliche Security-Header
- 1024-bit Google-DKIM → kryptografisch schwach
- Kein `/.well-known/security.txt` → kein Disclosure-Channel
- Webflow-Hosting in `us-east-1` → Schrems-II
- Tracking-Pixel-Loading vor Einwilligung

Bewertung mit CVSS und Empfehlungen siehe [`03-findings-report.md`](03-findings-report.md).
