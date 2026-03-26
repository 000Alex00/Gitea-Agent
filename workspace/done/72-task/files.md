# Dateien — Issue #72
> Skelett-Modus aktiv — **kein Volltext**. Nutze `--get-slice datei.py:START-END` für Code-Details.
> Automatisch erkannt via Backtick-Erwähnungen, Import-Analyse (AST) und Keyword-Suche (grep).

# Repo-Skelett


---

## agent_start.py  *(3684 Zeilen)*
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
  - Funktion `cmd_pr` Zeilen 1773-1931  `def cmd_pr(`
  - Funktion `cmd_generate_tests` Zeilen 1935-1960  `def cmd_generate_tests(number: int) -> None:`
  - Funktion `_current_issue_from_branch` Zeilen 1962-1977  `def _current_issue_from_branch() -> int | None:`
  - Funktion `_log_slice_request` Zeilen 1980-2001  `def _log_slice_request(spec: str) -> None:`
  - Funktion `cmd_get_slice` Zeilen 2004-2034  `def cmd_get_slice(spec: str) -> None:`
  - Funktion `_parse_search_replace` Zeilen 2046-2092  `def _parse_search_replace(text: str) -> list[dict]:`
  - Funktion `_normalize_ws` Zeilen 2095-2097  `def _normalize_ws(text: str) -> str:`
  - Funktion `_apply_patch` Zeilen 2100-2162  `def _apply_patch(`
  - Funktion `cmd_apply_patch` Zeilen 2165-2215  `def cmd_apply_patch(number: int, dry_run: bool = False) -> None:`
  - Funktion `cmd_fixup` Zeilen 2218-2262  `def cmd_fixup(number: int) -> None:`
  - Funktion `_auto_issue_exists` Zeilen 2270-2274  `def _auto_issue_exists(test_name: str) -> bool:`
  - Funktion `_auto_perf_issue_exists` Zeilen 2276-2280  `def _auto_perf_issue_exists(test_name: str) -> bool:`
  - Funktion `_auto_improvement_issue_exists` Zeilen 2284-2287  `def _auto_improvement_issue_exists(tag: str) -> bool:`
  - Funktion `_check_systematic_tag_failures` Zeilen 2289-2363  `def _check_systematic_tag_failures(project_root) -> None:`
  - Funktion `_sync_closed_contexts` Zeilen 2366-2391  `def _sync_closed_contexts() -> None:`
  - Funktion `_consecutive_passes_for_test` Zeilen 2394-2419  `def _consecutive_passes_for_test(test_name: str) -> int:`
  - Funktion `_close_resolved_auto_issues` Zeilen 2422-2501  `def _close_resolved_auto_issues(result: "evaluation.EvalResult") -> None:`
  - Funktion `_build_metadata` Zeilen 2504-2583  `def _build_metadata(`
  - Funktion `_session_path` Zeilen 2586-2588  `def _session_path() -> Path:`
  - Funktion `_session_load` Zeilen 2591-2615  `def _session_load() -> dict:`
  - Funktion `_session_increment` Zeilen 2618-2628  `def _session_increment() -> dict:`
  - Funktion `_session_status_line` Zeilen 2631-2644  `def _session_status_line(data: dict) -> str:`
  - Funktion `_format_history_block` Zeilen 2647-2683  `def _format_history_block(project_root: Path, n: int = 5) -> str:`
  - Funktion `_last_chat_inactive_minutes` Zeilen 2686-2734  `def _last_chat_inactive_minutes(log_path: str | Path) -> float | None:`
  - Funktion `_server_start_time` Zeilen 2737-2785  `def _server_start_time(log_path: str | Path) -> datetime.datetime | None:`
  - Funktion `_check_server_staleness` Zeilen 2788-2856  `def _check_server_staleness(branch: str, force: bool = False) -> None:`
  - Funktion `_restart_server_for_eval` Zeilen 2859-2881  `def _restart_server_for_eval() -> None:`
  - Funktion `_has_new_commits_since_last_eval` Zeilen 2884-2915  `def _has_new_commits_since_last_eval(project_root: Path) -> bool:`
  - Funktion `_wait_for_server` Zeilen 2918-2963  `def _wait_for_server(`
  - Funktion `cmd_eval_after_restart` Zeilen 2966-3028  `def cmd_eval_after_restart(number: int | None = None) -> None:`
  - Funktion `_build_auto_issue_body` Zeilen 3031-3129  `def _build_auto_issue_body(`
  - Funktion `cmd_watch` Zeilen 3132-3268  `def cmd_watch(interval_minutes: int = 60, patch_mode: bool = False) -> None:`
  - Funktion `_dashboard_event` Zeilen 3276-3283  `def _dashboard_event(context: str = "") -> None:`
  - Funktion `cmd_install_service` Zeilen 3309-3354  `def cmd_install_service() -> None:`
  - Funktion `cmd_dashboard` Zeilen 3362-3368  `def cmd_dashboard() -> None:`
  - Funktion `cmd_auto` Zeilen 3370-3462  `def cmd_auto() -> None:`
  - Funktion `_apply_auto_approve` Zeilen 3470-3498  `def _apply_auto_approve() -> None:`
  - Funktion `main` Zeilen 3501-3680  `def main():`
> Volltext: `python3 agent_start.py --get-slice agent_start.py:1-3684`

## settings.py  *(258 Zeilen)*
  - Funktion `_env` Zeilen 16-25  `def _env(key: str, default: str = "") -> str:`
  - Funktion `_env_list` Zeilen 28-30  `def _env_list(key: str, default: str) -> list[str]:`
  - Funktion `_env_int` Zeilen 33-37  `def _env_int(key: str, default: int) -> int:`
  - Funktion `_env_bool` Zeilen 40-41  `def _env_bool(key: str, default: bool = False) -> bool:`
> Volltext: `python3 agent_start.py --get-slice settings.py:1-258`
