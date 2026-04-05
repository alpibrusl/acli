"""Tests for acli.cli (the acli meta-CLI)."""

from __future__ import annotations

import json
import subprocess
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from acli.cli import _deep_validate, _load_tree, _run_introspect, _validate_tree, app


def _sample_tree() -> dict:
    return {
        "name": "testapp",
        "version": "1.0.0",
        "acli_version": "0.1.0",
        "commands": [
            {
                "name": "run",
                "description": "Run something.",
                "idempotent": False,
                "options": [
                    {"name": "file", "type": "path", "description": "File to run."},
                    {
                        "name": "dry_run",
                        "type": "bool",
                        "description": "Preview.",
                        "default": False,
                    },
                    {
                        "name": "output",
                        "type": "OutputFormat",
                        "description": "Output format.",
                        "default": "text",
                    },
                ],
                "see_also": ["status"],
                "arguments": [],
                "examples": [
                    {"description": "Run a file", "invocation": "testapp run --file x.yaml"},
                    {"description": "Run another", "invocation": "testapp run --file y.yaml"},
                ],
                "subcommands": [],
            },
            {
                "name": "introspect",
                "description": "Introspect.",
                "options": [],
                "arguments": [],
                "subcommands": [],
            },
            {
                "name": "version",
                "description": "Version.",
                "options": [],
                "arguments": [],
                "subcommands": [],
            },
        ],
    }


class TestValidateTree:
    def test_valid_tree_passes(self) -> None:
        results = _validate_tree(_sample_tree())
        must_results = [r for r in results if r["level"] == "MUST"]
        assert all(r["pass"] for r in must_results)

    def test_missing_examples_fails(self) -> None:
        tree = _sample_tree()
        tree["commands"][0]["examples"] = [{"description": "Only one", "invocation": "x"}]
        results = _validate_tree(tree)
        example_check = next(r for r in results if "examples" in r["check"])
        assert example_check["pass"] is False

    def test_missing_introspect_fails(self) -> None:
        tree = _sample_tree()
        tree["commands"] = [c for c in tree["commands"] if c["name"] != "introspect"]
        results = _validate_tree(tree)
        introspect_check = next(r for r in results if "introspect" in r["check"])
        assert introspect_check["pass"] is False

    def test_missing_version_fails(self) -> None:
        tree = _sample_tree()
        tree["commands"] = [c for c in tree["commands"] if c["name"] != "version"]
        results = _validate_tree(tree)
        version_check = next(r for r in results if "version command" in r["check"])
        assert version_check["pass"] is False

    def test_missing_idempotency_is_should(self) -> None:
        tree = _sample_tree()
        del tree["commands"][0]["idempotent"]
        results = _validate_tree(tree)
        idem_check = next(r for r in results if "idempotency" in r["check"])
        assert idem_check["level"] == "SHOULD"
        assert idem_check["pass"] is False

    def test_option_type_annotation(self) -> None:
        results = _validate_tree(_sample_tree())
        type_check = next(r for r in results if "type annotation" in r["check"])
        assert type_check["pass"] is True

    def test_option_missing_type(self) -> None:
        tree = _sample_tree()
        tree["commands"][0]["options"][0]["type"] = ""
        results = _validate_tree(tree)
        type_check = next(r for r in results if "type annotation" in r["check"])
        assert type_check["pass"] is False


class TestValidateCommand:
    def test_validate_from_cli_folder(self) -> None:
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            with (
                patch("sys.argv", ["acli", "validate"]),
                patch("acli.cli._load_tree", return_value=_sample_tree()),
            ):
                try:
                    app.run()
                except SystemExit as e:
                    assert e.code in (0, None)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert "PASS" in output


class TestSkillCommand:
    def test_skill_writes_file(self, tmp_path: Path) -> None:
        out_path = tmp_path / "SKILLS.md"
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            with (
                patch("sys.argv", ["acli", "skill", "--out", str(out_path)]),
                patch("acli.cli._load_tree", return_value=_sample_tree()),
            ):
                try:
                    app.run()
                except SystemExit:
                    pass
        finally:
            sys.stdout = old_stdout

        assert out_path.exists()
        content = out_path.read_text()
        assert "# testapp" in content


