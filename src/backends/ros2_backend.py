"""
ROS 2 backend adapter.

Provides:
- A clean interface that matches SimulatorBackend.execute()
- A MockROS2Backend for development without a ROS 2 installation
- A real ROS2Backend skeleton (requires rclpy + a running ROS 2 graph)

Design goal: the rest of the pipeline never needs to know whether it is
talking to the simulator, a mock, or real ROS 2.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ROS2Config:
    """Configuration for the real ROS 2 backend."""
    node_name: str = "prompt_to_robot_actions"
    move_topic: str = "/robot/move_to"
    pick_service: str = "/robot/pick"
    place_service: str = "/robot/place"
    navigate_action: str = "/navigate_to_pose"
    timeout_sec: float = 10.0


class MockROS2Backend:
    """
    Drop-in replacement that pretends to talk to ROS 2.

    Useful for testing the agent loop and logging without installing ROS.
    """

    def __init__(self):
        self.published: list[dict[str, Any]] = []
        self.position = {"x": 0.0, "y": 0.0, "z": 0.3}
        self.holding: str | None = None

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.published.append({"tool": tool_name, "args": arguments, "ts": time.time()})

        if tool_name == "move_to":
            self.position = {
                "x": float(arguments["x"]),
                "y": float(arguments["y"]),
                "z": float(arguments["z"]),
            }
            return {
                "success": True,
                "message": f"[ROS2-mock] Published move_to {self.position}",
                "position": self.position.copy(),
            }

        if tool_name == "pick":
            if self.holding:
                return {"success": False, "error": f"Already holding {self.holding}"}
            self.holding = arguments["object_id"]
            return {
                "success": True,
                "message": f"[ROS2-mock] pick service called for {self.holding}",
                "holding": self.holding,
            }

        if tool_name == "place":
            if not self.holding:
                return {"success": False, "error": "Nothing to place"}
            placed = self.holding
            self.holding = None
            return {
                "success": True,
                "message": f"[ROS2-mock] place service called for {placed}",
                "placed": placed,
            }

        if tool_name == "navigate":
            loc = arguments.get("location") or f"({arguments.get('x')}, {arguments.get('y')})"
            return {
                "success": True,
                "message": f"[ROS2-mock] navigate action to {loc}",
            }

        if tool_name == "inspect":
            return {
                "success": True,
                "message": f"[ROS2-mock] inspect {arguments.get('target')}",
                "observation": {"status": "ok"},
            }

        if tool_name == "wait":
            return {
                "success": True,
                "message": f"[ROS2-mock] waited {arguments.get('seconds', 1)}s",
            }

        return {"success": False, "error": f"Unknown tool: {tool_name}"}

    def get_state(self) -> dict[str, Any]:
        return {
            "position": self.position.copy(),
            "holding": self.holding,
            "published_count": len(self.published),
        }


class ROS2Backend:
    """
    Real ROS 2 backend (skeleton).

    Requires a working ROS 2 installation and rclpy.
    This class shows the intended integration points; fill in the
    publishers / clients according to your robot's topics and services.
    """

    def __init__(self, config: ROS2Config | None = None):
        self.config = config or ROS2Config()
        self._node = None
        self._init_ros()

    def _init_ros(self) -> None:
        try:
            import rclpy
            from rclpy.node import Node
        except ImportError as exc:
            raise ImportError(
                "rclpy is required for the real ROS2Backend. "
                "Use MockROS2Backend for development without ROS 2."
            ) from exp

        rclpy.init(args=None)
        self._node = Node(self.config.node_name)
        # TODO: create publishers / service clients / action clients here
        # Example:
        # self._move_pub = self._node.create_publisher(PoseStamped, self.config.move_topic, 10)

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Map high-level tools to ROS 2 topics / services / actions.

        Replace the stubs below with real publish / call_async logic.
        """
        if tool_name == "move_to":
            # publish PoseStamped or call a MoveTo service
            return {
                "success": True,
                "message": f"[ROS2] move_to published (stub) {arguments}",
            }

        if tool_name == "pick":
            return {
                "success": True,
                "message": f"[ROS2] pick service called (stub) {arguments}",
            }

        if tool_name == "place":
            return {
                "success": True,
                "message": f"[ROS2] place service called (stub) {arguments}",
            }

        if tool_name == "navigate":
            return {
                "success": True,
                "message": f"[ROS2] navigate action sent (stub) {arguments}",
            }

        if tool_name == "inspect":
            return {
                "success": True,
                "message": f"[ROS2] inspect (stub) {arguments}",
                "observation": {"status": "ok"},
            }

        if tool_name == "wait":
            time.sleep(float(arguments.get("seconds", 1.0)))
            return {"success": True, "message": "waited"}

        return {"success": False, "error": f"Unknown tool: {tool_name}"}

    def shutdown(self) -> None:
        if self._node is not None:
            self._node.destroy_node()
            try:
                import rclpy
                rclpy.shutdown()
            except Exception:
                pass
