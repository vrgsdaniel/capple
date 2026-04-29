# Infrastructure Scripts

## Prerequisites
- gcloud CLI installed and authenticated
- PROJECT_ID environment variable set

## Bootstrap (run once)
PROJECT_ID=capple-494416 ./scripts/setup.sh

## Environment variables required in Cloud Run
See .env.example at repo root for full list.

## Environment variables required in GitHub Secrets
- GCP_SA_KEY
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
