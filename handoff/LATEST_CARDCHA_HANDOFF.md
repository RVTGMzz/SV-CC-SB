# LATEST CARDCHA HANDOFF

Updated: 2026-09-17

Repository: `ronvotri/Cardcha-Shardbound`
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
Current TEST version: `0.3.0-alpha.28.0.4.14.4.5.12.70`
Current phase: `0696D3-E Runtime Interaction and Render-Depth Fix`

## Read first

1. `handoff/AIRSHIP_0696D3E_RUNTIME_INTERACTION_RENDER_DEPTH_FIX.md`
2. `handoff/AIRSHIP_0696D3D_CHECKPOINT.md`
3. `handoff/SESSION_HANDOFF_2026-09-15_CARDCHA_0696D3D.md`
4. `handoff/AIRSHIP_0696D3_ROOM_INTEGRATION_FEEDBACK.md`
5. `handoff/AIRSHIP_0696D3C_ROOM_SHELL_ENTRANCES_VALIDATION.json`
6. `handoff/AIRSHIP_0696D3B_PROP_INTEGRATION_VALIDATION.json`
7. `handoff/AIRSHIP_0696D3A_GAMEPLAY_ROOM_INTEGRATION_VALIDATION.json`
8. `handoff/AIRSHIP_0696D2_REBASELINE_CANONICAL.json`

## Current authority

0696D2.1 source recovery/re-baseline is complete. Do not restart it.

D3-A/B/C and D3-D remain historical validated checkpoints. Do not redo them.

The newest authority is Ron's runtime feedback that produced D3-E. Where an older document or validator conflicts with that runtime feedback, D3-E wins.

In particular, the old D3-D/D3-B assumption that the yellow/golden radar backing must remain is superseded for runtime presentation. D3-E keeps the underlying historical asset frozen for regression purposes but does not render that static/yellow backing behind the live radar.

## D3-E runtime failures addressed

1. Gate still overlaid the player.
2. Floor-2 props still blanket-overlaid the player.
3. Radar still showed a yellow/static background.
4. Radar was not actionable for travel.
5. Most objects on floors 1 and 2 missed interaction.

## D3-E implementation status

- Deck `DrawDeckMarkers` post-world pass is suppressed and replayed immediately before local Farmer drawing.
- Forest gate keeps actor-relative depth handling.
- Three unsafe legacy post-world physical painters remain suppressed.
- Upgrade stations are no longer blanket-suppressed and render in the pre-Farmer deck pass.
- Radar/helm footprint normalizes to the existing travel-gate handler.
- Travel gate, all four upgrade stations, deck exit, Sky Dock route/bay/lost+found/exit use forgiving visible-footprint normalization.
- Static radar background draw is removed from the live navigation-console path.
- Missing ambient assets no longer invoke the legacy full-overlay console fallback that could restore the yellow backing.

## Validation / CI

D3-E validator:
`tools/alpha28_0696d3e_runtime_interaction_render_depth.py`

D3-E package audit:
`tools/alpha28_0696d3e_package_audit.py`

Final successful D3-E workflow run:
`35190364448`

Successful job:
`105101364982`

Successful workflow/source commit:
`97133aaa38344593b89d6a65ae9b22bdfe8ab1b2`

D3-E checkpoint document commit:
`304a4fb7a8f55f211e7e1dfb3c8105ce79a18e5c`

CI result:
- historical D3-D regression: PASS
- D3-E static source contract: PASS
- no-legacy Window overlay guard: PASS
- render-depth contract: PASS
- Release compile: PASS, 0 errors
- D3-E TEST package audit: PASS
- TEST prerelease publication: PASS

## Package delivery

GitHub Actions artifact storage quota is currently full, so the validated TEST package is published as a GitHub prerelease asset instead of an Actions artifact.

Prerelease tag:
`cardcha-0696d3e-test-97133aaa`

Release ID:
`390482299`

Release URL:
`https://github.com/ronvotri/Cardcha-Shardbound/releases/tag/cardcha-0696d3e-test-97133aaa`

TEST package:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.70_0696D3E_RuntimeInteractionRenderDepthFix_TEST.zip`

Release asset ID:
`569629212`

Package digest:
`sha256:f811f9b8ad34c6310a3de39eab0408814227f0b57142004c8d6276b73a425ec3`

Direct package URL:
`https://github.com/ronvotri/Cardcha-Shardbound/releases/download/cardcha-0696d3e-test-97133aaa/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.70_0696D3E_RuntimeInteractionRenderDepthFix_TEST.zip`

## Current status

**RUNTIME RETEST REQUIRED**

Do not call Runtime PASS from CI/static/build/package evidence alone.

## Ron runtime retest checklist

1. Walk in front of and behind the gate and verify player occlusion is correct.
2. Walk around representative floor-2 props and all four upgrade stations and verify there is no blanket prop-over-player rendering.
3. Verify radar has no yellow/static backing.
4. Press/interact with radar from natural adjacent/visible tiles and verify the existing travel route behavior opens/works.
5. Test radar, travel gate, four upgrade machines, Sky Dock route, bay, lost + found, and exits on floors 1 and 2.
6. Verify interactions cannot trigger through obvious walls or from excessive distance.
7. Only Ron's successful in-game retest may change this checkpoint to Runtime PASS.

## Resume instruction

Resume from D3-E, not D3-D.

Do not restart D2. Do not redo D3-A/B/C. Do not restore the stale runtime yellow-radar-backing assumption. Do not create another package merely to repeat CI that is already green.

The next action is Ron's in-game retest of the D3-E prerelease package above. If any of the six runtime checks fail, patch incrementally from this D3-E checkpoint and produce a new validated TEST package.
