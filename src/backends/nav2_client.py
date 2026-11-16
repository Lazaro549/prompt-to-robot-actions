"""
Nav2 action client helper for closed-loop navigation feedback.

Uses nav2_msgs/action/NavigateToPose when available.
Falls back to publishing /goal_pose if the action server is missing.
"""

from __future__ import annotations

import time
from typing import Any


class Nav2Client:
    """
    Thin wrapper around NavigateToPose.

    Example:
        client = Nav2Client()
        result = client.navigate_to(x=1.5, y=0.5)
    """

    def __init__(self, action_name: str = "navigate_to_pose", timeout_sec: float = 60.0):
        self.action_name = action_name
        self.timeout_sec = timeout_sec
        self._node = None
        self._client = None
        self._goal_pub = None
        self._init()

    def _init(self) -> None:
        try:
            import rclpy
            from geometry_msgs.msg import PoseStamped
            from rclpy.action import ActionClient
            from rclpy.node import Node
        except ImportError as exc:
            raise ImportError(
                "rclpy required for Nav2Client. Use MockGazeboBackend.navigate in tests."
            ) from exc

        if not rclpy.ok():
            rclpy.init(args=None)
        self._node = Node("ptra_nav2_client")
        self._PoseStamped = PoseStamped
        self._goal_pub = self._node.create_publisher(PoseStamped, "/goal_pose", 10)

        try:
            from nav2_msgs.action import NavigateToPose

            self._client = ActionClient(self._node, NavigateToPose, self.action_name)
            self._NavigateToPose = NavigateToPose
        except ImportError:
            self._client = None

    def navigate_to(
        self,
        x: float,
        y: float,
        yaw: float = 0.0,
        frame_id: str = "map",
    ) -> dict[str, Any]:
        pose = self._PoseStamped()
        pose.header.frame_id = frame_id
        pose.header.stamp = self._node.get_clock().now().to_msg()
        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)
        pose.pose.orientation.w = 1.0

        if self._client is None:
            self._goal_pub.publish(pose)
            return {
                "success": True,
                "message": f"Published /goal_pose ({x}, {y}) — Nav2 action not available",
                "mode": "topic",
            }

        if not self._client.wait_for_server(timeout_sec=5.0):
            self._goal_pub.publish(pose)
            return {
                "success": True,
                "message": f"Nav2 server not ready; published /goal_pose ({x}, {y})",
                "mode": "topic_fallback",
            }

        goal = self._NavigateToPose.Goal()
        goal.pose = pose
        send_future = self._client.send_goal_async(goal)
        import rclpy

        rclpy.spin_until_future_complete(self._node, send_future, timeout_sec=10.0)
        goal_handle = send_future.result()
        if not goal_handle or not goal_handle.accepted:
            return {"success": False, "error": "Nav2 goal rejected", "mode": "action"}

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(
            self._node, result_future, timeout_sec=self.timeout_sec
        )
        result = result_future.result()
        return {
            "success": True,
            "message": f"Nav2 NavigateToPose completed to ({x}, {y})",
            "mode": "action",
            "status": getattr(result, "status", None),
        }

    def shutdown(self) -> None:
        if self._node is not None:
            self._node.destroy_node()
