"""
Vision module: detect objects and return structured observations
so the multi-turn agent (Claude) can replan.

- MockDetector: synthetic detections
- ROSCameraDetector: ROS image + YOLO-style process_image hook
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable


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
            if t != "current_area":
                dets = [
                    d
                    for d in dets
                    if t in d.label.lower() or t in d.object_id.lower()
                ]
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


def _default_yolo_infer(_bgr_image: Any) -> list[dict[str, Any]]:
    """
    Placeholder YOLO inference.

    Replace with ultralytics YOLO:
        from ultralytics import YOLO
        model = YOLO("yolov8n.pt")
        results = model(bgr_image)
        ...
    Return list of dicts: label, confidence, xyxy or xyz.
    """
    return []


class ROSCameraDetector:
    """
    Subscribe to sensor_msgs/Image and run a pluggable detector (YOLO by default hook).
    """

    def __init__(
        self,
        image_topic: str = "/camera/image_raw",
        infer_fn: Callable[[Any], list[dict[str, Any]]] | None = None,
    ):
        self.image_topic = image_topic
        self.infer_fn = infer_fn or _default_yolo_infer
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

    def _ros_image_to_bgr(self, msg: Any) -> Any:
        """Convert sensor_msgs/Image to numpy BGR if cv_bridge / numpy available."""
        try:
            import numpy as np
            from cv_bridge import CvBridge

            return CvBridge().imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception:
            return None

    def process_image(self, msg: Any) -> list[Detection]:
        bgr = self._ros_image_to_bgr(msg)
        if bgr is None:
            return []
        raw = self.infer_fn(bgr)
        detections: list[Detection] = []
        for i, item in enumerate(raw):
            label = str(item.get("label", f"obj_{i}"))
            detections.append(
                Detection(
                    object_id=str(item.get("object_id", label.replace(" ", "_"))),
                    label=label,
                    confidence=float(item.get("confidence", 0.5)),
                    x=float(item.get("x", 0.0)),
                    y=float(item.get("y", 0.0)),
                    z=float(item.get("z", 0.1)),
                )
            )
        return detections

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
            raw_note=f"ros_camera_yolo:{self.image_topic}",
        )

    def shutdown(self) -> None:
        if self._node is not None:
            self._node.destroy_node()
