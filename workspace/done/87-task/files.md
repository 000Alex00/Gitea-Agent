# Dateien — Issue #87
> Skelett-Modus aktiv — **kein Volltext**. Nutze `--get-slice datei.py:START-END` für Code-Details.
> Automatisch erkannt via Backtick-Erwähnungen, Import-Analyse (AST) und Keyword-Suche (grep).

# Repo-Skelett

## agent_self_check.py  *(206 Zeilen)*

- **Funktion** `check_labels` Zeilen 11-28
  `def check_labels() -> Tuple[bool, str]:`
- **Funktion** `check_flags` Zeilen 31-88
  `def check_flags() -> Tuple[bool, str]:`
- **Funktion** `check_required_fields` Zeilen 91-106
  `def check_required_fields() -> Tuple[bool, str]:`
- **Funktion** `check_env_sync` Zeilen 109-133
  `def check_env_sync() -> Tuple[bool, str]:`
- **Funktion** `check_test_tags` Zeilen 136-165
  `def check_test_tags() -> Tuple[bool, str]:`
- **Funktion** `run` Zeilen 168-202
  `def run() -> None:`

## agent_status.sh  *(91 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## stop_agent.sh  *(28 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## start_patch.sh  *(71 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## project.template.json  *(14 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## push_github.sh  *(26 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## agent_start.py  *(zu groß — Datei zu groß (141KB > 20KB))*

## gitea_api.py  *(425 Zeilen)*

- **Funktion** `_load_env` Zeilen 36-57
  `def _load_env() -> dict:`
- **Funktion** `_make_auth` Zeilen 60-75
  `def _make_auth(user: str, token: str, prompt_fallback: bool = False) -> str:`
- **Funktion** `_request` Zeilen 91-122
  `def _request(method: str, path: str, data: dict | None = None, auth: str | None = None) -> dict | list | None:`
- **Funktion** `get_issue` Zeilen 129-140
  `def get_issue(number: int) -> dict:`
- **Funktion** `get_issues` Zeilen 143-161
  `def get_issues(label: str | None = None, state: str = "open") -> list:`
- **Funktion** `create_issue` Zeilen 164-182
  `def create_issue(title: str, body: str, label: str | None = None) -> dict:`
- **Funktion** `close_issue` Zeilen 185-188
  `def close_issue(number: int) -> None:`
- **Funktion** `update_issue` Zeilen 191-207
  `def update_issue(number: int, *, state: str | None = None, body: str | None = None) -> dict:`
- **Funktion** `get_comments` Zeilen 214-224
  `def get_comments(number: int) -> list:`
- **Funktion** `post_comment` Zeilen 227-248
  `def post_comment(number: int, body: str) -> dict:`
- **Funktion** `check_approval` Zeilen 251-283
  `def check_approval(number: int, blocked_label: str | None = None) -> bool:`
- **Funktion** `get_all_labels` Zeilen 290-298
  `def get_all_labels() -> dict:`
- **Funktion** `add_label` Zeilen 301-314
  `def add_label(number: int, label_name: str) -> None:`
- **Funktion** `remove_label` Zeilen 317-329
  `def remove_label(number: int, label_name: str) -> None:`
- **Funktion** `swap_label` Zeilen 332-343
  `def swap_label(number: int, remove: str, add: str) -> None:`
- **Funktion** `get_pr_for_branch` Zeilen 350-372
  `def get_pr_for_branch(branch: str, base: str | None = None) -> dict | None:`
- **Funktion** `get_file_contents` Zeilen 375-393
  `def get_file_contents(path: str, ref: str) -> str | None:`
- **Funktion** `create_pr` Zeilen 396-425
  `def create_pr(branch: str, title: str, body: str, base: str | None = None) -> dict:`

## agent_eval.template.json  *(86 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## dashboard.py  *(299 Zeilen)*

- **Funktion** `generate` Zeilen 139-295
  `def generate(project_root: Path):`

## settings.py  *(301 Zeilen)*

- **Funktion** `_env` Zeilen 16-25
  `def _env(key: str, default: str = "") -> str:`
- **Funktion** `_env_list` Zeilen 28-30
  `def _env_list(key: str, default: str) -> list[str]:`
- **Funktion** `_env_int` Zeilen 33-37
  `def _env_int(key: str, default: int) -> int:`
- **Funktion** `_env_bool` Zeilen 40-41
  `def _env_bool(key: str, default: bool = False) -> bool:`
- **Funktion** `_load_features` Zeilen 257-275
  `def _load_features() -> dict:`
- **Funktion** `_load_project_type` Zeilen 280-291
  `def _load_project_type() -> str:`

## evaluation.py  *(604 Zeilen)*

- **Klasse** `TestResult` Zeilen 42-57
  `class TestResult:`
- **Klasse** `EvalResult` Zeilen 61-72
  `class EvalResult:`
- **Funktion** `_ping` Zeilen 80-88
  `def _ping(url: str) -> bool:`
- **Funktion** `_chat` Zeilen 91-120
  `def _chat(server_url: str, endpoint: str, message: str, eval_user: str) -> str | None:`
- **Funktion** `_keywords_match` Zeilen 123-126
  `def _keywords_match(text: str, keywords: list[str]) -> bool:`
- **Funktion** `_categorize` Zeilen 129-159
  `def _categorize(`
- **Funktion** `_run_steps` Zeilen 162-237
  `def _run_steps(`
- **Funktion** `_resolve_path` Zeilen 240-258
  `def _resolve_path(project_root: Path, new_rel: str, legacy_rel: str) -> Path:`
- **Funktion** `_resolve_config` Zeilen 261-266
  `def _resolve_config(project_root: Path) -> Path:`
- **Funktion** `_load_config` Zeilen 269-275
  `def _load_config(project_root: Path) -> dict | None:`
- **Funktion** `_load_baseline` Zeilen 278-285
  `def _load_baseline(project_root: Path) -> float | None:`
- **Funktion** `_save_baseline` Zeilen 288-293
  `def _save_baseline(project_root: Path, score: float) -> None:`
- **Funktion** `_get_commit_hash` Zeilen 296-307
  `def _get_commit_hash() -> str:`
- **Funktion** `_save_score_history` Zeilen 310-346
  `def _save_score_history(project_root: Path, result: "EvalResult", trigger: str) -> None:`
- **Funktion** `run` Zeilen 354-525
  `def run(`
- **Funktion** `format_terminal` Zeilen 533-557
  `def format_terminal(r: EvalResult) -> str:`
- **Funktion** `format_gitea_comment` Zeilen 560-579
  `def format_gitea_comment(r: EvalResult) -> str:`
- **Funktion** `main` Zeilen 587-600
  `def main() -> None:`

## repo_skeleton.json  *(zu groß — Datei zu groß (39KB > 20KB))*

## start_night.sh  *(24 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## context_export.sh  *(206 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## log.py  *(67 Zeilen)*

- **Funktion** `setup` Zeilen 21-54
  `def setup(log_file: str = "gitea-agent.log", level: str = "INFO") -> None:`
- **Funktion** `get_logger` Zeilen 57-67
  `def get_logger(name: str) -> logging.Logger:`

## plugins/patch.py  *(200 Zeilen)*

- **Funktion** `_project_root` Zeilen 17-22
  `def _project_root() -> Path:`
- **Funktion** `_normalize_ws` Zeilen 32-34
  `def _normalize_ws(text: str) -> str:`
- **Funktion** `_parse_search_replace` Zeilen 37-83
  `def _parse_search_replace(text: str) -> list[dict]:`
- **Funktion** `_apply_patch` Zeilen 86-147
  `def _apply_patch(`
- **Funktion** `cmd_apply_patch` Zeilen 150-200
  `def cmd_apply_patch(number: int, dry_run: bool = False) -> None:`

## plugins/changelog.py  *(165 Zeilen)*

