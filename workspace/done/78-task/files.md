# Dateien — Issue #78
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

## start_patch.sh  *(71 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## agent_start.py  *(zu groß — Datei zu groß (143KB > 20KB))*

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

## agent_eval.template.json  *(102 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## _create_issue_github.py  *(64 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## dashboard.py  *(302 Zeilen)*

- **Funktion** `generate` Zeilen 139-298
  `def generate(project_root: Path):`

## settings.py  *(260 Zeilen)*

- **Funktion** `_env` Zeilen 16-25
  `def _env(key: str, default: str = "") -> str:`
- **Funktion** `_env_list` Zeilen 28-30
  `def _env_list(key: str, default: str) -> list[str]:`
- **Funktion** `_env_int` Zeilen 33-37
  `def _env_int(key: str, default: int) -> int:`
- **Funktion** `_env_bool` Zeilen 40-41
  `def _env_bool(key: str, default: bool = False) -> bool:`

## evaluation.py  *(598 Zeilen)*

- **Klasse** `TestResult` Zeilen 41-56
  `class TestResult:`
- **Klasse** `EvalResult` Zeilen 60-71
  `class EvalResult:`
- **Funktion** `_ping` Zeilen 79-87
  `def _ping(url: str) -> bool:`
- **Funktion** `_chat` Zeilen 90-119
  `def _chat(server_url: str, endpoint: str, message: str, eval_user: str) -> str | None:`
- **Funktion** `_keywords_match` Zeilen 122-125
  `def _keywords_match(text: str, keywords: list[str]) -> bool:`
- **Funktion** `_categorize` Zeilen 128-158
  `def _categorize(`
- **Funktion** `_run_steps` Zeilen 161-236
  `def _run_steps(`
- **Funktion** `_resolve_path` Zeilen 239-257
  `def _resolve_path(project_root: Path, new_rel: str, legacy_rel: str) -> Path:`
- **Funktion** `_resolve_config` Zeilen 260-265
  `def _resolve_config(project_root: Path) -> Path:`
- **Funktion** `_load_config` Zeilen 268-274
  `def _load_config(project_root: Path) -> dict | None:`
- **Funktion** `_load_baseline` Zeilen 277-284
  `def _load_baseline(project_root: Path) -> float | None:`
- **Funktion** `_save_baseline` Zeilen 287-292
  `def _save_baseline(project_root: Path, score: float) -> None:`
- **Funktion** `_get_commit_hash` Zeilen 295-306
  `def _get_commit_hash() -> str:`
- **Funktion** `_save_score_history` Zeilen 309-345
  `def _save_score_history(project_root: Path, result: "EvalResult", trigger: str) -> None:`
- **Funktion** `run` Zeilen 353-519
  `def run(`
- **Funktion** `format_terminal` Zeilen 527-551
  `def format_terminal(r: EvalResult) -> str:`
- **Funktion** `format_gitea_comment` Zeilen 554-573
  `def format_gitea_comment(r: EvalResult) -> str:`
- **Funktion** `main` Zeilen 581-594
  `def main() -> None:`

## repo_skeleton.json  *(zu groß — Datei zu groß (24KB > 20KB))*

## context_export.sh  *(206 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## log.py  *(67 Zeilen)*

- **Funktion** `setup` Zeilen 21-54
  `def setup(log_file: str = "gitea-agent.log", level: str = "INFO") -> None:`
- **Funktion** `get_logger` Zeilen 57-67
  `def get_logger(name: str) -> logging.Logger:`

## tests/score_history.json  *(26 Zeilen)*

