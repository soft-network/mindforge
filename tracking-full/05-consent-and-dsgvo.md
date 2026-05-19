# Consent & DSGVO

Wie das Quiz DSGVO-konform tracked, ohne externes CMP-Tool zu nutzen.

---

## 1. Default-State

Beim ersten Seitenladen (vor Consent-Decision):
- `gtag('consent', 'default', { ad_storage: 'denied', analytics_storage: 'denied', ... })`
- GTM hält alle Marketing-Tags zurück
- Functional/Security-Storage ist `granted` (= notwendige Cookies, z.B. Session-ID)

Implementation: `quiz-frontend/tracking/gtm-bootstrap.js`

---

## 2. Consent-Banner

`quiz-frontend/tracking/consent.js` rendert einen Banner mit zwei
Optionen: „Nur notwendige" / „Alle akzeptieren".

Bei „Alle akzeptieren":
- Cookie `mf_consent=granted` (180 Tage)
- `gtag('consent', 'update', { ad_storage: 'granted', ... })`
- DataLayer-Event `consent_granted`
- GTM-Tags feuern jetzt

Bei „Nur notwendige":
- Cookie `mf_consent=denied`
- Alle Marketing-Tags bleiben deaktiviert
- Trotzdem läuft der Quiz-Submit (HubSpot + Airtable) — denn das ist
  **Vertragserfüllung** (Lead möchte sein Ergebnis bekommen) und nicht
  Marketing.

---

## 3. Was sich bei „denied" trotzdem feuert

Auch wenn Consent denied:
- **Make-Webhook** wird gefeuert (Vertragserfüllung)
- **HubSpot-Contact** wird angelegt (Vertragserfüllung)
- **Airtable-Lead** wird angelegt (Vertragserfüllung)
- **CAPI / GA4 MP / TikTok Events API server-side** werden NICHT gefeuert
  (Marketing-Zwecke)
- **Client-side Pixel** werden NICHT gefeuert (gtag-Consent-Mode)

Im Make-Szenario erste Aktion: Filter `{{1.contact.consent}} = true` für
alle Pixel-Pfade. Bei `false`: nur HubSpot + Airtable.

---

## 4. Datenschutzerklärung

Nicht im Scope dieser Demo, aber für Produktion zwingend:
- DPA mit HubSpot abschließen (EU-Region wählen)
- DPA mit Meta (Conversions API → automatisch beim Token-Generieren)
- DPA mit Google (über Google Workspace)
- DPA mit TikTok
- DPA mit Make.com
- DPA mit Airtable

Alle Anbieter haben Standard-DPAs unter `<anbieter>/legal/dpa`.

---

## 5. Rechtsgrundlagen

| Aktion | Rechtsgrundlage |
|---|---|
| Quiz beantworten | Art. 6 (1)(a) DSGVO Einwilligung |
| Kontaktdaten speichern | Art. 6 (1)(b) DSGVO Vertragserfüllung („Ergebnis senden") |
| Marketing-Pixel feuern | Art. 6 (1)(a) DSGVO Einwilligung |
| HubSpot-Workflow (Email an Setter) | Art. 6 (1)(b) DSGVO Vertragserfüllung |
| Cold-Outreach via Aircall | Art. 6 (1)(a) DSGVO Einwilligung — Setter darf nur anrufen wenn Consent für „Kontaktaufnahme" gegeben |

Im Quiz-Kontaktformular ist `consent`-Checkbox **required** → der User
willigt explizit ein.

---

## 6. Recht auf Löschung

Wenn ein User die Löschung anfordert:
1. **HubSpot:** Contact löschen → setzt automatisch `GDPR-deleted = true` auf der Email-Hash
2. **Airtable:** manueller Lookup nach Email → Record löschen
3. **Meta:** Deletion-Request über CAPI mit `data_processing_options = ["LDU"]`
4. **Google:** GA4 User Deletion API
5. **TikTok:** Events API mit `event = 'UserDeletion'`

Phase E baut diesen Cleanup-Flow nicht aus. Für die Bewerbung als
„future work" erwähnt.
