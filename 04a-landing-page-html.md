# Schritt 4a — HTML Landing Page (öffentlich)

**Ziel:** Eine echte, conversion-fokussierte Landing Page, die Leads über den Make-Webhook ins CRM einspeist.

**Warum HTML statt Streamlit:** Industriestandard, SEO-fähig, schnelle Ladezeit, Tracking-Pixel-fähig, mobile-optimiert. Das ist, wie es real gemacht wird (siehe [00-erweiterungs-plan.md](00-erweiterungs-plan.md)).

---

## Was schon gebaut ist

In `landing-page/`:
- **[index.html](landing-page/index.html)** — Komplette Page mit Hero, Programs, Form, Footer
- **[styles.css](landing-page/styles.css)** — Minimal modernes Styling
- **[script.js](landing-page/script.js)** — Form-Handler mit UTM-Capture, Validation, Webhook-Submit, Meta-Pixel-Trigger

## Features

| Feature | Wo im Code |
|---|---|
| **UTM-Quellen-Erkennung** (Google/Facebook/Instagram etc.) | `script.js` → `captureSource()` |
| **Referrer-Fallback** (wenn keine UTM) | `script.js` → `captureSource()` |
| **Client-Side Validation** (Name, Email, Programm) | `script.js` → `validateForm()` |
| **Event-ID Generation** (für Pixel-CAPI-Deduplication) | `script.js` → `generateEventId()` |
| **Meta Pixel** im `<head>` | `index.html` |
| **Google Tag Manager** Container | `index.html` |
| **Meta Pixel Lead Event** bei Submit | `script.js` → `fbq('track', 'Lead', ...)` |
| **GTM DataLayer Push** bei Submit | `script.js` → `dataLayer.push(...)` |
| **OpenGraph Meta-Tags** (Social Sharing) | `index.html` |
| **Mobile Responsive** | `styles.css` |
| **Accessibility** (aria-live, autocomplete) | `index.html` |

---

## Setup-Schritte

### 1. Config-Datei erstellen

Die Landing Page lädt Runtime-Werte aus `landing-page/config.js`. Diese Datei
ist gitignored — wird also nicht committed. Initial anlegen:

```bash
cd landing-page
copy config.example.js config.js         # Windows
# Mac/Linux: cp config.example.js config.js
```

Dann `config.js` öffnen und Werte einsetzen:

| Key | Wo bekommen |
|---|---|
| `WEBHOOK_URL` | Make-Scenario, Step 1 ([04-make-scenario.md](04-make-scenario.md)) |
| `META_PIXEL_ID` | Meta Events Manager ([10-meta-capi-tracking.md](10-meta-capi-tracking.md)) |
| `GTM_CONTAINER_ID` | Google Tag Manager ([01-accounts-setup.md](01-accounts-setup.md) Schritt 8) |

Damit sind beide Stellen versorgt: `script.js` liest `window.MINDFORGE_CONFIG.WEBHOOK_URL`,
die GTM- und Pixel-Init-Snippets in `index.html` ziehen ihre IDs aus derselben Config.

> **Hinweis:** Die `<noscript>`-Fallback-Tags in `index.html` enthalten weiterhin
> die Platzhalter `YOUR_META_PIXEL_ID` und `GTM-XXXXXXX`. Wenn dir das
> Pre-JS-Tracking (für Crawler oder JS-Off-User) wichtig ist, ersetze diese vor
> Deploy manuell. Für die Demo sind sie verzichtbar.

### 2. Lokal testen

```bash
cd C:\Users\msi\analyse\demo\landing-page
python -m http.server 8000
```

Dann öffne http://localhost:8000 im Browser.

→ Form ausfüllen → Submit → in Make sollte ein neuer Webhook-Eintrag erscheinen.

### 3. Auf GitHub Pages deployen

```bash
cd C:\Users\msi\analyse\demo
git init  # falls noch nicht geschehen
git add landing-page/
git commit -m "Add MindForge landing page"
git branch -M main
git remote add origin https://github.com/<dein-user>/mindforge-pipeline-demo.git
git push -u origin main
```

In GitHub:
1. Repo Settings → Pages
2. Source: Deploy from a branch
3. Branch: `main`, Folder: `/landing-page`
4. Save

→ Nach ~1 Minute: `https://<dein-user>.github.io/mindforge-pipeline-demo/`

### 4. Alternativ: Netlify Drop (noch einfacher)

1. Öffne https://app.netlify.com/drop
2. Drag & Drop des `landing-page/` Ordners
3. Sofort live unter `random-name-12345.netlify.app`
4. Optional: Custom-Subdomain einrichten

---

## Test-Cases

| Test | Erwartetes Verhalten |
|---|---|
| Page-Aufruf mit `?utm_source=facebook` | Hidden source field = "Facebook" |
| Page-Aufruf mit Referrer Instagram | Hidden source field = "Instagram" |
| Form leer absenden | Rote Feld-Outlines, Error-Message |
| Invalid Email | Email-Feld rot, Error-Message |
| Valid Submit | Webhook fired, Pixel "Lead" fired, Success-Message, Form reset |
| Network-Error simulieren (Webhook-URL falsch) | Error-Message, Button re-enabled |

---

## SEO + Meta-Tags (eingebaut)

- `<title>` und `<meta name="description">` für Google
- OpenGraph Tags für LinkedIn/Facebook/WhatsApp Sharing
- Semantic HTML (`<header>`, `<section>`, `<footer>`)
- Mobile-Viewport-Meta

## Performance

- Single HTML File, kein Framework-Overhead
- Inline-CSS Variables für Theming
- Vanilla JavaScript (kein React/Vue → kein Bundle)
- Total Page Size: ~10 KB
- Erste Anzeige: <500ms auch auf 3G

---

## Technische Eigenschaften

| Aspekt | Umsetzung |
|---|---|
| HTML / CSS / JavaScript | Komplette Page from scratch |
| API / Webhooks | Form → fetch() → Make Webhook |
| Tracking / Pixels | Meta Pixel + GTM + Event-ID Deduplication |
| Performance | <10 KB, kein Framework, schneller First Paint |
| UTM-Handling | Source-Detection aus URL und Referrer, dataLayer-Events |
| Mobile-First | Responsive CSS Grid |

---

## Zeitaufwand: ~2 Stunden (inkl. GitHub Pages Setup)

**Nächster Schritt:** [09-monitoring.md](09-monitoring.md) — UptimeRobot einrichten
