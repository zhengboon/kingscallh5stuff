from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


class RuntimeStatusWriter:
    """Writes live runtime heartbeat files for UI monitoring."""

    def __init__(
        self,
        output_dir: str | Path,
        instance_id: int,
        mode: str,
        monitor_index: int,
        capture_region: dict[str, int] | None,
        write_fps: float = 2.0,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.instance_id = int(instance_id)
        self._write_interval = 0.0 if write_fps <= 0 else 1.0 / float(write_fps)
        self._last_write_at = 0.0

        self.path = self.output_dir / f"instance_{self.instance_id}.json"
        self._payload: dict[str, Any] = {
            "instance_id": self.instance_id,
            "pid": os.getpid(),
            "mode": mode,
            "monitor_index": int(monitor_index),
            "capture_region": capture_region,
            "running": True,
            "started_at": time.time(),
            "updated_at": time.time(),
            "frame_count": 0,
            "fps": 0.0,
            "my_turn": False,
            "last_action": None,
            "last_error": None,
        }
        self._write(force=True)

    def _write(self, force: bool = False) -> None:
        now = time.time()
        if not force and self._write_interval > 0 and (now - self._last_write_at) < self._write_interval:
            return
        self._last_write_at = now

        self._payload["updated_at"] = now

        temp_path = self.path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(self._payload, indent=2), encoding="utf-8")
        temp_path.replace(self.path)

    def update(
        self,
        frame_count: int,
        fps: float,
        my_turn: bool,
        last_action: dict[str, Any] | None,
        state_summary: dict[str, Any],
    ) -> None:
        """Update dynamic status fields and write heartbeat."""
        self._payload["frame_count"] = int(frame_count)
        self._payload["fps"] = round(float(fps), 2)
        self._payload["my_turn"] = bool(my_turn)
        self._payload["last_action"] = last_action
        self._payload["state"] = state_summary
        self._write(force=False)

    def set_error(self, error_text: str) -> None:
        """Record runtime error text in status payload."""
        self._payload["last_error"] = str(error_text)
        self._write(force=True)

    def close(self) -> None:
        """Mark instance as stopped and flush final status file."""
        self._payload["running"] = False
        self._payload["stopped_at"] = time.time()
        self._write(force=True)


# TODO: expose rolling stats (action rate, avg loop time) in status payload.
