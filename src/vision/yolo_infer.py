"""
Optional YOLO inference helper (ultralytics).

Install: pip install -e ".[yolo]"

Usage with ROSCameraDetector:
    from src.vision.yolo_infer import make_yolo_infer
    from src.vision import ROSCameraDetector
    det = ROSCameraDetector(infer_fn=make_yolo_infer("yolov8n.pt"))
"""

from __future__ import annotations

from typing import Any, Callable


def make_yolo_infer(model_name: str = "yolov8n.pt") -> Callable[[Any], list[dict[str, Any]]]:
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise ImportError('Install YOLO extra: pip install -e ".[yolo]"') from exc

    model = YOLO(model_name)

    def infer(bgr_image: Any) -> list[dict[str, Any]]:
        results = model(bgr_image, verbose=False)
        out: list[dict[str, Any]] = []
        for r in results:
            names = r.names or {}
            boxes = getattr(r, "boxes", None)
            if boxes is None:
                continue
            for box in boxes:
                cls_id = int(box.cls[0]) if box.cls is not None else 0
                conf = float(box.conf[0]) if box.conf is not None else 0.0
                label = str(names.get(cls_id, f"class_{cls_id}"))
                xyxy = box.xyxy[0].tolist() if box.xyxy is not None else [0, 0, 0, 0]
                cx = (xyxy[0] + xyxy[2]) / 2.0
                cy = (xyxy[1] + xyxy[3]) / 2.0
                out.append(
                    {
                        "label": label,
                        "object_id": label.replace(" ", "_"),
                        "confidence": conf,
                        "x": cx,
                        "y": cy,
                        "z": 0.1,
                    }
                )
        return out

    return infer
