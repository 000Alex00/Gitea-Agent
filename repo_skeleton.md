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

## agent_start.py  *(4305 Zeilen)*

- **Funktion** `_project_root` Zeilen 70-92
  `def _project_root() -> Path:`
- **Funktion** `risk_level` Zeilen 103-124
  `def risk_level(issue: dict) -> tuple[int, str]:`
- **Funktion** `issue_type` Zeilen 127-139
  `def issue_type(issue: dict) -> str:`
- **Funktion** `relevant_files` Zeilen 147-165
  `def relevant_files(issue: dict) -> list[Path]:`
- **Funktion** `find_relevant_files_advanced` Zeilen 168-194
  `def find_relevant_files_advanced(issue: dict) -> list[Path]:`
- **Funktion** `branch_name` Zeilen 197-225
  `def branch_name(issue: dict) -> str:`
- **Funktion** `build_plan_comment` Zeilen 233-279
  `def build_plan_comment(issue: dict) -> str:`
- **Funktion** `print_context` Zeilen 287-318
  `def print_context(issue: dict) -> None:`
- **Funktion** `_context_dir` Zeilen 326-336
  `def _context_dir() -> Path:`
- **Funktion** `_issue_dir` Zeilen 339-346
  `def _issue_dir(issue: dict) -> Path:`
- **Funktion** `_find_issue_dir` Zeilen 349-359
  `def _find_issue_dir(number: int) -> Path | None:`
- **Funktion** `_done_dir` Zeilen 362-366
  `def _done_dir() -> Path:`
- **Funktion** `save_plan_context` Zeilen 369-423
  `def save_plan_context(issue: dict) -> Path:`
- **Funktion** `save_tests_context` Zeilen 427-463
  `def save_tests_context(issue: dict, files_dict: dict) -> tuple[Path, Path]:`
- **Funktion** `save_implement_context` Zeilen 465-591
  `def save_implement_context(issue: dict, files_dict: dict) -> tuple[Path, Path]:`
- **Funktion** `_build_issue_context_silent` Zeilen 594-620
  `def _build_issue_context_silent(issue: dict) -> bool:`
- **Funktion** `_get_exclude_dirs` Zeilen 648-668
  `def _get_exclude_dirs(project: Path) -> set[str]:`
- **Funktion** `_extract_ast_symbols` Zeilen 694-716
  `def _extract_ast_symbols(content: str) -> list[dict]:`
- **Funktion** `_create_repo_skeleton` Zeilen 719-773
  `def _create_repo_skeleton(files: list[Path], output_dir: Path, max_size_kb: int = _MAX_SKELETON_FILE_SIZE_KB) -> Path:`
- **Funktion** `_skeleton_to_md` Zeilen 776-795
  `def _skeleton_to_md(skeleton_data: list[dict]) -> str:`
- **Funktion** `cmd_build_skeleton` Zeilen 798-806
  `def cmd_build_skeleton() -> None:`
- **Funktion** `_update_skeleton_incremental` Zeilen 809-841
  `def _update_skeleton_incremental(changed_files: list[str]) -> None:`
- **Funktion** `_load_skeleton_map` Zeilen 844-855
  `def _load_skeleton_map(issue_dir: Path | None = None) -> dict:`
- **Funktion** `_find_imports` Zeilen 858-898
  `def _find_imports(files: list[Path], depth: int = 1) -> list[Path]:`
- **Funktion** `_search_keywords` Zeilen 901-951
  `def _search_keywords(issue_text: str, repo_path: Path) -> list[Path]:`
- **Funktion** `_build_analyse_comment` Zeilen 959-1036
  `def _build_analyse_comment(issue: dict, files: list[Path]) -> str:`
- **Funktion** `_has_detailed_plan` Zeilen 1044-1063
  `def _has_detailed_plan(number: int) -> bool:`
- **Funktion** `_parse_diff_changed_lines` Zeilen 1071-1102
  `def _parse_diff_changed_lines(branch: str) -> dict[str, list[int]]:`
- **Funktion** `_warn_diff_out_of_scope` Zeilen 1105-1191
  `def _warn_diff_out_of_scope(number: int, branch: str) -> None:`
- **Funktion** `_warn_slices_not_requested` Zeilen 1194-1290
  `def _warn_slices_not_requested(number: int, branch: str) -> bool:`
- **Funktion** `_check_pr_preconditions` Zeilen 1293-1444
  `def _check_pr_preconditions(number: int, branch: str) -> None:`
- **Funktion** `_validate_pr_completion` Zeilen 1447-1491
  `def _validate_pr_completion(`
- **Funktion** `_validate_comment` Zeilen 1494-1517
  `def _validate_comment(body: str, comment_type: str, *, critical: bool = False) -> None:`
- **Funktion** `_update_discussion` Zeilen 1520-1555
  `def _update_discussion(issue: dict, starter_path: Path) -> None:`
- **Funktion** `cmd_list` Zeilen 1563-1581
  `def cmd_list() -> None:`
- **Funktion** `cmd_plan` Zeilen 1584-1688
  `def cmd_plan(number: int) -> None:`
- **Funktion** `cmd_implement` Zeilen 1691-1834
  `def cmd_implement(number: int) -> None:`
