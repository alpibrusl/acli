"""Smoke tests for citecheck — no network."""
from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from citecheck import main as cc


SAMPLE_HTML = """
<html><head><title>T</title><script>var x=1;</script></head>
<body><p>Water  boils at 100°C at standard atmospheric pressure.</p>
<style>.a{}</style></body></html>
"""


def test_extract_text_strips_scripts_and_normalizes_whitespace():
    text = cc._extract_text(SAMPLE_HTML)
    assert "var x=1" not in text
    assert "Water boils at 100°C at standard atmospheric pressure." in text
    # whitespace normalized
    assert "  " not in text


def test_contains_claim_case_insensitive():
    assert cc._contains_claim("Hello World", "hello world")
    assert cc._contains_claim("Hello World", "WORLD")
    assert not cc._contains_claim("Hello World", "absent")


def test_run_id_is_stable_and_prefixed():
    rid1 = cc._run_id({"a": 1, "b": 2})
    rid2 = cc._run_id({"b": 2, "a": 1})
    assert rid1 == rid2
    assert rid1.startswith("run_")
    assert len(rid1) == len("run_") + 10


def test_link_regex_finds_markdown_links():
    md = "Foo [claim one](https://a.example) bar [two](https://b.example/x?q=1)."
    links = cc.LINK_RE.findall(md)
    assert links == [
        ("claim one", "https://a.example"),
        ("two", "https://b.example/x?q=1"),
    ]


def test_fetch_uses_httpx(monkeypatch):
    """Patch httpx.Client to avoid real network."""

    class FakeResp:
        status_code = 200
        text = "<html><body>hello</body></html>"

    class FakeClient:
        def __init__(self, *a, **kw): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def get(self, url, headers=None): return FakeResp()

    monkeypatch.setattr(cc.httpx, "Client", FakeClient)
    status, body = cc._fetch("https://anywhere.example")
    assert status == 200
    assert "hello" in body


def test_fetch_raises_request_error(monkeypatch):
    class FakeClient:
        def __init__(self, *a, **kw): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def get(self, url, headers=None):
            raise httpx.ConnectError("nope")

    monkeypatch.setattr(cc.httpx, "Client", FakeClient)
    with pytest.raises(httpx.RequestError):
        cc._fetch("https://anywhere.example")


def test_full_match_pipeline():
    """End-to-end: extract + match against a known claim."""
    text = cc._extract_text(SAMPLE_HTML)
    assert cc._contains_claim(text, "100°C at standard atmospheric pressure")
