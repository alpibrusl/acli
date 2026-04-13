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


class UpstreamError(ACLIError):
    """Raised when an upstream service (HTTP, database, external API) fails.

    Maps to ACLI exit code 7 (UPSTREAM_ERROR). Use for network errors, 5xx
    responses, timeouts fetching a remote resource, or any failure whose root
    cause is outside the tool's control.
    """

    def __init__(
        self,
        message: str,
        *,
        hint: str | None = None,
        hints: list[str] | None = None,
        docs: str | None = None,
    ) -> None:
        super().__init__(
            message, code=ExitCode.UPSTREAM_ERROR, hint=hint, hints=hints, docs=docs
        )


class TimeoutError(ACLIError):  # noqa: A001 — intentionally shadows builtin
    """Raised when a tool's own operation times out.

    Maps to ACLI exit code 6 (TIMEOUT). Distinct from UpstreamError: this is
    the tool giving up, not the network failing.
    """

    def __init__(
        self,
        message: str,
        *,
        hint: str | None = None,
        hints: list[str] | None = None,
        docs: str | None = None,
    ) -> None:
        super().__init__(
            message, code=ExitCode.TIMEOUT, hint=hint, hints=hints, docs=docs
        )


class PermissionDeniedError(ACLIError):
    """Raised when a tool lacks permission to perform the requested action.

    Maps to ACLI exit code 4 (PERMISSION_DENIED).
    """

    def __init__(
        self,
        message: str,
        *,
        hint: str | None = None,
        hints: list[str] | None = None,
        docs: str | None = None,
    ) -> None:
        super().__init__(
            message, code=ExitCode.PERMISSION_DENIED, hint=hint, hints=hints, docs=docs
        )


def suggest_flag(unknown: str, known: list[str]) -> str | None:
    """Suggest a close match for a mistyped flag per spec §4.1."""
    matches = get_close_matches(unknown, known, n=1, cutoff=0.6)
    return matches[0] if matches else None
