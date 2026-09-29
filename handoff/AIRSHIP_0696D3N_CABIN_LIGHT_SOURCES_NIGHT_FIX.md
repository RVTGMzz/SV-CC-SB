# CARDCHA 0696D3-N — CABIN LIGHT SOURCES NIGHT FIX

Updated: 2026-09-30

Repository: `RVTGMzz/SV-CC-SB`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`  
Version: `0.3.0-alpha.28.0.4.14.4.5.12.78`

## Status

**SOURCE / STATIC VALIDATION / RENDER DEPTH / RELEASE COMPILE / PACKAGE AUDIT / PRERELEASE: PASS**  
**RUNTIME: RETEST REQUIRED**

Ron supplied runtime evidence at 20:00 showing Room 1 almost completely black despite the D3-M ambient guard. D3-M is therefore Runtime FAIL for Room 1 night lighting.

## Root cause / correction

D3-M only reasserted `Game1.ambientLight`. Stardew's night lighting pass can still darken the rendered world after that ambient value is set.

D3-N keeps the ambient fallback but adds eight real Stardew `LightSource` fixtures, rendered through the same lighting pipeline as vanilla lamps.

Fixtures:
- Route board: (4,7), radius 3.4, sconce
- Lost & Found: (10,6), radius 3.2, sconce
- Waiting bench: (5,11), radius 3.0, lantern
- Luggage: (10,11), radius 3.0, lantern
- Boarding left: (15,7), radius 3.2, sconce
- Boarding right: (19,7), radius 3.2, sconce
- Boarding center: (17,8), radius 4.2, lantern
- Exit: (12,12), radius 3.6, lantern

All fixtures:
- use unique `Ronvotri.Cardcha/D3N/*` IDs;
- are scoped to `Cardcha_SkyDockInterior`;
- are reinstalled if Stardew clears the current light dictionary;
- are removed when leaving Room 1 or resetting runtime.

## Carry-forward locks

D3-N preserves D3-M:
- Room 2 Window lower-sill collision;
- full-body collision for all four UPGRADE stations;
- Window/console background depth correction;
- no forced `Farmer.Position` blocker;
- no broad collision Harmony postfix.

## CI authority

Run: `36618505784`  
Job: `109577593356`  
Source/package commit: `1a66357931b35bffff7a0894320e7d868880ab2c`  
Conclusion: **SUCCESS**

Release compile: **0 errors**  
Existing project analyzer warnings: **55**  
D3-N cabin-light validator: PASS  
render-depth validator: PASS  
package audit: PASS  
prerelease publication: PASS

Tag: `cardcha-0696d3n-test-1a663579`

Package:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.78_0696D3N_CabinLightSourcesNightFix_TEST.zip`

SHA256:
`133f6decaae31ce61578dc56075c7f2059be19189fb8f4243ac97112ef7354c7`

Direct:
`https://github.com/RVTGMzz/SV-CC-SB/releases/download/cardcha-0696d3n-test-1a663579/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.78_0696D3N_CabinLightSourcesNightFix_TEST.zip`

## Runtime retest

Use exact .78 package.

1. Enter Room 1 at 20:00 or later.
2. Verify the room has visible localized lamp pools and remains readable.
3. Check route board, Lost & Found, bench/luggage, BOARD AIRSHIP, and exit are all visibly lit.
4. Leave Room 1 and verify cabin light does not leak into Forest/other locations.
5. Re-enter and verify lights return.
6. Recheck D3-M Room 2 collision/depth quickly.

Only Ron's in-game confirmation may promote D3-N to Runtime PASS.
