# CARDCHA 0696D3-M — ROOM LIGHTING + TMX COLLISION + LAYER ORDER RUNTIME FIX

Updated: 2026-09-29

Repository: `RVTGMzz/SV-CC-SB`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`  
Version: `0.3.0-alpha.28.0.4.14.4.5.12.77`

## Status

**SOURCE / STATIC VALIDATION / RENDER DEPTH / RELEASE COMPILE / PACKAGE AUDIT / PRERELEASE: PASS**  
**RUNTIME: RETEST REQUIRED**

Ron supplied live screenshots from D3-L .76 after world entry. They are the runtime authority for D3-M:

1. Room 1 was nearly black/unreadable.
2. Room 2 allowed Farmer to stand inside/on UPGRADE machine bodies.
3. Room 2 Window/console presentation could visually cover Farmer/companion incorrectly.

D3-M is a narrow response to those three failures. It does not reopen save-load work and does not restore the broad collision Harmony postfix.

## Implementation

### Room 1 lighting recovery

`AirshipFoundationService` now owns a narrow runtime lighting guard while `Cardcha_SkyDockInterior` is active.

- target ambient: `255 250 240`
- previous `Game1.ambientLight` is saved on entry;
- target ambient is reasserted while Room 1 is active;
- previous ambient is restored on exit;
- no screen-sized translucent brightness overlay is drawn.

TMX is also authored with:
- `AmbientLight = 255 250 240`
- `AmbientNightLight = 225 215 200`

### Room 2 UPGRADE collision

The old base-row-only collision was insufficient because each runtime UPGRADE visual is 96x96.

D3-M uses native TMX `Buildings` collision across the full physical body:

- Engine: `x3..5, y7..8`
- Navigation: `x18..20, y7..8`
- Hull: `x6..8, y10..11`
- Reactor: `x15..17, y10..11`

Adjacent interaction lanes remain open.

### Room 2 Window collision

The Observation Window lower sill/body edge is now solid:

- `x7..16, y5`

This prevents Farmer entering the lower runtime-frame footprint.

### Room 2 layer/depth correction

The old transient Window/console depths near `0.884x/0.885x` were too high for content that must sit behind Farmer in the room.

D3-M uses true background depths:

- Window backdrop: `0.0200`
- Window airship: `0.0205`
- Window frame: `0.0210`
- Console glow: `0.0500`
- Console sweep: `0.0505`
- Console pings: `0.0510`
- Window lightning also uses the background Window depth.

## Carry-forward locks

D3-M preserves:
- no broad `GameLocation.isCollidingPosition` Harmony postfix;
- no `Farmer.Position` pin/rewind/restore;
- TRAVEL center lane;
- BOARD AIRSHIP center throat;
- Resonance front interaction access;
- D3-L load-safe startup architecture.

## CI / package authority

CI run: `36572926010`  
Job: `109421122962`  
Source/package commit: `5a95978cfb16d40e128c248d66f0b313d8e4294b`  
Conclusion: **SUCCESS**

Static checks:
- D3-M room runtime validator: PASS
- no legacy Window overlay reuse: PASS
- render-depth contract: PASS
- validator non-mutation: PASS
- Release compile: PASS, 0 errors
- package audit: PASS

The project emitted 55 pre-existing SMAPI analyzer warnings, mostly NetField guidance outside this D3-M patch. D3-M introduced no compile error.

Tag: `cardcha-0696d3m-test-5a95978c`

Package:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.77_0696D3M_RoomLightingCollisionLayer_TEST.zip`

SHA256:
`98d5b7e4e53e05e2ae731b94d266c27f5778d2b3bbc48fa01b221025b50ca412`

Direct package:
`https://github.com/RVTGMzz/SV-CC-SB/releases/download/cardcha-0696d3m-test-5a95978c/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.77_0696D3M_RoomLightingCollisionLayer_TEST.zip`

## Runtime acceptance

Use the exact .77 package above.

Verify:
1. Room 1 is readable and no longer near-black.
2. Leaving Room 1 does not leave the whole game over-bright; previous ambient is restored.
3. Farmer cannot stand inside any of the four UPGRADE machines.
4. UPGRADE menus remain reachable from adjacent tiles.
5. Farmer cannot enter the Observation Window lower sill.
6. Observation Window and console transient art no longer blanket-cover Farmer/companion.
7. TRAVEL center still works.
8. BOARD AIRSHIP center still works.
9. Resonance interaction still works.
10. No ghost-body / forced-position behavior returns.

Only Ron's explicit in-game confirmation may promote D3-M to Runtime PASS.
