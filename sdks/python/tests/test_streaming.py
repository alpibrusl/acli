"""Tests for NDJSON streaming (emit_progress, emit_result)."""

from __future__ import annotations

import json
import sys
from io import StringIO

from acli.output import emit_progress, emit_result


class TestEmitProgress:
    def test_basic(self) -> None:
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            emit_progress("validate", "ok")
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        line = json.loads(output.strip())
        assert line["type"] == "progress"
        assert line["step"] == "validate"
        assert line["status"] == "ok"
        assert "detail" not in line

    def test_with_detail(self) -> None:
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            emit_progress("build", "running", detail="compiling module A")
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        line = json.loads(output.strip())
        assert line["detail"] == "compiling module A"

    def test_multiple_lines(self) -> None:
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            emit_progress("step1", "ok")
            emit_progress("step2", "running")
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        lines = [json.loads(line) for line in output.strip().split("\n")]
        assert len(lines) == 2
        assert lines[0]["step"] == "step1"
        assert lines[1]["step"] == "step2"


class TestEmitResult:
    def test_success(self) -> None:
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            emit_result({"data": {"count": 42}})
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        line = json.loads(output.strip())
        assert line["type"] == "result"
        assert line["ok"] is True
        assert line["data"]["count"] == 42

    def test_failure(self) -> None:
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            emit_result({"error": "something broke"}, ok=False)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        line = json.loads(output.strip())
        assert line["ok"] is False
        assert line["error"] == "something broke"
