# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0648-stardew-visual-pass1`

Current build:
`0.3.0-alpha.28.0.4.14.4.5.12.6`

Read this FIRST when resuming from another chat:
`handoff/ALPHA28_0648_STARDew_VISUAL_PASS1.md`

Previous handoffs:
- `handoff/ALPHA28_0647E_AIRSHIP_PHYSICAL_DEPTH_REBUILD.md`
- `handoff/ALPHA28_0647D_FIXED_GATE_STATION_IDENTITY.md`
- `handoff/ALPHA28_0647C_AIRSHIP_TMX_CSV_HOTFIX.md`
- `handoff/ALPHA28_0647B_MIMI_PORTRAIT_RUNTIME_HOTFIX.md`
- `handoff/ALPHA28_0647A_MIMI_PORTRAIT_UNIFICATION.md`
- `handoff/ALPHA28_0647_AIRSHIP_ROOM_ARCHITECTURE.md`
- `handoff/ALPHA28_0646C_MIMI_HOME_ROUTINE_PORTRAIT.md`

## Current verified state
- `.5.12.6` is 0648 Stardew Visual Pass 1 built on the accepted physical/collision architecture from `.5.12.5`.
- Forest Gate placement, 160px action distance, `CollisionEdits=NONE`, route and farmer-aware depth are preserved.
- Forest Gate palette is warmer and less neon: muted violet/teal, warm brass and warmer stone.
- Sky Dock now has explicit transit-station hierarchy: route board left, boarding gantry right, central boarding lane, utility/service clutter and dock beacon.
- Sky Dock utility props are painted into the map; no pickup Furniture is seeded.
- Airship Deck now has a stronger central helm body, left/right system consoles, four matching service pads, a ChaCha resonance equipment alcove and a warmer central runner.
- Four level-aware upgrade machines remain 112x112, collision-backed and usable from their front edge.
- `airship_upgrade_visuals.png` edge-connected opaque purple cell backgrounds were removed; accent palette is muted toward Stardew-compatible teal/blue/mauve.
- TMX collision from 0647E is unchanged and independently validated.
- MiMi single-source portrait and home/TV/late movement regressions remain preserved.

## Verified build
- workflow run: `33976957299` SUCCESS
- job: `101335236454` SUCCESS
- materialization commit: `2315fe1a135024416bf4ce9b8c28c76660681e3a`
- artifact ID: `9972600991`
- outer artifact digest: `sha256:43c0c0a94487b581b3e456bc59971b772bb80db962b7a2fa0849c3fbc5a6d775`
- package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.6_StardewVisualPass1_TEST.zip`
- package SHA-256: `5e709b95af46a4ac4b0ad237a43aca10c2396e22fe8e0ff601b05fcaca81e858`
- compiled DLL size: `762880` bytes

## Materialized visual hashes
- `airship_deck_stardew.png`: `b0fbe6046a2555c8c2a1ccf69e40bcd91592a38dd334162ed3c454b348e889f5`
- `sky_dock_stardew.png`: `9a261a09f633cbe37a5d2bf333b0d806fcff5cf777ce98e7da86258c63ad03d1`
- `airship_upgrade_visuals.png`: `f86b7b69f6a8305189eb9049a78fba115f6c508917dd914695b851426723a16f`

## Locked canon / regression guard
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- locked `airship_visual.png` SHA unchanged: `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- Airship route remains `Forest -> Cardcha_SkyDockInterior -> Cardcha_AirshipDeck`.
- Airship upgrade menu/costs/levels and deferred gameplay bonuses unchanged.

## Next action
Install `.5.12.6`, fully restart SMAPI, test Forest Gate -> Sky Dock -> Airship Deck. Future visual changes should be screenshot-driven micro-polish only; do not redesign route/collision again unless a real gameplay bug is reported.
