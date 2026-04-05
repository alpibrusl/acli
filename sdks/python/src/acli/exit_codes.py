"""Semantic exit codes as defined by the ACLI spec §3."""

from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    """ACLI semantic exit codes.

    Codes 0-9 are defined by the spec. Codes 10-63 are reserved for tool-specific use.
    """

    SUCCESS = 0
    GENERAL_ERROR = 1
    INVALID_ARGS = 2
    NOT_FOUND = 3
    PERMISSION_DENIED = 4
    CONFLICT = 5
    TIMEOUT = 6
    UPSTREAM_ERROR = 7
    PRECONDITION_FAILED = 8
    DRY_RUN = 9

    @classmethod
    def from_int(cls, code: int) -> ExitCode:
        """Convert an integer to an ExitCode, raising ValueError if unknown."""
        try:
            return cls(code)
        except ValueError:
            if 10 <= code <= 63:
                msg = f"Exit code {code} is in the tool-specific range (10-63)"
                raise ValueError(msg) from None
            msg = f"Unknown exit code: {code}"
            raise ValueError(msg) from None
