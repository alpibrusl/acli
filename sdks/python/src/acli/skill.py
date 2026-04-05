"""Generate SKILLS.md files from ACLI command trees.

Bridges Stage 2 (SKILLS.md) and Stage 3 (ACLI) — an ACLI tool can auto-generate
a skill file so agents have immediate context without needing to run --help first.
The skill file is always re-generable from the source of truth (the tool itself).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

_BUILTIN_COMMANDS = ("introspect", "version", "skill")

_OUTPUT_SECTION = (
    "All commands support `--output json|text|table`. "
    "When using `--output json`, responses follow a standard envelope:"
)

_JSON_EXAMPLE = (
    '{"ok": true, "command": "...", "data": {...}, "meta": {"duration_ms": ..., "version": "..."}}'
)

_ERROR_SECTION = (
    'Errors use the same envelope with `"ok": false` and an '
    '`"error"` object containing `code`, `message`, `hint`, and `docs`.'
)


def generate_skill(
    command_tree: dict[str, Any],
    *,
    target_path: Path | None = None,
) -> str:
    """Generate a SKILLS.md file from an ACLI command tree.

    Args:
        command_tree: The full command tree from introspect/build_command_tree.
        target_path: If provided, write the skill file to this path.

    Returns:
        The generated skill file content as a string.
    """
    name = command_tree.get("name", "tool")
    version = command_tree.get("version", "0.0.0")
    commands = command_tree.get("commands", [])

    lines: list[str] = []
    lines.append(f"# {name}")
    lines.append("")
    lines.append(f"> Auto-generated skill file for `{name}` v{version}")
    lines.append(f"> Re-generate with: `{name} skill` or `acli skill --bin {name}`")
    lines.append("")

    # Quick reference
    lines.append("## Available commands")
    lines.append("")
    user_commands = [c for c in commands if c["name"] not in _BUILTIN_COMMANDS]
    for cmd in user_commands:
        desc = cmd.get("description", "")
        idem = cmd.get("idempotent")
        idem_tag = ""
        if idem is True:
            idem_tag = " (idempotent)"
        elif idem == "conditional":
            idem_tag = " (conditionally idempotent)"
        lines.append(f"- `{name} {cmd['name']}` — {desc}{idem_tag}")
    lines.append("")

    # Detailed usage per command
    for cmd in user_commands:
        _render_command(lines, name, cmd)

    # Output contracts
    lines.append("## Output format")
    lines.append("")
    lines.append(_OUTPUT_SECTION)
    lines.append("")
    lines.append("```json")
    lines.append(_JSON_EXAMPLE)
    lines.append("```")
    lines.append("")
    lines.append(_ERROR_SECTION)
    lines.append("")

    # Exit codes
    lines.append("## Exit codes")
    lines.append("")
    lines.append("| Code | Meaning | Action |")
    lines.append("|------|---------|--------|")
    lines.append("| 0 | Success | Proceed |")
    lines.append("| 2 | Invalid arguments | Correct and retry |")
    lines.append("| 3 | Not found | Check inputs |")
    lines.append("| 5 | Conflict | Resolve conflict |")
    lines.append("| 8 | Precondition failed | Fix precondition |")
    lines.append("| 9 | Dry-run completed | Review and confirm |")
    lines.append("")

    # Discovery hint
    lines.append("## Further discovery")
    lines.append("")
    lines.append(f"- `{name} --help` — full help for any command")
    lines.append(f"- `{name} introspect` — machine-readable command tree (JSON)")
    lines.append("- `.cli/README.md` — persistent reference (survives context resets)")
    lines.append("")

    content = "\n".join(lines)

    if target_path is not None:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content)

    return content


def _render_command(lines: list[str], tool_name: str, cmd: dict[str, Any]) -> None:
    """Render a single command's detailed section."""
    lines.append(f"## `{tool_name} {cmd['name']}`")
    lines.append("")
    if desc := cmd.get("description", ""):
        lines.append(desc)
        lines.append("")

    # Options
    for opt in cmd.get("options", []):
        if not lines[-1].startswith("### Options"):
            lines.append("### Options")
            lines.append("")
        opt_name = opt["name"].replace("_", "-")
        opt_type = opt.get("type", "")
        opt_desc = opt.get("description", "")
        default = opt.get("default")
        default_str = f" [default: {default}]" if default is not None else ""
        lines.append(f"- `--{opt_name}` ({opt_type}) — {opt_desc}{default_str}")
    if cmd.get("options"):
        lines.append("")

    # Arguments
    for arg in cmd.get("arguments", []):
        if not lines[-1].startswith("### Arguments"):
            lines.append("### Arguments")
            lines.append("")
        req = "required" if arg.get("required") else "optional"
        arg_type = arg.get("type", "")
        arg_desc = arg.get("description", "")
        lines.append(f"- `{arg['name']}` ({arg_type}, {req}) — {arg_desc}")
    if cmd.get("arguments"):
        lines.append("")

    # Examples
    examples = cmd.get("examples", [])
    if examples:
        lines.append("### Examples")
        lines.append("")
        for ex in examples:
            lines.append("```bash")
            lines.append(f"# {ex['description']}")
            lines.append(ex["invocation"])
            lines.append("```")
            lines.append("")

    # See also
    see_also = cmd.get("see_also", [])
    if see_also:
        refs = ", ".join(f"`{tool_name} {s}`" for s in see_also)
        lines.append(f"**See also:** {refs}")
        lines.append("")
