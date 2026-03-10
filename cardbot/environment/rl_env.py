from __future__ import annotations

from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from cardbot.agents.heuristic_agent import HeuristicAgent
from cardbot.engine.game_state import GameState


class RLEnv(gym.Env):
    """Gymnasium environment wrapping deterministic game engine.

    Action encoding:
    - 0..num_lanes-1: summon in lane using first hand card
    - num_lanes..2*num_lanes-1: attack in lane
    - 2*num_lanes: end turn
    """

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        num_lanes: int = 3,
        max_turns: int = 60,
        starting_hp: int = 20,
        starting_hand_size: int = 3,
        render_mode: str | None = None,
    ) -> None:
        super().__init__()

        if num_lanes not in (2, 3, 4):
            raise ValueError("num_lanes must be 2, 3, or 4")

        self.num_lanes = num_lanes
        self.max_turns = int(max_turns)
        self.starting_hp = int(starting_hp)
        self.starting_hand_size = int(starting_hand_size)
        self.render_mode = render_mode

        self.enemy_agent = HeuristicAgent()
        self.state = self._build_state()

        self.action_space = spaces.Discrete(2 * self.num_lanes + 1)
        self.observation_space = spaces.Dict(
            {
                "turn": spaces.Box(low=0, high=self.max_turns, shape=(1,), dtype=np.int32),
                "player_hp": spaces.Box(low=0, high=100, shape=(1,), dtype=np.int32),
                "enemy_hp": spaces.Box(low=0, high=100, shape=(1,), dtype=np.int32),
                "lanes": spaces.Box(
                    low=0,
                    high=500,
                    shape=(self.num_lanes, 2, 7),
                    dtype=np.int32,
                ),
            }
        )

    def _build_state(self) -> GameState:
        state = GameState.from_data_files(
            num_lanes=self.num_lanes,
            starting_hp=self.starting_hp,
        )
        state.draw_starting_hand("player", count=self.starting_hand_size)
        state.draw_starting_hand("enemy", count=self.starting_hand_size)
        return state

    def _decode_action(self, action: int, owner: str) -> dict[str, Any]:
        if action < self.num_lanes:
            hand = self.state.get_hand(owner)
            if not hand:
                return {"type": "end_turn"}
            return {
                "type": "summon",
                "lane": int(action),
                "hand_index": 0,
                "card_id": hand[0],
            }

        if action < 2 * self.num_lanes:
            return {"type": "attack", "lane": int(action - self.num_lanes)}

        return {"type": "end_turn"}

    def _is_decoded_action_valid(self, owner: str, action_dict: dict[str, Any]) -> bool:
        action_type = action_dict.get("type")

        if action_type == "end_turn":
            return True

        if action_type == "summon":
            lane_index = int(action_dict.get("lane", -1))
            if lane_index < 0 or lane_index >= self.num_lanes:
                return False
            hand = self.state.get_hand(owner)
            if not hand:
                return False
            return self.state.lanes[lane_index].has_empty_slot(owner)

        if action_type == "attack":
            lane_index = int(action_dict.get("lane", -1))
            if lane_index < 0 or lane_index >= self.num_lanes:
                return False
            attacker = self.state.lanes[lane_index].get_creature(owner)
            return attacker is not None and attacker.is_ready

        return False

    def valid_action_mask(self, owner: str = "player") -> np.ndarray:
        """Boolean mask of valid encoded actions."""
        mask = np.zeros(self.action_space.n, dtype=np.int8)
        for action_id in range(self.action_space.n):
            action_dict = self._decode_action(action_id, owner=owner)
            if self._is_decoded_action_valid(owner=owner, action_dict=action_dict):
                mask[action_id] = 1
        return mask

    def _choose_enemy_action_id(self) -> int:
        valid_mask = self.valid_action_mask(owner="enemy")
        valid_ids = np.flatnonzero(valid_mask)
        if valid_ids.size == 0:
            return self.action_space.n - 1

        lethal_attack: int | None = None
        direct_attack: int | None = None

        for action_id in valid_ids.tolist():
            action = self._decode_action(action_id, owner="enemy")
            if action.get("type") != "attack":
                continue
            lane = self.state.lanes[int(action["lane"])]
            attacker = lane.get_creature("enemy")
            defender = lane.get_creature("player")
            if attacker is None:
                continue
            if defender is not None and defender.hp <= attacker.effective_atk:
                lethal_attack = action_id
                break
            if defender is None and direct_attack is None:
                direct_attack = action_id

        if lethal_attack is not None:
            return lethal_attack
        if direct_attack is not None:
            return direct_attack

        summon_ids = [
            action_id
            for action_id in valid_ids.tolist()
            if self._decode_action(action_id, owner="enemy").get("type") == "summon"
        ]
        if summon_ids:
            return summon_ids[0]

        return int(valid_ids[0])

    def _get_obs(self) -> dict[str, np.ndarray]:
        lanes = np.zeros((self.num_lanes, 2, 7), dtype=np.int32)

        for lane_index, lane in enumerate(self.state.lanes):
            for side_index, owner in enumerate(("player", "enemy")):
                creature = lane.get_creature(owner)
                if creature is None:
                    continue
                lanes[lane_index, side_index, 0] = 1
                lanes[lane_index, side_index, 1] = creature.effective_atk
                lanes[lane_index, side_index, 2] = creature.hp
                lanes[lane_index, side_index, 3] = creature.max_hp
                lanes[lane_index, side_index, 4] = creature.countdown
                lanes[lane_index, side_index, 5] = len(creature.modifiers)
                lanes[lane_index, side_index, 6] = creature.flat_damage_bonus

        return {
            "turn": np.array([self.state.turn_number], dtype=np.int32),
            "player_hp": np.array([self.state.player_hp["player"]], dtype=np.int32),
            "enemy_hp": np.array([self.state.player_hp["enemy"]], dtype=np.int32),
            "lanes": lanes,
        }

    def reset(self, seed: int | None = None, options: dict[str, Any] | None = None):
        super().reset(seed=seed)
        load_error: str | None = None
        snapshot = None if options is None else options.get("state_snapshot")
        if isinstance(snapshot, dict):
            try:
                self.state = GameState.from_snapshot(snapshot=snapshot, num_lanes=self.num_lanes)
            except Exception as exc:
                load_error = str(exc)
                self.state = self._build_state()
        else:
            self.state = self._build_state()

        obs = self._get_obs()
        info: dict[str, Any] = {"valid_action_mask": self.valid_action_mask(owner="player")}
        if load_error is not None:
            info["snapshot_load_error"] = load_error
        return obs, info

    def step(self, action: int):
        action_id = int(action)
        player_action = self._decode_action(action_id, owner="player")

        reward = 0.0
        enemy_action: dict[str, Any] | None = None

        before_enemy_creatures = self.state.count_creatures("enemy")
        player_result = self.state.take_turn("player", player_action)
        after_enemy_creatures = self.state.count_creatures("enemy")

        killed_enemy = max(0, before_enemy_creatures - after_enemy_creatures)
        reward += float(killed_enemy * 10)

        if not self.state.is_terminal():
            enemy_action_id = self._choose_enemy_action_id()
            enemy_action = self._decode_action(enemy_action_id, owner="enemy")
            before_player_creatures = self.state.count_creatures("player")
            self.state.take_turn("enemy", enemy_action)
            after_player_creatures = self.state.count_creatures("player")
            lost_player_creatures = max(0, before_player_creatures - after_player_creatures)
            reward -= float(lost_player_creatures * 10)

        terminated = False
        truncated = False

        if self.state.winner == "player":
            reward += 100.0
            terminated = True
        elif self.state.winner == "enemy":
            reward -= 100.0
            terminated = True

        if self.state.turn_number >= self.max_turns and not terminated:
            truncated = True

        obs = self._get_obs()
        info = {
            "player_result": player_result,
            "player_action": player_action,
            "enemy_action": enemy_action,
            "winner": self.state.winner,
            "valid_action_mask": self.valid_action_mask(owner="player"),
        }
        return obs, reward, terminated, truncated, info

    def render(self) -> None:
        if self.render_mode == "human":
            print(self.state.to_dict())

    def close(self) -> None:
        """No extra resources currently allocated."""
        return None


# TODO: expose legal action list directly in Gym info for masked RL training.
