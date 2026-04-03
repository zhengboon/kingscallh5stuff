from __future__ import annotations

import ctypes
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


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

    # Key constants
    KEYEVENTF_KEYUP = 0x0002
    VK_TAB = 0x09
    VK_RETURN = 0x0D
    VK_SHIFT = 0x10

    # Mapping for common chars to VK codes (basic set)
    _VK_MAP = {
        **{chr(i): i for i in range(0x41, 0x5B)}, # A-Z
        **{chr(i).lower(): i for i in range(0x41, 0x5B)}, # a-z
        **{str(i): 0x30 + i for i in range(10)}, # 0-9
        ":": 0xBA, ";": 0xBA, ".": 0xBE, "/": 0xBF, "@": 0x32, " ": 0x20
    }

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
        logger.debug("click local(%d, %d) -> global(%d, %d)", x, y, gx, gy)

        try:
            ctypes.windll.user32.SetCursorPos(gx, gy)
            time.sleep(0.02)
            ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.05)
            ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            time.sleep(0.02)
        except OSError:
            logger.exception("Win32 click failed at global(%d, %d)", gx, gy)

    def drag(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.2) -> None:
        """Execute a drag action from (x1,y1) to (x2,y2) over duration seconds."""
        gx1, gy1 = self._to_global(x1, y1)
        gx2, gy2 = self._to_global(x2, y2)
        logger.debug("drag global(%d, %d) -> (%d, %d) duration=%.2fs", gx1, gy1, gx2, gy2, duration)

        try:
            ctypes.windll.user32.SetCursorPos(gx1, gy1)
            time.sleep(0.05)
            ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)

            steps = int(max(10, duration * 60))
            sleep_per_step = duration / steps
            for i in range(1, steps + 1):
                t = i / steps
                cx = int(gx1 + (gx2 - gx1) * t)
                cy = int(gy1 + (gy2 - gy1) * t)
                ctypes.windll.user32.SetCursorPos(cx, cy)
                time.sleep(sleep_per_step)

            time.sleep(0.05)
            ctypes.windll.user32.mouse_event(self.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            time.sleep(0.02)
        except OSError:
            logger.exception("Win32 drag failed")

    def type_text(self, text: str, delay: float = 0.05) -> None:
        """Type a string into the focused window using keyboard events."""
        masked = text.replace(text[1:-1], '***') if len(text) > 4 else '***'
        logger.debug("typing: %s", masked)

        for char in text:
            # Map char to keyboard scan code or virtual key
            # For simplicity, we use SendUnicode to handle everything correctly
            self._send_char(char)
            if delay > 0:
                time.sleep(delay)

    def _send_char(self, char: str) -> None:
        """Simulate a single character keydown/keyup."""
        # We use SendInput via ctypes for Unicode if possible, 
        # but for this environment, simple keybd_event works for basic ASCII.
        # Shift handling for symbols/uppercase:
        needs_shift = char.isupper() or char in "!@#$%^&*()_+{}|:\"<>?~"
        
        vk = self._VK_MAP.get(char, 0x20) # Space if unknown
        if needs_shift:
            ctypes.windll.user32.keybd_event(self.VK_SHIFT, 0, 0, 0)
            
        ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.01)
        ctypes.windll.user32.keybd_event(vk, 0, self.KEYEVENTF_KEYUP, 0)
        
        if needs_shift:
            ctypes.windll.user32.keybd_event(self.VK_SHIFT, 0, self.KEYEVENTF_KEYUP, 0)

    def type_enter(self) -> None:
        ctypes.windll.user32.keybd_event(self.VK_RETURN, 0, 0, 0)
        time.sleep(0.01)
        ctypes.windll.user32.keybd_event(self.VK_RETURN, 0, self.KEYEVENTF_KEYUP, 0)

    def type_tab(self) -> None:
        ctypes.windll.user32.keybd_event(self.VK_TAB, 0, 0, 0)
        time.sleep(0.01)
        ctypes.windll.user32.keybd_event(self.VK_TAB, 0, self.KEYEVENTF_KEYUP, 0)

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
                logger.warning("skip summon lane=%d (target not configured)", lane_index)

        elif action_type == "attack":
            lane_index = int(action.get("lane", -1))
            if lane_index in self.lane_targets:
                x, y = self.lane_targets[lane_index]
                self.click(int(x), int(y))
            else:
                logger.warning("skip attack lane=%d (target not configured)", lane_index)

        elif action_type == "end_turn":
            if self.end_turn_target is not None:
                x, y = self.end_turn_target
                self.click(int(x), int(y))
            else:
                logger.warning("skip end_turn (target not configured)")

        else:
            logger.warning("unknown action: %s", action)

        if self.action_delay > 0:
            time.sleep(self.action_delay)

