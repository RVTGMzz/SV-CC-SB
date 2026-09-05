# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0647b-mimi-portrait-runtime-hotfix`

Current build:
`0.3.0-alpha.28.0.4.14.4.5.12.2`

Read this FIRST when resuming from another chat:
`handoff/ALPHA28_0647B_MIMI_PORTRAIT_RUNTIME_HOTFIX.md`

Previous handoffs:
- `handoff/ALPHA28_0647A_MIMI_PORTRAIT_UNIFICATION.md`
- `handoff/ALPHA28_0647_AIRSHIP_ROOM_ARCHITECTURE.md`
- `handoff/ALPHA28_0646C_MIMI_HOME_ROUTINE_PORTRAIT.md`
- `handoff/ALPHA28_0646B_MIMI_ROUTINE_GATE_FIX.md`
- `handoff/ALPHA28_0646A_MIMI_HOME_STABILITY_PORTRAIT.md`
- `handoff/ALPHA28_0646_MIMI_SECRET_TV_ROUTINE.md`
- `handoff/ALPHA28_0645_MIMI_ATTIC_LIVING_LORE.md`

## Current verified state
- `.5.12.2` is the current MiMi portrait runtime hotfix acceptance build.
- Root cause of the `.5.12.1` SMAPI crash was a stale competing `WorldActorService` `LoadFromModFile` handler for `assets/mimi_portraits_runtime64.png`.
- That competing handler is removed; `MimiMysteryTownService` is now the single loader owner for `Portraits/Ronvotri.Cardcha_MiMi`.
- `WorldActorService` may request the logical Portrait asset through `Game1.content`, which resolves through the canonical master-derived Mystery loader.
- `assets/mimi_portraits.png` remains the only on-disk MiMi portrait source.
- final compiled DLL was byte-audited and contains zero UTF-8/UTF-16 references to `mimi_portraits_runtime64.png` or `mimi_npc_portraits.png`.
- final compiled DLL contains the canonical `assets/mimi_portraits.png` reference.
- nearest-neighbour compatibility rendering is preserved; no averaging blur reintroduced.
- 0647A MiMi home/TV/late movement anchors, wander pools and diagnostics are inherited unchanged.
- 0647 Airship/Sky Dock room architecture/collision pass is inherited unchanged.

## Verified build
- workflow run: `33959901128` SUCCESS
- job: `101289848996` SUCCESS
- materialization commit: `b0c9bb1f2b65952d45b32e5e06656ecacdbd9e62`
- artifact ID: `9967595697`
- outer artifact digest: `sha256:dc9bd5b68ab514c93b3d7646534a758c3ecad6d23ac2ea104d2dbe3324c8414c`
- package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.2_MiMiPortraitRuntimeHotfix_TEST.zip`
- package SHA-256: `40610ef4041fa357dd107e32efad7e077cf98990b8593e5c0915c44d4531f14c`

## Locked canon / regression guard
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- Forest Arcane Gate action distance 160px and `CollisionEdits=NONE`.
- locked `airship_visual.png` unchanged.
- Airship route, upgrade menu/costs and deferred gameplay bonuses unchanged.

## Next action
Install `.5.12.2` by replacing the previous Cardcha mod folder and fully restarting SMAPI. Confirm the `Portraits/Ronvotri.Cardcha_MiMi` load no longer throws `mimi_portraits_runtime64.png` errors, then compare MiMi portraits across Town/story/merchant/Attic dialogue and re-test `home`, `tv`, and `late` movement routines.
