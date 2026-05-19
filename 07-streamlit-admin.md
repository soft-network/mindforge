# Schritt 7 — Streamlit Coach Admin Dashboard

**Ziel:** Ein internes Web-Tool, mit dem das Coach-Team Leads verwalten, KPIs sehen und Status manuell ändern kann.

**Wo Streamlit hier RICHTIG eingesetzt ist:** internes Dashboard mit Login — nicht öffentliche Landing Page.

---

## Was schon gebaut ist

In `streamlit-app/`:
- **[app.py](streamlit-app/app.py)** — Komplette Streamlit-App (~250 Zeilen)
- **[requirements.txt](streamlit-app/requirements.txt)** — Python-Dependencies
- **[.streamlit/config.toml](streamlit-app/.streamlit/config.toml)** — Theme + Server-Config
- **[.streamlit/secrets.toml.example](streamlit-app/.streamlit/secrets.toml.example)** — Template für Secrets
- **[Dockerfile](streamlit-app/Dockerfile)** — Für GCP Cloud Run Deployment

## Features

| Feature | Wo im Code |
|---|---|
| **Passwort-Login** | `app.py` → `check_password()` |
| **Airtable API-Integration** (pyairtable) | `app.py` → `load_leads()`, `load_programs()` |
| **Cache mit TTL** | `@st.cache_data(ttl=60)` |
| **3 Seiten Navigation** | Sidebar Radio |
| **KPI-Cards** (Today, Week, Hot Leads, Conversion) | `render_kpis()` |
| **Funnel-Chart** (Plotly) | `render_funnel_chart()` |
| **Source-Performance Chart** (Plotly) | `render_source_chart()` |
| **Filterable Lead-Liste** (Status, Source, Score, Search) | `render_lead_list()` |
| **Inline Lead-Editor** (Status, Score ändern) | `update_lead()` |
| **Manuelles Cache-Reload** | Sidebar Button |
| **Theme-Match zur Landing Page** | `config.toml` (selbe Primärfarbe) |

---

## Lokal starten

### 1. Python-Umgebung

```bash
cd C:\Users\msi\analyse\demo\streamlit-app
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 2. Secrets konfigurieren

```bash
cd .streamlit
copy secrets.toml.example secrets.toml
```

Dann `secrets.toml` öffnen und Werte einsetzen:
- `AIRTABLE_API_TOKEN` — aus airtable.com/create/tokens
- `AIRTABLE_BASE_ID` — aus der URL deiner Base (`appXXXXXXX`)
- `ADMIN_PASSWORD` — wähle ein starkes Passwort

### 3. Starten

```bash
cd ..   # zurück nach streamlit-app/
streamlit run app.py
```

→ Browser öffnet sich auf `http://localhost:8501`

### 4. Login testen

- Passwort eingeben (das aus secrets.toml)
- Du landest auf Dashboard mit KPIs + Charts
- Leads-Seite: Filter testen, einen Lead-Status ändern, speichern
- → in Airtable prüfen: Status wurde aktualisiert

---

## Deployment-Optionen

### Option A: Streamlit Cloud (kostenlos, einfach)

1. Push den `streamlit-app/` Ordner in dein GitHub Repo
2. Auf https://share.streamlit.io → "New App"
3. Repo + Branch + Main File: `streamlit-app/app.py`
4. **Secrets** im UI eintragen (Advanced settings):
   ```
   AIRTABLE_API_TOKEN = "..."
   AIRTABLE_BASE_ID = "..."
   ADMIN_PASSWORD = "..."
   ```
5. Deploy → ~3 Min später live unter `<name>.streamlit.app`

**Vorteil:** kostenlos, schnell, kein Docker
**Nachteil:** öffentliche URL, App schläft nach Inaktivität ein

### Option B: GCP Cloud Run (Phase D)

Siehe [08-gcp-deployment.md](08-gcp-deployment.md). Vorteile:
- Custom Domain möglich
- Skaliert auto
- Privater Endpoint möglich
- Schläft nicht ein (mit min-instances=1)

---

## Testing-Checklist

