#!/bin/bash
# gemini_start.sh — Gemini CLI in Agent-Workflow integrieren
# Nutzung: ./gemini_start.sh [ISSUE_NR]

set -euo pipefail

AGENT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(python3 -c "import sys; sys.path.insert(0,'$AGENT_DIR'); import settings; print(settings.PROJECT_ROOT or '$AGENT_DIR/..')")"
CONTEXT_DIR="$PROJECT_ROOT/agent/data/contexts/open"

# Issue-Nummer: Argument oder erster offener Context
if [ -n "${1:-}" ]; then
    NR=$1
else
    NR=$(ls "$CONTEXT_DIR" 2>/dev/null | head -1 | cut -d'-' -f1)
fi

if [ -z "${NR:-}" ]; then
    echo "[!] Keine offene Issue gefunden."
    echo "    Erst ausführen: python3 agent_start.py --implement NR"
    exit 1
fi

# Context finden
STARTER=$(ls "$CONTEXT_DIR"/$NR-*/starter.md 2>/dev/null | head -1)
FILES=$(ls "$CONTEXT_DIR"/$NR-*/files.md 2>/dev/null | head -1)

if [ -z "${STARTER:-}" ]; then
    echo "[!] Kein Kontext für Issue #$NR gefunden."
    echo "    Erst ausführen: python3 agent_start.py --implement $NR"
    exit 1
fi

echo "========================================"
echo "  GEMINI AGENT — ISSUE #$NR"
echo "========================================"
echo "  Kontext: $STARTER"
[ -n "${FILES:-}" ] && echo "  Dateien:  $FILES"
echo "========================================"
echo ""
echo "  Hinweis nach Abschluss:"
echo "  python3 $AGENT_DIR/agent_start.py --pr $NR --branch \$(git -C $PROJECT_ROOT branch --show-current) --summary '...'"
echo "========================================"

# Gemini mit vollständigem Kontext starten
cd "$PROJECT_ROOT"
if [ -n "${FILES:-}" ]; then
    gemini "@$STARTER @$FILES Lies beide Dateien. Implementiere das Issue. Committe nach jeder Dateiänderung. Führe am Ende den PR-Befehl aus der oben angezeigt wurde aus."
else
    gemini "@$STARTER Lies die Datei. Implementiere das Issue. Committe nach jeder Dateiänderung. Führe am Ende den PR-Befehl aus der oben angezeigt wurde aus."
fi