- **Funktion** `_neustart_required` Zeilen 1847-1852
  `def _neustart_required(changed_files: list[str]) -> str:`
- **Funktion** `cmd_pr` Zeilen 1855-2020
  `def cmd_pr(`
- **Funktion** `cmd_generate_tests` Zeilen 2024-2049
  `def cmd_generate_tests(number: int) -> None:`
- **Funktion** `_current_issue_from_branch` Zeilen 2051-2066
  `def _current_issue_from_branch() -> int | None:`
- **Funktion** `_estimate_slice_tokens` Zeilen 2069-2080
  `def _estimate_slice_tokens(spec: str) -> int:`
- **Funktion** `_log_slice_request` Zeilen 2083-2125
  `def _log_slice_request(spec: str) -> None:`
- **Funktion** `cmd_get_slice` Zeilen 2128-2158
  `def cmd_get_slice(spec: str) -> None:`
- **Funktion** `cmd_get_llm_cmd` Zeilen 2161-2175
  `def cmd_get_llm_cmd(task: str) -> None:`
- **Funktion** `cmd_fixup` Zeilen 2184-2228
  `def cmd_fixup(number: int) -> None:`
- **Funktion** `_auto_issue_exists` Zeilen 2236-2240
  `def _auto_issue_exists(test_name: str) -> bool:`
- **Funktion** `_auto_perf_issue_exists` Zeilen 2242-2246
  `def _auto_perf_issue_exists(test_name: str) -> bool:`
- **Funktion** `_auto_improvement_issue_exists` Zeilen 2250-2253
  `def _auto_improvement_issue_exists(tag: str) -> bool:`
- **Funktion** `_check_systematic_tag_failures` Zeilen 2255-2329
  `def _check_systematic_tag_failures(project_root) -> None:`
- **Funktion** `_sync_closed_contexts` Zeilen 2332-2357
  `def _sync_closed_contexts() -> None:`
- **Funktion** `_consecutive_passes_for_test` Zeilen 2360-2385
  `def _consecutive_passes_for_test(test_name: str) -> int:`
- **Funktion** `_close_resolved_auto_issues` Zeilen 2388-2467
  `def _close_resolved_auto_issues(result: "evaluation.EvalResult") -> None:`
- **Funktion** `_build_metadata` Zeilen 2470-2549
  `def _build_metadata(`
- **Funktion** `_session_path` Zeilen 2552-2554
  `def _session_path() -> Path:`
- **Funktion** `_session_load` Zeilen 2557-2581
  `def _session_load() -> dict:`
- **Funktion** `_session_increment` Zeilen 2584-2594
  `def _session_increment() -> dict:`
- **Funktion** `_session_status_line` Zeilen 2597-2610
  `def _session_status_line(data: dict) -> str:`
- **Funktion** `_format_history_block` Zeilen 2613-2649
  `def _format_history_block(project_root: Path, n: int = 5) -> str:`
- **Funktion** `_last_chat_inactive_minutes` Zeilen 2652-2700
  `def _last_chat_inactive_minutes(log_path: str | Path) -> float | None:`
- **Funktion** `_server_start_time` Zeilen 2703-2751
  `def _server_start_time(log_path: str | Path) -> datetime.datetime | None:`
- **Funktion** `_check_server_staleness` Zeilen 2754-2822
  `def _check_server_staleness(branch: str, force: bool = False) -> None:`
- **Funktion** `_restart_server_for_eval` Zeilen 2825-2847
  `def _restart_server_for_eval() -> None:`
- **Funktion** `_has_new_commits_since_last_eval` Zeilen 2850-2881
  `def _has_new_commits_since_last_eval(project_root: Path) -> bool:`
- **Funktion** `_wait_for_server` Zeilen 2884-2929
  `def _wait_for_server(`
- **Funktion** `cmd_eval_after_restart` Zeilen 2932-2994
  `def cmd_eval_after_restart(number: int | None = None) -> None:`
- **Funktion** `_ast_diff` Zeilen 2997-3037
  `def _ast_diff(old_content: str, new_content: str) -> list[str]:`
- **Funktion** `_gitea_version_compare` Zeilen 3040-3091
  `def _gitea_version_compare(commit: str, changed_files: list[str]) -> str:`
- **Funktion** `_build_auto_issue_body` Zeilen 3094-3209
  `def _build_auto_issue_body(`
- **Funktion** `cmd_watch` Zeilen 3212-3389
  `def cmd_watch(interval_minutes: int = 60, patch_mode: bool = False) -> None:`
- **Funktion** `_dashboard_event` Zeilen 3397-3404
  `def _dashboard_event(context: str = "") -> None:`
- **Funktion** `cmd_install_service` Zeilen 3430-3475
  `def cmd_install_service() -> None:`
- **Funktion** `cmd_dashboard` Zeilen 3483-3489
  `def cmd_dashboard() -> None:`
- **Funktion** `cmd_auto` Zeilen 3491-3583
  `def cmd_auto() -> None:`
- **Funktion** `_apply_auto_approve` Zeilen 3591-3619
  `def _apply_auto_approve() -> None:`
