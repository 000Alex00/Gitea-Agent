import argparse
import ast
import re
import sys
from typing import List, Tuple

import gitea_api as gitea
import settings


def check_labels() -> Tuple[bool, str]:
    """1. Labels Check: All label constants in settings.py exist in Gitea."""
    required_labels = [
        settings.LABEL_READY,
        settings.LABEL_PROPOSED,
        settings.LABEL_PROGRESS,
        settings.LABEL_REVIEW,
        settings.LABEL_HELP,
    ]
    try:
        existing_labels = list(gitea.get_all_labels().keys())
    except Exception as e:
        return False, f"Could not fetch labels from Gitea: {e}"

    missing = [l for l in required_labels if l not in existing_labels]
    if missing:
        return False, f"Missing labels in Gitea: {', '.join(missing)}"
    return True, "All labels exist."


def check_flags() -> Tuple[bool, str]:
    """2. Flags Check: Every --flag in argparse has a cmd_* handler."""
    with open("agent_start.py", "r", encoding="utf-8") as f:
        content = f.read()

    tree = ast.parse(content)
    flags = []

    # Extract flags from add_argument calls
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_argument"
        ):
            for arg in node.args:
                if (
                    isinstance(arg, ast.Constant)
                    and isinstance(arg.value, str)
                    and arg.value.startswith("--")
                ):
                    flags.append(arg.value[2:].replace("-", "_"))

    # Find cmd_* functions
    cmd_funcs = [
        n.name
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name.startswith("cmd_")
    ]

    missing_handlers = []

    # Identify commands that should have handlers from agent_start.py
    # From help descriptions in add_argument: list, issue, implement, fixup, pr, watch, eval-after-restart
    action_flags = [
        "list",
        "issue",
        "implement",
        "fixup",
        "pr",
        "watch",
        "eval_after_restart",
        "auto",
        "generate_tests",
        "dashboard",
    ]

    for flag in flags:
        if flag in action_flags:
            expected_func = "cmd_plan" if flag == "issue" else f"cmd_{flag}"
            if expected_func not in cmd_funcs:
                missing_handlers.append(
                    f"--{flag.replace('_', '-')} missing {expected_func}()"
                )

    if missing_handlers:
        return False, f"Missing handlers: {', '.join(missing_handlers)}"
    return True, "All main flags have handlers."


def check_required_fields() -> Tuple[bool, str]:
    """3. Required Fields Check: COMMENT_REQUIRED_FIELDS referenced in post_comment calls."""
    with open("agent_start.py", "r", encoding="utf-8") as f:
        content = f.read()

    errors = []
    for comment_type, fields in settings.COMMENT_REQUIRED_FIELDS.items():
        for field in fields:
            if field not in content:
                errors.append(
                    f"Required field '{field}' for type '{comment_type}' not found in agent_start.py"
                )

    if errors:
        return False, "\n".join(errors)
    return True, "All required fields are referenced."


def check_env_sync() -> Tuple[bool, str]:
    """4. Env Sync Check: All _env() keys in settings.py documented in .env.example."""
    with open("settings.py", "r", encoding="utf-8") as f:
        settings_content = f.read()

    with open(".env.example", "r", encoding="utf-8") as f:
        env_example_content = f.read()

    # Find all _env("KEY"...) calls in settings.py
    # Also match _env_list, _env_int, _env_bool
    env_keys = re.findall(
        r'_env(?:_list|_int|_bool)?\(\s*["\']([A-Z0-9_]+)["\']', settings_content
    )

    missing_in_example = []
    for key in set(env_keys):
        if key not in env_example_content:
            missing_in_example.append(key)

    if missing_in_example:
        return (
            False,
            f"Environment variables missing in .env.example: {', '.join(missing_in_example)}",
        )
    return True, "All env vars are documented."


def run() -> None:
    print("Running Agent Self-Consistency Check...")
    checks = [
        ("Labels Check", check_labels),
        ("Flags Check", check_flags),
        ("Required Fields Check", check_required_fields),
        ("Env Sync Check", check_env_sync),
    ]

    all_passed = True
    for name, check_func in checks:
        passed, message = check_func()
        if not passed:
            print(f"❌ {name} FAILED:\n   {message}", file=sys.stderr)
            all_passed = False
        else:
            print(f"✅ {name} PASSED")

    if not all_passed:
        print(
            "\nAgent Self-Check failed. Please fix the issues above before merging.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    run()
