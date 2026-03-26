# Repo-Skelett

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

## agent_start.py  *(zu groß — Datei zu groß (138KB > 20KB))*

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

## dashboard.py  *(299 Zeilen)*

- **Funktion** `generate` Zeilen 139-295
  `def generate(project_root: Path):`

## settings.py  *(259 Zeilen)*

- **Funktion** `_env` Zeilen 16-25
  `def _env(key: str, default: str = "") -> str:`
- **Funktion** `_env_list` Zeilen 28-30
  `def _env_list(key: str, default: str) -> list[str]:`
- **Funktion** `_env_int` Zeilen 33-37
  `def _env_int(key: str, default: int) -> int:`
- **Funktion** `_env_bool` Zeilen 40-41
  `def _env_bool(key: str, default: bool = False) -> bool:`

## repo_skeleton.json  *(zu groß — Datei zu groß (39KB > 20KB))*

## scripts/agent_status.sh  *(91 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## scripts/start_patch.sh  *(71 Zeilen)*

*(keine Klassen/Funktionen erkannt)*

## data/doctor_last.json  *(46 Zeilen)*

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
