# Cardcha! — Project Handoff

> **Purpose:** external project memory for a future ChatGPT account, Codex session, or human developer. Read this file before editing code.

## 0. Read order
1. `PROJECT_HANDOFF.md` — current source-of-truth and safety rules.
2. `NEXT_SESSION_START_HERE.md` — current candidate-specific test focus.
3. `docs/STORY_GAMEPLAY_BIBLE.md` — approved story/gameplay canon vs TBD ideas.
4. `BUILD.md` — build/test process.
5. `KNOWN_ISSUES.md` — current risks and regressions.
6. `CHANGELOG.md` / `BUILD_HISTORY.md` — version lineage.
7. Only then inspect source.

## 1. Project identity
- Mod: **Cardcha! / Cardcha-Shardbound**
- Author: Ronvotri
- Stardew Valley SMAPI mod
- UniqueID: `Ronvotri.Cardcha`
- Current canonical candidate: **v0.3.0-alpha.25**
- Candidate label: `Cardcha! v0.3.0-alpha.25 GACHA INTERIOR FLASH`
- Canonical/default branch: `main`
- v0.3 development branch: `binder-v0.3-alpha1`

## 2. Source-of-truth status — ALPHA.25 VERIFIED AND PROMOTED TO MAIN
GitHub `src/Cardcha` on `main` is the canonical baseline source for alpha.25.

Verified alpha.25 source anchors:
- **source anchor commit:** `a083e0a0cb1eb94852964a6f732a73fd7f506b04`
- **promotion merge to main:** `ef7b34bbd9aebdd53c2aae3c6ead60606a1c8d33`
- `src/Cardcha/manifest.json`: `0.3.0-alpha.25`
- `src/Cardcha/Cardcha.csproj`: `0.3.0-alpha.25`
- exact `src/Cardcha` Git tree SHA: `89cff25d67700762ed94399a5905bdf1a52e736f`

The exact Git tree above was independently computed from all **69 files** in `Cardcha_v0.3.0-alpha.25_SOURCE_SNAPSHOT.zip` and matches GitHub byte-for-byte.

### Source precedence
Use this order:
1. checked-in GitHub `src/Cardcha` on `main`;
2. this handoff + `NEXT_SESSION_START_HERE.md`;
3. `docs/STORY_GAMEPLAY_BIBLE.md` for approved design canon;
4. packaged alpha.25 source snapshot as archival cross-check;
5. old chats/builds only as historical context.

If continuing on `binder-v0.3-alpha1`, first ensure it is at least at the current `main` baseline. Do not reconstruct the current build from older branch history unless explicitly debugging lineage.

## 3. Current accepted baseline
The user tested alpha.25 in game and accepted it as the **current working/canonical baseline**. This is stronger than a source-only candidate, but it is not a claim that every platform, controller, feature, or long regression matrix has been exhaustively tested.

### alpha.25 contains and preserves
- centralized multi-controller mapping via `ControllerProfileService`;
- controller layout options: Auto / Xbox / Nintendo / PlayStation / Generic;
- mapping options: Auto / Standard / NintendoNative;
- semantic physical actions: South=Confirm, East=Favorite, West=Deselect, North=Exit;
- Binder locked-card action context + double-click/double-confirm equip-toggle, including unequip;
- rounded Gacha result cards with large icon, localized NEW/DUPLICATE state and reveal sparkles;
- EN/VI audit for 80 card names/descriptions and 304 localized per-star rows per language;
- alpha.24 GMCM/Cinderbox fix: `IGenericModConfigMenuApi` is `public`;
- alpha.25 Gacha flash contract: the rarity/white pulse is an inset filter over the panel interior while the outer frame/border remains visually stable.

### Validation anchors
- alpha.25 source sync/tree comparison: **VERIFIED**;
- alpha.25 preparation static validation: **41/41 PASS**;
- user in-game acceptance: **CURRENT WORKING BASELINE**;
- do not describe it as a final public stable release without broader release QA.

