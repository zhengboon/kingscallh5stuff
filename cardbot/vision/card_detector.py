from __future__ import annotations

import cv2
import numpy as np

from cardbot.vision.template_matcher import TemplateMatcher


class CardDetector:
    """Detects card presence in lane crops using templates + edge density."""

    # Multiplier to convert raw edge ratio (typically 0.0–0.05) into a 0–1 confidence score.
    EDGE_CONFIDENCE_SCALE = 30.0

    def __init__(
        self,
        templates: list[np.ndarray] | None = None,
        match_threshold: float = 0.82,
        edge_ratio_threshold: float = 0.02,
    ) -> None:
        self.templates: list[np.ndarray] = list(templates or [])
        self.match_threshold = float(match_threshold)
        self.edge_ratio_threshold = float(edge_ratio_threshold)
        self.matcher = TemplateMatcher()

    def set_templates(self, templates: list[np.ndarray]) -> None:
        """Set card templates used by template matching."""
        self.templates = list(templates)

    def add_template(self, template: np.ndarray) -> None:
        """Add one card template image."""
        self.templates.append(template)

    def detect(self, lane_image: np.ndarray) -> tuple[bool, float]:
        """Return (is_present, confidence) for one lane image."""
        if lane_image is None or lane_image.size == 0:
            return False, 0.0

        best_template_score = 0.0
        for template in self.templates:
            score, _ = self.matcher.match_best(lane_image, template)
            if score > best_template_score:
                best_template_score = score

        gray = cv2.cvtColor(lane_image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 75, 150)
        edge_ratio = float(np.count_nonzero(edges)) / float(edges.size)

        edge_confidence = min(1.0, edge_ratio * self.EDGE_CONFIDENCE_SCALE)
        confidence = max(best_template_score, edge_confidence)

        is_present = best_template_score >= self.match_threshold or edge_ratio >= self.edge_ratio_threshold
        return is_present, confidence

    def detect_cards(self, lane_images: list[np.ndarray]) -> list[bool]:
        """Return presence flags for all lane images."""
        return [self.detect(image)[0] for image in lane_images]

    def detect_cards_with_scores(self, lane_images: list[np.ndarray]) -> list[tuple[bool, float]]:
        """Return detection flags with confidence scores."""
        return [self.detect(image) for image in lane_images]


# TODO: extend to multi-class card ID classification by template bank.
