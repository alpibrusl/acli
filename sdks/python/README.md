# acli-spec

Python SDK for the [ACLI (Agent-friendly CLI) specification](../../ACLI_SPEC.md).

Build CLI tools that AI agents can discover, learn, and use autonomously.

## Installation

```bash
pip install acli-spec
```

## Quick Start

```python
from pathlib import Path
from acli import ACLIApp, acli_command, OutputFormat
import typer

app = ACLIApp(name="myapp", version="1.0.0")

@app.command()
@acli_command(
    examples=[
        ("Run a task", "myapp run --file task.yaml"),
        ("Dry-run a task", "myapp run --file task.yaml --dry-run"),
    ],
    idempotent=False,
)
def run(
    file: Path = typer.Option(..., help="Path to task file. type:path"),
    dry_run: bool = typer.Option(False, help="Preview without executing."),
    output: OutputFormat = typer.Option(OutputFormat.text, help="Output format."),
) -> None:
    """Execute a task from a YAML file."""
    ...

if __name__ == "__main__":
    app.run()
```

## What you get automatically

- `introspect` command with full command tree as JSON
- `.cli/` folder generation (README, examples, schemas)
- JSON error envelope on `--output json`
- Semantic exit codes (0-9)
- `--version` with semver output

## License

[EUPL-1.2](../../LICENSE)
