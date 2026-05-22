# Meta Pixel + Conversion API

Dual-Tracking: client-side Pixel (via GTM) + server-side Conversion API
(via Make-Webhook), beide dedupliziert über dieselbe `event_id`.

---

## 1. Test-Pixel anlegen

1. `business.facebook.com` → **Events Manager** → **Connect Data Sources** → **Web** → **Meta Pixel**
2. Name: `MindForge Demo Pixel`
3. URL: `https://quiz.mindforge.demo` (GitHub-Pages-URL einsetzen)
4. Pixel-ID notieren — Format `123456789012345`
5. **Settings → Conversions API → Generate access token** → langlebigen Token erstellen
6. In `.env`:
   ```env
   META_PIXEL_ID=123456789012345
   META_ACCESS_TOKEN=EAA...
   META_TEST_EVENT_CODE=TEST12345
   ```

---

## 2. Automatic Advanced Matching (AAM) aktivieren

Events Manager → Pixel → **Settings → Automatic Advanced Matching: ON**.
Felder anhaken:
- E-Mail (em)
- Vorname (fn)
- Nachname (ln)
- Telefon (ph)
- Land (country)
- External ID (für `event_id`)

Damit sendet der client-side Pixel automatisch gehashte PII mit jedem
Event — das ist exakt was LLP nutzt (sichtbar im Pixel-Param
`cud[external_id]`).

---

## 3. Client-Side Pixel (in GTM)

→ siehe `01-gtm-container.md` §5.1 und §5.2

Wichtig: Beim `Lead`-Event **immer** das `eventID`-Argument mit
`{{DLV - event_id}}` mitgeben, sonst funktioniert die Server-Side-Deduplizierung nicht.

```js
fbq('track', 'Lead', {
  value: 0,
  currency: 'EUR',
  content_name: 'Quiz Submit',
  lead_score: {{DLV - score}}
}, { eventID: {{DLV - event_id}} });
```

---

## 4. Server-Side CAPI (in Make-Szenario #1)

→ Konfiguration im HTTP-Modul des Make-Szenarios, siehe
`make-bridge/01-quiz-submit-scenario.md` §6, Sub-Section **Meta CAPI**.

**Key Points:**
- Endpoint: `https://graph.facebook.com/v18.0/{PIXEL_ID}/events`
- Felder gehashed: `em`, `ph`, `fn`, `ln`, `country` → SHA-256 lower-case
- `event_id` muss identisch zum client-side Pixel sein
- `test_event_code` im Test-Mode → Events erscheinen im Test-Events-Tab statt in Produktion

---

## 5. Validierung der Deduplizierung

1. Quiz auf der lokalen Demo-URL durchspielen
2. **Meta Events Manager → Test Events**
3. Erwartet pro Submit zwei Zeilen:
   - `Lead` · `Browser` (client-side)
   - `Lead` · `Server` (CAPI)
4. Beide haben gleiche `event_id` → Meta zeigt **„Deduplicated ✓"**

Wenn nicht dedupliziert:
- Prüfen ob `event_id` in beiden Calls vorhanden
- Zeit-Differenz max. 7 Tage
- Test-Event-Code in beiden gesetzt (oder in beiden weggelassen)

---

## 6. Pixel-Quality-Score

Pixel-Quality wird von Meta automatisch bewertet. Ziel: **> 7/10**.

Hebel:
- AAM mit max. Feldern (gibt +2)
- CAPI mit `client_user_agent` + `client_ip_address` + Event-ID-Dedup (gibt +3)
- Kein Doppel-Fire desselben Events (gibt +1)
- `external_id` matching zwischen client + server (gibt +1)

---

## 7. Conversion-Object & Optimization

In Meta Ads Manager:
- **Custom Conversion** anlegen: „Hot Lead"
- Source: Pixel
- Rule: `Lead` mit `lead_score >= 70`
- Optimization-Event in Kampagnen: „Hot Lead" statt generisch „Lead"

→ Reduziert die Streuung, weil der Algorithmus nur noch auf qualifizierte
Leads optimiert (CAPI-Setup mit Custom Conversion auf Score-Threshold).