- **Funktion** `_project_root` Zeilen 16-21
  `def _project_root() -> Path:`
- **Funktion** `_git_log_since_tag` Zeilen 40-79
  `def _git_log_since_tag(cwd: Path) -> list[dict]:`
- **Funktion** `_classify_commit` Zeilen 82-93
  `def _classify_commit(subject: str) -> tuple[str, str]:`
- **Funktion** `_build_changelog_block` Zeilen 96-117
  `def _build_changelog_block(commits: list[dict], version: str, date: str) -> str:`
- **Funktion** `cmd_changelog` Zeilen 120-165
  `def cmd_changelog(version: str | None = None, update_file: bool = True) -> str:`

## scripts/agent_status.sh  *(91 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## scripts/stop_agent.sh  *(28 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## scripts/start_patch.sh  *(71 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## scripts/push_github.sh  *(26 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## scripts/start_night.sh  *(24 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## scripts/context_export.sh  *(206 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## data/doctor_last.json  *(46 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## tests/test_issue.py  *(149 Zeilen)*

- **Funktion** `_issue` Zeilen 12-13
  `def _issue(title="", labels=None):`
- **Funktion** `test_risk_level_bug` Zeilen 21-24
  `def test_risk_level_bug():`
- **Funktion** `test_risk_level_feature` Zeilen 27-29
  `def test_risk_level_feature():`
- **Funktion** `test_risk_level_enhancement` Zeilen 32-34
  `def test_risk_level_enhancement():`
- **Funktion** `test_risk_level_docs_keyword` Zeilen 37-40
  `def test_risk_level_docs_keyword():`
- **Funktion** `test_risk_level_default` Zeilen 43-45
  `def test_risk_level_default():`
- **Funktion** `test_risk_level_no_labels` Zeilen 48-50
  `def test_risk_level_no_labels():`
- **Funktion** `test_issue_type_bug` Zeilen 58-59
  `def test_issue_type_bug():`
- **Funktion** `test_issue_type_feature` Zeilen 62-63
  `def test_issue_type_feature():`
- **Funktion** `test_issue_type_enhancement` Zeilen 66-67
  `def test_issue_type_enhancement():`
- **Funktion** `test_issue_type_docs` Zeilen 70-71
  `def test_issue_type_docs():`
- **Funktion** `test_issue_type_default` Zeilen 74-75
  `def test_issue_type_default():`
- **Funktion** `test_branch_name_bug_prefix` Zeilen 83-85
  `def test_branch_name_bug_prefix():`
- **Funktion** `test_branch_name_feat_prefix` Zeilen 88-90
  `def test_branch_name_feat_prefix():`
- **Funktion** `test_branch_name_chore_prefix` Zeilen 93-95
  `def test_branch_name_chore_prefix():`
- **Funktion** `test_branch_name_docs_prefix` Zeilen 98-100
  `def test_branch_name_docs_prefix():`
- **Funktion** `test_branch_name_slug_length` Zeilen 103-107
  `def test_branch_name_slug_length():`
- **Funktion** `test_branch_name_umlaut_conversion` Zeilen 110-113
  `def test_branch_name_umlaut_conversion():`
- **Funktion** `test_branch_name_special_chars_removed` Zeilen 116-120
  `def test_branch_name_special_chars_removed():`
- **Funktion** `test_validate_comment_all_present` Zeilen 128-132
  `def test_validate_comment_all_present(capfd):`
- **Funktion** `test_validate_comment_missing_field` Zeilen 135-139
  `def test_validate_comment_missing_field(capfd):`
- **Funktion** `test_validate_comment_unknown_type` Zeilen 142-144
  `def test_validate_comment_unknown_type():`
- **Funktion** `test_validate_comment_case_insensitive` Zeilen 147-149
  `def test_validate_comment_case_insensitive():`

## tests/test_patch.py  *(152 Zeilen)*

- **Funktion** `test_normalize_ws_strips_trailing_spaces` Zeilen 20-21
  `def test_normalize_ws_strips_trailing_spaces():`
- **Funktion** `test_normalize_ws_crlf_to_lf` Zeilen 24-25
  `def test_normalize_ws_crlf_to_lf():`
- **Funktion** `test_normalize_ws_empty` Zeilen 28-29
  `def test_normalize_ws_empty():`
- **Funktion** `test_normalize_ws_no_change` Zeilen 32-33
  `def test_normalize_ws_no_change():`
- **Funktion** `test_parse_single_block` Zeilen 50-55
  `def test_parse_single_block():`
- **Funktion** `test_parse_multiple_blocks` Zeilen 58-62
  `def test_parse_multiple_blocks():`
- **Funktion** `test_parse_empty_text` Zeilen 65-66
  `def test_parse_empty_text():`
- **Funktion** `test_parse_no_py_header_ignored` Zeilen 69-71
  `def test_parse_no_py_header_ignored():`
- **Funktion** `test_parse_multiline_block` Zeilen 74-78
  `def test_parse_multiline_block():`
- **Funktion** `test_parse_incomplete_block_ignored` Zeilen 81-83
  `def test_parse_incomplete_block_ignored():`
- **Funktion** `_make_temp_py` Zeilen 91-98
  `def _make_temp_py(content: str) -> Path:`
- **Funktion** `test_apply_patch_happy_path` Zeilen 101-108
  `def test_apply_patch_happy_path(tmp_path, monkeypatch):`
- **Funktion** `test_apply_patch_search_not_found` Zeilen 111-117
  `def test_apply_patch_search_not_found(tmp_path, monkeypatch):`
- **Funktion** `test_apply_patch_file_not_found` Zeilen 120-125
  `def test_apply_patch_file_not_found(tmp_path, monkeypatch):`
- **Funktion** `test_apply_patch_dry_run` Zeilen 128-135
  `def test_apply_patch_dry_run(tmp_path, monkeypatch):`
- **Funktion** `test_apply_patch_syntax_error_rejected` Zeilen 138-144
  `def test_apply_patch_syntax_error_rejected(tmp_path, monkeypatch):`
- **Funktion** `test_apply_patch_creates_backup` Zeilen 147-152
  `def test_apply_patch_creates_backup(tmp_path, monkeypatch):`

## tests/score_history.json  *(26 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## tests/test_skeleton.py  *(121 Zeilen)*

- **Funktion** `test_extract_function` Zeilen 17-21
  `def test_extract_function():`
- **Funktion** `test_extract_class` Zeilen 24-27
  `def test_extract_class():`
- **Funktion** `test_extract_multiple` Zeilen 30-33
  `def test_extract_multiple():`
- **Funktion** `test_extract_syntax_error_returns_empty` Zeilen 36-38
  `def test_extract_syntax_error_returns_empty():`
- **Funktion** `test_extract_empty_string` Zeilen 41-42
  `def test_extract_empty_string():`
- **Funktion** `test_extract_line_numbers` Zeilen 45-51
  `def test_extract_line_numbers():`
- **Funktion** `test_extract_signature` Zeilen 54-58
  `def test_extract_signature():`
- **Funktion** `test_extract_async_function` Zeilen 61-64
  `def test_extract_async_function():`
- **Funktion** `test_skeleton_to_md_header` Zeilen 72-76
  `def test_skeleton_to_md_header():`
- **Funktion** `test_skeleton_to_md_function_entry` Zeilen 79-88
  `def test_skeleton_to_md_function_entry():`
- **Funktion** `test_skeleton_to_md_class_entry` Zeilen 91-99
  `def test_skeleton_to_md_class_entry():`
- **Funktion** `test_skeleton_to_md_truncated` Zeilen 102-105
  `def test_skeleton_to_md_truncated():`
- **Funktion** `test_skeleton_to_md_no_symbols` Zeilen 108-111
  `def test_skeleton_to_md_no_symbols():`
