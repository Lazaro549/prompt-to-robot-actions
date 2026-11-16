"""
Vision module: detect objects and return structured observations
so the multi-turn agent (Claude) can replan.

- MockDetector: returns synthetic detections (no camera needed)
- ROSCameraDetector: skeleton that subscribes to sensor_msgs/Image
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Detection:
    object_id: str
    label: str
    confidence: float
    x: float
    y: float
    z: float = 0.1

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_id": self.object_id,
            "label": self.label,
            "confidence": self.confidence,
            "position": {"x": self.x, "y": self.y, "z": self.z},
        }


@dataclass
class VisionObservation:
    timestamp: float
    detections: list[Detection] = field(default_factory=list)
    raw_note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "detections": [d.to_dict() for d in self.detections],
            "note": self.raw_note,
        }

    def summary_for_llm(self) -> str:
        if not self.detections:
            return "No objects detected."
        parts = [
            f"{d.label} (id={d.object_id}, conf={d.confidence:.2f}) "
            f"at ({d.x:.2f}, {d.y:.2f}, {d.z:.2f})"
            for d in self.detections
        ]
        return "Detected: " + "; ".join(parts)


class MockDetector:
    """
    Synthetic scene for demos and agent tests.

    Scene: red_cube on table, blue_cube nearby, empty floor zone.
    """

    def __init__(self):
        self._scene = [
            Detection("red_cube", "red cube", 0.94, 1.5, 0.5, 0.1),
            Detection("blue_cube", "blue cube", 0.91, 1.7, 0.4, 0.1),
        ]
        self._removed: set[str] = set()

    def detect(self, target: str | None = None) -> VisionObservation:
        dets = [d for d in self._scene if d.object_id not in self._removed]
        if target:
            t = target.lower()
            dets = [
                d
                for d in dets
                if t in d.label.lower() or t in d.object_id.lower() or t == "current_area"
            ]
            if t == "current_area":
                dets = [d for d in self._scene if d.object_id not in self._removed]
        return VisionObservation(
            timestamp=time.time(),
            detections=dets,
            raw_note="mock_detector",
        )

    def mark_picked(self, object_id: str) -> None:
        self._removed.add(object_id)

    def mark_placed(self, object_id: str, x: float, y: float, z: float = 0.1) -> None:
        self._removed.discard(object_id)
        for d in self._scene:
            if d.object_id == object_id:
                d.x, d.y, d.z = x, y, z
                break


class ROSCameraDetector:
    """
    Skeleton: subscribe to /camera/image_raw and run a detector.

    Plug in YOLO / Detectron / your model in process_image().
    """

    def __init__(self, image_topic: str = "/camera/image_raw"):
        self.image_topic = image_topic
        self._node = None
        self._last_image = None
        self._init_ros()

    def _init_ros(self) -> None:
        try:
            import rclpy
            from sensor_msgs.msg import Image
            from rclpy.node import Node
        except ImportError as exc:
            raise ImportError(
                "rclpy required for ROSCameraDetector. Use MockDetector otherwise."
            ) from exc

        if not rclpy.ok():
            rclpy.init(args=None)
        self._node = Node("prompt_to_robot_vision")
        self._node.create_subscription(Image, self.image_topic, self._on_image, 10)

    def _on_image(self, msg: Any) -> None:
        self._last_image = msg

    def process_image(self, msg: Any) -> list[Detection]:
        """Replace with real model inference."""
        # Example: convert ROS Image → numpy → YOLO → Detection list
        return []

    def detect(self, target: str | None = None) -> VisionObservation:
        import rclpy

        rclpy.spin_once(self._node, timeout_sec=0.5)
        dets: list[Detection] = []
        if self._last_image is not None:
            dets = self.process_image(self._last_image)
        if target and target != "current_area":
            t = target.lower()
            dets = [d for d in dets if t in d.label.lower() or t in d.object_id.lower()]
        return VisionObservation(
            timestamp=time.time(),
            detections=dets,
            raw_note=f"ros_camera:{self.image_topic}",
        )

    def shutdown(self) -> None:
        if self._node is not None:
            self._node.destroy_node()
