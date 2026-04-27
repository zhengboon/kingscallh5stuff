# Kings Call H5 — Deep Research File

> This file covers the H5 (browser) version specifically, plus comprehensive technical and platform details for Kings Call as of April 2026. Cross-reference with overview.md, technical.md, and history_timeline.md for shared background.

---

## 1. What Is "Kings Call H5"

The "H5" designation refers specifically to the HTML5 browser-playable version of Kings Call hosted at **xstargame.com**. "H5" is the industry-standard Chinese shorthand for HTML5 mobile/browser games, derived from the `<h5>` tag and used in Chinese game development to mean any lightweight browser-based game that runs without plugins.

Kings Call H5 is **NOT** the same service as the Steam version:
- H5 and Steam run on **separate servers with completely separate data**
- Accounts, progress, and purchases are NOT shared between the two
- H5 has a different card balance and card pool
- H5 focuses on "social features, cross-platform access, and quick play sessions"
- Steam focuses on "hardcore content"

This was confirmed in the official XstarGame FAQ: xstargame.com/news/index/details/id/73.html

---

## 2. H5 Version Access Methods

**To play Kings Call H5:**
- Open game directly via xstargame.com — no download or installation required
- Bookmark the official site or add it to your phone home screen for quick access
- Can also be accessed through TapTap (App ID: 33636339)

**Login options:**
- Guest login available (no account needed)
- **WARNING**: Guest login data is tied to browser cache — clearing cache or switching devices will lose your progress
- Strongly recommended to link your account to an email address early on
- Email-linked accounts are recoverable across devices and after cache clears

**Device Requirements:**
| Platform | Requirements |
|----------|-------------|
| PC Browser | Chrome 90+, 4GB RAM minimum |
| Android | Android 10+, stable connection |
| iOS | iOS 14+ |
| Network | Minimum 10 Mbps recommended |

---

## 3. H5 Card Balance Differences

The H5 version has a **modified card pool** compared to Steam:
- "Selected and rebalanced cards"
- "Some high-impact designs removed"
- Described as offering "a fresh meta with more balanced, stable, and strategic gameplay"

This means the H5 meta is different from the Steam meta. Cards that are dominant on Steam may not exist or may have different stats/abilities on H5.

**Practical implications:**
- Players migrating from Steam to H5 (or vice versa) are essentially starting a new game on a different balance patch
- Strategy guides written for Steam may not be fully applicable to H5
- The H5 version is positioned as more beginner/casual friendly due to the removal of high-impact designs

---

## 4. H5 Exclusive Features

Per official FAQ and announcements, H5 has unique features not found (or found differently) in the Steam version:

**First Login Bonuses**: Special rewards given when first logging into H5 (separate from Steam login rewards)

**Daily Check-In System**: H5 has its own daily check-in reward calendar

**Invite Campaign**: H5 offers invite-a-friend rewards separate from Steam

**Exclusive Redeem Codes**: Some gift codes are specifically issued for H5 and do not work on Steam (and vice versa). Server-specific codes (like "KCNA5" for NA5 server) are server-bound, not cross-platform.

**Cross-Platform Access**: H5 is specifically designed to be accessible from any device (PC browser, phone browser, tablet) without platform-specific installations.

---

## 5. H5 Platform — TapTap Listing

Kings Call H5 is also listed on TapTap:
- TapTap App ID: 33636339
- Rating base: Very small (approximately 3 ratings at time of research)
- TapTap is a Chinese alternative app store popular for game discovery
- The TapTap listing serves mainly as a discovery/download portal for the mobile H5 app wrapper

---

## 6. iOS App Store Version (Kings Call Mobile)

Kings Call is available on the Apple App Store as a native app wrapper around the H5 experience:

| Attribute | Detail |
|-----------|--------|
| App Name | Kings Call |
| Developer | Xstargame Limited |
| App Store ID | id6753857798 |
| Rating | 4.8/5 (only 4 ratings as of Jan 2025) |
| Version | 1.1.3 (as of January 24, 2025) |
| File Size | 428.7 MB |
| iOS Requirement | 12.0 or later |
| Age Rating | 16+ |
| Language | English |
| Price | Free (with in-app purchases) |

