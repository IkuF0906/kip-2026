#!/bin/sh
# Oracle Cloud の VM（Ubuntu 24.04、E2.1.Micro）を最初に整えたときの手順。ubuntu ユーザーで1回だけ実行する。
# 使い方: sh setup.sh "<デプロイ用の公開鍵>"
set -eu

# メモリが 1GB しかないので、2GB のスワップを足す
if ! swapon --show | grep -q /swapfile; then
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap -q /swapfile
  sudo swapon /swapfile
  echo "/swapfile none swap sw 0 0" | sudo tee -a /etc/fstab >/dev/null
  echo "vm.swappiness=10" | sudo tee /etc/sysctl.d/99-swap.conf >/dev/null
  sudo sysctl -q -p /etc/sysctl.d/99-swap.conf
fi

# Docker を公式のリポジトリから入れる
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq
sudo apt-get install -y -qq ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $VERSION_CODENAME stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update -qq
sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker ubuntu

# コンテナのログがディスクを使い切らないよう、大きさを制限する
echo '{"log-driver": "json-file", "log-opts": {"max-size": "10m", "max-file": "3"}}' | sudo tee /etc/docker/daemon.json >/dev/null
sudo systemctl restart docker

# デプロイ用スクリプトを置き、デプロイ用の鍵ではそれしか実行できないようにする
sudo install -d -o ubuntu -g ubuntu /opt/drill
install -m 0755 deploy.sh /opt/drill/deploy.sh
if [ -n "${1:-}" ] && ! grep -qF "$1" ~/.ssh/authorized_keys; then
  echo "command=\"/opt/drill/deploy.sh\",restrict $1" >> ~/.ssh/authorized_keys
fi
