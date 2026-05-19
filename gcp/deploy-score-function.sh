#!/usr/bin/env bash
# =============================================================================
# Deploy Lead-Scoring Cloud Function to GCP
# =============================================================================
# Voraussetzungen:
#   - AIRTABLE_API_TOKEN und AIRTABLE_BASE_ID liegen im Secret Manager
#   - Service Account hat secretAccessor-Recht (siehe 08-gcp-deployment.md)
# =============================================================================

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-mindforge-demo}"
REGION="${GCP_REGION:-europe-west1}"
FUNCTION_NAME="score-lead"

cd "$(dirname "$0")/cloud-function-score"

echo "Deploying $FUNCTION_NAME to $REGION in project $PROJECT_ID..."

gcloud functions deploy "$FUNCTION_NAME" \
    --project="$PROJECT_ID" \
    --gen2 \
    --runtime=python312 \
    --region="$REGION" \
    --source=. \
    --entry-point=score_lead \
    --trigger-http \
    --allow-unauthenticated \
    --memory=256MB \
    --timeout=15s \
    --max-instances=10 \
    --set-secrets=AIRTABLE_API_TOKEN=AIRTABLE_API_TOKEN:latest,AIRTABLE_BASE_ID=AIRTABLE_BASE_ID:latest

FUNCTION_URL=$(gcloud functions describe "$FUNCTION_NAME" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --gen2 \
    --format='value(serviceConfig.uri)')

echo ""
echo "Deployed!"
echo "Function URL: $FUNCTION_URL"
echo ""
echo "Test mit:"
echo "curl -X POST $FUNCTION_URL -H 'Content-Type: application/json' -d '{\"lead_id\":\"recXXXXX\"}'"
echo ""
echo "Diese URL als HTTP-Modul in Make einbauen — direkt nach 'Create Airtable Lead'."
