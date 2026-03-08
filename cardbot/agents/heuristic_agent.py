from __future__ import annotations

from typing import Any


class HeuristicAgent:
    """Rule-based baseline strategy for quick automation and RL opponents."""

    def select_action(self, state: Any, owner: str = "player") -> dict[str, Any]:
        """Choose action with simple lane combat heuristics."""
        if not hasattr(state, "lanes"):
            return {"type": "end_turn"}

        opponent = state.opponent(owner)

        # Rule 1: take lethal attacks on enemy creatures first.
        for lane in state.lanes:
            attacker = lane.get_creature(owner)
            defender = lane.get_creature(opponent)
            if attacker is None or not attacker.is_ready:
                continue
            if defender is not None and defender.hp <= attacker.effective_atk:
                return {"type": "attack", "lane": lane.index}

        # Rule 2: take direct attacks on empty opposing lane.
        for lane in state.lanes:
            attacker = lane.get_creature(owner)
            defender = lane.get_creature(opponent)
            if attacker is not None and attacker.is_ready and defender is None:
                return {"type": "attack", "lane": lane.index}

        # Rule 3: play first hand card into first empty lane.
        hand = state.get_hand(owner)
        if hand:
            for lane in state.lanes:
                if lane.has_empty_slot(owner):
                    return {
                        "type": "summon",
                        "lane": lane.index,
                        "hand_index": 0,
                        "card_id": hand[0],
                    }

        return {"type": "end_turn"}


# TODO: add lane threat scoring and hand-value evaluation.
