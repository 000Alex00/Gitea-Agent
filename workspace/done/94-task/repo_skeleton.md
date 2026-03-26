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

## project.template.json  *(14 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## push_github.sh  *(26 Zeilen)*

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

## agent_eval.template.json  *(86 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## dashboard.py  *(299 Zeilen)*

- **Funktion** `generate` Zeilen 139-295
  `def generate(project_root: Path):`

## settings.py  *(310 Zeilen)*

- **Funktion** `_env` Zeilen 16-25
  `def _env(key: str, default: str = "") -> str:`
- **Funktion** `_env_list` Zeilen 28-30
  `def _env_list(key: str, default: str) -> list[str]:`
- **Funktion** `_env_int` Zeilen 33-37
  `def _env_int(key: str, default: int) -> int:`
- **Funktion** `_env_bool` Zeilen 40-41
  `def _env_bool(key: str, default: bool = False) -> bool:`
- **Funktion** `_load_features` Zeilen 266-284
  `def _load_features() -> dict:`
- **Funktion** `_load_project_type` Zeilen 289-300
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

## repo_skeleton.json  *(zu groß — Datei zu groß (41KB > 20KB))*

## context_export.sh  *(206 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

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

## scripts/start_patch.sh  *(71 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## scripts/push_github.sh  *(26 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## scripts/context_export.sh  *(206 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## data/doctor_last.json  *(46 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

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

## log.py  *(67 Zeilen)*

- **Funktion** `setup` Zeilen 21-54
  `def setup(log_file: str = "gitea-agent.log", level: str = "INFO") -> None:`
- **Funktion** `get_logger` Zeilen 57-67
  `def get_logger(name: str) -> logging.Logger:`
