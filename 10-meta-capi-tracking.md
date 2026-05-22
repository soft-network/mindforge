# Schritt 10 — Meta Pixel + Conversion API (CAPI)

**Ziel:** Komplettes Marketing-Tracking mit iOS 14.5+ kompatibler Server-Side Attribution.

**Hintergrund:** Online-Coaching-Geschäfte sind stark auf Performance-Ads angewiesen.
Seit iOS 14.5 funktioniert reines Browser-Pixel-Tracking nur noch teilweise — die
saubere Lösung kombiniert clientseitiges Pixel mit serverseitiger Conversion API
und Event-ID-Deduplication, sodass jede Conversion genau einmal in Meta landet.

---

## Konzept: Pixel + CAPI parallel

```
┌────────────────────┐
│  Browser           │
│  Landing Page      │
│                    │
│  fbq('track',      │  ──── Pixel Event (Client-Side) ────►  Meta Servers
│   'Lead',          │       event_id: lead_1715432_xyz9
│   {eventID: X})    │                                          │
└─────────┬──────────┘                                          │
          │                                                     │  Deduplication
          │ POST                                                │  via event_id
          ▼                                                     │
┌─────────────────────┐                                         │
│  Make Pipeline      │                                         │
│  ──────────────     │                                         │
│  → Create Lead      │                                         │
│  → SHA-256 Hash     │                                         │
│    email + phone    │                                         │
│  → POST to CAPI     │  ──── CAPI Event (Server-Side) ──────►  Meta Servers
│    event_id: X      │                                          │
│    matching keys    │                                          │
└─────────────────────┘                                          │
                                                                  ▼
                                                       [1 deduped Conversion]
```

**Das Problem ohne CAPI:**
- iOS 14.5+: Browser-Pixel Tracking nur mit App Tracking Transparency Einwilligung
- ~70 % der iOS-User opt-out → Attribution verloren
- Meta Ads optimieren auf falscher Datenbasis

**Die Lösung mit CAPI:**
- Server-Side Event geht direkt von deinem Backend (Make) an Meta
- Funktioniert unabhängig vom Browser
- Mit Hash-PII (email, phone) → Meta matched Conversion zu User
- Pixel + CAPI mit gleichem `event_id` → keine Doppelzählung

---

## Tool 1: Meta Pixel (Client-Side, bereits im Code)

### Setup

1. **Meta Business Manager** öffnen: https://business.facebook.com
2. **Events Manager** → **+ Connect Data Sources** → **Web** → **Meta Pixel**
3. Name: `MindForge Pixel`
4. Pixel-ID kopieren

### In Landing Page eintragen

In `landing-page/index.html` (bereits vorhanden, nur ID ersetzen):

```html
<script>
!function(f,b,e,v,n,t,s)
{...}(window, document,'script', 'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', 'YOUR_META_PIXEL_ID');  // ← hier
fbq('track', 'PageView');
</script>
```

### Lead-Event mit Event-ID feuern

Bereits in `landing-page/script.js`:

```js
if (typeof fbq !== 'undefined') {
    fbq('track', 'Lead', {
        content_name: data.interest_program,
        content_category: 'coaching_lead'
    }, { eventID: eventId });
}
```

→ Das `eventID` ist der **Match-Schlüssel** zur Server-Side Variante.

### Test mit Facebook Pixel Helper

1. Chrome Extension installieren: "Meta Pixel Helper"
2. Landing Page öffnen
3. Pixel-Icon klickt → zeigt: `PageView` ✓ und nach Submit `Lead` ✓

---

## Tool 2: Conversion API in Make (Server-Side)

### Voraussetzungen

In Meta Business Manager:
1. **Events Manager** → **Pixel auswählen** → **Settings**
2. **Conversions API** → **Set up manually**
3. **Access Token generieren** und sicher speichern

### Make-Step nach "Create Airtable Record"

#### Step A: SHA-256 Hash für PII

- Add module: **Tools → Compose a string** (oder verwende JS-Code-Module)
- Für **E-Mail**: `{{lower(1.email)}}` → dann `{{sha256(<result>)}}`
- Für **Telefon** (E.164-normalisiert): `{{replace(replace(1.phone; "+"; ""); " "; "")}}` → `{{sha256(<result>)}}`

