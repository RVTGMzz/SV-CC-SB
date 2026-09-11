# Alpha 28 0695 - Region I Environment Prop Production Integration

## Source of truth
- Branch: `cardcha-alpha28-0695-region1-prop-integration`
- Parent concept: `cardcha-alpha28-0694-region1-environment-prop-concept` @ `5f8fdafa4dfd7db964728cbe6378da1c82b102ea`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.61`
- Materialized source head: `39e13a370281b29f77d94be497603a3243edda41`

## Approved direction
Ron approved the 0694 Region I environment concept for production integration. 0695 implements that approved Stardew-forest language without changing Hunt Run gameplay topology.

## Production changes
- Added one Cardcha-owned native 16px RGBA prop tilesheet: `region1_environment_props_0695.png` (256x128, 128 tiles).
- Added seven approved prop families: moss/root, log/stump, forage/mushroom, field-stone ruins, trail signs, briar/hollow growth, and Card Shrine relics.
- Integrated the sheet into all six `region1_rooms/*.tmx` maps as `CardchaRegion1Environment0695` at firstgid 6000.
- Added map-native `BackDecor` ground-detail compositions with a different authored signature per room.
- Replaced only already-solid `Buildings` cells on inherited outer collision geometry with visual prop bases; the zero/non-zero collision mask is unchanged.
- Added selective `Front` upper silhouettes only outside protected gameplay bands.
- Removed the runtime call to `Region1StardewDecorRenderer.Draw`.
- Removed the now-unused legacy `Region1StardewDecorRenderer.cs` and `region1_environment_decor.png`.
- Retired only the obsolete `WorldPhysicalOverlaySafetyPatch` hook which referenced the removed Region I room renderer; the Region I main-hub and Airship safety hooks remain active.

## Gameplay freeze
The following anchors remain source-of-truth and unchanged: arrival near `(14,17)`, retreat `(14,18)`, route choices `(9,2)` / `(19,2)`, boss `(14,2)`, boons `(7,5)` / `(14,5)` / `(21,5)`, and rare/lost-cache center `(14,10)`.

0695 changes environment presentation only. Encounters, rewards, run length, route logic, fares, boss rules and Region I main hub remain frozen.

## Rendering-depth contract
- Physical Hunt Run environment art is now TMX-owned (`BackDecor`, `Buildings`, selective `Front`).
- `Display.RenderedWorld` no longer paints the six-room physical environment prop atlas.
- Runtime Hunt Run route/boon/boss markers remain because those are interaction/VFX overlays, not permanent physical furniture.
- `AirshipFoundationService.DrawRegion1Details` remains separately audited legacy debt for the main Region I map and is not falsely marked migrated by 0695.

## Materialized room stats
```json
{
  "verdant-clearing": {"ground": 20, "solidReplacements": 8, "front": 3},
  "moss-creek": {"ground": 22, "solidReplacements": 9, "front": 3},
  "old-ruins": {"ground": 20, "solidReplacements": 11, "front": 4},
  "briar-thicket": {"ground": 22, "solidReplacements": 12, "front": 4},
  "hollow-grove": {"ground": 20, "solidReplacements": 10, "front": 4},
  "card-shrine": {"ground": 20, "solidReplacements": 9, "front": 4}
}
```

## Verified CI / package
Authoritative successful GitHub Actions run: `34655852302`

The successful run passed:
- native asset materialization;
- TMX integration;
- repository render-depth validator;
- dedicated 0695 validator;
- approved change-scope guard;
- inherited Airship / boss / Region I hub / Region II-IV freeze;
- SMAPI build environment;
- Cardcha compile;
- source/handoff materialization;
- TEST package audit;
- artifact upload.

Artifact:
- ID: `10285408808`
- name: `cardcha-alpha28-0695-region1-prop-integration`
- size: `2,658,362` bytes
- artifact digest: `sha256:065ed6936c5d06479eb2927a7c2b717d359a598447f3b9f6e5c35bc57221bbac`

Inner TEST ZIP:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.61_0695_Region1EnvironmentPropIntegration_TEST.zip`

Verified inner ZIP SHA256:
`fac7aaa1c9014aedfd0eba887a1b2bd46531fbb9f676ebd7896b15e321fce726`

Independent post-download audit confirmed:
- outer artifact SHA256 exactly matches GitHub's artifact digest;
- inner `.sha256` file exactly matches the independently recomputed TEST ZIP digest;
- manifest version is `.61`;
- `Cardcha.dll` has a valid `MZ` PE header and is 1,019,392 bytes;
- Region I prop sheet is true RGBA PNG, 256x128;
- all six Hunt Run TMX maps use `CardchaRegion1Environment0695` at firstgid 6000;
- per-room `BackDecor` / `Buildings` / `Front` counts match the validated materialization stats above;
- the legacy `region1_environment_decor.png` is absent from the package.

## Acceptance
CI / repository validation / compile / package: **PASS**.

**In-game visual acceptance: PENDING.** CI success is not visual acceptance. Ron must inspect the real TEST package before this Region I visual pass is called accepted.

Airship 0693 visual acceptance also remains **PENDING** unless Ron separately reports acceptance.

## Continuation
The next visual decision should be driven by Ron's in-game read of the six Hunt Run rooms:
- if composition, depth and readability are good, lock 0695 and move to the next planned system/content slice;
- if a specific room reads too sparse, too busy, or has a depth/occlusion problem, do a targeted 0696 Region I acceptance/polish pass rather than reintroducing physical `RenderedWorld` decoration.
