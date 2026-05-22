# Love Life Passport — External Security Assessment

**Scope:** Externes, rein passives Security Assessment der öffentlich
erreichbaren LLP-Infrastruktur. Vorgehen nach Industrie-Standards
(CVSS 3.1, STRIDE, OWASP ASVS L1, NIST SP 800-115 §4, RFC 9116) — als
eigenständige Audit-Komponente neben dem MindForge-Funnel-Demo.

---

## ⚠️ Scope-Disclaimer (wichtig!)

Dieses Assessment ist **rein passiv** durchgeführt:

- ✅ **erlaubt & durchgeführt:** OSINT, DNS-Queries, HTTP-Response-Header-Analyse,
  öffentlich abrufbares HTML/JS, Certificate-Transparency, Sitemap, robots.txt,
  öffentliche Datenbanken (HaveIBeenPwned-Range-API)
- ❌ **nicht durchgeführt:** Active Scanning (nmap aggressive, nikto, sqlmap,
  burp active), Credential-Brute-Force, Authentifizierungs-Bypass-Versuche,
  Payload-Injection, automatisierte Vulnerability-Scanner, Submit-Versuche
  am Quiz (würde Fake-Lead in LLPs HubSpot erzeugen)

**Rechtsgrundlage:** § 202a/b/c StGB ("Hackerparagraph") setzt ein
*Überwinden einer Zugangssicherung* bzw. *Ausspähen geschützter Daten* voraus.
Öffentlich abrufbare HTTP-Header und DNS-Records sind beides nicht.
Trotzdem würde ein echter Pentest erst nach schriftlicher Autorisierung
durch LLP (Letter of Authorization) durchgeführt — siehe [`04-disclosure-mail.md`](04-disclosure-mail.md).

---

## Inhalt

| Datei | Zweck |
|---|---|
| [`01-external-assessment.md`](01-external-assessment.md) | Roh-Befunde: Header, DNS, Tracking, Subdomain-Map |
| [`02-threat-model.md`](02-threat-model.md) | STRIDE-Threat-Model des LLP-Funnels |
| [`03-findings-report.md`](03-findings-report.md) | Konsolidierte Findings mit CVSS-Score + Fix |
| [`04-disclosure-mail.md`](04-disclosure-mail.md) | Responsible-Disclosure-Mail-Entwurf an LLP |

---

## Top-Findings (TL;DR)

| # | Finding | Severity | CVSS |
|---|---|---|---|
| F1 | DMARC-Policy `p=none` ohne Reporting — vollständiges E-Mail-Spoofing möglich | **HIGH** | 7.5 |
| F2 | Keine Content-Security-Policy (nur `frame-ancestors`) auf allen Funnel-Subdomains | **MEDIUM** | 6.1 |
| F3 | ClickFunnels-Webclass (`ateschthing.clickfunnels.com/llp-webclass`) komplett ohne Security-Header | **MEDIUM** | 5.4 |
| F4 | HSTS ohne `includeSubDomains` und `preload` auf Funnel-Builder-Subdomains | **MEDIUM** | 4.8 |
| F5 | Google-DKIM-Key nur 1024-bit RSA (Best Practice: ≥2048-bit) | **LOW** | 3.7 |
| F6 | Kein `/.well-known/security.txt` — kein definierter Disclosure-Channel (RFC 9116) | **LOW** | 2.0 |
| F7 | Information Disclosure via `x-lambda-id`, `x-wf-region`, `surrogate-key` (Webflow) | **INFO** | 0.0 |
| F8 | DSGVO-Risiko: Webflow hosting in `us-east-1` (Schrems-II-relevant) | **MEDIUM** | – |
| F9 | DSGVO-Risiko: HubSpot/GTM-Skripte werden im DOM vor Consent-Decision geladen (Pre-Consent-Loading) | **HIGH** | – |
| F10 | DSGVO-Risiko: HubSpot `__ptc.gif` Behavioral-Tracking mit Mauskoordinaten + CSS-Selectoren | **MEDIUM** | – |

---

## Methodik

Vorgehen nach **OWASP ASVS L1 Passive Checks** + **NIST SP 800-115 §4
(Information Gathering)** — beides sind die anerkannten Standards für
External Security Assessments im nicht-autorisierten Modus.

```
Phase 1: Footprinting           (passive DNS, WHOIS, crt.sh, sitemap)
Phase 2: Service Discovery       (HTTP-Header-Inspection, TLS-Profil)
Phase 3: Application Recon       (public HTML/JS, Tracking-IDs, Tech-Stack)
Phase 4: Threat Modeling         (STRIDE auf rekonstruierte Architektur)
Phase 5: Findings & Reporting    (CVSS 3.1 Scoring + Remediation)
Phase 6: Responsible Disclosure  (RFC 9116 + standardisierte Mail)
```

---

## Tools

Alle Tools sind passive Read-only-Tools — kein aktives Scanning:

- `curl -I` für HTTP-Header
- `nslookup -type=TXT/MX` für DNS-Records
- `crt.sh` Certificate Transparency (passive Subdomain-Enumeration)
- Manuelle Page-Source-Inspection (Chrome DevTools)
- Wayback Machine (historische Snapshots)
- CVSS 3.1 Calculator (FIRST.org)

---

## Stand

**Datum:** 2026-05-19
**Target:** lovelifepassport.com und alle bekannten Subdomains (Stand Mai 2026)