- **Funktion** `cmd_heal` Zeilen 3626-3725
  `def cmd_heal(test_name: str = "", log_lines: int = 30) -> None:`
- **Funktion** `cmd_doctor` Zeilen 3728-3876
  `def cmd_doctor() -> None:`
- **Funktion** `cmd_setup` Zeilen 3883-4078
  `def cmd_setup() -> None:`
- **Funktion** `main` Zeilen 4081-4301
  `def main():`
- **Funktion** `_sym_map` Zeilen 3008-3010
  `def _sym_map(content: str) -> dict[str, dict]:`
- **Funktion** `_chk` Zeilen 3734-3735
  `def _chk(name: str, status: str, detail: str = "", fix: str = "") -> None:`
- **Funktion** `_ask` Zeilen 3887-3890
  `def _ask(prompt: str, default: str = "") -> str:`
- **Funktion** `_api_get_raw` Zeilen 3892-3899
  `def _api_get_raw(url, user, token, path):`
- **Funktion** `_api_post_raw` Zeilen 3901-3911
  `def _api_post_raw(url, user, token, path, data: dict):`
- **Funktion** `_len` Zeilen 3021-3026
  `def _len(s: dict) -> int:`

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

## dashboard.py  *(299 Zeilen)*

- **Funktion** `generate` Zeilen 139-295
  `def generate(project_root: Path):`

## settings.py  *(329 Zeilen)*

- **Funktion** `_env` Zeilen 16-25
  `def _env(key: str, default: str = "") -> str:`
- **Funktion** `_env_list` Zeilen 28-30
  `def _env_list(key: str, default: str) -> list[str]:`
- **Funktion** `_env_int` Zeilen 33-37
  `def _env_int(key: str, default: int) -> int:`
- **Funktion** `_env_bool` Zeilen 40-41
  `def _env_bool(key: str, default: bool = False) -> bool:`
- **Funktion** `_load_features` Zeilen 284-303
  `def _load_features() -> dict:`
- **Funktion** `_load_project_type` Zeilen 308-319
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

## log.py  *(81 Zeilen)*

- **Funktion** `setup` Zeilen 25-68
  `def setup(log_file: str = "gitea-agent.log", level: str = "INFO") -> None:`
- **Funktion** `get_logger` Zeilen 71-81
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

## plugins/health.py  *(174 Zeilen)*

- **Klasse** `CheckResult` Zeilen 36-41
  `class CheckResult:`
- **Klasse** `HealthResult` Zeilen 45-51
  `class HealthResult:`
- **Funktion** `_load_config` Zeilen 54-62
  `def _load_config(project_root: Path) -> dict | None:`
- **Funktion** `_check_http` Zeilen 65-73
  `def _check_http(target: str, timeout: int = 5) -> tuple[bool, str]:`
- **Funktion** `_check_tcp` Zeilen 76-83
  `def _check_tcp(target: str, timeout: int = 3) -> tuple[bool, str]:`
- **Funktion** `_check_process` Zeilen 86-95
  `def _check_process(target: str) -> tuple[bool, str]:`
- **Funktion** `_check_disk` Zeilen 98-106
  `def _check_disk(target: str, threshold: int = 90) -> tuple[bool, str]:`
- **Funktion** `run_checks` Zeilen 109-164
  `def run_checks(project_root: Path) -> HealthResult:`
- **Funktion** `format_terminal` Zeilen 167-174
  `def format_terminal(result: HealthResult) -> str:`
- **Funktion** `all_passed` Zeilen 50-51
  `def all_passed(self) -> bool:`

## plugins/llm.py  *(438 Zeilen)*

- **Funktion** `_load_routing` Zeilen 40-49
  `def _load_routing(extra_path: Optional[Path] = None) -> dict:`
- **Funktion** `_resolve_task_config` Zeilen 52-63
  `def _resolve_task_config(task: str, routing: dict) -> dict:`
- **Funktion** `_load_system_prompt` Zeilen 66-81
  `def _load_system_prompt(cfg: dict) -> str:`
- **Klasse** `LLMResponse` Zeilen 89-98
  `class LLMResponse:`
- **Funktion** `_http_post` Zeilen 105-109
  `def _http_post(url: str, payload: dict, headers: dict, timeout: int) -> dict:`
- **Klasse** `ClaudeClient` Zeilen 112-150
  `class ClaudeClient:`
- **Klasse** `OpenAIClient` Zeilen 153-191
  `class OpenAIClient:`
- **Klasse** `DeepseekClient` Zeilen 194-203
  `class DeepseekClient(OpenAIClient):`
- **Klasse** `LMStudioClient` Zeilen 206-216
  `class LMStudioClient(OpenAIClient):`
- **Klasse** `GeminiClient` Zeilen 219-252
  `class GeminiClient:`
- **Klasse** `LocalClient` Zeilen 255-285
  `class LocalClient:`
- **Funktion** `_client_from_env` Zeilen 292-331
  `def _client_from_env() -> Optional["ClaudeClient | LocalClient"]:`
- **Funktion** `_build_client` Zeilen 334-387
  `def _build_client(cfg: dict) -> "ClaudeClient | OpenAIClient | GeminiClient | LocalClient":`
