# Cardcha: Shardbound Chat Handoff — 2026-09-02

This file is the canonical handoff for continuing work in a new ChatGPT session.

## Current active branch

`cardcha-alpha28-062-chacha-support-cast-runtime`

Current materialized head at end of this session:

`69b1a50a190075ed73d4399ab8d0b1846e966daa`

Materialization commit:

`chore: materialize alpha28.0.4.14.4.4 ChaCha Support Cast runtime [skip ci]`

## Current build

Version:

`0.3.0-alpha.28.0.4.14.4.4`

Test package created and CI-passed:

`Cardcha_v0.3.0-alpha.28.0.4.14.4.4_ChaChaSupportCastRuntime_TEST.zip`

CI workflow:

`Cardcha alpha28.0.4.14.4.4 ChaCha Support Cast Runtime`

Run ID:

`33642147718`

Artifact ID:

`9851270331`

Artifact digest:

`sha256:5a95fae3926dfa073ad471203d1450e54b5b2d8fd62b8442268670e99ab61d1b`

The local extracted test ZIP generated from the artifact had SHA-256:

`5ec76206722e70c3e49b2a65289b827a781f700a83b9de4f968b887de402c46d`

## Regression state

- Card runtime static audit: 76/76 PASS.
- Save schema remains 19.
- Boss Form duration remains 10 seconds.
- Boss Form activation remains controller Confirm + Deselect, keyboard Left Shift + A, or READY energy-bar click.
- Forest collision/map edits remain NONE.
- Airship/Cardcha/MiMi locked art remained unchanged by the ChaCha Support runtime work.

## ChaCha Support Cast canon now implemented

ChaCha has one normal-form Support Cast. The four Region skills are modules on the same cast, not four separate active skills or four cooldowns.

### Trigger A — Kill Cast

After the player kills a monster, if the shared cooldown is ready, roll:

- Lv1: 6%
- Lv2: 9%
- Lv3: 12%
- Lv4: 15%
- Lv5: 18%

Successful roll performs one Support Cast and resets the shared cooldown.

### Trigger B — Lucky Cast on incoming damage

Every time the local player receives damage, roll:

- Lv1: 4%
- Lv2: 5%
- Lv3: 6%
- Lv4: 7%
- Lv5: 8%

Successful Lucky Cast always fires immediately regardless of current HP and ignores cooldown readiness.

### Trigger C — Emergency Cast

If one hit changes the player from HP above 30% to HP at or below 30%, ChaCha performs one guaranteed Support Cast.

Emergency Cast ignores cooldown readiness.

If the player was already at or below 30% before the hit, that hit does not qualify for a new Emergency trigger. The player must first recover above 30% and cross down again on a later hit.

Lucky + Emergency on the same hit must produce at most one Support Cast.

### Shared cooldown

- Lv1: 40s
- Lv2: 35s
- Lv3: 30s
- Lv4: 25s
- Lv5: 20s

Any successful Support Cast resets the cooldown to the current Vital Blessing level's full duration.

Support Cast is normal-form behavior and is suspended while ChaCha Boss Form is active.

## Support Cast module effects

### Region I — Vital Blessing / Phúc Lành Sinh Khí

Heal percentage of Max HP:

- Lv1: 10%
- Lv2: 13%
- Lv3: 16%
- Lv4: 20%
- Lv5: 25%

This is the core Support Cast module.

### Region II — Bunny Aegis / Hộ Mệnh Thỏ Tiên

Once learned, every Support Cast also applies a 20-second protection window.

Incoming-damage reduction by skill level:

- Lv1: 20%
- Lv2: 25%
- Lv3: 30%
- Lv4: 35%
- Lv5: 40%

### Region III — Spirit Aid / Tinh Linh Tiếp Sức

Once learned, every Support Cast performs one 30% module roll.

If it succeeds, restore Max Stamina percentage:

- Lv1: 10%
- Lv2: 15%
- Lv3: 20%
- Lv4: 25%
- Lv5: 30%

### Region IV — Lucky Echo / Phúc Vận Thỏ Tiên

Once learned, every Support Cast performs one 50% module roll.

If it succeeds, apply +1 Luck for 10 seconds.

## Support Cast UI/runtime changes

- One Support Cast cooldown HUD, not four skill cooldowns.
- ChaCha Resonance Abilities view no longer treats the four Region skills as mutually exclusive active selections.
- Learned Region skills are modules that automatically augment the same Support Cast.
- No new player combat button was added.
- Runtime is hooked into both incoming-damage and monster-death pipelines.
- Debug commands include support status/forced-cast helpers for testing.

## Existing ChaCha material/Airship station system preserved

Four physical region materials:

1. `Ronvotri.Cardcha_VitalDewdrop` — Giọt Sương Sinh Khí / Vital Dewdrop
2. `Ronvotri.Cardcha_MoonshieldShard` — Mảnh Khiên Ánh Trăng / Moonshield Shard
3. `Ronvotri.Cardcha_BreezeFeather` — Lông Vũ Gió Nhẹ / Breeze Feather
4. `Ronvotri.Cardcha_FortuneCoin` — Đồng Xu Phúc Tinh / Fortune Coin

