from __future__ import annotations

from typing import TYPE_CHECKING, Any

from cardbot.engine.lane import Lane

if TYPE_CHECKING:
    from cardbot.engine.game_state import GameState


class Resolver:
    """Deterministic combat/action resolver for game state updates."""

    def __init__(self, state: "GameState") -> None:
        self.state = state

    def resolve_lane_attack(self, lane_index: int, attacker_owner: str) -> dict[str, Any]:
        """Resolve a single lane attack from one owner to the opposing side."""
        result: dict[str, Any] = {
            "success": False,
            "damage": 0,
            "enemy_creatures_killed": 0,
            "player_creatures_killed": 0,
            "direct_damage": 0,
            "message": "",
        }

        if lane_index < 0 or lane_index >= len(self.state.lanes):
            result["message"] = f"Invalid lane index: {lane_index}"
            return result

        lane = self.state.lanes[lane_index]
        defender_owner = Lane.opponent(attacker_owner)
        attacker = lane.get_creature(attacker_owner)
        defender = lane.get_creature(defender_owner)

        if attacker is None or not attacker.alive:
            result["message"] = "No living attacker in lane"
            return result

        if not attacker.is_ready:
            result["message"] = "Attacker countdown is not ready"
            return result

        damage = attacker.effective_atk
        if damage <= 0:
            result["message"] = "Attacker has no damage"
            return result

        result["damage"] = damage
        result["success"] = True

        if defender is None:
            dealt = self.state.deal_player_damage(defender_owner, damage, source=attacker)
            result["direct_damage"] = dealt
            self.state.event_bus.dispatch(
                "on_hit",
                state=self.state,
                actor=attacker,
                target=None,
                lane_index=lane_index,
                damage=dealt,
            )
            attacker.reset_attack_timer()
            return result

        was_alive = defender.alive
        dealt = defender.take_damage(damage, state=self.state, source=attacker)
        self.state.event_bus.dispatch(
            "on_hit",
            state=self.state,
            actor=attacker,
            target=defender,
            lane_index=lane_index,
            damage=dealt,
        )
        attacker.reset_attack_timer()

        if was_alive and not defender.alive:
            if defender.owner == "enemy":
                result["enemy_creatures_killed"] = 1
            elif defender.owner == "player":
                result["player_creatures_killed"] = 1

        return result


# TODO: support queued effect stacks for pre/post-combat triggers.
