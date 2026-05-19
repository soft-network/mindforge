# Dockerfile für MindForge Coach Admin Dashboard
# Optimiert für GCP Cloud Run Deployment

FROM python:3.12-slim

WORKDIR /app

# System deps minimal halten
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Dependencies first (Layer-Caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Cloud Run setzt PORT env automatisch (default 8080)
ENV PORT=8080
EXPOSE 8080

# Healthcheck endpoint via Streamlit's built-in /_stcore/health
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${PORT}/_stcore/health || exit 1

# Start Streamlit, bind to PORT env, headless mode
CMD streamlit run app.py \
    --server.port=${PORT} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --browser.gatherUsageStats=false
