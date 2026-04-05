# Output & Envelopes

## OutputFormat

```python
from acli import OutputFormat

OutputFormat.text   # Human-readable, coloured
OutputFormat.json   # Strict JSON envelope
OutputFormat.table  # ASCII table
```

Use as a Typer option in your commands:

```python
output: OutputFormat = typer.Option(OutputFormat.text, help="Output format.")
```

## Building envelopes

### Success

```python
from acli import success_envelope

envelope = success_envelope(
    "run",                              # command name
    {"result": "ok", "items": 42},      # data payload
    version="1.0.0",
    start_time=start,                   # optional: for duration_ms calculation
)
# {"ok": true, "command": "run", "data": {...}, "meta": {"duration_ms": ..., "version": "1.0.0"}}
```

### Dry-run success

```python
envelope = success_envelope(
    "deploy",
    {},
    version="1.0.0",
    dry_run=True,
    planned_actions=[
        {"action": "create", "target": "staging", "reversible": True},
    ],
)
# {"ok": true, "command": "deploy", "dry_run": true, "planned_actions": [...], "meta": {...}}
```

When `dry_run=True`, the `data` key is omitted and `planned_actions` is used instead.

### Error

```python
from acli import error_envelope

envelope = error_envelope(
    "run",
    code="INVALID_ARGS",
    message="Missing required argument: --pipeline",
    hint="Run `noether run --help` to see usage",
    docs=".cli/examples/run.sh",
    version="1.0.0",
)
```

## Emitting output

```python
from acli import emit

emit(envelope, OutputFormat.json)   # JSON to stdout
emit(envelope, OutputFormat.text)   # Human-readable (errors go to stderr)
emit(envelope, OutputFormat.table)  # ASCII table
```

The `emit` function handles format-specific rendering:

- **JSON**: `json.dump` with 2-space indent to stdout
- **Text**: key-value pairs for success, formatted error block for errors (to stderr)
- **Table**: column-aligned ASCII table for list data, key-value for dicts
