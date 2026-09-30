# SESSION HANDOFF — CARDCHA 0696D3-N

Updated: 2026-09-30

Repository: `RVTGMzz/SV-CC-SB`  
GitHub write account: `lengochung28191@gmail.com`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`

Current phase: `0696D3-N Cabin Light Sources Night Fix`  
Current TEST version: `0.3.0-alpha.28.0.4.14.4.5.12.78`

## Current authority

D3-N exists because Ron tested D3-M .77 around 20:00 and Room 1 was still almost completely black.

D3-M ambient-only recovery therefore failed at night.

D3-N adds **8 real Stardew LightSource fixtures** to `Cardcha_SkyDockInterior` instead of trying to solve the problem by raising ambient alone.

Fixture coverage:
- route board;
- Lost & Found;
- waiting bench;
- luggage;
- boarding left;
- boarding right;
- BOARD AIRSHIP center;
- exit.

The fixtures:
- use unique `Ronvotri.Cardcha/D3N/*` IDs;
- are scoped to Room 1;
- are re-added if Stardew clears them;
- are removed when leaving Room 1 or resetting runtime.

## Carry-forward from D3-M

Preserve:
- Room 2 Window lower-sill collision;
- full-body 3x2 TMX collision for all four UPGRADE stations;
- Window/console background-depth correction;
- no broad `GameLocation.isCollidingPosition` Harmony postfix;
- no `Farmer.Position` pin/rewind blocker;
- TRAVEL center remains open;
- BOARD AIRSHIP center throat remains open;
- Resonance interaction remains reachable.

Do not restart D2 and do not redo D3-A/B/C/D/E/F/G/H/I/J/K/L/M.

## CI / package

Canonical source/package commit:
`1a66357931b35bffff7a0894320e7d868880ab2c`

Current branch HEAD after documentation-only commits:
`18b50fdf042c9339a24def74371a408e9a82e8c3`

CI run: `36618505784`  
CI job: `109577593356`  
Conclusion: **SUCCESS**

Compile: **0 errors**  
Existing analyzer warnings: **55**

Tag:
`cardcha-0696d3n-test-1a663579`

Package:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.78_0696D3N_CabinLightSourcesNightFix_TEST.zip`

SHA256:
`133f6decaae31ce61578dc56075c7f2059be19189fb8f4243ac97112ef7354c7`

Direct package:
`https://github.com/RVTGMzz/SV-CC-SB/releases/download/cardcha-0696d3n-test-1a663579/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.78_0696D3N_CabinLightSourcesNightFix_TEST.zip`

Static checks:
- D3-N night cabin-light validator: PASS
- D3-M collision/depth carry-forward checks: PASS
- no legacy Window overlay reuse: PASS
- render-depth contract: PASS
- package audit: PASS
- prerelease publication: PASS

## Runtime status

**RUNTIME RETEST REQUIRED**

Do not call Runtime PASS until Ron tests exact .78 package in game.

Primary retest:
1. Enter Room 1 at 20:00 or later.
2. Confirm visible localized lamp pools and readable navigation.
3. Leave Room 1 and confirm cabin lights do not leak into Forest/other maps.
4. Re-enter and confirm lights return.
5. Quick regression check Room 2:
   - cannot stand inside four UPGRADE machines;
   - Window lower sill solid;
   - Window/console do not blanket-cover Farmer/companion;
   - TRAVEL / BOARD AIRSHIP / Resonance still work.

If .78 is still too dark:
- inspect exact SMAPI runtime log first;
- verify D3-N startup banner;
- check whether the eight light IDs are present/re-added;
- do not blindly increase ambient again.

If .78 works:
- promote D3-N to Runtime PASS for night lighting;
- continue only from new runtime feedback.

## Read first next session

1. `handoff/NEXT_CHAT_PROMPT_2026-09-30_CARDCHA_0696D3N.md`
2. `handoff/LATEST_CARDCHA_HANDOFF.md`
3. `handoff/AIRSHIP_0696D3N_CABIN_LIGHT_SOURCES_NIGHT_FIX.md`
4. `handoff/SESSION_HANDOFF_2026-09-30_CARDCHA_0696D3N.md`
5. `handoff/AIRSHIP_0696D3M_ROOM_LIGHTING_COLLISION_LAYER_FIX.md`
