# Alpha 28 0692 — Airship RGBA + Gate Restore Hotfix

## Source of truth
- Branch: `cardcha-alpha28-0692-airship-rgba-gate-restore`
- Parent: `cardcha-alpha28-0691-airship-prop-set02-harbor-furnishings` @ `91b9166e915f0b50a3dd23b0cb5e8fb888191974`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.59`
- Materialized source head: `4f443db19f05183a101c9ac4af9b8905b19b9f5f`

## Trigger
Ron tested 0691 in-game and reported a visual regression:
- the authored outdoor boarding gate was missing;
- the new Airship/Sky Dock physical prop group was largely absent even though the assets were present in the package;
- the room therefore fell back visually to sparse inherited/procedural elements.

## Root causes addressed
1. 0690/0691 TMX prop PNGs were left as indexed/palette PNGs on the production path. 0692 normalizes every physical Airship TMX prop to true RGBA and points TMX at flat, same-directory production copies.
2. `AirshipGateDepthPatch` suppresses legacy `DrawSkyDock()` by design, but the valid farmer-depth draw path also called `DrawSkyDock()`. 0692 introduces `DrawSkyDockCore()`; the Harmony-blocked wrapper stays legacy-only while farmer-depth rendering calls the unpatched core directly.

## Visual design
No visual redesign. The approved `boarding_gate_arch.png` remains the gate design. No old gate is restored.

## Rendering contract
- Interior physical props remain TMX-owned.
- Existing 0690 window/console motion remains VFX-only.
- No new physical `RenderedWorld` furniture is introduced.
- Exterior gate stays farmer-depth injected via the existing Harmony contract.

## Verified CI / package
Authoritative successful GitHub Actions run: `34628000033`

Artifact:
- ID: `10275895244`
- name: `cardcha-alpha28-0692-airship-rgba-gate-restore`
- artifact digest: `sha256:0c267f59d307a263c684975f97a23be4f85f1a2d15150b71fba9c04606e72627`

Inner TEST ZIP:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.59_0692_Airship_RGBA_GateRestore_TEST.zip`

Verified inner ZIP SHA256:
`0952bf1747e90908e31ebb8fda6bc5a28403d20e5b98586a9f0f00ca8cada695`

Independent post-download audit confirmed:
- manifest version `.59`;
- `Cardcha.dll` valid PE, 1,021,440 bytes;
- Airship Deck and Sky Dock TMX included;
- Set 01 and Set 02 physical PNGs are true `RGBA`;
- boarding gate, route board, signal lamp, cargo crate, departures board, waiting bench and luggage cart are present in the package.

## Acceptance
CI / compile / package: **PASS**.

In-game visual acceptance remains **PENDING** until Ron tests build `.59`. Do not claim the visibility fix is visually accepted before that report.

## Continuation
0692 is a visibility/runtime hotfix, not a new art direction. Future work should preserve the approved Airship visual contract and should not stack more Airship decoration merely to fill space before the hotfix is visually checked.

The next planned visual-design task from Ron's earlier direction is to return to Region I / Map 1 and replace the crude `region1_environment_decor.png` placeholder language with a richer Stardew-faithful map-native prop set. Concept approval should happen before production integration.
