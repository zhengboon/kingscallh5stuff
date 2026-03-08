from __future__ import annotations

import cv2
import numpy as np
import pytesseract


class OCRReader:
    """Simple OCR helper for reading numeric UI values."""

    def __init__(
        self,
        config: str = "--psm 7 -c tessedit_char_whitelist=0123456789",
        resize_factor: int = 2,
    ) -> None:
        self.config = config
        self.resize_factor = max(1, int(resize_factor))

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Apply lightweight preprocessing to improve OCR quality."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if self.resize_factor > 1:
            gray = cv2.resize(
                gray,
                None,
                fx=self.resize_factor,
                fy=self.resize_factor,
                interpolation=cv2.INTER_CUBIC,
            )
        blur = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    def read_text(self, image: np.ndarray) -> str:
        """Read raw OCR text from image."""
        processed = self.preprocess(image)
        try:
            return pytesseract.image_to_string(processed, config=self.config).strip()
        except pytesseract.TesseractNotFoundError:
            return ""

    def read_number(self, image: np.ndarray) -> int | None:
        """Read first integer from image, or None."""
        text = self.read_text(image)
        digits = "".join(ch for ch in text if ch.isdigit())
        if not digits:
            return None
        return int(digits)


# TODO: add OCR batching to reduce per-frame overhead.