Airship upgrade station:

`Bệ Cộng Hưởng ChaCha / ChaCha Resonance Pedestal`

Station tile on Airship Bridge:

`(19,5)`

Current alpha upgrade costs remain:

- Lv1→2: 3 matching material + 5 Magic Dust
- Lv2→3: 5 + 10
- Lv3→4: 8 + 15
- Lv4→5: 12 + 25

These costs were previously marked provisional but are still the implemented values in the current build.

## Airship / Sky Dock state recalled during this session

Current Airship foundation flow:

`Forest Arcane Gate → Cardcha_SkyDockInterior → Airship Bridge → Region route`

### Forest exterior Arcane Gate

Current implementation is presentation-only overlay and preserves `CollisionEdits=NONE`.

Visual ingredients in code:

- dark portal frame
- violet/cyan portal core
- rotating sigils
- gold rune
- two crystal pylons
- sparkles
- ground sigil

Normal Forest entry remains action-driven for compatibility.

### Sky Dock Interior

This exists specifically to avoid the old awkward visual where a tiny airship appeared unrealistically inside/below the room.

Current concept:

- arrival magic seal
- mana lanes
- route console
- boarding bay
- transfer from boarding bay to the actual Airship Bridge

### Airship exterior

Official runtime sprite remains:

`src/Cardcha/assets/airship_visual.png`

Locked SHA-256:

`1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`

The external ship visual is used for:

- Farm flyby
- departure animation
- return animation

Propeller direction previously clarified by the user:

- do not leave fake static propellers in the image and then add extra spinning propellers on top;
- the runtime visual should read as one ship with the intended moving propeller elements, not duplicate rotor geometry.

Current runtime has separately animated left/right rotor motion.

### Airship Bridge interior

The current implementation intentionally reads as being inside a flying ship, not as a room containing a miniature ship model.

Existing bridge visual elements:

- huge panoramic forward window
- moving daytime clouds / nighttime starfield
- central navigation dais
- rotating violet/cyan route rings
- floating crystal core
- side consoles
- mana lane from entrance toward helm
- four infrastructure sockets
- ChaCha Resonance Pedestal

## Visual direction agreed at end of this session

User approved returning to Airship visual polish before moving deeper into Region II/Boss content.

Three visual targets were discussed:

### A. Forest Arcane Gate polish

Goal: make the portal feel deep and spatial rather than a flat luminous rectangle.

Desired direction:

- stronger portal depth/parallax feel
- elegant dark stone/brass frame
- violet/cyan crystal technology
- gold rune language matching Cardcha
- clear walk-up readability
- no Forest collision/tile edits

A concept image was generated in-session showing a large magical forest gate with crystal pylons and a deep portal opening toward the airship realm. This image was conceptual reference only and was NOT committed to the repository or implemented as game art yet.

### B. Sky Dock / Boarding Bay polish

Goal: make the intermediate dock feel physically connected to boarding an actual airship.

Desired direction:

- stronger exterior-sky/airflow cues
- visible relationship between Boarding Bay and the ship
- avoid any tiny decorative airship model
- make the transition read as boarding, not arbitrary teleportation

No final game asset for this polish was committed yet.

### C. Airship Bridge polish

Goal: push the bridge further toward a cohesive magical airship cockpit.

Desired direction:

- panoramic sky dominates the front
- stronger ship-frame architecture around the window
- elegant wooden/brass/violet/cyan visual language
- clearer integrated helm/navigation dais
- richer side consoles without cluttering the walkable center
- naturally integrated ChaCha Resonance Pedestal
- absolutely no small ship model inside the bridge

A concept image was generated in-session showing a grand magical bridge with panoramic windows, a central crystal navigation mechanism, side consoles, and a ChaCha station. It is conceptual reference only and was NOT committed to the repository or implemented as game art yet.

## Important distinction for the next session

The concept images generated at the end of this chat are inspiration references, not approved replacement sprites/maps yet.

Do not silently replace `airship_visual.png` or alter the locked exterior asset based only on those concepts.

The user's last action was to ask to save the conversation history to GitHub and prepare to continue in a new chat.

## Recommended immediate next task

Continue with an Airship Visual Polish phase, likely version `.4.14.4.5` or a dedicated visual branch created from the current materialized head.

Suggested order:

1. Inspect current `DrawSkyDock`, `DrawSkyDockInteriorDetails`, and `DrawDeckMarkers` code plus current TMX maps.
2. Polish visual overlays while preserving all current gameplay transitions and collision contracts.
3. Keep `airship_visual.png` locked unless the user explicitly approves changing the official exterior sprite.
4. Build a test ZIP and have the user judge the visual in-game by screenshots.
5. Only after visual approval, decide whether any generated concept should be translated into production pixel art/assets.

## User working style reminder

- Language: Vietnamese.
- Prefers direct implementation and quick test builds.
- Likes visual cohesion and polished game feel.
- Expects CI, compile fixes, materialization, and packaging to be handled proactively.
- Do not invent unapproved balance/design details when a value is genuinely unresolved.