- **Funktion** `test_skeleton_to_md_multiple_files` Zeilen 114-121
  `def test_skeleton_to_md_multiple_files():`

## tests/test_changelog.py  *(97 Zeilen)*

- **Funktion** `test_classify_feat` Zeilen 17-18
  `def test_classify_feat():`
- **Funktion** `test_classify_fix` Zeilen 21-22
  `def test_classify_fix():`
- **Funktion** `test_classify_with_scope` Zeilen 25-28
  `def test_classify_with_scope():`
- **Funktion** `test_classify_breaking_change` Zeilen 31-34
  `def test_classify_breaking_change():`
- **Funktion** `test_classify_no_prefix` Zeilen 37-40
  `def test_classify_no_prefix():`
- **Funktion** `test_classify_empty` Zeilen 43-45
  `def test_classify_empty():`
- **Funktion** `test_classify_chore` Zeilen 48-51
  `def test_classify_chore():`
- **Funktion** `test_classify_case_insensitive_prefix` Zeilen 54-56
  `def test_classify_case_insensitive_prefix():`
- **Funktion** `test_build_changelog_block_header` Zeilen 64-66
  `def test_build_changelog_block_header():`
- **Funktion** `test_build_changelog_block_feat_section` Zeilen 69-74
  `def test_build_changelog_block_feat_section():`
- **Funktion** `test_build_changelog_block_multiple_types` Zeilen 77-84
  `def test_build_changelog_block_multiple_types():`
- **Funktion** `test_build_changelog_block_other_section` Zeilen 87-91
  `def test_build_changelog_block_other_section():`
- **Funktion** `test_build_changelog_block_empty_commits` Zeilen 94-97
  `def test_build_changelog_block_empty_commits():`

## tests/test_settings.py  *(35 Zeilen)*

- **Funktion** `test_dashboard_path_is_absolute` Zeilen 10-11
  `def test_dashboard_path_is_absolute():`
- **Funktion** `test_dashboard_path_ends_with_html` Zeilen 14-15
  `def test_dashboard_path_ends_with_html():`
- **Funktion** `test_dashboard_path_inside_agent_or_root` Zeilen 18-21
  `def test_dashboard_path_inside_agent_or_root():`
- **Funktion** `test_all_paths_consistent` Zeilen 24-35
  `def test_all_paths_consistent():`


---

## agent_self_check.py  *(206 Zeilen)*
  - Funktion `check_labels` Zeilen 11-28  `def check_labels() -> Tuple[bool, str]:`
  - Funktion `check_flags` Zeilen 31-88  `def check_flags() -> Tuple[bool, str]:`
  - Funktion `check_required_fields` Zeilen 91-106  `def check_required_fields() -> Tuple[bool, str]:`
  - Funktion `check_env_sync` Zeilen 109-133  `def check_env_sync() -> Tuple[bool, str]:`
  - Funktion `check_test_tags` Zeilen 136-165  `def check_test_tags() -> Tuple[bool, str]:`
  - Funktion `run` Zeilen 168-202  `def run() -> None:`
> Volltext: `python3 agent_start.py --get-slice agent_self_check.py:1-206`

## agent_status.sh
```sh
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
```

## stop_agent.sh
```sh
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
        systemctl --user stop "$svc"
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
```

## start_patch.sh
```sh
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
systemctl --user start "$PATCH_SVC"
echo "[✓] Patch-Modus aktiv"
echo "    Service: $PATCH_SVC"
echo "    Logs:    journalctl -u $PATCH_SVC -f"
```

## project.template.json
```json
{
    "_comment": "Vorlage für project.json — nach agent/config/project.json kopieren und anpassen",
    "type": "web_api",
    "_comment_type": "Projekttyp: web_api | cli_tool | llm_chat | library | custom",
    "features": {
        "eval":         true,
        "health_checks": false,
        "auto_issues":  true,
        "changelog":    true,
        "watch":        true,
        "pr_workflow":  true
    },
    "_comment_features": "Fehlende project.json oder fehlende Einträge → alle Features aktiv (Rückwärtskompatibilität)"
}
```

## push_github.sh
```sh
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
```

