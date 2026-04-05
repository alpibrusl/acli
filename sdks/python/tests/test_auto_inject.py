"""Tests for auto-injected --output and --dry-run parameters."""

from __future__ import annotations

import inspect
import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import typer

from acli.app import ACLIApp
from acli.command import acli_command
from acli.output import OutputFormat


class TestAutoInjectOutput:
    def test_output_added_when_missing(self) -> None:
        @acli_command(
            examples=[("A", "x a"), ("B", "x b")],
            idempotent=True,
        )
        def my_cmd(name: str = typer.Option(...)) -> None:
            """A command without --output."""

        sig = inspect.signature(my_cmd)
        assert "output" in sig.parameters

    def test_output_not_duplicated_when_present(self) -> None:
        @acli_command(
            examples=[("A", "x a"), ("B", "x b")],
            idempotent=True,
        )
        def my_cmd(
            name: str = typer.Option(...),
            output: OutputFormat = typer.Option(OutputFormat.json),
        ) -> None:
            """A command with --output already."""

        sig = inspect.signature(my_cmd)
        params = list(sig.parameters.keys())
        assert params.count("output") == 1

    def test_injected_output_not_passed_to_original(self) -> None:
        received: dict = {}

        @acli_command(
            examples=[("A", "x a"), ("B", "x b")],
            idempotent=True,
        )
        def my_cmd(name: str = typer.Option("world")) -> None:
            """No output param."""
            received["name"] = name

        # Call with the injected output param
        my_cmd(name="test", output=OutputFormat.json)
        assert received["name"] == "test"


class TestAutoInjectDryRun:
    def test_dry_run_added_for_non_idempotent(self) -> None:
        @acli_command(
            examples=[("A", "x a"), ("B", "x b")],
            idempotent=False,
        )
        def my_cmd(name: str = typer.Option(...)) -> None:
            """A non-idempotent command."""

        sig = inspect.signature(my_cmd)
        assert "dry_run" in sig.parameters
        assert "output" in sig.parameters

    def test_dry_run_not_added_for_idempotent(self) -> None:
        @acli_command(
            examples=[("A", "x a"), ("B", "x b")],
            idempotent=True,
        )
        def my_cmd(name: str = typer.Option(...)) -> None:
            """An idempotent command."""

        sig = inspect.signature(my_cmd)
        assert "dry_run" not in sig.parameters

    def test_dry_run_not_added_for_conditional(self) -> None:
        @acli_command(
            examples=[("A", "x a"), ("B", "x b")],
            idempotent="conditional",
        )
        def my_cmd(name: str = typer.Option(...)) -> None:
            """A conditionally idempotent command."""

        sig = inspect.signature(my_cmd)
        assert "dry_run" not in sig.parameters

    def test_dry_run_not_duplicated_when_present(self) -> None:
        @acli_command(
            examples=[("A", "x a"), ("B", "x b")],
            idempotent=False,
        )
        def my_cmd(
            name: str = typer.Option(...),
            dry_run: bool = typer.Option(False),
        ) -> None:
            """Already has --dry-run."""

        sig = inspect.signature(my_cmd)
        params = list(sig.parameters.keys())
        assert params.count("dry_run") == 1


class TestACLIErrorWithHint:
    def test_acli_error_includes_hint(self, tmp_path: Path) -> None:
        from acli.errors import InvalidArgsError

        app = ACLIApp(name="testcli", version="1.0.0", cli_dir=tmp_path)

        @app.command()
        @acli_command(
            examples=[("A", "testcli greet --name x"), ("B", "testcli greet --name y")],
            idempotent=True,
        )
        def greet(name: str = typer.Option(...)) -> None:
            """Greet."""
            raise InvalidArgsError(
                "Missing --name",
                hint="Did you mean: --name?",
                docs=".cli/examples/greet.sh",
            )

        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            with patch("sys.argv", ["testcli", "greet", "--name", "x"]):
                try:
                    app.run()
                except SystemExit as e:
                    assert e.code == 2
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        parsed = json.loads(output)
        assert parsed["ok"] is False
        assert parsed["error"]["hint"] == "Did you mean: --name?"
        assert parsed["error"]["docs"] == ".cli/examples/greet.sh"
