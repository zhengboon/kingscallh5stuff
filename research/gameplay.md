# Gameplay: Kings and Legends / Rise of Mythos / King's Call

## Core Concept

Kings and Legends / Rise of Mythos / Kings Call is a browser-based / H5 collectible card game (CCG) that blends tactical lane-based combat with MMO elements. The core loop involves:
1. Collecting creature and skill cards
2. Building a deck (max 30 cards, min 15)
3. Fighting through PvE campaigns and PvP matches on a grid-based battlefield
4. Upgrading your kingdom/city to access better resources
5. Progressing through multiple game modes for rewards

---

## Combat System

### The Battlefield Grid
- Combat takes place on a **4-lane grid**, each lane comprised of **12 squares** across.
- Players deploy creature cards into lanes from their side of the board.
- The opponent's forces start on the opposite side.
- The goal is to advance your creatures across the grid until they reach the enemy hero and reduce the enemy's HP to 0.

### Turn Structure
- The game is **turn-based**.
- Each turn, creatures move forward on the grid (default: 2 spaces per turn if not blocked).
- When two creatures occupy the same square, they fight.
- Creatures fight to the death; the winner continues advancing.
- Special creature abilities can modify movement speed, attack range, and damage type.

### Combat Mechanics
- **Default attack range**: 2 grid squares.
- **Melee vs Ranged**: Some creatures can attack from distance; ranged units are the backbone of "glass cannon" strategies.
- **Special abilities** (examples):
  - **Vigilance**: Can attack enemies around and behind the creature.
  - **Armored/Defensive**: Reduces all physical damage received by 1.
  - **Cavalry** (Human-specific): +2 movement speed bonus.
  - **Flying**: Lets the creature bypass ground-unit obstacles (introduced with Dragon race in v1.5).
  - **Poison**: Deals damage over time (Ranger and Goblin specialty).
  - **Regeneration**: Heals HP each turn (Ogre specialty).

### Auto-Combat
- There is an auto-play function for combat, but it is not reliable for challenging content.
- Manual play is generally required for difficult PvP and Challenge Hall battles.
- Auto-pick deck feature exists (computer selects "most powerful" cards) but is not optimal for strategic play.

---

## Character Classes

Players choose one of **4 classes** at character creation. Each class has its own exclusive set of **Skill Cards** that cannot be used by other classes. Class choice significantly influences playstyle.

### Warrior
- **Theme**: Strength, leadership, front-line combat
- **Role**: Buff allies, rally creatures, deal direct damage to enemy creatures
- **Key Skills**: Encourage (boosts Attack), Protect (boosts Defense), Command abilities (shift how troops attack or take damage)
- **Playstyle**: Tank-and-buff; supports a strong front line

### Ranger
- **Theme**: Tactical precision, poison, debuffs
- **Role**: Weaken and control enemy forces; deal ongoing damage
- **Key Skills**: Tactic: Sunder Armour (reduces enemy defense), Poison-based abilities
- **Playstyle**: Control and attrition; weakens enemies before they can engage

### Mage
- **Theme**: Elemental destruction, mind control
- **Role**: Area damage, direct damage, crowd control
- **Key Skills**: Fireball, Lightning Storm (direct damage spells), Petrify, Frost Nova (impede enemy movement)
- **Playstyle**: Glass cannon burst damage; prevents enemies from reaching your hero

### Priest
- **Theme**: Divine healing, defense, inspiration
- **Role**: Keep powerful creatures alive; buff elite and "King" tier cards
- **Key Skills**: Guardian Angel, Sanctuary (protective spells), Inspiration abilities
- **Playstyle**: Defensive synergy; run Kings and Elites with protective spells

---

## Factions / Races

Players can include creature cards from **up to 10+ factions** (expanded over time from the original 7). Cards from different factions can be freely mixed in a deck. Using creatures from the same faction can enable synergy bonuses.

### Original 7 Factions (Base Game, Kings and Legends / Rise of Mythos v1.0)

1. **Humans**
   - Armored infantry, healing Templars, swift Cavalry
   - Cavalry grants +2 movement bonus
   - Tenacious and coordinated fighters
   - Synergy with Priest class

2. **Elves**
   - Ranged archers, elemental Mages
   - High damage but low HP (fragile)
   - Prefer ranged attacks; vulnerable to close-range rushes