- [ ] Lokales Setup läuft
- [ ] Login funktioniert mit korrektem Passwort
- [ ] Login lehnt falsches Passwort ab
- [ ] Dashboard zeigt KPIs (auch wenn 0 Leads)
- [ ] Funnel-Chart rendert
- [ ] Source-Chart rendert
- [ ] Lead-Liste mit Filtern funktioniert
- [ ] Lead-Editor speichert Änderung zurück in Airtable
- [ ] Cache-Reload lädt frische Daten
- [ ] Programme-Seite zeigt alle Programme

---

## Architektur-Entscheidungen

| Entscheidung | Begründung |
|---|---|
| Streamlit statt React | Schnelle Entwicklung, Python-Stack passt zum Data-Flow, intern ausreichend |
| `pyairtable` statt direkter API | Robuster, Pagination integriert, weniger Boilerplate |
| `@st.cache_data(ttl=60)` | Reduziert API-Calls, API-Limit-Schutz, frische Daten gewährleistet |
| Simple Password statt OAuth | Demo-Setup; produktiv wäre Google OAuth via `streamlit-authenticator` |
| Plotly statt Streamlit-Charts | Interaktiver, exportierbar, professioneller Look |
| Dockerfile | Cloud-Run-ready, gleiche Umgebung lokal und in Produktion |

---

## Produktiv: Auth-Upgrade auf `streamlit-authenticator`

Für eine echte Produktion ersetzt du das simple Password-Gate durch
[`streamlit-authenticator`](https://github.com/mkhorasani/Streamlit-Authenticator)
— bcrypt-Hashing, Multi-User, Cookie-basierte Sessions, Logout-Button.

### Installation

```bash
pip install streamlit-authenticator==0.3.2
```

`requirements.txt` ergänzen:
```
streamlit-authenticator==0.3.2
```

### Patch in `app.py`

Ersetze `check_password()` durch:

```python
import streamlit_authenticator as stauth

def check_password():
    """Multi-user auth with bcrypt hashes + Cookie-Session."""
    credentials = {
        "usernames": {
            "coach1": {
                "email": "coach1@mindforge.demo",
                "name": "Coach One",
                "password": st.secrets["AUTH_HASH_COACH1"],
            },
            # weitere Coaches hier
        }
    }
    authenticator = stauth.Authenticate(
        credentials,
        cookie_name="mindforge_coach",
        key=st.secrets["AUTH_COOKIE_KEY"],
        cookie_expiry_days=7,
    )
    name, status, username = authenticator.login(location="main")
    if status is False:
        st.error("Falsches Passwort.")
        return False
    if status is None:
        st.warning("Bitte einloggen.")
        return False
    st.session_state["user"] = name
    authenticator.logout("Logout", "sidebar")
    return True
```

### Neue Secrets (`.streamlit/secrets.toml`)

```toml
AUTH_COOKIE_KEY = "ein-langer-zufaelliger-string"
AUTH_HASH_COACH1 = "$2b$12$..."   # bcrypt-Hash, generiert mit stauth.Hasher
```

### Hash erzeugen

```python
import streamlit_authenticator as stauth
hashed = stauth.Hasher(['DeinPasswort']).generate()
print(hashed[0])
```

→ Output in `secrets.toml` einsetzen.

### Was du gewinnst

| Feature | Demo (heute) | Mit `streamlit-authenticator` |
|---|---|---|
| User-Konzept | Ein gemeinsames Passwort | Multi-User mit Namen |
| Session-Persistenz | Browser-Tab | Cookie, 7 Tage |
| Audit | Nicht möglich | `st.session_state['user']` für Logs |
| Password-Storage | Klartext in `secrets.toml` | bcrypt-Hash |
| Logout | Tab schließen | Button in Sidebar |

→ Aufwand für Migration: ~1 Stunde (inkl. Hash-Generierung pro User).

---

## Technische Eigenschaften

| Aspekt | Umsetzung |
|---|---|
| Python-Stack | App in Streamlit + pyairtable |
| API-Konsum | Airtable REST API via pyairtable |
| Datenvisualisierung | Plotly Funnel + Source Chart |
| Authentifizierung | Session-State Passwort-Gate |
| Caching | `@st.cache_data` mit TTL |
| Containerisierung | Dockerfile mit Healthcheck |

---

## Zeitaufwand: ~5 Stunden (inkl. lokaler Test)

**Nächster Schritt:** [08-gcp-deployment.md](08-gcp-deployment.md) — Auf GCP Cloud Run deployen
