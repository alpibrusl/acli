"""Tests for acli.output."""

from __future__ import annotations

import json
import sys
import time
from io import StringIO

from acli.output import (
    OutputFormat,
    emit,
    error_envelope,
    success_envelope,
)


class TestOutputFormat:
    def test_enum_values(self) -> None:
        assert OutputFormat.text == "text"
        assert OutputFormat.json == "json"
        assert OutputFormat.table == "table"


class TestSuccessEnvelope:
    def test_basic(self) -> None:
        env = success_envelope("run", {"result": 42}, version="1.0.0")
        assert env["ok"] is True
        assert env["command"] == "run"
        assert env["data"] == {"result": 42}
        assert env["meta"]["version"] == "1.0.0"

    def test_with_timing(self) -> None:
        start = time.time() - 0.1
        env = success_envelope("run", {}, version="1.0.0", start_time=start)
        assert env["meta"]["duration_ms"] >= 100

    def test_dry_run(self) -> None:
        actions = [{"action": "create", "target": "x", "reversible": True}]
        env = success_envelope(
            "deploy",
            {},
            version="1.0.0",
            dry_run=True,
            planned_actions=actions,
        )
        assert env["dry_run"] is True
        assert env["planned_actions"] == actions
        assert "data" not in env

    def test_dry_run_no_data_key(self) -> None:
        env = success_envelope("deploy", {"ignored": True}, version="1.0.0", dry_run=True)
        assert "data" not in env


class TestErrorEnvelope:
    def test_basic(self) -> None:
        env = error_envelope(
            "run",
            code="INVALID_ARGS",
            message="Missing --pipeline",
            version="1.0.0",
        )
        assert env["ok"] is False
        assert env["error"]["code"] == "INVALID_ARGS"
        assert env["error"]["message"] == "Missing --pipeline"
        assert "hint" not in env["error"]
        assert "docs" not in env["error"]

    def test_with_hint_and_docs(self) -> None:
        env = error_envelope(
            "run",
            code="INVALID_ARGS",
            message="Missing --pipeline",
            hint="Run `noether run --help`",
            docs=".cli/examples/run.sh",
            version="1.0.0",
        )
        assert env["error"]["hint"] == "Run `noether run --help`"
        assert env["error"]["docs"] == ".cli/examples/run.sh"


class TestEmit:
    def test_json_output(self) -> None:
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            emit({"ok": True, "data": {"x": 1}}, OutputFormat.json)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        parsed = json.loads(output)
        assert parsed["data"]["x"] == 1

    def test_text_error_output(self) -> None:
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            emit(
                {"ok": False, "error": {"code": "NOT_FOUND", "message": "Gone", "hint": "Check"}},
                OutputFormat.text,
            )
            output = sys.stderr.getvalue()
        finally:
            sys.stderr = old_stderr
        assert "NOT_FOUND" in output
        assert "Gone" in output
        assert "Check" in output

    def test_text_success_output(self) -> None:
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            emit({"ok": True, "data": {"name": "test"}}, OutputFormat.text)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        assert "name: test" in output

    def test_table_dict_output(self) -> None:
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            emit({"ok": True, "data": {"a": 1, "b": 2}}, OutputFormat.table)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        assert "a" in output
        assert "b" in output

    def test_table_list_output(self) -> None:
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            emit(
                {"ok": True, "data": [{"col1": "x", "col2": "y"}, {"col1": "a", "col2": "b"}]},
                OutputFormat.table,
            )
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        assert "col1" in output
        assert "col2" in output
        assert "x" in output
        assert "a" in output

    def test_table_empty_data(self) -> None:
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            emit({"ok": True, "data": {}}, OutputFormat.table)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        assert output == ""

    def test_text_success_list_output(self) -> None:
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            emit({"ok": True, "data": ["item1", "item2"]}, OutputFormat.text)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        assert "item1" in output
        assert "item2" in output

    def test_text_error_with_docs(self) -> None:
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            emit(
                {
                    "ok": False,
                    "error": {
                        "code": "X",
                        "message": "m",
                        "hint": "h",
                        "docs": "d.sh",
                    },
                },
                OutputFormat.text,
            )
            output = sys.stderr.getvalue()
        finally:
            sys.stderr = old_stderr
        assert "Reference: d.sh" in output
