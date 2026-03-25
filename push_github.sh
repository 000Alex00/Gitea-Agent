#!/bin/bash
# push_github.sh — Pusht main auf Gitea (origin) + GitHub Mirror
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Token aus .env.agent laden
if [ -f "$SCRIPT_DIR/.env.agent" ]; then
    export $(grep -E "^GITHUB_TOKEN=|^GITHUB_REPO=" "$SCRIPT_DIR/.env.agent" | xargs)
fi

if [ -z "$GITHUB_TOKEN" ] || [ -z "$GITHUB_REPO" ]; then
    echo "[!] GITHUB_TOKEN oder GITHUB_REPO fehlt in .env.agent"
    exit 1
fi

BRANCH="${1:-main}"
GITHUB_URL="${GITHUB_REPO/https:\/\//https://Alexander-Benesch:${GITHUB_TOKEN}@}"

echo "[→] Push → origin ($BRANCH)..."
git push origin "$BRANCH"

echo "[→] Push → GitHub ($BRANCH)..."
git push "$GITHUB_URL" "$BRANCH"

echo "[✓] Beide Remotes aktuell"
