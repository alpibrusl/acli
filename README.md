# ACLI — Agent-friendly CLI

**Build CLI tools that AI agents can discover, learn, and use autonomously.**

ACLI is a specification and SDK for designing CLI tools that agents can bootstrap at runtime — without MCP servers, external schemas, or hand-written `SKILL.md` files.

```
MCP           → schema defined externally, injected at agent startup
SKILL.md      → authored instructions (agentskills.io open standard)
<cli> --help  → tool teaches itself to the agent on demand    ← ACLI
```

## Why ACLI?

| Property | MCP | SKILL.md | ACLI |
|----------|-----|-----------|------|
| Who maintains the schema? | Humans (external) | Humans (external) | The tool itself |
| Discovery | All at once (startup) | All at once (startup) | Incremental (on demand) |
| Output format | Structured (JSON) | Unstructured (prose) | Structured (JSON envelope) |
| Staleness risk | High (registry drift) | High (manual docs) | Low for `introspect` (generated); medium for `acli skill` output (static artefact, goes stale if regenerated and not committed) |
| Infrastructure needed | MCP server/registry | File in repo | Nothing — just the CLI |

Read the full comparison: [Why ACLI? MCP → Skills → CLI](https://alpibrusl.github.io/acli/spec/evolution/)

## Quick start

```bash
pip install acli-spec
```

```python
from acli import ACLIApp, OutputFormat, acli_command, emit, success_envelope
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
) -> None:
    """Get current weather for a city."""
    data = {"city": city, "temperature_c": 18.5, "condition": "sunny"}
    emit(success_envelope("get", data, version="1.0.0"), OutputFormat.text)

if __name__ == "__main__":
    app.run()
```

Note: `--output` is **auto-injected** — no need to declare it. `--dry-run` is also auto-injected on non-idempotent commands.

You automatically get:

- `weather introspect` — full command tree as JSON
- `weather skill` — auto-generated `SKILL.md` ([agentskills.io](https://agentskills.io)) for agent bootstrapping
- `weather version` — semver output with `--output json`
- `.cli/` folder with README, examples, and schemas
- JSON error envelopes with actionable hints and semantic exit codes (0–9)
- NDJSON streaming via `emit_progress()` / `emit_result()` for long-running commands

See the full [weather example](https://alpibrusl.github.io/acli/example/) for a complete walkthrough.

## The `acli` CLI

```bash
acli validate --bin weather         # Validate against the spec
acli validate --bin weather --deep  # Deep validation (runs tool, checks envelopes)
acli skill --bin weather            # Generate SKILL.md from the tool
acli init --name myapp              # Scaffold a new ACLI project
```

## Specification

The full spec is in [`ACLI_SPEC.md`](ACLI_SPEC.md). Key concepts:

- **Progressive Discovery** — `--help` → `introspect` → `.cli/` folder
- **Output contracts** — `--output json|text|table` with standard envelope `{ok, command, data|error, meta}`
- **Semantic exit codes** — 0 success, 2 invalid args, 3 not found, 5 conflict, 9 dry-run
- **Dry-run** — `--dry-run` on all state-modifying commands
- **Idempotency** — each command declares `true|false|conditional`
- **Skill files** — auto-generated `SKILL.md` ([agentskills.io](https://agentskills.io)) bridging cold-start gap

### Stability policy

The spec is **v0.1.0 (Draft)**. Until 1.0:

- No breaking changes to the envelope shape, exit codes, or required
  `introspect` fields. Safe to build against.
- Additive changes (new optional fields, new commands) may land on minor
  bumps. Consumers should ignore unknown fields.
- Breaking changes, if they become necessary, will ship as `v0.2.0` with
  a clear migration note — not silently.

There is not yet a conformance test suite. "ACLI-compliant" today means
"envelope and exit codes match the spec on manual inspection". A small
conformance runner is tracked in [issue #22](https://github.com/alpibrusl/acli/issues/22).

## SDKs

Seven SDKs are in the monorepo at different maturity levels. Python / Rust /
TypeScript are first-party — the spec author tests changes against them
first and keeps them in sync on each spec bump. The rest are
community-maintained and may lag.

| Language | Support | LOC (src+tests) | Package / source |
|----------|---------|-----------------|------------------|
| Python | **First-party** | ~3.4k | [`acli-spec`](https://pypi.org/project/acli-spec/) (Typer) |
| Rust | **First-party** | ~1.9k | [`acli`](https://crates.io/crates/acli) (clap) |
| TypeScript | **First-party** | ~1.2k | [`@acli/sdk`](https://www.npmjs.com/package/@acli/sdk) (Commander) |
| Go | Community | ~0.8k | [`sdks/go`](sdks/go) — module `github.com/alpibrusl/acli-go` |
| .NET | Community | ~0.7k | [`sdks/dotnet`](sdks/dotnet) — `Acli.Spec` |
| R | Community | ~0.3k | [`sdks/r`](sdks/r) — package `acli.spec` |
| Java | Community | ~1.2k | [`sdks/java`](sdks/java) — Maven `dev.acli:acli-spec` (build from source) |

*Community* means: bug reports accepted, PRs welcome, but no guarantee
the SDK tracks the current spec. File a GitHub issue if you depend on
one and it's drifted.

Overview and links: **[Documentation — SDKs](https://alpibrusl.github.io/acli/sdks/)**

## Documentation

**[alpibrusl.github.io/acli](https://alpibrusl.github.io/acli)**

## See also

The concept of agents discovering tools at runtime has emerged independently in several projects, notably as [Progressive Skills](https://googlecloudplatform.github.io/scion/philosophy/) in Scion (Google Cloud Platform).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, quality checks, and PR process.

## Project status

**One active maintainer, best-effort response times.** Spec is v0.1.0 Draft with a no-breaking-changes-until-1.0 policy (see *Stability policy* in the Specification section). First-party SDKs (Python, Rust, TypeScript) track every spec change; community SDKs may lag. Not suitable for deployments requiring vendor SLAs.

## License

[EUPL-1.2](LICENSE)
