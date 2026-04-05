# ACLI — Agent-friendly CLI Specification
> Version 0.1.0 · Draft

## Overview

ACLI is a lightweight specification for designing CLI tools that agents can discover, learn, and use autonomously — without pre-loaded schemas or external tool registries.

The core insight: a well-designed CLI is self-documenting enough that an agent can bootstrap its own understanding at runtime by running `<tool> --help`. ACLI formalises what "well-designed" means in an agentic context.

### Evolution of agent tool integration

```
MCP           → schema defined externally, injected at agent startup
SKILLS.md     → instructions written by humans, loaded into context
<cli> --help  → tool teaches itself to the agent on demand (Progressive Skills)
```

ACLI targets the third stage.

---

## Principles

1. **Progressive Discovery** — an agent should be able to learn the full capability surface of a tool incrementally, starting from `--help`.
2. **Machine-readable by default** — structured output (JSON) must be a first-class citizen, not an afterthought.
3. **Fail informatively** — errors must teach, not just reject.
4. **Safe exploration** — agents must be able to reason about actions before committing.
5. **Consistent contracts** — exit codes, output formats, and error shapes must be predictable across all commands.

---

## 1. Progressive Discovery

### 1.1 `--help` structure

Every command and subcommand MUST expose `--help` with the following sections, in order:

```
<one-line description>

USAGE:
  <tool> <command> [OPTIONS] [ARGS]

DESCRIPTION:
  <2–5 line explanation of what this command does and when to use it>

ARGUMENTS:
  <name>    <type>    <required|optional>    <description>

OPTIONS:
  --option    <type>    <description>    [default: <value>]

EXAMPLES:
  # <intent description>
  <tool> <command> <concrete invocation>

  # <second example with different case>
  <tool> <command> <concrete invocation>

SEE ALSO:
  <related subcommand>, <related subcommand>
```

**Rules:**
- Descriptions must be written for an agent that has no prior context.
- Every argument and option must have a type annotation (`string`, `int`, `bool`, `enum[a|b|c]`, `path`).
- At least **two examples** per command. Examples must be concrete (no `<placeholder>` in the actual invocation).
- `SEE ALSO` must list related commands by name.

### 1.2 Introspection command

Every ACLI tool MUST expose a top-level introspection command:

```bash
<tool> introspect
```

This command outputs the full command tree as JSON:

```json
{
  "name": "noether",
  "version": "1.2.0",
  "acli_version": "0.1.0",
  "commands": [
    {
      "name": "run",
      "description": "Execute a pipeline from a Lagrange YAML file",
      "arguments": [...],
      "options": [...],
      "subcommands": []
    }
  ]
}
```

This is the machine-readable complement to `--help`. Agents should prefer `introspect` for initial capability mapping and `--help` for contextual guidance on a specific command.

### 1.3 `.cli/` reference folder

Every ACLI tool MUST write a `.cli/` folder at the root of the working directory (or project root) containing:

```
.cli/
  README.md          # human-readable overview of the tool
  commands.json      # same output as `<tool> introspect`
  examples/
    <command>.sh     # runnable example scripts per command
  schemas/
    <type>.json      # JSON schemas for complex input/output types
  changelog.md       # recent changes agents should be aware of
```

The `.cli/` folder is the **persistent knowledge base** for agents. It allows an agent to orient itself without executing the tool, and survives context resets. Agents should check `.cli/README.md` first before any other discovery step.

**`.cli/` update rules:**
- Updated automatically on `<tool> --version` or `<tool> introspect`
- Never requires elevated permissions to write
- Safe to commit to version control

---

## 2. Output Contracts

### 2.1 Format flag

Every command that produces output MUST support:

```
--output <format>    enum[text|json|table]    Output format    [default: text]
```

**Behaviour by format:**

| Format | Use case | Rules |
|--------|----------|-------|
| `text` | Human reading | Coloured, formatted, may use unicode |
| `json` | Agent consumption | Strict JSON, no decorations, to stdout |
| `table` | Tabular data | ASCII-safe, parseable by column |

