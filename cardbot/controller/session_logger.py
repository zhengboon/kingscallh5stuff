from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class SessionLogger:
    """JSONL logger for observation and suggestion traces.

    The logger is intentionally lightweight so it can run alongside a ~30 FPS
    perception loop while writing only sampled records.
    """

    def __init__(
        self,
        output_dir: str | Path,
        mode: str,
        log_fps: float = 5.0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.file_path = self.output_dir / f"session_{timestamp}_{mode}.jsonl"
        self._fp = self.file_path.open("w", encoding="utf-8")

        self._min_interval = 0.0 if log_fps <= 0 else 1.0 / float(log_fps)
        self._last_frame_log_at = 0.0

        self._write(
            {
                "type": "meta",
                "created_at": time.time(),
                "mode": mode,
                "log_fps": log_fps,
                "metadata": metadata or {},
            }
        )

    def _write(self, payload: dict[str, Any]) -> None:
        self._fp.write(json.dumps(payload, separators=(",", ":")) + "\n")
        self._fp.flush()

    def log_frame(
        self,
        frame_index: int,
        my_turn: bool,
        lane_detections: list[tuple[bool, float]],
        state_summary: dict[str, Any],
        suggestion: dict[str, Any] | None,
    ) -> None:
        """Log sampled frame-level perception and shadow-state information."""
        now = time.time()
        if self._min_interval > 0 and (now - self._last_frame_log_at) < self._min_interval:
            return
        self._last_frame_log_at = now

        self._write(
            {
                "type": "frame",
                "t": now,
                "frame": frame_index,
                "my_turn": my_turn,
                "lane_detections": [
                    {"present": bool(present), "confidence": round(float(conf), 4)}
                    for present, conf in lane_detections
                ],
                "state": state_summary,
                "suggestion": suggestion,
            }
        )

    def log_turn_event(
        self,
        event: str,
        action: dict[str, Any] | None,
        executed: bool,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Log turn boundary and action suggestion/execution events."""
        self._write(
            {
                "type": "turn_event",
                "t": time.time(),
                "event": event,
                "action": action,
                "executed": executed,
                "extra": extra or {},
            }
        )

    def close(self) -> None:
        """Close file handle."""
        if not self._fp.closed:
            self._fp.close()


# TODO: add a compact binary mode if longer sessions become I/O bound.
