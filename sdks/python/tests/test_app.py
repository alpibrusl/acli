"""Tests for acli.app (ACLIApp integration)."""

from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import typer

from acli.app import ACLIApp
from acli.command import acli_command
from acli.errors import InvalidArgsError
from acli.exit_codes import ExitCode
from acli.output import OutputFormat


def _make_app(tmp_path: Path) -> ACLIApp:
    """Create a sample ACLIApp for testing."""
    app = ACLIApp(name="testcli", version="0.5.0", cli_dir=tmp_path)

    @app.command()
    @acli_command(
        examples=[
            ("Greet world", "testcli greet --name world"),
            ("Greet with caps", "testcli greet --name WORLD"),
        ],
        idempotent=True,
    )
    def greet(
        name: str = typer.Option(..., help="Name to greet. type:string"),
        output: OutputFormat = typer.Option(OutputFormat.text, help="Output format."),
    ) -> None:
        """Greet someone by name."""
        from acli.output import emit, success_envelope

        data = {"greeting": f"Hello, {name}!"}
        emit(success_envelope("greet", data, version="0.5.0"), output)

    return app


class TestACLIApp:
    def test_has_introspect_command(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path)
        tree = app.get_command_tree()
        cmd_names = [c["name"] for c in tree["commands"]]
        assert "introspect" in cmd_names

    def test_has_version_command(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path)
        tree = app.get_command_tree()
        cmd_names = [c["name"] for c in tree["commands"]]
        assert "version" in cmd_names

    def test_has_user_command(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path)
        tree = app.get_command_tree()
        cmd_names = [c["name"] for c in tree["commands"]]
        assert "greet" in cmd_names

    def test_command_tree_structure(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path)
        tree = app.get_command_tree()
        assert tree["name"] == "testcli"
        assert tree["version"] == "0.5.0"
        assert tree["acli_version"] == "0.1.0"

    def test_typer_app_property(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path)
        assert isinstance(app.typer_app, typer.Typer)

    def test_handle_acli_error(self, tmp_path: Path) -> None:
        app = ACLIApp(name="t", version="1.0.0", cli_dir=tmp_path)

        @app.command()
        def fail() -> None:
            """Always fails."""
            raise InvalidArgsError("bad input", hint="fix it")

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            with patch("sys.argv", ["t", "fail"]):
                try:
                    app.run()
                except SystemExit as e:
                    assert e.code == ExitCode.INVALID_ARGS
                else:
                    raise AssertionError("Expected SystemExit")
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        parsed = json.loads(output)
        assert parsed["ok"] is False
        assert parsed["error"]["code"] == "INVALID_ARGS"
        assert parsed["error"]["hint"] == "fix it"

    def test_handle_unexpected_error(self, tmp_path: Path) -> None:
        app = ACLIApp(name="t", version="1.0.0", cli_dir=tmp_path)

        @app.command()
        def crash() -> None:
            """Always crashes."""
            msg = "oh no"
            raise RuntimeError(msg)

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            with patch("sys.argv", ["t", "crash"]):
                try:
                    app.run()
                except SystemExit as e:
                    assert e.code == ExitCode.GENERAL_ERROR
                else:
                    raise AssertionError("Expected SystemExit")
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        parsed = json.loads(output)
        assert parsed["ok"] is False
        assert "oh no" in parsed["error"]["message"]

    def test_add_typer(self, tmp_path: Path) -> None:
        app = ACLIApp(name="t", version="1.0.0", cli_dir=tmp_path)
        sub = typer.Typer(help="Sub commands")

        @sub.command()
        def sub_cmd() -> None:
            """A sub command."""

        app.add_typer(sub, name="sub")
        tree = app.get_command_tree()
        group = next(c for c in tree["commands"] if c["name"] == "sub")
        assert group["description"] == "Sub commands"


class TestACLIAppIntrospect:
    def test_introspect_via_cli(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path)

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            with patch("sys.argv", ["testcli", "introspect", "--output", "json"]):
                try:
                    app.run()
                except SystemExit:
                    pass
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        parsed = json.loads(output)
        assert parsed["ok"] is True
        assert parsed["data"]["name"] == "testcli"

    def test_introspect_acli_version(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path)

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            with patch("sys.argv", ["testcli", "introspect", "--acli-version"]):
                try:
                    app.run()
                except SystemExit:
                    pass
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        parsed = json.loads(output)
        assert parsed["acli_version"] == "0.1.0"

    def test_introspect_acli_version_text(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path)

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            with patch(
                "sys.argv", ["testcli", "introspect", "--acli-version", "--output", "text"]
            ):
                try:
                    app.run()
                except SystemExit:
                    pass
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert "acli 0.1.0" in output


class TestACLIAppSkill:
    def test_skill_stdout(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path)

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            with patch("sys.argv", ["testcli", "skill"]):
                try:
                    app.run()
                except SystemExit:
                    pass
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert "# testcli" in output
        assert "## Available commands" in output

    def test_skill_json(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path)

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            with patch("sys.argv", ["testcli", "skill", "--output", "json"]):
                try:
                    app.run()
                except SystemExit:
                    pass
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        parsed = json.loads(output)
        assert parsed["ok"] is True
        assert "# testcli" in parsed["data"]["content"]

    def test_skill_to_file(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path)
        out_file = tmp_path / "SKILLS.md"

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            with patch("sys.argv", ["testcli", "skill", "--out", str(out_file)]):
                try:
                    app.run()
                except SystemExit:
                    pass
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert out_file.exists()
        assert "# testcli" in out_file.read_text()
        assert "Skill file written to" in output


class TestACLIAppVersion:
    def test_version_text(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path)

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            with patch("sys.argv", ["testcli", "version"]):
                try:
                    app.run()
                except SystemExit:
                    pass
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        assert "testcli 0.5.0" in output
        assert "acli 0.1.0" in output

    def test_version_json(self, tmp_path: Path) -> None:
        app = _make_app(tmp_path)

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            with patch("sys.argv", ["testcli", "version", "--output", "json"]):
                try:
                    app.run()
                except SystemExit:
                    pass
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        parsed = json.loads(output)
        assert parsed["ok"] is True
        assert parsed["data"]["tool"] == "testcli"
        assert parsed["data"]["version"] == "0.5.0"
