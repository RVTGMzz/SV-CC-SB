# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0646b-mimi-routine-gate-fix`

Current build:
`0.3.0-alpha.28.0.4.14.4.5.11.2`

Read this FIRST when resuming from another chat:
`handoff/ALPHA28_0646B_MIMI_ROUTINE_GATE_FIX.md`

Previous MiMi handoffs:
- `handoff/ALPHA28_0646A_MIMI_HOME_STABILITY_PORTRAIT.md`
- `handoff/ALPHA28_0646_MIMI_SECRET_TV_ROUTINE.md`
- `handoff/ALPHA28_0645_MIMI_ATTIC_LIVING_LORE.md`
- `handoff/ALPHA28_0643_MIMI_ATTIC_STARDew_REBUILD.md`

Previous Airship visual handoff:
- `handoff/ALPHA28_0642_AIRSHIP_INTERIOR_STARDew_REWORK.md`

## Current verified state
- `.5.11.2` is the current MiMi + gate acceptance build.
- MiMi's attic is a home only: no shop opens there after normal greeting; gifting remains native Stardew behavior.
- MiMi routine anchors are fixed: home `(10,4)`, TV `(5,10)`, late `(13,7)`.
- Runtime debug command: `cardcha_test_mimi_routine <home|tv|late|auto>`.
- Normal routine remains 6+ hearts, TV from 17:30 until 22:00, then personal-corner wind-down.
- Crisp portrait hotfix from `.5.11.1` remains.
- Forest Arcane Gate now searches for a clear placement reachable from the Farm side, targeting the open meadow immediately right of the pink blossom tree instead of blindly landing inside the fenced area.
- `cardcha_test_gate` remains runtime-only and does not alter persistent Airship unlock state.

## Verified build
- workflow run: `33955031159` SUCCESS
- artifact ID: `9966069204`
- package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.11.2_MiMiRoutineGateFix_TEST.zip`
- package SHA-256: `4a6513fee74a835de91fcdcb5db587fcece6ff079cef6431cf97790d1f1caae5`

## Locked canon / regression guard
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- Forest Arcane Gate uses 160px action distance and `CollisionEdits=NONE`.
- Locked Airship exterior `airship_visual.png` unchanged.
- Airship route, upgrade menu/costs and deferred gameplay bonuses remain unchanged.

## Next action
In-game accept `.5.11.2`: force MiMi `home`, `tv`, `late` states and confirm three distinct stable positions; then return to `auto` and verify real 17:30/22:00 transitions. Confirm no shop opens inside MiMi's attic. Run `cardcha_test_gate` and confirm the gate appears on the reachable meadow side immediately right of the pink blossom tree and can be activated.
