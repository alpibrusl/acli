"""ACLI error types with actionable messages per spec §4."""

from __future__ import annotations

from difflib import get_close_matches

from acli.exit_codes import ExitCode


class ACLIError(Exception):
    """Base error for ACLI commands. Always actionable per spec §4.2."""

    def __init__(
        self,
        message: str,
        *,
        code: ExitCode = ExitCode.GENERAL_ERROR,
        hint: str | None = None,
        hints: list[str] | None = None,
        docs: str | None = None,
        command: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.hint = hint
        self.hints = hints
        self.docs = docs
        self.command = command


class InvalidArgsError(ACLIError):
    """Raised when arguments are wrong or missing."""

    def __init__(
        self,
        message: str,
        *,
        hint: str | None = None,
        hints: list[str] | None = None,
        docs: str | None = None,
    ) -> None:
        super().__init__(
            message, code=ExitCode.INVALID_ARGS, hint=hint, hints=hints, docs=docs
        )


class NotFoundError(ACLIError):
    """Raised when a requested resource does not exist."""

    def __init__(
        self,
        message: str,
        *,
        hint: str | None = None,
        hints: list[str] | None = None,
        docs: str | None = None,
    ) -> None:
        super().__init__(message, code=ExitCode.NOT_FOUND, hint=hint, hints=hints, docs=docs)


class ConflictError(ACLIError):
    """Raised on state conflicts (already exists, locked)."""

    def __init__(
        self,
        message: str,
        *,
        hint: str | None = None,
        hints: list[str] | None = None,
        docs: str | None = None,
    ) -> None:
        super().__init__(message, code=ExitCode.CONFLICT, hint=hint, hints=hints, docs=docs)


class PreconditionError(ACLIError):
    """Raised when a required precondition is not met."""

    def __init__(
        self,
        message: str,
        *,
        hint: str | None = None,
        hints: list[str] | None = None,
        docs: str | None = None,
    ) -> None:
        super().__init__(
            message, code=ExitCode.PRECONDITION_FAILED, hint=hint, hints=hints, docs=docs
        )


def suggest_flag(unknown: str, known: list[str]) -> str | None:
    """Suggest a close match for a mistyped flag per spec §4.1."""
    matches = get_close_matches(unknown, known, n=1, cutoff=0.6)
    return matches[0] if matches else None
