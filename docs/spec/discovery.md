# Progressive Discovery

An agent should be able to learn the full capability surface of a tool incrementally, starting from `--help`.

!!! note "See also"
    The same concept of agents learning tools at runtime via `--help` appears independently in other projects, notably as **Progressive Skills** in [Scion](https://googlecloudplatform.github.io/scion/philosophy/) (Google Cloud Platform). ACLI formalises this idea into a full specification with structured output, semantic exit codes, and persistent discovery artifacts.

## `--help` structure

Every command and subcommand **MUST** expose `--help` with these sections, in order:

```
<one-line description>

USAGE:
  <tool> <command> [OPTIONS] [ARGS]

DESCRIPTION:
  <2–5 line explanation of what this command does and when to use it>

ARGUMENTS:
  <name>    <type>    <required|optional>    <description>

OPTIONS:
  --option    <type>    <description>    [default: <value>]

EXAMPLES:
  # <intent description>
  <tool> <command> <concrete invocation>

  # <second example with different case>
  <tool> <command> <concrete invocation>

SEE ALSO:
  <related subcommand>, <related subcommand>
```

### Rules

- Descriptions must be written for an agent that has **no prior context**
- Every argument and option must have a type annotation (`string`, `int`, `bool`, `enum[a|b|c]`, `path`)
- At least **two examples** per command, with concrete invocations (no `<placeholder>`)
- `SEE ALSO` must list related commands by name

## Introspection command

Every ACLI tool **MUST** expose:

```bash
<tool> introspect
```

This outputs the full command tree as JSON:

```json
{
  "name": "noether",
  "version": "1.2.0",
  "acli_version": "0.1.0",
  "commands": [
    {
      "name": "run",
      "description": "Execute a pipeline from a Lagrange YAML file",
      "arguments": [...],
      "options": [...],
      "subcommands": []
    }
  ]
}
```

Agents should prefer `introspect` for initial capability mapping and `--help` for contextual guidance on a specific command.

## `.cli/` reference folder

Every ACLI tool **MUST** maintain a `.cli/` folder at the project root:

```
.cli/
  README.md          # human-readable overview
  commands.json      # same output as introspect
  examples/
    <command>.sh     # runnable example scripts per command
  schemas/
    <type>.json      # JSON schemas for complex types
  changelog.md       # recent changes agents should be aware of
```

The `.cli/` folder is the **persistent knowledge base** for agents. It allows orientation without executing the tool, and survives context resets.

### Update rules

- Updated automatically on `<tool> --version` or `<tool> introspect`
- Never requires elevated permissions to write
- Safe to commit to version control
