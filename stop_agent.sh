#!/usr/bin/env bash
# stop_agent.sh — Stoppt alle Agent-Services → IDLE-Modus.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NIGHT_SVC="gitea-agent-night"
PATCH_SVC="gitea-agent-patch"
stopped=0

echo "[→] Stoppe Agent-Services..."

for svc in "$NIGHT_SVC" "$PATCH_SVC"; do
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        sudo systemctl stop "$svc"
        echo "[✓] $svc gestoppt"
        stopped=$((stopped + 1))
    fi
done

if [ "$stopped" -eq 0 ]; then
    echo "[✓] Kein aktiver Service — bereits IDLE"
fi

# Dashboard einmalig aktualisieren
cd "$SCRIPT_DIR"
python3 agent_start.py --dashboard 2>/dev/null && echo "[✓] Dashboard aktualisiert" || true

echo "[✓] Modus: IDLE"
