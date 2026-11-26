#!/bin/bash
# Installer for Start (Windows 11 style) on Raspberry Pi
set -e
SRC="$(cd "$(dirname "$0")" && pwd)"
if [ "$(id -u)" = "0" ]; then
  echo "Run this as your normal user (not with sudo). It will ask for sudo when needed."
  exit 1
fi

echo "==> Installing packages"
sudo apt-get update || echo "   (apt update had errors, continuing)"
if ! sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-gtklayershell-0.1 xdg-utils; then
  for p in python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-gtklayershell-0.1 xdg-utils; do
    sudo apt-get install -y "$p" || echo "   (could not install $p)"
  done
fi
sudo apt-get install -y fonts-open-sans || echo "   (Open Sans font not available, using system font)"
for p in swaylock; do
  sudo apt-get install -y "$p" || echo "   ($p not available, skipping)"
done

echo "==> Installing app"
sudo install -d /opt/pi-start
sudo install -m 644 "$SRC/pi_start.py" /opt/pi-start/pi_start.py
printf '#!/bin/sh\nexec /usr/bin/python3 /opt/pi-start/pi_start.py "$@"\n' | sudo tee /usr/local/bin/pi-start >/dev/null
sudo chmod 755 /usr/local/bin/pi-start

echo "==> Adding menu entry and icon"
sudo install -D -m 644 "$SRC/pi-start.svg" /usr/share/icons/hicolor/scalable/apps/pi-start.svg
sudo gtk-update-icon-cache -f -t /usr/share/icons/hicolor >/dev/null 2>&1 || true
sudo tee /usr/share/applications/pi-start.desktop >/dev/null <<'DESK'
[Desktop Entry]
Type=Application
Name=Start
GenericName=Start menu
Comment=Windows 11 style Start menu
Exec=pi-start 
Icon=pi-start
Terminal=false
Categories=Utility;GTK;
StartupWMClass=pi-start
StartupNotify=false
NoDisplay=true
DESK
sudo update-desktop-database -q /usr/share/applications 2>/dev/null || true

echo "==> Replacing the raspberry menu with Start"
sudo install -m 644 "$SRC/setup_desktop.py" /opt/pi-start/setup_desktop.py
pkill -f /opt/pi-start/pi_start.py 2>/dev/null || true
python3 /opt/pi-start/setup_desktop.py
if [ -n "$WAYLAND_DISPLAY" ] || [ -n "$DISPLAY" ]; then
  (setsid pi-start --background >/dev/null 2>&1 &)
fi

echo
echo "Done. Click the new Start button on the taskbar or press the Super key."
