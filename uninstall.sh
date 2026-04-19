#!/bin/bash

# Lucius Universal Uninstaller
# This script completely removes Lucius and its systemd service from the system.

set -e

INSTALL_DIR="/opt/lucius"
SERVICE_NAME="lucius.service"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}"

if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (e.g. sudo ./uninstall.sh)"
  exit 1
fi

echo "🗑️ Starting Lucius Uninstallation..."

# 1. Stop and disable the service
if systemctl is-active --quiet ${SERVICE_NAME}; then
    echo "🛑 Stopping ${SERVICE_NAME}..."
    systemctl stop ${SERVICE_NAME}
fi

if systemctl is-enabled --quiet ${SERVICE_NAME} 2>/dev/null; then
    echo "📴 Disabling ${SERVICE_NAME}..."
    systemctl disable ${SERVICE_NAME}
fi

# 2. Remove the service file
if [ -f "$SERVICE_FILE" ]; then
    echo "🗑️ Removing systemd service file..."
    rm -f "$SERVICE_FILE"
    systemctl daemon-reload
fi

# 3. Remove the installation directory
if [ -d "$INSTALL_DIR" ]; then
    echo "🗑️ Removing installation directory ($INSTALL_DIR)..."
    rm -rf "$INSTALL_DIR"
fi

echo ""
echo "✅ Lucius has been completely uninstalled from your system."
echo "If you ever want it back, you know where to find us!"
