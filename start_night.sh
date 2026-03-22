#!/usr/bin/env bash
# start_night.sh — Startet den Night-Modus (autonomer Betrieb).
#
# Stoppt Patch-Service falls aktiv, startet gitea-agent-night.service.
# Notebook kann danach zugeklappt werden.
set -euo pipefail

NIGHT_SVC="gitea-agent-night"
PATCH_SVC="gitea-agent-patch"

echo "[→] Starte Night-Modus..."

# Patch stoppen falls aktiv
if systemctl is-active --quiet "$PATCH_SVC" 2>/dev/null; then
    echo "[→] Stoppe Patch-Modus..."
    sudo systemctl stop "$PATCH_SVC"
    echo "[✓] Patch-Modus gestoppt"
fi

# Night starten
sudo systemctl start "$NIGHT_SVC"
echo "[✓] Night-Modus aktiv"
echo "    Service: $NIGHT_SVC"
echo "    Logs:    journalctl -u $NIGHT_SVC -f"
