"""Load exported scenarios into the RL environment for quick iteration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from cardbot.environment.rl_env import RLEnv


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run one exported scenario in RLEnv")
    parser.add_argument("scenario_file", type=str, help="Path to observed_scenarios.json")
    parser.add_argument("--index", type=int, default=0, help="Scenario index to load")
    parser.add_argument(
        "--action",
        type=int,
        default=None,
        help="Optional encoded action ID to execute once after reset",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point."""
    args = parse_args()
    scenario_file = Path(args.scenario_file)
    payload = json.loads(scenario_file.read_text(encoding="utf-8"))
    scenarios = payload.get("scenarios", [])

    if not isinstance(scenarios, list) or not scenarios:
        print("No scenarios found in file.")
        raise SystemExit(1)

    if args.index < 0 or args.index >= len(scenarios):
        print(f"Scenario index out of range: {args.index} (max={len(scenarios) - 1})")
        raise SystemExit(1)

    scenario = scenarios[args.index]
    snapshot = scenario.get("state_snapshot")
    if not isinstance(snapshot, dict):
        print("Selected scenario has no state_snapshot payload.")
        raise SystemExit(1)

    num_lanes = int(snapshot.get("num_lanes", 3))
    env = RLEnv(num_lanes=num_lanes)
    obs, info = env.reset(options={"state_snapshot": snapshot})

    mask = np.asarray(info.get("valid_action_mask", []), dtype=np.int8)
    print(f"scenario_id={scenario.get('id')}")
    print(f"turn={int(obs['turn'][0])} player_hp={int(obs['player_hp'][0])} enemy_hp={int(obs['enemy_hp'][0])}")
    print(f"valid_action_ids={np.flatnonzero(mask).tolist()}")

    if args.action is not None:
        next_obs, reward, terminated, truncated, next_info = env.step(int(args.action))
        print(
            f"step_reward={float(reward):.2f} "
            f"terminated={bool(terminated)} truncated={bool(truncated)} "
            f"winner={next_info.get('winner')}"
        )
        print(
            f"next_turn={int(next_obs['turn'][0])} "
            f"next_player_hp={int(next_obs['player_hp'][0])} "
            f"next_enemy_hp={int(next_obs['enemy_hp'][0])}"
        )

    env.close()


if __name__ == "__main__":
    main()