## 4. Cinderbox / GMCM compatibility
alpha.23 produced this SMAPI/Cardcha error on Cinderbox:
`Tried to map a mod-provided API to non-public interface 'Cardcha.Integrations.IGenericModConfigMenuApi'; must be a public interface.`

The fix is intentionally simple and must not regress:
- `IGenericModConfigMenuApi` is **public** in alpha.24+.

An unrelated button/remapping issue discussed elsewhere was resolved separately by the user and is **not part of this compatibility fix**. Do not reintroduce unrelated controller changes when working on GMCM/Cinderbox compatibility.

## 5. User-confirmed / protected interaction design
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

Displayed labels may vary by Xbox/Nintendo/PlayStation/Generic layout. This architecture exists specifically to avoid controller-brand-specific fixes.

### Binder UI protected decisions
- near-full-screen readable book;
- rarity bookmarks filter the collection;
- resource rail below rarity bookmarks and above Favorite;
- 5 normal skill slots grouped separately from Mythic and ChaCha slots;
- player-facing term is **Mythic Skill / Kỹ năng Thần Thoại**, not Boss Skill;
- ChaCha slot uses pink story/system identity;
- page arrows are pixel-drawn, not unsupported Unicode glyphs;
- locked card has an explicit visible lock border;
- control hints remain outside the book and follow the active input family.

### Gacha flash contract — alpha.25
During Stationary and Portable Cardcha rituals:
- flash should read as a full/interior panel light filter;
- it may pulse rarity color + white;
- it is inset about 8px from the panel bounds;
- **outer gold frame/border must stay stable** and must not pulse with the filter;
- do not restore the old inner rectangular aura around the machine.

## 6. Core gameplay architecture
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
- results are persisted before animation; skipping must not reroll;
- reveal/result visuals prioritize card identity + NEW/DUPLICATE, not redundant rarity text.

### Machines
- Stationary Cardcha Machine: main FarmHouse only;
- Portable Cardcha Machine: toolbar/use-tool interaction, not placeable;
- approved future progression direction:
  - 20 unique cards: quest + first Boss, Portable Machine reward;
  - 40 unique cards: quest/encounter, ChaCha absorbs/fuses Stationary + Portable machines and Cardcha access moves into Binder/ChaCha.

## 7. MiMi / ChaCha / story source of truth
For all new story implementation, read `docs/STORY_GAMEPLAY_BIBLE.md` first.

Locked direction includes:
- MiMi becomes a giftable friendship NPC with heart progression and mail;
- she gradually reveals a 17:30 favorite-TV / BL-couple-fan secret;
- her behavior can react to the farmer dating/marrying male NPCs;
- later she moves from roaming sales into a Community Center stall;
- on Community Center route, once per season she may contribute one eligible missing requirement rather than completing whole bundles;
- boss milestones are 20 / 40 / 60 / 80 cards;
- MiMi is intended as the 80-card final boss, but not as a simple evil-villain twist;
- Rune Factory-inspired airship travel is the preferred hub/transport solution for dedicated boss maps;
- ChaCha is normally non-verbal and communicates through expressions/body language;
- ChaCha can use Boss/Mythic forms;
- ChaCha support passive scaling is milestone-driven and requires MiMi food quests.

Do not convert **TBD** items into canon without a new explicit decision.

## 8. ChaCha support passive — approved numbers
### Trigger chance after a valid hit on a monster
- 0–19 cards: 2%
- 20–39: 4%
- 40–59: 6%
- 60–79: 8%
- 80: 10%

### Trigger chance when player receives damage
- 0–19: 1%
- 20–39: 2%
- 40–59: 3%
- 60–79: 4%
- 80: 5%

### Heal/Energy tier
Each new 10-card tier requires **9 ChaCha-favorite foods** + turn-in to MiMi:
- 0: 10%
- 10: 11%
- 20: 12%
- 30: 13%
- 40: 14%
- 50: 15%
- 60: 16%
- 70: 17%
- 80: 18%

