# Errors

## Error hierarchy

All ACLI errors extend `ACLIError`, which maps to a semantic exit code:

```python
from acli import ACLIError, InvalidArgsError, NotFoundError, ConflictError, PreconditionError

raise InvalidArgsError(
    "Missing required argument: --pipeline",
    hint="Run `noether run --help` to see usage",
    docs=".cli/examples/run.sh",
)
```

| Error class | Exit code | When to use |
|-------------|-----------|-------------|
| `ACLIError` | `GENERAL_ERROR` (1) | Base class, generic errors |
| `InvalidArgsError` | `INVALID_ARGS` (2) | Wrong arguments or flags |
| `NotFoundError` | `NOT_FOUND` (3) | Resource doesn't exist |
| `ConflictError` | `CONFLICT` (5) | State conflict (already exists, locked) |
| `PreconditionError` | `PRECONDITION_FAILED` (8) | Required state not met |

### Common fields

All error classes accept:

| Field | Type | Description |
|-------|------|-------------|
| `message` | `str` | What went wrong (positional) |
| `hint` | `str \| None` | How to fix it |
| `docs` | `str \| None` | Reference to example or docs |

## Automatic error handling

When using `ACLIApp.run()`, errors are automatically caught and converted to JSON error envelopes:

```python
app = ACLIApp(name="mytool", version="1.0.0")

@app.command()
def do_thing() -> None:
    raise InvalidArgsError("Missing --file", hint="Provide a YAML file path")

# Output:
# {"ok": false, "error": {"code": "INVALID_ARGS", "message": "Missing --file", "hint": "..."}, ...}
# Exit code: 2
```

## Flag suggestions

Use `suggest_flag` to provide typo corrections per spec §4.1:

```python
from acli import suggest_flag

suggestion = suggest_flag("--pipline", ["--pipeline", "--env", "--dry-run"])
# Returns: "--pipeline"

suggestion = suggest_flag("--zzz", ["--pipeline", "--env"])
# Returns: None
```

## ExitCode enum

```python
from acli import ExitCode

ExitCode.SUCCESS            # 0
ExitCode.GENERAL_ERROR      # 1
ExitCode.INVALID_ARGS       # 2
ExitCode.NOT_FOUND          # 3
ExitCode.PERMISSION_DENIED  # 4
ExitCode.CONFLICT           # 5
ExitCode.TIMEOUT            # 6
ExitCode.UPSTREAM_ERROR     # 7
ExitCode.PRECONDITION_FAILED # 8
ExitCode.DRY_RUN            # 9
```
