#!/bin/bash
# CruxBot ChromaDB Update Script
# Uploads a new chroma zip to GCP and replaces the existing data.
# Usage: bash scripts/update_chroma.sh <path_to_chroma.zip>
#
# Example:
#   bash scripts/update_chroma.sh ~/Downloads/chroma_fixed.zip

set -e

ZIP_PATH="${1}"
if [ -z "$ZIP_PATH" ]; then
  echo "Error: please provide path to chroma zip file."
  echo "Usage: bash scripts/update_chroma.sh <path_to_chroma.zip>"
  exit 1
fi

if [ ! -f "$ZIP_PATH" ]; then
  echo "Error: file not found: $ZIP_PATH"
  exit 1
fi

PROJECT="cs6120-lingyunxiao"
ZONE="us-west1-a"
VM_NAME="cruxbot-vm"

echo "==> Setting project to $PROJECT"
gcloud config set project $PROJECT

echo "==> Uploading $(basename $ZIP_PATH) ($(du -sh $ZIP_PATH | cut -f1))..."
gcloud compute scp --zone=$ZONE "$ZIP_PATH" $VM_NAME:~/chroma_update.zip

echo "==> Replacing ChromaDB on VM..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
  set -e
  echo '  Stopping app and streamlit...'
  cd ~/CruxBot && sudo docker compose stop app streamlit

  echo '  Extracting zip...'
  python3 -c \"import zipfile, os; zipfile.ZipFile(os.path.expanduser('~/chroma_update.zip')).extractall(os.path.expanduser('~/chroma_extracted'))\"

  echo '  Replacing data/chroma...'
  rm -rf ~/CruxBot/data/chroma
  mv ~/chroma_extracted/chroma ~/CruxBot/data/chroma
  rm -rf ~/chroma_extracted ~/chroma_update.zip

  echo '  New chroma size:' \$(du -sh ~/CruxBot/data/chroma | cut -f1)

  echo '  Restarting containers...'
  sudo docker compose up -d app streamlit
  sudo docker compose ps
"

echo ""
echo "=========================================="
echo "  ChromaDB updated!"
echo "  Streamlit UI : http://\$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='value(networkInterfaces[0].accessConfigs[0].natIP)'):8501"
echo "=========================================="
echo ""
echo "NOTE: First Streamlit request will trigger BM25 index rebuild (~30s)."
