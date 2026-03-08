from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from cardbot.engine.ability import AbilityLibrary
from cardbot.engine.creature import Creature
from cardbot.engine.event_bus import EventBus
from cardbot.engine.lane import Lane
from cardbot.engine.resolver import Resolver

GAME_EVENTS = (
    "on_turn_start",
    "on_turn_end",
    "on_summon",
    "on_hit",
    "on_damage_taken",
    "on_heal",
    "on_death",
)


class GameState:
    """Deterministic in-memory mirror of match state and rule resolution."""

    def __init__(
        self,
        num_lanes: int = 3,
        cards: dict[str, dict[str, Any]] | None = None,
        abilities: list[dict[str, Any]] | None = None,
        starting_hp: int = 20,
    ) -> None:
        if num_lanes not in (2, 3, 4):
            raise ValueError("num_lanes must be 2, 3, or 4")

        self.lanes: list[Lane] = [Lane(index=i) for i in range(num_lanes)]
        self.turn_number: int = 0
        self.active_player: str = "player"
        self.player_hand: list[str] = []
        self.enemy_hand: list[str] = []
        self.player_hp: dict[str, int] = {"player": int(starting_hp), "enemy": int(starting_hp)}
        self.history: list[str] = []
        self.winner: str | None = None

        self.cards_db: dict[str, dict[str, Any]] = dict(cards or {})
        self.ability_library = AbilityLibrary(definitions=abilities or [])

        self.event_bus = EventBus()
        self.resolver = Resolver(self)
        self._register_core_listeners()

    @classmethod
    def from_data_files(
        cls,
        num_lanes: int = 3,
        cards_path: str | Path | None = None,
        abilities_path: str | Path | None = None,
        starting_hp: int = 20,
    ) -> "GameState":
        """Build state from project card/ability JSON files."""
        data_dir = Path(__file__).resolve().parents[1] / "data"
        cards_file = Path(cards_path) if cards_path is not None else data_dir / "cards.json"
        abilities_file = Path(abilities_path) if abilities_path is not None else data_dir / "abilities.json"

        cards_payload = cls._read_json(cards_file)
        abilities_payload = cls._read_json(abilities_file)

        cards = {
            str(card["id"]): card
            for card in cards_payload.get("cards", [])
            if isinstance(card, dict) and "id" in card
        }
        abilities = [entry for entry in abilities_payload.get("abilities", []) if isinstance(entry, dict)]

        return cls(
            num_lanes=num_lanes,
            cards=cards,
            abilities=abilities,
            starting_hp=starting_hp,
        )

    @staticmethod
    def _read_json(file_path: Path) -> dict[str, Any]:
        if not file_path.exists():
            return {}
        return json.loads(file_path.read_text(encoding="utf-8"))

    @staticmethod
    def opponent(owner: str) -> str:
        """Return opposing owner label."""
        return Lane.opponent(owner)

    def _register_core_listeners(self) -> None:
        for event_name in GAME_EVENTS:
            self.event_bus.register(event_name, self._dispatch_abilities, priority=-10)

        self.event_bus.register("on_death", self._remove_dead_creature, priority=100)
        self.event_bus.register("on_turn_end", self._tick_modifiers_for_owner, priority=50)

    def _dispatch_abilities(self, event: str, **kwargs: Any) -> None:
        """Trigger all matching abilities for all creatures in stable order."""
        context = dict(kwargs)
        context.pop("state", None)
        creatures = list(self.iter_creatures())
        for creature in creatures:
            if not creature.alive:
                continue
            for ability_id in creature.ability_ids:
                ability = self.ability_library.get(ability_id)
                if ability is None:
                    continue
                if ability.should_trigger(event=event, owner=creature, context=context):
                    ability.execute(self, creature, event=event, **context)

    def _remove_dead_creature(self, event: str, **kwargs: Any) -> None:
        """Cleanup lane slot when a creature dies."""
        actor = kwargs.get("actor")
        if not isinstance(actor, Creature):
            return
        lane_index = actor.lane_index
        if lane_index is None or lane_index < 0 or lane_index >= len(self.lanes):
            return

        removed = self.lanes[lane_index].remove_creature_instance(actor)
        if removed:
            self.history.append(f"{event}:{actor.owner}:{actor.name}:lane={lane_index}")

    def _tick_modifiers_for_owner(self, event: str, **kwargs: Any) -> None:
        """Advance modifier durations for creatures on ending side."""
        owner = kwargs.get("owner")
        if owner not in {"player", "enemy"}:
            return

        for creature in self.iter_creatures(owner=owner):
            creature.tick_modifiers()

    def iter_creatures(self, owner: str | None = None) -> Iterable[Creature]:
        """Yield creatures in deterministic lane/side order."""
        for lane in self.lanes:
            player_creature = lane.get_creature("player")
            enemy_creature = lane.get_creature("enemy")

            if owner is None or owner == "player":
                if player_creature is not None:
                    yield player_creature

            if owner is None or owner == "enemy":
                if enemy_creature is not None:
                    yield enemy_creature

    def get_hand(self, owner: str) -> list[str]:
        """Return mutable hand list for owner."""
        if owner == "player":
            return self.player_hand
        if owner == "enemy":
            return self.enemy_hand
        raise ValueError(f"Unknown owner: {owner}")

    def draw_card(self, owner: str, card_id: str) -> None:
        """Add a card ID to hand."""
        if card_id not in self.cards_db:
            raise ValueError(f"Card id not found: {card_id}")
        self.get_hand(owner).append(card_id)

    def draw_starting_hand(self, owner: str, count: int = 3) -> None:
        """Draw deterministic opening hand from sorted card IDs."""
        if not self.cards_db:
            return
        card_ids = sorted(self.cards_db.keys())
        for index in range(max(0, int(count))):
            self.draw_card(owner, card_ids[index % len(card_ids)])

    def create_creature_from_card(self, card_id: str, owner: str) -> Creature:
        """Instantiate a creature from a card definition."""
        card = self.cards_db.get(card_id)
        if card is None:
            raise ValueError(f"Card id not found: {card_id}")

        return Creature(
            card_id=str(card_id),
            name=str(card.get("name", card_id)),
            owner=owner,
            atk=int(card.get("atk", 0)),
            hp=int(card.get("hp", 1)),
            countdown=int(card.get("countdown", 0)),
            ability_ids=list(card.get("abilities", [])),
        )

    def summon_creature(self, owner: str, lane_index: int, card_id: str) -> Creature:
        """Create and place a creature in a lane, then dispatch summon event."""
        if lane_index < 0 or lane_index >= len(self.lanes):
            raise ValueError(f"Invalid lane index: {lane_index}")

        lane = self.lanes[lane_index]
        if not lane.has_empty_slot(owner):
            raise ValueError(f"Lane {lane_index} slot for {owner} is occupied")

        creature = self.create_creature_from_card(card_id=card_id, owner=owner)
        lane.add_creature(creature, owner=owner)
        self.event_bus.dispatch(
            "on_summon",
            state=self,
            owner=owner,
            actor=creature,
            lane_index=lane_index,
            card_id=card_id,
        )
        self.history.append(f"on_summon:{owner}:{creature.name}:lane={lane_index}")
        return creature

    def start_turn(self, owner: str) -> None:
        """Start a turn: increment number, tick countdowns, dispatch event."""
        if self.winner is not None:
            return

        self.turn_number += 1
        self.active_player = owner
        for lane in self.lanes:
            lane.tick_countdowns(owner=owner)

        self.event_bus.dispatch("on_turn_start", state=self, owner=owner)
        self.history.append(f"on_turn_start:{owner}:turn={self.turn_number}")

    def end_turn(self, owner: str) -> None:
        """End a turn and dispatch end event."""
        if self.winner is not None:
            return

        self.event_bus.dispatch("on_turn_end", state=self, owner=owner)
        self.history.append(f"on_turn_end:{owner}:turn={self.turn_number}")

    def deal_player_damage(self, owner: str, amount: int, source: Creature | None = None) -> int:
        """Deal damage directly to player HP and evaluate winner."""
        raw_amount = max(0, int(amount))
        if raw_amount <= 0:
            return 0

        before = self.player_hp[owner]
        self.player_hp[owner] = max(0, before - raw_amount)
        dealt = before - self.player_hp[owner]

        source_name = "unknown" if source is None else source.name
        self.history.append(f"player_damage:{owner}:{dealt}:source={source_name}")

        if self.player_hp[owner] <= 0:
            self.winner = self.opponent(owner)
            self.history.append(f"winner:{self.winner}")

        return dealt

    def get_valid_actions(self, owner: str) -> list[dict[str, Any]]:
        """Return deterministic list of valid actions for the owner."""
        actions: list[dict[str, Any]] = []

        for lane in self.lanes:
            attacker = lane.get_creature(owner)
            if attacker is not None and attacker.is_ready:
                actions.append({"type": "attack", "lane": lane.index})

        hand = self.get_hand(owner)
        if hand:
            for lane in self.lanes:
                if not lane.has_empty_slot(owner):
                    continue
                for hand_index, card_id in enumerate(hand):
                    actions.append(
                        {
                            "type": "summon",
                            "lane": lane.index,
                            "hand_index": hand_index,
                            "card_id": card_id,
                        }
                    )

        actions.append({"type": "end_turn"})
        return actions

    def _remove_card_from_hand(
        self,
        owner: str,
        hand_index: int | None,
        card_id: str | None,
    ) -> str | None:
        hand = self.get_hand(owner)

        if hand_index is not None and 0 <= hand_index < len(hand):
            chosen = hand[hand_index]
            if card_id is not None and chosen != card_id:
                return None
            return hand.pop(hand_index)

        if card_id is not None:
            for index, candidate in enumerate(hand):
                if candidate == card_id:
                    return hand.pop(index)

        return None

    def apply_action(self, owner: str, action: dict[str, Any] | None) -> dict[str, Any]:
        """Apply one action for owner and return resolution info."""
        result: dict[str, Any] = {
            "success": False,
            "enemy_creatures_killed": 0,
            "player_creatures_killed": 0,
            "direct_damage": 0,
            "message": "",
        }

        if self.winner is not None:
            result["message"] = "Game already finished"
            return result

        action = action or {"type": "end_turn"}
        action_type = str(action.get("type", "end_turn"))

        if action_type == "end_turn":
            result["success"] = True
            result["message"] = "Turn ended"
            return result

        if action_type == "summon":
            lane_index = int(action.get("lane", -1))
            hand_index = action.get("hand_index")
            hand_index = int(hand_index) if hand_index is not None else None
            requested_card_id = action.get("card_id")
            requested_card_id = None if requested_card_id is None else str(requested_card_id)

            removed_card = self._remove_card_from_hand(
                owner=owner,
                hand_index=hand_index,
                card_id=requested_card_id,
            )
            if removed_card is None:
                result["message"] = "Card not available in hand"
                return result

            try:
                self.summon_creature(owner=owner, lane_index=lane_index, card_id=removed_card)
            except ValueError as exc:
                self.get_hand(owner).append(removed_card)
                result["message"] = str(exc)
                return result

            result["success"] = True
            result["message"] = f"Summoned {removed_card} in lane {lane_index}"
            return result

        if action_type == "attack":
            lane_index = int(action.get("lane", -1))
            attack_result = self.resolver.resolve_lane_attack(
                lane_index=lane_index,
                attacker_owner=owner,
            )
            result.update(attack_result)
            return result

        result["message"] = f"Unknown action type: {action_type}"
        return result

    def take_turn(self, owner: str, action: dict[str, Any] | None) -> dict[str, Any]:
        """Run full turn lifecycle for one owner."""
        self.start_turn(owner)
        result = self.apply_action(owner, action)
        self.end_turn(owner)
        return result

    def count_creatures(self, owner: str) -> int:
        """Count alive creatures for one owner."""
        return sum(1 for creature in self.iter_creatures(owner=owner) if creature.alive)

    def is_terminal(self) -> bool:
        """Whether game has a winner."""
        return self.winner is not None

    def to_dict(self) -> dict[str, Any]:
        """Serialize full game state."""
        return {
            "turn": self.turn_number,
            "active_player": self.active_player,
            "winner": self.winner,
            "player_hp": dict(self.player_hp),
            "lanes": [lane.to_dict() for lane in self.lanes],
            "hand": {
                "player": list(self.player_hand),
                "enemy": list(self.enemy_hand),
            },
            "history": list(self.history),
        }


# TODO: add deterministic mulligan/deck system if full match simulation is needed.
