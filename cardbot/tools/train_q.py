"""Train a tabular Q-learning policy on CardBot's Gymnasium environment."""

from __future__ import annotations

import argparse
import math
import pickle
from pathlib import Path
from typing import Any

import numpy as np

from cardbot.environment.rl_env import RLEnv


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for Q-learning training."""
    parser = argparse.ArgumentParser(description="Train tabular Q-learning policy for CardBot")
    parser.add_argument("--episodes", type=int, default=4000, help="Number of training episodes")
    parser.add_argument("--num-lanes", type=int, default=3, choices=[2, 3, 4])
    parser.add_argument("--max-turns", type=int, default=60)
    parser.add_argument("--alpha", type=float, default=0.10, help="Learning rate")
    parser.add_argument("--gamma", type=float, default=0.99, help="Discount factor")
    parser.add_argument("--epsilon-start", type=float, default=1.00)
    parser.add_argument("--epsilon-end", type=float, default=0.05)
    parser.add_argument("--epsilon-decay", type=float, default=0.9985)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--print-every", type=int, default=100)
    parser.add_argument(
        "--save-path",
        type=str,
        default="cardbot/data/models/q_table.pkl",
        help="Where to write the trained Q-table",
    )
    return parser.parse_args()


def bucketize_stat(value: int, bins: tuple[int, ...]) -> int:
    """Convert raw stat to a small bucket index."""
    for idx, threshold in enumerate(bins):
        if value <= threshold:
            return idx
    return len(bins)


def encode_obs(obs: dict[str, np.ndarray]) -> tuple[int, ...]:
    """Encode observation dict into a compact discrete state key.

    This keeps table size manageable while preserving strategic signal.
    """
    turn = int(obs["turn"][0])
    player_hp = int(obs["player_hp"][0])
    enemy_hp = int(obs["enemy_hp"][0])
    lanes = obs["lanes"]  # shape: (num_lanes, 2, 7)

    key: list[int] = []

    # Coarse global features
    key.append(bucketize_stat(turn, bins=(10, 20, 35, 50)))
    key.append(bucketize_stat(player_hp, bins=(5, 10, 15)))
    key.append(bucketize_stat(enemy_hp, bins=(5, 10, 15)))

    # Lane/side local features
    for lane_idx in range(lanes.shape[0]):
        for side_idx in range(2):
            present = int(lanes[lane_idx, side_idx, 0])
            atk = int(lanes[lane_idx, side_idx, 1])
            hp = int(lanes[lane_idx, side_idx, 2])
            countdown = int(lanes[lane_idx, side_idx, 4])
            damage_bonus = int(lanes[lane_idx, side_idx, 6])

            if present == 0:
                key.extend((0, 0, 0, 0, 0))
            else:
                key.append(1)
                key.append(bucketize_stat(atk, bins=(2, 4, 6)))
                key.append(bucketize_stat(hp, bins=(3, 6, 9)))
                key.append(bucketize_stat(countdown, bins=(0, 1, 2)))
                key.append(bucketize_stat(damage_bonus, bins=(0, 2, 4)))

    return tuple(key)


def epsilon_for_episode(ep: int, eps_start: float, eps_end: float, eps_decay: float) -> float:
    """Compute decayed epsilon for episode index."""
    value = eps_start * (eps_decay**ep)
    return max(eps_end, value)


def ensure_q_row(q_table: dict[tuple[int, ...], np.ndarray], state_key: tuple[int, ...], n_actions: int) -> np.ndarray:
    """Get or create Q-value row for state."""
    row = q_table.get(state_key)
    if row is None:
        row = np.zeros((n_actions,), dtype=np.float32)
        q_table[state_key] = row
    return row


def valid_action_indices(mask: np.ndarray) -> np.ndarray:
    """Return valid action IDs from mask, defaulting to all actions when empty."""
    ids = np.flatnonzero(mask)
    if ids.size == 0:
        return np.arange(mask.shape[0], dtype=np.int64)
    return ids


def masked_argmax(values: np.ndarray, valid_ids: np.ndarray) -> int:
    """Choose best action among valid IDs only."""
    if valid_ids.size == 0:
        return 0
    subset = values[valid_ids]
    return int(valid_ids[int(np.argmax(subset))])


def choose_action(
    q_values: np.ndarray,
    valid_ids: np.ndarray,
    epsilon: float,
    rng: np.random.Generator,
) -> int:
    """Epsilon-greedy action selection constrained by valid actions."""
    if valid_ids.size == 0:
        return 0

    if rng.random() < epsilon:
        return int(rng.choice(valid_ids))

    return masked_argmax(q_values, valid_ids)


def train(args: argparse.Namespace) -> dict[str, Any]:
    """Run tabular Q-learning and return training artifacts."""
    rng = np.random.default_rng(args.seed)

    env = RLEnv(num_lanes=args.num_lanes, max_turns=args.max_turns)
    n_actions = int(env.action_space.n)

    q_table: dict[tuple[int, ...], np.ndarray] = {}
    reward_history: list[float] = []
    win_history: list[int] = []

    for episode in range(args.episodes):
        obs, info = env.reset(seed=args.seed + episode)
        state_key = encode_obs(obs)
        epsilon = epsilon_for_episode(
            ep=episode,
            eps_start=args.epsilon_start,
            eps_end=args.epsilon_end,
            eps_decay=args.epsilon_decay,
        )

        total_reward = 0.0
        done = False

        while not done:
            current_q = ensure_q_row(q_table, state_key, n_actions)
            mask = np.array(info.get("valid_action_mask", np.ones((n_actions,), dtype=np.int8)), dtype=np.int8)
            valid_ids = valid_action_indices(mask)
            action = choose_action(current_q, valid_ids, epsilon, rng)

            next_obs, reward, terminated, truncated, next_info = env.step(action)
            done = bool(terminated or truncated)
            total_reward += float(reward)

            next_state_key = encode_obs(next_obs)
            next_q = ensure_q_row(q_table, next_state_key, n_actions)
            next_mask = np.array(next_info.get("valid_action_mask", np.ones((n_actions,), dtype=np.int8)), dtype=np.int8)
            next_valid_ids = valid_action_indices(next_mask)

            if done:
                target = float(reward)
            else:
                next_best = float(next_q[next_valid_ids].max()) if next_valid_ids.size > 0 else float(next_q.max())
                target = float(reward) + args.gamma * next_best

            current_q[action] = current_q[action] + args.alpha * (target - current_q[action])

            state_key = next_state_key
            info = next_info

        reward_history.append(total_reward)
        winner = info.get("winner")
        win_history.append(1 if winner == "player" else 0)

        if (episode + 1) % max(1, args.print_every) == 0:
            window = min(args.print_every, len(reward_history))
            avg_reward = float(np.mean(reward_history[-window:]))
            win_rate = float(np.mean(win_history[-window:]))
            print(
                f"ep={episode + 1:5d} epsilon={epsilon:.3f} "
                f"avg_reward={avg_reward:8.2f} win_rate={win_rate:5.2%} q_states={len(q_table)}"
            )

    env.close()

    return {
        "q_table": q_table,
        "meta": {
            "episodes": int(args.episodes),
            "num_lanes": int(args.num_lanes),
            "max_turns": int(args.max_turns),
            "alpha": float(args.alpha),
            "gamma": float(args.gamma),
            "epsilon_start": float(args.epsilon_start),
            "epsilon_end": float(args.epsilon_end),
            "epsilon_decay": float(args.epsilon_decay),
            "seed": int(args.seed),
            "q_states": int(len(q_table)),
            "final_avg_reward_100": float(np.mean(reward_history[-100:])) if reward_history else 0.0,
            "final_win_rate_100": float(np.mean(win_history[-100:])) if win_history else 0.0,
        },
    }


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    artifacts = train(args)

    save_path = Path(args.save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_bytes(pickle.dumps(artifacts))

    meta = artifacts["meta"]
    print(f"saved={save_path}")
    print(
        "summary: "
        f"q_states={meta['q_states']} "
        f"final_avg_reward_100={meta['final_avg_reward_100']:.2f} "
        f"final_win_rate_100={meta['final_win_rate_100']:.2%}"
    )


if __name__ == "__main__":
    main()
