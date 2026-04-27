# Cards and Meta: Kings and Legends / Rise of Mythos / King's Call

## Card Overview

The game's card system is the central mechanic. Cards come in two main categories — **Creature Cards** and **Skill Cards** — and span multiple rarity tiers. Card count has grown significantly across versions:
- Kings and Legends (GameSpree, 2012–2021): ~250–900+ unique cards cited in different eras
- Rise of Mythos (GameFuse, 2013–2019): 1,500+ troops referenced in mobile version description; multiple expansion sets
- Kings Call H5 (current, v1.1.7.0 per GitHub analysis): **7,785 playable cards**, **6,700 creature combat stats** in the APK database

---

## Card Types

### Creature Cards
- Represent units deployed on the battlefield grid
- Each has: ATK (attack), DEF (defense/HP), movement speed, attack type, faction/race, special abilities
- Categorized by race/faction (Human, Elf, Halfblood, Undead, Goblin, Ogre, Beast, Outsider, Dragon, Angel, Demon, etc.)
- Most also have **damage type**: Physical (dominant at 57.8%), Fire, Arcane, Holy, Frost, Lightning, Shadow

### Skill Cards
- Class-specific; each of the 4 classes (Warrior, Ranger, Mage, Priest) has exclusive skills
- Cannot be used by players of a different class
- Examples:
  - Warrior: Encourage, Protect, Command abilities
  - Ranger: Tactic: Sunder Armour, Poison effects
  - Mage: Fireball, Lightning Storm, Petrify, Frost Nova
  - Priest: Guardian Angel, Sanctuary, Inspiration

### Hybrid Creature Cards (added v2.0)
- Created through the Synthesis system (combining two different-race creatures)
- Result is a random Hybrid of a specific race combination
- Distinct card category introduced December 2015 (non-Chinese servers)

---

## Card Rarity System

Cards are rated by **stars** and **color**, from lowest to highest:

| Tier | Stars | Color   | Notes                                     |
|------|-------|---------|-------------------------------------------|
| Common    | 1 ★   | White   | Most abundant; beginner-accessible        |
| Good      | 2 ★★  | Green   | Slightly better; widely available         |
| Rare      | 3 ★★★ | Blue    | Meaningful power increase                 |
| Epic      | 4 ★★★★| Purple  | Strong cards; harder to obtain F2P        |
| Legendary | 5 ★★★★★| Orange | Very powerful; primarily from paid packs  |
| Godlike   | 6 ★★★★★★| Red  | Highest standard rarity; pay-gated        |
| Awakened  | N/A (above Godlike) | Special artwork | Introduced v1.7; enhanced stats + reworked abilities |