class TestInitCommand:
    def test_init_creates_project(self, tmp_path: Path) -> None:
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        old_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmp_path)
            with patch("sys.argv", ["acli", "init", "--name", "myapp"]):
                try:
                    app.run()
                except SystemExit:
                    pass
            output = sys.stdout.getvalue()
        finally:
            os.chdir(old_cwd)
            sys.stdout = old_stdout

        project = tmp_path / "myapp"
        assert project.exists()
        assert (project / "pyproject.toml").exists()
        assert (project / "src" / "myapp" / "main.py").exists()
        assert "Created ACLI project" in output

    def test_init_conflict_existing_dir(self, tmp_path: Path) -> None:
        (tmp_path / "existing").mkdir()
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        old_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmp_path)
            with patch("sys.argv", ["acli", "init", "--name", "existing"]):
                try:
                    app.run()
                except SystemExit as e:
                    assert e.code == 5
        finally:
            os.chdir(old_cwd)
            sys.stderr = old_stderr

    def test_init_json_output(self, tmp_path: Path) -> None:
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        old_cwd = Path.cwd()
        try:
            import os

            os.chdir(tmp_path)
            with patch("sys.argv", ["acli", "init", "--name", "jsonapp", "--output", "json"]):
                try:
                    app.run()
                except SystemExit:
                    pass
            output = sys.stdout.getvalue()
        finally:
            os.chdir(old_cwd)
            sys.stdout = old_stdout

        parsed = json.loads(output)
        assert parsed["ok"] is True
        assert parsed["data"]["name"] == "jsonapp"


class TestRunIntrospect:
    def test_command_not_found(self) -> None:
        try:
            _run_introspect("nonexistent_binary_xyz")
        except SystemExit as e:
            assert e.code == 3

    def test_timeout(self) -> None:
        with patch("acli.cli.subprocess.run", side_effect=subprocess.TimeoutExpired("x", 30)):
            try:
                _run_introspect("slow_tool")
            except SystemExit as e:
                assert e.code == 6

    def test_nonzero_exit(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "error"
        with patch("acli.cli.subprocess.run", return_value=mock_result):
            try:
                _run_introspect("bad_tool")
            except SystemExit as e:
                assert e.code == 1

    def test_invalid_json(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "not json"
        with patch("acli.cli.subprocess.run", return_value=mock_result):
            try:
                _run_introspect("bad_json_tool")
            except SystemExit as e:
                assert e.code == 1

    def test_valid_introspect(self) -> None:
        tree = _sample_tree()
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"ok": True, "data": tree})
        with patch("acli.cli.subprocess.run", return_value=mock_result):
            result = _run_introspect("good_tool")
        assert result["name"] == "testapp"


