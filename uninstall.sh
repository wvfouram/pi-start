#!/bin/bash
# Removes Start.
SRC="$(cd "$(dirname "$0")" && pwd)"
if [ "$(id -u)" = "0" ]; then
  echo "Run this as your normal user (not with sudo)."
  exit 1
fi

echo "==> Putting the raspberry menu back"
pkill -f /opt/pi-start/pi_start.py 2>/dev/null || true
if [ -f /opt/pi-start/setup_desktop.py ]; then
  python3 /opt/pi-start/setup_desktop.py --remove
fi

sudo rm -rf /opt/pi-start /usr/local/bin/pi-start /usr/share/applications/pi-start.desktop \
  /usr/share/icons/hicolor/scalable/apps/pi-start.svg
sudo update-desktop-database -q /usr/share/applications 2>/dev/null || true
echo "Start removed. Your settings are still in ~/.config/pi-start (delete that folder to remove them)."