**Critical:** `--output json` MUST apply to **both success and error responses**. An agent that passes `--output json` must never receive unstructured text on stderr.

### 2.2 JSON output envelope

All JSON output MUST follow this envelope:

```json
{
  "ok": true,
  "command": "run",
  "data": { ... },
  "meta": {
    "duration_ms": 142,
    "version": "1.2.0"
  }
}
```

Error envelope:

```json
{
  "ok": false,
  "command": "run",
  "error": {
    "code": "INVALID_ARGS",
    "message": "Missing required argument: --pipeline",
    "hint": "Run `noether run --help` to see usage",
    "docs": ".cli/examples/run.sh"
  },
  "meta": {
    "duration_ms": 3,
    "version": "1.2.0"
  }
}
```

### 2.3 Streaming output

For long-running commands, JSON streaming MUST use newline-delimited JSON (NDJSON):

```
{"type":"progress","step":"validate","status":"ok"}
{"type":"progress","step":"execute","status":"running"}
{"type":"result","ok":true,"data":{...}}
```

---

## 3. Exit Codes

ACLI tools MUST use the following exit code schema. Generic `0`/`1` is not sufficient for agentic retry logic.

| Code | Name | Meaning | Agent action |
|------|------|---------|--------------|
| `0` | `SUCCESS` | Command completed successfully | Proceed |
| `1` | `GENERAL_ERROR` | Unclassified error | Inspect stderr |
| `2` | `INVALID_ARGS` | Wrong arguments or flags | Correct and retry |
| `3` | `NOT_FOUND` | Resource does not exist | Check inputs |
| `4` | `PERMISSION_DENIED` | Insufficient permissions | Escalate or skip |
| `5` | `CONFLICT` | State conflict (already exists, locked) | Resolve conflict |
| `6` | `TIMEOUT` | Operation timed out | Retry with backoff |
| `7` | `UPSTREAM_ERROR` | External dependency failed | Retry or skip |
| `8` | `PRECONDITION_FAILED` | Required state not met | Fix precondition first |
| `9` | `DRY_RUN` | Dry-run completed, no changes made | Review and confirm |

Exit codes `10–63` are reserved for tool-specific codes, which MUST be documented in `.cli/README.md`.

---

## 4. Error Design

### 4.1 Syntax error feedback

When an agent provides incorrect syntax, the error MUST:

1. State exactly what was wrong (`"Unknown flag: --pipline"`)
2. Suggest the correct form (`"Did you mean: --pipeline?"`)
3. Point to a runnable example (`"See: .cli/examples/run.sh"`)
4. Include the relevant `--help` pointer (`"Run: noether run --help"`)

Example:

```
Error [INVALID_ARGS]: Unknown flag '--pipline'
  Did you mean: --pipeline?
  
  Usage: noether run --pipeline <path> [--env <name>]
  
  Example:
    noether run --pipeline ./sprint.yaml --env staging
  
  See full usage: noether run --help
  Reference:      .cli/examples/run.sh
```

### 4.2 Actionability requirement

Every error message MUST be **actionable**. The test: can an agent read the error and know exactly what to do next without any external context?

Forbidden error patterns:
- `"Error: invalid input"` — no specifics
- `"Something went wrong"` — not actionable
- `"See documentation"` — no link provided

---

## 5. Dry-run Mode

Every command that **modifies state** MUST support:

```
--dry-run    bool    Describe what would happen without executing    [default: false]
```

Dry-run output MUST:
- Describe each action that would be taken
- Include the exact parameters that would be used
- Emit exit code `9` (`DRY_RUN`)
- Respect `--output json`

Example dry-run JSON output:

