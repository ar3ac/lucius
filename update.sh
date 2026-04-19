#!/bin/bash

# Lucius Universal Updater
# This script securely updates Lucius to the latest version from GitHub.

set -e

INSTALL_DIR="/opt/lucius"
SERVICE_NAME="lucius.service"

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (e.g. sudo ./update.sh)"
  exit 1
fi

if [ ! -d "$INSTALL_DIR" ]; then
    echo "❌ Lucius is not installed in $INSTALL_DIR."
    exit 1
fi

echo "🔄 Starting Lucius Update..."

# 1. Stop the service
if systemctl is-active --quiet ${SERVICE_NAME}; then
    echo "🛑 Stopping ${SERVICE_NAME} to safely update files..."
    systemctl stop ${SERVICE_NAME}
fi

# 2. Git Pull latest changes
echo "📥 Pulling latest changes from GitHub..."
cd $INSTALL_DIR
git fetch origin main
git reset --hard origin/main

# 3. Update dependencies
echo "📦 Updating Python dependencies..."
source .venv/bin/activate
pip install -r requirements.txt

# 4. Restart the service
echo "🚀 Restarting ${SERVICE_NAME}..."
systemctl daemon-reload
systemctl start ${SERVICE_NAME}

echo ""
echo "✅ Lucius has been successfully updated to the latest version!"
