# Output Contracts

## Format flag

Every command that produces output **MUST** support:

```
--output <format>    enum[text|json|table]    Output format    [default: text]
```

### Behaviour by format

| Format | Use case | Rules |
|--------|----------|-------|
| `text` | Human reading | Coloured, formatted, may use unicode |
| `json` | Agent consumption | Strict JSON, no decorations, to stdout |
| `table` | Tabular data | ASCII-safe, parseable by column |

!!! warning "Critical"
    `--output json` **MUST** apply to both success and error responses. An agent that passes `--output json` must never receive unstructured text on stderr.

## JSON envelope

All JSON output **MUST** follow this envelope:

### Success

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

### Error

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

## Streaming output

For long-running commands, JSON streaming **MUST** use newline-delimited JSON (NDJSON):

```
{"type":"progress","step":"validate","status":"ok"}
{"type":"progress","step":"execute","status":"running"}
{"type":"result","ok":true,"data":{...}}
```
