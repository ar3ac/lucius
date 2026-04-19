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

# Detect current owner of the directory to restore it later
CURRENT_OWNER=$(stat -c '%u:%g' $INSTALL_DIR)
echo "👤 Current directory owner detected as: $CURRENT_OWNER"

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

# 2. Backup user data
echo "💾 Backing up user configurations..."
cd $INSTALL_DIR
[ -f commands.json ] && cp commands.json commands.json.bak
[ -f settings.json ] && cp settings.json settings.json.bak

# 3. Git Pull latest changes
echo "📥 Pulling latest changes from GitHub..."
git fetch origin main
git reset --hard origin/main

# 4. Restore user data
echo "♻️ Restoring user configurations..."
[ -f commands.json.bak ] && mv commands.json.bak commands.json
[ -f settings.json.bak ] && mv settings.json.bak settings.json

# 5. Restore permissions for the web app
echo "🔑 Restoring ownership to $CURRENT_OWNER..."
chown -R $CURRENT_OWNER $INSTALL_DIR

# 6. Update dependencies
echo "📦 Updating Python dependencies..."
source .venv/bin/activate
pip install -r requirements.txt

# 4. Restart the service
echo "🚀 Restarting ${SERVICE_NAME}..."
systemctl daemon-reload
systemctl start ${SERVICE_NAME}

echo ""
echo "✅ Lucius has been successfully updated to the latest version!"
