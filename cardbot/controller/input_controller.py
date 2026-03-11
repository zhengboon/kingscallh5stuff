from __future__ import annotations

import ctypes
import time
from typing import Any


class InputController:
    """Translates high-level actions into input operations.

    Executes real OS-level mouse clicks via win32 API using the screen
    capture boundaries to map local image coordinates into global desktop coordinates.
    """

    # Windows API constants
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    SM_CXSCREEN = 0
    SM_CYSCREEN = 1

    def __init__(
        self,
        capture_region: dict[str, int] | None = None,
        lane_targets: dict[int, tuple[int, int]] | None = None,
        end_turn_target: tuple[int, int] | None = None,
        action_delay: float = 0.05,
    ) -> None:
        self.capture_region = capture_region.copy() if capture_region else {"left": 0, "top": 0}
        self.lane_targets = lane_targets.copy() if lane_targets else {}
        self.end_turn_target = end_turn_target
        self.action_delay = float(max(0.0, action_delay))
        self.action_log: list[dict[str, Any]] = []

    def set_lane_targets(self, lane_targets: dict[int, tuple[int, int]]) -> None:
        """Set click target coordinates by lane index."""
        self.lane_targets = lane_targets.copy() if lane_targets else {}

    def set_end_turn_target(self, target: tuple[int, int]) -> None:
        """Set click target for turn end button."""
        self.end_turn_target = target

    def _to_global(self, x: int, y: int) -> tuple[int, int]:
        """Convert local capture coordinates to global desktop coordinates."""
        gx = x + self.capture_region.get("left", 0)
        gy = y + self.capture_region.get("top", 0)
        return (gx, gy)

    def click(self, x: int, y: int) -> None:
        """Execute a left mouse click at the specified local coordinates."""
        gx, gy = self._to_global(x, y)
        print(f"[INPUT] click local({x}, {y}) -> global({gx}, {gy})")
        
        # Move cursor
        ctypes.windll.user32.SetCursorPos(gx, gy)
        time.sleep(0.02)
        
        # Mouse down
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.05)
        
        # Mouse up
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        time.sleep(0.02)

    def drag(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.2) -> None:
        """Execute a drag action from (x1,y1) to (x2,y2) over duration seconds."""
        gx1, gy1 = self._to_global(x1, y1)
        gx2, gy2 = self._to_global(x2, y2)
        print(f"[INPUT] drag global({gx1}, {gy1}) -> ({gx2}, {gy2}) duration={duration:.2f}s")
        
        # Move to start
        ctypes.windll.user32.SetCursorPos(gx1, gy1)
        time.sleep(0.05)
        
        # Mouse down
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        
        # Interpolate movement
        steps = int(max(10, duration * 60))  # approx 60hz
        sleep_per_step = duration / steps
        for i in range(1, steps + 1):
            t = i / steps
            cx = int(gx1 + (gx2 - gx1) * t)
            cy = int(gy1 + (gy2 - gy1) * t)
            ctypes.windll.user32.SetCursorPos(cx, cy)
            time.sleep(sleep_per_step)
            
        # Mouse up
        time.sleep(0.05)
        ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        time.sleep(0.02)

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
                self.click(int(x), int(y))
            else:
                print(f"[INPUT] skip summon lane={lane_index} (target not configured)")

        elif action_type == "attack":
            lane_index = int(action.get("lane", -1))
            if lane_index in self.lane_targets:
                x, y = self.lane_targets[lane_index]
                self.click(int(x), int(y))
            else:
                print(f"[INPUT] skip attack lane={lane_index} (target not configured)")

        elif action_type == "end_turn":
            if self.end_turn_target is not None:
                x, y = self.end_turn_target
                self.click(int(x), int(y))
            else:
                print("[INPUT] skip end_turn (target not configured)")

        else:
            print(f"[INPUT] unknown action: {action}")

        if self.action_delay > 0:
            time.sleep(self.action_delay)

