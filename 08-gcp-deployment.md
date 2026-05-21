# Schritt 8 — GCP Deployment (Cloud Run + Cloud Function)

**Ziel:** Streamlit-App auf Cloud Run hosten + eine Cloud Function für E-Mail-Enrichment deployen.

**Schwerpunkte:** Containerisierung, Secret Management, Serverless für isolierte Aufgaben.

---

## Architektur

```
              ┌──────────────────────────────────┐
              │     Make Pipeline (existing)     │
              └──────┬───────────────────┬───────┘
                     │                   │
   HTTP POST email   │                   │  create lead
                     ▼                   ▼
         ┌────────────────────┐    [Airtable]
         │  GCP Cloud Function│        │
         │  enrich-email      │        │  read/write via API
         │  - personal vs biz │        │
         │  - score adjust    │        ▼
         └────────────────────┘    ┌────────────────────────┐
                                   │  GCP Cloud Run         │
                                   │  Streamlit Coach Admin │
                                   │  (auto-scale, HTTPS)   │
                                   └────────────────────────┘
```

**Free Tier (für die Demo völlig ausreichend):**
- Cloud Run: 2 Mio Requests/Monat, 360k vCPU-Sekunden, 180k GiB-Sekunden Memory
- Cloud Functions Gen2: 2 Mio Calls/Monat
- Artifact Registry: 0.5 GB Storage
- Egress: 1 GB/Monat in DACH-Region

---

## Voraussetzungen

### 1. gcloud CLI installieren

- **Windows:** https://cloud.google.com/sdk/docs/install#windows
- Nach Installation:
  ```bash
  gcloud auth login
  gcloud auth application-default login
  ```

### 2. Projekt anlegen

```bash
gcloud projects create mindforge-demo --name="MindForge Demo"
gcloud config set project mindforge-demo
```

### 3. Billing-Account verknüpfen

- In Cloud Console: https://console.cloud.google.com/billing
- Projekt `mindforge-demo` auswählen → Billing-Account verknüpfen
- (Free Tier ist aktiv, Belastung erst bei Überschreitung)

### 4. APIs aktivieren

```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    cloudfunctions.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com
```

---

## Teil 1: Secrets in Secret Manager

Statt Secrets im Build zu hardcoden, nutzen wir Cloud Secret Manager.

```bash
# Airtable Token
echo -n "patXXXXXXXX.YOUR_TOKEN" | gcloud secrets create AIRTABLE_API_TOKEN --data-file=-

# Airtable Base ID
echo -n "appXXXXXXXX" | gcloud secrets create AIRTABLE_BASE_ID --data-file=-

# Admin Password für Streamlit
echo -n "DeinSicheresPasswort!" | gcloud secrets create ADMIN_PASSWORD --data-file=-

# Service Account von Cloud Run berechtigen, Secrets zu lesen
PROJECT_NUMBER=$(gcloud projects describe mindforge-demo --format="value(projectNumber)")
SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

for SECRET in AIRTABLE_API_TOKEN AIRTABLE_BASE_ID ADMIN_PASSWORD; do
    gcloud secrets add-iam-policy-binding "$SECRET" \
        --member="serviceAccount:${SA}" \
        --role="roles/secretmanager.secretAccessor"
done
```

---

## Teil 2: Streamlit-App auf Cloud Run deployen

Das Dockerfile ist bereits in `streamlit-app/Dockerfile` vorhanden.

### Deployment-Script ausführen

```bash
cd C:\Users\msi\analyse\demo\gcp
bash deploy-streamlit.sh
```

→ Cloud Build baut den Container, deployed auf Cloud Run.
→ Output zeigt **Service URL**, z.B. `https://mindforge-coach-admin-XXXX-ew.a.run.app`

### Test

```bash
curl https://mindforge-coach-admin-XXXX-ew.a.run.app/_stcore/health
# → {"status": "ok"}
```

Im Browser: Service-URL öffnen → Login-Maske → Admin-Passwort → App läuft auf GCP.

### Custom Domain (optional)

```bash
gcloud beta run domain-mappings create \
    --service=mindforge-coach-admin \
    --domain=admin.mindforge.demo \
    --region=europe-west1
```

→ DNS-Records werden ausgegeben, die du beim Domain-Provider eintragen musst.

---

## Teil 3: Cloud Function für E-Mail-Enrichment

