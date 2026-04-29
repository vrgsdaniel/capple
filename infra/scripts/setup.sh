#!/bin/bash
# Capple GCP setup script
# Run once to bootstrap the project
# Usage: PROJECT_ID=capple-494416 ./setup.sh

set -e

echo "Setting up GCP project: $PROJECT_ID"

# Enable APIs
gcloud services enable run.googleapis.com --project=$PROJECT_ID
gcloud services enable artifactregistry.googleapis.com --project=$PROJECT_ID
gcloud services enable calendar-json.googleapis.com --project=$PROJECT_ID

# Artifact Registry
gcloud artifacts repositories create capple \
  --repository-format=docker \
  --location=europe-west1 \
  --project=$PROJECT_ID

# Service account
gcloud iam service-accounts create capple-github-actions \
  --project=$PROJECT_ID \
  --display-name="Capple GitHub Actions"

# IAM roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:capple-github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:capple-github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:capple-github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:capple-github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Cloud Run IAM - allow unauthenticated
gcloud run services add-iam-policy-binding capple-backend \
  --region=europe-west1 \
  --project=$PROJECT_ID \
  --member="allUsers" \
  --role="roles/run.invoker"

# Generate service account key
gcloud iam service-accounts keys create key.json \
  --iam-account=capple-github-actions@$PROJECT_ID.iam.gserviceaccount.com

echo "Done. Copy key.json to GitHub secrets as GCP_SA_KEY then delete it."
