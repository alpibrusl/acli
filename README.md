# ACLI — Agent-friendly CLI

**Build CLI tools that AI agents can discover, learn, and use autonomously.**

ACLI is a specification and SDK for designing CLI tools that agents can bootstrap at runtime — without MCP servers, external schemas, or hand-written SKILLS.md files.

```
MCP           → schema defined externally, injected at agent startup
SKILLS.md     → instructions written by humans, loaded into context
<cli> --help  → tool teaches itself to the agent on demand    ← ACLI
```

## Why ACLI?

| Property | MCP | SKILLS.md | ACLI |
|----------|-----|-----------|------|
| Who maintains the schema? | Humans (external) | Humans (external) | The tool itself |
| Discovery | All at once (startup) | All at once (startup) | Incremental (on demand) |
| Output format | Structured (JSON) | Unstructured (prose) | Structured (JSON envelope) |
| Staleness risk | High (registry drift) | High (manual docs) | None (generated from code) |
| Infrastructure needed | MCP server/registry | File in repo | Nothing — just the CLI |

Read the full comparison: [Why ACLI? MCP → Skills → CLI](https://alpibrusl.github.io/acli/spec/evolution/)

## Quick start

```bash
pip install acli-spec
```

```python
from acli import ACLIApp, acli_command, OutputFormat
import typer

app = ACLIApp(name="weather", version="1.0.0")

@app.command()
@acli_command(
    examples=[
        ("Get weather for London", "weather get --city london"),
        ("Get weather in JSON", "weather get --city london --output json"),
    ],
    idempotent=True,
)
def get(
    city: str = typer.Option(..., help="City name. type:string"),
    output: OutputFormat = typer.Option(OutputFormat.text),
) -> None:
    """Get current weather for a city."""
    from acli import emit, success_envelope
    data = {"city": city, "temperature_c": 18.5, "condition": "sunny"}
    emit(success_envelope("get", data, version="1.0.0"), output)

if __name__ == "__main__":
    app.run()
```

You automatically get:

- `weather introspect` — full command tree as JSON
- `weather skill` — auto-generated SKILLS.md for agent bootstrapping
- `weather version` — semver output with `--output json`
- `.cli/` folder with README, examples, and schemas
- JSON error envelopes with actionable hints and semantic exit codes (0–9)

See the full [weather example](https://alpibrusl.github.io/acli/example/) for a complete walkthrough.

## The `acli` CLI

```bash
acli validate --bin weather     # Validate against the spec
acli skill --bin weather        # Generate SKILLS.md from the tool
acli init --name myapp          # Scaffold a new ACLI project
```

## Specification

The full spec is in [`ACLI_SPEC.md`](ACLI_SPEC.md). Key concepts:

- **Progressive Discovery** — `--help` → `introspect` → `.cli/` folder
- **Output contracts** — `--output json|text|table` with standard envelope `{ok, command, data|error, meta}`
- **Semantic exit codes** — 0 success, 2 invalid args, 3 not found, 5 conflict, 9 dry-run
- **Dry-run** — `--dry-run` on all state-modifying commands
- **Idempotency** — each command declares `true|false|conditional`
- **Skill files** — auto-generated SKILLS.md bridging cold-start gap

## SDKs

| Language | Status | Package |
|----------|--------|---------|
| Python   | Available | [`acli-spec`](https://pypi.org/project/acli-spec/) |
| Go       | Planned  | — |
| Rust     | Planned  | — |
| Node.js  | Planned  | — |

## Documentation

**[alpibrusl.github.io/acli](https://alpibrusl.github.io/acli)**

## See also

The concept of agents discovering tools at runtime has emerged independently in several projects, notably as [Progressive Skills](https://googlecloudplatform.github.io/scion/philosophy/) in Scion (Google Cloud Platform).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, quality checks, and PR process.

## License

[EUPL-1.2](LICENSE)
