from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cardbot.vision.card_detector import CardDetector
from cardbot.vision.lane_detector import LaneDetector
from cardbot.vision.turn_detector import TurnDetector


def load_vision_profile(profile_path: str | Path | None) -> dict[str, Any]:
    """Load vision profile JSON.

    Returns an empty dictionary when profile_path is None or the file does not exist.
    """
    if profile_path is None:
        return {}

    path = Path(profile_path)
    if not path.exists():
        return {}

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Vision profile must be a JSON object")
    return payload


def save_vision_profile(profile_path: str | Path, profile: dict[str, Any]) -> Path:
    """Save a vision profile JSON to disk."""
    path = Path(profile_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return path


def apply_vision_profile(
    profile: dict[str, Any],
    lane_detector: LaneDetector,
    turn_detector: TurnDetector,
    card_detector: CardDetector,
) -> None:
    """Apply profile values to runtime vision components."""
    if not profile:
        return

    lane_coords_raw = profile.get("lane_coords")
    if isinstance(lane_coords_raw, list) and lane_coords_raw:
        lane_coords: list[tuple[int, int, int, int]] = []
        for item in lane_coords_raw:
            if not (isinstance(item, list) or isinstance(item, tuple)) or len(item) != 4:
                continue
            x, y, w, h = item
            lane_coords.append((int(x), int(y), int(w), int(h)))
        if lane_coords:
            lane_detector.set_lane_coords(lane_coords)

    turn_roi_raw = profile.get("turn_roi")
    if (isinstance(turn_roi_raw, list) or isinstance(turn_roi_raw, tuple)) and len(turn_roi_raw) == 4:
        x, y, w, h = turn_roi_raw
        turn_detector.set_roi((int(x), int(y), int(w), int(h)))

    turn_threshold = profile.get("turn_threshold")
    if turn_threshold is not None:
        turn_detector.threshold = float(turn_threshold)

    card_match_threshold = profile.get("card_match_threshold")
    if card_match_threshold is not None:
        card_detector.match_threshold = float(card_match_threshold)

    card_edge_ratio_threshold = profile.get("card_edge_ratio_threshold")
    if card_edge_ratio_threshold is not None:
        card_detector.edge_ratio_threshold = float(card_edge_ratio_threshold)


# TODO: support loading per-instance template images from profile file.
