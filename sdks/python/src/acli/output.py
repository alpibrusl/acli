"""Output format handling and JSON envelope as defined by ACLI spec §2."""

from __future__ import annotations

import json
import sys
import time
from enum import Enum
from typing import Any


class OutputFormat(str, Enum):
    """Supported output formats per ACLI spec §2.1."""

    text = "text"
    json = "json"
    table = "table"


def success_envelope(
    command: str,
    data: dict[str, Any],
    *,
    version: str,
    start_time: float | None = None,
    dry_run: bool = False,
    planned_actions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a success JSON envelope per ACLI spec §2.2."""
    duration_ms = int((time.time() - start_time) * 1000) if start_time else 0
    envelope: dict[str, Any] = {
        "ok": True,
        "command": command,
    }
    if dry_run:
        envelope["dry_run"] = True
        if planned_actions is not None:
            envelope["planned_actions"] = planned_actions
    else:
        envelope["data"] = data
    envelope["meta"] = {"duration_ms": duration_ms, "version": version}
    return envelope


def error_envelope(
    command: str,
    *,
    code: str,
    message: str,
    hint: str | None = None,
    docs: str | None = None,
    version: str,
    start_time: float | None = None,
) -> dict[str, Any]:
    """Build an error JSON envelope per ACLI spec §2.2."""
    duration_ms = int((time.time() - start_time) * 1000) if start_time else 0
    error: dict[str, Any] = {"code": code, "message": message}
    if hint:
        error["hint"] = hint
    if docs:
        error["docs"] = docs
    return {
        "ok": False,
        "command": command,
        "error": error,
        "meta": {"duration_ms": duration_ms, "version": version},
    }


def emit_progress(
    step: str,
    status: str,
    *,
    detail: str | None = None,
) -> None:
    """Emit a progress line as NDJSON per ACLI spec §2.3.

    Used for long-running commands to stream intermediate status.
    """
    line: dict[str, Any] = {"type": "progress", "step": step, "status": status}
    if detail is not None:
        line["detail"] = detail
    sys.stdout.write(json.dumps(line) + "\n")
    sys.stdout.flush()


def emit_result(data: dict[str, Any], *, ok: bool = True) -> None:
    """Emit a final result line as NDJSON per ACLI spec §2.3.

    Terminates an NDJSON stream with the final result.
    """
    line: dict[str, Any] = {"type": "result", "ok": ok}
    line.update(data)
    sys.stdout.write(json.dumps(line) + "\n")
    sys.stdout.flush()


def emit(data: dict[str, Any], fmt: OutputFormat) -> None:
    """Write output to stdout in the requested format."""
    if fmt == OutputFormat.json:
        json.dump(data, sys.stdout, indent=2)
        sys.stdout.write("\n")
    elif fmt == OutputFormat.table:
        _emit_table(data)
    else:
        _emit_text(data)


def _emit_text(data: dict[str, Any]) -> None:
    """Emit human-readable text output."""
    if data.get("ok") is False:
        err = data.get("error", {})
        sys.stderr.write(f"Error [{err.get('code', 'UNKNOWN')}]: {err.get('message', '')}\n")
        if hint := err.get("hint"):
            sys.stderr.write(f"  {hint}\n")
        if docs := err.get("docs"):
            sys.stderr.write(f"  Reference: {docs}\n")
    else:
        payload = data.get("data", data.get("planned_actions", {}))
        if isinstance(payload, dict):
            for key, value in payload.items():
                sys.stdout.write(f"{key}: {value}\n")
        elif isinstance(payload, list):
            for item in payload:
                sys.stdout.write(f"  {item}\n")


def _emit_table(data: dict[str, Any]) -> None:
    """Emit ASCII table output."""
    payload = data.get("data", {})
    if isinstance(payload, dict):
        if not payload:
            return
        max_key = max(len(str(k)) for k in payload)
        for key, value in payload.items():
            sys.stdout.write(f"{key!s:<{max_key}}  {value}\n")
    elif isinstance(payload, list) and payload and isinstance(payload[0], dict):
        headers = list(payload[0].keys())
        col_widths = {h: len(h) for h in headers}
        for row in payload:
            for h in headers:
                col_widths[h] = max(col_widths[h], len(str(row.get(h, ""))))
        header_line = "  ".join(f"{h:<{col_widths[h]}}" for h in headers)
        sys.stdout.write(header_line + "\n")
        sys.stdout.write("  ".join("-" * col_widths[h] for h in headers) + "\n")
        for row in payload:
            line = "  ".join(f"{row.get(h, '')!s:<{col_widths[h]}}" for h in headers)
            sys.stdout.write(line + "\n")
