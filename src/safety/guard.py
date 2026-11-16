"""Safety checks before executing robot tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ForbiddenZone:
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    name: str = "zone"

    def contains(self, x: float, y: float) -> bool:
        return self.x_min <= x <= self.x_max and self.y_min <= y <= self.y_max


@dataclass
class SafetyGuard:
    allowed_tools: set[str] = field(
        default_factory=lambda: {
            "move_to",
            "pick",
            "place",
            "inspect",
            "navigate",
            "wait",
        }
    )
    forbidden_zones: list[ForbiddenZone] = field(default_factory=list)

    def check(self, tool_name: str, arguments: dict[str, Any]) -> tuple[bool, str | None]:
        if tool_name not in self.allowed_tools:
            return False, f"Tool '{tool_name}' is not in the allow-list"

        if tool_name in ("move_to", "place", "navigate"):
            x = arguments.get("x")
            y = arguments.get("y")
            if x is not None and y is not None:
                for zone in self.forbidden_zones:
                    if zone.contains(float(x), float(y)):
                        return False, f"Target ({x}, {y}) is inside forbidden zone '{zone.name}'"

        return True, None


def safety_from_config(cfg: dict[str, Any] | None) -> SafetyGuard:
    if not cfg:
        return SafetyGuard()
    zones = [
        ForbiddenZone(
            x_min=float(z["x_min"]),
            x_max=float(z["x_max"]),
            y_min=float(z["y_min"]),
            y_max=float(z["y_max"]),
            name=str(z.get("name", "zone")),
        )
        for z in cfg.get("forbidden_zones", [])
    ]
    allowed = set(cfg.get("allowed_tools") or SafetyGuard().allowed_tools)
    return SafetyGuard(allowed_tools=allowed, forbidden_zones=zones)