## agent_start.py  *(3988 Zeilen)*
  - Funktion `_project_root` Zeilen 70-92  `def _project_root() -> Path:`
  - Funktion `risk_level` Zeilen 103-124  `def risk_level(issue: dict) -> tuple[int, str]:`
  - Funktion `issue_type` Zeilen 127-139  `def issue_type(issue: dict) -> str:`
  - Funktion `relevant_files` Zeilen 147-165  `def relevant_files(issue: dict) -> list[Path]:`
  - Funktion `find_relevant_files_advanced` Zeilen 168-194  `def find_relevant_files_advanced(issue: dict) -> list[Path]:`
  - Funktion `branch_name` Zeilen 197-225  `def branch_name(issue: dict) -> str:`
  - Funktion `build_plan_comment` Zeilen 233-279  `def build_plan_comment(issue: dict) -> str:`
  - Funktion `print_context` Zeilen 287-318  `def print_context(issue: dict) -> None:`
  - Funktion `_context_dir` Zeilen 326-336  `def _context_dir() -> Path:`
  - Funktion `_issue_dir` Zeilen 339-346  `def _issue_dir(issue: dict) -> Path:`
  - Funktion `_find_issue_dir` Zeilen 349-359  `def _find_issue_dir(number: int) -> Path | None:`
  - Funktion `_done_dir` Zeilen 362-366  `def _done_dir() -> Path:`
  - Funktion `save_plan_context` Zeilen 369-423  `def save_plan_context(issue: dict) -> Path:`
  - Funktion `save_tests_context` Zeilen 427-463  `def save_tests_context(issue: dict, files_dict: dict) -> tuple[Path, Path]:`
  - Funktion `save_implement_context` Zeilen 465-591  `def save_implement_context(issue: dict, files_dict: dict) -> tuple[Path, Path]:`
  - Funktion `_get_exclude_dirs` Zeilen 619-639  `def _get_exclude_dirs(project: Path) -> set[str]:`
  - Funktion `_extract_ast_symbols` Zeilen 665-687  `def _extract_ast_symbols(content: str) -> list[dict]:`
  - Funktion `_create_repo_skeleton` Zeilen 690-744  `def _create_repo_skeleton(files: list[Path], output_dir: Path, max_size_kb: int = _MAX_SKELETON_FILE_SIZE_KB) -> Path:`
  - Funktion `_skeleton_to_md` Zeilen 747-766  `def _skeleton_to_md(skeleton_data: list[dict]) -> str:`
  - Funktion `cmd_build_skeleton` Zeilen 769-777  `def cmd_build_skeleton() -> None:`
  - Funktion `_update_skeleton_incremental` Zeilen 780-812  `def _update_skeleton_incremental(changed_files: list[str]) -> None:`
  - Funktion `_load_skeleton_map` Zeilen 815-826  `def _load_skeleton_map(issue_dir: Path | None = None) -> dict:`
  - Funktion `_find_imports` Zeilen 829-869  `def _find_imports(files: list[Path], depth: int = 1) -> list[Path]:`
  - Funktion `_search_keywords` Zeilen 872-922  `def _search_keywords(issue_text: str, repo_path: Path) -> list[Path]:`
  - Funktion `_build_analyse_comment` Zeilen 930-1007  `def _build_analyse_comment(issue: dict, files: list[Path]) -> str:`
  - Funktion `_has_detailed_plan` Zeilen 1015-1034  `def _has_detailed_plan(number: int) -> bool:`
  - Funktion `_parse_diff_changed_lines` Zeilen 1042-1073  `def _parse_diff_changed_lines(branch: str) -> dict[str, list[int]]:`
  - Funktion `_warn_diff_out_of_scope` Zeilen 1076-1162  `def _warn_diff_out_of_scope(number: int, branch: str) -> None:`
  - Funktion `_warn_slices_not_requested` Zeilen 1165-1221  `def _warn_slices_not_requested(number: int, branch: str) -> None:`
  - Funktion `_check_pr_preconditions` Zeilen 1224-1370  `def _check_pr_preconditions(number: int, branch: str) -> None:`
  - Funktion `_validate_pr_completion` Zeilen 1373-1417  `def _validate_pr_completion(`
  - Funktion `_validate_comment` Zeilen 1420-1443  `def _validate_comment(body: str, comment_type: str, *, critical: bool = False) -> None:`
  - Funktion `_update_discussion` Zeilen 1446-1481  `def _update_discussion(issue: dict, starter_path: Path) -> None:`
  - Funktion `cmd_list` Zeilen 1489-1507  `def cmd_list() -> None:`
  - Funktion `cmd_plan` Zeilen 1510-1614  `def cmd_plan(number: int) -> None:`
  - Funktion `cmd_implement` Zeilen 1617-1760  `def cmd_implement(number: int) -> None:`
  - Funktion `_neustart_required` Zeilen 1773-1778  `def _neustart_required(changed_files: list[str]) -> str:`
  - Funktion `cmd_pr` Zeilen 1781-1946  `def cmd_pr(`
  - Funktion `cmd_generate_tests` Zeilen 1950-1975  `def cmd_generate_tests(number: int) -> None:`
  - Funktion `_current_issue_from_branch` Zeilen 1977-1992  `def _current_issue_from_branch() -> int | None:`
  - Funktion `_log_slice_request` Zeilen 1995-2016  `def _log_slice_request(spec: str) -> None:`
  - Funktion `cmd_get_slice` Zeilen 2019-2049  `def cmd_get_slice(spec: str) -> None:`
  - Funktion `cmd_fixup` Zeilen 2058-2102  `def cmd_fixup(number: int) -> None:`
  - Funktion `_auto_issue_exists` Zeilen 2110-2114  `def _auto_issue_exists(test_name: str) -> bool:`
  - Funktion `_auto_perf_issue_exists` Zeilen 2116-2120  `def _auto_perf_issue_exists(test_name: str) -> bool:`
  - Funktion `_auto_improvement_issue_exists` Zeilen 2124-2127  `def _auto_improvement_issue_exists(tag: str) -> bool:`
  - Funktion `_check_systematic_tag_failures` Zeilen 2129-2203  `def _check_systematic_tag_failures(project_root) -> None:`
  - Funktion `_sync_closed_contexts` Zeilen 2206-2231  `def _sync_closed_contexts() -> None:`
  - Funktion `_consecutive_passes_for_test` Zeilen 2234-2259  `def _consecutive_passes_for_test(test_name: str) -> int:`
  - Funktion `_close_resolved_auto_issues` Zeilen 2262-2341  `def _close_resolved_auto_issues(result: "evaluation.EvalResult") -> None:`
  - Funktion `_build_metadata` Zeilen 2344-2423  `def _build_metadata(`
  - Funktion `_session_path` Zeilen 2426-2428  `def _session_path() -> Path:`
  - Funktion `_session_load` Zeilen 2431-2455  `def _session_load() -> dict:`
  - Funktion `_session_increment` Zeilen 2458-2468  `def _session_increment() -> dict:`
  - Funktion `_session_status_line` Zeilen 2471-2484  `def _session_status_line(data: dict) -> str:`
  - Funktion `_format_history_block` Zeilen 2487-2523  `def _format_history_block(project_root: Path, n: int = 5) -> str:`
  - Funktion `_last_chat_inactive_minutes` Zeilen 2526-2574  `def _last_chat_inactive_minutes(log_path: str | Path) -> float | None:`
  - Funktion `_server_start_time` Zeilen 2577-2625  `def _server_start_time(log_path: str | Path) -> datetime.datetime | None:`
  - Funktion `_check_server_staleness` Zeilen 2628-2696  `def _check_server_staleness(branch: str, force: bool = False) -> None:`
  - Funktion `_restart_server_for_eval` Zeilen 2699-2721  `def _restart_server_for_eval() -> None:`
  - Funktion `_has_new_commits_since_last_eval` Zeilen 2724-2755  `def _has_new_commits_since_last_eval(project_root: Path) -> bool:`
  - Funktion `_wait_for_server` Zeilen 2758-2803  `def _wait_for_server(`
  - Funktion `cmd_eval_after_restart` Zeilen 2806-2868  `def cmd_eval_after_restart(number: int | None = None) -> None:`
  - Funktion `_ast_diff` Zeilen 2871-2911  `def _ast_diff(old_content: str, new_content: str) -> list[str]:`
  - Funktion `_gitea_version_compare` Zeilen 2914-2965  `def _gitea_version_compare(commit: str, changed_files: list[str]) -> str:`
  - Funktion `_build_auto_issue_body` Zeilen 2968-3083  `def _build_auto_issue_body(`
  - Funktion `cmd_watch` Zeilen 3086-3229  `def cmd_watch(interval_minutes: int = 60, patch_mode: bool = False) -> None:`
  - Funktion `_dashboard_event` Zeilen 3237-3244  `def _dashboard_event(context: str = "") -> None:`
  - Funktion `cmd_install_service` Zeilen 3270-3315  `def cmd_install_service() -> None:`
  - Funktion `cmd_dashboard` Zeilen 3323-3329  `def cmd_dashboard() -> None:`
  - Funktion `cmd_auto` Zeilen 3331-3423  `def cmd_auto() -> None:`
  - Funktion `_apply_auto_approve` Zeilen 3431-3459  `def _apply_auto_approve() -> None:`
  - Funktion `cmd_doctor` Zeilen 3466-3577  `def cmd_doctor() -> None:`
  - Funktion `cmd_setup` Zeilen 3584-3779  `def cmd_setup() -> None:`
  - Funktion `main` Zeilen 3782-3984  `def main():`
  - Funktion `_sym_map` Zeilen 2882-2884  `def _sym_map(content: str) -> dict[str, dict]:`
  - Funktion `_chk` Zeilen 3472-3473  `def _chk(name: str, status: str, detail: str = "", fix: str = "") -> None:`
  - Funktion `_ask` Zeilen 3588-3591  `def _ask(prompt: str, default: str = "") -> str:`
  - Funktion `_api_get_raw` Zeilen 3593-3600  `def _api_get_raw(url, user, token, path):`
  - Funktion `_api_post_raw` Zeilen 3602-3612  `def _api_post_raw(url, user, token, path, data: dict):`
  - Funktion `_len` Zeilen 2895-2900  `def _len(s: dict) -> int:`
> Volltext: `python3 agent_start.py --get-slice agent_start.py:1-3988`

## gitea_api.py  *(425 Zeilen)*
  - Funktion `_load_env` Zeilen 36-57  `def _load_env() -> dict:`
  - Funktion `_make_auth` Zeilen 60-75  `def _make_auth(user: str, token: str, prompt_fallback: bool = False) -> str:`
  - Funktion `_request` Zeilen 91-122  `def _request(method: str, path: str, data: dict | None = None, auth: str | None = None) -> dict | list | None:`
  - Funktion `get_issue` Zeilen 129-140  `def get_issue(number: int) -> dict:`
  - Funktion `get_issues` Zeilen 143-161  `def get_issues(label: str | None = None, state: str = "open") -> list:`
  - Funktion `create_issue` Zeilen 164-182  `def create_issue(title: str, body: str, label: str | None = None) -> dict:`
  - Funktion `close_issue` Zeilen 185-188  `def close_issue(number: int) -> None:`
  - Funktion `update_issue` Zeilen 191-207  `def update_issue(number: int, *, state: str | None = None, body: str | None = None) -> dict:`
  - Funktion `get_comments` Zeilen 214-224  `def get_comments(number: int) -> list:`
  - Funktion `post_comment` Zeilen 227-248  `def post_comment(number: int, body: str) -> dict:`
  - Funktion `check_approval` Zeilen 251-283  `def check_approval(number: int, blocked_label: str | None = None) -> bool:`
  - Funktion `get_all_labels` Zeilen 290-298  `def get_all_labels() -> dict:`
  - Funktion `add_label` Zeilen 301-314  `def add_label(number: int, label_name: str) -> None:`
  - Funktion `remove_label` Zeilen 317-329  `def remove_label(number: int, label_name: str) -> None:`
  - Funktion `swap_label` Zeilen 332-343  `def swap_label(number: int, remove: str, add: str) -> None:`
  - Funktion `get_pr_for_branch` Zeilen 350-372  `def get_pr_for_branch(branch: str, base: str | None = None) -> dict | None:`
  - Funktion `get_file_contents` Zeilen 375-393  `def get_file_contents(path: str, ref: str) -> str | None:`
  - Funktion `create_pr` Zeilen 396-425  `def create_pr(branch: str, title: str, body: str, base: str | None = None) -> dict:`
