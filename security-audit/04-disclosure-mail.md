# 04 · Responsible Disclosure — Mail-Entwurf

Reiner Disclosure-Mail-Entwurf an LLP. Frei von außerhalb-Demo-Kontext;
zum Versand sind nur die Platzhalter in eckigen Klammern zu füllen.

Adressaten-Empfehlung:

| Adresse | Begründung |
|---|---|
| `kontakt@lovelifepassport.com` | Allgemeiner Eingang (steht im Impressum) |
| `datenschutz@lovelifepassport.com` | Falls vorhanden — DSGVO-Findings (F8/F9/F10) gehören hierhin |
| Alex Westhuis (CEO) per LinkedIn-Direct-Message | CEO-Fraud-Risiko (F1) ist *direkt* sein Problem |

---

## Mail-Entwurf

> **Betreff:** Externes Security Assessment lovelifepassport.com — Disclosure von 10 Findings (1 HIGH)
>
> Hallo Team Love Life Passport,
>
> ich bin [Vorname Nachname], freier Webentwickler / Sicherheits-interessiert.
> Im Rahmen eines passiven External Security Assessments eurer öffentlich
> erreichbaren Infrastruktur habe ich 10 Findings dokumentiert, davon
> 1 mit HIGH-Severity (CVSS 7.5):
>
> **F1: DMARC-Policy `p=none` ohne Reporting**
> → erlaubt vollständiges E-Mail-Spoofing eurer Domain
> → konkrete CEO-Fraud- und Lead-Phishing-Vektoren
> → Fix in 1h durch einen DNS-Eintrag
>
> Weitere 9 Findings (MEDIUM/LOW/INFO) in den Bereichen Content-Security-Policy,
> HSTS-Konfiguration, DKIM-Key-Stärke, DSGVO/Schrems-II, Behavioral-Tracking,
> und Compliance-Hygiene (RFC 9116).
>
> Vorgehen: rein **passiv** nach OWASP ASVS L1 Passive Checks + NIST SP 800-115 §4.
> Kein Active Scanning, kein Quiz-Submit, keine Auth-Tests, kein
> Reverse-Engineering von JS-Bundles. Alles aus öffentlich abrufbaren
> HTTP-Headern, DNS-Records, und sichtbarem HTML/JS.
>
> Den vollständigen Bericht mit CVSS-Scoring, STRIDE-Threat-Model und
> konkreten Fix-Vorschlägen schicke ich euch gerne per Mail oder verlinke
> ein privates GitHub-Repo — wie es euch lieber ist.
>
> Disclosure-Zeitfenster nach Industriestandard: **90 Tage** (Ablauf:
> [Datum + 90 Tage]). Nach Fix oder Ablauf veröffentliche ich den
> Bericht *nicht* öffentlich — nur Ihr und ich kennen die Findings.
>
> Falls eine Anerkennung gewünscht ist (Hall-of-Fame, monetär oder
> ähnliches), freue ich mich — Pflicht ist es nicht.
>
> Beste Grüße
> [Vorname Nachname]
> [Kontakt]
> [PGP-Key-Link falls vorhanden]

---

## 3. Optional — Vorschlag für autorisierten Mini-Pentest

Falls aus dem Disclosure-Kontakt ein Folgegespräch entsteht, hier ist ein
**Scope-of-Work-Vorschlag** für einen autorisierten Mini-Pentest
(~20-40 Stunden):

### Scope

| In Scope | Out of Scope |
|---|---|
| analyse.lovelifepassport.com (Quiz-Endpoint) | Mitarbeiter-Accounts, Phishing-Tests |
| strategie.lovelifepassport.com | Aircall-Audio-Inhalte |
| Make-Webhook-Endpoint (sofern URL bereitgestellt) | Production-DoS-Tests |
| HubSpot Form-Embeds | HubSpot-interne Mitarbeiter-Daten |
| Public JS-Bundle-Analyse | Source-Code-Repos |
| Power BI Public Embed URLs (sofern existent) | GCP-IAM (intern) |

### Methodik

1. **Authentication-Tests** auf Quiz-Submit (CSRF-Token, Rate-Limiting, Bot-Detection)
2. **Input-Validation-Tests** auf Quiz-Antwort-Felder (XSS, SQLi, Command Injection, SSRF)
3. **JS-Bundle Reverse Engineering** des Funnel-Builders (`onecdn.io/b/client/.../main.bundle.js`)
4. **API-Endpoint-Discovery** über Network-Inspection (Quiz-Submit, Tracking)
5. **HubSpot Form-ID Enumeration** (Brute-Force auf Form-Embed-URLs)
6. **Make-Webhook-Replay-Tests** (Idempotenz, Auth, Rate-Limit)
7. **Cross-Subdomain-Cookie-Leaks** (Funnel-Tracking-Cookies)
8. **DNS-Subdomain-Takeover-Tests** (passive Enumeration auf gelöschte CNAMEs)

### Deliverable

- Vollständiger Bericht in DIN-ISO-27001-A.12.6.1-konformem Format
- Reproducible Steps + Screenshots pro Finding
- CVSS-3.1-Scoring
- Risk-Acceptance-Empfehlung (Fix / Mitigate / Accept / Transfer)
- Re-Test nach Fix (1 Iteration inklusive)

### Rechtliches

- Schriftlicher Letter of Authorization (LoA) durch CEO oder CISO erforderlich
- NDA gegenseitig
- Festgehaltene Test-Fenster (z.B. außerhalb Sales-Peaks)
- Keine Veröffentlichung ohne Freigabe

---

## 4. PGP-Key-Stub (Empfehlung)

Für einen professionellen Disclosure-Workflow sollte LLP einen PGP-Key
hinterlegen. Optional, als Empfehlung:

```
$ gpg --keyserver hkps://keys.openpgp.org --search-keys security@lovelifepassport.com
```

Bei Fehlen: in security.txt das Feld `Encryption:` weglassen und
unverschlüsselt entgegennehmen ist akzeptabel für eine Coaching-Marke
dieser Größe.

---

## 5. Checklist vor Versand der Mail

- [ ] Vor- und Nachname eintragen
- [ ] Telefonnummer eintragen
- [ ] LinkedIn-URL eintragen
- [ ] GitHub-Repo-URL eintragen (öffentlich oder per Einladung)
- [ ] Disclosure-Frist (Datum + 90 Tage) ausrechnen und eintragen
- [ ] PGP-Key-Link einfügen (falls vorhanden)
- [ ] Anhang oder Repo-Link prüfen (alle 4 Markdown-Dateien aus `security-audit/`)
- [ ] Ton noch einmal querlesen — sachlich, nicht alarmistisch
- [ ] **NICHT** parallel an Sales-Team senden — direkter Kontakt zu CEO + Datenschutz ist richtig
- [ ] **NICHT** den Bericht parallel öffentlich machen (Twitter, LinkedIn-Post) — verletzt das Responsible-Disclosure-Prinzip
