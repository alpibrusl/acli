# Exit Codes

ACLI tools **MUST** use semantic exit codes. Generic `0`/`1` is not sufficient for agentic retry logic.

## Standard exit codes

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

## Tool-specific codes

Exit codes `10–63` are reserved for tool-specific codes, which **MUST** be documented in `.cli/README.md`.

## Why this matters

Agents use exit codes to decide their next action without parsing error messages. A `TIMEOUT` (6) triggers a retry with backoff, while `INVALID_ARGS` (2) triggers argument correction. This structured feedback loop enables autonomous recovery.
