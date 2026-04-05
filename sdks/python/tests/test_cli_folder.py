"""Tests for acli.cli_folder."""

from __future__ import annotations

import json
from pathlib import Path

from acli.cli_folder import generate_cli_folder, needs_update


def _sample_tree() -> dict:
    return {
        "name": "noether",
        "version": "1.0.0",
        "acli_version": "0.1.0",
        "commands": [
            {
                "name": "run",
                "description": "Run a pipeline",
                "idempotent": False,
                "examples": [
                    {"description": "Basic run", "invocation": "noether run --file x.yaml"},
                    {
                        "description": "Dry run",
                        "invocation": "noether run --file x.yaml --dry-run",
                    },
                ],
                "arguments": [],
                "options": [],
                "subcommands": [],
            }
        ],
    }


class TestGenerateCliFolder:
    def test_creates_structure(self, tmp_path: Path) -> None:
        tree = _sample_tree()
        cli_dir = generate_cli_folder(tree, tmp_path)

        assert cli_dir == tmp_path / ".cli"
        assert (cli_dir / "commands.json").exists()
        assert (cli_dir / "README.md").exists()
        assert (cli_dir / "changelog.md").exists()
        assert (cli_dir / "examples").is_dir()
        assert (cli_dir / "schemas").is_dir()

    def test_commands_json_content(self, tmp_path: Path) -> None:
        tree = _sample_tree()
        cli_dir = generate_cli_folder(tree, tmp_path)

        data = json.loads((cli_dir / "commands.json").read_text())
        assert data["name"] == "noether"
        assert data["version"] == "1.0.0"
        assert len(data["commands"]) == 1

    def test_readme_content(self, tmp_path: Path) -> None:
        tree = _sample_tree()
        cli_dir = generate_cli_folder(tree, tmp_path)

        readme = (cli_dir / "README.md").read_text()
        assert "# noether" in readme
        assert "Version: 1.0.0" in readme
        assert "### run" in readme
        assert "Idempotent: False" in readme

    def test_example_scripts(self, tmp_path: Path) -> None:
        tree = _sample_tree()
        cli_dir = generate_cli_folder(tree, tmp_path)

        script = cli_dir / "examples" / "run.sh"
        assert script.exists()
        content = script.read_text()
        assert "#!/usr/bin/env bash" in content
        assert "noether run --file x.yaml" in content

    def test_changelog_not_overwritten(self, tmp_path: Path) -> None:
        tree = _sample_tree()
        cli_dir = generate_cli_folder(tree, tmp_path)

        # Write custom changelog
        (cli_dir / "changelog.md").write_text("# Custom")

        # Regenerate
        generate_cli_folder(tree, tmp_path)
        assert (cli_dir / "changelog.md").read_text() == "# Custom"

    def test_idempotent_generation(self, tmp_path: Path) -> None:
        tree = _sample_tree()
        generate_cli_folder(tree, tmp_path)
        generate_cli_folder(tree, tmp_path)

        data = json.loads((tmp_path / ".cli" / "commands.json").read_text())
        assert data["name"] == "noether"

    def test_command_without_examples(self, tmp_path: Path) -> None:
        tree = _sample_tree()
        tree["commands"].append(
            {
                "name": "status",
                "description": "Show status",
                "arguments": [],
                "options": [],
                "subcommands": [],
            }
        )
        cli_dir = generate_cli_folder(tree, tmp_path)
        assert not (cli_dir / "examples" / "status.sh").exists()


class TestNeedsUpdate:
    def test_no_existing_folder(self, tmp_path: Path) -> None:
        assert needs_update(_sample_tree(), tmp_path) is True

    def test_matching_content(self, tmp_path: Path) -> None:
        tree = _sample_tree()
        generate_cli_folder(tree, tmp_path)
        assert needs_update(tree, tmp_path) is False

    def test_changed_content(self, tmp_path: Path) -> None:
        tree = _sample_tree()
        generate_cli_folder(tree, tmp_path)
        tree["version"] = "2.0.0"
        assert needs_update(tree, tmp_path) is True

    def test_corrupted_json(self, tmp_path: Path) -> None:
        cli_dir = tmp_path / ".cli"
        cli_dir.mkdir()
        (cli_dir / "commands.json").write_text("not json")
        assert needs_update(_sample_tree(), tmp_path) is True
