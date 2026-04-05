"""The @acli_command decorator and command metadata per ACLI spec §1, §5, §6."""

from __future__ import annotations

import dataclasses
from typing import Any


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
        setattr(func, ACLI_META_ATTR, meta)
        return func

    return decorator
