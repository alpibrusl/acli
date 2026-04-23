"""ACLI — Agent-friendly CLI Python SDK."""

from acli.app import ACLIApp
from acli.command import CommandExample, CommandMeta, ParamVersionMeta, acli_command
from acli.errors import (
    ACLIError,
    ConflictError,
    InvalidArgsError,
    NotFoundError,
    PermissionDeniedError,
    PreconditionError,
    TimeoutError,  # noqa: A004 — spec §3 TIMEOUT exit code; shadowing is intentional
    UpstreamError,
    suggest_flag,
)
from acli.exit_codes import ExitCode
from acli.output import (
    CacheMeta,
    OutputFormat,
    emit,
    emit_progress,
    emit_result,
    error_envelope,
    success_envelope,
)
from acli.skill import generate_skill

__all__ = [
    "ACLIApp",
    "ACLIError",
    "CacheMeta",
    "CommandExample",
    "CommandMeta",
    "ConflictError",
    "ExitCode",
    "InvalidArgsError",
    "NotFoundError",
    "OutputFormat",
    "ParamVersionMeta",
    "PermissionDeniedError",
    "PreconditionError",
    "TimeoutError",
    "UpstreamError",
    "acli_command",
    "emit",
    "emit_progress",
    "emit_result",
    "error_envelope",
    "generate_skill",
    "success_envelope",
    "suggest_flag",
]

__version__ = "0.5.0"
