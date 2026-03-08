from __future__ import annotations

import cv2
import numpy as np

from cardbot.vision.template_matcher import TemplateMatcher


class TurnDetector:
    """Detects whether the player's turn indicator is visible."""

    def __init__(
        self,
        indicator_template: np.ndarray | None = None,
        threshold: float = 0.82,
        indicator_roi: tuple[int, int, int, int] | None = None,
    ) -> None:
        self.indicator_template = indicator_template
        self.threshold = float(threshold)
        self.indicator_roi = indicator_roi
        self.matcher = TemplateMatcher()

    def set_indicator(self, template: np.ndarray) -> None:
        """Set UI template for turn indicator."""
        self.indicator_template = template

    def set_roi(self, roi: tuple[int, int, int, int]) -> None:
        """Set ROI for faster turn detection."""
        self.indicator_roi = tuple(int(value) for value in roi)

    def _crop_roi(self, frame: np.ndarray) -> np.ndarray:
        if self.indicator_roi is None:
            return frame
        x, y, w, h = self.indicator_roi
        return frame[y : y + h, x : x + w]

    def _fallback_color_detection(self, frame: np.ndarray) -> bool:
        """Fallback heuristic using bright green indicator pixels."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower_green = np.array([35, 70, 70], dtype=np.uint8)
        upper_green = np.array([85, 255, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower_green, upper_green)
        green_ratio = float(np.count_nonzero(mask)) / float(mask.size)
        return green_ratio >= 0.01

    def is_my_turn(self, frame: np.ndarray) -> bool:
        """Return True when turn indicator is detected."""
        roi_frame = self._crop_roi(frame)

        if self.indicator_template is not None:
            return self.matcher.exists(roi_frame, self.indicator_template, threshold=self.threshold)

        return self._fallback_color_detection(roi_frame)


# TODO: support multiple indicator themes/skins via template set.
