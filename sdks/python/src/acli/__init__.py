"""ACLI — Agent-friendly CLI Python SDK."""

from acli.app import ACLIApp
from acli.command import CommandExample, CommandMeta, ParamVersionMeta, acli_command
from acli.errors import (
    ACLIError,
    ConflictError,
    InvalidArgsError,
    NotFoundError,
    PreconditionError,
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
    "ParamVersionMeta",
    "ConflictError",
    "ExitCode",
    "InvalidArgsError",
    "NotFoundError",
    "OutputFormat",
    "PreconditionError",
    "acli_command",
    "emit",
    "emit_progress",
    "emit_result",
    "error_envelope",
    "generate_skill",
    "success_envelope",
    "suggest_flag",
]

__version__ = "0.4.0"