3. **Halfbloods**
   - Scout Feles, lance-wielding Centaurs, flying Tengu
   - Excel at guerrilla tactics
   - Diverse mix of abilities

4. **Undead**
   - Self-reviving Zombies, life-stealing Vampires, Ghosts (which can return after death)
   - Strong endurance in extended fights
   - Synergize well with Ranger's poison mechanics

5. **Goblins**
   - Poison-expert horde
   - Counter-attack abilities
   - Generally low-cost, high-quantity strategy

6. **Ogres**
   - Regenerating brutes; gain power when enraged
   - Stun capability
   - High defense; ideal for tank builds

7. **Beasts**
   - Swift movement (hounds)
   - Disease-carrying creatures
   - Elemental attacks on some variants

### Expanded Factions (Added in Later Versions)

8. **Outsiders** (later version)
   - Not allied with major races
   - Unique and powerful abilities but poor group synergy
   - Independently powerful cards

9. **Dragons** (added v1.5)
   - 4 subtypes: Fire, Ice, Lightning, Light
   - Damage corresponds to their element type
   - Most have Flying ability
   - High stats; endgame-tier creatures

10. **Angels** (added v1.5)
    - Powerful healers
    - Holy damage to shred enemy resistances
    - Support-oriented but offensively capable

11. **Demons** (added later, exact version unclear)
    - Opposite of Angels
    - Shadow/dark damage

**Note**: The Kings Call H5 APK analysis via the GitHub repo (zhengboon/kingscallh5stuff) documents **7,785 playable cards** and **6,700 creature combat stats**, indicating substantial content expansion beyond the original game.

---

## Deck Building

- Maximum deck size: **30 cards**
- Minimum deck size: **15 cards**
- Can include **creature cards** and **skill cards** (class-specific)
- **No more than 3 copies** of any card with the same name
- No faction restrictions — any race can be combined freely
- Strategy tip: Pure-faction decks can leverage racial synergy bonuses; mixed decks offer versatility

### Deck Archetypes (community-identified)
- **Rush/Aggro**: Heavy on Cavalry (Human) and fast Beasts; overwhelm the opponent before they can set up
- **Ranged/Glass Cannon**: Ranged Archers and Elves; maximum damage output from distance; fragile to close-range threats
- **Control/Poison**: Ranger class with Goblin and Undead creatures; slow the opponent down and win through attrition
- **Tank/Buff**: Warrior or Priest with Ogres and Humans; outlast opponent through superior healing/defense
- **Mage Swarm**: Mage with Priests and front-line Mages; strong spell damage

---

## Game Modes

### PvE — Campaign / Story Mode
- Story-based battles protecting Silver Heron Ridge
- Multiple regions/maps to progress through
- Tutorial takes place in Silver Heron Ridge (first map area)
- AI opponents of increasing difficulty
- Rewards: experience, silver, cards

### PvE — Ascension Tower
- 50 levels of solo challenges (or more in later versions)
- Available to heroes at level 25
- Free attempt once per day; additional attempts via **Tower Tickets**
- Weekly reset (progress resets to Level 1 each week)
- Rewards: Tower Coins (redeemable at Tower Shop for cards and items)

### PvE — Challenge Hall (Cooperative Boss Fights)
- Up to 4 players team up against powerful boss enemies
- Two main difficulties (plus Casual mode for Shimmering Cave)
- Each battle has 2 stages
- A small chance exists that Stage 2 will trigger an "Awakened" boss (using Godlike/Awakened cards, much harder)
- Rewards: Experience, Silver, Reputation; card flips at end of battle for extra rewards (Soul Shards, Awakened Fragments, special saddles)

### PvP — Arena
- **1v1 Duels**: Individual ranked and practice play
- **2v2 Team**: Partner-up matches
- **4v4 Guild Showdown**: Guild-based team competition proving guild dominance
- All PvP modes offer ranked play with ladder rankings
- Special PvP-exclusive reward cards can be earned through competition

### Social / Guild System
- Players join or create guilds
- Guild donation system (donate Silver for guild wealth/experience and personal contribution)
- Guild Showdown is the primary guild-vs-guild activity
- Guild skills system exists (the GitHub analysis of the Kings Call APK identifies 200+ guild skills)

---

## Kingdom / City Building

