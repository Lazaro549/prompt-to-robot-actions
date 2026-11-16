"""Validate tool arguments against ROBOT_TOOLS input schemas."""

from __future__ import annotations

from typing import Any

from src.tools.definitions import ROBOT_TOOLS, get_tool_by_name


class ValidationError(ValueError):
    """Raised when tool arguments do not match the schema."""


def validate_tool_call(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and normalize arguments for a robot tool.

    Returns a cleaned arguments dict (defaults applied).
    Raises ValidationError on failure.
    """
    tool = get_tool_by_name(tool_name)
    if tool is None:
        known = ", ".join(t["name"] for t in ROBOT_TOOLS)
        raise ValidationError(f"Unknown tool '{tool_name}'. Known: {known}")

    schema = tool.get("input_schema", {})
    props = schema.get("properties", {})
    required = schema.get("required", [])

    if not isinstance(arguments, dict):
        raise ValidationError(f"Arguments for {tool_name} must be a dict")

    cleaned: dict[str, Any] = {}

    for key in required:
        if key not in arguments or arguments[key] is None:
            raise ValidationError(f"{tool_name}: missing required argument '{key}'")

    for key, value in arguments.items():
        if key not in props:
            continue
        cleaned[key] = _coerce(key, value, props[key])

    for key, prop in props.items():
        if key not in cleaned and "default" in prop:
            cleaned[key] = prop["default"]

    return cleaned


def _coerce(key: str, value: Any, prop: dict[str, Any]) -> Any:
    expected = prop.get("type")
    if expected == "number":
        try:
            num = float(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"'{key}' must be a number") from exc
        if "minimum" in prop and num < prop["minimum"]:
            raise ValidationError(f"'{key}' must be >= {prop['minimum']}")
        return num
    if expected == "string":
        if not isinstance(value, str):
            raise ValidationError(f"'{key}' must be a string")
        enum = prop.get("enum")
        if enum and value not in enum:
            raise ValidationError(f"'{key}' must be one of {enum}")
        return value
    if expected == "integer":
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise ValidationError(f"'{key}' must be an integer") from exc
    return value
