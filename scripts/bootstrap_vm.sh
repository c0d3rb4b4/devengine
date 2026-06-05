#!/usr/bin/env bash
set -euo pipefail

if [[ $(id -u) -eq 0 ]]; then
  echo "Run this as your normal user, not root."
  exit 1
fi

sudo apt update && sudo apt upgrade -y
sudo apt install -y \
  ca-certificates \
  curl \
  git \
  unzip \
  jq \
  htop \
  ufw \
  build-essential \
  python3 \
  python3-venv \
  python3-pip \
  docker.io \
  docker-compose-v2

sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker "$USER"

echo
echo "VM bootstrap complete. Log out and back in so Docker group membership applies."
