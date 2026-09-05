# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0647a-mimi-portrait-unification`

Current build:
`0.3.0-alpha.28.0.4.14.4.5.12.1`

Read this FIRST when resuming from another chat:
`handoff/ALPHA28_0647A_MIMI_PORTRAIT_UNIFICATION.md`

Previous handoffs:
- `handoff/ALPHA28_0647_AIRSHIP_ROOM_ARCHITECTURE.md`
- `handoff/ALPHA28_0646C_MIMI_HOME_ROUTINE_PORTRAIT.md`
- `handoff/ALPHA28_0646B_MIMI_ROUTINE_GATE_FIX.md`
- `handoff/ALPHA28_0646A_MIMI_HOME_STABILITY_PORTRAIT.md`
- `handoff/ALPHA28_0646_MIMI_SECRET_TV_ROUTINE.md`
- `handoff/ALPHA28_0645_MIMI_ATTIC_LIVING_LORE.md`

## Current verified state
- `.5.12.1` is the current MiMi portrait + movement acceptance build.
- `assets/mimi_portraits.png` is the only on-disk MiMi portrait source in the packaged mod.
- `mimi_portraits_runtime64.png` and `mimi_npc_portraits.png` are removed from source/package.
- Stardew's required 64px dialogue compatibility texture is generated only in memory from the 128px master using nearest-neighbour sampling, not averaging blur.
- Story, Town, merchant, social, Attic and TV routine dialogue all route through the same canonical master-derived portrait pipeline.
- MiMi home anchor moved off the upper wall/window row to `(10,6)`; TV anchor is `(5,9)`; late anchor remains `(13,7)`.
- Home/TV/late each have open-floor wander pools with clear-tile fallback instead of freezing on a blocked first entry.
- `cardcha_story_status` / Home diagnostics expose `RoutineState`, `WanderTarget`, and current actor location/tile.
- 0647 Airship/Sky Dock room architecture/collision pass is inherited unchanged.

## Verified build
- workflow run: `33958161204` SUCCESS
- job: `101285144806` SUCCESS
- artifact ID: `9967046225`
- outer artifact digest: `sha256:6d025d8a175a62717cfa4e3b3346f02e54070f638730ef3ef5e3044b309b55d3`
- package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.1_MiMiPortraitUnified_TEST.zip`
- package SHA-256: `607409ab95c156885b1f0a2c753bbeb3dfc76b31f57ad58c537e2ba62bc10673`

## Locked canon / regression guard
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- Forest Arcane Gate action distance 160px and `CollisionEdits=NONE`.
- locked `airship_visual.png` unchanged.
- Airship route, upgrade menu/costs and deferred gameplay bonuses unchanged.

## Next action
In-game accept `.5.12.1`: compare MiMi portrait inside the Attic against Town/story/merchant dialogue; then force `home`, `tv`, and `late` with `cardcha_test_mimi_routine`, wait 10-15 seconds in each state, and confirm she visibly walks within the intended floor zone instead of standing at the window. Use `cardcha_story_status` to report `RoutineState`, `WanderTarget`, and Actor tile if movement still fails.
