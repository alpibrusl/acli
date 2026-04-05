# ACLI — Agent-friendly CLI

**Build CLI tools that AI agents can discover, learn, and use autonomously.**

ACLI is a lightweight specification for designing CLI tools that agents can bootstrap at runtime — without pre-loaded schemas or external tool registries. The core insight: a well-designed CLI is self-documenting enough that an agent can learn it on demand by running `<tool> --help`.

## How it works

```
MCP           → schema defined externally, injected at agent startup
SKILLS.md     → instructions written by humans, loaded into context
<cli> --help  → tool teaches itself to the agent on demand
```

ACLI formalises what "well-designed" means in an agentic context, targeting the third stage.

## Key principles

1. **Progressive Discovery** — learn the full capability surface incrementally, starting from `--help`
2. **Machine-readable by default** — structured output (JSON) is a first-class citizen
3. **Fail informatively** — errors teach, not just reject
4. **Safe exploration** — reason about actions before committing via `--dry-run`
5. **Consistent contracts** — exit codes, output formats, and error shapes are predictable

## Quick start

### Install the Python SDK

```bash
pip install acli-spec
```

### Build your first ACLI tool

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
    output: OutputFormat = typer.Option(OutputFormat.text),
) -> None:
    """Execute a task from a YAML file."""
    ...

if __name__ == "__main__":
    app.run()
```

You automatically get:

- `myapp introspect` — full command tree as JSON
- `myapp version` — semver output with `--output json` support
- `.cli/` folder with README, examples, and schemas
- JSON error envelopes with actionable hints
- Semantic exit codes (0–9)

## SDKs

| Language | Status | Package |
|----------|--------|---------|
| Python   | ✅ Available | `pip install acli-spec` |
| Go       | 🔜 Planned  | — |
| Rust     | 🔜 Planned  | — |
| Node.js  | 🔜 Planned  | — |

## License

[EUPL-1.2](https://github.com/alpibrusl/acli/blob/main/LICENSE)
