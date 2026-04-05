# Dry-run & Idempotency

## Dry-run mode

Every command that **modifies state** MUST support:

```
--dry-run    bool    Describe what would happen without executing    [default: false]
```

### Dry-run output requirements

- Describe each action that would be taken
- Include the exact parameters that would be used
- Emit exit code `9` (`DRY_RUN`)
- Respect `--output json`

### Example output

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

The `reversible` field helps agents assess risk before confirming execution.

## Idempotency

Commands **MUST** declare their idempotency in `--help` and in `commands.json`:

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
| `"conditional"` | Idempotent if `--force` is not passed |

Agents use this to determine whether to retry on ambiguous failure — an idempotent command can be safely retried, while a non-idempotent one requires confirmation.
