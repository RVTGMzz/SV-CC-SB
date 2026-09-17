# AIRSHIP 0696D3-E RUNTIME INTERACTION AND RENDER-DEPTH FIX

Updated: 2026-09-17

Repository: `ronvotri/Cardcha-Shardbound`
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
Current TEST version: `0.3.0-alpha.28.0.4.14.4.5.12.70`

## Authority

This D3-E checkpoint supersedes stale D3-D runtime assumptions wherever Ron's latest in-game feedback conflicts with them.

D3-D remains a historical regression baseline only. In particular, D3-D's yellow/golden radar backing acceptance is NOT current runtime authority. Ron's latest runtime feedback requires the visible radar/navigation console to have no yellow/static backing behind the animated radar.

Do not restart D2 and do not redo D3-A/B/C.

## Runtime failures addressed by D3-E

1. Forest/Airship gate overlays the player.
2. Floor-2 props blanket-overlay the player.
3. Radar still shows the yellow/static backing.
4. Radar is not actionable for travel.
5. Most floor-1/floor-2 props miss interaction because gameplay was tied to fragile exact action tiles.

## Source corrections

### Render depth

`src/Cardcha/Patches/AirshipGateDepthPatch.cs`

- Suppresses the normal post-world `AirshipFoundationService.DrawDeckMarkers` pass.
- Replays `DrawDeckMarkers` immediately before local `Farmer.draw` while on `Cardcha_AirshipDeck`.
- Keeps the existing Forest gate before/after-Farmer depth handling.
- This is an incremental safety bridge until every solid Airship prop has native/TMX world ownership.

`src/Cardcha/Patches/WorldPhysicalOverlaySafetyPatch.cs`

- Keeps the three unsafe legacy post-world painters suppressed:
  - `AirshipFoundationService.DrawRegion1Details`
  - `AirshipInteriorStardewRenderer.DrawDeckStardewDecor`
  - `AirshipInteriorStardewRenderer.DrawDockStardewDecor`
- `DrawUpgradeStations` is deliberately NOT blanket-suppressed in D3-E because upgrade stations now render inside the pre-Farmer deck pass.

### Interaction footprints

`AirshipGateDepthPatch` postfixes `AirshipFoundationService.GetActionTile()` and normalizes visible prop footprints back to the existing canonical gameplay handlers.

Deck coverage:
- radar/helm footprint -> existing travel-gate handler
- travel gate
- all four upgrade stations
- deck exit

Sky Dock interior coverage:
- route station
- bay station
- lost + found
- exit

The existing travel system remains authoritative; D3-E does not introduce a parallel travel implementation.

### Radar backing

`src/Cardcha/Services/AirshipAmbientAnimationService.cs`

- Main navigation-console path no longer draws `RadarBackground`.
- Animated glow/sweep/pings remain.
- Missing/failed ambient assets no longer fall back through `DrawLegacyFullOverlay()` for the console.
- The map-native console remains visible if ambient assets are unavailable, preventing the old yellow/static radar backing from resurfacing through fallback.

## D3-E validators

Added:
- `tools/alpha28_0696d3e_runtime_interaction_render_depth.py`
- `tools/alpha28_0696d3e_package_audit.py`

The D3-E static validator explicitly checks:
- depth patches are registered
- normal post-world deck-marker pass is suppressed
- deck markers replay before local Farmer
- exactly the three known unsafe legacy painters remain suppressed
- upgrade stations are not blanket-suppressed
- action-tile postfix is installed
- radar routes to the existing travel gate handler
- travel gate, four upgrades, and floor-1 interaction footprints are covered
- radar background is not rendered
- legacy console fallback is disabled
- missing ambient assets keep the map-native console
- animated radar layers remain

## CI / package evidence

Final successful workflow run:
`35190364448`

Job:
`105101364982`

Final workflow/source commit used by the successful run:
`97133aaa38344593b89d6a65ae9b22bdfe8ab1b2`

Workflow:
`.github/workflows/cardcha-alpha28-0696d3e-runtime-interaction-render-depth.yml`

CI result:
- historical D3-D regression: PASS
- D3-E static validator: PASS
- no-legacy Window overlay validator: PASS
- render-depth contract validator: PASS
- Release compile: PASS
- TEST package audit: PASS
- prerelease publication: PASS

The compile completed with 0 errors. Existing unrelated warnings remain outside D3-E scope.

## Artifact storage workaround

GitHub Actions artifact upload could not be used because the account hit its Actions artifact storage quota.

D3-E therefore publishes its validated TEST payload as a GitHub prerelease asset instead. This does not change the compiled package or its validation status.

Prerelease tag:
`cardcha-0696d3e-test-97133aaa`

Release ID:
`390482299`

Release URL:
`https://github.com/ronvotri/Cardcha-Shardbound/releases/tag/cardcha-0696d3e-test-97133aaa`

## TEST package

`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.70_0696D3E_RuntimeInteractionRenderDepthFix_TEST.zip`

Release asset ID:
`569629212`

Release asset digest:
`sha256:f811f9b8ad34c6310a3de39eab0408814227f0b57142004c8d6276b73a425ec3`

Direct package URL:
`https://github.com/ronvotri/Cardcha-Shardbound/releases/download/cardcha-0696d3e-test-97133aaa/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.70_0696D3E_RuntimeInteractionRenderDepthFix_TEST.zip`

The prerelease also contains:
- D3-D regression evidence
- D3-E runtime interaction/render-depth validation evidence
- D3-E package audit
- D3-E CI identity evidence
- package SHA file

## Runtime status

**RUNTIME RETEST REQUIRED**

CI/static/build/package are green. This is NOT Runtime PASS.

Only Ron's in-game test can accept D3-E.

## Ron runtime retest checklist

1. Walk in front of and behind the gate; confirm it no longer blanket-overlays the player and the intended occlusion still reads correctly.
2. Walk around representative floor-2 props and all four upgrade stations; confirm they no longer all render above the player.
3. Check the radar/navigation console; confirm there is no yellow/static backing behind the radar animation.
4. Interact with the radar from natural adjacent/visible footprint tiles; confirm it opens/uses the existing travel route behavior.
5. Test representative interactions on both floors: radar, travel gate, four upgrade machines, Sky Dock route, bay, lost + found, and exits.
6. Confirm interaction cannot trigger through obvious walls or from an excessive distance.
7. Only after these checks pass may D3-E be called `Runtime PASS`.

## Resume instruction

Start from this D3-E checkpoint and `handoff/LATEST_CARDCHA_HANDOFF.md`.

Do not restore the D3-D yellow/golden radar-backing runtime assumption. Do not recreate a package just to repeat already-green CI. The next authority is Ron's runtime retest of the D3-E prerelease above.
