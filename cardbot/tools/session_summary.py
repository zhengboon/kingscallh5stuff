"""Summarize CardBot JSONL session logs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Summarize cardbot session log(s)")
    parser.add_argument("path", type=str, help="Path to a .jsonl file or directory")
    return parser.parse_args()


def iter_logs(path: Path) -> list[Path]:
    """Collect log files from path."""
    if path.is_file():
        return [path]
    if not path.exists():
        return []
    return sorted(path.rglob("*.jsonl"))


def summarize_file(file_path: Path) -> dict[str, object]:
    """Build summary metrics for one session JSONL file."""
    meta: dict = {}
    frame_count = 0
    turn_events = 0
    suggestions = 0
    executed_actions = 0
    my_turn_frames = 0
    card_presence_total = 0
    card_presence_samples = 0

    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        payload = json.loads(raw_line)
        record_type = payload.get("type")

        if record_type == "meta":
            meta = payload
            continue

        if record_type == "frame":
            frame_count += 1
            if bool(payload.get("my_turn", False)):
                my_turn_frames += 1
            lane_detections = payload.get("lane_detections", [])
            for lane in lane_detections:
                card_presence_total += 1 if lane.get("present") else 0
                card_presence_samples += 1
            if payload.get("suggestion") is not None:
                suggestions += 1
            continue

        if record_type == "turn_event":
            turn_events += 1
            if bool(payload.get("executed", False)):
                executed_actions += 1

    card_presence_ratio = 0.0
    if card_presence_samples > 0:
        card_presence_ratio = card_presence_total / card_presence_samples

    return {
        "file": str(file_path),
        "mode": meta.get("mode", "-"),
        "frames": frame_count,
        "turn_events": turn_events,
        "suggestions": suggestions,
        "executed_actions": executed_actions,
        "my_turn_frames": my_turn_frames,
        "card_presence_ratio": round(card_presence_ratio, 4),
    }


def main() -> None:
    """Entry point."""
    args = parse_args()
    path = Path(args.path)
    logs = iter_logs(path)

    if not logs:
        print("No session logs found.")
        raise SystemExit(1)

    for file_path in logs:
        summary = summarize_file(file_path)
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
