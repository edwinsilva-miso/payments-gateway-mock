#!/bin/bash

set -e

source secrets.sh

IMAGE_PATH="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${TAG}"

cd ..

echo "[INFO]: configuring docker"
gcloud auth configure-docker "${REGION}-docker.pkg.dev"

echo "[INFO]: building image"
docker build -t "${IMAGE_NAME}:${TAG}" .

echo "[INFO]: tagging image"
docker tag "${IMAGE_NAME}:${TAG}" "${IMAGE_PATH}"

echo "[INFO]: pushing image"
docker push "${IMAGE_PATH}"

echo "[INFO]: image successfully pushed to ${IMAGE_PATH}!"
