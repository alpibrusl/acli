"""Tests for acli.skill."""

from __future__ import annotations

from pathlib import Path

from acli.skill import generate_skill


def _sample_tree() -> dict:
    return {
        "name": "noether",
        "version": "1.0.0",
        "acli_version": "0.1.0",
        "commands": [
            {
                "name": "run",
                "description": "Execute a pipeline from a YAML file.",
                "idempotent": False,
                "options": [
                    {
                        "name": "pipeline",
                        "type": "path",
                        "description": "Path to pipeline file.",
                    },
                    {
                        "name": "env",
                        "type": "string",
                        "description": "Target environment.",
                        "default": "dev",
                    },
                ],
                "arguments": [
                    {
                        "name": "target",
                        "type": "string",
                        "required": True,
                        "description": "Deployment target.",
                    },
                ],
                "examples": [
                    {
                        "description": "Run in staging",
                        "invocation": "noether run --pipeline x.yaml --env staging",
                    },
                    {
                        "description": "Dry run",
                        "invocation": "noether run --pipeline x.yaml --dry-run",
                    },
                ],
                "see_also": ["status"],
                "subcommands": [],
            },
            {
                "name": "status",
                "description": "Show pipeline status.",
                "idempotent": True,
                "options": [],
                "arguments": [],
                "examples": [],
                "subcommands": [],
            },
            {
                "name": "introspect",
                "description": "Output command tree.",
                "options": [],
                "arguments": [],
                "subcommands": [],
            },
            {
                "name": "version",
                "description": "Show version.",
                "options": [],
                "arguments": [],
                "subcommands": [],
            },
        ],
    }


class TestGenerateSkill:
    def test_basic_structure(self) -> None:
        content = generate_skill(_sample_tree())
        assert "# noether" in content
        assert "v1.0.0" in content
        assert "## Available commands" in content

    def test_excludes_builtin_commands(self) -> None:
        content = generate_skill(_sample_tree())
        assert "`noether run`" in content
        assert "`noether status`" in content
        available = content.split("## Available commands")[1].split("##")[0]
        assert "`noether introspect`" not in available

    def test_command_details(self) -> None:
        content = generate_skill(_sample_tree())
        assert "## `noether run`" in content
        assert "Execute a pipeline" in content

    def test_options_rendered(self) -> None:
        content = generate_skill(_sample_tree())
        assert "--pipeline" in content
        assert "--env" in content
        assert "[default: dev]" in content

    def test_arguments_rendered(self) -> None:
        content = generate_skill(_sample_tree())
        assert "`target`" in content
        assert "required" in content
        assert "Deployment target" in content

    def test_examples_rendered(self) -> None:
        content = generate_skill(_sample_tree())
        assert "noether run --pipeline x.yaml --env staging" in content
        assert "# Run in staging" in content

    def test_see_also_rendered(self) -> None:
        content = generate_skill(_sample_tree())
        assert "`noether status`" in content
        assert "**See also:**" in content

    def test_idempotent_tag(self) -> None:
        content = generate_skill(_sample_tree())
        assert "(idempotent)" in content

    def test_conditional_idempotent(self) -> None:
        tree = _sample_tree()
        tree["commands"][0]["idempotent"] = "conditional"
        content = generate_skill(tree)
        assert "(conditionally idempotent)" in content

    def test_output_format_section(self) -> None:
        content = generate_skill(_sample_tree())
        assert "## Output format" in content
        assert '"ok": true' in content

    def test_exit_codes_section(self) -> None:
        content = generate_skill(_sample_tree())
        assert "## Exit codes" in content
        assert "Invalid arguments" in content

    def test_further_discovery_section(self) -> None:
        content = generate_skill(_sample_tree())
        assert "## Further discovery" in content
        assert "`noether --help`" in content
        assert "`noether introspect`" in content
        assert "`.cli/README.md`" in content

    def test_write_to_file(self, tmp_path: Path) -> None:
        target = tmp_path / "SKILLS.md"
        content = generate_skill(_sample_tree(), target_path=target)
        assert target.exists()
        assert target.read_text() == content

    def test_write_creates_parent_dirs(self, tmp_path: Path) -> None:
        target = tmp_path / "nested" / "dir" / "SKILLS.md"
        generate_skill(_sample_tree(), target_path=target)
        assert target.exists()

    def test_regenerate_hint(self) -> None:
        content = generate_skill(_sample_tree())
        assert "Re-generate with:" in content
        assert "`noether skill`" in content
