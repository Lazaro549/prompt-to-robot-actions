"""
Composite backend: mobile base (Gazebo/Nav2) + arm (MoveIt) + vision.

Routes tools to the right subsystem and enriches `inspect` with detections
so the multi-turn agent can replan.
"""

from __future__ import annotations

from typing import Any, Protocol

from src.vision.detector import MockDetector, VisionObservation


class Backend(Protocol):
    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]: ...


class CompositeBackend:
    """
    Routes:
      navigate, move_to (base) → base_backend
      pick, place, move_to (arm preference) → arm_backend if present
      inspect → vision detector (+ optional camera motion)
      wait → either

    Example:
        from src.backends.gazebo_ros2 import MockGazeboBackend
        from src.backends.moveit_bridge import MockMoveItBackend
        from src.vision import MockDetector

        backend = CompositeBackend(
            base=MockGazeboBackend(),
            arm=MockMoveItBackend(),
            detector=MockDetector(),
        )
    """

    # Tools primarily handled by the arm
    ARM_TOOLS = {"pick", "place"}
    BASE_TOOLS = {"navigate"}

    def __init__(
        self,
        base: Backend,
        arm: Backend | None = None,
        detector: MockDetector | None = None,
        prefer_arm_for_move_to: bool = True,
    ):
        self.base = base
        self.arm = arm
        self.detector = detector or MockDetector()
        self.prefer_arm_for_move_to = prefer_arm_for_move_to

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool_name == "inspect":
            return self._inspect(arguments)

        if tool_name == "pick":
            result = self._route_pick(arguments)
            if result.get("success") and hasattr(self.detector, "mark_picked"):
                self.detector.mark_picked(arguments.get("object_id", ""))
            return result

        if tool_name == "place":
            result = self._route_place(arguments)
            if result.get("success") and hasattr(self.detector, "mark_placed"):
                self.detector.mark_placed(
                    arguments.get("object_id") or result.get("placed", "object"),
                    float(arguments.get("x", 0.0)),
                    float(arguments.get("y", 0.0)),
                    float(arguments.get("z", 0.1)),
                )
            return result

        if tool_name == "move_to":
            if self.arm and self.prefer_arm_for_move_to:
                return self.arm.execute(tool_name, arguments)
            return self.base.execute(tool_name, arguments)

        if tool_name in self.BASE_TOOLS:
            return self.base.execute(tool_name, arguments)

        if tool_name in self.ARM_TOOLS and self.arm:
            return self.arm.execute(tool_name, arguments)

        # Fallback: try base, then arm
        result = self.base.execute(tool_name, arguments)
        if not result.get("success") and self.arm:
            return self.arm.execute(tool_name, arguments)
        return result

    def _route_pick(self, arguments: dict[str, Any]) -> dict[str, Any]:
        if self.arm:
            return self.arm.execute("pick", arguments)
        return self.base.execute("pick", arguments)

    def _route_place(self, arguments: dict[str, Any]) -> dict[str, Any]:
        if self.arm:
            return self.arm.execute("place", arguments)
        return self.base.execute("place", arguments)

    def _inspect(self, arguments: dict[str, Any]) -> dict[str, Any]:
        target = arguments.get("target")
        obs: VisionObservation = self.detector.detect(target)
        return {
            "success": True,
            "message": obs.summary_for_llm(),
            "observation": obs.to_dict(),
            "detections": [d.to_dict() for d in obs.detections],
        }

    def get_state(self) -> dict[str, Any]:
        state: dict[str, Any] = {}
        if hasattr(self.base, "get_state"):
            state["base"] = self.base.get_state()
        if self.arm and hasattr(self.arm, "get_state"):
            state["arm"] = self.arm.get_state()
        state["vision"] = self.detector.detect().to_dict()
        return state
