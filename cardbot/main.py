"""Main automation loop for capture -> vision -> state -> action -> execution."""

from __future__ import annotations

import argparse
import logging
import time
from typing import Any

import cv2

logger = logging.getLogger(__name__)

from cardbot.agents.heuristic_agent import HeuristicAgent
from cardbot.agents.random_agent import RandomAgent
from cardbot.capture.screen_capture import ScreenCapture
from cardbot.controller.input_controller import InputController
from cardbot.controller.runtime_status import RuntimeStatusWriter
from cardbot.controller.session_logger import SessionLogger
from cardbot.engine.game_state import GameState
from cardbot.vision.card_detector import CardDetector
from cardbot.vision.debug_overlay import DebugOverlay
from cardbot.vision.lane_detector import LaneDetector
from cardbot.vision.ocr_reader import OCRReader
from cardbot.vision.profile import apply_vision_profile, load_vision_profile, save_vision_profile
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


def summarize_state(state: GameState) -> dict:
    """Create a reconstructable state snapshot for session logs."""
    return state.to_snapshot()


def parse_args() -> argparse.Namespace:
    """Parse CLI options."""
    parser = argparse.ArgumentParser(description="Cardbot automation loop")
    parser.add_argument("--instance-id", type=int, default=0, help="Logical bot instance ID")
    parser.add_argument("--monitor-index", type=int, default=1, help="MSS monitor index (default: primary)")
    parser.add_argument("--capture-left", type=int, default=None, help="Capture region left offset")
    parser.add_argument("--capture-top", type=int, default=None, help="Capture region top offset")
    parser.add_argument("--capture-width", type=int, default=None, help="Capture region width")
    parser.add_argument("--capture-height", type=int, default=None, help="Capture region height")
    parser.add_argument(
        "--vision-profile",
        type=str,
        default=None,
        help="Optional JSON profile path for lane/turn/card vision settings",
    )
    parser.add_argument(
        "--save-vision-profile",
        type=str,
        default=None,
        help="Save current auto/profile-adjusted vision settings to this JSON path",
    )
    parser.add_argument("--lanes", type=int, default=3, choices=[2, 3, 4], help="Number of board lanes")
    parser.add_argument(
        "--mode",
        type=str,
        default="observe",
        choices=["observe", "assist", "autoplay"],
        help="observe=watch+log, assist=watch+suggest, autoplay=watch+act",
    )
    parser.add_argument(
        "--agent",
        type=str,
        default="heuristic",
        choices=["heuristic", "random"],
        help="Action policy to use",
    )
    parser.add_argument("--target-fps", type=float, default=30.0, help="Target perception FPS")
    parser.add_argument("--log-fps", type=float, default=5.0, help="Session log sampling FPS")
    parser.add_argument(
        "--session-dir",
        type=str,
        default="cardbot/data/sessions",
        help="Directory for observation session logs",
    )
    parser.add_argument(
        "--status-dir",
        type=str,
        default="cardbot/data/runtime_status",
        help="Directory for runtime status heartbeat files",
    )
    parser.add_argument(
        "--status-fps",
        type=float,
        default=2.0,
        help="Heartbeat write frequency for UI status",
    )
    parser.add_argument("--debug-window", action="store_true", help="Show OpenCV debug window")
    parser.add_argument(
        "--max-frames",
        type=int,
        default=0,
        help="Stop after N frames; 0 means run forever",
    )
    return parser.parse_args()


def build_capture_region(args: argparse.Namespace) -> dict[str, int] | None:
    """Build capture region dict from CLI args or return None for full monitor."""
    values: list[Any] = [
        args.capture_left,
        args.capture_top,
        args.capture_width,
        args.capture_height,
    ]
    if all(value is None for value in values):
        return None
    if any(value is None for value in values):
        raise ValueError(
            "Capture region requires all of --capture-left/--capture-top/"
            "--capture-width/--capture-height"
        )
    return {
        "left": int(args.capture_left),
        "top": int(args.capture_top),
        "width": int(args.capture_width),
        "height": int(args.capture_height),
    }


