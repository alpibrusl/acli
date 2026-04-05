"""ACLI — Agent-friendly CLI Python SDK."""

from acli.app import ACLIApp
from acli.command import CommandExample, CommandMeta, acli_command
from acli.errors import (
    ACLIError,
    ConflictError,
    InvalidArgsError,
    NotFoundError,
    PreconditionError,
    suggest_flag,
)
from acli.exit_codes import ExitCode
from acli.output import OutputFormat, emit, error_envelope, success_envelope
from acli.skill import generate_skill

__all__ = [
    "ACLIApp",
    "ACLIError",
    "CommandExample",
    "CommandMeta",
    "ConflictError",
    "ExitCode",
    "InvalidArgsError",
    "NotFoundError",
    "OutputFormat",
    "PreconditionError",
    "acli_command",
    "emit",
    "error_envelope",
    "generate_skill",
    "success_envelope",
    "suggest_flag",
]

__version__ = "0.1.4"