- Players maintain a "kingdom" with various buildings:
  - **Blacksmith**: Crafting/upgrading equipment
  - **Seaport**: Trade/card acquisition resources
  - **Alchemist**: Card combination and upgrade
  - **Alchemy Lab**: Primary card upgrade facility
  - **City Hall**: Central building governing overall city level and unlock gates
- Resources gathered include Silver (primary F2P currency), earned through gameplay
- Kingdom level gates progression (e.g., Auction House accessible at level 15/35)

---

## Card Upgrade Systems

### Alchemy Lab
The central card upgrading facility with three functions:

1. **Combine**: Combine 2+ cards of the same name and rank to create a card of higher rank. Additional same-name cards can be added to increase success chance. Costs Silver. Higher Alchemy Lab level = higher success chance and access to higher tier upgrades.

2. **Extract**: Break down unwanted cards into materials (used for Fuse function). Failed combination attempts also produce materials.

3. **Fuse**: Use extracted materials (following specific recipes) to create new cards.

### Synthesis / Hybridization
- The **Synthesizer** allows fusing two creatures of different races into a random **Hybrid** creature.
- Both cards must be the same rarity.
- Requires a **Synthesize Crystal** or **Advanced Synthesize Crystal**.
- Hybrid creatures are a distinct race category.
- Synthesis was introduced in **Version 2.0** (December 2015 on non-Chinese servers).

### Card Evolution Tiers (Kings Call H5 / modern version)
The GitHub repository analysis indicates a **6-tier card evolution system**, which aligns with the rarity tiers (Common → Good → Rare → Epic → Legendary → Godlike) plus Awakened as an additional evolution above Godlike.

---

## Pets (Kings Call Modern Version)
- Pet system launched September 10, 2024 in Kings Call
- Unlocks when hero level reaches level 20
- Pets provide passive bonuses
- Community expressed concerns about pets creating additional P2W imbalance in PvP

---

## Damage Types (Kings Call H5 APK Data)
From the GitHub repository analysis of the Kings Call APK:
- **Physical**: 57.8% (3,873 creatures)
- **Fire**: 10.6% (709 creatures)
- **Arcane**: 7.6% (507 creatures)
- **Holy**: 7.2% (482 creatures)
- **Frost**: 6.5% (433 creatures)
- **Lightning**: 6.3% (421 creatures)
- **Shadow**: 4.1% (275 creatures)

---

## AOE Patterns
The GitHub repository identified **33+ AOE (Area of Effect) geometry patterns** in the Kings Call H5 game data, indicating a complex spell and ability system affecting multiple grid squares.

---

## Sources

- [F2P.com — Rise of Mythos](https://www.f2p.com/games/rise-mythos/)
- [MMOReviews — Rise of Mythos](https://www.mmoreviews.com/rise-of-mithos/)
- [OnRPG — Kings and Legends](https://www.onrpg.com/games/kings-and-legends/)
- [Rise of Mythos Fandom Wiki — Classes](https://rise-of-mythos.fandom.com/wiki/Classes)
- [Rise of Mythos Fandom Wiki — Races](https://rise-of-mythos.fandom.com/wiki/Races)
- [Rise of Mythos Fandom Wiki — Ascension Tower](https://rise-of-mythos.fandom.com/wiki/Ascension_Tower)
- [Rise of Mythos Fandom Wiki — Challenge Hall](https://rise-of-mythos.fandom.com/wiki/Challenge_Hall)
- [Rise of Mythos Fandom Wiki — Alchemy Lab](https://rise-of-mythos.fandom.com/wiki/Alchemy_Lab)
- [GitHub repo: zhengboon/kingscallh5stuff](https://github.com/zhengboon/kingscallh5stuff)
- [HubPages — Rise of Mythos Beginner Guide](https://discover.hubpages.com/games-hobbies/Rise-of-Mythos-Guide-Tips-for-Beginners-to-the-RPG-Card-Game)
- [Kongregate Forum — Newbie Guide to Guild Showdown](http://www.kongregate.com/forums/12-kongregate-multiplayer-games/topics/420896-rise-of-mythos-newbie-guide-to-guild-showdown-part-i-key-tips-building-a-balanced-4v4-deck)
- [Steam Community — Kings Call Reviews](https://steamcommunity.com/app/2674290/reviews/)
- [Engadget — Rise and Shiny: Rise of Mythos (2013)](https://www.engadget.com/2013-10-13-rise-and-shiny-rise-of-mythos.html)
