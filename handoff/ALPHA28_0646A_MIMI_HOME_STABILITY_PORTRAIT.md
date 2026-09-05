# ALPHA28_0646A MiMi Home Stability + Portrait Hotfix

Branch:
`cardcha-alpha28-0646a-mimi-home-stability-portrait`

Build:
`0.3.0-alpha.28.0.4.14.4.5.11.1`

## Why this hotfix exists
In-game screenshots from `.5.11` revealed two concrete problems inside MiMi Attic:
1. MiMi could visibly ping-pong/teleport between nearby tiles while the home scheduler was active.
2. Normal social dialogue inside the attic could use the coarse `mimi_portraits_runtime64.png` fallback instead of the sharper runtime portrait pipeline used by Cardcha story dialogue.

The user also requested a direct way to test the Forest Arcane Gate without walking across the Forest or mutating story progression.

## Fixes
### Stable MiMi home anchors
- `MimiHomeService` now caches one resolved tile per current attic routine state (`home`, `tv`, `late`).
- The resolver is no longer rerun every update tick while MiMi herself occupies the chosen tile.
- This removes the A/B tile ping-pong caused by collision checks treating MiMi's current tile as occupied.
- 17:30-22:00 TV routine and 22:00+ personal-corner behavior remain unchanged in design.

### Crisp portrait pipeline
- `MimiMysteryTownService` exposes the already-established in-memory runtime portrait sheet for MiMi social/home dialogue.
- `MimiSocialService` prepares this crisp portrait before Stardew native talk/gift handling.
- During the 17:30 TV routine, empty-hand interaction is deferred to `MimiHomeService`, which uses the same portrait dialogue pipeline.
- Gifting still goes through Stardew's native NPC interaction.

### Direct Arcane Gate test
New SMAPI console command:
`cardcha_test_gate`

Behavior:
- warps the farmer directly beside the resolved Forest Arcane Gate;
- enables runtime-only gate rendering/interaction for the current session;
- does not change `AirshipUnlocked`, story progression, fares, or save schema;
- gate interaction remains 160px and `CollisionEdits=NONE`.

## Verified build
- workflow run: `33954172247` SUCCESS
- materialization commit: `ba292a9c763aab31943607636ca179fb3dca0a07`
- artifact ID: `9965803745`
- artifact outer digest: `sha256:aec2d99fb51c063afa1a978357fe159d8dbee3be7c2f22a864c7da257e98831a`
- package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.11.1_MiMiHomeStabilityPortrait_TEST.zip`
- package SHA-256: `a76a43fbf507af3c94f2a083649565c0e9478026e33b164c9aeefb116d1a29cb`

## Regression locks
- Save schema 19.
- Boss Form 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- Forest Arcane Gate 160px action distance and `CollisionEdits=NONE`.
- locked `airship_visual.png` SHA-256 remains `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- no room-sized MiMi Attic overlay restored.
- Airship route/upgrades/costs and deferred bonuses unchanged.

## In-game acceptance
1. At 6+ hearts, enter MiMi Attic and watch MiMi for 10-20 seconds before/after 17:30. She should remain on one stable tile, not blink between positions.
2. Talk to MiMi before 17:30 and during the 17:30 TV routine. Portrait should match the sharper Cardcha portrait style instead of the coarse fallback.
3. At 22:00 MiMi should relocate once to the late/personal routine tile and stay there.
4. Run `cardcha_test_gate`. Farmer should appear beside the Forest gate and be able to activate it without changing persistent Airship unlock state.
