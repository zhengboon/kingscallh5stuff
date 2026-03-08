from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from cardbot.engine.modifier import Modifier

if TYPE_CHECKING:
    from cardbot.engine.creature import Creature
    from cardbot.engine.game_state import GameState


class Ability:
    """Shared ability definition resolved by ID from a central library."""

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        trigger: str,
        effect: str,
        value: int = 0,
        scope: str = "self",
        params: dict[str, Any] | None = None,
    ) -> None:
        self.id = id
        self.name = name
        self.description = description
        self.trigger = trigger
        self.effect = effect
        self.value = int(value)
        self.scope = scope
        self.params = dict(params or {})

    def should_trigger(self, event: str, owner: "Creature", context: dict[str, Any]) -> bool:
        """Check whether this ability should run for the current event."""
        if event != self.trigger:
            return False

        actor = context.get("actor")
        if self.scope == "self" and actor is not None and actor is not owner:
            return False
        if self.scope == "ally" and actor is not None and getattr(actor, "owner", None) != owner.owner:
            return False
        if self.scope == "enemy" and actor is not None and getattr(actor, "owner", None) == owner.owner:
            return False

        if event in {"on_turn_start", "on_turn_end"}:
            turn_owner = context.get("owner")
            active_only = bool(self.params.get("active_turn_only", True))
            if active_only and turn_owner is not None and turn_owner != owner.owner:
                return False

        return True

    def execute(self, state: "GameState", owner: "Creature", **context: Any) -> None:
        """Apply this ability's effect to game state."""
        if not owner.alive:
            return

        if self.effect == "heal_self":
            owner.heal(self.value, state=state, source=owner)
            return

        if self.effect == "increase_max_hp_self":
            heal_for_delta = bool(self.params.get("heal_for_delta", True))
            owner.change_max_hp(self.value, state=state, heal_for_delta=heal_for_delta)
            return

        if self.effect == "gain_damage_bonus_self":
            owner.gain_damage_bonus(self.value)
            return

        if self.effect == "add_modifier_self":
            modifier = Modifier(
                id=str(self.params.get("modifier_id", f"{self.id}_mod")),
                name=str(self.params.get("modifier_name", self.name)),
                atk_bonus=int(self.params.get("atk_bonus", 0)),
                max_hp_bonus=int(self.params.get("max_hp_bonus", 0)),
                damage_bonus_per_hit=int(self.params.get("damage_bonus_per_hit", 0)),
                duration_turns=self.params.get("duration_turns"),
                stacks=int(self.params.get("stacks", 1)),
            )
            owner.add_modifier(
                modifier,
                heal_for_new_max=bool(self.params.get("heal_for_delta", False)),
            )
            return

        if self.effect == "heal_lane_ally":
            if owner.lane_index is None:
                return
            ally = state.lanes[owner.lane_index].get_creature(owner.owner)
            if ally is not None:
                ally.heal(self.value, state=state, source=owner)
            return

        state.history.append(f"ability_unhandled:{self.id}:effect={self.effect}")

    def to_dict(self) -> dict[str, Any]:
        """Serialize ability definition."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "trigger": self.trigger,
            "effect": self.effect,
            "value": self.value,
            "scope": self.scope,
            "params": dict(self.params),
        }


class AbilityLibrary:
    """Registry of shared ability definitions loaded from JSON."""

    def __init__(self, definitions: list[dict[str, Any]] | None = None) -> None:
        self._abilities: dict[str, Ability] = {}
        if definitions:
            self.load_from_definitions(definitions)

    def register(self, ability: Ability) -> None:
        """Add or replace an ability by ID."""
        self._abilities[ability.id] = ability

    def get(self, ability_id: str) -> Ability | None:
        """Lookup ability by ID."""
        return self._abilities.get(ability_id)

    def load_from_definitions(self, definitions: list[dict[str, Any]]) -> None:
        """Load abilities from JSON-style dictionaries."""
        for definition in definitions:
            params = dict(definition.get("params", {}))
            for key in (
                "active_turn_only",
                "heal_for_delta",
                "modifier_id",
                "modifier_name",
                "duration_turns",
                "stacks",
                "atk_bonus",
                "max_hp_bonus",
                "damage_bonus_per_hit",
            ):
                if key in definition:
                    params[key] = definition[key]

            ability = Ability(
                id=str(definition["id"]),
                name=str(definition.get("name", definition["id"])),
                description=str(definition.get("description", "")),
                trigger=str(definition.get("trigger", "on_summon")),
                effect=str(definition.get("effect", "heal_self")),
                value=int(definition.get("value", 0)),
                scope=str(definition.get("scope", "self")),
                params=params,
            )
            self.register(ability)

    @classmethod
    def from_json_file(cls, file_path: str | Path) -> "AbilityLibrary":
        """Create library from an abilities JSON file."""
        payload = json.loads(Path(file_path).read_text(encoding="utf-8"))
        return cls(definitions=list(payload.get("abilities", [])))

    def to_dict(self) -> dict[str, Any]:
        """Serialize ability registry."""
        return {ability_id: ability.to_dict() for ability_id, ability in self._abilities.items()}


# TODO: support composite effect chains for complex abilities.
