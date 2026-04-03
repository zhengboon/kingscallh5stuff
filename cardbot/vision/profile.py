from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import cv2

from cardbot.controller.input_controller import InputController
from cardbot.vision.card_detector import CardDetector
from cardbot.vision.lane_detector import LaneDetector
from cardbot.vision.turn_detector import TurnDetector

logger = logging.getLogger(__name__)


def load_vision_profile(profile_path: str | Path | None) -> dict[str, Any]:
    """Load vision profile JSON and its associated anchor image if it exists.

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

    # Load associated anchor image if configured
    if "window_anchor_roi" in payload:
        anchor_path = path.parent / f"{path.stem}_anchor.png"
        if anchor_path.exists():
            image = cv2.imread(str(anchor_path))
            if image is not None:
                payload["window_anchor_template"] = image
            else:
                logger.warning("Failed to decode anchor image at %s", anchor_path)
        else:
            logger.warning("Anchor image not found at %s", anchor_path)

    return payload


def save_vision_profile(profile_path: str | Path, profile: dict[str, Any]) -> Path:
    """Save a vision profile JSON to disk."""
    path = Path(profile_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract anchor image if present and remove it from JSON payload
    # Make a copy to avoid mutating the user's dictionary
    payload = dict(profile)
    anchor_template = payload.pop("window_anchor_template", None)
    
    if anchor_template is not None:
        import numpy as np
        if isinstance(anchor_template, np.ndarray):
            anchor_path = path.parent / f"{path.stem}_anchor.png"
            cv2.imwrite(str(anchor_path), anchor_template)
            logger.info("Saved anchor image -> %s", anchor_path)

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def apply_vision_profile(
    profile: dict[str, Any],
    lane_detector: LaneDetector,
    turn_detector: TurnDetector,
    card_detector: CardDetector,
    input_controller: InputController | None = None,
) -> None:
    """Apply profile values to runtime vision components and controllers."""
    if not profile:
        return

    lane_coords_raw = profile.get("lane_coords")
    if isinstance(lane_coords_raw, list) and lane_coords_raw:
        lane_coords: list[tuple[int, int, int, int]] = []
        for item in lane_coords_raw:
            if not isinstance(item, (list, tuple)) or len(item) != 4:
                continue
            x, y, w, h = item
            lane_coords.append((int(x), int(y), int(w), int(h)))
        if lane_coords:
            lane_detector.set_lane_coords(lane_coords)

    turn_roi_raw = profile.get("turn_roi")
    if isinstance(turn_roi_raw, (list, tuple)) and len(turn_roi_raw) == 4:
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

    if input_controller:
        lane_targets_raw = profile.get("lane_targets")
        if isinstance(lane_targets_raw, list) and lane_targets_raw:
            targets = {}
            for i, item in enumerate(lane_targets_raw):
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    targets[i] = (int(item[0]), int(item[1]))
            input_controller.set_lane_targets(targets)
            
        end_turn = profile.get("end_turn_target")
        if isinstance(end_turn, (list, tuple)) and len(end_turn) == 2:
            input_controller.set_end_turn_target((int(end_turn[0]), int(end_turn[1])))