*(keine Klassen/Funktionen erkannt)*


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
```

## agent_start.py  *(3960 Zeilen)*
  - Funktion `_project_root` Zeilen 62-84  `def _project_root() -> Path:`
  - Funktion `risk_level` Zeilen 95-116  `def risk_level(issue: dict) -> tuple[int, str]:`
  - Funktion `issue_type` Zeilen 119-131  `def issue_type(issue: dict) -> str:`
  - Funktion `relevant_files` Zeilen 139-157  `def relevant_files(issue: dict) -> list[Path]:`
  - Funktion `find_relevant_files_advanced` Zeilen 160-186  `def find_relevant_files_advanced(issue: dict) -> list[Path]:`
  - Funktion `branch_name` Zeilen 189-217  `def branch_name(issue: dict) -> str:`
  - Funktion `build_plan_comment` Zeilen 225-271  `def build_plan_comment(issue: dict) -> str:`
  - Funktion `print_context` Zeilen 279-310  `def print_context(issue: dict) -> None:`
  - Funktion `_context_dir` Zeilen 318-328  `def _context_dir() -> Path:`
  - Funktion `_issue_dir` Zeilen 331-338  `def _issue_dir(issue: dict) -> Path:`
  - Funktion `_find_issue_dir` Zeilen 341-351  `def _find_issue_dir(number: int) -> Path | None:`
  - Funktion `_done_dir` Zeilen 354-358  `def _done_dir() -> Path:`
  - Funktion `save_plan_context` Zeilen 361-415  `def save_plan_context(issue: dict) -> Path:`
  - Funktion `save_tests_context` Zeilen 419-455  `def save_tests_context(issue: dict, files_dict: dict) -> tuple[Path, Path]:`
  - Funktion `save_implement_context` Zeilen 457-583  `def save_implement_context(issue: dict, files_dict: dict) -> tuple[Path, Path]:`
  - Funktion `_get_exclude_dirs` Zeilen 611-631  `def _get_exclude_dirs(project: Path) -> set[str]:`
  - Funktion `_extract_ast_symbols` Zeilen 657-679  `def _extract_ast_symbols(content: str) -> list[dict]:`
  - Funktion `_create_repo_skeleton` Zeilen 682-736  `def _create_repo_skeleton(files: list[Path], output_dir: Path, max_size_kb: int = _MAX_SKELETON_FILE_SIZE_KB) -> Path:`
  - Funktion `_skeleton_to_md` Zeilen 739-758  `def _skeleton_to_md(skeleton_data: list[dict]) -> str:`
  - Funktion `cmd_build_skeleton` Zeilen 761-769  `def cmd_build_skeleton() -> None:`
  - Funktion `_update_skeleton_incremental` Zeilen 772-804  `def _update_skeleton_incremental(changed_files: list[str]) -> None:`
  - Funktion `_load_skeleton_map` Zeilen 807-818  `def _load_skeleton_map(issue_dir: Path | None = None) -> dict:`
  - Funktion `_find_imports` Zeilen 821-861  `def _find_imports(files: list[Path], depth: int = 1) -> list[Path]:`
  - Funktion `_search_keywords` Zeilen 864-914  `def _search_keywords(issue_text: str, repo_path: Path) -> list[Path]:`
  - Funktion `_build_analyse_comment` Zeilen 922-999  `def _build_analyse_comment(issue: dict, files: list[Path]) -> str:`
  - Funktion `_has_detailed_plan` Zeilen 1007-1026  `def _has_detailed_plan(number: int) -> bool:`
  - Funktion `_parse_diff_changed_lines` Zeilen 1034-1065  `def _parse_diff_changed_lines(branch: str) -> dict[str, list[int]]:`
  - Funktion `_warn_diff_out_of_scope` Zeilen 1068-1154  `def _warn_diff_out_of_scope(number: int, branch: str) -> None:`
  - Funktion `_warn_slices_not_requested` Zeilen 1157-1213  `def _warn_slices_not_requested(number: int, branch: str) -> None:`
  - Funktion `_check_pr_preconditions` Zeilen 1216-1362  `def _check_pr_preconditions(number: int, branch: str) -> None:`
  - Funktion `_validate_pr_completion` Zeilen 1365-1409  `def _validate_pr_completion(`
  - Funktion `_validate_comment` Zeilen 1412-1435  `def _validate_comment(body: str, comment_type: str, *, critical: bool = False) -> None:`
  - Funktion `_update_discussion` Zeilen 1438-1473  `def _update_discussion(issue: dict, starter_path: Path) -> None:`
  - Funktion `cmd_list` Zeilen 1481-1499  `def cmd_list() -> None:`
  - Funktion `cmd_plan` Zeilen 1502-1606  `def cmd_plan(number: int) -> None:`
  - Funktion `cmd_implement` Zeilen 1609-1752  `def cmd_implement(number: int) -> None:`
  - Funktion `_neustart_required` Zeilen 1765-1770  `def _neustart_required(changed_files: list[str]) -> str:`
  - Funktion `cmd_pr` Zeilen 1773-1938  `def cmd_pr(`
  - Funktion `cmd_generate_tests` Zeilen 1942-1967  `def cmd_generate_tests(number: int) -> None:`
  - Funktion `_current_issue_from_branch` Zeilen 1969-1984  `def _current_issue_from_branch() -> int | None:`
  - Funktion `_log_slice_request` Zeilen 1987-2008  `def _log_slice_request(spec: str) -> None:`
  - Funktion `cmd_get_slice` Zeilen 2011-2041  `def cmd_get_slice(spec: str) -> None:`
  - Funktion `_parse_search_replace` Zeilen 2053-2099  `def _parse_search_replace(text: str) -> list[dict]:`
  - Funktion `_normalize_ws` Zeilen 2102-2104  `def _normalize_ws(text: str) -> str:`
  - Funktion `_apply_patch` Zeilen 2107-2169  `def _apply_patch(`
  - Funktion `cmd_apply_patch` Zeilen 2172-2222  `def cmd_apply_patch(number: int, dry_run: bool = False) -> None:`
  - Funktion `_git_log_since_tag` Zeilen 2243-2282  `def _git_log_since_tag(cwd: Path) -> list[dict]:`
  - Funktion `_classify_commit` Zeilen 2285-2296  `def _classify_commit(subject: str) -> tuple[str, str]:`
  - Funktion `_build_changelog_block` Zeilen 2299-2320  `def _build_changelog_block(commits: list[dict], version: str, date: str) -> str:`
  - Funktion `cmd_changelog` Zeilen 2323-2368  `def cmd_changelog(version: str | None = None, update_file: bool = True) -> str:`
  - Funktion `cmd_fixup` Zeilen 2371-2415  `def cmd_fixup(number: int) -> None:`
  - Funktion `_auto_issue_exists` Zeilen 2423-2427  `def _auto_issue_exists(test_name: str) -> bool:`
  - Funktion `_auto_perf_issue_exists` Zeilen 2429-2433  `def _auto_perf_issue_exists(test_name: str) -> bool:`
  - Funktion `_auto_improvement_issue_exists` Zeilen 2437-2440  `def _auto_improvement_issue_exists(tag: str) -> bool:`
  - Funktion `_check_systematic_tag_failures` Zeilen 2442-2516  `def _check_systematic_tag_failures(project_root) -> None:`
  - Funktion `_sync_closed_contexts` Zeilen 2519-2544  `def _sync_closed_contexts() -> None:`
  - Funktion `_consecutive_passes_for_test` Zeilen 2547-2572  `def _consecutive_passes_for_test(test_name: str) -> int:`
  - Funktion `_close_resolved_auto_issues` Zeilen 2575-2654  `def _close_resolved_auto_issues(result: "evaluation.EvalResult") -> None:`
  - Funktion `_build_metadata` Zeilen 2657-2736  `def _build_metadata(`
  - Funktion `_session_path` Zeilen 2739-2741  `def _session_path() -> Path:`
  - Funktion `_session_load` Zeilen 2744-2768  `def _session_load() -> dict:`
  - Funktion `_session_increment` Zeilen 2771-2781  `def _session_increment() -> dict:`
  - Funktion `_session_status_line` Zeilen 2784-2797  `def _session_status_line(data: dict) -> str:`
  - Funktion `_format_history_block` Zeilen 2800-2836  `def _format_history_block(project_root: Path, n: int = 5) -> str:`
  - Funktion `_last_chat_inactive_minutes` Zeilen 2839-2887  `def _last_chat_inactive_minutes(log_path: str | Path) -> float | None:`
  - Funktion `_server_start_time` Zeilen 2890-2938  `def _server_start_time(log_path: str | Path) -> datetime.datetime | None:`
  - Funktion `_check_server_staleness` Zeilen 2941-3009  `def _check_server_staleness(branch: str, force: bool = False) -> None:`
  - Funktion `_restart_server_for_eval` Zeilen 3012-3034  `def _restart_server_for_eval() -> None:`
  - Funktion `_has_new_commits_since_last_eval` Zeilen 3037-3068  `def _has_new_commits_since_last_eval(project_root: Path) -> bool:`
  - Funktion `_wait_for_server` Zeilen 3071-3116  `def _wait_for_server(`
  - Funktion `cmd_eval_after_restart` Zeilen 3119-3181  `def cmd_eval_after_restart(number: int | None = None) -> None:`
  - Funktion `_ast_diff` Zeilen 3184-3224  `def _ast_diff(old_content: str, new_content: str) -> list[str]:`
  - Funktion `_gitea_version_compare` Zeilen 3227-3278  `def _gitea_version_compare(commit: str, changed_files: list[str]) -> str:`
  - Funktion `_build_auto_issue_body` Zeilen 3281-3396  `def _build_auto_issue_body(`
  - Funktion `cmd_watch` Zeilen 3399-3535  `def cmd_watch(interval_minutes: int = 60, patch_mode: bool = False) -> None:`
  - Funktion `_dashboard_event` Zeilen 3543-3550  `def _dashboard_event(context: str = "") -> None:`
  - Funktion `cmd_install_service` Zeilen 3576-3621  `def cmd_install_service() -> None:`
  - Funktion `cmd_dashboard` Zeilen 3629-3635  `def cmd_dashboard() -> None:`
  - Funktion `cmd_auto` Zeilen 3637-3729  `def cmd_auto() -> None:`
  - Funktion `_apply_auto_approve` Zeilen 3737-3765  `def _apply_auto_approve() -> None:`
  - Funktion `main` Zeilen 3768-3956  `def main():`
  - Funktion `_sym_map` Zeilen 3195-3197  `def _sym_map(content: str) -> dict[str, dict]:`
  - Funktion `_len` Zeilen 3208-3213  `def _len(s: dict) -> int:`
> Volltext: `python3 agent_start.py --get-slice agent_start.py:1-3960`

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
    "server_url": "http://localhost:8000",
    "chat_endpoint": "/chat",
    "pi5_url": "",
    "log_path": "/path/to/your/logs/system.log",
    "restart_script": "/path/to/your/start.sh",
    "inactivity_minutes": 5,
    "watch_interval_minutes": 60,
    "log_analysis_interval_minutes": 120,
    "llm_log_analysis": {
        "enabled": false,
        "provider": "openai",
        "url": "http://localhost:8000/v1/chat/completions",
        "model": "llama-3",
        "api_key": ""
    },
    "tests": [
        {
            "name": "Basis-Antwort",
            "tag": "routing",
            "weight": 1,
            "pi5_required": false,
            "message": "Was ist 2 plus 2?",
            "expected_keywords": ["4"],
            "_comment": "Einfachster Test — Server erreichbar und antwortet"
        },
        {
            "name": "Kontext-Speicherung",
            "tag": "chroma_retrieval",
            "weight": 2,
            "pi5_required": true,
            "steps": [
                {
                    "message": "Mein Name ist TestUser",
                    "expect_stored": true,
                    "_comment": "Step 1: Information speichern"
                },
                {
                    "message": "Wie heiße ich?",
                    "expected_keywords": ["TestUser"],
                    "_comment": "Step 2: Gespeicherte Information abrufen"
                }
            ]
        },
        {
            "name": "System-Prompt Ton",
            "tag": "system_prompt",
            "weight": 1,
            "pi5_required": false,
            "message": "Hallo, wie geht es dir?",
            "expected_keywords": [],
            "_comment": "Prüft ob der Assistent antwortet — Keywords projektspezifisch anpassen"
        }
    ],
    "improvement_hints": {
        "chroma_retrieval": {
            "hypothesis": "Chroma verliert Kontext oder Retrieval findet relevante Chunks nicht",
            "levers": [
                "Chroma-Persistenz prüfen — wird collection.persist() aufgerufen?",
                "k (Anzahl zurückgegebener Chunks) erhöhen",
                "Score-Threshold senken",
                "Chunk-Size verkleinern",
                "Embedding-Modell prüfen"
            ],
            "affected_files": ["chroma_handler.py", "retrieval.py", "memory.py"],
            "_comment": "Dateipfade ans Projekt anpassen"
        },
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
        "system_prompt": {
            "hypothesis": "Systemkontext zu lang oder Instruktionen unklar",
            "levers": [
                "Systemprompt kürzen",
                "Explizite Instruktionen für Grenzfälle ergänzen",
                "Prompt auf Widersprüche prüfen"
            ],
            "affected_files": ["prompts/system.txt", "config.py"],
            "_comment": "Dateipfade ans Projekt anpassen"
        },
        "web_search": {
            "hypothesis": "Web-Search antwortet nicht oder liefert leere Ergebnisse",
            "levers": [
                "API-Key prüfen",
                "Timeout erhöhen",
                "Fallback wenn Web-Search offline"
            ],
            "affected_files": ["web_search.py", "server.py"],
            "_comment": "Nur relevant wenn Web-Search genutzt wird — sonst entfernen"
        }
    },
    "context_loader": {
        "exclude_dirs": ["Backup", "Documentation", "node_modules", ".venv"]
    }
}
```

## _create_issue_github.py
```py
import sys
sys.argv = ['x', '--self']
import agent_start
from agent_start import gitea

body = (
    "## Ziel\n"
    "Neuer Befehl `--github-push` der den aktuellen Stand des lokalen Gitea-Repos "
    "auf ein öffentliches GitHub-Repository spiegelt — mit automatischer Anonymisierung "
    "sensibler Daten vor dem Push.\n\n"

    "## Hintergrund\n"
    "Code liegt lokal auf Gitea (self-hosted). Für öffentliche Sichtbarkeit auf GitHub "
    "müssen vor dem Push sensible Daten entfernt werden:\n"
    "- Lokale IP-Adressen (`192.168.x.x`)\n"
    "- Lokale Pfade (`/home/ki02/`, benutzerspezifische Verzeichnisse)\n"
    "- `.env`-Dateien (Tokens, Passwörter)\n"
    "- Konfigurierbare weitere Patterns\n\n"

    "## Scope (bewusst begrenzt)\n"
    "- ✅ Aktueller Branch-Stand wird bereinigt und gepusht\n"
    "- ✅ `.env`-Dateien werden grundsätzlich nicht gepusht\n"
    "- ✅ Konfigurierbare Pattern-Liste für Ersetzungen\n"
    "- ✅ Dry-run Modus zeigt was ersetzt/ausgelassen würde\n"
    "- ❌ Kein History-Rewrite (zu riskant, SHA-Änderungen würden alles brechen)\n"
    "- ❌ Kein automatisches GitHub-Repo anlegen (muss vorher existieren)\n\n"

    "## Implementierungsidee\n"
    "```bash\n"
    "python3 agent_start.py --github-push                  # Push mit Anonymisierung\n"
    "python3 agent_start.py --github-push --dry-run        # Vorschau: was wird ersetzt?\n"
    "```\n\n"
    "Ablauf:\n"
    "1. `github_push_patterns` aus `.env` laden (IPs, Pfade, Namen)\n"
    "2. Alle getrackten Dateien auf sensitive Patterns prüfen\n"
    "3. Temporären Export-Branch erstellen (`github-mirror/DATUM`)\n"
    "4. Dateien mit ersetzten Patterns in temp-Branch committen\n"
    "5. Temp-Branch zu GitHub pushen (`origin-github` remote)\n"
    "6. Temp-Branch lokal wieder löschen\n\n"

    "## Konfiguration in .env\n"
    "```\n"
    "GITHUB_REMOTE=https://github.com/user/repo.git\n"
    "GITHUB_TOKEN=ghp_...\n"
    "GITHUB_PUSH_BRANCH=main\n"
    "GITHUB_ANONYMIZE_PATTERNS=192.168.1.60:YOUR-SERVER,/home/ki02:/home/user,Alexmistrator:contributor\n"
    "```\n\n"

    "## Akzeptanzkriterien\n"
    "- `--github-push` pusht aktuellen Stand auf GitHub\n"
    "- `.env`-Dateien werden nie gepusht (hard-coded Ausschluss)\n"
    "- Alle konfigurierten Patterns werden ersetzt bevor Push\n"
    "- `--dry-run` zeigt Diff: Original vs. anonymisiert, welche Dateien betroffen\n"
    "- Push schlägt fehl wenn GitHub-Remote nicht konfiguriert (klare Fehlermeldung)\n"
    "- Lokale Dateien werden nicht verändert (nur temp-Branch)\n"
    "- Dokumentation in README.md + `.env.example` aktualisiert\n\n"

    "## Risikostufe\n"
    "2/4 — MITTEL — pusht Code nach extern, aber lokale Dateien bleiben unberührt. "
    "Dry-run Pflicht vor erstem echten Push empfohlen."
)

r = gitea.create_issue("--github-push: Gitea → GitHub Spiegel mit Anonymisierung", body, "ready-for-agent")
print(f'#{r["number"]} — {r["title"]}')
```

## dashboard.py  *(260 Zeilen)*
  - Funktion `generate` Zeilen 135-256  `def generate(project_root: Path):`
> Volltext: `python3 agent_start.py --get-slice dashboard.py:1-260`

## settings.py  *(258 Zeilen)*
  - Funktion `_env` Zeilen 16-25  `def _env(key: str, default: str = "") -> str:`
  - Funktion `_env_list` Zeilen 28-30  `def _env_list(key: str, default: str) -> list[str]:`
  - Funktion `_env_int` Zeilen 33-37  `def _env_int(key: str, default: int) -> int:`
  - Funktion `_env_bool` Zeilen 40-41  `def _env_bool(key: str, default: bool = False) -> bool:`
> Volltext: `python3 agent_start.py --get-slice settings.py:1-258`

## evaluation.py  *(598 Zeilen)*
  - Klasse `TestResult` Zeilen 41-56  `class TestResult:`
  - Klasse `EvalResult` Zeilen 60-71  `class EvalResult:`
  - Funktion `_ping` Zeilen 79-87  `def _ping(url: str) -> bool:`
  - Funktion `_chat` Zeilen 90-119  `def _chat(server_url: str, endpoint: str, message: str, eval_user: str) -> str | None:`
  - Funktion `_keywords_match` Zeilen 122-125  `def _keywords_match(text: str, keywords: list[str]) -> bool:`
  - Funktion `_categorize` Zeilen 128-158  `def _categorize(`
  - Funktion `_run_steps` Zeilen 161-236  `def _run_steps(`
  - Funktion `_resolve_path` Zeilen 239-257  `def _resolve_path(project_root: Path, new_rel: str, legacy_rel: str) -> Path:`
  - Funktion `_resolve_config` Zeilen 260-265  `def _resolve_config(project_root: Path) -> Path:`
  - Funktion `_load_config` Zeilen 268-274  `def _load_config(project_root: Path) -> dict | None:`
  - Funktion `_load_baseline` Zeilen 277-284  `def _load_baseline(project_root: Path) -> float | None:`
  - Funktion `_save_baseline` Zeilen 287-292  `def _save_baseline(project_root: Path, score: float) -> None:`
  - Funktion `_get_commit_hash` Zeilen 295-306  `def _get_commit_hash() -> str:`
  - Funktion `_save_score_history` Zeilen 309-345  `def _save_score_history(project_root: Path, result: "EvalResult", trigger: str) -> None:`
  - Funktion `run` Zeilen 353-519  `def run(`
  - Funktion `format_terminal` Zeilen 527-551  `def format_terminal(r: EvalResult) -> str:`
  - Funktion `format_gitea_comment` Zeilen 554-573  `def format_gitea_comment(r: EvalResult) -> str:`
  - Funktion `main` Zeilen 581-594  `def main() -> None:`
> Volltext: `python3 agent_start.py --get-slice evaluation.py:1-598`

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
    "lines": 3960,
    "size_kb": 136,
    "symbols": [
      {
        "type": "function",
        "name": "_project_root",
        "lines": "62-84",
        "signature": "def _project_root() -> Path:"
      },
      {
        "type": "function",
        "name": "risk_level",
        "lines": "95-116",
        "signature": "def risk_level(issue: dict) -> tuple[int, str]:"
      },
      {
        "type": "function",
        "name": "issue_type",
        "lines": "119-131",
        "signature": "def issue_type(issue: dict) -> str:"
      },
      {
        "type": "function",
        "name": "relevant_files",
        "lines": "139-157",
        "signature": "def relevant_files(issue: dict) -> list[Path]:"
      },
      {
        "type": "function",
        "name": "find_relevant_files_advanced",
        "lines": "160-186",
        "signature": "def find_relevant_files_advanced(issue: dict) -> list[Path]:"
      },
      {
        "type": "function",
        "name": "branch_name",
        "lines": "189-217",
        "signature": "def branch_name(issue: dict) -> str:"
      },
      {
        "type": "function",
        "name": "build_plan_comment",
        "lines": "225-271",
        "signature": "def build_plan_comment(issue: dict) -> str:"
      },
      {
        "type": "function",
        "name": "print_context",
        "lines": "279-310",
        "signature": "def print_context(issue: dict) -> None:"
      },
      {
        "type": "function",
        "name": "_context_dir",
        "lines": "318-328",
        "signature": "def _context_dir() -> Path:"
      },
      {
        "type": "function",
        "name": "_issue_dir",
        "lines": "331-338",
        "signature": "def _issue_dir(issue: dict) -> Path:"
      },
      {
        "type": "function",
        "name": "_find_issue_dir",
        "lines": "341-351",
        "signature": "def _find_issue_dir(number: int) -> Path | None:"
      },
      {
        "type": "function",
        "name": "_done_dir",
        "lines": "354-358",
        "signature": "def _done_dir() -> Path:"
      },
      {
        "type": "function",
        "name": "save_plan_context",
        "lines": "361-415",
        "signature": "def save_plan_context(issue: dict) -> Path:"
      },
      {
        "type": "function",
        "name": "save_tests_context",
        "lines": "419-455",
        "signature": "def save_tests_context(issue: dict, files_dict: dict) -> tuple[Path, Path]:"
      },
      {
        "type": "function",
        "name": "save_implement_context",
        "lines": "457-583",
        "signature": "def save_implement_context(issue: dict, files_dict: dict) -> tuple[Path, Path]:"
      },
      {
        "type": "function",
        "name": "_get_exclude_dirs",
        "lines": "611-631",
        "signature": "def _get_exclude_dirs(project: Path) -> set[str]:"
      },
      {
        "type": "function",
        "name": "_extract_ast_symbols",
        "lines": "657-679",
        "signature": "def _extract_ast_symbols(content: str) -> list[dict]:"
      },
      {
        "type": "function",
        "name": "_create_repo_skeleton",
        "lines": "682-736",
        "signature": "def _create_repo_skeleton(files: list[Path], output_dir: Path, max_size_kb: int = _MAX_SKELETON_FILE_SIZE_KB) -> Path:"
      },
      {
        "type": "function",
        "name": "_skeleton_to_md",
        "lines": "739-758",
        "signature": "def _skeleton_to_md(skeleton_data: list[dict]) -> str:"
      },
      {
        "type": "function",
        "name": "cmd_build_skeleton",
        "lines": "761-769",
        "signature": "def cmd_build_skeleton() -> None:"
      },
      {
        "type": "function",
        "name": "_update_skeleton_incremental",
        "lines": "772-804",
        "signature": "def _update_skeleton_incremental(changed_files: list[str]) -> None:"
      },
      {
        "type": "function",
        "name": "_load_skeleton_map",
        "lines": "807-818",
        "signature": "def _load_skeleton_map(issue_dir: Path | None = None) -> dict:"
      },
      {
        "type": "function",
        "name": "_find_imports",
        "lines": "821-861",
        "signature": "def _find_imports(files: list[Path], depth: int = 1) -> list[Path]:"
      },
      {
        "type": "function",
        "name": "_search_keywords",
        "lines": "864-914",
        "signature": "def _search_keywords(issue_text: str, repo_path: Path) -> list[Path]:"
      },
      {
        "type": "function",
        "name": "_build_analyse_comment",
        "lines": "922-999",
        "signature": "def _build_analyse_comment(issue: dict, files: list[Path]) -> str:"
      },
      {
        "type": "function",
        "name": "_has_detailed_plan",
        "lines": "1007-1026",
        "signature": "def _has_detailed_plan(number: int) -> bool:"
      },
      {
        "type": "function",
        "name": "_parse_diff_changed_lines",
        "lines": "1034-1065",
        "signature": "def _parse_diff_changed_lines(branch: str) -> dict[str, list[int]]:"
      },
      {
        "type": "function",
        "name": "_warn_diff_out_of_scope",
        "lines": "1068-1154",
        "signature": "def _warn_diff_out_of_scope(number: int, branch: str) -> None:"
      },
      {
        "type": "function",
        "name": "_warn_slices_not_requested",
        "lines": "1157-1213",
        "signature": "def _warn_slices_not_requested(number: int, branch: str) -> None:"
      },
      {
        "type": "function",
        "name": "_check_pr_preconditions",
        "lines": "1216-1362",
        "signature": "def _check_pr_preconditions(number: int, branch: str) -> None:"
      },
      {
        "type": "function",
        "name": "_validate_pr_completion",
        "lines": "1365-1409",
        "signature": "def _validate_pr_completion("
      },
      {
        "type": "function",
        "name": "_validate_comment",
        "lines": "1412-1435",
        "signature": "def _validate_comment(body: str, comment_type: str, *, critical: bool = False) -> None:"
      },
      {
        "type": "function",
        "name": "_update_discussion",
        "lines": "1438-1473",
        "signature": "def _update_discussion(issue: dict, starter_path: Path) -> None:"
      },
      {
        "type": "function",
        "name": "cmd_list",
        "lines": "1481-1499",
        "signature": "def cmd_list() -> None:"
      },
      {
        "type": "function",
        "name": "cmd_plan",
        "lines": "1502-1606",
        "signature": "def cmd_plan(number: int) -> None:"
      },
      {
        "type": "function",
        "name": "cmd_implement",
        "lines": "1609-1752",
        "signature": "def cmd_implement(number: int) -> None:"
      },
      {
        "type": "function",
        "name": "_neustart_required",
        "lines": "1765-1770",
        "signature": "def _neustart_required(changed_files: list[str]) -> str:"
      },
      {
        "type": "function",
        "name": "cmd_pr",
        "lines": "1773-1938",
        "signature": "def cmd_pr("
      },
      {
        "type": "function",
        "name": "cmd_generate_tests",
        "lines": "1942-1967",
        "signature": "def cmd_generate_tests(number: int) -> None:"
      },
      {
        "type": "function",
        "name": "_current_issue_from_branch",
        "lines": "1969-1984",
        "signature": "def _current_issue_from_branch() -> int | None:"
      },
      {
        "type": "function",
        "name": "_log_slice_request",
        "lines": "1987-2008",
        "signature": "def _log_slice_request(spec: str) -> None:"
      },
      {
        "type": "function",
        "name": "cmd_get_slice",

[... 550 weitere Zeilen — --get-slice für vollständigen Code ...]
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
