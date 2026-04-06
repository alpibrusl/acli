"""Introspection command and command-tree builder per ACLI spec §1.2."""

from __future__ import annotations

import inspect
from typing import Any, get_type_hints

import typer

from acli.command import ACLI_META_ATTR, CommandMeta, ParamVersionMeta


def build_command_tree(app: typer.Typer, app_name: str, version: str) -> dict[str, Any]:
    """Build the full command tree JSON as specified in ACLI spec §1.2."""
    commands = []

    for command_info in app.registered_commands:
        cmd_dict = _extract_command_info(command_info)
        if cmd_dict:
            commands.append(cmd_dict)

    for group_info in app.registered_groups:
        if group_info.typer_instance:
            group_name = group_info.name or ""
            group_commands = []
            for sub_cmd in group_info.typer_instance.registered_commands:
                cmd_dict = _extract_command_info(sub_cmd)
                if cmd_dict:
                    group_commands.append(cmd_dict)
            commands.append(
                {
                    "name": group_name,
                    "description": group_info.typer_instance.info.help or "",
                    "subcommands": group_commands,
                }
            )

    return {
        "name": app_name,
        "version": version,
        "acli_version": "0.1.0",
        "commands": commands,
    }


def _extract_command_info(command_info: Any) -> dict[str, Any] | None:
    """Extract structured info from a single Typer command registration."""
    callback = command_info.callback
    if callback is None:
        return None

    name = command_info.name or getattr(callback, "__name__", "unknown")
    doc = inspect.getdoc(callback) or ""
    description = doc.split("\n")[0] if doc else ""

    meta: CommandMeta | None = getattr(callback, ACLI_META_ATTR, None)

    param_lookup: dict[str, ParamVersionMeta] = {}
    if meta and meta.param_meta:
        param_lookup = dict(meta.param_meta)

    arguments, options = _extract_params(callback, param_lookup)

    result: dict[str, Any] = {
        "name": name,
        "description": description,
        "arguments": arguments,
        "options": options,
        "subcommands": [],
    }

    if meta:
        result["idempotent"] = meta.idempotent
        result["examples"] = [
            {"description": ex.description, "invocation": ex.invocation} for ex in meta.examples
        ]
        if meta.see_also:
            result["see_also"] = list(meta.see_also)

    return result


def _extract_params(
    func: Any,
    param_meta: dict[str, ParamVersionMeta],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract argument and option metadata from a function's signature."""

    def _apply_param_meta(entry: dict[str, Any], param_name: str) -> None:
        pv = param_meta.get(param_name)
        if pv is None:
            return
        if pv.since_version:
            entry["since_version"] = pv.since_version
        if pv.deprecated_since:
            entry["deprecated_since"] = pv.deprecated_since

    arguments: list[dict[str, Any]] = []
    options: list[dict[str, Any]] = []

    sig = inspect.signature(func)
    try:
        hints = get_type_hints(func)
    except Exception:
        hints = {}

    for param_name, param in sig.parameters.items():
        type_hint = hints.get(param_name, str)
        type_str = _type_to_str(type_hint)
        default = param.default

        if isinstance(default, typer.models.OptionInfo):
            entry: dict[str, Any] = {
                "name": param_name,
                "type": type_str,
                "description": default.help or "",
            }
            if default.default is not ...:
                entry["default"] = _serialize_default(default.default)
            _apply_param_meta(entry, param_name)
            options.append(entry)
        elif isinstance(default, typer.models.ArgumentInfo):
            entry = {
                "name": param_name,
                "type": type_str,
                "required": default.default is ...,
                "description": default.help or "",
            }
            _apply_param_meta(entry, param_name)
            arguments.append(entry)
        elif default is inspect.Parameter.empty:
            entry = {
                "name": param_name,
                "type": type_str,
                "required": True,
                "description": "",
            }
            _apply_param_meta(entry, param_name)
            arguments.append(entry)

    return arguments, options


def _type_to_str(type_hint: Any) -> str:
    """Convert a Python type hint to an ACLI type string."""
    if type_hint is str:
        return "string"
    if type_hint is int:
        return "int"
    if type_hint is float:
        return "float"
    if type_hint is bool:
        return "bool"
    origin = getattr(type_hint, "__origin__", None)
    if origin is not None:
        return str(type_hint)
    if hasattr(type_hint, "__name__"):
        return str(type_hint.__name__)
    return str(type_hint)


def _serialize_default(value: Any) -> Any:
    """Serialize a default value for JSON output."""
    if hasattr(value, "value"):
        return value.value
    return value
