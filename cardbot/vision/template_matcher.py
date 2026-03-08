from __future__ import annotations

from typing import Any

import cv2
import numpy as np


class TemplateMatcher:
    """Utility class for OpenCV template matching operations."""

    def __init__(self, method: int = cv2.TM_CCOEFF_NORMED) -> None:
        self.method = method

    @staticmethod
    def _to_gray(image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            return image
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def match_best(self, image: np.ndarray, template: np.ndarray) -> tuple[float, tuple[int, int, int, int] | None]:
        """Return best match score and bounding box."""
        if image is None or template is None:
            return 0.0, None

        image_gray = self._to_gray(image)
        template_gray = self._to_gray(template)

        ih, iw = image_gray.shape[:2]
        th, tw = template_gray.shape[:2]
        if th > ih or tw > iw:
            return 0.0, None

        response = cv2.matchTemplate(image_gray, template_gray, self.method)
        _, max_val, _, max_loc = cv2.minMaxLoc(response)
        x, y = max_loc
        return float(max_val), (x, y, tw, th)

    def find_all(
        self,
        image: np.ndarray,
        template: np.ndarray,
        threshold: float = 0.8,
        max_results: int = 20,
    ) -> list[tuple[int, int, int, int, float]]:
        """Return all matches above threshold with simple deduping."""
        image_gray = self._to_gray(image)
        template_gray = self._to_gray(template)

        ih, iw = image_gray.shape[:2]
        th, tw = template_gray.shape[:2]
        if th > ih or tw > iw:
            return []

        response = cv2.matchTemplate(image_gray, template_gray, self.method)
        ys, xs = np.where(response >= threshold)

        candidates: list[tuple[int, int, int, int, float]] = []
        for y, x in zip(ys.tolist(), xs.tolist()):
            score = float(response[y, x])
            candidates.append((x, y, tw, th, score))

        candidates.sort(key=lambda item: item[4], reverse=True)

        accepted: list[tuple[int, int, int, int, float]] = []
        min_dist_sq = max(1, (min(tw, th) // 3) ** 2)
        for match in candidates:
            if len(accepted) >= max_results:
                break
            x, y, w, h, score = match

            too_close = False
            for ax, ay, _, _, _ in accepted:
                dx = x - ax
                dy = y - ay
                if dx * dx + dy * dy <= min_dist_sq:
                    too_close = True
                    break

            if not too_close:
                accepted.append((x, y, w, h, score))

        return accepted

    def exists(self, image: np.ndarray, template: np.ndarray, threshold: float = 0.8) -> bool:
        """True if best template match is above threshold."""
        score, _ = self.match_best(image=image, template=template)
        return score >= threshold


# TODO: add scale-invariant matching for multiple UI resolutions.
