# Error Design

## Actionability requirement

Every error message **MUST** be actionable. The test: *can an agent read the error and know exactly what to do next without any external context?*

### Forbidden patterns

- `"Error: invalid input"` — no specifics
- `"Something went wrong"` — not actionable
- `"See documentation"` — no link provided

## Syntax error feedback

When an agent provides incorrect syntax, the error **MUST**:

1. State exactly what was wrong
2. Suggest the correct form
3. Point to a runnable example
4. Include the relevant `--help` pointer

### Example

```
Error [INVALID_ARGS]: Unknown flag '--pipline'
  Did you mean: --pipeline?

  Usage: noether run --pipeline <path> [--env <name>]

  Example:
    noether run --pipeline ./sprint.yaml --env staging

  See full usage: noether run --help
  Reference:      .cli/examples/run.sh
```

## JSON error format

When `--output json` is active, errors use the standard envelope:

```json
{
  "ok": false,
  "command": "run",
  "error": {
    "code": "INVALID_ARGS",
    "message": "Unknown flag '--pipline'",
    "hint": "Did you mean: --pipeline? Run `noether run --help`",
    "docs": ".cli/examples/run.sh"
  },
  "meta": {
    "duration_ms": 3,
    "version": "1.2.0"
  }
}
```

The `code` field maps directly to the [semantic exit codes](exit-codes.md), enabling programmatic error handling.
