---
title: ACLI Python SDK — Getting Started
description: Build agent-friendly CLI tools in Python with the acli-spec package. Wraps Typer with automatic introspection, JSON envelopes, and semantic exit codes.
---

# Python SDK — Getting Started

The `acli-spec` package wraps [Typer](https://typer.tiangolo.com/) to automatically enforce the ACLI specification.

## Installation

```bash
pip install acli-spec
```

For development:

```bash
git clone https://github.com/alpibrusl/acli.git
cd acli/sdks/python
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Minimal example

```python
from pathlib import Path
from acli import ACLIApp, acli_command, OutputFormat
import typer

app = ACLIApp(name="noether", version="1.0.0")

@app.command()
@acli_command(
    examples=[
        ("Run a pipeline in staging", "noether run --pipeline ./sprint.yaml --env staging"),
        ("Dry-run a pipeline", "noether run --pipeline ./sprint.yaml --dry-run"),
    ],
    idempotent=False,
)
def run(
    pipeline: Path = typer.Option(..., help="Path to Lagrange YAML pipeline file. type:path"),
    env: str = typer.Option("dev", help="Target environment. type:enum[dev|staging|prod]"),
    dry_run: bool = typer.Option(False, help="Describe actions without executing."),
    output: OutputFormat = typer.Option(OutputFormat.text),
) -> None:
    """Execute a pipeline from a Lagrange YAML file."""
    from acli import emit, success_envelope

    data = {"pipeline": str(pipeline), "env": env, "status": "completed"}
    emit(success_envelope("run", data, version="1.0.0"), output)

if __name__ == "__main__":
    app.run()
```

## What you get automatically

When you create an `ACLIApp`, the SDK automatically:

- Registers an `introspect` command that outputs the full command tree as JSON
- Registers a `version` command with `--output json` support
- Generates and maintains the `.cli/` folder on introspect/version calls
- Catches `ACLIError` exceptions and emits JSON error envelopes
- Catches unexpected exceptions with a generic error envelope

## Running checks

```bash
ruff check src/ tests/          # Lint
ruff format --check src/ tests/ # Format check
mypy src/                       # Type check
pytest                          # Tests (90% coverage minimum)
```
