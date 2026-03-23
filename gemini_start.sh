#!/usr/bin/env bash
# gemini_start.sh — Startet den Agent-Workflow mit Gemini.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

export MODEL="gemini-pro"

echo "[→] Starte Agent-Workflow mit Gemini..."
echo "    Modell: $MODEL"

cd "$SCRIPT_DIR"
python3 agent_start.py "$@"

echo "[✓] Gemini-Workflow beendet."
