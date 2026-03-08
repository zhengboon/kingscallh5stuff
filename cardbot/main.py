"""Main automation loop for capture -> vision -> state -> action -> execution."""

from __future__ import annotations

import argparse
import time

import cv2

from cardbot.agents.heuristic_agent import HeuristicAgent
from cardbot.agents.random_agent import RandomAgent
from cardbot.capture.screen_capture import ScreenCapture
from cardbot.controller.input_controller import InputController
from cardbot.engine.game_state import GameState
from cardbot.vision.card_detector import CardDetector
from cardbot.vision.debug_overlay import DebugOverlay
from cardbot.vision.lane_detector import LaneDetector
from cardbot.vision.ocr_reader import OCRReader
from cardbot.vision.turn_detector import TurnDetector


def ensure_minimum_hand(state: GameState, owner: str = "player", minimum_cards: int = 1) -> None:
    """Draw cards until the owner has at least `minimum_cards` cards."""
    hand = state.get_hand(owner)
    while len(hand) < minimum_cards and state.cards_db:
        next_card = sorted(state.cards_db.keys())[len(hand) % len(state.cards_db)]
        state.draw_card(owner, next_card)


def sync_state_from_vision(
    state: GameState,
    lane_card_presence: list[bool],
    default_enemy_card_id: str | None,
) -> None:
    """Project lane card detections into the internal engine state.

    This keeps an approximate mirror until full card identity + OCR integration is added.
    """
    if default_enemy_card_id is None:
        return

    for lane_index, card_present in enumerate(lane_card_presence):
        lane = state.lanes[lane_index]
        enemy_creature = lane.get_creature("enemy")

        if card_present and enemy_creature is None:
            try:
                state.summon_creature("enemy", lane_index, default_enemy_card_id)
            except ValueError:
                pass

        if not card_present and enemy_creature is not None:
            lane.remove_creature("enemy")
            state.history.append(f"vision_remove:enemy:lane={lane_index}")


def build_agent(agent_name: str):
    """Create agent instance by CLI option."""
    if agent_name == "random":
        return RandomAgent(seed=42)
    return HeuristicAgent()


def parse_args() -> argparse.Namespace:
    """Parse CLI options."""
    parser = argparse.ArgumentParser(description="Cardbot automation loop")
    parser.add_argument("--lanes", type=int, default=3, choices=[2, 3, 4], help="Number of board lanes")
    parser.add_argument(
        "--agent",
        type=str,
        default="heuristic",
        choices=["heuristic", "random"],
        help="Action policy to use",
    )
    parser.add_argument("--target-fps", type=float, default=30.0, help="Target perception FPS")
    parser.add_argument("--debug-window", action="store_true", help="Show OpenCV debug window")
    parser.add_argument(
        "--max-frames",
        type=int,
        default=0,
        help="Stop after N frames; 0 means run forever",
    )
    return parser.parse_args()


def main() -> None:
    """Run the end-to-end automation loop."""
    args = parse_args()

    capture = ScreenCapture()
    first_frame = capture.grab_frame()

    lane_detector = LaneDetector(lane_count=args.lanes)
    lane_detector.auto_configure(first_frame.shape)

    card_detector = CardDetector()
    turn_detector = TurnDetector()
    ocr_reader = OCRReader()  # Placeholder, used when numeric ROI mapping is added.
    overlay = DebugOverlay(fps_window=30)

    controller = InputController()
    agent = build_agent(args.agent)

    state = GameState.from_data_files(num_lanes=args.lanes)
    ensure_minimum_hand(state, owner="player", minimum_cards=3)
    ensure_minimum_hand(state, owner="enemy", minimum_cards=3)
    default_enemy_card_id = sorted(state.cards_db.keys())[0] if state.cards_db else None

    target_frame_time = 1.0 / max(1.0, float(args.target_fps))
    frame_count = 0

    try:
        while args.max_frames <= 0 or frame_count < args.max_frames:
            tick_start = time.perf_counter()

            frame = capture.grab_frame()
            lane_images = lane_detector.get_lanes(frame)
            lane_detections = card_detector.detect_cards_with_scores(lane_images)
            lane_presence = [present for present, _ in lane_detections]
            my_turn = turn_detector.is_my_turn(frame)

            # TODO: map fixed ROIs and use OCR to read HP/countdown per lane with `ocr_reader`.
            _ = ocr_reader

            sync_state_from_vision(
                state=state,
                lane_card_presence=lane_presence,
                default_enemy_card_id=default_enemy_card_id,
            )

            if my_turn and not state.is_terminal():
                ensure_minimum_hand(state, owner="player", minimum_cards=1)
                action = agent.select_action(state, owner="player")
                state.take_turn("player", action)
                controller.execute_action(action)

            debug_frame = overlay.draw_lane_boxes(frame, lane_detector.get_lane_boxes())
            debug_frame = overlay.draw_card_presence(
                debug_frame,
                lane_detector.get_lane_boxes(),
                lane_detections,
            )
            debug_frame = overlay.draw_fps(debug_frame)

            if args.debug_window:
                cv2.imshow("cardbot-debug", debug_frame)
                if cv2.waitKey(1) & 0xFF == 27:
                    break

            frame_count += 1
            elapsed = time.perf_counter() - tick_start
            sleep_time = target_frame_time - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    finally:
        capture.close()
        if args.debug_window:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
