"""
MoveIt 2 bridge for arm pick / place / move_to.

Pick pipeline stages: pre_grasp → approach → close_gripper → retreat
Place pipeline: approach → open_gripper → retreat
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MoveItConfig:
    planning_group: str = "arm"
    gripper_group: str = "gripper"
    frame_id: str = "base_link"
    move_action: str = "/move_action"
    gripper_action: str = "/gripper_controller/gripper_cmd"
    planning_time: float = 5.0
    approach_offset_z: float = 0.08
    retreat_offset_z: float = 0.12


@dataclass
class MockArmState:
    joints: list[float] = field(default_factory=lambda: [0.0] * 6)
    ee_pose: dict[str, float] = field(
        default_factory=lambda: {"x": 0.3, "y": 0.0, "z": 0.4}
    )
    gripper_open: bool = True
    holding: str | None = None
    last_pipeline: list[str] = field(default_factory=list)


class MockMoveItBackend:
    """Simulates full pick/place pipeline without ROS."""

    def __init__(self, config: MoveItConfig | None = None):
        self.config = config or MoveItConfig()
        self.state = MockArmState()

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool_name == "move_to":
            self.state.ee_pose = {
                "x": float(arguments["x"]),
                "y": float(arguments["y"]),
                "z": float(arguments["z"]),
            }
            self.state.last_pipeline = ["plan", "execute_to_pose"]
            return {
                "success": True,
                "message": f"[MoveIt-mock] Planned & moved EE to {self.state.ee_pose}",
                "ee_pose": self.state.ee_pose.copy(),
                "pipeline": self.state.last_pipeline,
            }

        if tool_name == "pick":
            return self._pick_pipeline(arguments)

        if tool_name == "place":
            return self._place_pipeline(arguments)

        if tool_name == "inspect":
            return {
                "success": True,
                "message": "[MoveIt-mock] Arm at observe pose",
                "observation": {"status": "ok"},
            }

        if tool_name == "wait":
            time.sleep(min(float(arguments.get("seconds", 1.0)), 0.05))
            return {"success": True, "message": "waited"}

        if tool_name == "navigate":
            return {
                "success": False,
                "error": "navigate is a base action; use Gazebo/Nav2 backend",
            }

        return {"success": False, "error": f"Unknown tool: {tool_name}"}

    def _pick_pipeline(self, args: dict[str, Any]) -> dict[str, Any]:
        if self.state.holding:
            return {"success": False, "error": f"Already holding {self.state.holding}"}
        object_id = args["object_id"]
        stages = [
            "pre_grasp",
            "approach",
            "close_gripper",
            "retreat",
        ]
        # Simulate EE motion above object then down
        self.state.ee_pose["z"] = self.state.ee_pose.get("z", 0.4)
        self.state.gripper_open = False
        self.state.holding = object_id
        self.state.last_pipeline = stages
        return {
            "success": True,
            "message": f"[MoveIt-mock] Pick pipeline complete for {object_id}",
            "holding": object_id,
            "pipeline": stages,
        }

    def _place_pipeline(self, args: dict[str, Any]) -> dict[str, Any]:
        if not self.state.holding:
            return {"success": False, "error": "Nothing to place"}
        placed = self.state.holding
        stages = ["approach_place", "open_gripper", "retreat"]
        self.state.ee_pose = {
            "x": float(args.get("x", self.state.ee_pose["x"])),
            "y": float(args.get("y", self.state.ee_pose["y"])),
            "z": float(args.get("z", 0.15)),
        }
        self.state.gripper_open = True
        self.state.holding = None
        self.state.last_pipeline = stages
        return {
            "success": True,
            "message": f"[MoveIt-mock] Place pipeline complete for {placed}",
            "placed": placed,
            "pipeline": stages,
            "ee_pose": self.state.ee_pose.copy(),
        }

    def get_state(self) -> dict[str, Any]:
        return {
            "ee_pose": self.state.ee_pose.copy(),
            "gripper_open": self.state.gripper_open,
            "holding": self.state.holding,
            "last_pipeline": list(self.state.last_pipeline),
        }


class MoveItBackend:
    """
    Real MoveIt 2 backend with explicit pick/place pipeline stages.

    Requires moveit_py + robot moveit_config. Stage methods are stubs to
    fill with your planner/gripper action clients.
    """

    def __init__(self, config: MoveItConfig | None = None):
        self.config = config or MoveItConfig()
        self._moveit = None
        self._init_moveit()

    def _init_moveit(self) -> None:
        try:
            from moveit.planning import MoveItPy
        except ImportError as exc:
            raise ImportError(
                "moveit_py is required for MoveItBackend. "
                "Use MockMoveItBackend without MoveIt installed."
            ) from exc

        self._moveit = MoveItPy(node_name="prompt_to_robot_moveit")
        self._arm = self._moveit.get_planning_component(self.config.planning_group)

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            if tool_name == "move_to":
                return self._move_to(arguments)
            if tool_name == "pick":
                return self._pick(arguments)
            if tool_name == "place":
                return self._place(arguments)
            if tool_name == "wait":
                time.sleep(float(arguments.get("seconds", 1.0)))
                return {"success": True, "message": "waited"}
            return {"success": False, "error": f"Unsupported tool for MoveIt: {tool_name}"}
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc)}

    def _move_to(self, args: dict[str, Any]) -> dict[str, Any]:
        self._arm.set_start_state_to_current_state()
        # TODO: set pose goal from args and plan/execute
        return {
            "success": True,
            "message": f"[MoveIt] move_to planned (stub execute) {args}",
            "pipeline": ["plan", "execute"],
        }

    def _pick(self, args: dict[str, Any]) -> dict[str, Any]:
        object_id = args.get("object_id")
        pipeline = [
            self._stage_pre_grasp(object_id),
            self._stage_approach(object_id),
            self._stage_close_gripper(),
            self._stage_retreat(),
        ]
        ok = all(s.get("success") for s in pipeline)
        return {
            "success": ok,
            "message": f"[MoveIt] pick pipeline for {object_id}",
            "holding": object_id if ok else None,
            "pipeline": pipeline,
        }

    def _place(self, args: dict[str, Any]) -> dict[str, Any]:
        pipeline = [
            self._stage_approach_place(args),
            self._stage_open_gripper(),
            self._stage_retreat(),
        ]
        ok = all(s.get("success") for s in pipeline)
        return {
            "success": ok,
            "message": f"[MoveIt] place pipeline at {args}",
            "pipeline": pipeline,
        }

    def _stage_pre_grasp(self, object_id: str | None) -> dict[str, Any]:
        return {"stage": "pre_grasp", "success": True, "object_id": object_id}

    def _stage_approach(self, object_id: str | None) -> dict[str, Any]:
        return {"stage": "approach", "success": True, "object_id": object_id}

    def _stage_close_gripper(self) -> dict[str, Any]:
        return {"stage": "close_gripper", "success": True}

    def _stage_open_gripper(self) -> dict[str, Any]:
        return {"stage": "open_gripper", "success": True}

    def _stage_retreat(self) -> dict[str, Any]:
        return {"stage": "retreat", "success": True}

    def _stage_approach_place(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"stage": "approach_place", "success": True, "args": args}

    def shutdown(self) -> None:
        pass
