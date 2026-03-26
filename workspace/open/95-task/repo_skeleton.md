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

## llm_routing.template.json  *(73 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## repo_skeleton.json  *(zu groß — Datei zu groß (50KB > 20KB))*

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

## plugins/llm.py  *(346 Zeilen)*

- **Funktion** `_load_routing` Zeilen 36-45
  `def _load_routing(extra_path: Optional[Path] = None) -> dict:`
- **Funktion** `_resolve_task_config` Zeilen 48-59
  `def _resolve_task_config(task: str, routing: dict) -> dict:`
- **Klasse** `LLMResponse` Zeilen 67-76
  `class LLMResponse:`
- **Funktion** `_http_post` Zeilen 83-87
  `def _http_post(url: str, payload: dict, headers: dict, timeout: int) -> dict:`
- **Klasse** `ClaudeClient` Zeilen 90-123
  `class ClaudeClient:`
- **Klasse** `OpenAIClient` Zeilen 126-157
  `class OpenAIClient:`
- **Klasse** `GeminiClient` Zeilen 160-188
  `class GeminiClient:`
- **Klasse** `LocalClient` Zeilen 191-217
  `class LocalClient:`
- **Funktion** `_client_from_env` Zeilen 224-251
  `def _client_from_env() -> Optional["ClaudeClient | LocalClient"]:`
- **Funktion** `_build_client` Zeilen 254-295
  `def _build_client(cfg: dict) -> "ClaudeClient | OpenAIClient | GeminiClient | LocalClient":`
- **Funktion** `get_client` Zeilen 302-331
  `def get_client(`
- **Funktion** `complete` Zeilen 334-346
  `def complete(`
- **Funktion** `ok` Zeilen 75-76
  `def ok(self) -> bool:`
- **Funktion** `__init__` Zeilen 96-100
  `def __init__(self, model: str, api_key: str, max_tokens: int = 1024, timeout: int = 60):`
- **Funktion** `complete` Zeilen 102-123
  `def complete(self, prompt: str) -> LLMResponse:`
- **Funktion** `__init__` Zeilen 129-135
  `def __init__(self, model: str, api_key: str, base_url: str = "https://api.openai.com/v1",`
- **Funktion** `complete` Zeilen 137-157
  `def complete(self, prompt: str) -> LLMResponse:`
- **Funktion** `__init__` Zeilen 165-169
  `def __init__(self, model: str, api_key: str, max_tokens: int = 1024, timeout: int = 60):`
- **Funktion** `complete` Zeilen 171-188
  `def complete(self, prompt: str) -> LLMResponse:`
- **Funktion** `__init__` Zeilen 194-199
  `def __init__(self, model: str, base_url: str = "http://localhost:11434",`
- **Funktion** `complete` Zeilen 201-217
  `def complete(self, prompt: str) -> LLMResponse:`
- **Funktion** `_get` Zeilen 240-241
  `def _get(key: str, default: str = "") -> str:`
- **Funktion** `_get_key` Zeilen 258-268
  `def _get_key(env_var: str) -> str:`

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

## tests/test_llm.py  *(264 Zeilen)*

- **Klasse** `TestLLMResponse` Zeilen 27-38
  `class TestLLMResponse(unittest.TestCase):`
- **Klasse** `TestLoadRouting` Zeilen 41-64
  `class TestLoadRouting(unittest.TestCase):`
- **Klasse** `TestResolveTaskConfig` Zeilen 67-94
  `class TestResolveTaskConfig(unittest.TestCase):`
- **Klasse** `TestBuildClient` Zeilen 97-123
  `class TestBuildClient(unittest.TestCase):`
- **Klasse** `TestClaudeClient` Zeilen 126-158
  `class TestClaudeClient(unittest.TestCase):`
- **Klasse** `TestOpenAIClient` Zeilen 161-181
  `class TestOpenAIClient(unittest.TestCase):`
- **Klasse** `TestGeminiClient` Zeilen 184-198
  `class TestGeminiClient(unittest.TestCase):`
- **Klasse** `TestLocalClient` Zeilen 201-218
  `class TestLocalClient(unittest.TestCase):`
- **Klasse** `TestGetClient` Zeilen 221-248
  `class TestGetClient(unittest.TestCase):`
- **Klasse** `TestCompleteConvenience` Zeilen 251-260
  `class TestCompleteConvenience(unittest.TestCase):`
- **Funktion** `test_ok_with_text` Zeilen 28-30
  `def test_ok_with_text(self):`
- **Funktion** `test_not_ok_empty` Zeilen 32-34
  `def test_not_ok_empty(self):`
- **Funktion** `test_not_ok_with_error` Zeilen 36-38
  `def test_not_ok_with_error(self):`
- **Funktion** `test_no_config` Zeilen 42-44
  `def test_no_config(self):`
- **Funktion** `test_valid_config` Zeilen 46-56
  `def test_valid_config(self):`
- **Funktion** `test_invalid_json` Zeilen 58-64
  `def test_invalid_json(self):`
- **Funktion** `setUp` Zeilen 68-75
  `def setUp(self):`
- **Funktion** `test_known_task` Zeilen 77-79
  `def test_known_task(self):`
- **Funktion** `test_unknown_task_falls_back_to_default` Zeilen 81-84
  `def test_unknown_task_falls_back_to_default(self):`
- **Funktion** `test_default_as_string` Zeilen 86-90
  `def test_default_as_string(self):`
- **Funktion** `test_empty_routing` Zeilen 92-94
  `def test_empty_routing(self):`
- **Funktion** `test_claude` Zeilen 98-101
  `def test_claude(self):`
- **Funktion** `test_openai` Zeilen 103-105
  `def test_openai(self):`
- **Funktion** `test_gemini` Zeilen 107-109
  `def test_gemini(self):`
- **Funktion** `test_local` Zeilen 111-115
  `def test_local(self):`
- **Funktion** `test_ollama_alias` Zeilen 117-119
  `def test_ollama_alias(self):`
- **Funktion** `test_unknown_provider_falls_back_to_local` Zeilen 121-123
  `def test_unknown_provider_falls_back_to_local(self):`
- **Funktion** `_mock_response` Zeilen 127-135
  `def _mock_response(self, text: str, input_tokens: int = 10, output_tokens: int = 20):`
- **Funktion** `test_success` Zeilen 137-144
  `def test_success(self):`
- **Funktion** `test_api_error` Zeilen 146-152
  `def test_api_error(self):`
- **Funktion** `test_connection_error` Zeilen 154-158
  `def test_connection_error(self):`
- **Funktion** `test_success` Zeilen 162-175
  `def test_success(self):`
- **Funktion** `test_connection_error` Zeilen 177-181
  `def test_connection_error(self):`
- **Funktion** `test_success` Zeilen 185-198
  `def test_success(self):`
- **Funktion** `test_success` Zeilen 202-212
  `def test_success(self):`
- **Funktion** `test_connection_error` Zeilen 214-218
  `def test_connection_error(self):`
- **Funktion** `test_no_routing_falls_back_to_env` Zeilen 222-228
  `def test_no_routing_falls_back_to_env(self):`
- **Funktion** `test_routing_selects_correct_provider` Zeilen 230-237
  `def test_routing_selects_correct_provider(self):`
- **Funktion** `test_default_used_for_unknown_task` Zeilen 239-248
  `def test_default_used_for_unknown_task(self):`
- **Funktion** `test_delegates_to_client` Zeilen 252-260
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