- **Funktion** `get_client` Zeilen 394-423
  `def get_client(`
- **Funktion** `complete` Zeilen 426-438
  `def complete(`
- **Funktion** `ok` Zeilen 97-98
  `def ok(self) -> bool:`
- **Funktion** `__init__` Zeilen 118-124
  `def __init__(self, model: str, api_key: str, max_tokens: int = 1024, timeout: int = 60,`
- **Funktion** `complete` Zeilen 126-150
  `def complete(self, prompt: str) -> LLMResponse:`
- **Funktion** `__init__` Zeilen 158-165
  `def __init__(self, model: str, api_key: str, base_url: str = "https://api.openai.com/v1",`
- **Funktion** `complete` Zeilen 167-191
  `def complete(self, prompt: str) -> LLMResponse:`
- **Funktion** `__init__` Zeilen 200-203
  `def __init__(self, model: str, api_key: str, max_tokens: int = 1024, timeout: int = 60):`
- **Funktion** `__init__` Zeilen 212-216
  `def __init__(self, model: str, api_key: str = "lm-studio",`
- **Funktion** `__init__` Zeilen 224-230
  `def __init__(self, model: str, api_key: str, max_tokens: int = 1024, timeout: int = 60,`
- **Funktion** `complete` Zeilen 232-252
  `def complete(self, prompt: str) -> LLMResponse:`
- **Funktion** `__init__` Zeilen 258-264
  `def __init__(self, model: str, base_url: str = "http://localhost:11434",`
- **Funktion** `complete` Zeilen 266-285
  `def complete(self, prompt: str) -> LLMResponse:`
- **Funktion** `_get` Zeilen 308-309
  `def _get(key: str, default: str = "") -> str:`
- **Funktion** `_get_key` Zeilen 337-347
  `def _get_key(env_var: str) -> str:`

## plugins/__init__.py  *(0 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## plugins/llm_config_guard.py  *(376 Zeilen)*

- **Klasse** `ConfigFileResult` Zeilen 81-90
  `class ConfigFileResult:`
- **Klasse** `SkeletonResult` Zeilen 94-103
  `class SkeletonResult:`
- **Klasse** `GuardResult` Zeilen 107-120
  `class GuardResult:`
- **Funktion** `check_skeleton_fresh` Zeilen 127-158
  `def check_skeleton_fresh(project_root: Path) -> SkeletonResult:`
- **Funktion** `check` Zeilen 165-190
  `def check(project_root: Path, check_skeleton: bool = True) -> GuardResult:`
- **Funktion** `repair` Zeilen 193-240
  `def repair(project_root: Path, create_missing: bool = False) -> list[str]:`
- **Funktion** `_extract_missing_sections` Zeilen 243-274
  `def _extract_missing_sections(`
- **Funktion** `_build_minimal_block` Zeilen 277-290
  `def _build_minimal_block(missing_markers: list[str]) -> str:`
- **Funktion** `_fmt_age` Zeilen 297-302
  `def _fmt_age(seconds: int) -> str:`
- **Funktion** `_print_result` Zeilen 305-327
  `def _print_result(result: GuardResult, verbose: bool = False) -> None:`
- **Funktion** `main` Zeilen 330-372
  `def main(argv: list[str] | None = None) -> int:`
- **Funktion** `ok` Zeilen 88-90
  `def ok(self) -> bool:`
- **Funktion** `ok` Zeilen 102-103
  `def ok(self) -> bool:`
- **Funktion** `all_ok` Zeilen 112-115
  `def all_ok(self) -> bool:`
- **Funktion** `failures` Zeilen 118-120
  `def failures(self) -> list[ConfigFileResult]:`
- **Funktion** `_flush` Zeilen 255-264
  `def _flush():`

## plugins/healing.py  *(474 Zeilen)*

- **Funktion** `_load_healing_cfg` Zeilen 40-53
  `def _load_healing_cfg(project_root: Path) -> dict:`
- **Klasse** `HealingAttempt` Zeilen 61-68
  `class HealingAttempt:`
- **Klasse** `HealingResult` Zeilen 72-86
  `class HealingResult:`
- **Funktion** `_git` Zeilen 93-96
  `def _git(args: list[str], cwd: Path) -> str:`
- **Funktion** `_git_run` Zeilen 99-103
  `def _git_run(args: list[str], cwd: Path) -> bool:`
- **Funktion** `_current_branch` Zeilen 106-107
  `def _current_branch(project_root: Path) -> str:`
- **Funktion** `_short_hash` Zeilen 110-114
  `def _short_hash(project_root: Path) -> str:`
- **Funktion** `_create_temp_branch` Zeilen 117-121
  `def _create_temp_branch(project_root: Path) -> str:`
- **Funktion** `_delete_branch` Zeilen 124-129
  `def _delete_branch(project_root: Path, branch: str) -> None:`
- **Funktion** `_cherry_pick` Zeilen 132-149
  `def _cherry_pick(project_root: Path, from_branch: str, onto_branch: str) -> bool:`
- **Funktion** `_estimate_tokens` Zeilen 156-158
  `def _estimate_tokens(text: str) -> int:`
