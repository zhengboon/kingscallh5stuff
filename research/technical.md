# Technical: Kings and Legends / Rise of Mythos / King's Call

## Platform Evolution Overview

| Era                     | Platform          | Technology                    | Notes                                              |
|-------------------------|------------------|-------------------------------|----------------------------------------------------|
| 2012–2013 (K&L launch)  | Browser           | Adobe Flash                   | Flash-based browser game; no download required     |
| 2013–2019 (Rise of Mythos) | Browser + Mobile | Adobe Flash (browser); Native Android (mobile) | Multiple platforms: Kongregate, Armor Games, Facebook, GameFuse.com |
| 2016 (RoM Mobile)       | Android           | Native APK                    | Google Play packages: com.gamefuse.riseofmythos.google, com.huoys.wzzh.us |
| 2020 (王者神域 / KING GOD DOMAIN) | Steam + Browser | Unknown (browser-based wrapper) | Steam App 1383670; released Sept 1, 2020         |
| 2023 (火焰征程 / Flame Journey) | Steam         | Unknown (likely Cocos/HTML5 wrapped for Steam) | Steam App 2492430; Chinese only |
| 2023–present (Kings Call) | Steam + Mobile + Browser | Cocos Creator 3.8.7 (H5) + Firebase + Wancms SDK | Steam App 2674290; Google Play com.xstar.kingscall |

---

## Kings Call (Current) — Technical Stack

This is the most well-documented version thanks to the GitHub repository **zhengboon/kingscallh5stuff** which performed full APK decompilation and analysis.

### Game Engine
- **Cocos Creator 3.8.7**
- Cocos Creator is a Chinese-developed, cross-platform game engine (free/open-source) for 2D and 3D games
- Supports HTML5/browser deployment as well as Android, iOS, Windows, Mac, and Linux builds
- The game is fundamentally an **H5 (HTML5)** game wrapped in an Electron-like shell for Steam delivery

### Authentication & Backend
- **Firebase Authentication** — user login and account management
- **Firebase Realtime Database** — game state synchronization
- **Wancms SDK** — integrated into the game; used for (presumably) analytics, monetization, or platform management. Specific Wancms SDK function in Kings Call not fully documented.

### CDN / Asset Delivery
- **CDN host**: `cdn.xstargame.com` — hot-update CDN for pushing game content updates without a full client download
- This is a common pattern in Cocos Creator games; assets (cards, images, data tables) are downloaded from CDN on first access rather than bundled in the initial APK/install

### Package IDs
- Android package (Google Play): `com.xstar.kingscall`
- Game version analyzed in GitHub repo: **v1.1.7.0**

### Kings Call H5 (Browser Version)
- The "H5" designation refers specifically to the HTML5 browser-playable version hosted at xstargame.com
- Kings Call H5 is also the version available on TapTap
- **IMPORTANT**: Per official XstarGame FAQ (xstargame.com/news/index/details/id/73.html): **H5 and Steam versions run on SEPARATE servers with separate data — no shared accounts or progress**
- H5 version has "selected and rebalanced cards" with "some high-impact designs removed" for a "fresh meta with more balanced, stable, and strategic gameplay"
- Steam is focused on "hardcore content"; H5 focused on "social features, cross-platform access, and quick play sessions"
- Device requirements for H5: PC: Chrome 90+, 4GB RAM; Mobile: Android 10+, iOS 14+; Network: minimum 10 Mbps
- Guest login supported on H5 (with warning to link email to avoid data loss on cache clear)
- A standalone mobile app was described as "already in the works" (as of FAQ publication)

---

## Rise of Mythos — Technical Details

### Browser Version (2013–2019)
- **Adobe Flash** — the original browser game ran exclusively on Flash Player
- Flash end-of-life (EOL) was December 31, 2020 (Adobe stopped distributing Flash Player; browsers blocked Flash)
- Rise of Mythos was shut down August 30, 2019 — approximately 16 months **before** Flash EOL
- The shutdown was thus a business decision (publisher/developer partnership termination), not a technical constraint
- Available on: Kongregate, Armor Games, Facebook (via fbpartneronline.gamefuse.com), GameFuse.com portal, 101XP portal

### Mobile Version (2013–2016)
- Android APK: Package `com.gamefuse.riseofmythos.google` (Google Play, updated August 17, 2015)
- Android APK (US version): Package `com.huoys.wzzh.us` (released January 7, 2016)
- Developer: Changyou.com (US) LLC
- Minimum Android: 2.3.4+
- Version noted in archives: 1.1.0 (APKFab), 1.0.5 (updated 2023 in some archive)
- Rise of Mythos Mobile Facebook page: https://www.facebook.com/riseofmythosmobile/
- The mobile version described as "Rise of Mythos, the #1 hit strategy/RPG browser game, now mobile" — marketed as a companion to the browser game

### Facebook Integration
- Rise of Mythos had a dedicated Facebook app version (fbpartneronline.gamefuse.com)
- Multiple named servers existed on the Facebook platform ("Ayer's Square" documented in a preserved URL)
- The Facebook version and Kongregate/Armor Games versions operated as **separate server instances** — players on different platforms could not interact

---

## Kings and Legends — Technical Details

### Browser Version (2012–2021)
- Also Adobe Flash for the Western/European version (GameSpree/gamigo)
- Domain: kingsandlegends.com
- Website appears to still be online at kingsandlegends.com as of research (April 2026) but the game itself shut down February 9, 2021
- The "isitdownrightnow" service tracked kingsandlegends.com uptime, suggesting it was monitored by community

