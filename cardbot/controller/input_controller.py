from __future__ import annotations

import time
from typing import Any


class InputController:
    """Translates high-level actions into input operations.

    This baseline implementation logs placeholder click/drag calls.
    Replace internals with platform APIs when wiring real automation.
    """

    def __init__(
        self,
        lane_targets: dict[int, tuple[int, int]] | None = None,
        end_turn_target: tuple[int, int] | None = None,
        action_delay: float = 0.05,
    ) -> None:
        self.lane_targets = dict(lane_targets or {})
        self.end_turn_target = end_turn_target
        self.action_delay = max(0.0, float(action_delay))
        self.action_log: list[dict[str, Any]] = []

    def set_lane_targets(self, lane_targets: dict[int, tuple[int, int]]) -> None:
        """Set click target coordinates by lane index."""
        self.lane_targets = dict(lane_targets)

    def set_end_turn_target(self, target: tuple[int, int]) -> None:
        """Set click target for turn end button."""
        self.end_turn_target = target

    def click(self, x: int, y: int) -> None:
        """Placeholder click action."""
        print(f"[INPUT] click ({x}, {y})")

    def drag(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.2) -> None:
        """Placeholder drag action."""
        print(f"[INPUT] drag ({x1}, {y1}) -> ({x2}, {y2}) duration={duration:.2f}s")

    def execute_action(self, action: dict[str, Any] | None) -> None:
        """Execute one high-level game action."""
        if action is None:
            return

        self.action_log.append(dict(action))
        action_type = action.get("type")

        if action_type == "summon":
            lane_index = int(action.get("lane", -1))
            if lane_index in self.lane_targets:
                x, y = self.lane_targets[lane_index]
                self.click(x, y)
            else:
                print(f"[INPUT] summon lane={lane_index} (target not configured)")

        elif action_type == "attack":
            lane_index = int(action.get("lane", -1))
            if lane_index in self.lane_targets:
                x, y = self.lane_targets[lane_index]
                self.click(x, y)
            else:
                print(f"[INPUT] attack lane={lane_index} (target not configured)")

        elif action_type == "end_turn":
            if self.end_turn_target is not None:
                x, y = self.end_turn_target
                self.click(x, y)
            else:
                print("[INPUT] end_turn")

        else:
            print(f"[INPUT] unknown action: {action}")

        if self.action_delay > 0:
            time.sleep(self.action_delay)


# TODO: integrate real mouse/keyboard API for production automation.
