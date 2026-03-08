from __future__ import annotations

import cv2
import numpy as np


class LaneDetector:
    """Detects lane regions based on fixed or auto-generated ROIs."""

    def __init__(self, lane_count: int = 3, lane_coords: list[tuple[int, int, int, int]] | None = None) -> None:
        if lane_count not in (2, 3, 4):
            raise ValueError("lane_count must be 2, 3, or 4")
        self.lane_count = lane_count
        self.lane_coords: list[tuple[int, int, int, int]] = list(lane_coords or [])

    def set_lane_coords(self, coords: list[tuple[int, int, int, int]]) -> None:
        """Set explicit lane bounding boxes as (x, y, w, h)."""
        self.lane_coords = [(int(x), int(y), int(w), int(h)) for x, y, w, h in coords]

    def auto_configure(
        self,
        frame_shape: tuple[int, ...],
        board_left_ratio: float = 0.1,
        board_right_ratio: float = 0.9,
        board_top_ratio: float = 0.3,
        board_bottom_ratio: float = 0.75,
    ) -> list[tuple[int, int, int, int]]:
        """Auto-generate lane regions from frame size ratios."""
        height, width = frame_shape[:2]

        board_left = int(width * board_left_ratio)
        board_right = int(width * board_right_ratio)
        board_top = int(height * board_top_ratio)
        board_bottom = int(height * board_bottom_ratio)

        board_width = max(1, board_right - board_left)
        lane_width = max(1, board_width // self.lane_count)
        lane_height = max(1, board_bottom - board_top)

        coords: list[tuple[int, int, int, int]] = []
        for lane_index in range(self.lane_count):
            x = board_left + lane_index * lane_width
            if lane_index == self.lane_count - 1:
                w = board_right - x
            else:
                w = lane_width
            coords.append((x, board_top, w, lane_height))

        self.lane_coords = coords
        return coords

    def get_lane_boxes(self) -> list[tuple[int, int, int, int]]:
        """Return current lane bounding boxes."""
        return list(self.lane_coords)

    def get_lanes(self, frame: np.ndarray) -> list[np.ndarray]:
        """Crop and return lane images in lane order."""
        lanes: list[np.ndarray] = []
        for x, y, w, h in self.lane_coords:
            lanes.append(frame[y : y + h, x : x + w])
        return lanes

    def extract_lane_regions(self, frame: np.ndarray) -> list[tuple[tuple[int, int, int, int], np.ndarray]]:
        """Return (bbox, crop) tuples for each lane."""
        return [((x, y, w, h), frame[y : y + h, x : x + w]) for x, y, w, h in self.lane_coords]

    def draw_lane_boxes(
        self,
        frame: np.ndarray,
        color: tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2,
    ) -> np.ndarray:
        """Draw lane boxes for debugging."""
        vis = frame.copy()
        for x, y, w, h in self.lane_coords:
            cv2.rectangle(vis, (x, y), (x + w, y + h), color, thickness)
        return vis


# TODO: replace ratio-based ROIs with runtime calibration from UI anchors.
