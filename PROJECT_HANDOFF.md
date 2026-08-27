# Cardcha! — Project Handoff

> **Purpose:** external project memory for a future ChatGPT account, Codex session, or human developer. Read this file before editing code.

## 0. Read order
1. `PROJECT_HANDOFF.md` — current source-of-truth and safety rules.
2. `NEXT_SESSION_START_HERE.md` — latest candidate-specific test focus.
3. `docs/STORY_GAMEPLAY_BIBLE.md` — approved story/gameplay canon vs TBD ideas.
4. `BUILD.md` — Windows build/test process.
5. `KNOWN_ISSUES.md` — current risks and regressions.
6. `CHANGELOG.md` / `BUILD_HISTORY.md` — version lineage.
7. Only then inspect source.

## 1. Project identity
- Mod: **Cardcha! / Cardcha-Shardbound**
- Author: Ronvotri
- Stardew Valley SMAPI mod
- UniqueID: `Ronvotri.Cardcha`
- Current documented candidate: **v0.3.0-alpha.23**
- Candidate label: `Cardcha! v0.3.0-alpha.23 MULTI-CONTROLLER + GACHA POLISH`
- Main active development branch for this work: `binder-v0.3-alpha1`

## 2. Source-of-truth status — SYNC COMPLETE
The GitHub branch is now the canonical source for alpha.23.

Source synchronization was completed on 2026-08-27:
- **Source sync commit:** `69a0f5d8cccddb2200e2a8748904dabf754275ad`
- Commit message: `sync: alpha23 source snapshot`
- `src/Cardcha/manifest.json`: `0.3.0-alpha.23`
- `src/Cardcha/Cardcha.csproj`: `0.3.0-alpha.23`
- Exact `src/Cardcha` Git tree SHA: `389fec3708f19e759ae6ab7aab33f98c5455e197`

The Git tree SHA above was independently computed from all **69 files** in `Cardcha_v0.3.0-alpha.23_SOURCE_SNAPSHOT.zip` and matches GitHub exactly. This verifies the checked-in `src/Cardcha` tree is byte-for-byte identical to the alpha.23 source snapshot.

### Current source precedence
Use this order:
1. checked-in GitHub `src/Cardcha` on `binder-v0.3-alpha1`;
2. current handoff/docs;
3. packaged alpha.23 source snapshot only as an archival cross-check;
4. old chat/exported history only as secondary historical context.

Do not reconstruct alpha.23 from older branches or historical source unless explicitly debugging lineage.

## 3. Latest candidate status
### alpha.23 contains
- centralized multi-controller mapping via `ControllerProfileService`;
- controller layout options: Auto / Xbox / Nintendo / PlayStation / Generic;
- runtime mapping options: Auto / Standard / NintendoNative;
- semantic physical actions: South=Confirm, East=Favorite, West=Deselect, North=Exit;
- Binder double-click / double-confirm equip-toggle, including unequip of an equipped card;
- rounded Gacha result cards;
- large result icons;
- result cards show localized Name + NEW/DUPLICATE only, no rarity line;
- sparkle burst during reveal;
- full large-panel resonance flash with the old inner rectangular aura removed;
- EN/VI audit for 80 card names/descriptions and 304 localized star-rule rows per language.

### Validation status
- source sync to GitHub: **VERIFIED**;
- targeted static validation: **53/53 PASS** in the build-preparation environment;
- **real Windows compile is still required** because that environment had no `dotnet` executable and no Stardew/SMAPI assemblies;
- alpha.23 must be built with `BUILD_ALPHA23_TEST.bat` and then tested in-game.

Do not call alpha.23 “stable” or “compile-passed” until the Windows build succeeds and user testing confirms it.

## 4. User-confirmed / protected interaction design
### Binder selection model
- free focus movement previews cards;
- explicit selection creates a persistent locked-card action context;
- normal grid movement must not retarget that locked card;
- Favorite / Equip / Upgrade act on the locked card;
- only explicit Deselect releases it;
- double activation on a card is the quick equip/unequip gesture.

