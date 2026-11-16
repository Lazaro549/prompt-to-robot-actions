"""
MoveIt 2 bridge for arm pick / place / move_to.

- MockMoveItBackend: pure Python, for agent development without MoveIt
- MoveItBackend: skeleton that calls MoveIt via moveit_py / action clients

Wire this behind GazeboROS2Backend or use it as a dedicated arm backend.
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


@dataclass
class MockArmState:
    joints: list[float] = field(default_factory=lambda: [0.0] * 6)
    ee_pose: dict[str, float] = field(
        default_factory=lambda: {"x": 0.3, "y": 0.0, "z": 0.4}
    )
    gripper_open: bool = True
    holding: str | None = None


class MockMoveItBackend:
    """Simulates MoveIt planning + gripper without ROS."""

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
            return {
                "success": True,
                "message": f"[MoveIt-mock] Planned & moved EE to {self.state.ee_pose}",
                "ee_pose": self.state.ee_pose.copy(),
            }

        if tool_name == "pick":
            if self.state.holding:
                return {"success": False, "error": f"Already holding {self.state.holding}"}
            object_id = arguments["object_id"]
            # pre-grasp → close
            self.state.gripper_open = False
            self.state.holding = object_id
            return {
                "success": True,
                "message": f"[MoveIt-mock] Pick sequence complete for {object_id}",
                "holding": object_id,
            }

        if tool_name == "place":
            if not self.state.holding:
                return {"success": False, "error": "Nothing to place"}
            placed = self.state.holding
            self.state.ee_pose = {
                "x": float(arguments.get("x", self.state.ee_pose["x"])),
                "y": float(arguments.get("y", self.state.ee_pose["y"])),
                "z": float(arguments.get("z", 0.15)),
            }
            self.state.gripper_open = True
            self.state.holding = None
            return {
                "success": True,
                "message": f"[MoveIt-mock] Placed {placed} at {self.state.ee_pose}",
                "placed": placed,
            }

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

    def get_state(self) -> dict[str, Any]:
        return {
            "ee_pose": self.state.ee_pose.copy(),
            "gripper_open": self.state.gripper_open,
            "holding": self.state.holding,
        }


class MoveItBackend:
    """
    Real MoveIt 2 backend (skeleton).

    Requires a sourced ROS 2 workspace with MoveIt 2 and your robot's
    moveit_config package. Uses moveit_py when available.
    """

    def __init__(self, config: MoveItConfig | None = None):
        self.config = config or MoveItConfig()
        self._moveit = None
        self._init_moveit()

    def _init_moveit(self) -> None:
        try:
            # moveit_py is the preferred ROS 2 Python API (Humble+)
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
        # Pseudocode for moveit_py pose goal — adapt to your API version
        self._arm.set_start_state_to_current_state()
        # pose_goal = ... build PoseStamped from args
        # self._arm.set_goal_state(pose_stamped_msg=pose_goal)
        # plan = self._arm.plan()
        # self._moveit.execute(plan.trajectory, controllers=[])
        return {
            "success": True,
            "message": f"[MoveIt] move_to planned (stub execute) {args}",
        }

    def _pick(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "success": True,
            "message": f"[MoveIt] pick sequence for {args.get('object_id')} (stub)",
            "holding": args.get("object_id"),
        }

    def _place(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "success": True,
            "message": f"[MoveIt] place at {args} (stub)",
        }

    def shutdown(self) -> None:
        pass