**In-App Purchase Pricing (iOS):**
| Item | Price |
|------|-------|
| 100 Gold | $0.99 |
| 500 Gold | $4.99 |
| 2,000 Gold | $19.99 |
| 5,000 Gold | $49.99 |
| 10,000 Gold | $99.99 |

**Note**: There are at least TWO distinct "King's Call" apps in the App Store:
1. `id1418694646` — Green Bee Creative LLC (a completely different game/app, not related to xstargame)
2. `id6753857798` — Xstargame Limited (the correct Kings Call by the developers discussed in this research)

Researchers and players must use ID `id6753857798` or search specifically for "Xstargame Limited" as the developer.

---

## 7. Google Play Version

| Attribute | Detail |
|-----------|--------|
| Package ID | com.xstar.kingscall |
| Developer | Xstargame Limited |
| Platform | Android |
| Status | Active as of April 2026 |
| Price | Free (with in-app purchases) |

---

## 8. Steam Version (Kings Call)

| Attribute | Detail |
|-----------|--------|
| Steam App ID | 2674290 |
| Release Date | December 25–26, 2023 |
| Developer | X Star Game Limited / Starlight Games |
| Price | Free to Play |
| Steam Deck | "Playable" (some limitations) |
| Windows | 64-bit Windows 10+, Core i3-3210, 4GB RAM, 2GB storage |
| macOS | macOS 10.12+, dual-core |
| Linux | Supported |

---

## 9. Kings Call H5 Technical Architecture

From the GitHub APK analysis (zhengboon/kingscallh5stuff):

**Game Engine**: Cocos Creator 3.8.7
- Cross-platform Chinese game engine
- Supports HTML5/browser, Android, iOS, Windows, Mac, Linux
- The game is fundamentally H5 with platform wrappers for each distribution channel

**Backend Services**:
- **Firebase Authentication** — user login and account management
- **Firebase Realtime Database** — game state synchronization
- **Wancms SDK** — analytics/monetization/platform management integration

**CDN**:
- `cdn.xstargame.com` — hot-update delivery
- Assets (card images, data tables) are streamed from CDN rather than bundled in the install
- This means the game can update card stats, balance, and events without requiring a client download

**APK Analysis Results** (version 1.1.7.0):
| Category | Count | File Size |
|----------|-------|-----------|
| Playable cards | 7,785 | 4.9 MB |
| Creature combat stats | 6,700 | 2.9 MB |
| Skills/abilities | 552 | 501 KB |
| Status effects | 372 | 169 KB |
| Compound effects | 2,649 | 1.4 MB |
| Gacha pools | 20+ | — |
| Guild skills | 200+ | — |
| AOE patterns | 33+ | — |
| Dragon wing variants | 5 | — |
| Dragon scale variants | 5 | — |

---

## 10. Related Games on the XstarGame Platform

XstarGame (xstargame.com) operates multiple games:

1. **Kings Call** — the primary English CCG (this game)
2. **Kings Call H5** — the H5/browser version of Kings Call
3. **Expedition Call** — another turn-based strategy card game by the same company; described as a flagship title alongside Kings Call
4. **火焰征程 (Flame Journey)** — the Chinese-language Steam version (Steam App 2492430); same game mechanics, Chinese-only, Mostly Negative reviews (37% positive, 437 reviews)
5. **王者神域 (KING GOD DOMAIN)** — Steam App 1383670 by Easy Joy Technology Limited; Asian-region version; Mixed reviews (54% positive, 46 reviews)

**Note on Expedition Call**: It is described as also being a "turn-based strategy card game," suggesting it may share DNA with Kings Call but is positioned as a separate product. Research has not fully characterized its relationship to the Kings Call IP.

---

## 11. Game Update Frequency and Maintenance Pattern

Kings Call on Steam (which shares server infrastructure with H5) follows a regular maintenance schedule:

**Regular Weekly Maintenance**: Typically Tuesdays, approximately 4:00–6:00 PM Beijing time (UTC+8)
- Maintenance windows used to push event content
- Servers maintained include NA1-8, EU1-8, AS1-3 (as of 2025)

