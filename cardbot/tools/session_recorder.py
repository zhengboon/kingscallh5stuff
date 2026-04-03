"""Live session recorder — captures screenshots and logs during gameplay.

Usage as standalone:
    python -m cardbot.tools.session_recorder --output analysis/live_sessions --interval 2.0

Also importable for GUI integration.
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    import mss
    import mss.tools
except ImportError:
    mss = None  # type: ignore[assignment]


class SessionRecorder:
    """Background thread that periodically captures screenshots and logs."""

    # Stop recording if free disk space drops below this threshold (bytes).
    MIN_FREE_DISK_BYTES = 100 * 1024 * 1024  # 100 MB

    def __init__(
        self,
        output_root: str | Path = "analysis/live_sessions",
        interval: float = 2.0,
        region: dict[str, int] | None = None,
    ):
        self.output_root = Path(output_root)
        self.interval = max(0.5, interval)
        self.region = region  # {"left": x, "top": y, "width": w, "height": h}

        self._running = False
        self._thread: threading.Thread | None = None
        self._session_dir: Path | None = None
        self._screenshot_dir: Path | None = None
        self._log_path: Path | None = None
        self._frame_count = 0
        self._start_time: float = 0.0
        self._log_lines: list[str] = []
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @property
    def session_dir(self) -> Path | None:
        return self._session_dir

    @property
    def log_lines(self) -> list[str]:
        with self._lock:
            return list(self._log_lines)

    def _append_log(self, entry: dict[str, Any]) -> None:
        line = json.dumps(entry, ensure_ascii=False)
        with self._lock:
            self._log_lines.append(line)
        if self._log_path:
            with open(self._log_path, "a", encoding="utf-8") as fp:
                fp.write(line + "\n")

    def start(self) -> Path:
        """Start a new recording session. Returns session directory."""
        if self._running:
            raise RuntimeError("Session already running")
        if mss is None:
            raise ImportError("mss is required for screen capture")

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self._session_dir = self.output_root / ts
        self._screenshot_dir = self._session_dir / "screenshots"
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)
        self._log_path = self._session_dir / "capture_log.jsonl"
        self._frame_count = 0
        self._start_time = time.time()
        with self._lock:
            self._log_lines.clear()

        self._append_log({
            "event": "session_start",
            "timestamp": time.time(),
            "interval": self.interval,
            "region": self.region,
        })

        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        return self._session_dir

    def stop(self) -> dict[str, Any]:
        """Stop the recording session. Returns summary."""
        if not self._running:
            return {}
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None

        elapsed = time.time() - self._start_time
        summary = {
            "event": "session_end",
            "timestamp": time.time(),
            "frames_captured": self._frame_count,
            "duration_sec": round(elapsed, 2),
            "session_dir": str(self._session_dir),
        }
        self._append_log(summary)
        return summary

    def _capture_loop(self) -> None:
        """Main capture loop running in background thread."""
        try:
            with mss.mss() as sct:
                monitors = sct.monitors
                if self.region:
                    monitor = self.region
                elif len(monitors) > 1:
                    monitor = monitors[1]  # Primary display
                else:
                    monitor = monitors[0]

                while self._running:
                    t0 = time.time()
                    try:
                        free = shutil.disk_usage(self._session_dir).free
                        if free < self.MIN_FREE_DISK_BYTES:
                            logger.warning("Disk space low (%d MB free), stopping recorder", free // (1024 * 1024))
                            self._append_log({"event": "disk_space_low", "timestamp": t0, "free_bytes": free})
                            self._running = False
                            break

                        screenshot = sct.grab(monitor)
                        self._frame_count += 1
                        fname = f"frame_{self._frame_count:06d}.png"
                        fpath = self._screenshot_dir / fname
                        mss.tools.to_png(screenshot.rgb, screenshot.size, output=str(fpath))

                        self._append_log({
                            "event": "frame",
                            "frame": self._frame_count,
                            "timestamp": t0,
                            "file": fname,
                            "size": [screenshot.width, screenshot.height],
                        })
                    except Exception as exc:
                        self._append_log({
                            "event": "capture_error",
                            "timestamp": t0,
                            "error": str(exc),
                        })

                    # Sleep for remaining interval
                    elapsed = time.time() - t0
                    sleep_time = max(0.0, self.interval - elapsed)
                    if sleep_time > 0 and self._running:
                        time.sleep(sleep_time)
        except Exception as exc:
            self._append_log({
                "event": "fatal_error",
                "timestamp": time.time(),
                "error": str(exc),
            })
            self._running = False


def main() -> None:
    parser = argparse.ArgumentParser(description="KingsCall live session recorder")
    parser.add_argument("--output", type=str, default="analysis/live_sessions")
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--duration", type=float, default=60.0, help="Recording duration in seconds")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    recorder = SessionRecorder(output_root=args.output, interval=args.interval)
    session = recorder.start()
    logger.info("Started -> %s", session)
    try:
        time.sleep(args.duration)
    except KeyboardInterrupt:
        pass
    summary = recorder.stop()
    logger.info("Done -> %d frames in %ss", summary.get('frames_captured', 0), summary.get('duration_sec', 0))


if __name__ == "__main__":
    main()
