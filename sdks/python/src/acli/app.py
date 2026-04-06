"""ACLIApp — the main application class wrapping Typer per ACLI spec §8."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import typer

from acli.cli_folder import generate_cli_folder, needs_update
from acli.errors import ACLIError
from acli.exit_codes import ExitCode
from acli.introspect import build_command_tree
from acli.output import OutputFormat, emit, error_envelope, success_envelope
from acli.skill import generate_skill


class ACLIApp:
    """ACLI-compliant application wrapper around Typer.

    Automatically registers the ``introspect`` command, enforces JSON error
    envelopes, and generates the ``.cli/`` folder.
    """

    def __init__(
        self,
        name: str,
        version: str,
        *,
        cli_dir: Path | None = None,
        **typer_kwargs: Any,
    ) -> None:
        self.name = name
        self.version = version
        self.cli_dir = cli_dir
        self._typer = typer.Typer(name=name, help=typer_kwargs.pop("help", None), **typer_kwargs)
        self._register_introspect()
        self._register_version()
        self._register_skill()

    @property
    def typer_app(self) -> typer.Typer:
        """Access the underlying Typer instance."""
        return self._typer

    # ── Public API ────────────────────────────────────────────────────────────

    def command(self, *args: Any, **kwargs: Any) -> Any:
        """Register a command — proxy to typer.command()."""
        return self._typer.command(*args, **kwargs)

    def add_typer(self, *args: Any, **kwargs: Any) -> None:
        """Add a sub-group — proxy to typer.add_typer()."""
        self._typer.add_typer(*args, **kwargs)

    def run(self) -> None:
        """Run the application with ACLI error handling."""
        try:
            self._typer()
        except ACLIError as exc:
            self._handle_acli_error(exc)
        except SystemExit:
            raise
        except Exception as exc:
            self._handle_unexpected_error(exc)

    def get_command_tree(self) -> dict[str, Any]:
        """Build the introspection command tree."""
        return build_command_tree(self._typer, self.name, self.version)

    # ── Built-in commands ─────────────────────────────────────────────────────

    def _register_introspect(self) -> None:
        @self._typer.command(name="introspect", hidden=True)
        def introspect(
            acli_version: bool = typer.Option(
                False, "--acli-version", help="Show only the ACLI spec version. type:bool"
            ),
            output: OutputFormat = typer.Option(
                OutputFormat.json, "--output", help="Output format. type:enum[text|json|table]"
            ),
        ) -> None:
            """Output the full command tree as JSON for agent consumption."""
            if acli_version:
                if output == OutputFormat.json:
                    json.dump({"acli_version": "0.1.0"}, sys.stdout)
                    sys.stdout.write("\n")
                else:
                    sys.stdout.write("acli 0.1.0\n")
                return

            tree = self.get_command_tree()

            # Update .cli/ if needed
            if needs_update(tree, self.cli_dir):
                generate_cli_folder(tree, self.cli_dir)

            emit(success_envelope("introspect", tree, version=self.version), output)

    def _register_version(self) -> None:
        @self._typer.command(name="version", hidden=True)
        def version_cmd(
            output: OutputFormat = typer.Option(
                OutputFormat.text,
                "--output",
                help="Output format. type:enum[text|json|table]",
            ),
        ) -> None:
            """Show version information."""
            if output == OutputFormat.json:
                data = {
                    "tool": self.name,
                    "version": self.version,
                    "acli_version": "0.1.0",
                }
                emit(success_envelope("version", data, version=self.version), output)
            else:
                sys.stdout.write(f"{self.name} {self.version}\n")
                sys.stdout.write("acli 0.1.0\n")

            # Update .cli/ if needed
            tree = self.get_command_tree()
            if needs_update(tree, self.cli_dir):
                generate_cli_folder(tree, self.cli_dir)

    def _register_skill(self) -> None:
        @self._typer.command(name="skill", hidden=True)
        def skill_cmd(
            out: str = typer.Option(
                "",
                "--out",
                help="Write skill file to this path instead of stdout. type:path",
            ),
            output: OutputFormat = typer.Option(
                OutputFormat.text,
                "--output",
                help="Output format. type:enum[text|json|table]",
            ),
        ) -> None:
            """Generate a SKILLS.md file for agent bootstrapping."""
            tree = self.get_command_tree()
            target = Path(out) if out else None
            content = generate_skill(tree, target_path=target)

            if output == OutputFormat.json:
                data = {"path": str(target) if target else None, "content": content}
                emit(success_envelope("skill", data, version=self.version), output)
            elif target:
                sys.stdout.write(f"Skill file written to {target}\n")
            else:
                sys.stdout.write(content)

    # ── Error handling ────────────────────────────────────────────────────────

    def _handle_acli_error(self, exc: ACLIError) -> None:
        cmd_name = exc.command or self.name
        envelope = error_envelope(
            cmd_name,
            code=exc.code.name,
            message=str(exc),
            hint=exc.hint,
            hints=exc.hints,
            docs=exc.docs,
            version=self.version,
        )
        emit(envelope, OutputFormat.json)
        raise SystemExit(exc.code.value)

    def _handle_unexpected_error(self, exc: Exception) -> None:
        envelope = error_envelope(
            self.name,
            code="GENERAL_ERROR",
            message=str(exc),
            hint="This is an unexpected error. Please report it.",
            version=self.version,
        )
        emit(envelope, OutputFormat.json)
        raise SystemExit(ExitCode.GENERAL_ERROR)