**Event Rotation**: Each maintenance cycle rotates in new events:
- Weekly: Gold Rush (consumption-based rewards)
- Monthly: Supremacy events (featuring specific named cards)
- Monthly: Buy Points Get Rewards
- Regular: Daily Cumulative Recharge
- Special: Seasonal events (Halloween, New Year, National Day, April Fools)

**Content Update Type**: The game does NOT release traditional "patch notes." Instead, updates are delivered via:
1. Steam maintenance announcements (listing events that will be added)
2. CDN hot-updates (card data can be changed without a full client update)
3. Version reveal announcements (occasional roadmap posts)

**Version History Note**: The analyzed APK was version 1.1.7.0. Maintenance patch names reference server-specific dates (e.g., "Regularly Updated Maintenance (EU5) 20250325") rather than semantic version numbers.

---

## 12. New Game Modes Added in Kings Call (not in original Rise of Mythos)

Based on research, Kings Call H5/Steam has added several game modes not present or documented in the original Rise of Mythos or Kings and Legends versions:

**Magic Pet Realm** (launched September 2024):
- A dedicated game mode for pet-related content
- Players battle bosses (e.g., Cerberus, Gryphon) to earn pet fragments
- Rewards claimed through Event tab, then via mail
- Known bug: Some players reported claim buttons not working; fix involves contacting support with screenshots

**Pet System** (launched September 10, 2024):
- Unlocks at hero level 20
- Pets provide passive combat bonuses in battle
- Active in PvP modes (community criticized this as adding P2W randomness)
- Pet fragments earned through Magic Pet Realm and other activities

**Fool's Wonderland Dungeon** (announced/launched April 1, 2025):
- April Fools' Day special event dungeon
- First-clear rewards and completion rewards offered
- Available across all servers: NA1-5, EU1-5, AS1-3
- A new game mode type (dungeon exploration) distinct from previous boss fights

**Tower of Heaven** (referenced in November 2024 maintenance):
- Features "Big Shuck" as a boss
- Part of the recurring event rotation

**Mystical Valley**: Referenced as a game mode in update content
**Chaotic Wastes**: Existing mode (from Rise of Mythos era), retained in Kings Call
**Temple of Souls**: Listed as a game mode accessible in Kings Call
**VIP Dungeon**: VIP-exclusive game mode/content
**Mysterious Casket**: Listed as a feature/game mode

---

## 13. Hall of Fame System (Kings Call Exclusive Feature)

The Hall of Fame is a unique feature where VIP 12 players can design their own custom card:

**How It Works**:
1. A player at VIP 12 is invited/selected to design a Hall of Fame card
2. The player customizes the card's artwork and concept
3. The game team produces the card
4. Once completed, the **Awakened version** of the card is delivered directly to the VIP 12 designer
5. Other players can only obtain the **Godlike version** of Hall of Fame cards at most
6. The Awakened version remains permanently exclusive to the VIP 12 designer

**Availability for Regular Players**:
- Hall of Fame cards enter the guide/card index as Godlike-tier cards
- Players can obtain these Godlike versions over time
- Approximately **one new Hall of Fame card becomes available per month**
- Release timing is NOT tied to when the card appears in the guide — there is a deliberate delay
- This contrasts with Shan Hai Jing cards, which release through events simultaneously with guide additions

**Community Reaction**:
- One Steam user sarcastically noted "You must sell your family...to get those" in reference to the Awakened versions
- The system is seen as creating ultra-exclusive content for the highest spenders while teasing other players with Godlike versions
- No public list of Hall of Fame cards was found in research; they appear to be added gradually

---

## 14. Soul Summoner System

A card acquisition system where players can earn cards through the "Soul Summoner":

**What It Is**: A system where players can earn legendary cards (possibly through specific activities, PvE content, or grind-based mechanics)

**Key Restriction**: Soul Summoner cards **CANNOT be Awakened** through the Alchemy Lab
- Players who attempt to Awaken Soul Summoner cards lose their resources (fire ruby, cards, silver) in a failed attempt
- These cards also do not appear in the completion guide, making them "useless for completion rate" purposes
- Fire rubies can be used to enhance Soul Summoner cards to gold-like quality, but this falls short of Awakening

