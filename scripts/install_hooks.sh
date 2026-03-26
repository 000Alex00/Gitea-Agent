#!/bin/bash
# install_hooks.sh — Installiert git hooks für gitea-agent
# Aufruf: bash scripts/install_hooks.sh

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOKS_DIR="$REPO_DIR/.git/hooks"

echo "Installiere git hooks in $HOOKS_DIR ..."

# pre-commit: Skeleton vor jedem Commit neu bauen
cat > "$HOOKS_DIR/pre-commit" << 'HOOK'
#!/bin/bash
# Skeleton vor jedem Commit neu bauen und stagen
cd /home/ki02/gitea-agent
python3 agent_start.py --self --build-skeleton 2>/dev/null
git add repo_skeleton.json repo_skeleton.md 2>/dev/null
exit 0
HOOK
chmod +x "$HOOKS_DIR/pre-commit"
echo "  ✅ pre-commit gesetzt"

echo "Fertig."