- **Funktion** `_call_llm_local` Zeilen 161-173
  `def _call_llm_local(url: str, model: str, prompt: str, timeout: int) -> str:`
- **Funktion** `_call_llm_claude` Zeilen 176-183
  `def _call_llm_claude(model: str, prompt: str) -> str:`
- **Funktion** `_build_fix_prompt` Zeilen 186-225
  `def _build_fix_prompt(`
- **Funktion** `_parse_fix` Zeilen 228-242
  `def _parse_fix(llm_output: str) -> list[dict]:`
- **Funktion** `_apply_fixes` Zeilen 245-258
  `def _apply_fixes(project_root: Path, fixes: list[dict]) -> tuple[bool, list[str], str]:`
- **Funktion** `_run_eval` Zeilen 265-280
  `def _run_eval(project_root: Path) -> tuple[bool, float, str]:`
- **Funktion** `run_healing_loop` Zeilen 287-450
  `def run_healing_loop(`
- **Funktion** `format_terminal` Zeilen 457-474
  `def format_terminal(result: HealingResult) -> str:`
- **Funktion** `attempt_count` Zeilen 85-86
  `def attempt_count(self) -> int:`

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

## tests/test_health.py  *(247 Zeilen)*

- **Klasse** `TestCheckResult` Zeilen 25-34
  `class TestCheckResult(unittest.TestCase):`
- **Klasse** `TestHealthResult` Zeilen 37-45
  `class TestHealthResult(unittest.TestCase):`
- **Klasse** `TestCheckHttp` Zeilen 48-79
  `class TestCheckHttp(unittest.TestCase):`
- **Klasse** `TestCheckTcp` Zeilen 82-99
  `class TestCheckTcp(unittest.TestCase):`
- **Klasse** `TestCheckProcess` Zeilen 102-113
  `class TestCheckProcess(unittest.TestCase):`
- **Klasse** `TestCheckDisk` Zeilen 116-137
  `class TestCheckDisk(unittest.TestCase):`
- **Klasse** `TestRunChecks` Zeilen 140-223
  `class TestRunChecks(unittest.TestCase):`
- **Klasse** `TestFormatTerminal` Zeilen 226-243
  `class TestFormatTerminal(unittest.TestCase):`
- **Funktion** `test_defaults` Zeilen 26-29
  `def test_defaults(self):`
- **Funktion** `test_failed` Zeilen 31-34
  `def test_failed(self):`
- **Funktion** `test_all_passed_empty` Zeilen 38-40
  `def test_all_passed_empty(self):`
- **Funktion** `test_all_passed_with_failures` Zeilen 42-45
  `def test_all_passed_with_failures(self):`
- **Funktion** `test_ok_response` Zeilen 49-57
  `def test_ok_response(self):`
- **Funktion** `test_server_error` Zeilen 59-66
  `def test_server_error(self):`
- **Funktion** `test_client_error_is_ok` Zeilen 68-74
  `def test_client_error_is_ok(self):`
- **Funktion** `test_connection_error` Zeilen 76-79
  `def test_connection_error(self):`
- **Funktion** `test_reachable` Zeilen 83-90
  `def test_reachable(self):`
- **Funktion** `test_unreachable` Zeilen 92-95
  `def test_unreachable(self):`
- **Funktion** `test_invalid_target` Zeilen 97-99
  `def test_invalid_target(self):`
- **Funktion** `test_found` Zeilen 103-107
  `def test_found(self):`
- **Funktion** `test_not_found` Zeilen 109-113
  `def test_not_found(self):`
- **Funktion** `test_below_threshold` Zeilen 117-124
  `def test_below_threshold(self):`
- **Funktion** `test_above_threshold` Zeilen 126-132
  `def test_above_threshold(self):`
- **Funktion** `test_path_error` Zeilen 134-137
  `def test_path_error(self):`
- **Funktion** `_make_config` Zeilen 141-146
  `def _make_config(self, tmp_path: Path, checks: list, threshold: int = 3) -> Path:`
- **Funktion** `test_no_config` Zeilen 148-153
  `def test_no_config(self):`
- **Funktion** `test_http_check_passes` Zeilen 155-169
  `def test_http_check_passes(self):`
- **Funktion** `test_consecutive_failures_threshold` Zeilen 171-185
  `def test_consecutive_failures_threshold(self):`
- **Funktion** `test_consecutive_failures_exceed_threshold` Zeilen 187-203
  `def test_consecutive_failures_exceed_threshold(self):`
- **Funktion** `test_recovery_clears_state` Zeilen 205-223
  `def test_recovery_clears_state(self):`
- **Funktion** `test_empty` Zeilen 227-228
  `def test_empty(self):`
- **Funktion** `test_passed` Zeilen 230-235
  `def test_passed(self):`
- **Funktion** `test_failed` Zeilen 237-243
  `def test_failed(self):`

## tests/test_llm.py  *(337 Zeilen)*

- **Klasse** `TestLLMResponse` Zeilen 29-40
  `class TestLLMResponse(unittest.TestCase):`
- **Klasse** `TestLoadRouting` Zeilen 43-66
  `class TestLoadRouting(unittest.TestCase):`
