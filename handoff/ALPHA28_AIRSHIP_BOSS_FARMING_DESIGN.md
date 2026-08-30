# Cardcha-Shardbound — Alpha.28 Airship + Farming Regions + Boss Progression

Status: design locked enough to preserve; implementation not started yet.
Branch: `cardcha-alpha27-mimi-real-npc`
Baseline to protect: accepted `0.3.0-alpha.27.0.7.9.0` behavior and all non-regression contracts already documented in `handoff/BINDER_CONTROLLER_SELECTION_ACTION_RULES.md` and `handoff/ALPHA27_NEXT_BUILD_PLAN_AFTER_0790.md`.

## Core problem this feature solves

Cardcha must be playable as a self-contained mod even when the player does **not** install Pelipper Town, SVE, Ridgeside, Stardew Druid, or any other mod that adds lots of monsters.

The player therefore needs an official Cardcha-controlled place where they can deliberately farm monsters, earn Scrap, roll the gacha, and progress the 80-card collection.

The airship system becomes the main Cardcha hunting/farming backbone.

## Story timing

### 1. Airship foreshadowing before MiMi appears

Before MiMi's official story introduction, the player can witness a short mini-scene of an unknown airship flying over/near the farm.

Goals:
- establish that Cardcha's world exists before the player meets MiMi;
- make MiMi feel like she was already traveling/working in the valley;
- create a later recognition moment: the player eventually realizes the airship belongs to MiMi / Cardcha's story.

This scene happens before the current MiMi story reveal and must not expose her identity too early.

### 2. First Scrap still starts MiMi's real onboarding

The current first-Cardboard-Scrap trigger remains meaningful.

After the player gets the first Scrap, MiMi's quest/story begins. The early quest should now lead toward **earning access to the airship**, rather than waiting until the player has already collected 20 unique cards.

### 3. Airship is unlocked early

The player receives access to the airship early enough that Region I becomes the primary monster-farming location for the 0–20 unique-card phase.

The airship itself is therefore **not** the 20-card reward.

## Main gameplay loop

The intended loop is:

1. Fly to a Cardcha hunting region.
2. Fight randomly spawned monsters.
3. Earn normal Cardcha monster rewards / Scrap.
4. Return and use Cardcha gacha.
5. Increase unique-card count.
6. Reach the region's Boss Gate requirement.
7. Defeat that region's boss.
8. Unlock the next region / progression reward.
9. Previous regions remain permanently revisitable.

Important: normal monsters should continue feeding the existing Cardcha economy. Do **not** casually change the core economy into direct card drops unless separately designed later.

## Four progression regions

Use code/design terms such as `Tier1..Tier4` or `Region1..Region4`; the player-facing names can be decided later.

### Region I — 0 to 20 unique cards

- Unlocked through the early MiMi/airship onboarding quest.
- Available well before 20 cards.
- Provides enough random monsters that a vanilla-only Cardcha player can realistically farm Scrap and build their first 20 unique cards.
- Boss Gate is visible inside the region but remains sealed until **20 unique cards**.
- Defeating Boss I completes the old approved 20-card progression idea.
- Preferred major reward: **Portable Cardcha Machine**.
- This replaces the old temporary behavior where reaching 20 cards could simply hand out the portable machine without the boss encounter.

### Region II — 21 to 40 progression band

- Unlocked after Boss I / Region I completion.
- New monster pool and visual identity.
- Boss Gate requires **40 unique cards**.
- Player can always return to Region I.

### Region III — 41 to 60 progression band

- Unlocked after Boss II.
- New monster pool and harder encounter profile.
- Boss Gate requires **60 unique cards**.
- Regions I and II remain open.

### Region IV — 61 to 80 progression band

- Unlocked after Boss III.
- Endgame hunting area / strongest ordinary monster pool.
- Final Boss Gate requires **80 unique cards**.
- Designed as the final 80-card progression destination, with room for post-completion farming afterward.

## Boss Gate behavior

Each hunting region should contain a physical/visual Boss Gate or sealed entrance.

The player should be able to discover the gate before meeting the unique-card requirement.

Example UI/message concept:

`Card Resonance: 13 / 20`

or equivalent localized wording.

The gate should clearly communicate progression rather than simply behaving like an invisible wall.

Only the **boss area** is locked by the unique-card threshold. The farming region itself must already be usable.

This is essential: players need the region precisely so they have somewhere to farm **before** reaching 20 / 40 / 60 / 80 cards.

## Monster spawning philosophy

Do not make these regions static maps where every monster is always in the same exact spot.

Preferred system:
- each region contains authored spawn zones / spawn points;
- when entering or refreshing the region, the game selects monsters from that region's pool;
- spawn composition is semi-random;
- support common, stronger/elite, and rare encounters later;
- region identity comes from a controlled pool, not from completely unrestricted global monster spawning.

Goals:
- repeated trips feel less scripted;
- the region works as a real farming destination;
- map layout can stay authored while combat composition changes;
- future balance can modify pools without rebuilding the whole map.

## Airship experience

The airship should have two levels of presentation.

### First unlock / major story flights

Use a real cinematic presentation:
- MiMi introduces or grants access to the ship;
- ChaCha can participate in the scene if story state allows;
- ship takes off from/near the farm;
- visual sky/farm transition;
- first trip feels important.

### Repeat travel

Do not force the full cutscene every time.

