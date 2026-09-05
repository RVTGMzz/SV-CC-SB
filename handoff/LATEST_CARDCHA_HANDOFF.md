# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0647d-fixed-gate-station-identity`

Current build:
`0.3.0-alpha.28.0.4.14.4.5.12.4`

Read this FIRST when resuming from another chat:
`handoff/ALPHA28_0647D_FIXED_GATE_STATION_IDENTITY.md`

Previous handoffs:
- `handoff/ALPHA28_0647C_AIRSHIP_TMX_CSV_HOTFIX.md`
- `handoff/ALPHA28_0647B_MIMI_PORTRAIT_RUNTIME_HOTFIX.md`
- `handoff/ALPHA28_0647A_MIMI_PORTRAIT_UNIFICATION.md`
- `handoff/ALPHA28_0647_AIRSHIP_ROOM_ARCHITECTURE.md`
- `handoff/ALPHA28_0646C_MIMI_HOME_ROUTINE_PORTRAIT.md`
- `handoff/ALPHA28_0646B_MIMI_ROUTINE_GATE_FIX.md`
- `handoff/ALPHA28_0646A_MIMI_HOME_STABILITY_PORTRAIT.md`
- `handoff/ALPHA28_0646_MIMI_SECRET_TV_ROUTINE.md`
- `handoff/ALPHA28_0645_MIMI_ATTIC_LIVING_LORE.md`

## Current verified state
- `.5.12.4` fixes the Forest Arcane Gate having two competing runtime placement systems.
- Gate placement is now deterministic from the Forest Farm warp at offset `(-23,+10)`, clamped only to map bounds.
- The old `AirshipGateRelocationPatch` installs no runtime relocation/flood-fill hook.
- Forest gate interaction is canonical 160px and `CollisionEdits=NONE` remains locked.
- `cardcha_test_gate` no longer invalidates/re-rolls gate placement before warping the farmer.
- Route remains `Forest -> Cardcha_SkyDockInterior -> Cardcha_AirshipDeck`; there is no MiMi-attic routing from AirshipFoundationService.
- Sky Dock domestic cues were removed and replaced with transit/workshop wall panels + dock beacon.
- Airship Deck has stronger bridge/control-room identity while preserving the existing helm and four upgrade stations.
- 0647C TMX CSV parser fix is preserved: Airship 336 tokens/layer; Sky Dock 540 tokens/layer; no empty tokens/trailing commas.
- 0647B MiMi portrait single-source runtime fix remains intact.
- MiMi home/TV/late movement code and diagnostics remain intact.

## Verified build
- workflow run: `33962944082` SUCCESS
- job: `101297906920` SUCCESS
- materialization commit: `2f37ebe7abb2fad9298c55149a464291fa00e599`
- artifact ID: `9968514179`
- outer artifact digest: `sha256:c77424cf2a6941be2c7e6731f2d202ff9c530d2a295e186ecf58bba877dbff73`
- package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.4_FixedGateStationIdentity_TEST.zip`
- package SHA-256: `8f80946661ba0cc6b85c0aa0ac1a972121529e65282ee2f2ff1556ed19cfe382`

## Locked canon / regression guard
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- Forest Arcane Gate action distance 160px and `CollisionEdits=NONE`.
- locked `airship_visual.png` unchanged.
- Airship route, upgrade menu/costs and deferred gameplay bonuses unchanged.

## Next action
Install `.5.12.4`, fully restart SMAPI, run `cardcha_test_gate`, and repeatedly approach/leave the gate to verify its world position is fixed. Enter the gate, verify Sky Dock is visually distinct from MiMi's attic, then use the boarding bay to reach the Airship Deck and verify the bridge identity/upgrades.