**Developer Response**: When asked about this restriction, developer "Minionsss" stated they had "not received any updates about locked cards becoming eligible for awakening" — strongly implying this is intentional design

**Community Assessment**: Players noted this restriction existed in predecessor games (Kings and Legends / Rise of Mythos) and speculated the lock is intentional monetization — forcing players to purchase card packs to obtain Awakened-eligible versions rather than using the F2P Soul Summoner path

**Time Investment**: Community members estimated earning a Legendary card via Soul Summoner takes approximately 6–8 months of play

---

## 15. Pack Transparency Problem

A documented complaint in Kings Call is the **absence of in-game pack content disclosure**:

**The Issue**:
- Card packs do not display what cards are possible to obtain from them
- Players can spend premium currency (Gold/Rubies) on a pack hoping for a specific card, only to discover the card is not in that pack's possible drops at all
- No drop rates are disclosed for any pack

**The Developer's Solution**:
- On June 11, 2025, developer "Minionsss" acknowledged the complaint and directed players to the official Discord server
- Specifically cited: **a channel called "packs-and-cards"** on the Kings Call Discord (discord.gg/jbsm4tEuSM) where pack contents details are listed

**The Problem With This Solution**:
- Forces players to use an external platform (Discord) to access basic purchase transparency information
- Information is not in-game at point of purchase
- Discord is a separate service with its own access requirements

This is a documented community complaint that was raised again as late as June 2025, indicating the problem had not been resolved with an in-game fix.

---

## 16. Known Balance Issues and Reported Bugs (Community Reports)

**Mirrorcraft Card (Reported Bug/Balance Issue)**:
- Mirrorcraft is a card that copies opponent's creatures
- Community reports: allows unlimited copies of Elite Monsters on the field
- Elite monsters normally have a one-per-field restriction
- Mirrorcraft bypasses this restriction, enabling game-breaking combinations (e.g., multiple copies of Princess Sarya, Garghael)
- Result: Mages who use Mirrorcraft dominate PvP according to community reports
- Status: Developer "Minionsss" asked for details and screenshots; no balance patch confirmed as of research date
- Community expressed frustration that "months" of reporting produced no action

**Ranger Overpowered (Balance Complaint)**:
- Community reports that Ranger skill cards "counter everything" in PvP
- Rangers dominate PvP ranked boards according to player reports
- Historical context: NamuWiki documentation from Rise of Mythos era also identified Ranger as "the best PVP class"
- Appears to be a persistent balance issue across all versions of the game

**Arena Bot Matchmaking**:
- Arena matchmaking range for bots was adjusted to 0–600 points in a 2026 patch
- Previous range apparently created matchmaking issues (players being matched against bots at inappropriate rating levels)

**Reconnection Bug**:
- Players who disconnect mid-battle and reconnect report losing rewards earned before the disconnect
- Developer recommended contacting support with screenshots

**Pet System Fairness**:
- Pets are active during PvP (confirmed)
- Community complained this adds P2W randomness; higher-tier pets from paid content provide combat advantages
- No documented developer response to this specific balance concern

**Overpowered Godlike Pets**:
- Community reports of "godlike pets" creating large power gaps in PvP
- Combined with the Mirrorcraft issue, PvP at high levels reportedly involves multiple compounding P2W advantages

---

## 17. XstarGame Company Information

**X Star Game Limited**:
- Registered Address: Rm 12 20/F HO KING COML BLDG 2-16 FA YUEN ST, Mong Kok, Hong Kong
- Support Email: huoyanzhengcheng@gmail.com
- Secondary Support Email: gs@xstargame.com
- Company Website: xstargame.com
- Twitter: @starlghtgames (note intentional typo: "starlght" not "starlight")

**What XstarGame Publishes**:
- Kings Call (English Steam + H5 + mobile)
- Kings Call H5 (browser version)
- Expedition Call (separate game)
- 火焰征程 / Flame Journey (Chinese Steam version — Steam App 2492430)

**Developer Alias**: "Starlight Games" is used interchangeably with "X Star Game Limited" in Steam announcements

---

## 18. Steam Player Count History