def main() -> None:
    """Run the end-to-end automation loop."""
    args = parse_args()

    capture_region = build_capture_region(args)
    capture = ScreenCapture(monitor_index=args.monitor_index, region=capture_region)
    first_frame = capture.grab_frame()

    lane_detector = LaneDetector(lane_count=args.lanes)
    card_detector = CardDetector()
    turn_detector = TurnDetector()
    ocr_reader = OCRReader()  # Placeholder, used when numeric ROI mapping is added.
    overlay = DebugOverlay(fps_window=30)
    lane_detector.auto_configure(first_frame.shape)

    controller = InputController(capture_region=capture_region)
    profile_payload = load_vision_profile(args.vision_profile)
    if args.vision_profile and not profile_payload:
        logger.info("[instance:%d] no vision profile at %s, using auto layout", args.instance_id, args.vision_profile)
    apply_vision_profile(
        profile=profile_payload,
        lane_detector=lane_detector,
        turn_detector=turn_detector,
        card_detector=card_detector,
        input_controller=controller,
    )

    window_anchor_roi = profile_payload.get("window_anchor_roi")
    window_anchor_template = profile_payload.get("window_anchor_template")

    if len(lane_detector.get_lane_boxes()) != args.lanes:
        logger.warning(
            "[instance:%d] profile lane count mismatch (expected=%d, got=%d), using auto layout",
            args.instance_id, args.lanes, len(lane_detector.get_lane_boxes()),
        )
        lane_detector.auto_configure(first_frame.shape)

    if args.save_vision_profile:
        saved_path = save_vision_profile(
            args.save_vision_profile,
            {
                "lane_coords": [list(box) for box in lane_detector.get_lane_boxes()],
                "turn_roi": list(turn_detector.indicator_roi) if turn_detector.indicator_roi else None,
                "turn_threshold": turn_detector.threshold,
                "card_match_threshold": card_detector.match_threshold,
                "card_edge_ratio_threshold": card_detector.edge_ratio_threshold,
            },
        )
        logger.info("[instance:%d] saved vision profile -> %s", args.instance_id, saved_path)

    agent = build_agent(args.agent)
    session_logger = SessionLogger(
        output_dir=args.session_dir,
        mode=args.mode,
        log_fps=args.log_fps,
        metadata={
            "instance_id": args.instance_id,
            "monitor_index": args.monitor_index,
            "capture_region": capture_region,
            "vision_profile": args.vision_profile,
            "lanes": args.lanes,
            "agent": args.agent,
            "target_fps": args.target_fps,
            "debug_window": bool(args.debug_window),
        },
    )
    status_writer = RuntimeStatusWriter(
        output_dir=args.status_dir,
        instance_id=args.instance_id,
        mode=args.mode,
        monitor_index=args.monitor_index,
        capture_region=capture_region,
        write_fps=args.status_fps,
    )

    state = GameState.from_data_files(num_lanes=args.lanes)
    ensure_minimum_hand(state, owner="player", minimum_cards=3)
    ensure_minimum_hand(state, owner="enemy", minimum_cards=3)
    default_enemy_card_id = sorted(state.cards_db.keys())[0] if state.cards_db else None

    target_frame_time = 1.0 / max(1.0, float(args.target_fps))
    frame_count = 0
    was_my_turn = False
    last_suggestion: dict | None = None

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logger.info(
        "[instance:%d] mode=%s agent=%s lanes=%d region=%s profile=%s log=%s",
        args.instance_id, args.mode, args.agent, args.lanes,
        capture_region if capture_region is not None else "full-monitor",
        args.vision_profile or "auto",
        session_logger.file_path,
    )

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

            if my_turn and not was_my_turn and not state.is_terminal():
                ensure_minimum_hand(state, owner="player", minimum_cards=1)
                action = agent.select_action(state, owner="player")
                last_suggestion = dict(action) if action is not None else None
                session_logger.log_turn_event(
                    event="turn_start_detected",
                    action=last_suggestion,
                    executed=False,
                    extra={"mode": args.mode},
                )

                if args.mode == "autoplay":
                    can_act = True
                    if window_anchor_roi is not None and window_anchor_template is not None:
                        ax, ay, aw, ah = [int(v) for v in window_anchor_roi]
                        if ay + ah <= frame.shape[0] and ax + aw <= frame.shape[1]:
                            roi_img = frame[ay:ay+ah, ax:ax+aw]
                            res = cv2.matchTemplate(roi_img, window_anchor_template, cv2.TM_CCOEFF_NORMED)
                            _, max_val, _, _ = cv2.minMaxLoc(res)
                            if max_val < 0.90:
                                error_msg = f"Anchor validation failed! Confidence: {max_val:.2f}"
                                logger.warning("[instance:%d] %s. Aborting action.", args.instance_id, error_msg)
                                can_act = False
                                status_writer.set_error(error_msg)
                        else:
                            logger.warning("[instance:%d] Anchor bounds invalid. Aborting action.", args.instance_id)
                            can_act = False

                    if can_act:
                        state.take_turn("player", action)
                        controller.execute_action(action)
                        session_logger.log_turn_event(
                            event="action_executed",
                            action=last_suggestion,
                            executed=True,
                        )
                elif args.mode == "assist":
                    logger.info("[SUGGEST] %s", action)
            was_my_turn = my_turn

            session_logger.log_frame(
                frame_index=frame_count,
                my_turn=my_turn,
                lane_detections=lane_detections,
                state_summary=summarize_state(state),
                suggestion=last_suggestion,
            )
            loop_elapsed = time.perf_counter() - tick_start
            loop_fps = 0.0 if loop_elapsed <= 0 else (1.0 / loop_elapsed)
            status_writer.update(
                frame_count=frame_count,
                fps=loop_fps,
                my_turn=my_turn,
                last_action=last_suggestion,
                state_summary=summarize_state(state),
            )

            debug_frame = overlay.draw_lane_boxes(frame, lane_detector.get_lane_boxes())
            debug_frame = overlay.draw_card_presence(
                debug_frame,
                lane_detector.get_lane_boxes(),
                lane_detections,
            )
            debug_frame = overlay.draw_fps(debug_frame)

            if args.debug_window:
                cv2.imshow(f"cardbot-debug-{args.instance_id}", debug_frame)
                if cv2.waitKey(1) & 0xFF == 27:
                    break

            frame_count += 1
            elapsed = time.perf_counter() - tick_start
            sleep_time = target_frame_time - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    except Exception as exc:
        status_writer.set_error(str(exc))
        raise
    finally:
        capture.close()
        session_logger.close()
        status_writer.close()
        if args.debug_window:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