- **Klasse** `TestResolveTaskConfig` Zeilen 69-96
  `class TestResolveTaskConfig(unittest.TestCase):`
- **Klasse** `TestBuildClient` Zeilen 99-142
  `class TestBuildClient(unittest.TestCase):`
- **Klasse** `TestClaudeClient` Zeilen 145-177
  `class TestClaudeClient(unittest.TestCase):`
- **Klasse** `TestOpenAIClient` Zeilen 180-200
  `class TestOpenAIClient(unittest.TestCase):`
- **Klasse** `TestGeminiClient` Zeilen 203-217
  `class TestGeminiClient(unittest.TestCase):`
- **Klasse** `TestDeepseekClient` Zeilen 220-246
  `class TestDeepseekClient(unittest.TestCase):`
- **Klasse** `TestLMStudioClient` Zeilen 249-271
  `class TestLMStudioClient(unittest.TestCase):`
- **Klasse** `TestLocalClient` Zeilen 274-291
  `class TestLocalClient(unittest.TestCase):`
- **Klasse** `TestGetClient` Zeilen 294-321
  `class TestGetClient(unittest.TestCase):`
- **Klasse** `TestCompleteConvenience` Zeilen 324-333
  `class TestCompleteConvenience(unittest.TestCase):`
- **Funktion** `test_ok_with_text` Zeilen 30-32
  `def test_ok_with_text(self):`
- **Funktion** `test_not_ok_empty` Zeilen 34-36
  `def test_not_ok_empty(self):`
- **Funktion** `test_not_ok_with_error` Zeilen 38-40
  `def test_not_ok_with_error(self):`
- **Funktion** `test_no_config` Zeilen 44-46
  `def test_no_config(self):`
- **Funktion** `test_valid_config` Zeilen 48-58
  `def test_valid_config(self):`
- **Funktion** `test_invalid_json` Zeilen 60-66
  `def test_invalid_json(self):`
- **Funktion** `setUp` Zeilen 70-77
  `def setUp(self):`
- **Funktion** `test_known_task` Zeilen 79-81
  `def test_known_task(self):`
- **Funktion** `test_unknown_task_falls_back_to_default` Zeilen 83-86
  `def test_unknown_task_falls_back_to_default(self):`
- **Funktion** `test_default_as_string` Zeilen 88-92
  `def test_default_as_string(self):`
- **Funktion** `test_empty_routing` Zeilen 94-96
  `def test_empty_routing(self):`
- **Funktion** `test_claude` Zeilen 100-103
  `def test_claude(self):`
- **Funktion** `test_openai` Zeilen 105-107
  `def test_openai(self):`
- **Funktion** `test_gemini` Zeilen 109-111
  `def test_gemini(self):`
- **Funktion** `test_local` Zeilen 113-117
  `def test_local(self):`
- **Funktion** `test_ollama_alias` Zeilen 119-121
  `def test_ollama_alias(self):`
- **Funktion** `test_deepseek` Zeilen 123-127
  `def test_deepseek(self):`
- **Funktion** `test_lmstudio` Zeilen 129-132
  `def test_lmstudio(self):`
- **Funktion** `test_lmstudio_custom_url` Zeilen 134-138
  `def test_lmstudio_custom_url(self):`
- **Funktion** `test_unknown_provider_falls_back_to_local` Zeilen 140-142
  `def test_unknown_provider_falls_back_to_local(self):`
- **Funktion** `_mock_response` Zeilen 146-154
  `def _mock_response(self, text: str, input_tokens: int = 10, output_tokens: int = 20):`
- **Funktion** `test_success` Zeilen 156-163
  `def test_success(self):`
- **Funktion** `test_api_error` Zeilen 165-171
  `def test_api_error(self):`
- **Funktion** `test_connection_error` Zeilen 173-177
  `def test_connection_error(self):`
- **Funktion** `test_success` Zeilen 181-194
  `def test_success(self):`
- **Funktion** `test_connection_error` Zeilen 196-200
  `def test_connection_error(self):`
- **Funktion** `test_success` Zeilen 204-217
  `def test_success(self):`
- **Funktion** `test_success` Zeilen 221-235
  `def test_success(self):`
- **Funktion** `test_uses_deepseek_base_url` Zeilen 237-239
  `def test_uses_deepseek_base_url(self):`
- **Funktion** `test_connection_error` Zeilen 241-246
  `def test_connection_error(self):`
- **Funktion** `test_success` Zeilen 250-263
  `def test_success(self):`
- **Funktion** `test_default_url` Zeilen 265-267
  `def test_default_url(self):`
- **Funktion** `test_no_api_key_required` Zeilen 269-271
  `def test_no_api_key_required(self):`
- **Funktion** `test_success` Zeilen 275-285
  `def test_success(self):`
- **Funktion** `test_connection_error` Zeilen 287-291
  `def test_connection_error(self):`
- **Funktion** `test_no_routing_falls_back_to_env` Zeilen 295-301
  `def test_no_routing_falls_back_to_env(self):`
- **Funktion** `test_routing_selects_correct_provider` Zeilen 303-310
  `def test_routing_selects_correct_provider(self):`
- **Funktion** `test_default_used_for_unknown_task` Zeilen 312-321
  `def test_default_used_for_unknown_task(self):`