### Controller semantic contract
Never implement gameplay behavior directly from raw printed A/B/X/Y labels.
Use physical/semantic positions:
- **South** = Select / Confirm;
- **East** = Favorite;
- **West** = Deselect;
- **North** = Exit to gameplay.

Displayed labels may vary by Xbox/Nintendo/PlayStation/Generic layout.
This architecture exists specifically to avoid controller-brand-specific fixes.

### Binder UI protected decisions
- near-full-screen readable book;
- rarity bookmarks filter the collection;
- resource rail below rarity bookmarks and above Favorite;
- 5 normal skill slots grouped separately from Mythic/Boss and ChaCha slots;
- player-facing term is **Mythic Skill / Kỹ năng Thần Thoại**, not Boss Skill;
- ChaCha slot uses pink story/system identity;
- footer page arrows are pixel-drawn, not unsupported Unicode glyphs;
- locked card has an explicit visible lock border;
- bottom control-hint bar is outside the book and follows the active input family.

## 5. Core gameplay architecture
### Collection
- base collection: **80 cards**;
- Base IDs: 1–80;
- rarity target counts: 27 Common / 23 Rare / 16 Epic / 10 Legendary / 4 Mythic;
- duplicate copies feed card upgrades before Max Star;
- post-Max duplicate sink is planned as Suspicious Dust / future Boss-system progression.

### Gacha
- Standard and Premium pull systems exist;
- pity/pull index must remain functional;
- reload should not deterministically force the exact same card forever;
- reveal/result visuals should prioritize card identity and NEW/DUPLICATE state, not redundant rarity text.

### Machines
- Stationary Cardcha Machine: main FarmHouse only;
- Portable Cardcha Machine: toolbar/use-tool interaction, not placeable;
- approved future progression replaces the temporary direct-access bridge:
  - 20 unique cards: quest + first Boss, Portable Machine reward;
  - 40 unique cards: quest/encounter, ChaCha absorbs/fuses Stationary + Portable machines and Cardcha access moves into Binder/ChaCha.

## 6. MiMi / ChaCha / story source of truth
For all new story implementation, read `docs/STORY_GAMEPLAY_BIBLE.md` first.

Important locked direction includes:
- MiMi becomes a real giftable friendship NPC with heart progression and mail;
- MiMi gradually reveals a 17:30 favorite-TV / BL-couple-fan secret;
- her behavior reacts to the farmer dating/marrying male NPCs;
- later she moves from roaming sales into a Community Center stall;
- on Community Center route, once per season she may contribute one eligible missing requirement rather than completing whole bundles for the player;
- boss milestones are 20 / 40 / 60 / 80 cards;
- MiMi is intended as the 80-card final boss, but not as a simple evil-villain twist;
- Rune Factory-inspired airship travel is the preferred hub/transport solution for dedicated boss mini-maps;
- ChaCha is non-verbal and communicates through expressions/body language;
- ChaCha can use Boss/Mythic forms;
- ChaCha support passive scaling is milestone-driven and requires MiMi food quests.

Do not convert items marked **TBD** in the Story/Gameplay Bible into canon without a new explicit decision.

## 7. ChaCha support passive — approved numbers
### Trigger chance after a valid hit on a monster
- 0–19 cards: 2%
- 20–39: 4%
- 40–59: 6%
- 60–79: 8%
- 80: 10%

### Trigger chance when the player receives damage
Exactly half of the offensive rate:
- 0–19: 1%
- 20–39: 2%
- 40–59: 3%
- 60–79: 4%
- 80: 5%

### Heal strength tier
Unlocked every 10 discovered cards, but the new tier only activates after delivering **9 ChaCha-favorite foods** and turning the quest in to MiMi:
- 0 cards: 10% HP / 10% Energy
- 10: 11% / 11%
- 20: 12% / 12%
- 30: 13% / 13%
- 40: 14% / 14%
- 50: 15% / 15%
- 60: 16% / 16%
- 70: 17% / 17%
- 80: 18% / 18%

When the passive successfully heals HP, there is a **30% chance** to also restore Energy at the same tier percentage.

Internal cooldown details are still TBD unless later locked in the Story/Gameplay Bible.

