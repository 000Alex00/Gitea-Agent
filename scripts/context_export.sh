#!/bin/bash
# context_export.sh — LLM-agnostischer Kontext-Export + Dual-Repo-Unterstützung
#
# Nutzung:
#   ./context_export.sh NR              → plain text ausgeben (copy/paste)
#   ./context_export.sh NR gemini       → Gemini CLI direkt starten
#   ./context_export.sh NR file         → context_NR.md zum Hochladen erzeugen
#   ./context_export.sh NR --self       → gitea-agent Repo statt jetson-llm-chat
#   ./context_export.sh NR --self gemini
#   ./context_export.sh NR --self file

set -euo pipefail

AGENT_DIR="$(cd "$(dirname "$0")" && pwd)"

# --- Argumente parsen ---
NR=""
FORMAT="plain"
SELF=0

for ARG in "$@"; do
    case "$ARG" in
        --self) SELF=1 ;;
        gemini|file|plain) FORMAT="$ARG" ;;
        [0-9]*) NR="$ARG" ;;
    esac
done

if [ -z "$NR" ]; then
    echo "Nutzung: $0 NR [plain|gemini|file] [--self]"
    echo ""
    echo "  NR       Issue-Nummer"
    echo "  plain    Kontext im Terminal ausgeben (Standard)"
    echo "  gemini   Gemini CLI direkt starten"
    echo "  file     context_NR.md erzeugen (für Web-Chats)"
    echo "  --self   gitea-agent Repo statt jetson-llm-chat"
    exit 1
fi

# --- Projekt-Root bestimmen ---
if [ "$SELF" -eq 1 ]; then
    ENV_FILE="$AGENT_DIR/.env.agent"
    if [ ! -f "$ENV_FILE" ]; then
        echo "[!] .env.agent nicht gefunden: $ENV_FILE"
        exit 1
    fi
    PROJECT_ROOT="$(grep '^PROJECT_ROOT=' "$ENV_FILE" | cut -d= -f2)"
    GITEA_REPO="$(grep '^GITEA_REPO=' "$ENV_FILE" | cut -d= -f2)"
else
    ENV_FILE="$AGENT_DIR/.env"
    PROJECT_ROOT="$(python3 -c "import sys; sys.path.insert(0,'$AGENT_DIR'); import settings; print(settings.PROJECT_ROOT or '$AGENT_DIR/..')" 2>/dev/null || echo "$AGENT_DIR/..")"
    GITEA_REPO="$(grep '^GITEA_REPO=' "$ENV_FILE" | cut -d= -f2)"
fi

CONTEXT_DIR="$(grep '^CONTEXT_DIR=' "$ENV_FILE" 2>/dev/null | cut -d= -f2)"
if [ -z "${CONTEXT_DIR:-}" ]; then
    CONTEXT_DIR="$PROJECT_ROOT/agent/data/contexts/open"
fi

# --- Kontext finden ---
STARTER=$(ls "$CONTEXT_DIR"/$NR-*/starter.md 2>/dev/null | head -1)
FILES=$(ls "$CONTEXT_DIR"/$NR-*/files.md 2>/dev/null | head -1)

if [ -z "${STARTER:-}" ]; then
    echo "[!] Kein Kontext für Issue #$NR gefunden."
    if [ "$SELF" -eq 1 ]; then
        echo "    Erst ausführen: python3 $AGENT_DIR/agent_start.py --self --implement $NR"
    else
        echo "    Erst ausführen: python3 $AGENT_DIR/agent_start.py --implement $NR"
    fi
    exit 1
fi

# --- Branch aus starter.md extrahieren ---
BRANCH=$(grep -oP '(?<=Branch: )`?\K[^\`\n]+' "$STARTER" 2>/dev/null | head -1 || true)
if [ -z "${BRANCH:-}" ]; then
    BRANCH=$(grep -oP '(?<=branch: )[^\s]+' "$STARTER" 2>/dev/null | head -1 || true)
fi
if [ -z "${BRANCH:-}" ]; then
    BRANCH=$(grep -oP '(feat|fix|chore|docs)/[^\s`"]+' "$STARTER" 2>/dev/null | head -1 || true)
fi

# --- Feature-Branch erstellen ---
if [ -n "${BRANCH:-}" ]; then
    cd "$PROJECT_ROOT"
    if ! git show-ref --quiet refs/heads/"$BRANCH" 2>/dev/null; then
        echo "[→] Branch erstellen: $BRANCH"
        git checkout -b "$BRANCH" 2>/dev/null || git checkout "$BRANCH"
    else
        git checkout "$BRANCH" 2>/dev/null || true
    fi
    cd "$AGENT_DIR"
