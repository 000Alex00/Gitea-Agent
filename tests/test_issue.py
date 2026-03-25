"""Tests für risk_level, issue_type, branch_name, _validate_comment (agent_start.py)."""

import sys

import pytest

sys.argv = ["x", "--self"]
import agent_start
from agent_start import _validate_comment, branch_name, issue_type, risk_level


def _issue(title="", labels=None):
    return {"number": 1, "title": title, "labels": [{"name": l} for l in (labels or [])]}


# ---------------------------------------------------------------------------
# risk_level
# ---------------------------------------------------------------------------


def test_risk_level_bug():
    level, desc = risk_level(_issue(labels=["bug"]))
    assert level == 3
    assert "Bug" in desc


def test_risk_level_feature():
    level, desc = risk_level(_issue(labels=["Feature request"]))
    assert level == 3


def test_risk_level_enhancement():
    level, desc = risk_level(_issue(labels=["enhancement"]))
    assert level == 2


def test_risk_level_docs_keyword():
    level, desc = risk_level(_issue(title="update docs for API", labels=["enhancement"]))
    assert level == 1
    assert "NIEDRIG" in desc


def test_risk_level_default():
    level, _ = risk_level(_issue())
    assert level == 2


def test_risk_level_no_labels():
    level, _ = risk_level(_issue(title="random task"))
    assert level in (1, 2, 3, 4)


# ---------------------------------------------------------------------------
# issue_type
# ---------------------------------------------------------------------------


def test_issue_type_bug():
    assert issue_type(_issue(labels=["bug"])) == "bug"


def test_issue_type_feature():
    assert issue_type(_issue(labels=["Feature request"])) == "feature_request"


def test_issue_type_enhancement():
    assert issue_type(_issue(labels=["enhancement"])) == "enhancement"


def test_issue_type_docs():
    assert issue_type(_issue(title="update docs", labels=["enhancement"])) == "docs"


def test_issue_type_default():
    assert issue_type(_issue()) == "task"


# ---------------------------------------------------------------------------
# branch_name
# ---------------------------------------------------------------------------


def test_branch_name_bug_prefix():
    name = branch_name(_issue(title="fix crash on startup", labels=["bug"]))
    assert name.startswith("fix/issue-")


def test_branch_name_feat_prefix():
    name = branch_name(_issue(title="add new feature", labels=["Feature request"]))
    assert name.startswith("feat/issue-")


def test_branch_name_chore_prefix():
    name = branch_name(_issue(title="update config"))
    assert name.startswith("chore/issue-")


def test_branch_name_docs_prefix():
    name = branch_name(_issue(title="update docs for setup", labels=["enhancement"]))
    assert name.startswith("docs/issue-")


def test_branch_name_slug_length():
    long_title = "this is a very long title that exceeds the maximum slug length limit"
    name = branch_name(_issue(title=long_title))
    slug = name.split("/issue-1-")[1]
    assert len(slug) <= 35


def test_branch_name_umlaut_conversion():
    name = branch_name(_issue(title="füge neue Übersicht hinzu"))
    assert "ü" not in name
    assert "ö" not in name


def test_branch_name_special_chars_removed():
    name = branch_name(_issue(title="fix: the bug (critical)"))
    assert "(" not in name
    assert ")" not in name
    assert ":" not in name


# ---------------------------------------------------------------------------
# _validate_comment
# ---------------------------------------------------------------------------


def test_validate_comment_all_present(capfd):
    body = "Risikostufe 2\nBetroffene Dateien: foo.py\nOK zum Implementieren?"
    _validate_comment(body, "plan")
    out = capfd.readouterr().out
    assert out == ""


def test_validate_comment_missing_field(capfd):
    body = "nur Risikostufe vorhanden"
    _validate_comment(body, "plan")
    out = capfd.readouterr().out
    assert "[!]" in out


def test_validate_comment_unknown_type():
    # Unbekannter Typ → keine required fields → kein Fehler
    _validate_comment("anything", "unknown_type")


def test_validate_comment_case_insensitive():
    body = "RISIKOSTUFE ok\nBETROFFENE DATEIEN: x\nOK ZUM IMPLEMENTIEREN?"
    _validate_comment(body, "plan")