On a successful HP proc, there is a **30% chance** to restore Energy at the same percentage. Internal cooldown remains TBD.

## 9. Localization rules
English and Vietnamese are the primary/reference languages.
- every player-facing feature added in one should be added consistently in the other;
- avoid mixed English/Vietnamese fragments in Vietnamese UI unless proper names;
- prefer player-readable terminology over literal translation;
- future translations should be based on finalized EN/VI semantic keys, not scattered hard-coded strings.

## 10. MiMi implementation details that must not regress
- pre-reveal identity may appear as `???`;
- after reveal/handoff, the name remains **MiMi**;
- weekday merchant window: Monday–Friday 11:00–17:00;
- clear weather: Town plaza;
- rain/harsh weather: WizardHouse;
- broom arrivals/departures start/end beyond viewport;
- approved `mimi_broom.png` is an official project asset;
- standing MiMi runtime scale around 0.575; broom compensation around 0.6325;
- MiMi/??? NPC Map Locations marker uses a dedicated face crop because world sprites use larger frames.

## 11. DO NOT CHANGE without explicit approval
- do not collapse controller logic back to one hard-coded controller brand;
- do not make normal Binder focus movement overwrite the locked card;
- do not reintroduce unsupported Unicode page arrows;
- do not rename player-facing Mythic Skill back to Boss Skill;
- do not make the Gacha frame itself pulse again when only the interior filter should flash;
- do not make MiMi's final-boss lore a simple “evil all along” twist;
- do not use copyrighted game-specific Hades assets as public mod assets; mythological inspiration is fine, original art is required;
- do not mark 20/40/60/80 progression as implemented when it is still design-only;
- do not overwrite approved user art casually;
- do not claim exhaustive release QA that has not happened.

## 12. Debug/test commands worth preserving
- `cardcha_open_binder`
- `cardcha_give_machine`
- `cardcha_open_machine`
- `cardcha_give_portable_machine`
- `cardcha_open_portable_machine`
- `cardcha_controller_status`
- `cardcha_version`
- Scrap/gacha debug syntax should be verified against current source before treating it as permanent API.

## 13. Migration checklist
Before editing:
- connect repo `ronvotri/Cardcha-Shardbound`;
- checkout `main` for the canonical baseline, or create a fresh development branch from current `main`;
- read the files in section 0;
- treat checked-in `src/Cardcha` as alpha.25 source of truth;
- source anchor: `a083e0a0cb1eb94852964a6f732a73fd7f506b04`;
- promotion merge: `ef7b34bbd9aebdd53c2aae3c6ead60606a1c8d33`;
- exact source tree: `89cff25d67700762ed94399a5905bdf1a52e736f`;
- never assume ChatGPT account memory exists;
- current source + handoff docs beat old chats when they conflict.

## 14. Branch policy
`main` is the canonical baseline branch as of alpha.25. `binder-v0.3-alpha1` is retained as the historical/continuing v0.3 development branch and should be kept at or ahead of the current `main` baseline before new changes are made.

Prefer a new feature/fix branch from `main` for risky changes, then merge back after testing. This keeps the accepted alpha.25 baseline easy to recover.

## 15. Current baseline policy
`v0.3.0-alpha.25` is the **current accepted working baseline**.

Canonical anchors:
- `ALPHA25 SOURCE COMMIT: a083e0a0cb1eb94852964a6f732a73fd7f506b04`
- `ALPHA25 PROMOTION MERGE: ef7b34bbd9aebdd53c2aae3c6ead60606a1c8d33`
- `ALPHA25 SOURCE TREE: 89cff25d67700762ed94399a5905bdf1a52e736f`
- `ALPHA25 SOURCE SNAPSHOT: Cardcha_v0.3.0-alpha.25_SOURCE_SNAPSHOT.zip`
- `ALPHA25 BUILDER: Cardcha_v0.3.0-alpha.25_GachaInteriorFlash_WindowsBuilder_FULL.zip`

Use alpha.25 as the rollback/reference point for the next development step unless the user explicitly chooses a newer baseline.