| Month | Average Players | Peak Players | Notes |
|-------|-----------------|--------------|-------|
| Dec 2023 | (launch) | — | Launch month |
| May 2024 | 191 | 345 | |
| Jun 2024 | 206 | 363 | |
| Jul 2024 | 310 | 456 | Large increase |
| Aug 2024 | 359 | 518 | All-time peak |
| Sep 2024 | 326 | 490 | Pet system launch month |
| Oct 2024 | 258 | 399 | |
| Nov 2024 | 341 | 479 | NA5 server opening |
| Dec 2024 | 363 | 502 | New Year event |
| Jan 2025 | 244 | 393 | EU5 opening |
| Feb 2025 | 294 | 498 | |
| Mar 2025 | 156 | 270 | Sharp drop |
| Apr 2025 | 264 | 427 | Recovery |
| May 2025 | 268 | 398 | |
| Jun 2025 | 265 | 407 | |
| Jul 2025 | 269 | 387 | |
| Aug 2025 | 269 | 387 | |
| Sep 2025 | 309 | 425 | |
| Oct 2025 | 284 | 399 | |
| Nov 2025 | 162 | 362 | Dip |
| Dec 2025 | 300 | 417 | Holiday recovery |
| Jan 2026 | 288 | 412 | |
| Feb 2026 | 321 | 470 | |
| Mar 2026 | 282 | 432 | |
| Apr 2026 | 277 | 425 | Current (research date) |

**All-time peak**: 518 players (August 27, 2024)
**Steambase Score**: 64/100 (Mixed rating, 534 total reviews)
**Steam review ratio**: ~64% positive overall; approximately 40% positive in last 30 days as of late 2025

**Interpretation**:
- The game has maintained a stable core player base of 250–380 average players throughout 2024–2026
- Spikes correlate with new server openings and major events
- The March 2025 drop (156 avg) is notable and unexplained from available data
- The game has NOT experienced the typical mobile game "launch spike and crash" pattern; instead showing a longer flat retention curve typical of a loyal niche audience

---

## 19. Gaming Press Coverage

**Massively Overpowered (February 4, 2024)**:
- Article: "MMOs You've Never Heard Of: Sneak Out, ManaSoul, Rise of Mythos aka Kings Call"
- Coverage described the game as Rise of Mythos returned, acknowledged positive gameplay but criticized monetization
- URL: massivelyop.com/2024/02/04/mmos-youve-never-heard-of-sneak-out-manasoul-rise-of-mythos-aka-kings-call/

**Kotaku**:
- Has a game hub page for Kings Call (dated November 21, 2023)
- URL: kotaku.com/games/kings-call
- No full critical review found; page appears to be a game listing/hub rather than a dedicated review

**Metacritic**:
- Kings Call is listed on Metacritic
- No Metascore (insufficient critic reviews)
- User score: Not available (requires 4+ ratings; only 1 user rating as of research)
- URL: metacritic.com/game/kings-call/

**GameFAQs**:
- Rise of Mythos is listed (same game) with a detailed player review
- Review title: "Kings and Legends - Prepare that your life can be ruined by this game"
- Heavy P2W criticism; detailed mechanical breakdown
- URL: gamefaqs.gamespot.com/webonly/691922-rise-of-mythos/reviews/160836

---

## 20. YouTube Content Catalog

**Official/Promotional**:
- "Kings Call Game Trailer" — youtube.com/watch?v=FpXFmvgMC6g
- "kings call Gameplay (Steam F2P)" — youtube.com/watch?v=G7Epocl5zEI

**Community Content (2023 Launch Era)**:
- "Kings Call (Rise of Mythos - EN) - Arena x1, Master's Pack, Halfblood & Dragon | BR 2023 #medieval" — youtube.com/watch?v=TLC_z3oe-VU (Shows: Arena gameplay, pack opening, deck compositions)
- "World Boss - Kings Call (Rise of Mythos - EN) | BR 2023" — youtube.com/watch?v=a_KG1t-ofoE (Shows: World Boss Queen Sharia fight mechanics)
- "Open Packs - Kings Call (Rise of Mythos - EN) | BR 2023" — youtube.com/watch?v=-ezmP8sMcA4 (Shows: Pack opening, card reveal animations)
- "Kings and Legends / Rise of Mythos / Kings Call is back! New Character" — youtube.com/watch?v=P7IOc2KYSDs
- "Kings Call Gameplay (Lanzamiento Oficial) - Android Cartas!" — youtube.com/watch?v=HwXOm5uv7-w (Spanish language gameplay)

