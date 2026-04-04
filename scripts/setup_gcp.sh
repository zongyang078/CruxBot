#!/bin/bash
# CruxBot GCP VM Setup Script
# Usage: bash scripts/setup_gcp.sh

set -e

# ── Config ──────────────────────────────────────────────────────────────────
PROJECT="cs6120-lingyunxiao"
ZONE="us-west1-a"
VM_NAME="cruxbot-vm"
MACHINE_TYPE="g2-standard-4"
ACCELERATOR="type=nvidia-l4,count=1"
DISK_SIZE="100GB"
IMAGE_PROJECT="ubuntu-os-cloud"
IMAGE_FAMILY="ubuntu-2204-lts"
# ────────────────────────────────────────────────────────────────────────────

echo "==> Setting project to $PROJECT"
gcloud config set project $PROJECT

echo "==> Creating VM: $VM_NAME in $ZONE"
gcloud compute instances create $VM_NAME \
  --zone=$ZONE \
  --machine-type=$MACHINE_TYPE \
  --accelerator=$ACCELERATOR \
  --image-family=$IMAGE_FAMILY \
  --image-project=$IMAGE_PROJECT \
  --boot-disk-size=$DISK_SIZE \
  --maintenance-policy=TERMINATE \
  --tags=cruxbot \
  --metadata=install-nvidia-driver=True

echo "==> Creating firewall rules"
gcloud compute firewall-rules create cruxbot-ports \
  --allow=tcp:8080,tcp:8501 \
  --target-tags=cruxbot \
  --description="CruxBot FastAPI and Streamlit" 2>/dev/null || echo "Firewall rule already exists, skipping."

echo "==> Waiting 60s for VM to boot..."
sleep 60

echo "==> Installing NVIDIA driver, Docker + NVIDIA Container Toolkit on VM"
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
  set -e

  # NVIDIA driver (match current kernel, no kernel upgrade)
  sudo apt-get update -qq
  sudo apt-get install -y linux-headers-\$(uname -r)
  sudo apt-get install -y nvidia-driver-535 nvidia-dkms-535
  echo 'NVIDIA driver installed'

  # Docker
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker \$USER

  # NVIDIA Container Toolkit
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
  sudo apt-get update -qq
  sudo apt-get install -y nvidia-container-toolkit
  sudo nvidia-ctk runtime configure --runtime=docker
  sudo systemctl restart docker
  echo 'Docker + NVIDIA Container Toolkit ready'
"

echo "==> Rebooting VM to load NVIDIA driver..."
gcloud compute instances reset $VM_NAME --zone=$ZONE
echo "==> Waiting 90s for VM to come back up..."
sleep 90

echo "==> Uploading code to VM"
gcloud compute ssh $VM_NAME --zone=$ZONE --command="mkdir -p ~/CruxBot/data ~/CruxBot/src ~/CruxBot/scripts"

gcloud compute scp --recurse \
  --zone=$ZONE \
  app.py streamlit_app.py Dockerfile docker-compose.yml requirements.txt \
  $VM_NAME:~/CruxBot/

gcloud compute scp --recurse --zone=$ZONE src $VM_NAME:~/CruxBot/

echo "==> Uploading ChromaDB data (2.3GB, may take a few minutes)..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command="mkdir -p ~/CruxBot/data/chroma"
gcloud compute scp --recurse --zone=$ZONE data/chroma/ $VM_NAME:~/CruxBot/data/chroma/

echo "==> Building Docker images on VM"
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
  cd ~/CruxBot
  sudo docker compose build
"

echo "==> Starting Ollama and pulling llama3"
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
  cd ~/CruxBot
  sudo docker compose up -d ollama
  sleep 10
  sudo docker compose exec ollama ollama pull llama3
"

echo "==> Starting all services"
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
  cd ~/CruxBot
  sudo docker compose up -d
  sudo docker compose ps
"

EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format="value(networkInterfaces[0].accessConfigs[0].natIP)")

echo ""
echo "=========================================="
echo "  CruxBot is up!"
echo "  Streamlit UI : http://$EXTERNAL_IP:8501"
echo "  FastAPI      : http://$EXTERNAL_IP:8080"
echo "=========================================="
