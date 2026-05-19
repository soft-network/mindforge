#!/usr/bin/env bash
# =============================================================================
# Deploy Email-Enrichment Cloud Function to GCP
# =============================================================================

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-mindforge-demo}"
REGION="${GCP_REGION:-europe-west1}"
FUNCTION_NAME="enrich-email"

cd "$(dirname "$0")/cloud-function"

echo "Deploying $FUNCTION_NAME to $REGION..."

gcloud functions deploy "$FUNCTION_NAME" \
    --project="$PROJECT_ID" \
    --gen2 \
    --runtime=python312 \
    --region="$REGION" \
    --source=. \
    --entry-point=enrich_email \
    --trigger-http \
    --allow-unauthenticated \
    --memory=256MB \
    --timeout=10s \
    --max-instances=10

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
echo "curl -X POST $FUNCTION_URL -H 'Content-Type: application/json' -d '{\"email\":\"test@acme.com\"}'"
echo ""
echo "Diese URL kannst du jetzt in Make als HTTP-Modul aufrufen."