```json
{
  "ok": true,
  "command": "deploy",
  "dry_run": true,
  "planned_actions": [
    { "action": "create_namespace", "target": "staging", "reversible": true },
    { "action": "apply_manifest", "target": "./k8s/deploy.yaml", "reversible": true }
  ],
  "meta": { "duration_ms": 12, "version": "1.2.0" }
}
```

---

## 6. Idempotency

Commands MUST declare their idempotency in `--help` and in `commands.json`:

```json
{
  "name": "apply",
  "idempotent": true,
  "description": "Apply configuration. Safe to run multiple times."
}
```

| Value | Meaning |
|-------|---------|
| `true` | Running N times produces same result as running once |
| `false` | Each run has side effects |
| `conditional` | Idempotent if `--force` is not passed |

Agents use this to determine whether to retry on ambiguous failure.

---

## 7. Versioning & Capability Detection

### 7.1 Version output

```bash
<tool> --version
```

MUST output semver-parseable format:

```
noether 1.2.0
acli 0.1.0
```

With `--output json`:

```json
{
  "tool": "noether",
  "version": "1.2.0",
  "acli_version": "0.1.0",
  "build": "2026-04-01T10:00:00Z"
}
```

### 7.2 Capability negotiation

Agents that depend on specific features MAY check:

```bash
<tool> introspect --acli-version
```

Returns the ACLI spec version the tool claims compliance with. Agents can use this to decide which interaction patterns to apply.

---

## 8. Implementation Guide (Python / Typer)

The reference implementation is the `acli` Python package, which wraps Typer to enforce this spec automatically.

```python
from acli import ACLIApp, acli_command, OutputFormat

app = ACLIApp(name="noether", version="1.2.0")

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
):
    """Execute a pipeline from a Lagrange YAML file.
    
    Loads the pipeline definition, validates all steps, resolves dependencies,
    and executes each agent task in DAG order. Use --dry-run to inspect the
    execution plan before committing.
    """
    ...
```

The `acli` package automatically:
- Generates `.cli/` folder on first run
- Enforces JSON error envelope when `--output json`
- Registers semantic exit codes
- Adds `introspect` command to every app
- Validates `--help` completeness at startup (dev mode)

---

## Compliance Checklist

Use `acli validate` to check compliance automatically.

| # | Requirement | Required |
|---|-------------|----------|
| 1 | `--help` includes USAGE, DESCRIPTION, ARGUMENTS, OPTIONS, EXAMPLES, SEE ALSO | MUST |
| 2 | Every argument has type annotation | MUST |
| 3 | At least 2 concrete examples per command | MUST |
| 4 | `introspect` command outputs full command tree as JSON | MUST |
| 5 | `.cli/` folder generated and kept up to date | MUST |
| 6 | `--output json\|text\|table` supported on all commands | MUST |
| 7 | JSON error envelope used when `--output json` | MUST |
| 8 | Semantic exit codes (0–9) used | MUST |
| 9 | Error messages include correction hint and example pointer | MUST |
| 10 | `--dry-run` on all state-modifying commands | MUST |
| 11 | `--version` outputs semver-parseable format | MUST |
| 12 | Idempotency declared per command | SHOULD |
| 13 | NDJSON streaming for long-running commands | SHOULD |
| 14 | `.cli/schemas/` contains JSON schemas for complex types | MAY |

---

## Roadmap

- **v0.2** — Multi-language ports (Rust/clap, Go/cobra, Node/oclif)
- **v0.3** — `acli validate` CI integration and GitHub Action
- **v0.4** — `.cli/` format stabilisation and registry proposal
- **v1.0** — Stable spec, reference implementations in 3+ languages

---

## Reference Implementation

- Python package: `pip install acli-spec`
- Source: [github.com/youorg/acli](https://github.com/youorg/acli)
- Docs: [acli.dev](https://acli.dev)

---

*ACLI is inspired by the Progressive Skills pattern observed in [Scion](https://googlecloudplatform.github.io/scion/philosophy/) (Google Cloud Platform) and motivated by practical experience building agent-native CLIs for multi-agent platforms.*
