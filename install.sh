#!/bin/bash

# Lucius Universal Installer
# This script installs Lucius on any Linux system (Ubuntu, Debian, Raspberry Pi OS, etc.)

set -e

# Configuration
INSTALL_DIR="/opt/lucius"
REPO_URL="https://github.com/ar3ac/lucius.git"

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (e.g. sudo ./install.sh)"
  exit 1
fi

echo "🚀 Starting Lucius Installation..."

# Install dependencies based on package manager
if command -v apt-get >/dev/null; then
    echo "📦 Installing system dependencies (apt)..."
    apt-get update
    apt-get install -y python3 python3-venv git curl
elif command -v dnf >/dev/null; then
    echo "📦 Installing system dependencies (dnf)..."
    dnf install -y python3 git curl
elif command -v pacman >/dev/null; then
    echo "📦 Installing system dependencies (pacman)..."
    pacman -Sy --noconfirm python git curl
else
    echo "⚠️ Unsupported package manager. Please ensure python3, python3-venv, and git are installed."
fi

# Clone the repository
if [ -d "$INSTALL_DIR" ]; then
    echo "🔄 Updating existing installation..."
    cd $INSTALL_DIR
    git pull
else
    echo "📥 Cloning repository..."
    git clone $REPO_URL $INSTALL_DIR
    cd $INSTALL_DIR
fi

# Setup Virtual Environment
echo "🐍 Setting up Python Virtual Environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Setup Security PIN
if [ ! -f ".env" ]; then
    echo ""
    echo "🔒 Security Setup"
    read -s -p "Enter a secure PIN to access Lucius: " LUCIUS_PIN
    echo ""
    echo "LUCIUS_PIN=$LUCIUS_PIN" > .env
    echo "✅ PIN saved to .env"
fi

# Setup Systemd Service
echo "⚙️ Configuring Systemd Service..."
SERVICE_FILE="/etc/systemd/system/lucius.service"

# Use the current user if running via sudo, otherwise fallback to root
TARGET_USER=${SUDO_USER:-root}

# Replace placeholders in lucius.service template
sed -e "s|__INSTALL_DIR__|$INSTALL_DIR|g" \
    -e "s|__USER__|$TARGET_USER|g" \
    lucius.service > $SERVICE_FILE

# Reload systemd and start service
systemctl daemon-reload
systemctl enable lucius
systemctl restart lucius

echo ""
echo "🎉 Lucius Installation Complete!"
echo "🌐 You can now access Lucius at: http://<your-server-ip>:8000"
echo "To check the service status, run: sudo systemctl status lucius"
