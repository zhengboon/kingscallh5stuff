from __future__ import annotations

import random
from typing import Any


class RandomAgent:
    """Agent that samples uniformly from valid game actions."""

    def __init__(self, action_space: Any = None, seed: int | None = None) -> None:
        self.action_space = action_space
        self._rng = random.Random(seed)

    def select_action(self, state: Any, owner: str = "player") -> dict[str, Any] | Any:
        """Pick a random valid action.

        If `state` provides `get_valid_actions(owner)`, that source is used.
        Otherwise falls back to `action_space.sample()` if available.
        """
        if hasattr(state, "get_valid_actions"):
            actions = state.get_valid_actions(owner)
            if not actions:
                return {"type": "end_turn"}
            return self._rng.choice(actions)

        if self.action_space is not None and hasattr(self.action_space, "sample"):
            return self.action_space.sample()

        return {"type": "end_turn"}


# TODO: add weighted random policy for curriculum training.
