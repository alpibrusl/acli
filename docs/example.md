---
title: "Example: ACLI Weather CLI for AI Agents"
description: Complete example of an ACLI-compliant weather CLI showing introspection, JSON envelopes, error handling, dry-run, and auto-generated skill files.
---

# Example: Weather CLI

A complete ACLI-compliant weather tool that demonstrates every spec feature. This is the classic "weather" example used in AI agent demos — rebuilt to show how ACLI makes CLI tools agent-friendly.

The full source is at [`examples/weather/weather.py`](https://github.com/alpibrusl/acli/blob/main/examples/weather/weather.py).

## The tool

```python
from acli import ACLIApp, acli_command, OutputFormat, NotFoundError
from acli import emit, success_envelope
import typer

app = ACLIApp(name="weather", version="1.0.0")

@app.command()
@acli_command(
    examples=[
        ("Get weather for London", "weather get --city london"),
        ("Get weather for Tokyo in JSON", "weather get --city tokyo --output json"),
    ],
    idempotent=True,
    see_also=["forecast", "alerts"],
)
def get(
    city: str = typer.Option(..., help="City name (lowercase, hyphenated). type:string"),
    units: str = typer.Option("metric", help="Unit system. type:enum[metric|imperial]"),
    output: OutputFormat = typer.Option(OutputFormat.text),
) -> None:
    """Get current weather for a city."""
    if city not in CITIES:
        raise NotFoundError(
            f"Unknown city: '{city}'",
            hint=f"Available cities: {', '.join(sorted(CITIES))}",
            docs=".cli/examples/get.sh",
        )
    data = get_weather(city)
    emit(success_envelope("get", data, version="1.0.0"), output)
```

The tool also has `forecast`, `alerts`, and `favorite` commands — see the [full source](https://github.com/alpibrusl/acli/blob/main/examples/weather/weather.py).

## What an agent sees

### Step 1: Discovery via `--help`

An agent encountering this tool for the first time runs:

```
$ weather --help
```

It learns the available commands: `get`, `forecast`, `alerts`, `favorite`, plus built-in `introspect`, `version`, and `skill`.

### Step 2: Machine-readable introspection

For structured discovery, the agent runs:

```
$ weather introspect --output json
```

```json
{
  "ok": true,
  "command": "introspect",
  "data": {
    "name": "weather",
    "version": "1.0.0",
    "acli_version": "0.1.0",
    "commands": [
      {
        "name": "get",
        "description": "Get current weather for a city.",
        "options": [
          {"name": "city", "type": "string", "description": "City name (lowercase, hyphenated). type:string"},
          {"name": "units", "type": "string", "description": "Unit system. type:enum[metric|imperial]", "default": "metric"},
          {"name": "output", "type": "OutputFormat", "description": "Output format. type:enum[text|json|table]", "default": "text"}
        ],
        "idempotent": true,
        "examples": [
          {"description": "Get weather for London", "invocation": "weather get --city london"},
          {"description": "Get weather for Tokyo in JSON", "invocation": "weather get --city tokyo --output json"}
        ],
        "see_also": ["forecast", "alerts"]
      }
    ]
  }
}
```

### Step 3: Using the tool

**Successful request:**

```
$ weather get --city london --output json
```

```json
{
  "ok": true,
  "command": "get",
  "data": {
    "city": "london",
    "country": "GB",
    "temperature_c": 27.4,
    "humidity_pct": 68,
    "wind_kph": 3.3,
    "condition": "cloudy",
    "coordinates": {"lat": 51.5, "lon": -0.1}
  },
  "meta": {"duration_ms": 0, "version": "1.0.0"}
}
```

**Error with actionable hint (exit code 3):**

```
$ weather get --city mars --output json
```

```json
{
  "ok": false,
  "command": "weather",
  "error": {
    "code": "NOT_FOUND",
    "message": "Unknown city: 'mars'",
    "hint": "Available cities: london, new-york, paris, sydney, tokyo",
    "docs": ".cli/examples/get.sh"
  },
  "meta": {"duration_ms": 0, "version": "1.0.0"}
}
```

The agent reads exit code `3` (NOT_FOUND), knows to check inputs, and sees the hint listing valid cities. No guesswork needed.

**Dry-run mode (exit code 9):**

```
$ weather favorite --city paris --dry-run --output json
```

```json
{
  "ok": true,
  "command": "favorite",
  "dry_run": true,
  "planned_actions": [
    {
      "action": "add_favorite",
      "target": "paris",
      "reversible": true,
      "already_exists": false
    }
  ],
  "meta": {"duration_ms": 0, "version": "1.0.0"}
}
```

The agent can review the planned action and decide whether to proceed without `--dry-run`.

**NDJSON streaming for long-running operations:**

```
$ weather refresh --cities london,paris,tokyo
```

```
{"type":"progress","step":"refresh","status":"running","detail":"Fetching data for london"}
{"type":"progress","step":"refresh","status":"running","detail":"Fetching data for paris"}
{"type":"progress","step":"refresh","status":"running","detail":"Fetching data for tokyo"}
{"type":"result","ok":true,"cities_refreshed":["london","paris","tokyo"],"count":3}
```

The agent can parse each line as it arrives, tracking progress in real time. Note that `refresh` has `idempotent=False`, so `--dry-run` and `--output` were **auto-injected** by `@acli_command` — no need to declare them.

**Deep validation:**

```
$ acli validate --bin weather --deep
  ...
  [PASS] MUST   top-level --help runs successfully (§1.1)
  [PASS] MUST   get: JSON error envelope on bad input (§2.2)
  [PASS] MUST   version --output json returns valid envelope (§7.1)
```

The `--deep` flag actually runs the tool and verifies that JSON envelopes are correctly formed.

## Generated skill file

Running `weather skill` auto-generates a SKILLS.md that gives agents immediate context:

```
$ weather skill
```

```markdown
# weather

> Auto-generated skill file for `weather` v1.0.0
> Re-generate with: `weather skill` or `acli skill --bin weather`

## Available commands

- `weather get` — Get current weather for a city. (idempotent)
- `weather forecast` — Get multi-day weather forecast for a city. (idempotent)
- `weather alerts` — List active weather alerts. (idempotent)
- `weather favorite` — Add a city to your favorites list. (conditionally idempotent)

## `weather get`

Get current weather for a city.

### Options

- `--city` (string) — City name (lowercase, hyphenated). type:string
- `--units` (string) — Unit system. type:enum[metric|imperial] [default: metric]
- `--output` (OutputFormat) — Output format. type:enum[text|json|table] [default: text]

### Examples

​```bash
# Get weather for London
weather get --city london
​```

​```bash
# Get weather for Tokyo in JSON
weather get --city tokyo --output json
​```

**See also:** `weather forecast`, `weather alerts`
```

This file can be committed to the repo, loaded into an agent's context, or served alongside the tool. Because it's generated from the tool itself, it's never stale.

## Validation

```
$ acli validate --bin weather
  [PASS] MUST   introspect command exists (§1.2)
  [PASS] MUST   version command exists (§7.1)
  [PASS] MUST   get: at least 2 examples (§1.1)
  [PASS] MUST   get: --city has type annotation (§1.1)
  [PASS] MUST   get: --units has type annotation (§1.1)
  [PASS] MUST   get: --output has type annotation (§1.1)
  [PASS] SHOULD get: idempotency declared (§6)
  ...
  [PASS] SHOULD favorite: idempotency declared (§6)

19/19 checks passed — ACLI compliant
```

## How an agent uses this

Here's the complete agent interaction pattern:

```
1. Agent reads SKILLS.md           → immediate context (commands, options, examples)
2. Agent runs: weather get ...     → structured JSON response, predictable exit codes
3. On error: agent reads hint      → knows exactly what to fix
4. On unknown command: --help      → deeper discovery on demand
5. For full mapping: introspect    → machine-readable command tree
6. After context reset: .cli/      → persistent orientation
```

No MCP server. No external schema. No human-maintained docs. The tool teaches itself to the agent.
