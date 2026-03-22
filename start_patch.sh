#!/usr/bin/env bash
# start_patch.sh — Startet den Patch-Modus (aktive Entwicklung).
#
# Stoppt Night-Service falls aktiv, führt Server-Neustart + Eval durch,
# startet gitea-agent-patch.service.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NIGHT_SVC="gitea-agent-night"
PATCH_SVC="gitea-agent-patch"

echo "[→] Starte Patch-Modus..."

# Night stoppen falls aktiv
if systemctl is-active --quiet "$NIGHT_SVC" 2>/dev/null; then
    echo "[→] Stoppe Night-Modus..."
    sudo systemctl stop "$NIGHT_SVC"
    echo "[✓] Night-Modus gestoppt"
fi

# Server-Neustart (falls restart_script konfiguriert)
RESTART_SCRIPT=$(python3 -c "
import json, sys
from pathlib import Path
for p in ['agent/config/agent_eval.json', 'tests/agent_eval.json']:
    cfg = Path('${SCRIPT_DIR}').parent / p
    if not cfg.exists():
        cfg = Path(sys.argv[1]) / p if len(sys.argv) > 1 else cfg
    try:
        print(json.load(open(cfg))['restart_script'])
        break
    except Exception:
        pass
" 2>/dev/null || true)

if [ -n "$RESTART_SCRIPT" ] && [ -x "$RESTART_SCRIPT" ]; then
    echo "[→] Server-Neustart via $RESTART_SCRIPT..."
    "$RESTART_SCRIPT"
    echo "[✓] Server neu gestartet"
fi

# Eval + Dashboard
echo "[→] Eval durchführen..."
cd "$SCRIPT_DIR"
python3 agent_start.py --eval-after-restart
python3 agent_start.py --dashboard
echo "[✓] Eval + Dashboard aktualisiert"

# Patch starten
sudo systemctl start "$PATCH_SVC"
echo "[✓] Patch-Modus aktiv"
echo "    Service: $PATCH_SVC"
echo "    Logs:    journalctl -u $PATCH_SVC -f"