**Historical Rise of Mythos Content**:
- ZeeZ Rise of Mythos channel: youtube.com/@zeezriseofmythos592 (dedicated RoM content creator with multiple videos)
- "Rise Of Mythos aka Kings & Legends" playlist: youtube.com/playlist?list=PL88LfPGGtH2P1WRRG_dVsGiQ7ftyhjBYR
- "Rise of Mythos - Soloing World Boss (All Stages)" — youtube.com/watch?v=lH_1frbX218

**What the Videos Show**:
- Arena gameplay videos reveal: 4-lane grid combat visible; creatures deployed from bottom and advancing toward enemy hero; cards displayed with ATK/DEF stats and rarity coloring
- Pack opening videos show: pack selection screen, animated card reveals with rarity effects, Legendary and Godlike cards having distinctive opening effects
- World Boss videos show: multi-player format against a shared enemy; the screen shows multiple players' creatures simultaneously
- The dated visual assets are clearly visible in all footage — identical art from the 2013 Flash game era

---

## Sources for This File

- [XstarGame Official FAQ for Kings Call H5](https://www.xstargame.com/news/index/details/id/73.html)
- [XstarGame Official Site](https://www.xstargame.com/)
- [XstarGame Gift Packs](https://www.xstargame.com/gift)
- [Kings Call App Store (iOS)](https://apps.apple.com/us/app/kings-call/id6753857798)
- [Kings Call Google Play](https://play.google.com/store/apps/details?id=com.xstar.kingscall)
- [Steam — Kings Call](https://store.steampowered.com/app/2674290/kings_call/)
- [Steambase — Kings Call Steam Charts](https://steambase.io/games/kings-call/steam-charts)
- [Steam — Hall of Fame Discussion](https://steamcommunity.com/app/2674290/discussions/0/603031298030780381/)
- [Steam — Mirrorcraft Balance Discussion](https://steamcommunity.com/app/2674290/discussions/0/4407417621393412151/)
- [Steam — Soul Summoner Awakening Discussion](https://steamcommunity.com/app/2674290/discussions/0/594013058474479479/)
- [Steam — Card Pack Transparency Discussion](https://steamcommunity.com/app/2674290/discussions/0/599655112388906378/)
- [Steam — Magic Pet Realm Discussion](https://steamcommunity.com/app/2674290/discussions/0/4693405423940166922/)
- [Steam — Pet System Discussion](https://steamcommunity.com/app/2674290/discussions/0/4756452833137870173)
- [Steam — F2P Discussion](https://steamcommunity.com/app/2674290/discussions/0/5829413623764551764/)
- [Game Update Notifier — NA5 Event Update](https://gameupdatenotifier.com/g/kings-call/v/announcement-of-event-update-for-the-new-server-na5-20241231)
- [Steam News — April Fools Day Event & Dungeon](https://store.steampowered.com/news/app/2674290/view/524212840420082866)
- [GitHub — zhengboon/kingscallh5stuff](https://github.com/zhengboon/kingscallh5stuff)
- [Massively Overpowered — Rise of Mythos aka Kings Call (2024)](https://massivelyop.com/2024/02/04/mmos-youve-never-heard-of-sneak-out-manasoul-rise-of-mythos-aka-kings-call/)
- [Metacritic — Kings Call](https://www.metacritic.com/game/kings-call/)
- [Kings Call Fandom Wiki](https://kings-call.fandom.com/wiki/Kings_Call)
- [Rise of Mythos Fandom Wiki — Challenge Hall](https://rise-of-mythos.fandom.com/wiki/Challenge_Hall)
- [Rise of Mythos Fandom Wiki — World Boss (Queen Sharia)](https://rise-of-mythos.fandom.com/wiki/Queen_Sharia)
- [TapTap — Kings Call](https://www.taptap.io/app/33636339)
