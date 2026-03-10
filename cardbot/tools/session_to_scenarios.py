"""Export reusable environment scenarios from CardBot JSONL session logs."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Iterable


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Export CardBot scenarios from session logs")
    parser.add_argument("path", type=str, help="Path to a .jsonl file or a directory of logs")
    parser.add_argument(
        "--output",
        type=str,
        default="cardbot/data/scenarios/observed_scenarios.json",
        help="Output JSON file path",
    )
    parser.add_argument(
        "--max-scenarios",
        type=int,
        default=200,
        help="Maximum scenarios to export",
    )
    parser.add_argument(
        "--my-turn-only",
        action="store_true",
        help="Keep only frames where my_turn was true",
    )
    parser.add_argument(
        "--include-empty",
        action="store_true",
        help="Include states with no creatures on board",
    )
    return parser.parse_args()


def iter_logs(path: Path) -> list[Path]:
    """Collect input log files."""
    if path.is_file():
        return [path]
    if not path.exists():
        return []
    return sorted(path.rglob("*.jsonl"))


def _count_creatures_in_state(state: dict[str, Any]) -> int:
    lanes = state.get("lanes", [])
    if not isinstance(lanes, list):
        return 0
    total = 0
    for lane in lanes:
        if not isinstance(lane, dict):
            continue
        for owner in ("player", "enemy"):
            if lane.get(owner) is not None:
                total += 1
    return total


def _state_key(state: dict[str, Any]) -> str:
    """Create a deterministic hashable key for deduplication."""
    return json.dumps(state, sort_keys=True, separators=(",", ":"))


def iter_frame_records(file_path: Path) -> Iterable[tuple[dict[str, Any], dict[str, Any]]]:
    """Yield (meta, frame) records from one session log."""
    meta: dict[str, Any] = {}
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue
        payload = json.loads(raw_line)
        if payload.get("type") == "meta":
            meta = payload
            continue
        if payload.get("type") == "frame":
            yield meta, payload


def build_scenarios(
    logs: list[Path],
    max_scenarios: int,
    my_turn_only: bool,
    include_empty: bool,
) -> list[dict[str, Any]]:
    """Extract unique, reconstructable states from frame records."""
    scenarios: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for file_path in logs:
        for meta, frame in iter_frame_records(file_path):
            state = frame.get("state")
            if not isinstance(state, dict):
                continue

            if my_turn_only and not bool(frame.get("my_turn", False)):
                continue

            if not include_empty and _count_creatures_in_state(state) <= 0:
                continue

            key = _state_key(state)
            if key in seen_keys:
                continue
            seen_keys.add(key)

            frame_id = int(frame.get("frame", 0))
            scenario = {
                "id": f"{file_path.stem}_f{frame_id}",
                "source_log": str(file_path),
                "source_mode": meta.get("mode", "unknown"),
                "frame": frame_id,
                "t": frame.get("t"),
                "my_turn": bool(frame.get("my_turn", False)),
                "lane_detections": frame.get("lane_detections", []),
                "suggestion": frame.get("suggestion"),
                "state_snapshot": state,
            }
            scenarios.append(scenario)

            if len(scenarios) >= max_scenarios:
                return scenarios

    return scenarios


def main() -> None:
    """Entry point."""
    args = parse_args()
    input_path = Path(args.path)
    logs = iter_logs(input_path)

    if not logs:
        print("No session logs found.")
        raise SystemExit(1)

    scenarios = build_scenarios(
        logs=logs,
        max_scenarios=max(1, int(args.max_scenarios)),
        my_turn_only=bool(args.my_turn_only),
        include_empty=bool(args.include_empty),
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "created_at": time.time(),
        "source_path": str(input_path),
        "scenario_count": len(scenarios),
        "my_turn_only": bool(args.my_turn_only),
        "include_empty": bool(args.include_empty),
        "scenarios": scenarios,
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"logs_scanned={len(logs)}")
    print(f"scenarios_exported={len(scenarios)}")
    print(f"output={output_path}")


if __name__ == "__main__":
    main()

