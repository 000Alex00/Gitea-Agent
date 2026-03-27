#!/bin/bash
# context_export.sh — LLM-agnostischer Kontext-Export + Dual-Repo-Unterstützung
#
# Nutzung:
#   ./context_export.sh NR                   → plain text ausgeben (copy/paste)
#   ./context_export.sh NR llm [TASK]        → LLM-CLI aus llm_routing.json starten
#   ./context_export.sh NR file              → context_NR.md zum Hochladen erzeugen
#   ./context_export.sh NR --self            → gitea-agent Repo statt Projekt
#   ./context_export.sh NR --self llm [TASK]
#
# LLM-Routing: config/llm/routing.json — cli_cmd Feld pro Task.
# Ohne cli_cmd → Fehler mit Hinweis welches Feld fehlt.

set -euo pipefail

AGENT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# --- Argumente parsen ---
NR=""
FORMAT="plain"
LLM_TASK="implementation"
SELF=0

for ARG in "$@"; do
    case "$ARG" in
        --self) SELF=1 ;;
        llm)    FORMAT="llm" ;;
        file|plain) FORMAT="$ARG" ;;
        [0-9]*) NR="$ARG" ;;
        implementation|deep_coding|docs|log_analysis|healing|pr_review|test_generation)
                LLM_TASK="$ARG" ;;
    esac
done

if [ -z "$NR" ]; then
    echo "Nutzung: $0 NR [plain|llm [TASK]|file] [--self]"
    echo ""
    echo "  NR       Issue-Nummer"
    echo "  plain    Kontext im Terminal ausgeben (Standard)"
    echo "  llm      LLM-CLI aus llm_routing.json starten (TASK: implementation)"
    echo "  file     context_NR.md erzeugen (für Web-Chats)"
    echo "  --self   gitea-agent Repo statt Projekt"
    echo ""
    echo "  LLM-Tasks: implementation, deep_coding, docs, log_analysis, healing"
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
    CONTEXT_DIR="$PROJECT_ROOT/workspace/open"
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

    llm)
        # cli_cmd aus llm_routing.json lesen
        LLM_CMD=$(python3 "$AGENT_DIR/agent_start.py" ${SELF:+--self} --get-llm-cmd "$LLM_TASK" 2>/dev/null || true)
        if [ -z "${LLM_CMD:-}" ]; then
            echo "[✗] Kein cli_cmd für Task '$LLM_TASK' in llm_routing.json konfiguriert."
            echo "    Beispiel in config/llm/routing.json:"
            echo "      \"$LLM_TASK\": {\"provider\": \"deepseek\", \"model\": \"deepseek-chat\", \"cli_cmd\": \"lmstudio\"}"
            exit 1
        fi

        # Slice-Loop VOR dem LLM-Start
        echo "$PROMPT_HEADER"
        echo "--- starter.md ---"
        cat "$STARTER"
        if [ -n "${FILES:-}" ]; then
            echo ""
            echo "--- files.md ---"
            cat "$FILES"
        fi
        echo ""
        echo "=========================================="
        echo "  SLICE-MODUS — Zeile eingeben:"
        echo "  SLICE: datei.py:START-END   → Code laden"
        echo "  READY                       → LLM starten ($LLM_CMD)"
        echo "=========================================="
        SLICE_CONTENT=""
        while true; do
            printf "> "
            read -r INPUT
            if [ "$INPUT" = "READY" ] || [ -z "$INPUT" ]; then
                break
            fi
            SLICE=$(echo "$INPUT" | sed -n 's/^SLICE: //p')
            if [ -n "$SLICE" ]; then
                SLICE_OUT=$(python3 "$AGENT_DIR/agent_start.py" ${SELF:+--self} --get-slice "$SLICE" 2>/dev/null || echo "[Slice nicht gefunden: $SLICE]")
                echo "$SLICE_OUT"
                SLICE_CONTENT="$SLICE_CONTENT

--- SLICE: $SLICE ---
$SLICE_OUT"
            fi
        done

        # PFLICHTREGELN + vollständiger Prompt für LLM
        PFLICHTREGELN=$(python3 -c "
import sys; sys.path.insert(0,'$AGENT_DIR')
import os; os.environ.setdefault('AGENT_ENV_FILE','$AGENT_DIR/.env.agent')
import settings; print(settings.STARTER_MD_PFLICHTREGELN)
" 2>/dev/null || echo "NIEMALS auf main committen. NIEMALS curl statt agent_start.py. NIEMALS PR manuell erstellen.")

        LLM_PROMPT="$PFLICHTREGELN

$PROMPT_HEADER

--- starter.md ---
$(cat "$STARTER")
$([ -n "${FILES:-}" ] && echo "
--- files.md ---
$(cat "$FILES")" || true)
$SLICE_CONTENT

--- AUFGABE ---
Branch: ${BRANCH:-unbekannt}
Arbeitsverzeichnis: $PROJECT_ROOT
NIEMALS auf main committen.
Nach jeder Dateiänderung: git add <datei> && git commit -m \"...\"

PR-Befehl nach Abschluss:
$PR_CMD
"
        # Temporäre Prompt-Datei (für CLIs die Dateien lesen)
        PROMPT_FILE=$(mktemp /tmp/context_export_XXXXXX.md)
        echo "$LLM_PROMPT" > "$PROMPT_FILE"

        echo ""
        echo "[→] Starte LLM: $LLM_CMD  (Task: $LLM_TASK)"
        echo "    Prompt-Datei: $PROMPT_FILE"
        echo ""

        cd "$PROJECT_ROOT"
        # CLI starten — Argumente je nach Binary
        case "$LLM_CMD" in
            gemini)
                $LLM_CMD "@$PROMPT_FILE" ;;
            claude)
                $LLM_CMD --file "$PROMPT_FILE" 2>/dev/null || $LLM_CMD "@$PROMPT_FILE" ;;
            *)
                # Generisch: Prompt-Datei als erstes Argument
                $LLM_CMD "$PROMPT_FILE" ;;
        esac

        rm -f "$PROMPT_FILE"
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
