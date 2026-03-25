"""Tests für _extract_ast_symbols, _skeleton_to_md (agent_start.py)."""

import sys

import pytest

sys.argv = ["x", "--self"]
import agent_start
from agent_start import _extract_ast_symbols, _skeleton_to_md


# ---------------------------------------------------------------------------
# _extract_ast_symbols
# ---------------------------------------------------------------------------


def test_extract_function():
    code = "def foo():\n    pass\n"
    syms = _extract_ast_symbols(code)
    names = [s["name"] for s in syms]
    assert "foo" in names


def test_extract_class():
    code = "class Bar:\n    pass\n"
    syms = _extract_ast_symbols(code)
    assert any(s["type"] == "class" and s["name"] == "Bar" for s in syms)


def test_extract_multiple():
    code = "def a(): pass\ndef b(): pass\nclass C: pass\n"
    syms = _extract_ast_symbols(code)
    assert len(syms) == 3


def test_extract_syntax_error_returns_empty():
    syms = _extract_ast_symbols("def broken(:\n    pass")
    assert syms == []


def test_extract_empty_string():
    assert _extract_ast_symbols("") == []


def test_extract_line_numbers():
    code = "def foo():\n    pass\n"
    syms = _extract_ast_symbols(code)
    foo = next(s for s in syms if s["name"] == "foo")
    start, end = map(int, foo["lines"].split("-"))
    assert start == 1
    assert end >= 1


def test_extract_signature():
    code = "def greet(name: str) -> str:\n    return name\n"
    syms = _extract_ast_symbols(code)
    foo = next(s for s in syms if s["name"] == "greet")
    assert "greet" in foo["signature"]


def test_extract_async_function():
    code = "async def fetch():\n    pass\n"
    syms = _extract_ast_symbols(code)
    assert any(s["name"] == "fetch" for s in syms)


# ---------------------------------------------------------------------------
# _skeleton_to_md
# ---------------------------------------------------------------------------


def test_skeleton_to_md_header():
    data = [{"path": "foo.py", "lines": 10, "symbols": []}]
    result = _skeleton_to_md(data)
    assert "## foo.py" in result
    assert "10 Zeilen" in result


def test_skeleton_to_md_function_entry():
    data = [{
        "path": "bar.py",
        "lines": 5,
        "symbols": [{"type": "function", "name": "baz", "lines": "1-5", "signature": "def baz():"}],
    }]
    result = _skeleton_to_md(data)
    assert "**Funktion**" in result
    assert "`baz`" in result
    assert "1-5" in result


def test_skeleton_to_md_class_entry():
    data = [{
        "path": "c.py",
        "lines": 8,
        "symbols": [{"type": "class", "name": "MyClass", "lines": "1-8", "signature": "class MyClass:"}],
    }]
    result = _skeleton_to_md(data)
    assert "**Klasse**" in result
    assert "`MyClass`" in result


def test_skeleton_to_md_truncated():
    data = [{"path": "huge.py", "truncated": True, "reason": "zu groß", "symbols": []}]
    result = _skeleton_to_md(data)
    assert "zu groß" in result


def test_skeleton_to_md_no_symbols():
    data = [{"path": "empty.py", "lines": 2, "symbols": []}]
    result = _skeleton_to_md(data)
    assert "keine Klassen/Funktionen" in result


def test_skeleton_to_md_multiple_files():
    data = [
        {"path": "a.py", "lines": 1, "symbols": []},
        {"path": "b.py", "lines": 2, "symbols": []},
    ]
    result = _skeleton_to_md(data)
    assert "## a.py" in result
    assert "## b.py" in result
