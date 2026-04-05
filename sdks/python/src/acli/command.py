"""The @acli_command decorator and command metadata per ACLI spec §1, §5, §6."""

from __future__ import annotations

import dataclasses
import functools
import inspect
from typing import Any

import typer

from acli.output import OutputFormat


@dataclasses.dataclass(frozen=True)
class CommandExample:
    """A concrete usage example for a command."""

    description: str
    invocation: str


@dataclasses.dataclass(frozen=True)
class CommandMeta:
    """Metadata attached to a command by @acli_command."""

    examples: tuple[CommandExample, ...]
    idempotent: bool | str  # True, False, or "conditional"
    see_also: tuple[str, ...]


ACLI_META_ATTR = "_acli_meta"


def acli_command(
    *,
    examples: list[tuple[str, str]],
    idempotent: bool | str = False,
    see_also: list[str] | None = None,
) -> Any:
    """Decorator that attaches ACLI metadata to a Typer command function.

    Automatically injects ``--output`` if not already present.
    Automatically injects ``--dry-run`` if ``idempotent=False``.

    Args:
        examples: List of (description, invocation) tuples. At least 2 required per spec.
        idempotent: Whether the command is idempotent (True/False/"conditional").
        see_also: Related command names for the SEE ALSO section.
    """
    if len(examples) < 2:
        msg = "ACLI spec requires at least 2 examples per command"
        raise ValueError(msg)

    if isinstance(idempotent, str) and idempotent != "conditional":
        msg = f"idempotent must be True, False, or 'conditional', got '{idempotent}'"
        raise ValueError(msg)

    parsed = tuple(CommandExample(desc, inv) for desc, inv in examples)
    meta = CommandMeta(
        examples=parsed,
        idempotent=idempotent,
        see_also=tuple(see_also or []),
    )

    def decorator(func: Any) -> Any:
        wrapped = _inject_params(func, idempotent)
        setattr(wrapped, ACLI_META_ATTR, meta)
        return wrapped

    return decorator


def _inject_params(func: Any, idempotent: bool | str) -> Any:
    """Inject --output and --dry-run parameters if not already present."""
    sig = inspect.signature(func)
    params = dict(sig.parameters)
    added_output = False
    added_dry_run = False

    if "output" not in params:
        added_output = True

    if idempotent is False and "dry_run" not in params:
        added_dry_run = True

    if not added_output and not added_dry_run:
        return func

    @functools.wraps(func)
    def wrapper(**kwargs: Any) -> Any:
        # Remove injected params before calling the original if it doesn't expect them
        if added_output and "output" not in sig.parameters:
            kwargs.pop("output", None)
        if added_dry_run and "dry_run" not in sig.parameters:
            kwargs.pop("dry_run", None)
        return func(**kwargs)

    # Build new parameter list
    new_params = list(sig.parameters.values())

    if added_output:
        new_params.append(
            inspect.Parameter(
                "output",
                inspect.Parameter.KEYWORD_ONLY,
                default=typer.Option(
                    OutputFormat.text,
                    help="Output format. type:enum[text|json|table]",
                ),
                annotation=OutputFormat,
            )
        )

    if added_dry_run:
        new_params.append(
            inspect.Parameter(
                "dry_run",
                inspect.Parameter.KEYWORD_ONLY,
                default=typer.Option(
                    False,
                    "--dry-run",
                    help="Describe actions without executing. type:bool",
                ),
                annotation=bool,
            )
        )

    wrapper.__signature__ = sig.replace(parameters=new_params)  # type: ignore[attr-defined]
    return wrapper
