"""Generate SKILL.md files from ACLI command trees.

Emits a file conforming to the agentskills.io open standard
(https://agentskills.io): YAML frontmatter (``name``, ``description``, optional
``when_to_use``) followed by the ACLI command reference body. The generated
file drops into ``.claude/skills/<tool>/SKILL.md``,
``.cursor/skills/<tool>/SKILL.md``, Gemini CLI, Codex, etc. without
modification.
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


def _default_description(name: str, user_commands: list[dict[str, Any]]) -> str:
    if not user_commands:
        return f"Invoke the `{name}` CLI."
    shown = [c["name"] for c in user_commands[:4]]
    suffix = "…" if len(user_commands) > 4 else ""
    return f"Invoke the `{name}` CLI. Commands: {', '.join(shown)}{suffix}"


def _one_line(value: str) -> str:
    return " ".join(value.split())


# YAML indicators that, when a scalar starts with them, require quoting.
_YAML_RESERVED_START = ("!", "&", "*", "?", "|", ">", "'", '"', "%", "@", "`", "#", ",", "[", "]", "{", "}", "-")


def _yaml_scalar(value: str) -> str:
    """Render a scalar safe for a single-line YAML block mapping value.

    Double-quotes the value when it contains constructs that would make a
    strict YAML parser reject the plain form — in particular ``": "`` (which
    looks like a nested mapping) and comment-introducing `` # ``. Backslash
    and double-quote are escaped inside the quoted form.
    """
    if not value:
        return '""'
    needs_quoting = (
        ": " in value
        or " #" in value
        or value[0] in _YAML_RESERVED_START
        or value[-1] == ":"
        or value.strip() != value
    )
    if not needs_quoting:
        return value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def generate_skill(
    command_tree: dict[str, Any],
    *,
    target_path: Path | None = None,
    description: str | None = None,
    when_to_use: str | None = None,
) -> str:
    """Generate a SKILL.md file from an ACLI command tree.

    Args:
        command_tree: Full command tree (as produced by ``build_command_tree``).
        target_path: If provided, write the skill file to this path.
        description: Frontmatter ``description``. When omitted, synthesised
            from the tool name and its first few user-facing commands.
        when_to_use: Optional frontmatter ``when_to_use``. Only rendered when
            explicitly supplied.

    Returns:
        The generated skill file content as a string.
    """
    name = command_tree.get("name", "tool")
    version = command_tree.get("version", "0.0.0")
    commands = command_tree.get("commands", [])
    user_commands = [c for c in commands if c["name"] not in _BUILTIN_COMMANDS]

    desc = _one_line(description) if description else _default_description(name, user_commands)

    lines: list[str] = [
        "---",
        f"name: {_yaml_scalar(name)}",
        f"description: {_yaml_scalar(desc)}",
    ]
    if when_to_use:
        lines.append(f"when_to_use: {_yaml_scalar(_one_line(when_to_use))}")
    lines.append("---")
    lines.append("")

    lines.append(f"# {name}")
    lines.append("")
    lines.append(f"> Auto-generated skill file for `{name}` v{version}")
    lines.append(f"> Re-generate with: `{name} skill` or `acli skill --bin {name}`")
    lines.append("")

    # Quick reference
    lines.append("## Available commands")
    lines.append("")
    for cmd in user_commands:
        cmd_desc = cmd.get("description", "")
        idem = cmd.get("idempotent")
        idem_tag = ""
        if idem is True:
            idem_tag = " (idempotent)"
        elif idem == "conditional":
            idem_tag = " (conditionally idempotent)"
        lines.append(f"- `{name} {cmd['name']}` — {cmd_desc}{idem_tag}")
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
    options = cmd.get("options", [])
    if options:
        lines.append("### Options")
        lines.append("")
        for opt in options:
            opt_name = opt["name"].replace("_", "-")
            opt_type = opt.get("type", "")
            opt_desc = opt.get("description", "")
            default = opt.get("default")
            default_str = f" [default: {default}]" if default is not None else ""
            lines.append(f"- `--{opt_name}` ({opt_type}) — {opt_desc}{default_str}")
        lines.append("")

    # Arguments
    arguments = cmd.get("arguments", [])
    if arguments:
        lines.append("### Arguments")
        lines.append("")
        for arg in arguments:
            req = "required" if arg.get("required") else "optional"
            arg_type = arg.get("type", "")
            arg_desc = arg.get("description", "")
            lines.append(f"- `{arg['name']}` ({arg_type}, {req}) — {arg_desc}")
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
