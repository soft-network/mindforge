#!/usr/bin/env bash
# =============================================================================
# Deploy MindForge Coach Admin (Streamlit) to GCP Cloud Run
# =============================================================================
# Voraussetzungen:
#   - gcloud CLI installiert und authentifiziert
#   - Projekt bereits angelegt
#   - Cloud Build + Cloud Run + Artifact Registry APIs aktiviert
# =============================================================================

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-mindforge-demo}"
REGION="${GCP_REGION:-europe-west1}"
SERVICE_NAME="mindforge-coach-admin"
SOURCE_DIR="../streamlit-app"

echo "Deploying $SERVICE_NAME to $REGION in project $PROJECT_ID..."

# Build & deploy in one command — Cloud Run baut das Dockerfile automatisch
gcloud run deploy "$SERVICE_NAME" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --source="$SOURCE_DIR" \
    --platform=managed \
    --allow-unauthenticated \
    --port=8080 \
    --memory=512Mi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=3 \
    --timeout=300 \
    --set-secrets=AIRTABLE_API_TOKEN=AIRTABLE_API_TOKEN:latest \
    --set-secrets=AIRTABLE_BASE_ID=AIRTABLE_BASE_ID:latest \
    --set-secrets=ADMIN_PASSWORD=ADMIN_PASSWORD:latest

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --format='value(status.url)')

echo ""
echo "Deployed successfully!"
echo "Service URL: $SERVICE_URL"
echo ""
echo "Don't forget to add the URL to UptimeRobot monitoring."