**Key notes on rarity access:**
- Cards above Legendary (Godlike and Awakened) are typically only obtainable through VIP-locked card packs
- Free-to-play players are practically limited to Epic rarity and below for competitive cards
- Godlike cards are locked behind VIP rank 5+ (King's Pack in Rise of Mythos)
- Awakened cards in Kings Call have been cited as costing approximately $500 per card to upgrade

---

## Card Evolution / Upgrade System

Cards can be upgraded through the **Alchemy Lab**:
1. **Combine**: Merge 2+ identical cards of the same rarity to promote to next rarity tier (e.g., 2x Rare → 1x Epic). Chance-based; fails produce materials.
2. **Extract**: Disassemble unwanted cards into fusion materials.
3. **Fuse**: Use specific material recipes to craft target cards.

The GitHub analysis of Kings Call H5 identifies a **6-tier card evolution system** within the game code.

For **Awakened** cards:
- Awakened represents the ultimate evolution beyond Godlike
- Stats are elevated above their Godlike equivalents
- Some Awakened cards have reworked/improved abilities (not just stat bumps)
- Elite and Skill cards get new artwork when Awakened
- Cooldowns remain the same as lower-tier equivalents
- Awakened was introduced in Version 1.7

---

## Card Packs

Rise of Mythos / Kings and Legends packs (historical):

| Pack Name      | Cost (Silver) | Cost (Gold/Ruby) | Access        | Notable Contents                                   |
|---------------|--------------|-------------------|---------------|----------------------------------------------------|
| Novice's Pack  | 1,000 Silver  | 12 Gold           | All players   | Common and Good cards only; beginner focused       |
| Standard Pack  | 5,000 Silver  | 58 Gold           | Level 10+     | Common through Rare drops; widely available        |
| Elite Pack     | 15,000 Silver | 98 Gold           | Level 20+ or VIP 1 | Better drop rates for Rare/Epic                |
| Master's Pack  | N/A           | 198 Gold/Ruby     | VIP 3+        | Guaranteed Epic minimum; Legendary possible        |
| King's Pack    | N/A           | 598 Gold/Ruby     | VIP 5+        | Epic/Legendary focus; Godlike possible             |
| Mythos Pack    | N/A           | Variable          | High VIP      | Top-tier pack; best drop rates                     |

**Kings Call (current version)** note:
- Has 4 basic packs with large card pools available to all players regardless of VIP
- Additional VIP-locked packs exist
- Novice's Pack in Kings Call exclusively contains Human, Elf, Goblin, and Ogre race creatures, plus skills for all 4 classes
- VIP system expanded to VIP 13 (as of 2024–2025), up from VIP 12 at launch

**Raw Pack Data**: The Rise of Mythos wiki includes a "Raw Pack Data" page documenting exact card contents per pack. The Kings Call H5 APK analysis identifies **20+ gacha pools** in the game code.

---

## Card Acquisition Methods

- **Card packs** (both Silver-purchasable and premium Gold/Ruby packs)
- **Quest rewards** (completing story/daily quests)
- **Auction House** (player-to-player trading using Rubies)
- **Ascension Tower Shop** (Tower Coins → specific cards)
- **Challenge Hall** (card flips at end of boss fights)
- **PvP Arena** (exclusive PvP reward cards)
- **Fusion** (alchemy lab crafting)
- **Synthesis** (Hybrid creature creation)
- **Special events** (limited-time event cards, sometimes cash-only)
- **Daily login rewards** (minor card fragments/materials)

---

## Known Powerful / Meta Cards

No formal tier list was found during research. Community sources identify the following meta dynamics:

### Rise of Mythos Era (2013–2019)
- High-value cards were consistently those with self-sustaining abilities: Vampires (life steal), Ghosts (return after death), Zombie regeneration
- Dragons (introduced v1.5) became immediately dominant — Fire, Ice, Lightning, Light variants each strong in their element
- Angels (introduced v1.5) as top-tier support/healing
- The "shuffle graveyard into deck" card cited in GameFAQs review as game-breaking: with a 30-card deck limit, running out of cards is a common loss condition in control mirrors, making this card a solo win condition in grind-heavy matchups
- Awakened cards are categorically above Godlike in power; access was heavily monetized

### Kings Call Era (2023–present)
- Top cards locked behind $500+ Awakened upgrade paths per community reports
- "Awakening elite hero cards" cited at ~$500 each in Steam reviews
- NA1 server described as "whale central" by community, indicating power gap between spending tiers
- No public tier list found; community discussions on Steam mention P2W dominance in high-level play

---

## Notable Card Mechanics

From the Kings Call H5 APK analysis (GitHub: zhengboon/kingscallh5stuff), the game code contains:
- **552 skills/abilities** documented
- **372 status effects**
- **2,649 compound effects** (combinations of effects triggered by conditions)
- **33+ AOE (Area of Effect) geometry patterns** (different spell/ability AoE shapes)
- **5 dragon wing variants** and **5 dragon scale variants** (cosmetic/subtype differentiation for Dragon race)
- **Pet companion system** with growth curves (added 2024)

---

## Card Database Resources

- [Rise of Mythos Wiki — Cards page](https://rise-of-mythos.fandom.com/wiki/Cards)
- [Rise of Mythos Wiki — Races](https://rise-of-mythos.fandom.com/wiki/Races)
- [Rise of Mythos Wiki — Awakened](https://rise-of-mythos.fandom.com/wiki/Awakened)
- [Rise of Mythos Wiki — Raw Pack Data](https://rise-of-mythos.fandom.com/wiki/Raw_Pack_Data)
- [Kings and Legends Wiki — Cards](https://kings-and-legends.fandom.com/wiki/Kings_and_Legends_Wiki)
- [NamuWiki — Rise of Mythos Unit Cards](https://en.namu.wiki/w/Rise%20of%20Mythos/%EC%9C%A0%EB%8B%9B%20%EC%B9%B4%EB%93%9C) (Korean)
- [GitHub — kingscallh5stuff APK analysis](https://github.com/zhengboon/kingscallh5stuff)
- [GameFAQs — Rise of Mythos detailed review (card mechanics breakdown)](https://gamefaqs.gamespot.com/webonly/691922-rise-of-mythos/reviews/160836)

---

## Meta Notes

### What makes the game Pay-to-Win at high levels
1. **VIP-locked packs** gate the best rarities (Godlike, Awakened) behind significant spending
2. **Event-exclusive cards**: New powerful cards released during limited 2-day windows, purchasable with real money only. Free versions of these cards (Epic or lower) are available cheaply in the Auction House but are fundamentally weaker
3. **No disclosed drop rates**: Community complaints that packs don't list their actual card drop probabilities
4. **VIP level gates**: Cards like King's Pack (VIP 5 required), Master's Pack (VIP 3 required) simply aren't available to non-paying players regardless of playtime

### Free-to-Play ceiling
- F2P players realistically cap out at Epic tier cards through grinding
- Standard Pack (available with Silver) drops up to Rare reliably
- Elite Pack (available with Silver at level 20 or VIP 1) offers better Epic odds
- Competitive PvP at high ranks is dominated by players with Legendary, Godlike, and Awakened cards