> Volltext: `python3 agent_start.py --get-slice gitea_api.py:1-425`

## agent_eval.template.json
```json
{
    "_comment": "Vorlage für agent_eval.json — nach agent/config/agent_eval.json kopieren und anpassen",
    "server_url": "http://localhost:8000",
    "chat_endpoint": "/chat",
    "secondary_url": "",
    "_comment_secondary": "Optional: URL eines sekundären Dienstes (z.B. DB, Cache, Worker). Tests mit secondary_required:true werden übersprungen wenn nicht erreichbar.",
    "log_path": "/path/to/your/app.log",
    "restart_script": "/path/to/your/start.sh",
    "inactivity_minutes": 5,
    "watch_interval_minutes": 60,
    "log_analysis_interval_minutes": 120,
    "tests": [
        {
            "name": "Basis-Antwort",
            "tag": "routing",
            "weight": 1,
            "secondary_required": false,
            "message": "Was ist 2 plus 2?",
            "expected_keywords": ["4"],
            "_comment": "Einfachster Test — Server erreichbar und antwortet"
        },
        {
            "name": "Mehrstufiger Dialog",
            "tag": "context",
            "weight": 2,
            "secondary_required": true,
            "_comment": "Nur ausführen wenn secondary_url erreichbar ist",
            "steps": [
                {
                    "message": "Mein Name ist TestUser",
                    "expect_stored": true,
                    "_comment": "Step 1: Information übergeben"
                },
                {
                    "message": "Wie heiße ich?",
                    "expected_keywords": ["TestUser"],
                    "_comment": "Step 2: Information abrufen"
                }
            ]
        },
        {
            "name": "Basis-Ton",
            "tag": "system_prompt",
            "weight": 1,
            "secondary_required": false,
            "message": "Hallo, wie geht es dir?",
            "expected_keywords": [],
            "_comment": "Prüft ob Server antwortet — expected_keywords projektspezifisch anpassen"
        }
    ],
    "improvement_hints": {
        "routing": {
            "hypothesis": "Anfragen werden falsch geroutet oder Server antwortet nicht",
            "levers": [
                "Server-Routing-Logik prüfen",
                "Timeout-Werte erhöhen",
                "Fallback-Handler prüfen"
            ],
            "affected_files": ["server.py", "router.py"],
            "_comment": "Dateipfade ans Projekt anpassen"
        },
        "context": {
            "hypothesis": "Kontext wird nicht korrekt gespeichert oder abgerufen",
            "levers": [
                "Persistenz-Mechanismus prüfen",
                "Retrieval-Parameter anpassen",
                "Chunk-Größe überprüfen"
            ],
            "affected_files": ["memory.py", "retrieval.py"],
            "_comment": "Dateipfade ans Projekt anpassen"
        },
        "system_prompt": {
            "hypothesis": "Systemkontext zu lang oder Instruktionen unklar",
            "levers": [
                "Systemprompt kürzen",
                "Explizite Instruktionen für Grenzfälle ergänzen",
                "Prompt auf Widersprüche prüfen"
            ],
            "affected_files": ["prompts/system.txt", "config.py"],
            "_comment": "Dateipfade ans Projekt anpassen"
        }
    },
    "context_loader": {
        "exclude_dirs": ["Backup", "Documentation", "node_modules", ".venv"]
    }
}
```

## dashboard.py  *(299 Zeilen)*
  - Funktion `generate` Zeilen 139-295  `def generate(project_root: Path):`
> Volltext: `python3 agent_start.py --get-slice dashboard.py:1-299`

## settings.py  *(301 Zeilen)*
  - Funktion `_env` Zeilen 16-25  `def _env(key: str, default: str = "") -> str:`
  - Funktion `_env_list` Zeilen 28-30  `def _env_list(key: str, default: str) -> list[str]:`
  - Funktion `_env_int` Zeilen 33-37  `def _env_int(key: str, default: int) -> int:`
  - Funktion `_env_bool` Zeilen 40-41  `def _env_bool(key: str, default: bool = False) -> bool:`
  - Funktion `_load_features` Zeilen 257-275  `def _load_features() -> dict:`
  - Funktion `_load_project_type` Zeilen 280-291  `def _load_project_type() -> str:`
> Volltext: `python3 agent_start.py --get-slice settings.py:1-301`

## evaluation.py  *(604 Zeilen)*
  - Klasse `TestResult` Zeilen 42-57  `class TestResult:`
  - Klasse `EvalResult` Zeilen 61-72  `class EvalResult:`
  - Funktion `_ping` Zeilen 80-88  `def _ping(url: str) -> bool:`
  - Funktion `_chat` Zeilen 91-120  `def _chat(server_url: str, endpoint: str, message: str, eval_user: str) -> str | None:`
  - Funktion `_keywords_match` Zeilen 123-126  `def _keywords_match(text: str, keywords: list[str]) -> bool:`
  - Funktion `_categorize` Zeilen 129-159  `def _categorize(`
  - Funktion `_run_steps` Zeilen 162-237  `def _run_steps(`
  - Funktion `_resolve_path` Zeilen 240-258  `def _resolve_path(project_root: Path, new_rel: str, legacy_rel: str) -> Path:`
  - Funktion `_resolve_config` Zeilen 261-266  `def _resolve_config(project_root: Path) -> Path:`
  - Funktion `_load_config` Zeilen 269-275  `def _load_config(project_root: Path) -> dict | None:`
  - Funktion `_load_baseline` Zeilen 278-285  `def _load_baseline(project_root: Path) -> float | None:`
  - Funktion `_save_baseline` Zeilen 288-293  `def _save_baseline(project_root: Path, score: float) -> None:`
  - Funktion `_get_commit_hash` Zeilen 296-307  `def _get_commit_hash() -> str:`
  - Funktion `_save_score_history` Zeilen 310-346  `def _save_score_history(project_root: Path, result: "EvalResult", trigger: str) -> None:`
  - Funktion `run` Zeilen 354-525  `def run(`
  - Funktion `format_terminal` Zeilen 533-557  `def format_terminal(r: EvalResult) -> str:`
  - Funktion `format_gitea_comment` Zeilen 560-579  `def format_gitea_comment(r: EvalResult) -> str:`
  - Funktion `main` Zeilen 587-600  `def main() -> None:`
> Volltext: `python3 agent_start.py --get-slice evaluation.py:1-604`