### Mobile Version
- Kings and Legends was announced for iOS mobile in May 2014 (European iOS App Stores)
- Android release described as "coming soon" at that time
- APK available: Package `com.huoys.wzzh.ger` (German/EU version) on APKPure
- SEA version: Operated via ftcgames.asia / kalftcgames.asia (browser-based, flash)

---

## Kings Call H5 — Data Analysis (from GitHub: zhengboon/kingscallh5stuff)

The **zhengboon/kingscallh5stuff** repository is a Python-based automation and analysis framework for Kings Call H5. The developer performed APK decompilation and decoded 215 game data tables. Key findings:

### APK Data Tables
| Category                | Count     | File Size |
|-------------------------|-----------|-----------|
| Playable cards          | 7,785     | 4.9 MB    |
| Creature combat stats   | 6,700     | 2.9 MB    |
| Skills/abilities        | 552       | 501 KB    |
| Status effects          | 372       | 169 KB    |
| Compound effects        | 2,649     | 1.4 MB    |
| Gacha pools             | 20+       | —         |
| Guild skills            | 200+      | —         |

### Damage Type Distribution (7,785 total creatures)
| Damage Type | Count  | Percentage |
|-------------|--------|------------|
| Physical    | 3,873  | 57.8%      |
| Fire        | 709    | 10.6%      |
| Arcane      | 507    | 7.6%       |
| Holy        | 482    | 7.2%       |
| Frost       | 433    | 6.5%       |
| Lightning   | 421    | 6.3%       |
| Shadow      | 275    | 4.1%       |

### Game Mechanics in Code
- **6-tier card evolution system** (Common → Good → Rare → Epic → Legendary → Godlike + Awakened above)
- **33+ AOE geometry patterns** (various area-of-effect shapes for spells/abilities)
- **5 dragon wing variants** and **5 dragon scale variants** (sub-typing for Dragon cards)
- **Pet companion system** with growth curves
- Race/faction synergy systems
- Guild economy systems

### Automation Framework (GitHub Repo Purpose)
The repository is a research/automation framework with:
- **Multi-instance launcher**: Support for 1–12 simultaneous game windows
- **Autologin**: Via Chrome extensions or keyboard macro fallback
- **Screen capture**: MSS library at ~4 FPS
- **Computer vision**: OpenCV pipeline for card/board state recognition
- **RL (Reinforcement Learning) agent**: Gymnasium framework; Q-learning agent training
- **APK data browser**: UI to browse all 215 decoded game tables
- **Session recording**: Live capture for analysis

### Repository Stats
- 9 total commits
- 100% Python codebase
- Designed for Windows environments
- Requirements: Python 3.9+

---

## Steam Client Technical Details

### Kings Call Steam (App 2674290)
- **Windows minimum specs**: 64-bit Windows 10, Intel Core i3-3210, 4GB RAM, 2GB storage
- **macOS minimum**: macOS 10.12+, dual-core processor, 2GB storage
- **Linux**: Supported (as listed on Steambase)
- **Steam Deck**: "Playable" with some limitations
- The Steam version is HTML5 packaged likely via Electron or similar framework, given:
  - The game is confirmed H5/Cocos Creator based
  - The CDN hot-update system (cdn.xstargame.com) works with web-based asset delivery
  - System requirements are low relative to a native 3D game

### Why Kings Call Says "Flash Game" in Community
Despite being rebuilt in Cocos Creator, community members ask "is this a flash game?" because:
1. The visual assets and art style are identical to the 2013 Flash version
2. No visual or UX upgrades were made — the "dated graphics" are the exact same assets from ~2010s
3. The gameplay feel and interface are unchanged
4. Community confirmed: "it was a flash game original name rise of mythos" — visually indistinguishable from the Flash original

---

## Platform Availability Summary (Kings Call, 2024–2026)

| Platform        | Store ID / URL                    | Notes                                         |
|-----------------|----------------------------------|-----------------------------------------------|
| Steam (Windows/Mac/Linux) | App 2674290             | Free; Mixed reviews; Steam Deck Playable       |
| Google Play (Android) | com.xstar.kingscall          | Free; active as of Feb 2026                   |
| Apple App Store (iOS) | Not confirmed in research      | Google Play listing exists; iOS unclear        |
| TapTap          | App 33636339                      | Browser/App version; small rating base (3 ratings) |
| Browser (direct) | xstargame.com                   | H5 browser version; same codebase as mobile   |

---

## Sources

- [GitHub — zhengboon/kingscallh5stuff](https://github.com/zhengboon/kingscallh5stuff)
- [Steambase — Kings Call](https://steambase.io/games/kings-call/info)
- [Steam — Kings Call Store Page](https://store.steampowered.com/app/2674290/kings_call/)
- [Steam — 火焰征程](https://store.steampowered.com/app/2492430)
- [Steam — KING GOD DOMAIN](https://store.steampowered.com/app/1383670)
- [Google Play — Kings Call](https://play.google.com/store/apps/details?id=com.xstar.kingscall)
- [TapTap — Kings Call](https://www.taptap.io/app/33636339)
- [XstarGame Official Site](https://www.xstargame.com/)
- [Steam Discussion — This is a flash game?](https://steamcommunity.com/app/2674290/discussions/0/4303823318972554044/)
- [APKPure — Rise of Mythos APK](https://apkpure.com/rise-of-mythos/com.gamefuse.riseofmythos.google)
- [APKCombo — Rise of Mythos](https://apkcombo.com/rise-of-mythos/com.huoys.wzzh.us/)
- [APKPure — Kings and Legends APK](https://apkpure.com/kings-and-legends/com.huoys.wzzh.ger)
- [Cocos Creator Documentation](https://docs.cocos.com/creator/3.8/manual/en/)
- [Armor Games — Rise of Mythos](https://armorgames.com/rise-of-mythos-game/15647)
