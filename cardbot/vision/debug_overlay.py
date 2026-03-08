from __future__ import annotations

import time
from collections import deque

import cv2
import numpy as np


class DebugOverlay:
    """Draws lane, detection, and FPS information onto frames."""

    def __init__(self, fps_window: int = 30) -> None:
        self._frame_times: deque[float] = deque(maxlen=max(2, int(fps_window)))

    def _update_fps(self) -> float:
        now = time.perf_counter()
        self._frame_times.append(now)
        if len(self._frame_times) < 2:
            return 0.0
        duration = self._frame_times[-1] - self._frame_times[0]
        if duration <= 0:
            return 0.0
        return float((len(self._frame_times) - 1) / duration)

    def draw_lane_boxes(
        self,
        frame: np.ndarray,
        lane_boxes: list[tuple[int, int, int, int]],
    ) -> np.ndarray:
        """Draw lane rectangles and lane indices."""
        output = frame.copy()
        for lane_index, (x, y, w, h) in enumerate(lane_boxes):
            cv2.rectangle(output, (x, y), (x + w, y + h), (60, 200, 60), 2)
            cv2.putText(
                output,
                f"Lane {lane_index}",
                (x + 6, y + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (60, 200, 60),
                2,
            )
        return output

    def draw_card_presence(
        self,
        frame: np.ndarray,
        lane_boxes: list[tuple[int, int, int, int]],
        detections: list[tuple[bool, float]],
    ) -> np.ndarray:
        """Draw card detection flags and confidence for each lane."""
        output = frame.copy()
        for lane_index, (detected, confidence) in enumerate(detections):
            if lane_index >= len(lane_boxes):
                break
            x, y, _, _ = lane_boxes[lane_index]
            label = f"card={int(detected)} conf={confidence:.2f}"
            color = (0, 255, 255) if detected else (120, 120, 120)
            cv2.putText(output, label, (x + 6, y + 44), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        return output

    def draw_fps(self, frame: np.ndarray) -> np.ndarray:
        """Draw rolling FPS estimate."""
        output = frame.copy()
        fps = self._update_fps()
        cv2.putText(
            output,
            f"FPS: {fps:5.1f}",
            (12, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 180, 60),
            2,
        )
        return output


# TODO: include OCR readouts (HP/countdown) in lane annotations.
