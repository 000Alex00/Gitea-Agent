#!/usr/bin/env bash
# start_patch.sh — Startet den Patch-Modus (aktive Entwicklung).
#
# Stoppt Night-Service falls aktiv, führt Server-Neustart + Eval durch,
# startet gitea-agent-patch.service.
#
# Optionen:
#   --self   gitea-agent Eigenentwicklung (.env.agent, kein Eval)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NIGHT_SVC="gitea-agent-night"
PATCH_SVC="gitea-agent-patch"
SELF=0

for ARG in "$@"; do
    [ "$ARG" = "--self" ] && SELF=1
done

if [ "$SELF" -eq 1 ]; then
    echo "[→] Patch-Modus: gitea-agent Eigenentwicklung (--self)"
    export AGENT_ENV_FILE="$SCRIPT_DIR/.env.agent"
    cd "$SCRIPT_DIR"
    python3 agent_start.py --self --watch --patch &
    echo "[✓] gitea-agent Watch-Loop gestartet (PID $!)"
    echo "    Env: $AGENT_ENV_FILE"
    exit 0
fi

echo "[→] Starte Patch-Modus..."

# Night stoppen falls aktiv
if systemctl is-active --quiet "$NIGHT_SVC" 2>/dev/null; then
    echo "[→] Stoppe Night-Modus..."
    systemctl --user stop "$NIGHT_SVC"
    echo "[✓] Night-Modus gestoppt"
fi

# Server-Neustart (falls restart_script konfiguriert)
RESTART_SCRIPT=$(python3 -c "
import json
from pathlib import Path
cfg = Path('${SCRIPT_DIR}').parent / 'config/agent_eval.json'
try:
    print(json.load(open(cfg))['restart_script'])
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
systemctl --user start "$PATCH_SVC"
echo "[✓] Patch-Modus aktiv"
echo "    Service: $PATCH_SVC"
echo "    Logs:    journalctl -u $PATCH_SVC -f"
