# Introspection

## Command tree

`build_command_tree` extracts the full command tree from a Typer app via reflection:

```python
from acli.introspect import build_command_tree

tree = build_command_tree(app.typer_app, "noether", "1.0.0")
```

The returned dict follows the spec §1.2 format:

```json
{
  "name": "noether",
  "version": "1.0.0",
  "acli_version": "0.1.0",
  "commands": [
    {
      "name": "run",
      "description": "Execute a pipeline from a YAML file.",
      "arguments": [],
      "options": [
        {"name": "pipeline", "type": "Path", "description": "..."},
        {"name": "env", "type": "string", "description": "...", "default": "dev"}
      ],
      "subcommands": [],
      "idempotent": false,
      "examples": [
        {"description": "Run in staging", "invocation": "noether run --pipeline x.yaml --env staging"}
      ],
      "see_also": ["status"]
    }
  ]
}
```

Options, arguments, types, and defaults are all extracted automatically from the function signature and type hints.

## `.cli/` folder generation

```python
from acli.cli_folder import generate_cli_folder, needs_update

tree = app.get_command_tree()

if needs_update(tree, target_dir=Path(".")):
    cli_dir = generate_cli_folder(tree, target_dir=Path("."))
```

### Generated structure

```
.cli/
  commands.json       # Full command tree (same as introspect output)
  README.md           # Auto-generated overview with command list
  changelog.md        # Created once, never overwritten
  examples/
    run.sh            # One script per command with examples
  schemas/            # Reserved for JSON schemas
```

!!! note
    `changelog.md` is only created if it doesn't exist. Manual edits are preserved across regeneration.

### Checking for updates

```python
needs_update(tree, target_dir)  # True if .cli/commands.json differs from tree
```

This is called automatically by the built-in `introspect` and `version` commands.
