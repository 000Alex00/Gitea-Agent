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

## agent_start.py  *(4037 Zeilen)*

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
- **Funktion** `_get_exclude_dirs` Zeilen 619-639
  `def _get_exclude_dirs(project: Path) -> set[str]:`
- **Funktion** `_extract_ast_symbols` Zeilen 665-687
  `def _extract_ast_symbols(content: str) -> list[dict]:`
- **Funktion** `_create_repo_skeleton` Zeilen 690-744
  `def _create_repo_skeleton(files: list[Path], output_dir: Path, max_size_kb: int = _MAX_SKELETON_FILE_SIZE_KB) -> Path:`
- **Funktion** `_skeleton_to_md` Zeilen 747-766
  `def _skeleton_to_md(skeleton_data: list[dict]) -> str:`
- **Funktion** `cmd_build_skeleton` Zeilen 769-777
  `def cmd_build_skeleton() -> None:`
- **Funktion** `_update_skeleton_incremental` Zeilen 780-812
  `def _update_skeleton_incremental(changed_files: list[str]) -> None:`
- **Funktion** `_load_skeleton_map` Zeilen 815-826
  `def _load_skeleton_map(issue_dir: Path | None = None) -> dict:`
- **Funktion** `_find_imports` Zeilen 829-869
  `def _find_imports(files: list[Path], depth: int = 1) -> list[Path]:`
- **Funktion** `_search_keywords` Zeilen 872-922
  `def _search_keywords(issue_text: str, repo_path: Path) -> list[Path]:`
- **Funktion** `_build_analyse_comment` Zeilen 930-1007
  `def _build_analyse_comment(issue: dict, files: list[Path]) -> str:`
- **Funktion** `_has_detailed_plan` Zeilen 1015-1034
  `def _has_detailed_plan(number: int) -> bool:`
- **Funktion** `_parse_diff_changed_lines` Zeilen 1042-1073
  `def _parse_diff_changed_lines(branch: str) -> dict[str, list[int]]:`
- **Funktion** `_warn_diff_out_of_scope` Zeilen 1076-1162
  `def _warn_diff_out_of_scope(number: int, branch: str) -> None:`
- **Funktion** `_warn_slices_not_requested` Zeilen 1165-1221
  `def _warn_slices_not_requested(number: int, branch: str) -> None:`
- **Funktion** `_check_pr_preconditions` Zeilen 1224-1370
  `def _check_pr_preconditions(number: int, branch: str) -> None:`
- **Funktion** `_validate_pr_completion` Zeilen 1373-1417
  `def _validate_pr_completion(`
- **Funktion** `_validate_comment` Zeilen 1420-1443
  `def _validate_comment(body: str, comment_type: str, *, critical: bool = False) -> None:`
- **Funktion** `_update_discussion` Zeilen 1446-1481
  `def _update_discussion(issue: dict, starter_path: Path) -> None:`
- **Funktion** `cmd_list` Zeilen 1489-1507
  `def cmd_list() -> None:`
- **Funktion** `cmd_plan` Zeilen 1510-1614
  `def cmd_plan(number: int) -> None:`
- **Funktion** `cmd_implement` Zeilen 1617-1760
  `def cmd_implement(number: int) -> None:`
- **Funktion** `_neustart_required` Zeilen 1773-1778
  `def _neustart_required(changed_files: list[str]) -> str:`
- **Funktion** `cmd_pr` Zeilen 1781-1946
  `def cmd_pr(`
- **Funktion** `cmd_generate_tests` Zeilen 1950-1975
  `def cmd_generate_tests(number: int) -> None:`
- **Funktion** `_current_issue_from_branch` Zeilen 1977-1992
  `def _current_issue_from_branch() -> int | None:`
- **Funktion** `_log_slice_request` Zeilen 1995-2016
  `def _log_slice_request(spec: str) -> None:`
- **Funktion** `cmd_get_slice` Zeilen 2019-2049
  `def cmd_get_slice(spec: str) -> None:`
- **Funktion** `cmd_fixup` Zeilen 2058-2102
  `def cmd_fixup(number: int) -> None:`
- **Funktion** `_auto_issue_exists` Zeilen 2110-2114
  `def _auto_issue_exists(test_name: str) -> bool:`
- **Funktion** `_auto_perf_issue_exists` Zeilen 2116-2120
  `def _auto_perf_issue_exists(test_name: str) -> bool:`
- **Funktion** `_auto_improvement_issue_exists` Zeilen 2124-2127
  `def _auto_improvement_issue_exists(tag: str) -> bool:`
