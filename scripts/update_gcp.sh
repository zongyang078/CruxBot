#!/bin/bash
# CruxBot GCP VM Update Script
# Starts the stopped VM, uploads changed code, rebuilds and restarts containers.
# Usage: bash scripts/update_gcp.sh

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

echo "==> Uploading updated source files..."
gcloud compute scp --zone=$ZONE \
  requirements.txt \
  streamlit_app.py \
  $VM_NAME:~/CruxBot/

gcloud compute scp --recurse --zone=$ZONE src/ $VM_NAME:~/CruxBot/src/
gcloud compute scp --recurse --zone=$ZONE scripts/ $VM_NAME:~/CruxBot/scripts/

echo "==> Rebuilding and restarting containers..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
  cd ~/CruxBot
  sudo docker compose build app streamlit
  sudo docker compose up -d
  sudo docker compose ps
"

EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format="value(networkInterfaces[0].accessConfigs[0].natIP)")

echo ""
echo "=========================================="
echo "  CruxBot updated!"
echo "  Streamlit UI : http://$EXTERNAL_IP:8501"
echo "  FastAPI      : http://$EXTERNAL_IP:8080"
echo "=========================================="
echo ""
echo "NOTE: First Streamlit request will trigger BM25 index build (~30s)."
