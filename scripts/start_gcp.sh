#!/bin/bash
# CruxBot GCP VM Start Script
# Starts the stopped VM and brings up all containers.
# Usage: bash scripts/start_gcp.sh

set -e

PROJECT="cs6120-lingyunxiao"
ZONE="us-west1-a"
VM_NAME="cruxbot-vm"

echo "==> Setting project to $PROJECT"
gcloud config set project $PROJECT

echo "==> Starting VM: $VM_NAME"
gcloud compute instances start $VM_NAME --zone=$ZONE

echo "==> Waiting 30s for VM to boot..."
sleep 30

echo "==> Starting containers..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
  cd ~/CruxBot && sudo docker compose up -d
  sudo docker compose ps
"

EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format="value(networkInterfaces[0].accessConfigs[0].natIP)")

echo ""
echo "=========================================="
echo "  CruxBot is up!"
echo "  Streamlit UI : http://$EXTERNAL_IP:8501"
echo "  FastAPI      : http://$EXTERNAL_IP:8080"
echo "=========================================="