- **Funktion** `_check_systematic_tag_failures` Zeilen 2129-2203
  `def _check_systematic_tag_failures(project_root) -> None:`
- **Funktion** `_sync_closed_contexts` Zeilen 2206-2231
  `def _sync_closed_contexts() -> None:`
- **Funktion** `_consecutive_passes_for_test` Zeilen 2234-2259
  `def _consecutive_passes_for_test(test_name: str) -> int:`
- **Funktion** `_close_resolved_auto_issues` Zeilen 2262-2341
  `def _close_resolved_auto_issues(result: "evaluation.EvalResult") -> None:`
- **Funktion** `_build_metadata` Zeilen 2344-2423
  `def _build_metadata(`
- **Funktion** `_session_path` Zeilen 2426-2428
  `def _session_path() -> Path:`
- **Funktion** `_session_load` Zeilen 2431-2455
  `def _session_load() -> dict:`
- **Funktion** `_session_increment` Zeilen 2458-2468
  `def _session_increment() -> dict:`
- **Funktion** `_session_status_line` Zeilen 2471-2484
  `def _session_status_line(data: dict) -> str:`
- **Funktion** `_format_history_block` Zeilen 2487-2523
  `def _format_history_block(project_root: Path, n: int = 5) -> str:`
- **Funktion** `_last_chat_inactive_minutes` Zeilen 2526-2574
  `def _last_chat_inactive_minutes(log_path: str | Path) -> float | None:`
- **Funktion** `_server_start_time` Zeilen 2577-2625
  `def _server_start_time(log_path: str | Path) -> datetime.datetime | None:`
- **Funktion** `_check_server_staleness` Zeilen 2628-2696
  `def _check_server_staleness(branch: str, force: bool = False) -> None:`
- **Funktion** `_restart_server_for_eval` Zeilen 2699-2721
  `def _restart_server_for_eval() -> None:`
- **Funktion** `_has_new_commits_since_last_eval` Zeilen 2724-2755
  `def _has_new_commits_since_last_eval(project_root: Path) -> bool:`
- **Funktion** `_wait_for_server` Zeilen 2758-2803
  `def _wait_for_server(`
- **Funktion** `cmd_eval_after_restart` Zeilen 2806-2868
  `def cmd_eval_after_restart(number: int | None = None) -> None:`
- **Funktion** `_ast_diff` Zeilen 2871-2911
  `def _ast_diff(old_content: str, new_content: str) -> list[str]:`
- **Funktion** `_gitea_version_compare` Zeilen 2914-2965
  `def _gitea_version_compare(commit: str, changed_files: list[str]) -> str:`
- **Funktion** `_build_auto_issue_body` Zeilen 2968-3083
  `def _build_auto_issue_body(`
- **Funktion** `cmd_watch` Zeilen 3086-3222
  `def cmd_watch(interval_minutes: int = 60, patch_mode: bool = False) -> None:`
- **Funktion** `_dashboard_event` Zeilen 3230-3237
  `def _dashboard_event(context: str = "") -> None:`
- **Funktion** `cmd_install_service` Zeilen 3263-3308
  `def cmd_install_service() -> None:`
- **Funktion** `cmd_dashboard` Zeilen 3316-3322
  `def cmd_dashboard() -> None:`
- **Funktion** `cmd_doctor` Zeilen 3324-3485
  `def cmd_doctor() -> None:`
- **Funktion** `cmd_auto` Zeilen 3488-3580
  `def cmd_auto() -> None:`
- **Funktion** `_apply_auto_approve` Zeilen 3588-3616
  `def _apply_auto_approve() -> None:`
- **Funktion** `cmd_setup` Zeilen 3623-3828
  `def cmd_setup() -> None:`
- **Funktion** `main` Zeilen 3831-4033
  `def main():`
- **Funktion** `_sym_map` Zeilen 2882-2884
  `def _sym_map(content: str) -> dict[str, dict]:`
- **Funktion** `_check` Zeilen 3337-3345
  `def _check(status: str, name: str, detail: str, fix: str = "") -> None:`
- **Funktion** `_ask` Zeilen 3632-3635
  `def _ask(prompt: str, default: str = "") -> str:`
- **Funktion** `_ask_secret` Zeilen 3637-3638
  `def _ask_secret(prompt: str) -> str:`
- **Funktion** `_api_get` Zeilen 3640-3647
  `def _api_get(url: str, user: str, token: str, path: str):`
- **Funktion** `_api_post` Zeilen 3649-3663
  `def _api_post(url: str, user: str, token: str, path: str, data: dict):`
- **Funktion** `_len` Zeilen 2895-2900
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

## plugins/__init__.py  *(0 Zeilen)*

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
