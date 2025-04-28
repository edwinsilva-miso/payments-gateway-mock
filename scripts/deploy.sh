#!/bin/bash

set -e

source secrets.sh

gcloud alpha run deploy "$IMAGE_NAME" \
  --image="$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/$IMAGE_NAME:$TAG" \
  --region="$REGION" \
  --platform=managed \
  --allow-unauthenticated \
  --port=5000 \
  --no-cache
