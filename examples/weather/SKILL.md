---
name: weather
description: Invoke the `weather` CLI. Commands: get, forecast, alerts, favorite…
---

# weather

> Auto-generated skill file for `weather` v1.0.0
> Re-generate with: `weather skill` or `acli skill --bin weather`

## Available commands

- `weather get` — Get current weather for a city. (idempotent)
- `weather forecast` — Get multi-day weather forecast for a city. (idempotent)
- `weather alerts` — List active weather alerts. (idempotent)
- `weather favorite` — Add a city to your favorites list. (conditionally idempotent)
- `weather refresh` — Refresh cached weather data for cities.

## `weather get`

Get current weather for a city.

### Options

- `--city` (string) — City name (lowercase, hyphenated). type:string
- `--units` (string) — Unit system. type:enum[metric|imperial] [default: metric]
- `--output` (OutputFormat) — Output format. type:enum[text|json|table] [default: text]

### Examples

```bash
# Get weather for London
weather get --city london
```

```bash
# Get weather for Tokyo in JSON
weather get --city tokyo --output json
```

**See also:** `weather forecast`, `weather alerts`

## `weather forecast`

Get multi-day weather forecast for a city.

### Options

- `--city` (string) — City name (lowercase, hyphenated). type:string
- `--days` (int) — Number of forecast days (1-7). type:int [default: 3]
- `--output` (OutputFormat) — Output format. type:enum[text|json|table] [default: text]

### Examples

```bash
# Get 3-day forecast for Paris
weather forecast --city paris --days 3
```

```bash
# Get 7-day forecast in JSON
weather forecast --city london --days 7 --output json
```

**See also:** `weather get`, `weather alerts`

## `weather alerts`

List active weather alerts.

### Options

- `--city` (string) — Filter alerts by city (optional). type:string [default: ]
- `--output` (OutputFormat) — Output format. type:enum[text|json|table] [default: text]

### Examples

```bash
# Check all active alerts
weather alerts
```

```bash
# Check alerts for Tokyo
weather alerts --city tokyo
```

**See also:** `weather get`, `weather forecast`

## `weather favorite`

Add a city to your favorites list.

### Options

- `--city` (string) — City to add to favorites. type:string
- `--dry-run` (bool) — Preview without saving. type:bool [default: False]
- `--output` (OutputFormat) — Output format. type:enum[text|json|table] [default: text]

### Examples

```bash
# Add London to favorites
weather favorite --city london
```

```bash
# Dry-run adding Paris
weather favorite --city paris --dry-run
```

**See also:** `weather get`

## `weather refresh`

Refresh cached weather data for cities.

### Options

- `--cities` (string) — Comma-separated city names to refresh (default: all). type:string [default: ]
- `--output` (string) — Output format. type:enum[text|json|table] [default: text]
- `--dry-run` (string) — Describe actions without executing. type:bool [default: False]

### Examples

```bash
# Refresh all cities
weather refresh
```

```bash
# Refresh specific cities
weather refresh --cities london,paris
```

**See also:** `weather get`, `weather forecast`

## Output format

All commands support `--output json|text|table`. When using `--output json`, responses follow a standard envelope:

```json
{"ok": true, "command": "...", "data": {...}, "meta": {"duration_ms": ..., "version": "..."}}
```

Errors use the same envelope with `"ok": false` and an `"error"` object containing `code`, `message`, `hint`, and `docs`.

## Exit codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Proceed |
| 2 | Invalid arguments | Correct and retry |
| 3 | Not found | Check inputs |
| 5 | Conflict | Resolve conflict |
| 8 | Precondition failed | Fix precondition |
| 9 | Dry-run completed | Review and confirm |

## Further discovery

- `weather --help` — full help for any command
- `weather introspect` — machine-readable command tree (JSON)
- `.cli/README.md` — persistent reference (survives context resets)