## repo_skeleton.json
```json
[
  {
    "path": "agent_self_check.py",
    "truncated": false,
    "lines": 206,
    "size_kb": 6,
    "symbols": [
      {
        "type": "function",
        "name": "check_labels",
        "lines": "11-28",
        "signature": "def check_labels() -> Tuple[bool, str]:"
      },
      {
        "type": "function",
        "name": "check_flags",
        "lines": "31-88",
        "signature": "def check_flags() -> Tuple[bool, str]:"
      },
      {
        "type": "function",
        "name": "check_required_fields",
        "lines": "91-106",
        "signature": "def check_required_fields() -> Tuple[bool, str]:"
      },
      {
        "type": "function",
        "name": "check_env_sync",
        "lines": "109-133",
        "signature": "def check_env_sync() -> Tuple[bool, str]:"
      },
      {
        "type": "function",
        "name": "check_test_tags",
        "lines": "136-165",
        "signature": "def check_test_tags() -> Tuple[bool, str]:"
      },
      {
        "type": "function",
        "name": "run",
        "lines": "168-202",
        "signature": "def run() -> None:"
      }
    ]
  },
  {
    "path": "agent_start.py",
    "truncated": false,
    "lines": 3988,
    "size_kb": 141,
    "symbols": [
      {
        "type": "function",
        "name": "_project_root",
        "lines": "70-92",
        "signature": "def _project_root() -> Path:"
      },
      {
        "type": "function",
        "name": "risk_level",
        "lines": "103-124",
        "signature": "def risk_level(issue: dict) -> tuple[int, str]:"
      },
      {
        "type": "function",
        "name": "issue_type",
        "lines": "127-139",
        "signature": "def issue_type(issue: dict) -> str:"
      },
      {
        "type": "function",
        "name": "relevant_files",
        "lines": "147-165",
        "signature": "def relevant_files(issue: dict) -> list[Path]:"
      },
      {
        "type": "function",
        "name": "find_relevant_files_advanced",
        "lines": "168-194",
        "signature": "def find_relevant_files_advanced(issue: dict) -> list[Path]:"
      },
      {
        "type": "function",
        "name": "branch_name",
        "lines": "197-225",
        "signature": "def branch_name(issue: dict) -> str:"
      },
      {
        "type": "function",
        "name": "build_plan_comment",
        "lines": "233-279",
        "signature": "def build_plan_comment(issue: dict) -> str:"
      },
      {
        "type": "function",
        "name": "print_context",
        "lines": "287-318",
        "signature": "def print_context(issue: dict) -> None:"
      },
      {
        "type": "function",
        "name": "_context_dir",
        "lines": "326-336",
        "signature": "def _context_dir() -> Path:"
      },
      {
        "type": "function",
        "name": "_issue_dir",
        "lines": "339-346",
        "signature": "def _issue_dir(issue: dict) -> Path:"
      },
      {
        "type": "function",
        "name": "_find_issue_dir",
        "lines": "349-359",
        "signature": "def _find_issue_dir(number: int) -> Path | None:"
      },
      {
        "type": "function",
        "name": "_done_dir",
        "lines": "362-366",
        "signature": "def _done_dir() -> Path:"
      },
      {
        "type": "function",
        "name": "save_plan_context",
        "lines": "369-423",
        "signature": "def save_plan_context(issue: dict) -> Path:"
      },
      {
        "type": "function",
        "name": "save_tests_context",
        "lines": "427-463",
        "signature": "def save_tests_context(issue: dict, files_dict: dict) -> tuple[Path, Path]:"
      },
      {
        "type": "function",
        "name": "save_implement_context",
        "lines": "465-591",
        "signature": "def save_implement_context(issue: dict, files_dict: dict) -> tuple[Path, Path]:"
      },
      {
        "type": "function",
        "name": "_get_exclude_dirs",
        "lines": "619-639",
        "signature": "def _get_exclude_dirs(project: Path) -> set[str]:"
      },
      {
        "type": "function",
        "name": "_extract_ast_symbols",
        "lines": "665-687",
        "signature": "def _extract_ast_symbols(content: str) -> list[dict]:"
      },
      {
        "type": "function",
        "name": "_create_repo_skeleton",
        "lines": "690-744",
        "signature": "def _create_repo_skeleton(files: list[Path], output_dir: Path, max_size_kb: int = _MAX_SKELETON_FILE_SIZE_KB) -> Path:"
      },
      {
        "type": "function",
        "name": "_skeleton_to_md",
        "lines": "747-766",
        "signature": "def _skeleton_to_md(skeleton_data: list[dict]) -> str:"
      },
      {
        "type": "function",
        "name": "cmd_build_skeleton",
        "lines": "769-777",
        "signature": "def cmd_build_skeleton() -> None:"
      },
      {
        "type": "function",
        "name": "_update_skeleton_incremental",
        "lines": "780-812",
        "signature": "def _update_skeleton_incremental(changed_files: list[str]) -> None:"
      },
      {
        "type": "function",
        "name": "_load_skeleton_map",
        "lines": "815-826",
        "signature": "def _load_skeleton_map(issue_dir: Path | None = None) -> dict:"
      },
      {
        "type": "function",
        "name": "_find_imports",
        "lines": "829-869",
        "signature": "def _find_imports(files: list[Path], depth: int = 1) -> list[Path]:"
      },
      {
        "type": "function",
        "name": "_search_keywords",
        "lines": "872-922",
        "signature": "def _search_keywords(issue_text: str, repo_path: Path) -> list[Path]:"
      },
      {
        "type": "function",
        "name": "_build_analyse_comment",
        "lines": "930-1007",
        "signature": "def _build_analyse_comment(issue: dict, files: list[Path]) -> str:"
      },
      {
        "type": "function",
        "name": "_has_detailed_plan",
        "lines": "1015-1034",
        "signature": "def _has_detailed_plan(number: int) -> bool:"
      },
      {
        "type": "function",
        "name": "_parse_diff_changed_lines",
        "lines": "1042-1073",
        "signature": "def _parse_diff_changed_lines(branch: str) -> dict[str, list[int]]:"
      },
      {
        "type": "function",
        "name": "_warn_diff_out_of_scope",
        "lines": "1076-1162",
        "signature": "def _warn_diff_out_of_scope(number: int, branch: str) -> None:"
      },
      {
        "type": "function",
        "name": "_warn_slices_not_requested",
        "lines": "1165-1221",
        "signature": "def _warn_slices_not_requested(number: int, branch: str) -> None:"
      },
      {
        "type": "function",
        "name": "_check_pr_preconditions",
        "lines": "1224-1370",
        "signature": "def _check_pr_preconditions(number: int, branch: str) -> None:"
      },
      {
        "type": "function",
        "name": "_validate_pr_completion",
        "lines": "1373-1417",
        "signature": "def _validate_pr_completion("
      },
      {
        "type": "function",
        "name": "_validate_comment",
        "lines": "1420-1443",
        "signature": "def _validate_comment(body: str, comment_type: str, *, critical: bool = False) -> None:"
      },
      {
        "type": "function",
        "name": "_update_discussion",
        "lines": "1446-1481",
        "signature": "def _update_discussion(issue: dict, starter_path: Path) -> None:"
      },
      {
        "type": "function",
        "name": "cmd_list",
        "lines": "1489-1507",
        "signature": "def cmd_list() -> None:"
      },
      {
        "type": "function",
        "name": "cmd_plan",
        "lines": "1510-1614",
        "signature": "def cmd_plan(number: int) -> None:"
      },
      {
        "type": "function",
        "name": "cmd_implement",
        "lines": "1617-1760",
        "signature": "def cmd_implement(number: int) -> None:"
      },
      {
        "type": "function",
        "name": "_neustart_required",
        "lines": "1773-1778",
        "signature": "def _neustart_required(changed_files: list[str]) -> str:"
      },
      {
        "type": "function",
        "name": "cmd_pr",
        "lines": "1781-1946",
        "signature": "def cmd_pr("
      },
      {
        "type": "function",
        "name": "cmd_generate_tests",
        "lines": "1950-1975",
        "signature": "def cmd_generate_tests(number: int) -> None:"
      },
      {
        "type": "function",
        "name": "_current_issue_from_branch",
        "lines": "1977-1992",
        "signature": "def _current_issue_from_branch() -> int | None:"
      },
      {
        "type": "function",
        "name": "_log_slice_request",
        "lines": "1995-2016",
        "signature": "def _log_slice_request(spec: str) -> None:"
      },
      {
        "type": "function",
        "name": "cmd_get_slice",

[... 1099 weitere Zeilen — --get-slice für vollständigen Code ...]
```

