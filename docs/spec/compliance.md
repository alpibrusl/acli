# Compliance Checklist

Use `acli validate` to check compliance automatically.

## Requirements

| # | Requirement | Level |
|---|-------------|-------|
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