- **Funktion** `test_delegates_to_client` Zeilen 325-333
  `def test_delegates_to_client(self):`

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

## tests/test_healing.py  *(192 Zeilen)*

- **Klasse** `TestEstimateTokens` Zeilen 24-30
  `class TestEstimateTokens(unittest.TestCase):`
- **Klasse** `TestParseFix` Zeilen 33-68
  `class TestParseFix(unittest.TestCase):`
- **Klasse** `TestApplyFixes` Zeilen 71-99
  `class TestApplyFixes(unittest.TestCase):`
- **Klasse** `TestBuildFixPrompt` Zeilen 102-121
  `class TestBuildFixPrompt(unittest.TestCase):`
- **Klasse** `TestRunHealingLoopSkipped` Zeilen 124-147
  `class TestRunHealingLoopSkipped(unittest.TestCase):`
- **Klasse** `TestHealingResult` Zeilen 150-158
  `class TestHealingResult(unittest.TestCase):`
- **Klasse** `TestFormatTerminal` Zeilen 161-188
  `class TestFormatTerminal(unittest.TestCase):`
- **Funktion** `test_empty` Zeilen 25-26
  `def test_empty(self):`
- **Funktion** `test_approximation` Zeilen 28-30
  `def test_approximation(self):`
- **Funktion** `test_valid_block` Zeilen 34-47
  `def test_valid_block(self):`
- **Funktion** `test_no_block` Zeilen 49-51
  `def test_no_block(self):`
- **Funktion** `test_multiple_blocks` Zeilen 53-68
  `def test_multiple_blocks(self):`
- **Funktion** `test_successful_replace` Zeilen 72-81
  `def test_successful_replace(self):`
- **Funktion** `test_file_not_found` Zeilen 83-89
  `def test_file_not_found(self):`
- **Funktion** `test_search_not_found` Zeilen 91-99
  `def test_search_not_found(self):`
- **Funktion** `test_contains_test_name` Zeilen 103-109
  `def test_contains_test_name(self):`
- **Funktion** `test_contains_attempt_history` Zeilen 111-121
  `def test_contains_attempt_history(self):`
- **Funktion** `test_feature_not_enabled_skipped_if_no_llm` Zeilen 125-134
  `def test_feature_not_enabled_skipped_if_no_llm(self):`
- **Funktion** `test_git_error_skipped` Zeilen 136-147
  `def test_git_error_skipped(self):`
- **Funktion** `test_attempt_count` Zeilen 151-158
  `def test_attempt_count(self):`
- **Funktion** `test_skipped` Zeilen 162-166
  `def test_skipped(self):`
- **Funktion** `test_success` Zeilen 168-177
  `def test_success(self):`
- **Funktion** `test_failure` Zeilen 179-188
  `def test_failure(self):`

## tests/test_log_analyzer.py  *(221 Zeilen)*

- **Klasse** `TestKnownPatterns` Zeilen 19-64
  `class TestKnownPatterns(unittest.TestCase):`
- **Klasse** `TestRunSkipped` Zeilen 67-78
  `class TestRunSkipped(unittest.TestCase):`
- **Klasse** `TestRunWithLog` Zeilen 81-172
  `class TestRunWithLog(unittest.TestCase):`
- **Klasse** `TestFormatTerminal` Zeilen 175-217
  `class TestFormatTerminal(unittest.TestCase):`
- **Funktion** `test_connection_refused` Zeilen 20-24
  `def test_connection_refused(self):`
- **Funktion** `test_timeout` Zeilen 26-30
  `def test_timeout(self):`
- **Funktion** `test_memory_error` Zeilen 32-36
  `def test_memory_error(self):`
- **Funktion** `test_import_error` Zeilen 38-42
  `def test_import_error(self):`
- **Funktion** `test_permission_error` Zeilen 44-48
  `def test_permission_error(self):`
- **Funktion** `test_no_match` Zeilen 50-53
  `def test_no_match(self):`
- **Funktion** `test_one_finding_per_line` Zeilen 55-59
  `def test_one_finding_per_line(self):`
- **Funktion** `test_line_numbers` Zeilen 61-64
  `def test_line_numbers(self):`
- **Funktion** `test_no_log_path_in_config` Zeilen 68-72
  `def test_no_log_path_in_config(self):`
- **Funktion** `test_log_file_missing` Zeilen 74-78
  `def test_log_file_missing(self):`
- **Funktion** `_make_log` Zeilen 82-85
  `def _make_log(self, tmp_path, content: str) -> Path:`
- **Funktion** `test_clean_log` Zeilen 87-98
  `def test_clean_log(self):`
- **Funktion** `test_log_with_errors` Zeilen 100-111
  `def test_log_with_errors(self):`
- **Funktion** `test_tail_lines_respected` Zeilen 113-125
  `def test_tail_lines_respected(self):`
- **Funktion** `test_llm_enabled_no_server` Zeilen 127-140
  `def test_llm_enabled_no_server(self):`
- **Funktion** `test_llm_local_called` Zeilen 142-157
  `def test_llm_local_called(self):`
