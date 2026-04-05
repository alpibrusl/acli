"""The `acli` CLI tool — the ACLI of ACLI.

A meta-CLI that helps developers build, validate, and bootstrap ACLI-compliant tools.
It is itself ACLI-compliant.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import typer

from acli.app import ACLIApp
from acli.command import acli_command
from acli.output import OutputFormat, emit, success_envelope
from acli.skill import generate_skill

app = ACLIApp(name="acli", version="0.1.0")


@app.command()
@acli_command(
    examples=[
        ("Validate current directory", "acli validate"),
        ("Validate a specific binary", "acli validate --bin noether"),
    ],
    idempotent=True,
    see_also=["skill", "init"],
)
def validate(
    bin_name: str = typer.Option(
        "",
        "--bin",
        help="Name or path of the CLI binary to validate. type:string",
    ),
    output: OutputFormat = typer.Option(
        OutputFormat.text, "--output", help="Output format. type:enum[text|json|table]"
    ),
) -> None:
    """Validate an ACLI tool against the specification checklist.

    Runs the target tool's introspect command and checks compliance with
    the ACLI spec: help structure, examples, output format, exit codes,
    dry-run support, and idempotency declarations.
    """
    tree = _load_tree(bin_name)
    tool_name = bin_name or tree.get("name", "unknown")
    results = _validate_tree(tree)
    _emit_results(results, tool_name, output)


@app.command()
@acli_command(
    examples=[
        ("Generate skill file for a tool", "acli skill --bin noether"),
        ("Write skill file to a specific path", "acli skill --bin noether --out SKILLS.md"),
    ],
    idempotent=True,
    see_also=["validate", "init"],
)
def skill(
    bin_name: str = typer.Option(
        "",
        "--bin",
        help="Name or path of the CLI binary to generate a skill file for. type:string",
    ),
    out: str = typer.Option(
        "",
        "--out",
        help="Write skill file to this path instead of stdout. type:path",
    ),
    output: OutputFormat = typer.Option(
        OutputFormat.text, "--output", help="Output format. type:enum[text|json|table]"
    ),
) -> None:
    """Generate a SKILLS.md file for an ACLI tool.

    Creates a skill file that gives agents immediate context about the tool's
    capabilities, commands, options, and examples. This bridges the cold-start
    gap: agents get Stage 2 context (SKILLS.md) auto-generated from Stage 3
    source of truth (the tool itself).
    """
    tree = _load_tree(bin_name)
    target = Path(out) if out else None
    content = generate_skill(tree, target_path=target)

    if output == OutputFormat.json:
        data = {"path": str(target) if target else None, "content": content}
        emit(success_envelope("skill", data, version="0.1.0"), output)
    elif target:
        sys.stdout.write(f"Skill file written to {target}\n")
    else:
        sys.stdout.write(content)


@app.command()
@acli_command(
    examples=[
        ("Scaffold a new ACLI project", "acli init --name myapp"),
        ("Scaffold with version", "acli init --name myapp --ver 0.1.0"),
    ],
    idempotent=False,
    see_also=["validate", "skill"],
)
def init(
    name: str = typer.Option(..., "--name", help="Name of the new ACLI tool. type:string"),
    ver: str = typer.Option("0.1.0", "--ver", help="Initial version. type:string"),
    output: OutputFormat = typer.Option(
        OutputFormat.text, "--output", help="Output format. type:enum[text|json|table]"
    ),
) -> None:
    """Scaffold a new ACLI-compliant Python project.

    Creates a minimal project structure with ACLIApp, pyproject.toml,
    and a sample command that follows the specification.
    """
    if not name.isidentifier():
        sys.stderr.write(f"Invalid project name: '{name}' (must be a valid Python identifier)\n")
        raise SystemExit(2)

    target = Path.cwd() / name
    if target.resolve().parent != Path.cwd().resolve():
        sys.stderr.write(f"Invalid project name: '{name}' (path traversal not allowed)\n")
        raise SystemExit(2)

    if target.exists():
        sys.stderr.write(f"Directory {target} already exists.\n")
        raise SystemExit(5)

    target.mkdir(parents=True)
    src_dir = target / "src" / name
    src_dir.mkdir(parents=True)

    replacements = {"{{name}}": name, "{{version}}": ver}

    # pyproject.toml
    (target / "pyproject.toml").write_text(_render_template("pyproject.toml.tpl", replacements))

    # __init__.py
    (src_dir / "__init__.py").write_text("")

    # main.py
    (src_dir / "main.py").write_text(_render_template("main.py.tpl", replacements))

    created = ["pyproject.toml", f"src/{name}/__init__.py", f"src/{name}/main.py"]

    if output == OutputFormat.json:
        data = {"name": name, "version": ver, "path": str(target), "files": created}
        emit(success_envelope("init", data, version="0.1.0"), output)
    else:
        sys.stdout.write(f"Created ACLI project '{name}' at {target}\n")
        for f in created:
            sys.stdout.write(f"  {f}\n")


# ── Helpers ───────────────────────────────────────────────────────────────────


def _render_template(template_name: str, replacements: dict[str, str]) -> str:
    """Render a template file from acli/templates/ with replacements."""
    template_dir = Path(__file__).parent / "templates"
    content = (template_dir / template_name).read_text()
    for key, value in replacements.items():
        content = content.replace(key, value)
    return content


def _load_tree(bin_name: str) -> dict[str, Any]:
    """Load a command tree from --bin or from .cli/commands.json in cwd."""
    if bin_name:
        return _run_introspect(bin_name)

    cli_dir = Path.cwd() / ".cli"
    if cli_dir.exists():
        commands_file = cli_dir / "commands.json"
        if commands_file.exists():
            return json.loads(commands_file.read_text())  # type: ignore[no-any-return]

    sys.stderr.write("No --bin specified and no .cli/ folder found in current directory.\n")
    sys.stderr.write("Usage: acli <command> --bin <tool>\n")
    raise SystemExit(2)


def _run_introspect(bin_name: str) -> dict[str, Any]:
    """Run a tool's introspect command and return the command tree."""
    try:
        result = subprocess.run(  # noqa: S603
            [bin_name, "introspect", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except FileNotFoundError:
        sys.stderr.write(f"Command not found: {bin_name}\n")
        raise SystemExit(3) from None
    except subprocess.TimeoutExpired:
        sys.stderr.write(f"Timed out running: {bin_name} introspect\n")
        raise SystemExit(6) from None

    if result.returncode != 0:
        sys.stderr.write(f"Failed to run '{bin_name} introspect':\n{result.stderr}\n")
        raise SystemExit(1)

    try:
        envelope: dict[str, Any] = json.loads(result.stdout)
        data: dict[str, Any] = envelope.get("data", envelope)
        return data
    except json.JSONDecodeError:
        sys.stderr.write(f"Invalid JSON from '{bin_name} introspect'\n")
        raise SystemExit(1) from None


def _validate_tree(tree: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate a command tree against the ACLI spec checklist."""
    results: list[dict[str, Any]] = []
    commands = tree.get("commands", [])
    builtin = ("introspect", "version", "skill")
    user_commands = [c for c in commands if c.get("name") not in builtin]

    # §1.2 — introspect command exists
    has_introspect = any(c.get("name") == "introspect" for c in commands)
    results.append(
        {
            "check": "introspect command exists",
            "spec": "§1.2",
            "level": "MUST",
            "pass": has_introspect,
        }
    )

    # §7.1 — version command exists
    has_version = any(c.get("name") == "version" for c in commands)
    results.append(
        {
            "check": "version command exists",
            "spec": "§7.1",
            "level": "MUST",
            "pass": has_version,
        }
    )

    for cmd in user_commands:
        cmd_name = cmd.get("name", "unknown")

        # §1.1 — at least 2 examples
        examples = cmd.get("examples", [])
        results.append(
            {
                "check": f"{cmd_name}: at least 2 examples",
                "spec": "§1.1",
                "level": "MUST",
                "pass": len(examples) >= 2,
            }
        )

        # §1.1 — type annotations on options
        for opt in cmd.get("options", []):
            has_type = bool(opt.get("type"))
            results.append(
                {
                    "check": f"{cmd_name}: --{opt['name']} has type annotation",
                    "spec": "§1.1",
                    "level": "MUST",
                    "pass": has_type,
                }
            )

        # §2.1 — --output flag exists
        option_names = [o.get("name", "") for o in cmd.get("options", [])]
        has_output = "output" in option_names
        results.append(
            {
                "check": f"{cmd_name}: --output flag exists",
                "spec": "§2.1",
                "level": "MUST",
                "pass": has_output,
            }
        )

        # §5 — --dry-run on non-idempotent commands
        is_idempotent = cmd.get("idempotent")
        if is_idempotent is False:
            has_dry_run = "dry_run" in option_names or "dry-run" in option_names
            results.append(
                {
                    "check": f"{cmd_name}: --dry-run on state-modifying command",
                    "spec": "§5",
                    "level": "MUST",
                    "pass": has_dry_run,
                }
            )

        # §1.1 — description exists
        has_description = bool(cmd.get("description", "").strip())
        results.append(
            {
                "check": f"{cmd_name}: has description",
                "spec": "§1.1",
                "level": "MUST",
                "pass": has_description,
            }
        )

        # §6 — idempotency declared
        has_idempotent = "idempotent" in cmd
        results.append(
            {
                "check": f"{cmd_name}: idempotency declared",
                "spec": "§6",
                "level": "SHOULD",
                "pass": has_idempotent,
            }
        )

        # §1.1 — SEE ALSO present
        has_see_also = bool(cmd.get("see_also"))
        results.append(
            {
                "check": f"{cmd_name}: SEE ALSO references",
                "spec": "§1.1",
                "level": "SHOULD",
                "pass": has_see_also,
            }
        )

    return results


def _emit_results(results: list[dict[str, Any]], tool_name: str, fmt: OutputFormat) -> None:
    """Emit validation results."""
    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    all_must_pass = all(r["pass"] for r in results if r["level"] == "MUST")

    if fmt == OutputFormat.json:
        data = {
            "tool": tool_name,
            "passed": passed,
            "total": total,
            "compliant": all_must_pass,
            "results": results,
        }
        emit(success_envelope("validate", data, version="0.1.0"), fmt)
    else:
        for r in results:
            status = "PASS" if r["pass"] else "FAIL"
            sys.stdout.write(f"  [{status}] {r['level']:6s} {r['check']} ({r['spec']})\n")
        sys.stdout.write(f"\n{passed}/{total} checks passed")
        if all_must_pass:
            sys.stdout.write(" — ACLI compliant\n")
        else:
            sys.stdout.write(" — NOT compliant (MUST requirements failed)\n")

    if not all_must_pass:
        raise SystemExit(8)


def main() -> None:
    """Entry point for the acli CLI."""
    app.run()
