from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Modifier:
    """Represents a stat modifier that can stack and expire."""

    id: str
    name: str
    atk_bonus: int = 0
    max_hp_bonus: int = 0
    damage_bonus_per_hit: int = 0
    duration_turns: int | None = None
    stacks: int = 1

    @property
    def total_atk_bonus(self) -> int:
        """Total attack bonus from all stacks."""
        return self.atk_bonus * self.stacks

    @property
    def total_max_hp_bonus(self) -> int:
        """Total max HP bonus from all stacks."""
        return self.max_hp_bonus * self.stacks

    @property
    def total_damage_bonus_per_hit(self) -> int:
        """Total per-hit growth bonus from all stacks."""
        return self.damage_bonus_per_hit * self.stacks

    def copy(self) -> "Modifier":
        """Return a copy used when attaching to creatures."""
        return Modifier(
            id=self.id,
            name=self.name,
            atk_bonus=self.atk_bonus,
            max_hp_bonus=self.max_hp_bonus,
            damage_bonus_per_hit=self.damage_bonus_per_hit,
            duration_turns=self.duration_turns,
            stacks=self.stacks,
        )

    def tick(self) -> bool:
        """Advance duration by one turn.

        Returns True when the modifier should expire.
        """
        if self.duration_turns is None:
            return False
        self.duration_turns -= 1
        return self.duration_turns <= 0

    def to_dict(self) -> dict[str, Any]:
        """Serialize modifier state."""
        return {
            "id": self.id,
            "name": self.name,
            "atk_bonus": self.atk_bonus,
            "max_hp_bonus": self.max_hp_bonus,
            "damage_bonus_per_hit": self.damage_bonus_per_hit,
            "duration_turns": self.duration_turns,
            "stacks": self.stacks,
        }


# TODO: support richer stacking policies (replace, refresh, cap).
