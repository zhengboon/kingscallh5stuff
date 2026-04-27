from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from cardbot.engine.ability import AbilityLibrary
from cardbot.engine.creature import Creature
from cardbot.engine.event_bus import EventBus
from cardbot.engine.lane import Lane
from cardbot.engine.modifier import Modifier
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
    """Deterministic in-memory mirror of match state and rule resolution.

    The live game uses a 4-lane board, so ``num_lanes`` defaults to 4. The
    2- and 3-lane modes are kept for unit-test ergonomics and reduced state
    spaces during early RL training; they do not match real King's Call.
    """

    def __init__(
        self,
        num_lanes: int = 4,
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
        num_lanes: int = 4,
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

    @classmethod
    def from_snapshot(
        cls,
        snapshot: dict[str, Any],
        num_lanes: int | None = None,
        cards_path: str | Path | None = None,
        abilities_path: str | Path | None = None,
    ) -> "GameState":
        """Build a game state from a serialized snapshot payload."""
        payload = dict(snapshot or {})
        lane_payloads = payload.get("lanes", [])
        inferred_lanes = len(lane_payloads) if isinstance(lane_payloads, list) else 4
        lane_count = int(num_lanes if num_lanes is not None else payload.get("num_lanes", inferred_lanes or 4))

        if lane_count not in (2, 3, 4):
            raise ValueError("Snapshot lane count must be 2, 3, or 4")

        state = cls.from_data_files(
            num_lanes=lane_count,
            cards_path=cards_path,
            abilities_path=abilities_path,
        )

        state.turn_number = max(0, int(payload.get("turn", 0)))

        active_player = str(payload.get("active_player", "player"))
        state.active_player = active_player if active_player in {"player", "enemy"} else "player"

        winner = payload.get("winner")
        state.winner = str(winner) if winner in {"player", "enemy"} else None

        player_hp = payload.get("player_hp", {})
        if isinstance(player_hp, dict):
            for owner in ("player", "enemy"):
                if owner in player_hp:
                    state.player_hp[owner] = max(0, int(player_hp[owner]))

        hand = payload.get("hand", {})
        if isinstance(hand, dict):
            for owner in ("player", "enemy"):
                owner_hand = hand.get(owner, [])
                if isinstance(owner_hand, list):
                    state.get_hand(owner).clear()
                    state.get_hand(owner).extend(str(card_id) for card_id in owner_hand)

        if not isinstance(lane_payloads, list):
            return state

        for lane_index, lane_payload in enumerate(lane_payloads):
            if lane_index >= lane_count or not isinstance(lane_payload, dict):
                continue
            lane = state.lanes[lane_index]
            for owner in ("player", "enemy"):
                creature_payload = lane_payload.get(owner)
                if not isinstance(creature_payload, dict):
                    continue
                creature = state._creature_from_snapshot_payload(owner=owner, payload=creature_payload)
                if creature is None:
                    continue
                lane.add_creature(creature, owner=owner)

        return state

    @staticmethod
    def _read_json(file_path: Path) -> dict[str, Any]:
        if not file_path.exists():
            return {}
        return json.loads(file_path.read_text(encoding="utf-8"))

    @staticmethod
    def opponent(owner: str) -> str:
        """Return opposing owner label."""
        return Lane.opponent(owner)

    def _creature_from_snapshot_payload(self, owner: str, payload: dict[str, Any]) -> Creature | None:
        """Deserialize a creature snapshot into a Creature instance."""
        alive = bool(payload.get("alive", True))
        if not alive:
            return None

        card_id = str(payload.get("card_id", payload.get("name", "observed_unit")))
        base_atk = int(payload.get("base_atk", payload.get("atk", 0)))
        hp = max(0, int(payload.get("hp", 1)))
        max_hp = max(1, int(payload.get("max_hp", max(hp, 1))))
        base_countdown = max(0, int(payload.get("base_countdown", payload.get("countdown", 0))))
        countdown = max(0, int(payload.get("countdown", base_countdown)))
        ability_payload = payload.get("abilities", [])
        ability_ids = [str(ability_id) for ability_id in ability_payload] if isinstance(ability_payload, list) else []

        if card_id in self.cards_db:
            creature = self.create_creature_from_card(card_id=card_id, owner=owner)
            creature.name = str(payload.get("name", creature.name))
        else:
            creature = Creature(
                card_id=card_id,
                name=str(payload.get("name", card_id)),
                owner=owner,
                atk=base_atk,
                hp=max_hp,
                countdown=base_countdown,
                ability_ids=ability_ids,
            )

        creature.base_atk = base_atk
        creature.max_hp = max_hp
        creature.hp = min(hp, max_hp)
        creature.base_countdown = base_countdown
        creature.countdown = countdown
        creature.ability_ids = ability_ids
        creature.flat_damage_bonus = int(payload.get("flat_damage_bonus", 0))
        creature.alive = True

        creature.modifiers = []
        modifiers = payload.get("modifiers", [])
        if isinstance(modifiers, list):
            for item in modifiers:
                if not isinstance(item, dict):
                    continue
                duration_turns_raw = item.get("duration_turns")
                duration_turns = None if duration_turns_raw is None else int(duration_turns_raw)
                creature.modifiers.append(
                    Modifier(
                        id=str(item.get("id", "snapshot_modifier")),
                        name=str(item.get("name", "Snapshot Modifier")),
                        atk_bonus=int(item.get("atk_bonus", 0)),
                        max_hp_bonus=int(item.get("max_hp_bonus", 0)),
                        damage_bonus_per_hit=int(item.get("damage_bonus_per_hit", 0)),
                        duration_turns=duration_turns,
                        stacks=max(1, int(item.get("stacks", 1))),
                    )
                )

        return creature

    def _register_core_listeners(self) -> None:
        for event_name in GAME_EVENTS:
            self.event_bus.register(event_name, self._dispatch_abilities, priority=-10)

        self.event_bus.register("on_death", self._remove_dead_creature, priority=100)
        self.event_bus.register("on_turn_end", self._tick_modifiers_for_owner, priority=50)

    def _dispatch_abilities(self, event: str, **kwargs: Any) -> None:
        """Trigger all matching abilities for all creatures in stable order."""
        context = dict(kwargs)
        context.pop("state", None)
        context.pop("owner", None)
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

    @staticmethod
    def _serialize_creature_snapshot(creature: Creature | None) -> dict[str, Any] | None:
        if creature is None:
            return None
        return {
            "card_id": creature.card_id,
            "name": creature.name,
            "owner": creature.owner,
            "base_atk": creature.base_atk,
            "atk": creature.effective_atk,
            "hp": creature.hp,
            "max_hp": creature.max_hp,
            "countdown": creature.countdown,
            "base_countdown": creature.base_countdown,
            "abilities": list(creature.ability_ids),
            "modifiers": [modifier.to_dict() for modifier in creature.modifiers],
            "flat_damage_bonus": creature.flat_damage_bonus,
            "alive": creature.alive,
        }

    def to_snapshot(self) -> dict[str, Any]:
        """Serialize state into a compact payload that can be restored later."""
        return {
            "num_lanes": len(self.lanes),
            "turn": self.turn_number,
            "active_player": self.active_player,
            "winner": self.winner,
            "player_hp": dict(self.player_hp),
            "hand": {
                "player": list(self.player_hand),
                "enemy": list(self.enemy_hand),
            },
            "lanes": [
                {
                    "index": lane.index,
                    "player": self._serialize_creature_snapshot(lane.get_creature("player")),
                    "enemy": self._serialize_creature_snapshot(lane.get_creature("enemy")),
                }
                for lane in self.lanes
            ],
        }

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
