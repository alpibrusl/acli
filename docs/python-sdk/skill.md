# Skill File Generation

ACLI bridges the gap between Stage 2 (SKILLS.md) and Stage 3 (CLI self-discovery) by letting tools auto-generate their own skill files.

## Why skill files?

The first time an agent encounters an ACLI tool, it faces a cold-start problem: it needs to run `--help` or `introspect` before it can act. A skill file provides immediate context — and because it's generated from the tool itself, it's always accurate.

```
Agent reads SKILLS.md  →  knows commands, options, examples immediately
Agent runs --help       →  gets deeper details on demand
Agent runs introspect   →  gets machine-readable command tree
```

The skill file is the fast path; `--help` and `introspect` are the deep path.

## Generating a skill file

### From any ACLIApp (built-in command)

Every `ACLIApp` gets a `skill` command automatically:

```bash
myapp skill                          # Print to stdout
myapp skill --out SKILLS.md          # Write to file
myapp skill --output json            # JSON envelope with content
```

### Using the acli CLI

```bash
acli skill --bin myapp               # Generate from any installed ACLI tool
acli skill --bin myapp --out SKILLS.md
```

### Programmatically

```python
from acli import generate_skill

tree = app.get_command_tree()
content = generate_skill(tree, target_path=Path("SKILLS.md"))
```

## What's included

The generated skill file contains:

1. **Command overview** — all user-facing commands with descriptions and idempotency tags
2. **Detailed usage** — options, arguments, types, defaults for each command
3. **Examples** — concrete invocations from `@acli_command` metadata
4. **See also** — cross-references between related commands
5. **Output format** — JSON envelope contract summary
6. **Exit codes** — semantic exit code table
7. **Discovery hints** — pointers to `--help`, `introspect`, and `.cli/` for deeper exploration

## Regeneration

Skill files include a header with regeneration instructions:

```markdown
> Auto-generated skill file for `myapp` v1.0.0
> Re-generate with: `myapp skill` or `acli skill --bin myapp`
```

After updating your tool's commands, regenerate the skill file to keep it in sync.

## The acli CLI

The `acli` command is the meta-CLI for working with ACLI tools:

| Command | Description |
|---------|-------------|
| `acli validate --bin <tool>` | Validate a tool against the ACLI spec checklist |
| `acli skill --bin <tool>` | Generate a skill file for a tool |
| `acli init --name <name>` | Scaffold a new ACLI-compliant Python project |

The `acli` CLI is itself ACLI-compliant — you can run `acli validate --bin acli` to verify.