fi

# --- PR-Befehl zusammenbauen ---
if [ "$SELF" -eq 1 ]; then
    PR_CMD="cd $PROJECT_ROOT && GITEA_REPO=$GITEA_REPO python3 $AGENT_DIR/agent_start.py --self --pr $NR --branch ${BRANCH:-BRANCH} --summary \"...\""
else
    PR_CMD="cd $PROJECT_ROOT && python3 $AGENT_DIR/agent_start.py --pr $NR --branch ${BRANCH:-BRANCH} --summary \"...\""
fi

# --- Kontext zusammenbauen ---
PROMPT_HEADER="$(cat <<HEADER
========================================
  KONTEXT FÜR ISSUE #$NR
  Repo: $GITEA_REPO
  Branch: ${BRANCH:-unbekannt}
========================================

Du arbeitest auf Branch: ${BRANCH:-unbekannt}
NIEMALS auf main committen.
Nach jeder Dateiänderung: git add <datei> && git commit -m "..."
Arbeitsverzeichnis: $PROJECT_ROOT

========================================
  PR ERSTELLEN (nach Abschluss):
  $PR_CMD
========================================

HEADER
)"

# --- Format-Ausgabe ---
case "$FORMAT" in

    plain)
        echo "$PROMPT_HEADER"
        echo "--- starter.md ---"
        cat "$STARTER"
        if [ -n "${FILES:-}" ]; then
            echo ""
            echo "--- files.md ---"
            cat "$FILES"
        fi

        # Slice-Anforderungsschleife
        echo ""
        echo "=========================================="
        echo "  SLICE-MODUS — Zeile eingeben:"
        echo "  SLICE: datei.py:START-END   → Code laden"
        echo "  READY                       → Starten"
        echo "=========================================="
        while true; do
            printf "> "
            read -r INPUT
            if [ "$INPUT" = "READY" ] || [ -z "$INPUT" ]; then
                break
            fi
            SLICE=$(echo "$INPUT" | sed -n 's/^SLICE: //p')
            if [ -n "$SLICE" ]; then
                python3 "$AGENT_DIR/agent_start.py" ${SELF:+--self} --get-slice "$SLICE"
            fi
        done
        ;;

    gemini)
        echo "$PROMPT_HEADER"
        [ -n "${FILES:-}" ] && echo "  Dateien: $FILES"
        echo ""
        cd "$PROJECT_ROOT"
        INSTRUCTION="Du arbeitest auf Branch ${BRANCH:-unbekannt} in $PROJECT_ROOT. NIEMALS auf main committen. Nach jeder Dateiänderung committen. Am Ende diesen PR-Befehl ausführen: $PR_CMD"
        SLICE_HINT="files.md enthält nur Skelett. Fordere Code-Slices an mit: 'SLICE: datei.py:START-END'. Der Agent liefert den Zeilenbereich."
        INSTRUCTION="$INSTRUCTION $SLICE_HINT"
        if [ -n "${FILES:-}" ]; then
            gemini "@$STARTER @$FILES $INSTRUCTION"
        else
            gemini "@$STARTER $INSTRUCTION"
        fi
        ;;

    file)
        OUTFILE="$AGENT_DIR/context_${NR}.md"
        {
            echo "$PROMPT_HEADER"
            echo ""
            cat "$STARTER"
            if [ -n "${FILES:-}" ]; then
                echo ""
                echo "---"
                echo ""
                cat "$FILES"
            fi
            echo ""
            echo "---"
            echo ""
            cat <<'SLICEDOC'
## Slice-Workflow
files.md enthält nur Skelett — kein Volltext.
Fordere Slices explizit an:

  SLICE: datei.py:START-END

Beispiel:
  SLICE: agent_start.py:646-695

Der Betreuer liefert den exakten Zeilenbereich.
Starte die Implementierung erst wenn du alle nötigen Slices hast.
SLICEDOC
        } > "$OUTFILE"
        echo "[✓] Kontext-Datei erzeugt: $OUTFILE"
        echo "    → Datei in Web-Chat hochladen (GPT, Claude Web, Gemini Web)"
        echo "    → Anweisung: 'Lies die Datei und arbeite das Issue ab'"
        echo "    → Nach Session PR-Befehl manuell ausführen:"
        echo "       $PR_CMD"
        ;;
esac
