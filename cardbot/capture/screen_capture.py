from __future__ import annotations

from typing import Any

import mss
import numpy as np


class ScreenCapture:
    """High-throughput screen capture helper backed by MSS."""

    def __init__(self, monitor_index: int = 1, region: dict[str, int] | None = None) -> None:
        self._sct = mss.mss()
        self.monitor_index = monitor_index
        self._full_monitor = self._resolve_monitor(monitor_index)
        self.region = self._resolve_region(region)

    def _resolve_monitor(self, monitor_index: int) -> dict[str, Any]:
        monitors = self._sct.monitors
        if monitor_index < 1 or monitor_index >= len(monitors):
            return monitors[1]
        return monitors[monitor_index]

    def _resolve_region(self, region: dict[str, int] | None) -> dict[str, int]:
        if region is None:
            return {
                "left": int(self._full_monitor["left"]),
                "top": int(self._full_monitor["top"]),
                "width": int(self._full_monitor["width"]),
                "height": int(self._full_monitor["height"]),
            }

        return {
            "left": int(region["left"]),
            "top": int(region["top"]),
            "width": int(region["width"]),
            "height": int(region["height"]),
        }

    def set_region(self, region: dict[str, int]) -> None:
        """Update capture region."""
        self.region = self._resolve_region(region)

    def grab_frame(self) -> np.ndarray:
        """Capture one BGR frame."""
        raw = np.array(self._sct.grab(self.region), dtype=np.uint8)
        return raw[:, :, :3]

    def close(self) -> None:
        """Release MSS resources."""
        self._sct.close()

    def __enter__(self) -> "ScreenCapture":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


# TODO: add optional frame buffering if multi-threaded pipelines are introduced.
