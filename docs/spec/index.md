# ACLI Specification

> Version 0.1.0 · Draft

The ACLI specification defines how CLI tools should be designed so that AI agents can discover, learn, and use them autonomously at runtime.

## Sections

| Section | What it covers |
|---------|---------------|
| [Why ACLI? MCP → Skills → CLI](evolution.md) | How agent tool integration evolved and where ACLI fits |
| [Progressive Discovery](discovery.md) | `--help` structure, `introspect` command, `.cli/` folder |
| [Output Contracts](output.md) | `--output` flag, JSON envelope, streaming |
| [Exit Codes](exit-codes.md) | Semantic exit codes 0–9 |
| [Error Design](errors.md) | Actionable errors, typo suggestions |
| [Dry-run & Idempotency](dry-run.md) | `--dry-run` mode, idempotency declaration |
| [Compliance Checklist](compliance.md) | Full requirements table |

## Evolution of agent tool integration

```
MCP           → schema defined externally, injected at agent startup
SKILL.md      → authored instructions (agentskills.io open standard)
<cli> --help  → tool teaches itself to the agent on demand (Progressive Skills)
```

ACLI targets the third stage — tools that are self-describing enough for agents to use without prior configuration. See the [full comparison](evolution.md) for a deep dive into the trade-offs between each approach.