## start_night.sh
```sh
#!/usr/bin/env bash
# start_night.sh — Startet den Night-Modus (autonomer Betrieb).
#
# Stoppt Patch-Service falls aktiv, startet gitea-agent-night.service.
# Notebook kann danach zugeklappt werden.
set -euo pipefail

NIGHT_SVC="gitea-agent-night"
PATCH_SVC="gitea-agent-patch"

echo "[→] Starte Night-Modus..."

# Patch stoppen falls aktiv
if systemctl is-active --quiet "$PATCH_SVC" 2>/dev/null; then
    echo "[→] Stoppe Patch-Modus..."
    systemctl --user stop "$PATCH_SVC"
    echo "[✓] Patch-Modus gestoppt"
fi

# Night starten
systemctl --user start "$NIGHT_SVC"
echo "[✓] Night-Modus aktiv"
echo "    Service: $NIGHT_SVC"
echo "    Logs:    journalctl -u $NIGHT_SVC -f"
```

## context_export.sh
```sh
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
```

## log.py  *(67 Zeilen)*
  - Funktion `setup` Zeilen 21-54  `def setup(log_file: str = "gitea-agent.log", level: str = "INFO") -> None:`
  - Funktion `get_logger` Zeilen 57-67  `def get_logger(name: str) -> logging.Logger:`
> Volltext: `python3 agent_start.py --get-slice log.py:1-67`

## plugins/patch.py  *(200 Zeilen)*
  - Funktion `_project_root` Zeilen 17-22  `def _project_root() -> Path:`
  - Funktion `_normalize_ws` Zeilen 32-34  `def _normalize_ws(text: str) -> str:`
  - Funktion `_parse_search_replace` Zeilen 37-83  `def _parse_search_replace(text: str) -> list[dict]:`
  - Funktion `_apply_patch` Zeilen 86-147  `def _apply_patch(`
  - Funktion `cmd_apply_patch` Zeilen 150-200  `def cmd_apply_patch(number: int, dry_run: bool = False) -> None:`
> Volltext: `python3 agent_start.py --get-slice plugins/patch.py:1-200`

## plugins/changelog.py  *(165 Zeilen)*
  - Funktion `_project_root` Zeilen 16-21  `def _project_root() -> Path:`
  - Funktion `_git_log_since_tag` Zeilen 40-79  `def _git_log_since_tag(cwd: Path) -> list[dict]:`
  - Funktion `_classify_commit` Zeilen 82-93  `def _classify_commit(subject: str) -> tuple[str, str]:`
  - Funktion `_build_changelog_block` Zeilen 96-117  `def _build_changelog_block(commits: list[dict], version: str, date: str) -> str:`
  - Funktion `cmd_changelog` Zeilen 120-165  `def cmd_changelog(version: str | None = None, update_file: bool = True) -> str:`
> Volltext: `python3 agent_start.py --get-slice plugins/changelog.py:1-165`

## scripts/agent_status.sh
```sh
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
```

## scripts/stop_agent.sh
```sh
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
        systemctl --user stop "$svc"
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
```

## scripts/start_patch.sh
```sh
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
systemctl --user start "$PATCH_SVC"
echo "[✓] Patch-Modus aktiv"
echo "    Service: $PATCH_SVC"
echo "    Logs:    journalctl -u $PATCH_SVC -f"
```

## scripts/push_github.sh
```sh
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
```

## scripts/start_night.sh
```sh
#!/usr/bin/env bash
# start_night.sh — Startet den Night-Modus (autonomer Betrieb).
#
# Stoppt Patch-Service falls aktiv, startet gitea-agent-night.service.
# Notebook kann danach zugeklappt werden.
set -euo pipefail

NIGHT_SVC="gitea-agent-night"
PATCH_SVC="gitea-agent-patch"

echo "[→] Starte Night-Modus..."

# Patch stoppen falls aktiv
if systemctl is-active --quiet "$PATCH_SVC" 2>/dev/null; then
    echo "[→] Stoppe Patch-Modus..."
    systemctl --user stop "$PATCH_SVC"
    echo "[✓] Patch-Modus gestoppt"
fi

# Night starten
systemctl --user start "$NIGHT_SVC"
echo "[✓] Night-Modus aktiv"
echo "    Service: $NIGHT_SVC"
echo "    Logs:    journalctl -u $NIGHT_SVC -f"
```

## scripts/context_export.sh
```sh
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
```

## data/doctor_last.json
```json
{
  "timestamp": "2026-03-26T20:30:36",
  "summary": {
    "ok": 5,
    "warn": 1,
    "fail": 0
  },
  "checks": [
    {
      "name": "Gitea-Verbindung",
      "status": "ok",
      "detail": "http://192.168.1.60:3001 → Alexmistrator/gitea-agent",
      "fix": ""
    },
    {
      "name": "Projekt-Verzeichnis",
      "status": "ok",
      "detail": "/home/ki02/gitea-agent",
      "fix": ""
    },
    {
      "name": "repo_skeleton.json",
      "status": "ok",
      "detail": "40028 Bytes",
      "fix": ""
    },
    {
      "name": "agent_eval.json",
      "status": "warn",
      "detail": "Nicht vorhanden",
      "fix": "python3 agent_start.py --setup oder manuell erstellen"
    },
    {
      "name": "Labels",
      "status": "ok",
      "detail": "Alle 5 vorhanden",
      "fix": ""
    },
    {
      "name": ".env",
      "status": "ok",
      "detail": "/home/ki02/gitea-agent/.env",
      "fix": ""
    }
  ]
}
```

## tests/test_issue.py  *(149 Zeilen)*
  - Funktion `_issue` Zeilen 12-13  `def _issue(title="", labels=None):`
  - Funktion `test_risk_level_bug` Zeilen 21-24  `def test_risk_level_bug():`
  - Funktion `test_risk_level_feature` Zeilen 27-29  `def test_risk_level_feature():`
  - Funktion `test_risk_level_enhancement` Zeilen 32-34  `def test_risk_level_enhancement():`
  - Funktion `test_risk_level_docs_keyword` Zeilen 37-40  `def test_risk_level_docs_keyword():`
  - Funktion `test_risk_level_default` Zeilen 43-45  `def test_risk_level_default():`
  - Funktion `test_risk_level_no_labels` Zeilen 48-50  `def test_risk_level_no_labels():`
  - Funktion `test_issue_type_bug` Zeilen 58-59  `def test_issue_type_bug():`
  - Funktion `test_issue_type_feature` Zeilen 62-63  `def test_issue_type_feature():`
  - Funktion `test_issue_type_enhancement` Zeilen 66-67  `def test_issue_type_enhancement():`
  - Funktion `test_issue_type_docs` Zeilen 70-71  `def test_issue_type_docs():`
  - Funktion `test_issue_type_default` Zeilen 74-75  `def test_issue_type_default():`
  - Funktion `test_branch_name_bug_prefix` Zeilen 83-85  `def test_branch_name_bug_prefix():`
  - Funktion `test_branch_name_feat_prefix` Zeilen 88-90  `def test_branch_name_feat_prefix():`
  - Funktion `test_branch_name_chore_prefix` Zeilen 93-95  `def test_branch_name_chore_prefix():`
  - Funktion `test_branch_name_docs_prefix` Zeilen 98-100  `def test_branch_name_docs_prefix():`
  - Funktion `test_branch_name_slug_length` Zeilen 103-107  `def test_branch_name_slug_length():`
  - Funktion `test_branch_name_umlaut_conversion` Zeilen 110-113  `def test_branch_name_umlaut_conversion():`
  - Funktion `test_branch_name_special_chars_removed` Zeilen 116-120  `def test_branch_name_special_chars_removed():`
  - Funktion `test_validate_comment_all_present` Zeilen 128-132  `def test_validate_comment_all_present(capfd):`
  - Funktion `test_validate_comment_missing_field` Zeilen 135-139  `def test_validate_comment_missing_field(capfd):`
  - Funktion `test_validate_comment_unknown_type` Zeilen 142-144  `def test_validate_comment_unknown_type():`
  - Funktion `test_validate_comment_case_insensitive` Zeilen 147-149  `def test_validate_comment_case_insensitive():`
