# ALPHA28 0646B MiMi Routine + Gate Fix

Branch: `cardcha-alpha28-0646b-mimi-routine-gate-fix`

Version: `0.3.0-alpha.28.0.4.14.4.5.11.2`

Verified workflow run: `33955031159` SUCCESS

Artifact ID: `9966069204`

TEST package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.11.2_MiMiRoutineGateFix_TEST.zip`

TEST SHA-256: `4a6513fee74a835de91fcdcb5db587fcece6ff079cef6431cf97790d1f1caae5`

## User-reported issues fixed

1. MiMi's attic is now explicitly a home, not a shop. After the normal daily friendship greeting, empty-hand interaction in `Cardcha_MiMiAttic` no longer opens the MiMi shop. Gifting remains native Stardew behavior.
2. MiMi attic routine uses fixed known anchors instead of re-resolving a nearby clear tile each tick:
   - default home `(10,4)`
   - TV routine `(5,10)` facing north
   - late/personal `(13,7)`
3. Added runtime-only debug command `cardcha_test_mimi_routine <home|tv|late|auto>` so each home state can be forced immediately without changing friendship or save progression.
4. `cardcha_version` now reports `ModManifest.Version` instead of a stale hardcoded build string.
5. Forest Arcane Gate relocation was changed from a blind fenced-area shift to a reachable-placement resolver. Target direction is toward the open meadow immediately right of the pink blossom tree. It flood-fills walkable tiles from the Farm side and accepts only a clear 3x3 gate footprint with a reachable action tile.
6. `cardcha_test_gate` now lands one tile farther below the resolved gate to improve reachable-side testing.

## Locked contracts preserved
- Save schema 19.
- Boss Form 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 card audit PASS.
- Arcane Gate action distance 160px.
- `CollisionEdits=NONE` remains locked. No fence/map collision is removed.
- Locked Airship exterior SHA remains unchanged.
- Airship upgrade costs/routes and deferred bonuses unchanged.

## In-game acceptance
- In attic run `cardcha_test_mimi_routine home`, `tv`, `late`; MiMi must visibly occupy three different anchors and stay stable.
- Run `cardcha_test_mimi_routine auto`, set 6+ hearts, then verify 17:30 -> TV and 22:00 -> personal corner.
- Talk twice to MiMi at home; second empty-hand interaction must not open shop.
- Run `cardcha_test_gate`; gate and farmer must be on the reachable side near the pink blossom tree. Action should enter the Arcane Dock.
