# ACLIApp

`ACLIApp` is the main application class. It wraps `typer.Typer` and automatically enforces ACLI spec compliance.

## Constructor

```python
from acli import ACLIApp

app = ACLIApp(
    name="mytool",       # Tool name (used in version output and introspect)
    version="1.0.0",     # Semver version string
    cli_dir=None,        # Optional: override .cli/ folder location
)
```

## Registering commands

Use `@app.command()` just like Typer, combined with [`@acli_command`](commands.md) for ACLI metadata:

```python
@app.command()
@acli_command(
    examples=[("Example 1", "mytool do --flag"), ("Example 2", "mytool do --other")],
    idempotent=True,
)
def do(
    flag: str = typer.Option(..., help="A required flag. type:string"),
) -> None:
    """Do something."""
    ...
```

## Adding sub-groups

```python
import typer

sub = typer.Typer(help="Manage configs")

@sub.command()
def show() -> None:
    """Show current config."""
    ...

app.add_typer(sub, name="config")
```

## Running the app

```python
app.run()
```

This wraps `typer()` with ACLI error handling:

- `ACLIError` subclasses are caught and emitted as JSON error envelopes with the correct exit code
- Unexpected exceptions are caught and emitted as `GENERAL_ERROR` (exit code 1)
- `SystemExit` is re-raised as-is

## Built-in commands

### `introspect`

```bash
mytool introspect                    # Full command tree as JSON
mytool introspect --acli-version     # Just the ACLI spec version
```

Also updates `.cli/` if out of date.

### `version`

```bash
mytool version                       # Human-readable
mytool version --output json         # JSON envelope
```

## Accessing internals

```python
app.typer_app          # The underlying typer.Typer instance
app.get_command_tree() # Build the introspection tree as a dict
```
