# Cardcha Alpha28 0648A - Airship + MiMi Acceptance Hotfix

## Canonical branch
`cardcha-alpha28-0648a-airship-mimi-acceptance-hotfix`

## Build
- Version: `0.3.0-alpha.28.0.4.14.4.5.12.7`
- Package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.7_AirshipMiMiAcceptanceHotfix_TEST.zip`
- Inner package SHA-256: `d6ecf532e3218cf7e28521c9fbade8b4f2a31ad152f1526835011b54b23702b2`
- Compiled DLL size: 764,416 bytes

## Verified CI
- Workflow run: `33980136589` SUCCESS
- Job: `101343778226` SUCCESS
- Artifact ID: `9973503051`
- Artifact name: `cardcha-alpha28-0648a-airship-mimi-acceptance-hotfix`
- Outer artifact digest: `sha256:724d062543ac8db42e0903885c8b13c3a439615209a97604a03d424ded2e83c5`
- Materialization commit: `9a3e306274326baa53e1279ad86193f1722f1964`

## Scope fixed from in-game 0648 rejection
### 1. Airship wall collision
- Airship wall rows 0-7 are fully blocked on `Buildings`.
- Sky Dock wall rows 0-8 are fully blocked.
- The visual floor starts exactly at those walkable boundaries.
- This prevents the farmer from walking onto window/wall art.

### 2. Bottom/side void escape
- Airship bottom row now has exactly two openings: tiles 11 and 12.
- Sky Dock bottom row now has exactly two openings: tiles 14 and 15.
- These exactly match `IsBottomDoorwayZone()`.
- The accidental third opening from 0647E/0648 was removed, so the farmer cannot slip into black void and walk sideways outside the room.

### 3. Upgrade machine alignment
0648 support pads were offset by -8px/-8px from the runtime machine tile centers. 0648A moves the baked pad centers to:
- Engine `(88,152)`
- Navigation `(296,152)`
- Hull `(136,168)`
- Reactor `(248,168)`

Runtime station visual center was also lowered from `tile.Y*64 + 34` to `tile.Y*64 + 54`, so the machine body visually seats into its base instead of hovering above it.

### 4. Airship brightness and active machine glow
- Airship backdrop receives a warm ambient brightness lift.
- Sky Dock receives a smaller warm lift.
- Upgrade atlas dark values are raised without resampling or changing alpha.
- Every upgrade machine gets a low, always-on pixel glow even at level 0.
- Existing stronger level > 0 / level 3 accents remain.

### 5. ChaCha Resonance access
Old station tile `(19,5)` overlapped the right console/collision mass.
0648A splits it into:
- visual anchor: `(21,5)`
- interaction anchor: `(21,8)`

The backdrop alcove and renderer accent are moved to the far-right wall while player interaction stays on the walkable floor.

### 6. MiMi clock acceptance test
Normal gameplay still requires 6 hearts for the 17:30 TV routine.

For TEST acceptance only, `cardcha_test_attic` now turns on a runtime-only clock preview without changing friendship or story flags. While that preview is active:
- `world_settime 1720` => HOME
- `world_settime 1730` => TV
- `world_settime 2000` => TV
- `world_settime 2200` => LATE

MiMi home anchor moved away from the window:
- home anchor: `(9,8)`
- home idle pool: `(9,8) (8,8) (10,8) (9,9) (10,9)`
- TV anchor remains `(5,9)`
- late anchor remains `(13,7)`

`cardcha_story_status` / HomeService diagnostics now expose clock preview, current clock, routine state, wander target and actor tile.

## Independent package verification
- Airship TMX: 24x14, valid CSV token counts, wall rows 0-7 blocked, bottom openings exactly `[11,12]`.
- Sky Dock TMX: 30x18, valid CSV token counts, wall rows 0-8 blocked, bottom openings exactly `[14,15]`.
- Four machine socket collision anchors remain nonzero.
- Central travel lanes remain walkable.
- `mimi_portraits.png` remains the only packaged MiMi portrait source.
- Deprecated `mimi_portraits_runtime64.png` and `mimi_npc_portraits.png` remain absent.

## Visual asset hashes
- `airship_deck_stardew.png`: `59b44c565074ca296269900c039234ccd09982c9a5e0ec4812af7566625642c5`
- `sky_dock_stardew.png`: `5da83b825c779a929f811ead5b1ad06b489852631774b4a23ae52a2a14f2ba6f`
- `airship_upgrade_visuals.png`: `54e685feb0e8611c69c5e07f840ad8f43282c7edb53f04ec0ffb8931ed64b861`

## Locked canon / regression guards
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- Forest Arcane Gate action distance remains 160px.
- Forest `CollisionEdits=NONE` remains locked.
- `airship_visual.png` remains unchanged at SHA-256 `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- Route remains `Forest -> Cardcha_SkyDockInterior -> Cardcha_AirshipDeck`.
- Upgrade menu/costs/levels and deferred Airship gameplay bonuses are unchanged.
- No pickup Airship furniture is reintroduced.

## Acceptance test
1. Replace the whole Cardcha folder and restart SMAPI.
2. `cardcha_version`
3. `cardcha_test_airship`
   - try walking into upper wall/windows
   - try escaping at bottom left/right
   - inspect four machine alignment/glow
   - approach ChaCha Resonance from the floor
4. `cardcha_test_attic`
5. Run in order:
   - `world_settime 1720`
   - `world_settime 1730`
   - `world_settime 2000`
   - `world_settime 2200`
6. If MiMi still fails to move, run `cardcha_story_status` and capture the diagnostics.