### Code-Ansicht

In `gcp/cloud-function/main.py`:
- HTTP-Endpoint, der POST mit E-Mail empfängt
- Klassifiziert Domain als personal (Gmail/Yahoo etc.) vs business
- Gibt Score-Adjustment zurück (-5 für privat, +10 für business, +20 für High-Value)

### Deployment

```bash
cd C:\Users\msi\analyse\demo\gcp
bash deploy-function.sh
```

### Test der deployten Function

```bash
curl -X POST https://enrich-email-XXXX-ew.a.run.app \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@acme.com"}'
```

Erwartete Antwort:
```json
{
  "email": "alice@acme.com",
  "domain": "acme.com",
  "is_business": true,
  "is_personal": false,
  "is_high_value": false,
  "type": "business",
  "score_adjustment": 10
}
```

Test mit Gmail-Adresse:
```bash
curl -X POST https://enrich-email-XXXX-ew.a.run.app \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@gmail.com"}'
```

→ `is_personal: true, score_adjustment: -5`

### Integration in Make

Im Make-Scenario, nach `Create Airtable Lead`:

1. **Add module: HTTP → Make a request**
2. **URL:** Cloud Function URL aus dem Deploy
3. **Method:** POST
4. **Body type:** JSON
5. **Request content:**
   ```json
   {"email": "{{1.email}}"}
   ```

6. **Add module: Airtable → Update Record**
   - Record ID: vorheriges Airtable-Modul
   - Notizen (oder neues Custom-Field): `"E-Mail type: " + {{HTTP_response.type}} + " | Score adj: " + {{HTTP_response.score_adjustment}}`
   - Lead Score: `{{current_score}} + {{HTTP_response.score_adjustment}}`

→ Damit beeinflusst die Cloud Function das Lead Scoring **in Echtzeit**.

---

## Monitoring der GCP-Services

In UptimeRobot ergänzen:
- Monitor 3: Cloud Run Streamlit URL → ping `/healthz` alle 5 Min
- Monitor 4: Cloud Function URL → POST mit Test-E-Mail alle 5 Min

→ Bei Ausfall: Slack-Alert + Statuspage-Update.

---

## Cost-Estimate (Free Tier sollte reichen)

| Service | Demo-Verbrauch | Free Tier | Kosten |
|---|---|---|---|
| Cloud Run (Streamlit) | ~100 Requests/Tag | 2 Mio/Monat | **€0** |
| Cloud Function | ~50 Calls/Tag | 2 Mio/Monat | **€0** |
| Cloud Build (initial Builds) | ~5 Builds | 120 Build-Min/Tag free | **€0** |
| Artifact Registry | ~200 MB | 0.5 GB free | **€0** |
| Secret Manager | 3 Secrets, ~100 Accesses | 6 Secret-Versionen + 10k Accesses free | **€0** |
| Egress | ~10 MB/Tag | 1 GB/Monat free | **€0** |
| **Gesamt** | | | **~€0/Monat** |

→ Solange du im Free Tier bleibst (was bei Demo-Traffic sicher der Fall ist), entstehen **keine Kosten**.

---

## Alternativen, falls GCP nicht zur Verfügung steht

**Variante B — Streamlit Cloud + Render.com:**
- Streamlit-App: deploy auf Streamlit Cloud (Free Tier)
- Cloud-Function-Equivalent: deploy als Web Service auf Render.com (Free Tier)

**Variante C — Azure:**
- Mit Universitäts-E-Mail: Azure for Students = $100 Credit ohne Kreditkarte
- Cloud-Run-Equivalent: Azure Container Apps
- Cloud-Function-Equivalent: Azure Functions

---

## Technische Eigenschaften

| Aspekt | Umsetzung |
|---|---|
| Cloud-Hosting | Cloud Run für Streamlit + Cloud Functions für Helper |
| Containerization | Dockerfile, Cloud Build automatisiert |
| Serverless | Cloud Function für isolierte Aufgabe (E-Mail-Enrichment) |
| Infrastructure-as-Code (light) | Versionierte Deploy-Skripte |
| Cost-Awareness | Free-Tier-bewusste Architektur |
| Production-Mindset | Secret Manager, Healthchecks, Multi-Service-Architektur |

---

## Zeitaufwand: ~5 Stunden

→ Damit ist der Demo-Stack komplett. Alle weiteren Schritte sind optional.
