"""Tests für _classify_commit, _build_changelog_block (plugins/changelog.py)."""

import sys

import pytest

sys.argv = ["x", "--self"]
import agent_start  # noqa: F401 — sets up sys.path + env
from plugins.changelog import _build_changelog_block, _classify_commit


# ---------------------------------------------------------------------------
# _classify_commit
# ---------------------------------------------------------------------------


def test_classify_feat():
    assert _classify_commit("feat: add new command") == ("feat", "add new command")


def test_classify_fix():
    assert _classify_commit("fix: correct off-by-one") == ("fix", "correct off-by-one")


def test_classify_with_scope():
    typ, desc = _classify_commit("fix(auth): handle expired token")
    assert typ == "fix"
    assert desc == "handle expired token"


def test_classify_breaking_change():
    typ, desc = _classify_commit("feat!: remove legacy API")
    assert typ == "feat"
    assert desc == "remove legacy API"


def test_classify_no_prefix():
    typ, desc = _classify_commit("just a plain commit message")
    assert typ == "other"
    assert desc == "just a plain commit message"


def test_classify_empty():
    typ, desc = _classify_commit("")
    assert typ == "other"


def test_classify_chore():
    typ, desc = _classify_commit("chore: update dependencies")
    assert typ == "chore"
    assert desc == "update dependencies"


def test_classify_case_insensitive_prefix():
    typ, _ = _classify_commit("Feat: something")
    assert typ == "feat"


# ---------------------------------------------------------------------------
# _build_changelog_block
# ---------------------------------------------------------------------------


def test_build_changelog_block_header():
    result = _build_changelog_block([], "1.0.0", "2026-01-01")
    assert "## [1.0.0] — 2026-01-01" in result


def test_build_changelog_block_feat_section():
    commits = [{"subject": "feat: add doctor command", "hash": "abc1234"}]
    result = _build_changelog_block(commits, "1.1.0", "2026-03-25")
    assert "### Features" in result
    assert "add doctor command" in result
    assert "abc1234" in result


def test_build_changelog_block_multiple_types():
    commits = [
        {"subject": "feat: new thing", "hash": "aaa"},
        {"subject": "fix: broken thing", "hash": "bbb"},
    ]
    result = _build_changelog_block(commits, "1.2.0", "2026-03-25")
    assert "### Features" in result
    assert "### Bugfixes" in result


def test_build_changelog_block_other_section():
    commits = [{"subject": "WIP something weird", "hash": "ccc"}]
    result = _build_changelog_block(commits, "0.9.0", "2026-01-01")
    assert "### Sonstiges" in result
    assert "WIP something weird" in result


def test_build_changelog_block_empty_commits():
    result = _build_changelog_block([], "1.0.0", "2026-01-01")
    assert "## [1.0.0]" in result
    assert "### Features" not in result
