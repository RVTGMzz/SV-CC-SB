# LATEST CARDCHA HANDOFF

Updated: 2026-09-17

Repository: `ronvotri/Cardcha-Shardbound`
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
Current TEST version: `0.3.0-alpha.28.0.4.14.4.5.12.70`
Current phase: `0696D3-F Physical Blocking, Travel Affordance, and Deck Depth Recovery`
Current status: **RUNTIME RETEST REQUIRED**

## Read first

1. `handoff/AIRSHIP_0696D3F_PHYSICAL_BLOCKING_TRAVEL_DEPTH_FIX.md`
2. `handoff/AIRSHIP_0696D3E_RUNTIME_INTERACTION_RENDER_DEPTH_FIX.md`
3. `handoff/AIRSHIP_0696D3D_CHECKPOINT.md`
4. `handoff/SESSION_HANDOFF_2026-09-15_CARDCHA_0696D3D.md`
5. `handoff/AIRSHIP_0696D3_ROOM_INTEGRATION_FEEDBACK.md`
6. `handoff/AIRSHIP_0696D3C_ROOM_SHELL_ENTRANCES_VALIDATION.json`
7. `handoff/AIRSHIP_0696D3B_PROP_INTEGRATION_VALIDATION.json`
8. `handoff/AIRSHIP_0696D3A_GAMEPLAY_ROOM_INTEGRATION_VALIDATION.json`
9. `handoff/AIRSHIP_0696D2_REBASELINE_CANONICAL.json`

## Current authority

0696D2.1 source recovery/re-baseline is complete. Do not restart it.

D3-A/B/C/D and D3-E remain historical checkpoints. Do not redo them.

The newest authority is Ron's 2026-09-17 in-game screenshot feedback after testing D3-E. D3-E did **not** pass runtime acceptance.

The screenshots proved:

- exterior gate art still allowed impossible player overlap;
- floor-1 props needed real no-enter footprints;
- room-2 deck props still behaved like a floating blanket overlay;
- four upgrade stations were not visibly present;
- the yellow/static console base still survived because it came from the map-native `Buildings2` console body;
- boarding/travel had no obvious visual affordance.

Where any older document or validator conflicts with this runtime evidence, D3-F wins.

## D3-F implementation

D3-F removes the D3-E strategy of replaying the complete `DrawDeckMarkers` pass before the Farmer.

The legacy deck-marker pass is now suppressed. A narrow D3-F pre-Farmer pass owns only:

- Window + transparent radar ambient animation;
- dedicated travel gate / visible `TRAVEL` pad;
- four explicit upgrade stations.

D3-F also adds a physical no-enter guard for Cardcha-owned large-prop footprints. The guard restores the local Farmer to the last safe position before render if movement enters those footprints. Forest map tiles themselves are not rewritten.

### Room 2 / Airship bridge

No-enter footprints now cover:

- navigation-console lower body;
- all four upgrade stations;
- travel-gate side posts while leaving the center open.

Four upgrade stations are explicitly rendered at canonical sockets `(4,8)`, `(19,8)`, `(7,11)`, `(16,11)`. If their atlas fails, visible fallback machines are rendered instead of disappearing.

### Room 1 / Sky Dock

No-enter footprints now cover:

- route/notice-board cluster;
- waiting bench;
- boarding-gate side posts;
- right cargo/service cluster.

A visible `BOARD AIRSHIP` pad is rendered at canonical bay `(23,8)`.

### Forest gate

Only the two visual post zones are guarded. The center/approach remains open. Cardcha does not rewrite Forest collision tiles.

### Radar / console

D3-E had already stopped drawing `state.RadarBackground`, but runtime proved the yellow body was map-native.

D3-F clears only the live 7x5 console-base footprint from `Buildings2` at `x=9..15, y=5..9`, then keeps the transparent runtime console frame plus radar glow/sweep/pings.

Radar remains an alternate travel control. The visible `TRAVEL` pad at the dedicated deck gate is the primary travel affordance.

## Validation / CI

D3-F validator:
`tools/alpha28_0696d3f_physical_blocking_travel_depth.py`

D3-F package audit:
`tools/alpha28_0696d3f_package_audit.py`

D3-F main source patch commit:
`d3c35cb595ef32f3f9970f747c3bfd4a84fe2a79`

D3-F validator commit:
`e1f3a8f6820536d9038be34fd2233cf86a1b3d94`

D3-F package-audit commit:
`3153d7e796a118ab78c4229f2ec5db539f53fcbd`

D3-F workflow/package source commit:
`76471e8de7160449d882dfc416b15c34d4db61ea`

Final successful D3-F workflow run:
`35247550568`

Successful job:
`105291478417`

CI result:

- historical D3-D regression: PASS
- D3-F static source contract: PASS
- no-legacy Window overlay guard: PASS
- render-depth contract: PASS
- Release compile: PASS
- D3-F TEST package audit: PASS
- TEST prerelease publication: PASS

The superseded D3-E workflow is now manual-only so it cannot report fake failures against D3-F architecture.

D3-E workflow-freeze commit:
`97d4dc54a9db07c109f71aa6544e8d2cde942253`

D3-F checkpoint document commit:
`3c79398d2f44e4e4e3dbaba411ac0fd232d85f56`

## Current TEST package

Prerelease tag:
`cardcha-0696d3f-test-76471e8d`

Release ID:
`390886558`

Release URL:
`https://github.com/ronvotri/Cardcha-Shardbound/releases/tag/cardcha-0696d3f-test-76471e8d`

Package:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.70_0696D3F_PhysicalBlockingTravelDepthRecovery_TEST.zip`

Release asset ID:
`570641822`

Package digest:
`sha256:7811763b5a8263f13dc5cb11d9dad6657223cbb7529a0e4c423591ed11f998f4`

Direct package URL:
`https://github.com/ronvotri/Cardcha-Shardbound/releases/download/cardcha-0696d3f-test-76471e8d/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.70_0696D3F_PhysicalBlockingTravelDepthRecovery_TEST.zip`

## Ron runtime retest checklist

1. Forest gate: verify the Farmer cannot stand inside either side post, while the center approach stays usable.
2. Room 1: test the notice-board cluster, waiting bench, boarding posts and right cargo/service cluster. No impossible player overlap should remain.
3. Room 1: verify the visible `BOARD AIRSHIP` pad at the right boarding gate and confirm it reaches the Airship bridge.
4. Room 2: try to enter the navigation console, four station footprints and travel-gate posts. The Farmer should be blocked from the physical body areas.
5. Verify the yellow/static 7x5 navigation-console base is gone while transparent radar/frame animation remains.
6. Verify all four upgrade stations are visible and each opens the intended upgrade menu from a natural adjacent tile.
7. Verify the visible `TRAVEL` pad starts the existing travel flow. Radar must also remain a valid alternate travel control.
8. Verify the central walking spine and bottom doorway remain traversable and the blocking does not feel excessive.
9. Only Ron's successful in-game retest may change this checkpoint to Runtime PASS.

## Resume instruction

Resume from D3-F, not D3-E.

Do not restart D2. Do not redo D3-A/B/C/D. Do not restore the D3-E blanket `DrawDeckMarkers` replay. Do not restore the map-native yellow/static navigation-console base.

The next action is Ron's in-game retest of the D3-F prerelease package above. If any runtime check fails, patch incrementally from D3-F and use the observed screenshot/gameplay behavior as authority.
