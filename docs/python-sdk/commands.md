# Commands

## `@acli_command` decorator

Attaches ACLI metadata to a Typer command function.

```python
from acli import acli_command

@app.command()
@acli_command(
    examples=[
        ("Run basic", "tool run --file a.yaml"),
        ("Run with env", "tool run --file a.yaml --env prod"),
    ],
    idempotent=False,
    see_also=["status", "logs"],
)
def run(...) -> None:
    """Execute a pipeline."""
    ...
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `examples` | `list[tuple[str, str]]` | Yes | `(description, invocation)` pairs. Minimum 2 per spec. |
| `idempotent` | `bool \| "conditional"` | No | Whether the command is safe to retry. Default: `False`. |
| `see_also` | `list[str]` | No | Related command names for the SEE ALSO section. |

### Auto-injected parameters

The decorator automatically adds parameters that the spec requires:

- **`--output`** (§2.1): Added if not already present. Supports `text|json|table`.
- **`--dry-run`** (§5): Added if `idempotent=False` and not already present.

This means a minimal command needs no boilerplate:

```python
@app.command()
@acli_command(
    examples=[("Run task", "myapp run --file x.yaml"), ("Dry run", "myapp run --file x.yaml --dry-run")],
    idempotent=False,
)
def run(file: str = typer.Option(..., help="File to run. type:path")) -> None:
    """Run a task."""
    # --output and --dry-run are available automatically
    ...
```

If you need to access the injected values, declare them explicitly and they won't be duplicated:

```python
def run(
    file: str = typer.Option(...),
    dry_run: bool = typer.Option(False, "--dry-run"),
    output: OutputFormat = typer.Option(OutputFormat.text),
) -> None: ...
```

### Validation

The decorator raises `ValueError` at import time if:

- Fewer than 2 examples are provided
- `idempotent` is a string other than `"conditional"`

## CommandMeta

The decorator stores a frozen `CommandMeta` dataclass on the function:

```python
from acli.command import ACLI_META_ATTR, CommandMeta

meta: CommandMeta = getattr(my_func, ACLI_META_ATTR)
meta.examples      # tuple of CommandExample(description, invocation)
meta.idempotent    # True, False, or "conditional"
meta.see_also      # tuple of command name strings
```

Both `CommandMeta` and `CommandExample` are frozen dataclasses — immutable after creation.