> Volltext: `python3 agent_start.py --get-slice tests/test_issue.py:1-149`

## tests/test_patch.py  *(152 Zeilen)*
  - Funktion `test_normalize_ws_strips_trailing_spaces` Zeilen 20-21  `def test_normalize_ws_strips_trailing_spaces():`
  - Funktion `test_normalize_ws_crlf_to_lf` Zeilen 24-25  `def test_normalize_ws_crlf_to_lf():`
  - Funktion `test_normalize_ws_empty` Zeilen 28-29  `def test_normalize_ws_empty():`
  - Funktion `test_normalize_ws_no_change` Zeilen 32-33  `def test_normalize_ws_no_change():`
  - Funktion `test_parse_single_block` Zeilen 50-55  `def test_parse_single_block():`
  - Funktion `test_parse_multiple_blocks` Zeilen 58-62  `def test_parse_multiple_blocks():`
  - Funktion `test_parse_empty_text` Zeilen 65-66  `def test_parse_empty_text():`
  - Funktion `test_parse_no_py_header_ignored` Zeilen 69-71  `def test_parse_no_py_header_ignored():`
  - Funktion `test_parse_multiline_block` Zeilen 74-78  `def test_parse_multiline_block():`
  - Funktion `test_parse_incomplete_block_ignored` Zeilen 81-83  `def test_parse_incomplete_block_ignored():`
  - Funktion `_make_temp_py` Zeilen 91-98  `def _make_temp_py(content: str) -> Path:`
  - Funktion `test_apply_patch_happy_path` Zeilen 101-108  `def test_apply_patch_happy_path(tmp_path, monkeypatch):`
  - Funktion `test_apply_patch_search_not_found` Zeilen 111-117  `def test_apply_patch_search_not_found(tmp_path, monkeypatch):`
  - Funktion `test_apply_patch_file_not_found` Zeilen 120-125  `def test_apply_patch_file_not_found(tmp_path, monkeypatch):`
  - Funktion `test_apply_patch_dry_run` Zeilen 128-135  `def test_apply_patch_dry_run(tmp_path, monkeypatch):`
  - Funktion `test_apply_patch_syntax_error_rejected` Zeilen 138-144  `def test_apply_patch_syntax_error_rejected(tmp_path, monkeypatch):`
  - Funktion `test_apply_patch_creates_backup` Zeilen 147-152  `def test_apply_patch_creates_backup(tmp_path, monkeypatch):`
> Volltext: `python3 agent_start.py --get-slice tests/test_patch.py:1-152`

## tests/score_history.json
```json
[
  {
    "timestamp": "2026-03-23T08:06:49",
    "commit": "611e83b58da382f997272a2e4f3cce3bdd1f9b04",
    "trigger": "manual",
    "score": 0,
    "max_score": 1,
    "baseline": 0.0,
    "passed": true,
    "failed": [
      {
        "name": "Dummy Test",
        "reason": "Keywords ['Hello'] nicht in Antwort",
        "tag": ""
      }
    ],
    "latencies": [
      {
        "name": "Dummy Test",
        "ms": 3.36,
        "max_ms": null,
        "tag": ""
      }
    ]
  }
]
```

## tests/test_skeleton.py  *(121 Zeilen)*
  - Funktion `test_extract_function` Zeilen 17-21  `def test_extract_function():`
  - Funktion `test_extract_class` Zeilen 24-27  `def test_extract_class():`
  - Funktion `test_extract_multiple` Zeilen 30-33  `def test_extract_multiple():`
  - Funktion `test_extract_syntax_error_returns_empty` Zeilen 36-38  `def test_extract_syntax_error_returns_empty():`
  - Funktion `test_extract_empty_string` Zeilen 41-42  `def test_extract_empty_string():`
  - Funktion `test_extract_line_numbers` Zeilen 45-51  `def test_extract_line_numbers():`
  - Funktion `test_extract_signature` Zeilen 54-58  `def test_extract_signature():`
  - Funktion `test_extract_async_function` Zeilen 61-64  `def test_extract_async_function():`
  - Funktion `test_skeleton_to_md_header` Zeilen 72-76  `def test_skeleton_to_md_header():`
  - Funktion `test_skeleton_to_md_function_entry` Zeilen 79-88  `def test_skeleton_to_md_function_entry():`
  - Funktion `test_skeleton_to_md_class_entry` Zeilen 91-99  `def test_skeleton_to_md_class_entry():`
  - Funktion `test_skeleton_to_md_truncated` Zeilen 102-105  `def test_skeleton_to_md_truncated():`
  - Funktion `test_skeleton_to_md_no_symbols` Zeilen 108-111  `def test_skeleton_to_md_no_symbols():`
  - Funktion `test_skeleton_to_md_multiple_files` Zeilen 114-121  `def test_skeleton_to_md_multiple_files():`
> Volltext: `python3 agent_start.py --get-slice tests/test_skeleton.py:1-121`

## tests/test_changelog.py  *(97 Zeilen)*
  - Funktion `test_classify_feat` Zeilen 17-18  `def test_classify_feat():`
  - Funktion `test_classify_fix` Zeilen 21-22  `def test_classify_fix():`
  - Funktion `test_classify_with_scope` Zeilen 25-28  `def test_classify_with_scope():`
  - Funktion `test_classify_breaking_change` Zeilen 31-34  `def test_classify_breaking_change():`
  - Funktion `test_classify_no_prefix` Zeilen 37-40  `def test_classify_no_prefix():`
  - Funktion `test_classify_empty` Zeilen 43-45  `def test_classify_empty():`
  - Funktion `test_classify_chore` Zeilen 48-51  `def test_classify_chore():`
  - Funktion `test_classify_case_insensitive_prefix` Zeilen 54-56  `def test_classify_case_insensitive_prefix():`
  - Funktion `test_build_changelog_block_header` Zeilen 64-66  `def test_build_changelog_block_header():`
  - Funktion `test_build_changelog_block_feat_section` Zeilen 69-74  `def test_build_changelog_block_feat_section():`
  - Funktion `test_build_changelog_block_multiple_types` Zeilen 77-84  `def test_build_changelog_block_multiple_types():`
  - Funktion `test_build_changelog_block_other_section` Zeilen 87-91  `def test_build_changelog_block_other_section():`
  - Funktion `test_build_changelog_block_empty_commits` Zeilen 94-97  `def test_build_changelog_block_empty_commits():`
> Volltext: `python3 agent_start.py --get-slice tests/test_changelog.py:1-97`

## tests/test_settings.py  *(35 Zeilen)*
  - Funktion `test_dashboard_path_is_absolute` Zeilen 10-11  `def test_dashboard_path_is_absolute():`
  - Funktion `test_dashboard_path_ends_with_html` Zeilen 14-15  `def test_dashboard_path_ends_with_html():`
  - Funktion `test_dashboard_path_inside_agent_or_root` Zeilen 18-21  `def test_dashboard_path_inside_agent_or_root():`
  - Funktion `test_all_paths_consistent` Zeilen 24-35  `def test_all_paths_consistent():`
> Volltext: `python3 agent_start.py --get-slice tests/test_settings.py:1-35`
