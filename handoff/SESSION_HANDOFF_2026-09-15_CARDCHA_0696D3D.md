# Cardcha session handoff — 2026-09-15 — 0696D3-D

Repository: `ronvotri/Cardcha-Shardbound`
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
Head before this handoff was written: `25fa61c66253e73a78609b41859ee57e9f7a0db0`
Current TEST version in source: `0.3.0-alpha.28.0.4.14.4.5.12.70`

## Resume point

Resume at **0696D3-D regression + TEST packaging**. Do not restart D2 source recovery and do not redo D3-A/B/C from scratch.

D3-A, D3-B and D3-C implementation work already exists on the branch. D3-D has only been started far enough to restore the corrected radar backing and bump the source/manifest version to `.70`. A final D3-D regression run, compile/package audit and downloadable TEST artifact have **not** yet been completed at this checkpoint.

## Completed work

### 0696D3-A — gameplay room integration

Status: implemented + CI pass.

Checkpoint: `handoff/AIRSHIP_0696D3A_CHECKPOINT.md`
Validation: `handoff/AIRSHIP_0696D3A_GAMEPLAY_ROOM_INTEGRATION_VALIDATION.json`
Materialized commit: `fa23a9ba178d36da5d1cf55080d3594ea20a16ff`
Successful workflow run: `34895005876`

Implemented:
- dedicated travel/boarding interaction at deck tile `(4,5)` using existing boarding-gate art;
- Region I departure owned by the dedicated gate instead of being hidden on the helm/radar interaction;
- all four upgrade systems remain present: Engine, Navigation, Hull, Reactor;
- grounded plinth treatment added to the upgrade stations;
- physical base-footprint collision added to all four stations;
- D2.1 Observation Window source bytes and frozen D1S independent airship preserved.

Upgrade collision footprints:
- Engine: `(4,8)`, `(5,8)`
- Navigation: `(18,8)`, `(19,8)`
- Hull: `(7,11)`, `(8,11)`
- Reactor: `(15,11)`, `(16,11)`

### 0696D3-B — prop integration

Status: implementation + CI pass exists, but one historical radar cleanup decision was later corrected by Ron and superseded.

Checkpoint: `handoff/AIRSHIP_0696D3B_CHECKPOINT.md`
Validation: `handoff/AIRSHIP_0696D3B_PROP_INTEGRATION_VALIDATION.json`
Materialized commit: `f3bde3e46934d0d7d1830ef71d888360b3a4807d`
Successful workflow run: `34895825578`

Implemented before correction:
- radar/desk physical collision footprint;
- four upgrade-machine visuals normalized from 104x104 to 96x96 while keeping D3-A gameplay coordinates/interactions;
- D3-A travel gate preserved.

**Authoritative correction from Ron:** the supplied radar/workstation reference intentionally has a warm yellow/golden backing/background. The earlier D3-B assumption that this backing should be removed was wrong. The reference image itself is authoritative. Do not make the radar backing transparent just because it is opaque/yellow.

Correction commit:
`7f988f492bd5b7f0a6bee14b0db4ffacdf19c8fe` — `fix: restore 0696D3 radar reference backing`

Current radar source file:
`src/Cardcha/assets/airship_props/set01_redux/navigation_console_base.png`

Important regression hazard: the old D3-B checkpoint and the existing D3-B automation/script were created before Ron's correction and may still encode the now-invalid "remove yellow/beige backing" rule. **Do not blindly rerun D3-B materialization/workflow until its expectations are updated to preserve the restored yellow/golden reference backing.** Historical checkpoint text describing background removal is superseded by this handoff and by `handoff/AIRSHIP_0696D3_ROOM_INTEGRATION_FEEDBACK.md` after commit `99fabc0f052930a1374ae92afcda3cfdb5ede882`.

### 0696D3-C — room shell and entrances

Status: validation PASS.

Validation: `handoff/AIRSHIP_0696D3C_ROOM_SHELL_ENTRANCES_VALIDATION.json`
Materialized commit: `167fd9e6aceca142ea2d767466961c2cb6d7793b`

Validated implementation:
- room 1 shares the room-shell/border treatment;
- room-1 doorway tiles remain `(14,17)` and `(15,17)`;
- outdoor entrance gate scale changed from `1.48` to `2.88`, with bottom-anchor policy preserved;
- gate use distance changed from `160` to `256`;
- Observation Window presentation scale changed from `4.0` to `4.25`, about `+6.25%`, using centered runtime overscan;
- approved D2.1 canonical source bytes were not changed.

