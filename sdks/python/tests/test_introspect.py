"""Tests for acli.introspect."""

from __future__ import annotations

from pathlib import Path

import typer

from acli.command import acli_command
from acli.introspect import build_command_tree
from acli.output import OutputFormat


def _make_app() -> typer.Typer:
    """Create a sample Typer app for testing."""
    app = typer.Typer()

    @app.command()
    @acli_command(
        examples=[
            ("Run a pipeline", "noether run --pipeline ./sprint.yaml"),
            ("Dry-run a pipeline", "noether run --pipeline ./sprint.yaml --dry-run"),
        ],
        idempotent=False,
        see_also=["status"],
    )
    def run(
        pipeline: Path = typer.Option(..., help="Path to pipeline file. type:path"),
        env: str = typer.Option("dev", help="Target environment. type:enum[dev|staging|prod]"),
        dry_run: bool = typer.Option(False, help="Describe actions without executing."),
        output: OutputFormat = typer.Option(OutputFormat.text, help="Output format."),
    ) -> None:
        """Execute a pipeline from a YAML file."""

    @app.command()
    def status() -> None:
        """Show current pipeline status."""

    return app


class TestBuildCommandTree:
    def test_structure(self) -> None:
        app = _make_app()
        tree = build_command_tree(app, "noether", "1.0.0")

        assert tree["name"] == "noether"
        assert tree["version"] == "1.0.0"
        assert tree["acli_version"] == "0.1.0"
        assert len(tree["commands"]) == 2

    def test_command_metadata(self) -> None:
        app = _make_app()
        tree = build_command_tree(app, "noether", "1.0.0")

        run_cmd = next(c for c in tree["commands"] if c["name"] == "run")
        assert run_cmd["description"] == "Execute a pipeline from a YAML file."
        assert run_cmd["idempotent"] is False
        assert len(run_cmd["examples"]) == 2
        assert run_cmd["see_also"] == ["status"]

    def test_options_extracted(self) -> None:
        app = _make_app()
        tree = build_command_tree(app, "noether", "1.0.0")

        run_cmd = next(c for c in tree["commands"] if c["name"] == "run")
        option_names = [o["name"] for o in run_cmd["options"]]
        assert "pipeline" in option_names
        assert "env" in option_names
        assert "dry_run" in option_names

    def test_option_defaults(self) -> None:
        app = _make_app()
        tree = build_command_tree(app, "noether", "1.0.0")

        run_cmd = next(c for c in tree["commands"] if c["name"] == "run")
        env_opt = next(o for o in run_cmd["options"] if o["name"] == "env")
        assert env_opt["default"] == "dev"

    def test_command_without_meta(self) -> None:
        app = _make_app()
        tree = build_command_tree(app, "noether", "1.0.0")

        status_cmd = next(c for c in tree["commands"] if c["name"] == "status")
        assert status_cmd["description"] == "Show current pipeline status."
        assert "idempotent" not in status_cmd

    def test_subgroups(self) -> None:
        app = typer.Typer()
        sub = typer.Typer(help="Manage configs")

        @sub.command()
        def show() -> None:
            """Show config."""

        app.add_typer(sub, name="config")

        tree = build_command_tree(app, "tool", "1.0.0")
        config_group = next(c for c in tree["commands"] if c["name"] == "config")
        assert config_group["description"] == "Manage configs"
        assert len(config_group["subcommands"]) == 1
        assert config_group["subcommands"][0]["name"] == "show"
