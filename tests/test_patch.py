"""Tests für _parse_search_replace, _normalize_ws, _apply_patch (plugins/patch.py)."""

import sys
import tempfile
from pathlib import Path

import pytest

sys.argv = ["x", "--self"]
import agent_start  # noqa: F401 — sets up sys.path + env
import plugins.patch as patch_module
from plugins.patch import _apply_patch, _normalize_ws, _parse_search_replace


# ---------------------------------------------------------------------------
# _normalize_ws
# ---------------------------------------------------------------------------


def test_normalize_ws_strips_trailing_spaces():
    assert _normalize_ws("hello   \nworld  ") == "hello\nworld"


def test_normalize_ws_crlf_to_lf():
    assert _normalize_ws("line1\r\nline2\r\n") == "line1\nline2"


def test_normalize_ws_empty():
    assert _normalize_ws("") == ""


def test_normalize_ws_no_change():
    assert _normalize_ws("clean\ntext") == "clean\ntext"


# ---------------------------------------------------------------------------
# _parse_search_replace
# ---------------------------------------------------------------------------

_BLOCK = """\
## myfile.py
<<<<<<< SEARCH
old code
=======
new code
>>>>>>> REPLACE
"""


def test_parse_single_block():
    patches = _parse_search_replace(_BLOCK)
    assert len(patches) == 1
    assert patches[0]["file"] == "myfile.py"
    assert patches[0]["search"] == "old code"
    assert patches[0]["replace"] == "new code"


def test_parse_multiple_blocks():
    text = _BLOCK + "\n## other.py\n<<<<<<< SEARCH\nfoo\n=======\nbar\n>>>>>>> REPLACE\n"
    patches = _parse_search_replace(text)
    assert len(patches) == 2
    assert patches[1]["file"] == "other.py"


def test_parse_empty_text():
    assert _parse_search_replace("") == []


def test_parse_no_py_header_ignored():
    text = "## README.md\n<<<<<<< SEARCH\nold\n=======\nnew\n>>>>>>> REPLACE\n"
    assert _parse_search_replace(text) == []


def test_parse_multiline_block():
    text = "## f.py\n<<<<<<< SEARCH\nline1\nline2\n=======\nreplaced\n>>>>>>> REPLACE\n"
    patches = _parse_search_replace(text)
    assert patches[0]["search"] == "line1\nline2"
    assert patches[0]["replace"] == "replaced"


def test_parse_incomplete_block_ignored():
    text = "## f.py\n<<<<<<< SEARCH\nonly search\n"
    assert _parse_search_replace(text) == []


# ---------------------------------------------------------------------------
# _apply_patch
# ---------------------------------------------------------------------------


def _make_temp_py(content: str) -> Path:
    """Schreibt temporäre .py-Datei in PROJECT-Verzeichnis und gibt rel. Pfad zurück."""
    tmp = tempfile.NamedTemporaryFile(
        suffix=".py", dir=str(patch_module.PROJECT), delete=False, mode="w", encoding="utf-8"
    )
    tmp.write(content)
    tmp.close()
    return Path(tmp.name)


def test_apply_patch_happy_path(tmp_path, monkeypatch):
    monkeypatch.setattr(patch_module, "PROJECT", tmp_path)
    (tmp_path / "target.py").write_text("def foo():\n    return 1\n", encoding="utf-8")
    patch = {"file": "target.py", "search": "def foo():\n    return 1", "replace": "def foo():\n    return 2"}
    ok, msg = _apply_patch(patch)
    assert ok
    assert "gepatcht" in msg
    assert "return 2" in (tmp_path / "target.py").read_text(encoding="utf-8")


def test_apply_patch_search_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(patch_module, "PROJECT", tmp_path)
    (tmp_path / "f.py").write_text("def foo(): pass\n", encoding="utf-8")
    patch = {"file": "f.py", "search": "def bar(): pass", "replace": "def bar(): return 1"}
    ok, msg = _apply_patch(patch)
    assert not ok
    assert "SEARCH nicht gefunden" in msg


def test_apply_patch_file_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr(patch_module, "PROJECT", tmp_path)
    patch = {"file": "nonexistent.py", "search": "x", "replace": "y"}
    ok, msg = _apply_patch(patch)
    assert not ok
    assert "nicht gefunden" in msg


def test_apply_patch_dry_run(tmp_path, monkeypatch):
    monkeypatch.setattr(patch_module, "PROJECT", tmp_path)
    (tmp_path / "g.py").write_text("x = 1\n", encoding="utf-8")
    patch = {"file": "g.py", "search": "x = 1", "replace": "x = 2"}
    ok, msg = _apply_patch(patch, dry_run=True)
    assert ok
    assert "dry-run" in msg
    assert (tmp_path / "g.py").read_text(encoding="utf-8") == "x = 1\n"


def test_apply_patch_syntax_error_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(patch_module, "PROJECT", tmp_path)
    (tmp_path / "h.py").write_text("def foo():\n    pass\n", encoding="utf-8")
    patch = {"file": "h.py", "search": "def foo():\n    pass", "replace": "def foo(\n    broken syntax"}
    ok, msg = _apply_patch(patch)
    assert not ok
    assert "Syntax" in msg


def test_apply_patch_creates_backup(tmp_path, monkeypatch):
    monkeypatch.setattr(patch_module, "PROJECT", tmp_path)
    (tmp_path / "bak.py").write_text("a = 1\n", encoding="utf-8")
    patch = {"file": "bak.py", "search": "a = 1", "replace": "a = 2"}
    _apply_patch(patch)
    assert (tmp_path / "bak.py.bak").exists()