D2.1 canonical Observation Window production SHA256 values remain:
- morning: `93f6d4fcd403838d5758be012448c44978e65a8a4cb8bb33d4b24e4fb00802c0`
- noon: `38cf1e47d73b7374c21932ca6fbd957a3f55d833385698d0b415721ebaddb29f`
- evening: `2b3fb1ec4e4dd8d0bb7b2a3cf511ce7f8757e8dbbbb9ba54493f791df6aa0b5f`
- night: `5d9ec8cbb2f13221d0463e474209d5a7bb3fbc4d1eb05bee28a15483b4c1173b`

## Latest correction chain

- `99fabc0f052930a1374ae92afcda3cfdb5ede882` — corrected the 0696D3 integration checklist and recorded the yellow/golden radar backing requirement.
- `7f988f492bd5b7f0a6bee14b0db4ffacdf19c8fe` — restored the radar reference backing.
- `25fa61c66253e73a78609b41859ee57e9f7a0db0` — bumped Cardcha D3-D TEST version from `.69` to `.70` in `Cardcha.csproj`, `Directory.Build.targets` and `manifest.json`.

## Authoritative Ron requirements for the next TEST

1. Upgrade pedestal rebuild + restoring the missing floor-2 upgrade machines is **one combined task**, never two separate checklist items.
2. Upgrade machinery must feel integrated rather than pasted, use believable scale and proper base collision, and intended machines must be interactable.
3. Map travel / boarding gate must be obvious, discoverable and functional so Ron can reach route/combat testing.
4. Radar/workstation must follow Ron's supplied reference image. Preserve its characteristic yellow/golden backing plus the warm ornate wood/gold workstation and turquoise/green central radar/map display. Do not invent a different machine and do not strip the backing merely for transparency.
5. Room 1 border/shell must visually match room 2.
6. Entrance/boarding arch should be aligned and roughly 2x the prior presentation while preserving usable opening/collision.
7. Observation Window should be only slightly larger, not 2x, and its four time buckets must still work.
8. Frozen D1S independent small-airship art/animation must remain intact.

## D3-D work still to do

Before creating the `.70 TEST` package:

1. Reconcile D3-B regression tooling with Ron's corrected radar requirement so no automation removes the restored yellow/golden backing.
2. Run regression checks for:
   - Morning / Noon / Evening / Night Observation Window resolution;
   - D1S independent airship preserved;
   - four upgrade stations present after reload and their intended interactions reachable;
   - dedicated travel gate reachable from normal player approach and route travel functional;
   - major machine/radar footprints block walk-through only at physical bases;
   - room 1 and room 2 shell/borders render correctly;
   - entrance arch remains aligned, enlarged and usable;
   - Observation Window remains at the slight D3-C presentation enlargement;
   - radar reference backing remains yellow/golden and not stripped.
3. Compile Release.
4. Produce/package the next `.70 TEST` artifact.
5. Run package audit/validation against the final packaged bytes.
6. Record the final workflow run, artifact ID/digest, package SHA256 and materialized commit in a D3-D validation/checkpoint file.
7. Hand Ron only the resulting TEST package for visual/gameplay acceptance.

At this handoff there is no completed `.70 TEST` package to claim and no D3-D CI PASS to claim yet.

## Do not do

- Do not restart exhausted 0696D2 source recovery.
- Do not claim the historical lost 160x80 production hashes were recovered.
- Do not modify the frozen D1S small-airship source art.
- Do not activate weather/season runtime variants as part of this room-integration finish unless Ron explicitly expands scope.
- Do not silently restore legacy Observation Window background overlays.
- Do not make the radar backing transparent against Ron's corrected reference.
- Do not recreate the radar from memory.
- Do not split upgrade-pedestal rebuild and floor-2 upgrade-machine restoration into separate checklist tasks.
- Do not treat `.69` as accepted.
- Do not claim `.70` is packaged or accepted until D3-D actually finishes.

## Files to read first in the next chat

1. `handoff/SESSION_HANDOFF_2026-09-15_CARDCHA_0696D3D.md`
2. `handoff/LATEST_CARDCHA_HANDOFF.md`
3. `handoff/AIRSHIP_0696D3_ROOM_INTEGRATION_FEEDBACK.md`
4. `handoff/AIRSHIP_0696D3_ROOM_INTEGRATION_PLAN.md`
5. `handoff/AIRSHIP_0696D3C_ROOM_SHELL_ENTRANCES_VALIDATION.json`
6. `handoff/AIRSHIP_0696D3B_CHECKPOINT.md` only as historical implementation evidence, with its old radar-background-removal wording treated as superseded.
7. `handoff/AIRSHIP_0696D3A_CHECKPOINT.md`
8. `handoff/AIRSHIP_0696D2_REBASELINE_CANONICAL.json`

When Ron says **"tiếp"** in the next chat, immediately resume D3-D from this checkpoint. Do not ask him to restate the checklist.
