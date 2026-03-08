from __future__ import annotations

from typing import TYPE_CHECKING, Any

from cardbot.engine.modifier import Modifier

if TYPE_CHECKING:
    from cardbot.engine.game_state import GameState


class Creature:
    """A board unit with combat stats, countdown, and shared ability IDs."""

    def __init__(
        self,
        card_id: str,
        name: str,
        owner: str,
        atk: int,
        hp: int,
        countdown: int,
        ability_ids: list[str] | None = None,
    ) -> None:
        self.card_id = card_id
        self.name = name
        self.owner = owner
        self.base_atk = int(atk)
        self.hp = int(hp)
        self.max_hp = int(hp)
        self.base_countdown = max(0, int(countdown))
        self.countdown = max(0, int(countdown))
        self.ability_ids = list(ability_ids or [])
        self.modifiers: list[Modifier] = []
        self.flat_damage_bonus: int = 0
        self.lane_index: int | None = None
        self.alive: bool = True

    @property
    def effective_atk(self) -> int:
        """Current attack after modifiers and persistent hit bonuses."""
        modifier_bonus = sum(mod.total_atk_bonus for mod in self.modifiers)
        return max(0, self.base_atk + modifier_bonus + self.flat_damage_bonus)

    @property
    def is_ready(self) -> bool:
        """Whether this creature can attack right now."""
        return self.alive and self.countdown <= 0

    def tick_countdown(self) -> None:
        """Decrease countdown by one (floored at 0)."""
        self.countdown = max(0, self.countdown - 1)

    def reset_attack_timer(self) -> None:
        """Reset countdown after an attack."""
        self.countdown = self.base_countdown

    def take_damage(self, amount: int, state: "GameState", source: "Creature | None" = None) -> int:
        """Apply incoming damage and emit engine events."""
        if not self.alive:
            return 0
        raw_amount = max(0, int(amount))
        if raw_amount <= 0:
            return 0

        before = self.hp
        self.hp = max(0, self.hp - raw_amount)
        dealt = before - self.hp
        state.event_bus.dispatch(
            "on_damage_taken",
            state=state,
            actor=self,
            source=source,
            amount=dealt,
        )

        if self.hp <= 0:
            self.die(state=state, source=source)

        return dealt

    def heal(self, amount: int, state: "GameState", source: "Creature | None" = None) -> int:
        """Heal HP up to max HP and emit events."""
        if not self.alive:
            return 0
        raw_amount = max(0, int(amount))
        if raw_amount <= 0:
            return 0

        before = self.hp
        self.hp = min(self.max_hp, self.hp + raw_amount)
        healed = self.hp - before
        if healed > 0:
            state.event_bus.dispatch(
                "on_heal",
                state=state,
                actor=self,
                source=source,
                amount=healed,
            )
        return healed

    def change_max_hp(self, delta: int, state: "GameState", heal_for_delta: bool = False) -> None:
        """Change max HP and keep HP within legal bounds."""
        if not self.alive:
            return

        delta_int = int(delta)
        self.max_hp = max(1, self.max_hp + delta_int)

        if heal_for_delta and delta_int > 0:
            self.hp = min(self.max_hp, self.hp + delta_int)
        else:
            self.hp = min(self.hp, self.max_hp)

        state.history.append(
            f"max_hp_change:{self.owner}:{self.name}:delta={delta_int}:max={self.max_hp}"
        )

    def gain_damage_bonus(self, amount: int) -> None:
        """Increase flat damage bonus used on each attack."""
        self.flat_damage_bonus += max(0, int(amount))

    def add_modifier(self, modifier: Modifier, heal_for_new_max: bool = False) -> None:
        """Add a modifier, stacking by modifier ID."""
        incoming = modifier.copy()
        existing = next((mod for mod in self.modifiers if mod.id == incoming.id), None)

        applied_max_hp_bonus = incoming.total_max_hp_bonus

        if existing is None:
            self.modifiers.append(incoming)
        else:
            existing.stacks += incoming.stacks
            applied_max_hp_bonus = incoming.max_hp_bonus * incoming.stacks
            if incoming.duration_turns is not None:
                if existing.duration_turns is None:
                    existing.duration_turns = incoming.duration_turns
                else:
                    existing.duration_turns = max(existing.duration_turns, incoming.duration_turns)

        if applied_max_hp_bonus != 0:
            self.max_hp = max(1, self.max_hp + applied_max_hp_bonus)
            if heal_for_new_max and applied_max_hp_bonus > 0:
                self.hp = min(self.max_hp, self.hp + applied_max_hp_bonus)
            else:
                self.hp = min(self.hp, self.max_hp)

    def remove_modifier(self, modifier_id: str, stacks: int | None = None) -> bool:
        """Remove all or part of a modifier stack by ID."""
        for mod in list(self.modifiers):
            if mod.id != modifier_id:
                continue

            remove_stacks = mod.stacks if stacks is None else max(0, min(stacks, mod.stacks))
            if remove_stacks <= 0:
                return False

            hp_delta = mod.max_hp_bonus * remove_stacks
            mod.stacks -= remove_stacks
            if mod.stacks <= 0:
                self.modifiers.remove(mod)

            if hp_delta != 0:
                self.max_hp = max(1, self.max_hp - hp_delta)
                self.hp = min(self.hp, self.max_hp)
            return True
        return False

    def tick_modifiers(self) -> None:
        """Advance modifier durations and remove expired modifiers."""
        expired: list[tuple[str, int]] = []
        for mod in self.modifiers:
            if mod.tick():
                expired.append((mod.id, mod.stacks))

        for modifier_id, stacks in expired:
            self.remove_modifier(modifier_id, stacks=stacks)

    def die(self, state: "GameState", source: "Creature | None" = None) -> None:
        """Mark dead and dispatch death event once."""
        if not self.alive:
            return
        self.alive = False
        self.hp = 0
        state.event_bus.dispatch(
            "on_death",
            state=state,
            actor=self,
            source=source,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize creature state."""
        return {
            "card_id": self.card_id,
            "name": self.name,
            "owner": self.owner,
            "atk": self.effective_atk,
            "base_atk": self.base_atk,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "countdown": self.countdown,
            "base_countdown": self.base_countdown,
            "abilities": list(self.ability_ids),
            "modifiers": [modifier.to_dict() for modifier in self.modifiers],
            "flat_damage_bonus": self.flat_damage_bonus,
            "lane_index": self.lane_index,
            "alive": self.alive,
        }


# TODO: add status effect flags (silence, stun, shield) as game rules expand.
