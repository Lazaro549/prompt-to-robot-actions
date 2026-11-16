"""
ROS 2 + Gazebo backend.

Maps high-level robot tools (move_to, pick, place, navigate, inspect, wait)
to common ROS 2 interfaces used with Gazebo simulations:

- geometry_msgs/Twist          → /cmd_vel
- geometry_msgs/PoseStamped    → navigation goals
- std_srvs / custom services   → pick / place (gripper)
- sensor_msgs / vision topics  → inspect (optional)

Two modes:
1. MockGazeboBackend  — no ROS required, for unit tests and demos
2. GazeboROS2Backend  — real rclpy node (needs ROS 2 + Gazebo running)

Typical stack this targets:
  Gazebo Harmonic / Fortress + ros_gz_bridge + Nav2 (optional) + a mobile
  manipulator or mobile base (TurtleBot4, Clearpath, custom URDF, etc.).
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GazeboROS2Config:
    """Topic / service names used with a typical Gazebo + ROS 2 robot."""

    node_name: str = "prompt_to_robot_gazebo"

    # Mobile base
    cmd_vel_topic: str = "/cmd_vel"
    odom_topic: str = "/odom"

    # Navigation (Nav2)
    navigate_action: str = "/navigate_to_pose"
    goal_pose_topic: str = "/goal_pose"

    # Arm / gripper (adjust to your robot)
    move_arm_topic: str = "/arm_controller/joint_trajectory"
    gripper_service: str = "/gripper/command"

    # Vision / inspect
    camera_topic: str = "/camera/image_raw"

    # Timing
    move_duration_sec: float = 1.5
    timeout_sec: float = 30.0
    frame_id: str = "map"


# ---------------------------------------------------------------------------
# Mock (no ROS installation required)
# ---------------------------------------------------------------------------


@dataclass
class MockGazeboState:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    yaw: float = 0.0
    holding: str | None = None
    history: list[dict[str, Any]] = field(default_factory=list)


class MockGazeboBackend:
    """
    Simulates a Gazebo robot in pure Python.

    Useful for developing the agent loop and logging without launching
    Gazebo or ROS 2.
    """

    def __init__(self, config: GazeboROS2Config | None = None):
        self.config = config or GazeboROS2Config()
        self.state = MockGazeboState()

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        handler = getattr(self, f"_handle_{tool_name}", None)
        if handler is None:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        result = handler(arguments)
        self.state.history.append({"tool": tool_name, "args": arguments, "result": result})
        return result

    def _handle_move_to(self, args: dict[str, Any]) -> dict[str, Any]:
        self.state.x = float(args["x"])
        self.state.y = float(args["y"])
        self.state.z = float(args.get("z", self.state.z))
        return {
            "success": True,
            "message": f"[Gazebo-mock] Moved base/EE to ({self.state.x:.2f}, {self.state.y:.2f}, {self.state.z:.2f})",
            "position": {"x": self.state.x, "y": self.state.y, "z": self.state.z},
        }

    def _handle_navigate(self, args: dict[str, Any]) -> dict[str, Any]:
        if "location" in args and args["location"]:
            # Named waypoints for the mock world
            waypoints = {
                "home": (0.0, 0.0),
                "table": (1.5, 0.5),
                "kitchen": (2.0, 1.0),
                "charging_station": (-1.0, 0.0),
            }
            loc = args["location"]
            if loc not in waypoints:
                return {"success": False, "error": f"Unknown location: {loc}"}
            self.state.x, self.state.y = waypoints[loc]
            return {
                "success": True,
                "message": f"[Gazebo-mock] Navigated to '{loc}' ({self.state.x}, {self.state.y})",
                "position": {"x": self.state.x, "y": self.state.y},
            }

        self.state.x = float(args.get("x", self.state.x))
        self.state.y = float(args.get("y", self.state.y))
        return {
            "success": True,
            "message": f"[Gazebo-mock] Navigated to ({self.state.x}, {self.state.y})",
            "position": {"x": self.state.x, "y": self.state.y},
        }

    def _handle_pick(self, args: dict[str, Any]) -> dict[str, Any]:
        if self.state.holding:
            return {"success": False, "error": f"Already holding {self.state.holding}"}
        self.state.holding = args["object_id"]
        return {
            "success": True,
            "message": f"[Gazebo-mock] Picked {self.state.holding} (gripper closed)",
            "holding": self.state.holding,
        }

    def _handle_place(self, args: dict[str, Any]) -> dict[str, Any]:
        if not self.state.holding:
            return {"success": False, "error": "Nothing to place"}
        placed = self.state.holding
        self.state.holding = None
        self.state.x = float(args.get("x", self.state.x))
        self.state.y = float(args.get("y", self.state.y))
        self.state.z = float(args.get("z", 0.1))
        return {
            "success": True,
            "message": f"[Gazebo-mock] Placed {placed} at ({self.state.x}, {self.state.y}, {self.state.z})",
            "placed": placed,
        }

    def _handle_inspect(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "success": True,
            "message": f"[Gazebo-mock] Inspected {args.get('target')} via camera",
            "observation": {
                "target": args.get("target"),
                "sensor": args.get("sensor", "camera"),
                "status": "ok",
                "note": "In real Gazebo this would sample /camera/image_raw",
            },
        }

    def _handle_wait(self, args: dict[str, Any]) -> dict[str, Any]:
        seconds = float(args.get("seconds", 1.0))
        time.sleep(min(seconds, 0.05))  # don't block tests
        return {"success": True, "message": f"[Gazebo-mock] Waited {seconds}s"}

    def get_state(self) -> dict[str, Any]:
        return {
            "x": self.state.x,
            "y": self.state.y,
            "z": self.state.z,
            "yaw": self.state.yaw,
            "holding": self.state.holding,
            "history_len": len(self.state.history),
        }


# ---------------------------------------------------------------------------
# Real ROS 2 + Gazebo backend
# ---------------------------------------------------------------------------


class GazeboROS2Backend:
    """
    Real backend that talks to a Gazebo simulation through ROS 2.

    Prerequisites (on the machine that runs this code):
      - ROS 2 (Humble / Iron / Jazzy)
      - Gazebo (Fortress or Harmonic) + ros_gz_bridge / gazebo_ros packages
      - A robot spawned in Gazebo that exposes /cmd_vel (and optionally Nav2)

    Launch example (see ros2_ws/ for launch files):
      ros2 launch prompt_to_robot_gazebo gazebo_sim.launch.py
    """

    def __init__(self, config: GazeboROS2Config | None = None):
        self.config = config or GazeboROS2Config()
        self._node = None
        self._cmd_vel_pub = None
        self._goal_pub = None
        self._init_ros()

    def _init_ros(self) -> None:
        try:
            import rclpy
            from geometry_msgs.msg import Twist, PoseStamped
            from rclpy.node import Node
        except ImportError as exc:
            raise ImportError(
                "rclpy and geometry_msgs are required for GazeboROS2Backend.\n"
                "Use MockGazeboBackend for development without ROS 2 / Gazebo.\n"
                "Install ROS 2 and source your workspace first."
            ) from exc

        if not rclpy.ok():
            rclpy.init(args=None)

        self._node = Node(self.config.node_name)
        self._cmd_vel_pub = self._node.create_publisher(Twist, self.config.cmd_vel_topic, 10)
        self._goal_pub = self._node.create_publisher(PoseStamped, self.config.goal_pose_topic, 10)
        self._Twist = Twist
        self._PoseStamped = PoseStamped

        self._node.get_logger().info(
            f"GazeboROS2Backend ready | cmd_vel={self.config.cmd_vel_topic} "
            f"| goal_pose={self.config.goal_pose_topic}"
        )

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        handler = getattr(self, f"_ros_{tool_name}", None)
        if handler is None:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        try:
            return handler(arguments)
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc), "tool": tool_name}

    # ---- tool handlers -----------------------------------------------------

    def _ros_move_to(self, args: dict[str, Any]) -> dict[str, Any]:
        """
        Approximate move_to for a mobile base using /cmd_vel.

        For a manipulator, replace this with a joint trajectory or MoveIt goal.
        """
        # Simple open-loop drive toward (x, y) for a fixed duration.
        # A production system should use odometry feedback or Nav2.
        twist = self._Twist()
        # Very rough: publish a forward velocity; real code should compute heading.
        twist.linear.x = 0.2
        self._cmd_vel_pub.publish(twist)
        time.sleep(self.config.move_duration_sec)
        twist.linear.x = 0.0
        self._cmd_vel_pub.publish(twist)

        return {
            "success": True,
            "message": f"[Gazebo-ROS2] cmd_vel move toward ({args.get('x')}, {args.get('y')})",
            "note": "Open-loop; prefer navigate + Nav2 for closed-loop goals",
        }

    def _ros_navigate(self, args: dict[str, Any]) -> dict[str, Any]:
        """Publish a PoseStamped goal (works with Nav2 goal_pose or simple bridges)."""
        pose = self._PoseStamped()
        pose.header.frame_id = self.config.frame_id
        pose.header.stamp = self._node.get_clock().now().to_msg()

        if args.get("location"):
            # Map named locations to coordinates in your Gazebo world
            waypoints = {
                "home": (0.0, 0.0),
                "table": (1.5, 0.5),
                "kitchen": (2.0, 1.0),
                "charging_station": (-1.0, 0.0),
            }
            loc = args["location"]
            if loc not in waypoints:
                return {"success": False, "error": f"Unknown location: {loc}"}
            x, y = waypoints[loc]
        else:
            x = float(args.get("x", 0.0))
            y = float(args.get("y", 0.0))

        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.orientation.w = 1.0

        self._goal_pub.publish(pose)
        return {
            "success": True,
            "message": f"[Gazebo-ROS2] Published navigate goal to ({x}, {y})",
            "goal": {"x": x, "y": y, "frame": self.config.frame_id},
        }

    def _ros_pick(self, args: dict[str, Any]) -> dict[str, Any]:
        """
        Gripper close stub.

        Wire this to your gripper topic/service, e.g.:
          - /gripper_controller/gripper_cmd
          - a std_srvs/SetBool service
        """
        object_id = args.get("object_id", "object")
        # Placeholder: log and return success so the pipeline can continue.
        self._node.get_logger().info(f"PICK requested for {object_id}")
        return {
            "success": True,
            "message": f"[Gazebo-ROS2] Pick command sent for {object_id} (wire gripper service)",
            "holding": object_id,
        }

    def _ros_place(self, args: dict[str, Any]) -> dict[str, Any]:
        self._node.get_logger().info(f"PLACE requested at {args}")
        return {
            "success": True,
            "message": f"[Gazebo-ROS2] Place command sent (wire gripper open + arm goal)",
            "placed_at": {"x": args.get("x"), "y": args.get("y"), "z": args.get("z")},
        }

    def _ros_inspect(self, args: dict[str, Any]) -> dict[str, Any]:
        """
        In a full setup, subscribe once to camera_topic or call a vision service.
        Here we only acknowledge the request.
        """
        return {
            "success": True,
            "message": f"[Gazebo-ROS2] Inspect {args.get('target')} (subscribe to {self.config.camera_topic})",
            "observation": {"target": args.get("target"), "status": "ok"},
        }

    def _ros_wait(self, args: dict[str, Any]) -> dict[str, Any]:
        seconds = float(args.get("seconds", 1.0))
        time.sleep(seconds)
        return {"success": True, "message": f"[Gazebo-ROS2] Waited {seconds}s"}

    def spin_once(self) -> None:
        """Allow ROS callbacks to run (call periodically if needed)."""
        import rclpy

        rclpy.spin_once(self._node, timeout_sec=0.05)

    def shutdown(self) -> None:
        if self._node is not None:
            self._node.destroy_node()
            try:
                import rclpy

                if rclpy.ok():
                    rclpy.shutdown()
            except Exception:
                pass
