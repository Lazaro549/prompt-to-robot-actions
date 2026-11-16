"""Simple in-memory robot simulator for testing the pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SimulatorState:
    position: dict[str, float] = field(
        default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.3}
    )
    holding: str | None = None
    last_action: str | None = None
    history: list[dict[str, Any]] = field(default_factory=list)


class SimulatorBackend:
    """
    Minimal robot simulator.

    Supports the tools defined in src.tools.definitions.
    Useful for end-to-end testing without real hardware or ROS.
    """

    def __init__(self):
        self.state = SimulatorState()

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a single tool call and return a result dict."""
        handler = getattr(self, f"_handle_{tool_name}", None)
        if handler is None:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
                "tool": tool_name,
            }

        result = handler(arguments)
        self.state.last_action = tool_name
        self.state.history.append({"tool": tool_name, "args": arguments, "result": result})
        return result

    def _handle_move_to(self, args: dict[str, Any]) -> dict[str, Any]:
        self.state.position = {
            "x": float(args["x"]),
            "y": float(args["y"]),
            "z": float(args["z"]),
        }
        return {
            "success": True,
            "message": f"Moved to ({args['x']}, {args['y']}, {args['z']})",
            "position": self.state.position.copy(),
        }

    def _handle_pick(self, args: dict[str, Any]) -> dict[str, Any]:
        object_id = args["object_id"]
        if self.state.holding is not None:
            return {
                "success": False,
                "error": f"Already holding {self.state.holding}",
                "tool": "pick",
            }
        self.state.holding = object_id
        return {
            "success": True,
            "message": f"Picked {object_id}",
            "holding": object_id,
        }

    def _handle_place(self, args: dict[str, Any]) -> dict[str, Any]:
        if self.state.holding is None:
            return {
                "success": False,
                "error": "Nothing to place",
                "tool": "place",
            }
        placed = self.state.holding
        self.state.holding = None
        self.state.position = {
            "x": float(args["x"]),
            "y": float(args["y"]),
            "z": float(args["z"]),
        }
        return {
            "success": True,
            "message": f"Placed {placed} at ({args['x']}, {args['y']}, {args['z']})",
            "placed": placed,
        }

    def _handle_inspect(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "success": True,
            "message": f"Inspected {args.get('target')} with {args.get('sensor', 'camera')}",
            "observation": {
                "target": args.get("target"),
                "sensor": args.get("sensor", "camera"),
                "status": "ok",
            },
        }

    def _handle_navigate(self, args: dict[str, Any]) -> dict[str, Any]:
        location = args.get("location")
        if location:
            # simple named locations
            locations = {
                "home": {"x": 0.0, "y": 0.0},
                "kitchen": {"x": 2.0, "y": 1.5},
                "charging_station": {"x": -1.0, "y": 0.0},
            }
            pos = locations.get(location, {"x": 0.0, "y": 0.0})
            self.state.position.update(pos)
            return {
                "success": True,
                "message": f"Navigated to {location}",
                "position": self.state.position.copy(),
            }

        if "x" in args and "y" in args:
            self.state.position["x"] = float(args["x"])
            self.state.position["y"] = float(args["y"])
            return {
                "success": True,
                "message": f"Navigated to ({args['x']}, {args['y']})",
                "position": self.state.position.copy(),
            }

        return {"success": False, "error": "No valid navigation target"}

    def _handle_wait(self, args: dict[str, Any]) -> dict[str, Any]:
        seconds = float(args.get("seconds", 1.0))
        return {
            "success": True,
            "message": f"Waited {seconds} seconds",
            "seconds": seconds,
        }

    def get_state(self) -> dict[str, Any]:
        return {
            "position": self.state.position.copy(),
            "holding": self.state.holding,
            "last_action": self.state.last_action,
            "history_length": len(self.state.history),
        }