## 8. Localization rules
English and Vietnamese are the two primary/reference languages.

Rules:
- every player-facing feature added in one must be added consistently in the other;
- avoid mixed English/Vietnamese fragments in Vietnamese UI unless they are proper names;
- prefer player-readable terminology over literal machine translation;
- example: damage variance should be explained as random damage fluctuation / `độ dao động ngẫu nhiên của sát thương`;
- future translations should be derived from the finalized EN/VI semantic keys, not from scattered hard-coded strings.

## 9. MiMi established implementation details that must not regress
- pre-reveal identity can appear as `???`;
- after handoff/reveal, the name must stay **MiMi**;
- weekday merchant window: Monday–Friday 11:00–17:00;
- clear weather merchant location: Town plaza;
- harsh weather/rain: WizardHouse;
- official broom arrivals/departures should start/end beyond the viewport;
- approved user-supplied `mimi_broom.png` is an official project asset;
- standing MiMi scale around 0.575; broom runtime compensation around 0.6325;
- MiMi/??? NPC Map Locations marker requires a dedicated full-face crop because the world sprite uses larger frames.

## 10. DO NOT CHANGE without explicit approval
- do not collapse the controller system back to one hard-coded controller brand;
- do not make ordinary focus movement overwrite the locked Binder card;
- do not reintroduce unsupported Unicode page arrows that render as hearts/stars;
- do not rename player-facing Mythic Skill back to Boss Skill;
- do not make MiMi final-boss lore “MiMi was simply evil all along” unless explicitly redesigned;
- do not use copyrighted game-specific Hades sprites/assets as public mod assets; mythological inspiration is fine, original art is required;
- do not mark design-only 20/40/60/80 progression as implemented unless code actually exists;
- do not overwrite approved user art assets casually;
- do not claim a build passed unless it actually compiled against Stardew/SMAPI references.

## 11. Debug / test commands worth preserving
Known useful commands include:
- `cardcha_open_binder`
- `cardcha_give_machine`
- `cardcha_open_machine`
- `cardcha_give_portable_machine`
- `cardcha_open_portable_machine`
- `cardcha_controller_status`
- Scrap/gacha debug commands should be verified against the current source before documenting exact syntax as permanent API.

## 12. Migration checklist for a new ChatGPT account
Before editing:
- connect the same GitHub repository;
- checkout branch `binder-v0.3-alpha1`;
- read this handoff and the files listed in section 0;
- treat checked-in `src/Cardcha` as the alpha.23 source of truth;
- verify the source-sync anchor if needed: commit `69a0f5d8cccddb2200e2a8748904dabf754275ad`, tree `389fec3708f19e759ae6ab7aab33f98c5455e197`;
- never assume account memory exists;
- treat GitHub documentation as project memory;
- if old ChatGPT history is available via exported conversations, use it only as secondary historical context — current source + handoff docs win when they conflict.

## 13. Immediate next actions
1. Windows-compile alpha.23 with `BUILD_ALPHA23_TEST.bat`.
2. In-game test controller profiles/overrides, Binder double unequip, Gacha rounded/sparkle/full-panel visuals, and EN/VI localization.
3. Fix any alpha.23 regression found by the user.
4. After compile + in-game confirmation, record the exact last-known-good commit/build artifact and tested Stardew/SMAPI versions.

## 14. Last-known-good commit policy
There is currently **no fully established alpha.23 last-known-good commit** because alpha.23 has not yet received a verified Windows compile + full user test.

The source itself **is synchronized and verified** at:
- `ALPHA23 SOURCE SYNC COMMIT: 69a0f5d8cccddb2200e2a8748904dabf754275ad`
- `ALPHA23 SOURCE TREE: 389fec3708f19e759ae6ab7aab33f98c5455e197`

Do not confuse “source synchronized” with “build tested”.

Once a candidate is compiled and user-confirmed, record here:
- `LAST KNOWN GOOD VERSION:`
- `LAST KNOWN GOOD COMMIT:`
- `LAST KNOWN GOOD BUILD ARTIFACT:`
- `TESTED WITH:` Stardew / SMAPI versions.