Make hat `sha256()` als eingebaute Funktion in der String-Toolbox.

#### Step B: HTTP Request an CAPI

- Add module: **HTTP → Make a request**
- **URL:** `https://graph.facebook.com/v19.0/YOUR_PIXEL_ID/events?access_token=YOUR_ACCESS_TOKEN`
- **Method:** POST
- **Headers:** `Content-Type: application/json`
- **Body (JSON):**

```json
{
  "data": [
    {
      "event_name": "Lead",
      "event_time": {{round(parseDate(1.timestamp; "iso8601") / 1000)}},
      "event_id": "{{1.event_id}}",
      "event_source_url": "{{1.page_url}}",
      "action_source": "website",
      "user_data": {
        "em": ["{{sha256_email}}"],
        "ph": ["{{sha256_phone}}"],
        "client_user_agent": "{{1.user_agent}}",
        "client_ip_address": "{{1.connection.client.address}}"
      },
      "custom_data": {
        "content_name": "{{1.interest_program}}",
        "content_category": "coaching_lead",
        "currency": "EUR",
        "value": {{program_price}}
      }
    }
  ],
  "test_event_code": "TEST12345"
}
```

→ Für **Produktion**: `test_event_code` weglassen.

### Test im Events Manager

1. Meta Business Manager → **Events Manager** → **Test Events** Tab
2. **Test Event Code** generieren: z.B. `TEST12345`
3. In Make-Body als `test_event_code` einsetzen
4. Lead absenden via Landing Page
5. → In Test Events sollte erscheinen: 1x Lead (Pixel) + 1x Lead (Server) → **deduped to 1**

---

## Bonus: Google Tag Manager Setup

GTM verwaltet **alle** Pixel zentral statt jeden einzeln in HTML zu hardcoden.

### Container erstellen

1. https://tagmanager.google.com → **Create Account**
2. Container: `MindForge` (Type: Web)
3. Container-ID kopieren (`GTM-XXXXXXX`)

### In HTML ersetzen

In `landing-page/index.html`: GTM-XXXXXXX 2x ersetzen (bereits vorbereitet).

### Tags in GTM einrichten

#### Tag 1: Meta Pixel Base Code

- New Tag → Custom HTML
- Code: Standard Meta Pixel Snippet
- Trigger: All Pages

#### Tag 2: Meta Lead Event

- New Tag → Custom HTML
- Code: `fbq('track', 'Lead', {...}, {eventID: '{{DLV - event_id}}'});`
- Trigger: Custom Event = `lead_submitted`

#### Variable: DLV - event_id

- New Variable → Data Layer Variable
- Variable Name: `event_id`

#### Trigger: Custom Event lead_submitted

- New Trigger → Custom Event
- Event Name: `lead_submitted`

#### Publish

- Submit → Container Version → Publish

→ Damit kannst du auch **Google Ads Conversion**, **TikTok Pixel**, **LinkedIn Insight Tag** und beliebige weitere Tracking-Tags ohne Code-Änderung hinzufügen.

---

## Setup-Checkliste

- [ ] Meta Business Manager Account
- [ ] Meta Pixel erstellt + ID in HTML eingetragen
- [ ] CAPI Access Token generiert
- [ ] Make-Steps für Hash + CAPI POST eingefügt
- [ ] Test Event Code generiert
- [ ] End-to-End-Test: Lead → 1 deduped Event in Events Manager
- [ ] Pixel Helper zeigt Pixel + Lead Event grün
- [ ] Optional: GTM-Container live
- [ ] Optional: Google Ads Conversion Tag hinzugefügt

---

## Technische Eigenschaften

| Aspekt | Umsetzung |
|---|---|
| Conversion-Tracking | Pixel + CAPI mit Event-ID-Deduplication |
| iOS-14.5+ Kompatibilität | Server-Side Tracking als Fallback für Browser-Limits |
| Datenschutz | PII (E-Mail, Telefon) per SHA-256 vor Versand gehasht |
| Tag-Management | GTM-Container für zentrale Pixel-Verwaltung |
| API-Integration | CAPI Direct-Call mit korrekter Payload-Struktur |

---

## Zeitaufwand: ~3 Stunden

**Nächster Schritt:** [07-streamlit-admin.md](07-streamlit-admin.md) — Streamlit Coach Admin Dashboard