- **Funktion** `test_claude_api_called` Zeilen 159-172
  `def test_claude_api_called(self):`
- **Funktion** `test_skipped` Zeilen 176-179
  `def test_skipped(self):`
- **Funktion** `test_clean` Zeilen 181-184
  `def test_clean(self):`
- **Funktion** `test_with_findings` Zeilen 186-194
  `def test_with_findings(self):`
- **Funktion** `test_with_llm_summary` Zeilen 196-201
  `def test_with_llm_summary(self):`
- **Funktion** `test_with_llm_error` Zeilen 203-207
  `def test_with_llm_error(self):`
- **Funktion** `test_max_10_findings_shown` Zeilen 209-217
  `def test_max_10_findings_shown(self):`

## tests/test_slice_gate.py  *(105 Zeilen)*

- **Klasse** `TestSliceGateSettings` Zeilen 14-19
  `class TestSliceGateSettings(unittest.TestCase):`
- **Klasse** `TestWarnSlicesNotRequested` Zeilen 22-101
  `class TestWarnSlicesNotRequested(unittest.TestCase):`
- **Funktion** `test_disabled_by_default` Zeilen 15-16
  `def test_disabled_by_default(self):`
- **Funktion** `test_min_lines_default` Zeilen 18-19
  `def test_min_lines_default(self):`
- **Funktion** `setUp` Zeilen 23-25
  `def setUp(self):`
- **Funktion** `_patch_diff` Zeilen 27-31
  `def _patch_diff(self, changed_files: list[str]):`
- **Funktion** `test_no_py_files_changed` Zeilen 33-36
  `def test_no_py_files_changed(self):`
- **Funktion** `test_small_files_ignored` Zeilen 38-50
  `def test_small_files_ignored(self):`
- **Funktion** `test_large_file_no_slices` Zeilen 52-64
  `def test_large_file_no_slices(self):`
- **Funktion** `test_large_file_with_matching_slice` Zeilen 66-84
  `def test_large_file_with_matching_slice(self):`
- **Funktion** `test_gate_blocks_when_enabled` Zeilen 86-101
  `def test_gate_blocks_when_enabled(self):`

## tests/test_token_budget.py  *(79 Zeilen)*

- **Klasse** `TestEstimateSliceTokens` Zeilen 13-39
  `class TestEstimateSliceTokens(unittest.TestCase):`
- **Klasse** `TestTokenBudgetSettings` Zeilen 42-51
  `class TestTokenBudgetSettings(unittest.TestCase):`
- **Klasse** `TestTokenAccumulation` Zeilen 54-75
  `class TestTokenAccumulation(unittest.TestCase):`
- **Funktion** `setUp` Zeilen 14-17
  `def setUp(self):`
- **Funktion** `test_range` Zeilen 19-22
  `def test_range(self):`
- **Funktion** `test_single_line` Zeilen 24-26
  `def test_single_line(self):`
- **Funktion** `test_large_range` Zeilen 28-30
  `def test_large_range(self):`
- **Funktion** `test_invalid_spec` Zeilen 32-35
  `def test_invalid_spec(self):`
- **Funktion** `test_invalid_range` Zeilen 37-39
  `def test_invalid_range(self):`
- **Funktion** `test_warn_threshold_positive` Zeilen 43-44
  `def test_warn_threshold_positive(self):`
- **Funktion** `test_lines_factor_positive` Zeilen 46-47
  `def test_lines_factor_positive(self):`
- **Funktion** `test_defaults` Zeilen 49-51
  `def test_defaults(self):`
- **Funktion** `test_cumulative_sum` Zeilen 57-65
  `def test_cumulative_sum(self):`
- **Funktion** `test_threshold_detection` Zeilen 67-75
  `def test_threshold_detection(self):`

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

## config/log_analyzer.py  *(317 Zeilen)*

- **Funktion** `_load_eval_cfg` Zeilen 39-46
  `def _load_eval_cfg() -> dict:`
- **Klasse** `LogFinding` Zeilen 104-110
  `class LogFinding:`
- **Klasse** `LogAnalysisResult` Zeilen 114-129
  `class LogAnalysisResult:`
- **Funktion** `_analyze_rules` Zeilen 136-154
  `def _analyze_rules(lines: list[str]) -> list[LogFinding]:`
- **Funktion** `_call_llm_local` Zeilen 161-177
  `def _call_llm_local(url: str, model: str, prompt: str, timeout: int) -> str:`
- **Funktion** `_call_llm_claude` Zeilen 180-189
  `def _call_llm_claude(model: str, prompt: str, max_tokens: int = 512) -> str:`
- **Funktion** `_analyze_llm` Zeilen 192-231
  `def _analyze_llm(lines: list[str], rule_findings: list[LogFinding], cfg: dict) -> tuple[str, str]:`
- **Funktion** `run` Zeilen 238-283
  `def run() -> LogAnalysisResult:`
- **Funktion** `format_terminal` Zeilen 290-317
  `def format_terminal(result: LogAnalysisResult) -> str:`
- **Funktion** `error_count` Zeilen 124-125
  `def error_count(self) -> int:`
- **Funktion** `tags` Zeilen 128-129
  `def tags(self) -> list[str]:`
