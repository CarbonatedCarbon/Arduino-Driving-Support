#!/usr/bin/env bash
# ==============================================================================
# ReverseCam Pi Deployment & Setup Script
# ==============================================================================
set -e

echo "[*] Updating apt and installing system Bluetooth dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv bluez libglib2.0-dev

echo "[*] Installing Python dependencies..."
pip3 install -r requirements.txt

echo "[*] Setting up systemd trigger..."
sudo cp deploy/reverse-cam.service /etc/systemd/system/reverse-cam.service
sudo systemctl daemon-reload
sudo systemctl enable reverse-cam.service

echo "[+] ReverseCam deployment setup complete!"
echo "    Start service with: sudo systemctl start reverse-cam.service"
echo "    Check logs with:    journalctl -u reverse-cam.service -f"
