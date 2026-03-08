from __future__ import annotations

from typing import Any

from cardbot.engine.creature import Creature


class Lane:
    """Represents one battle lane with one slot per owner side."""

    def __init__(self, index: int) -> None:
        self.index = index
        self.player_creature: Creature | None = None
        self.enemy_creature: Creature | None = None

    @staticmethod
    def opponent(owner: str) -> str:
        """Return opposing owner label."""
        if owner == "player":
            return "enemy"
        if owner == "enemy":
            return "player"
        raise ValueError(f"Unknown owner: {owner}")

    def _get_slot_name(self, owner: str) -> str:
        if owner == "player":
            return "player_creature"
        if owner == "enemy":
            return "enemy_creature"
        raise ValueError(f"Unknown owner: {owner}")

    def has_empty_slot(self, owner: str) -> bool:
        """Whether the owner's slot in this lane is empty."""
        return self.get_creature(owner) is None

    def get_creature(self, owner: str) -> Creature | None:
        """Return creature in the owner's slot."""
        return getattr(self, self._get_slot_name(owner))

    def add_creature(self, creature: Creature, owner: str) -> None:
        """Add a creature to an owner's slot."""
        slot_name = self._get_slot_name(owner)
        if getattr(self, slot_name) is not None:
            raise ValueError(f"Lane {self.index} slot for {owner} is already occupied")

        creature.owner = owner
        creature.lane_index = self.index
        creature.alive = True
        setattr(self, slot_name, creature)

    def remove_creature(self, owner: str) -> Creature | None:
        """Remove and return creature from owner slot."""
        slot_name = self._get_slot_name(owner)
        creature = getattr(self, slot_name)
        setattr(self, slot_name, None)
        if creature is not None:
            creature.lane_index = None
        return creature

    def remove_creature_instance(self, creature: Creature) -> bool:
        """Remove a specific creature instance if found in the lane."""
        if self.player_creature is creature:
            self.remove_creature("player")
            return True
        if self.enemy_creature is creature:
            self.remove_creature("enemy")
            return True
        return False

    def iter_creatures(self) -> list[Creature]:
        """Return creatures in deterministic owner order."""
        result: list[Creature] = []
        if self.player_creature is not None:
            result.append(self.player_creature)
        if self.enemy_creature is not None:
            result.append(self.enemy_creature)
        return result

    def tick_countdowns(self, owner: str | None = None) -> None:
        """Decrease countdowns for one side or both sides in this lane."""
        if owner is None:
            creatures = self.iter_creatures()
        else:
            candidate = self.get_creature(owner)
            creatures = [candidate] if candidate is not None else []

        for creature in creatures:
            creature.tick_countdown()

    def to_dict(self) -> dict[str, Any]:
        """Serialize lane state."""
        return {
            "index": self.index,
            "player": None if self.player_creature is None else self.player_creature.to_dict(),
            "enemy": None if self.enemy_creature is None else self.enemy_creature.to_dict(),
        }


# TODO: support multi-slot lanes if future game modes need formations.
