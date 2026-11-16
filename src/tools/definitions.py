"""Tool definitions for common robot actions."""

from typing import Any


# Tool schemas compatible with Claude / Bedrock tool use
ROBOT_TOOLS = [
    {
        "name": "move_to",
        "description": "Move the robot end-effector or base to a specific position.",
        "input_schema": {
            "type": "object",
            "properties": {
                "x": {"type": "number", "description": "X coordinate in meters"},
                "y": {"type": "number", "description": "Y coordinate in meters"},
                "z": {"type": "number", "description": "Z coordinate in meters"},
                "frame": {
                    "type": "string",
                    "description": "Reference frame (e.g. 'world', 'base')",
                    "default": "world",
                },
            },
            "required": ["x", "y", "z"],
        },
    },
    {
        "name": "pick",
        "description": "Pick an object at the current or specified location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "object_id": {
                    "type": "string",
                    "description": "Identifier of the object to pick",
                },
                "force": {
                    "type": "number",
                    "description": "Grip force (0.0 - 1.0)",
                    "default": 0.5,
                },
            },
            "required": ["object_id"],
        },
    },
    {
        "name": "place",
        "description": "Place the currently held object at a target location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "x": {"type": "number"},
                "y": {"type": "number"},
                "z": {"type": "number"},
                "object_id": {
                    "type": "string",
                    "description": "Optional: confirm which object is being placed",
                },
            },
            "required": ["x", "y", "z"],
        },
    },
    {
        "name": "inspect",
        "description": "Inspect an object or area using the robot's camera / sensors.",
        "input_schema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "What to inspect (object_id or area description)",
                },
                "sensor": {
                    "type": "string",
                    "enum": ["camera", "depth", "force"],
                    "default": "camera",
                },
            },
            "required": ["target"],
        },
    },
    {
        "name": "navigate",
        "description": "Navigate the mobile base to a named location or coordinates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Named location (e.g. 'kitchen', 'charging_station')",
                },
                "x": {"type": "number"},
                "y": {"type": "number"},
            },
        },
    },
    {
        "name": "wait",
        "description": "Pause execution for a given number of seconds.",
        "input_schema": {
            "type": "object",
            "properties": {
                "seconds": {"type": "number", "minimum": 0},
            },
            "required": ["seconds"],
        },
    },
]


def get_tool_by_name(name: str) -> dict[str, Any] | None:
    """Return a tool definition by name."""
    for tool in ROBOT_TOOLS:
        if tool["name"] == name:
            return tool
    return None
