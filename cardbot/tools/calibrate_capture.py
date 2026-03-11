"""Interactive calibration tool for CardBot vision profiles."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from cardbot.capture.screen_capture import ScreenCapture
from cardbot.run_multi import compute_grid_regions, get_monitor_bounds
from cardbot.vision.profile import save_vision_profile


class CalibrationUI:
    """OpenCV UI for clicking and dragging ROIs."""

    def __init__(self, image: np.ndarray, title: str, num_lanes: int) -> None:
        self.image = image.copy()
        self.display_image = image.copy()
        self.title = title
        self.num_lanes = num_lanes

        self.state_queue = []
        for i in range(num_lanes):
            self.state_queue.append(("lane_target", i))
        self.state_queue.append(("end_turn_target", 0))
        self.state_queue.append(("turn_roi", 0))
        for i in range(num_lanes):
            self.state_queue.append(("lane_coord", i))
        self.state_queue.append(("window_anchor_roi", 0))

        self.results: dict[str, Any] = {
            "lane_targets": [],
            "end_turn_target": None,
            "turn_roi": None,
            "lane_coords": [],
            "window_anchor_roi": None,
        }

        self.drawing = False
        self.start_pt = (-1, -1)
        self.current_pt = (-1, -1)
        self.done = False

    def get_prompt(self) -> str:
        if not self.state_queue:
            return "Done! Press ESC to finish."

        state_type, index = self.state_queue[0]
        if state_type == "lane_target":
            return f"Click center of Lane {index} target area"
        if state_type == "end_turn_target":
            return "Click 'End Turn' button"
        if state_type == "turn_roi":
            return "Drag rectangle for Turn Indicator ROI"
        if state_type == "lane_coord":
            return f"Drag rectangle for Lane {index} cards ROI"
        if state_type == "window_anchor_roi":
            return "Drag rectangle for Window Anchor (static UI)"
        return ""

    def update_display(self) -> None:
        self.display_image = self.image.copy()

        # Draw previous results
        for pt in self.results["lane_targets"]:
            cv2.circle(self.display_image, tuple(pt), 5, (0, 255, 0), -1)
        if self.results["end_turn_target"]:
            cv2.circle(self.display_image, tuple(self.results["end_turn_target"]), 5, (0, 0, 255), -1)
        if self.results["turn_roi"]:
            x, y, w, h = self.results["turn_roi"]
            cv2.rectangle(self.display_image, (x, y), (x + w, y + h), (255, 255, 0), 2)
        for roi in self.results["lane_coords"]:
            x, y, w, h = roi
            cv2.rectangle(self.display_image, (x, y), (x + w, y + h), (255, 0, 255), 2)
        if self.results["window_anchor_roi"]:
            x, y, w, h = self.results["window_anchor_roi"]
            cv2.rectangle(self.display_image, (x, y), (x + w, y + h), (0, 255, 255), 2)

        prompt = self.get_prompt()
        cv2.putText(self.display_image, prompt, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4)
        cv2.putText(self.display_image, prompt, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        if self.drawing:
            x1, y1 = self.start_pt
            x2, y2 = self.current_pt
            cv2.rectangle(self.display_image, (x1, y1), (x2, y2), (0, 0, 255), 1)

        cv2.imshow(self.title, self.display_image)

    def mouse_callback(self, event: int, x: int, y: int, flags: int, param: Any) -> None:
        if self.done or not self.state_queue:
            return

        state_type, index = self.state_queue[0]
        is_click_mode = state_type in ("lane_target", "end_turn_target")

        if event == cv2.EVENT_LBUTTONDOWN:
            if is_click_mode:
                if state_type == "lane_target":
                    self.results["lane_targets"].append([x, y])
                elif state_type == "end_turn_target":
                    self.results["end_turn_target"] = [x, y]
                self.state_queue.pop(0)
            else:
                self.drawing = True
                self.start_pt = (x, y)
                self.current_pt = (x, y)

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                self.current_pt = (x, y)

        elif event == cv2.EVENT_LBUTTONUP:
            if self.drawing:
                self.drawing = False
                self.current_pt = (x, y)
                x1, y1 = self.start_pt
                x2, y2 = self.current_pt
                x_min, x_max = min(x1, x2), max(x1, x2)
                y_min, y_max = min(y1, y2), max(y1, y2)

                roi = (x_min, y_min, x_max - x_min, y_max - y_min)

                if roi[2] > 5 and roi[3] > 5:
                    if state_type == "turn_roi":
                        self.results["turn_roi"] = list(roi)
                    elif state_type == "lane_coord":
                        self.results["lane_coords"].append(list(roi))
                    elif state_type == "window_anchor_roi":
                        self.results["window_anchor_roi"] = list(roi)
                    self.state_queue.pop(0)

                if not self.state_queue:
                    self.done = True

        self.update_display()

    def run(self) -> dict[str, Any]:
        cv2.namedWindow(self.title)
        cv2.setMouseCallback(self.title, self.mouse_callback)
        self.update_display()
        
        while not self.done and self.state_queue:
            key = cv2.waitKey(50)
            if key == 27:  # ESC
                print("[CALIBRATE] Aborted by user.")
                sys.exit(1)

        self.update_display()
        print(f"[CALIBRATE] Instance finished. Press ESC to continue to next or exit.")
        while True:
            key = cv2.waitKey(50)
            if key == 27:
                break
                
        cv2.destroyWindow(self.title)
        return self.results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calibrate vision profiles for multi-instance.")
    parser.add_argument("--instances", type=int, default=4)
    parser.add_argument("--rows", type=int, default=2)
    parser.add_argument("--cols", type=int, default=2)
    parser.add_argument("--padding", type=int, default=0)
    parser.add_argument("--monitor-index", type=int, default=1)
    parser.add_argument("--lanes", type=int, default=3)
    parser.add_argument("--out-dir", type=str, default="cardbot/data/profiles")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    mon_bounds = get_monitor_bounds(args.monitor_index)
    regions = compute_grid_regions(
        left=mon_bounds[0],
        top=mon_bounds[1],
        width=mon_bounds[2],
        height=mon_bounds[3],
        rows=args.rows,
        cols=args.cols,
        padding=max(0, args.padding),
    )[: args.instances]

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for i, region in enumerate(regions):
        left, top, width, height = region
        mss_region = {"left": left, "top": top, "width": width, "height": height}
        print(f"[CALIBRATE] Capturing Instance {i} region: {mss_region}")

        capture = ScreenCapture(monitor_index=args.monitor_index, region=mss_region)
        frame = capture.grab_frame()
        capture.close()

        ui = CalibrationUI(frame, f"Calibration: Instance {i}", args.lanes)
        results = ui.run()

        profile = {
            "lane_coords": results["lane_coords"],
            "turn_roi": results["turn_roi"],
            "lane_targets": results["lane_targets"],
            "end_turn_target": results["end_turn_target"],
            "window_anchor_roi": results["window_anchor_roi"],
            "turn_threshold": 0.82,
            "card_match_threshold": 0.82,
            "card_edge_ratio_threshold": 0.02,
        }

        if results["window_anchor_roi"]:
            ax, ay, aw, ah = results["window_anchor_roi"]
            anchor_img = frame[ay : ay + ah, ax : ax + aw]
            profile["window_anchor_template"] = anchor_img

        out_path = out_dir / f"instance_{i}.json"
        save_vision_profile(out_path, profile)
        print(f"[CALIBRATE] Saved profile for instance {i} to {out_path}")


if __name__ == "__main__":
    main()
