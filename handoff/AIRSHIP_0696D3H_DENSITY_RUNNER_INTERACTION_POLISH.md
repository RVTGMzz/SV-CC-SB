# AIRSHIP 0696D3-H — DENSITY + RUNNER + INTERACTION POLISH

Updated: 2026-09-18

Repository: `ronvotri/Cardcha-Shardbound`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`  
Version: `0.3.0-alpha.28.0.4.14.4.5.12.72`

## Status

**SOURCE / ASSET / TMX / STATIC API AUDIT: PASS**  
**GITHUB CI: BLOCKED BEFORE RUNNER**  
**PACKAGE: NOT BUILT YET**  
**RUNTIME: PENDING RON IN GAME**

Never call CI PASS or Runtime PASS for D3-H until those exact stages really happen.

## Runtime authority

Newest authority is Ron's 2026-09-18 post-D3-G 12-image retest.

D2 and D3-A/B/C/D/E/F/G are historical checkpoints. Do not restart them.

D3-H specifically responds to:
- Room 1 feeling too large / sparse;
- several Room 1 props visually oversized;
- Lost & Found interaction incorrectly landing on the waiting bench;
- prop head-cut / foreground ownership problems;
- need for a Stardew-like floor runner leading to boarding/travel;
- Room 1 daylight still needing stronger recovery;
- D3-G console separation removing too much machine detail;
- TRAVEL affordance needing to be larger;
- Navigation upgrade station needing to be larger;
- remaining lamp/depth interference;
- Observation Window reading detached from the wall.

## Materialized D3-H changes

### Room 1

- Resized `sky_dock_interior.tmx` from `30x18` to `24x15`.
- New room area is exactly `360 / 540 = 2/3` of the old map area.
- Day ambient changed to `25 25 25`; night ambient remains differentiated at `105 95 85`.
- Added restrained functional pixel light pools at route / Lost & Found / boarding anchors.
- Added nearest-neighbor ~2/3 visual versions of:
  - waiting bench;
  - Lost & Found wall board;
  - luggage cart.
- Lost & Found interaction moved from the waiting bench to the large wall board.
- Waiting bench, luggage cart and cargo now have their own localized info interactions.
- Bench / luggage / cargo bodies no longer live on `Front2`.
- Native collision `5400` covers solid bases/posts only.
- Front interaction rows stay open so the Farmer can stand in front and press Use.
- Boarding gate posts are blocked but center passage remains open.
- Signal lamp base has native collision.

### Runner / floor guidance

New asset:

`src/Cardcha/assets/airship_props/set01_redux/airship_runner_d3h.png`

Contract:
- 16px-high tile atlas;
- 10-color pixel palette;
- alpha values only `0 / 150 / 220 / 255`;
- woven purple texture;
- brass stitch;
- subtle floor shadow;
- map-owned on `Back2`, not a post-world smooth overlay.

Room 1 runner leads from the bottom doorway to `BOARD AIRSHIP`.

Room 2 runner leads from the bottom doorway to `TRAVEL`.

### Room 2

- D3-G frame-only console body is retired.
- D3-H uses `navigation_console_body_d3h.png`, byte-identical to the original full-detail hard-alpha machine asset.
- Console remains map-owned and out of `Front2`.
- TRAVEL gate presentation width increased from `244` to `366` pixels, i.e. 1.5x.
- Navigation upgrade presentation uses `192x192` instead of `96x96`, i.e. 2x.
- All four upgrade stations keep their canonical sockets:
  - `(4,8)`
  - `(19,8)`
  - `(7,11)`
  - `(16,11)`
- All four remain native-collision-backed.
- Station glow is stronger but remains pixel-rect based.
- Remaining signal lamp moved to the far-right wall and receives native collision.
- Observation Window presentation changed from `4.25x` overscan to exact `4.0x` wall footprint.

## Collision / interaction guards

Do not reintroduce:
- `player.Position = ...` collision recovery;
- `LastSafePlayerPosition`;
- D3-F/D3-G forced-footprint rewind helpers;
- console body on `Front2`;
- full `DrawDeckMarkers` replay;
- giant collision rectangles over walkable center lanes.

Keep:
- native `5400` collision;
- open front interaction rows;
- four upgrade sockets;
- TRAVEL;
- BOARD AIRSHIP;
- center gate passages.

## Static evidence

`handoff/AIRSHIP_0696D3H_STATIC_API_AUDIT.json`

Implementation/static-audit source commit before handoff docs:

`49ad816ab33a86af28ced60c2bd67fcea97d4c3d`

Static/API audit result: **PASS**.

The audit verifies version identity, map size, collision cells, open interaction rows, scaled asset wiring, runner placement, console ownership, TRAVEL scale, Navigation 2x scale, four sockets, lamp relocation, Window ownership, and absence of forced Farmer-position correction.

## CI blocker

D3-H workflow:

`.github/workflows/cardcha-alpha28-0696d3h-density-runner-interaction-polish.yml`

Run:

`35347643349`

Attempts: `3`

Attempt 1 job: `105607896700`  
Attempt 2 job: `105608153047`  
Attempt 3 job: `105611724798`

All three attempts failed before `Set up job`, with zero steps and no allocated runner.

For comparison, D3-G run `35287327146` previously received a GitHub runner, executed all 27 steps, compiled, packaged and published successfully.

Therefore the current D3-H CI failure is an infrastructure/runner-allocation blocker, not evidence of a C# compile or validator failure.

Do not call this CI PASS.

## Local build fallback

Canonical Windows fallback script:

`tools/build_0696d3h_local.ps1`

It runs the D3-H static validator, historical guards, Release compile, package assembly, package audit and SHA256 generation. It does not promote Runtime PASS.

## Package status

No canonical D3-H TEST ZIP exists yet.

Do not reuse the D3-G DLL/package and relabel it D3-H because D3-H contains C# changes in interaction, travel/station scale, ambient presentation and depth behavior.

A real D3-H package must contain a freshly compiled `Cardcha.dll`.

## Runtime acceptance

After CI/build becomes available, Ron must test the exact D3-H package and verify:

1. Room 1 feels denser and appropriately scaled.
2. Waiting bench is only a bench; Lost & Found is the large wall board.
3. Room 1 props can be approached and interacted with naturally from the front.
4. Bench/luggage/cargo no longer cut across the Farmer's head.
5. Runner visually belongs to Stardew and does not look like a flat luminous overlay.
6. Runner leads naturally to BOARD AIRSHIP / TRAVEL.
7. Daytime Room 1 is clearly readable.
8. Console keeps full machine detail without beige/yellow matte or blanket foreground coverage.
9. TRAVEL feels ~1.5x more prominent.
10. Navigation upgrade feels ~2x larger while the other three remain coherent.
11. All four upgrade stations remain visible/interactable.
12. Lamp no longer intersects the relevant gate/station space.
13. Observation Window sits against the wall and does not float/overscan.
14. No ghost/body desync returns.

Only Ron's explicit in-game confirmation promotes D3-H to Runtime PASS.
