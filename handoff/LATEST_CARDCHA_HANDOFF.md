# LATEST CARDCHA HANDOFF

Updated: 2026-09-30

Repository: `RVTGMzz/SV-CC-SB`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`  
Current TEST version: `0.3.0-alpha.28.0.4.14.4.5.12.78`  
Current phase: `0696D3-N Cabin Light Sources Night Fix`  
Current status: **CI PASS / PACKAGE READY / RUNTIME RETEST REQUIRED**

## Read first

1. `handoff/NEXT_CHAT_PROMPT_2026-09-30_CARDCHA_0696D3N.md`
2. `handoff/AIRSHIP_0696D3N_CABIN_LIGHT_SOURCES_NIGHT_FIX.md`
3. `handoff/SESSION_HANDOFF_2026-09-30_CARDCHA_0696D3N.md`
4. `handoff/AIRSHIP_0696D3M_ROOM_LIGHTING_COLLISION_LAYER_FIX.md`
5. `handoff/RUNTIME_FEEDBACK_2026-09-29_D3L_ROOM_COLLISION_LIGHTING.md`

## Latest runtime authority

Ron tested Room 1 around 20:00 and supplied a screenshot where the room is nearly black even with D3-M .77 ambient recovery.

Therefore:
- D3-M Room 1 night lighting = Runtime FAIL.
- Do not solve this by only increasing `Game1.ambientLight` again.
- D3-N adds real Stardew `LightSource` fixtures.

## D3-N .78

Eight room-scoped light fixtures now illuminate:
- route board;
- Lost & Found;
- waiting bench;
- luggage;
- boarding left;
- boarding right;
- BOARD AIRSHIP center;
- exit.

The lights are re-added if Stardew clears them and removed on room exit/runtime reset.

D3-M Room 2 collision/depth fixes remain locked.

## CI / package

CI run: `36618505784`  
Job: `109577593356`  
Canonical source/package commit: `1a66357931b35bffff7a0894320e7d868880ab2c`  
Conclusion: **SUCCESS**

Tag: `cardcha-0696d3n-test-1a663579`

Package:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.78_0696D3N_CabinLightSourcesNightFix_TEST.zip`

SHA256:
`133f6decaae31ce61578dc56075c7f2059be19189fb8f4243ac97112ef7354c7`

Direct package:
`https://github.com/RVTGMzz/SV-CC-SB/releases/download/cardcha-0696d3n-test-1a663579/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.78_0696D3N_CabinLightSourcesNightFix_TEST.zip`

Static / CI:
- D3-N night cabin-light validator: PASS
- D3-M collision/depth carry-forward checks: PASS
- no legacy Window overlay reuse: PASS
- render-depth contract: PASS
- Release compile: PASS, 0 errors
- package audit: PASS
- prerelease publication: PASS

Project still emits 55 pre-existing analyzer warnings, mostly NetField guidance outside this patch.

## Runtime retest focus

1. Enter Room 1 at 20:00 or later.
2. Confirm visible light pools and readable room.
3. Leave Room 1; confirm no light leaks into other maps.
4. Re-enter; confirm cabin lights return.
5. Quickly recheck Room 2 UPGRADE collision + Window/console depth.

Do not call Runtime PASS until Ron confirms this exact .78 package in game.


## Next-chat authority

Use `handoff/NEXT_CHAT_PROMPT_2026-09-30_CARDCHA_0696D3N.md` for the next session.

The older `handoff/NEXT_CHAT_PROMPT_2026-09-19_CARDCHA_0696D3K.md` is historical only and must not be treated as current authority.