Preferred repeat-use flow:
- small airship deck / hub location;
- interact with navigation control / map;
- choose destination;
- short transition into the selected hunting region.

This keeps the Rune Factory 4-style travel feeling without making repeated farming slow.

## Rune Factory 4 inspiration

The intended fantasy is close to a Rune Factory 4-style progression map:
- a transport hub;
- several distinct hunting destinations;
- regions unlock over time;
- each region contains regular combat and a gated boss objective;
- the player repeatedly returns to earlier places when useful.

The implementation does **not** need full continuous real-time world traversal between every destination. A convincing deck/hub + destination transition is preferable to an overly complicated scrolling simulation for the first version.

## Stardew Druid prototype inspiration

The user supplied a copy of Stardew Druid for research/prototyping. Its archive contains many potentially useful monster/boss and environment references, including examples such as:

- monster/boss-style sprites: `Crowmother`, `Jellyking`, `BoneWitch`, `PeatWitch`, `Reaper`, `Dragon`, `Carnivellion`, `PhantomCaptain`, `SeafarerCaptain`, various serpents/fiends/spectres;
- environment sheets: `Grove`, `Clearing`, `Moors`, `Graveyard`, `Cavern`, `Lair`, `Atoll`, `Overlook`, `Skyblue`, `Skynight`, `Ritual`, and others.

Possible prototype biome mapping discussed:
- Region I: Grove / Clearing-style environment;
- Region II: Moors / Graveyard-style environment;
- Region III: Cavern / Lair-style environment;
- Region IV: Atoll / Overlook / Skynight-style sky/endgame environment.

These are **prototype/moodboard references, not final Cardcha canon names or guaranteed shipping assets**.

### Permission rule

Before public release, do not ship another mod author's original sprites, tilesheets, audio, or other assets unless their license/permissions clearly allow it or explicit permission is obtained.

Using the supplied Stardew Druid assets for private prototype/layout research is separate from deciding what can be redistributed publicly.

## Connection to previously approved Cardcha progression

This design preserves the older progression concepts already recorded in previous handoffs:

### 20-card milestone

Old design:
- 20 unique cards -> ChaCha information -> quest -> Boss -> Portable reward.

New airship design integrates that directly:
- Region I is available before 20;
- 20 unique cards opens Boss I;
- Boss I completes the milestone and grants the Portable Machine reward.

### 40-card milestone

Previously approved future concept:
- 40 unique cards -> quest/encounter -> ChaCha fuses stationary + portable machines -> Cardcha access directly from Binder.

Do not discard this. Its exact placement relative to Boss II should be designed during Region II implementation. One strong option is to make Boss II / the 40-card story the trigger for that fusion milestone.

## Boss slot / Binder connection

The existing Binder already visually reserves a Boss-oriented slot/system. Future boss rewards or Boss Card behavior should connect to this instead of inventing an unrelated parallel UI.

Do not change the accepted Binder controller selection/action behavior while implementing boss progression.

## Proposed Alpha.28 implementation order

Do **not** build all four regions in one pass.

### Alpha.28 Feature 1 — vertical slice

Build only the complete first loop:

1. Pre-MiMi airship flyby mini-scene.
2. First Scrap still triggers MiMi onboarding.
3. MiMi quest grants early airship access.
4. Airship hub/deck or equivalent repeat-travel interaction.
5. Region I hunting map.
6. Region I controlled random monster spawning.
7. Region I Boss Gate visible from early progression.
8. Boss Gate checks 20 unique cards and remains locked below the threshold.
9. Return flow back to farm/airship.
10. Existing Scrap -> gacha -> unique-card progression must work naturally with this region.

Boss I itself may be implemented in the next build if needed, but the vertical slice should prove the core loop:

`fly -> farm monsters -> return -> gacha -> increase collection -> approach Boss Gate`

### Alpha.28 Feature 2 — Boss I

- Boss I arena and encounter.
- 20-card gate opens correctly.
- Boss victory state persists.
- Portable Cardcha Machine becomes the intended reward.
- Region II unlock hook is created.

### Later Alpha.28 / Alpha.29 content

- Region II + Boss II / 40-card milestone.
- Region III + Boss III / 60-card milestone.
- Region IV + final 80-card boss progression.

## Non-regression rules while building this feature

Preserve all currently accepted 0.7.9.0 behavior unless explicitly changed later:

- MiMi approved walk/broom/social assets;
- MiMi attic current accepted layout;
- mystery `???` phase has no random idle ChaCha emotes;
- Binder `PreviewCard` / `LockedCard` coexistence;
- Favorite/Equip synthetic-click suppression;
- stationary Cardcha Machine placeable indoors;
- Portable Machine non-placeable;
- `main` remains rollback baseline; continue feature work on the active development branch until explicitly promoted.

## Design intent summary

The airship is not just decoration and not just a late-game unlock.

It becomes Cardcha's self-contained monster-hunting infrastructure:

**Airship -> Hunting Region -> Random Monsters -> Scrap -> Gacha -> Unique Cards -> Boss Gate -> Boss -> Next Region.**

Four major regions cover the full 80-card journey:

**Region I: 0–20**
**Region II: 21–40**
**Region III: 41–60**
**Region IV: 61–80**

The region remains available before its boss threshold so even a player with no other monster-expansion mods always has a viable place to farm Cardcha progression.