class TestLoadTree:
    def test_no_bin_no_cli_folder(self, tmp_path: Path) -> None:
        import os

        old_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            with pytest.raises(SystemExit) as exc_info:
                _load_tree("")
            assert exc_info.value.code == 2
        finally:
            os.chdir(old_cwd)

    def test_loads_from_cli_folder(self, tmp_path: Path) -> None:
        import os

        cli_dir = tmp_path / ".cli"
        cli_dir.mkdir()
        (cli_dir / "commands.json").write_text(json.dumps(_sample_tree()))
        old_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            tree = _load_tree("")
            assert tree["name"] == "testapp"
        finally:
            os.chdir(old_cwd)

    def test_loads_from_bin(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({"ok": True, "data": _sample_tree()})
        with patch("acli.cli.subprocess.run", return_value=mock_result):
            tree = _load_tree("sometool")
        assert tree["name"] == "testapp"


class TestSkillViaLoadTree:
    def test_skill_json_output(self) -> None:
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            with (
                patch("sys.argv", ["acli", "skill", "--output", "json"]),
                patch("acli.cli._load_tree", return_value=_sample_tree()),
            ):
                try:
                    app.run()
                except SystemExit:
                    pass
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        parsed = json.loads(output)
        assert parsed["ok"] is True
        assert "# testapp" in parsed["data"]["content"]

    def test_skill_stdout(self) -> None:
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            with (
                patch("sys.argv", ["acli", "skill"]),
                patch("acli.cli._load_tree", return_value=_sample_tree()),
            ):
                try:
                    app.run()
                except SystemExit:
                    pass
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert "# testapp" in output


class TestValidateWithBin:
    def test_validate_bin_json(self) -> None:
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            with (
                patch("sys.argv", ["acli", "validate", "--bin", "testapp", "--output", "json"]),
                patch("acli.cli._load_tree", return_value=_sample_tree()),
            ):
                try:
                    app.run()
                except SystemExit:
                    pass
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        parsed = json.loads(output)
        assert parsed["ok"] is True
        assert parsed["data"]["compliant"] is True


class TestEmitResultsFailing:
    def test_failing_must_exits_8(self) -> None:
        tree = _sample_tree()
        tree["commands"][0]["examples"] = []
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            with (
                patch("sys.argv", ["acli", "validate"]),
                patch("acli.cli._load_tree", return_value=tree),
            ):
                try:
                    app.run()
                except SystemExit as e:
                    assert e.code == 8
        finally:
            sys.stdout = old_stdout


class TestInitValidation:
    def test_rejects_non_identifier(self, tmp_path: Path) -> None:
        import os

        old_cwd = Path.cwd()
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            os.chdir(tmp_path)
            with patch("sys.argv", ["acli", "init", "--name", "not-valid"]):
                try:
                    app.run()
                except SystemExit as e:
                    assert e.code == 2
        finally:
            os.chdir(old_cwd)
            sys.stderr = old_stderr

    def test_rejects_path_traversal(self, tmp_path: Path) -> None:
        import os

        old_cwd = Path.cwd()
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            os.chdir(tmp_path)
            with patch("sys.argv", ["acli", "init", "--name", "../../etc"]):
                try:
                    app.run()
                except SystemExit as e:
                    assert e.code == 2
        finally:
            os.chdir(old_cwd)
            sys.stderr = old_stderr


class TestDeepValidate:
    def test_help_success(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Usage: testapp [OPTIONS] COMMAND"
        with patch("acli.cli.subprocess.run", return_value=mock_result):
            results = _deep_validate("testapp", _sample_tree())
        help_check = next(r for r in results if "help" in r["check"])
        assert help_check["pass"] is True

    def test_help_failure(self) -> None:
        with patch("acli.cli.subprocess.run", side_effect=FileNotFoundError):
            results = _deep_validate("nonexistent", _sample_tree())
        help_check = next(r for r in results if "help" in r["check"])
        assert help_check["pass"] is False

    def test_version_json_valid(self) -> None:
        def mock_run(cmd, **kwargs):
            m = MagicMock()
            if "version" in cmd:
                m.returncode = 0
                m.stdout = json.dumps(
                    {
                        "ok": True,
                        "data": {"tool": "testapp", "version": "1.0.0"},
                    }
                )
            else:
                m.returncode = 0
                m.stdout = "help text"
                m.stderr = ""
            return m

        with patch("acli.cli.subprocess.run", side_effect=mock_run):
            results = _deep_validate("testapp", _sample_tree())
        ver_check = next(r for r in results if "version" in r["check"])
        assert ver_check["pass"] is True

    def test_error_envelope_check(self) -> None:
        error_envelope = json.dumps(
            {
                "ok": False,
                "error": {"code": "INVALID_ARGS", "message": "bad flag"},
            }
        )

        def mock_run(cmd, **kwargs):
            m = MagicMock()
            if "--bad-flag-xyz" in cmd:
                m.returncode = 2
                m.stdout = error_envelope
                m.stderr = ""
            elif "version" in cmd:
                m.returncode = 0
                m.stdout = json.dumps({"ok": True, "data": {"version": "1.0.0"}})
            else:
                m.returncode = 0
                m.stdout = "help"
                m.stderr = ""
            return m

        with patch("acli.cli.subprocess.run", side_effect=mock_run):
            results = _deep_validate("testapp", _sample_tree())
        envelope_checks = [r for r in results if "envelope" in r["check"]]
        assert any(r["pass"] for r in envelope_checks)
