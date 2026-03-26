#!/usr/bin/env bash
# agent_status.sh — Zeigt aktiven Betriebsmodus + Status.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NIGHT_SVC="gitea-agent-night"
PATCH_SVC="gitea-agent-patch"

# --- Modus erkennen ---
mode="IDLE"
active_svc=""

if systemctl is-active --quiet "$NIGHT_SVC" 2>/dev/null; then
    mode="NIGHT"
    active_svc="$NIGHT_SVC"
elif systemctl is-active --quiet "$PATCH_SVC" 2>/dev/null; then
    mode="PATCH"
    active_svc="$PATCH_SVC"
fi

echo "=== Agent-Status ==="
echo "Modus:    $mode"

# --- Laufzeit ---
if [ -n "$active_svc" ]; then
    runtime=$(systemctl show "$active_svc" --property=ActiveEnterTimestamp --value 2>/dev/null || echo "")
    if [ -n "$runtime" ]; then
        echo "Seit:     $runtime"
        # Laufzeit berechnen
        start_ts=$(date -d "$runtime" +%s 2>/dev/null || echo "")
        if [ -n "$start_ts" ]; then
            now_ts=$(date +%s)
            diff=$((now_ts - start_ts))
            hours=$((diff / 3600))
            mins=$(( (diff % 3600) / 60 ))
            echo "Laufzeit: ${hours}h ${mins}m"
        fi
    fi
fi

# --- Letzter Eval-Score ---
echo ""
cd "$SCRIPT_DIR"
python3 -c "
import json
from pathlib import Path

# Pfade auflösen (neue Struktur → Legacy-Fallback)
candidates = []
try:
    from settings import PROJECT_ROOT
    if PROJECT_ROOT:
        candidates.append(Path(PROJECT_ROOT) / 'agent' / 'data' / 'score_history.json')
        candidates.append(Path(PROJECT_ROOT) / 'tests' / 'score_history.json')
except Exception:
    pass
candidates.append(Path('tests/score_history.json'))

for p in candidates:
    if p.exists():
        history = json.load(p.open())
        if history:
            last = history[-1]
            ts = last.get('timestamp', '?')[:16]
            score = last.get('score', '?')
            mx = last.get('max_score', '?')
            passed = '✅ PASS' if last.get('passed') else '❌ FAIL'
            print(f'Letzter Eval: {score}/{mx} {passed} ({ts})')
            if last.get('failed'):
                for f in last['failed']:
                    print(f'  ↳ FAIL: {f[\"name\"]}')
        break
else:
    print('Letzter Eval: keine Daten')
" 2>/dev/null || echo "Letzter Eval: nicht verfügbar"

# --- Offene Issues ---
echo ""
python3 -c "
import gitea_api as gitea
issues = gitea.get_issues(state='open')
auto = [i for i in issues if i['title'].startswith('[Auto')]
manual = [i for i in issues if not i['title'].startswith('[Auto')]
print(f'Offene Issues: {len(issues)} ({len(auto)} Auto, {len(manual)} manuell)')
for i in issues[:5]:
    labels = ', '.join(l['name'] for l in i.get('labels', []))
    lbl = f' [{labels}]' if labels else ''
    print(f'  #{i[\"number\"]:3d} {i[\"title\"][:60]}{lbl}')
if len(issues) > 5:
    print(f'  ... und {len(issues)-5} weitere')
" 2>/dev/null || echo "Offene Issues: nicht verfügbar"
