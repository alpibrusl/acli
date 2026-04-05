"""Generate and maintain the .cli/ reference folder per ACLI spec §1.3."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def generate_cli_folder(
    command_tree: dict[str, Any],
    target_dir: Path | None = None,
) -> Path:
    """Generate the .cli/ folder with all required files.

    Args:
        command_tree: The full command tree from introspect.
        target_dir: Root directory for .cli/. Defaults to cwd.

    Returns:
        Path to the generated .cli/ directory.
    """
    root = (target_dir or Path.cwd()) / ".cli"
    root.mkdir(parents=True, exist_ok=True)
    (root / "examples").mkdir(exist_ok=True)
    (root / "schemas").mkdir(exist_ok=True)

    # commands.json
    (root / "commands.json").write_text(json.dumps(command_tree, indent=2) + "\n")

    # README.md
    _write_readme(root, command_tree)

    # Example scripts
    _write_examples(root, command_tree)

    # changelog.md (create if missing)
    changelog = root / "changelog.md"
    if not changelog.exists():
        version = command_tree.get("version", "0.0.0")
        changelog.write_text(f"# Changelog\n\n## {version}\n\n- Initial release\n")

    return root


def _write_readme(cli_dir: Path, tree: dict[str, Any]) -> None:
    """Generate .cli/README.md from the command tree."""
    name = tree.get("name", "tool")
    version = tree.get("version", "0.0.0")
    lines = [
        f"# {name}",
        "",
        f"Version: {version}",
        f"ACLI version: {tree.get('acli_version', '0.1.0')}",
        "",
        "## Commands",
        "",
    ]
    for cmd in tree.get("commands", []):
        lines.append(f"### {cmd['name']}")
        lines.append("")
        lines.append(cmd.get("description", ""))
        lines.append("")
        if cmd.get("idempotent") is not None:
            lines.append(f"Idempotent: {cmd['idempotent']}")
            lines.append("")

    (cli_dir / "README.md").write_text("\n".join(lines) + "\n")


def _write_examples(cli_dir: Path, tree: dict[str, Any]) -> None:
    """Generate .cli/examples/<command>.sh files."""
    for cmd in tree.get("commands", []):
        examples = cmd.get("examples", [])
        if not examples:
            continue
        lines = ["#!/usr/bin/env bash", f"# Examples for: {cmd['name']}", ""]
        for ex in examples:
            lines.append(f"# {ex['description']}")
            lines.append(ex["invocation"])
            lines.append("")
        path = cli_dir / "examples" / f"{cmd['name']}.sh"
        path.write_text("\n".join(lines))


def needs_update(command_tree: dict[str, Any], target_dir: Path | None = None) -> bool:
    """Check whether .cli/commands.json is out of date."""
    root = (target_dir or Path.cwd()) / ".cli"
    commands_file = root / "commands.json"
    if not commands_file.exists():
        return True
    try:
        existing = json.loads(commands_file.read_text())
    except (json.JSONDecodeError, OSError):
        return True
    return bool(existing != command_tree)
