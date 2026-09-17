# SESSION HANDOFF — 2026-09-18 — CARDCHA 0696D3-G

Repository: `ronvotri/Cardcha-Shardbound`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`

## Resume authority

Read first:

1. `handoff/AIRSHIP_0696D3G_ASSET_SEPARATION_NATURAL_COLLISION_DAYLIGHT_RECOVERY.md`
2. `handoff/LATEST_CARDCHA_HANDOFF.md`
3. this file

Newest runtime authority is Ron's 2026-09-18 D3-F in-game feedback. D3-G has now been implemented and packaged, but has **not yet been runtime accepted**.

## Current status

- D3-F: CI PASS / Runtime FAIL.
- D3-G: source + asset + TMX + validator + Release compile + package audit + prerelease **PASS**.
- D3-G runtime: **RETEST REQUIRED**.
- Never call Runtime PASS until Ron tests the exact D3-G `.71` package and explicitly confirms.

## What D3-G changed

- Removed all forced local-Farmer position rewind/pinning collision logic.
- Replaced Room 1 / Room 2 owned collision with native TMX `5400` footprints.
- Added conservative Forest-gate collision through Stardew's collision query, solid segments only, center passage open.
- Added real production asset `navigation_console_body_d3g.png` with verified alpha.
- Moved all console body tiles to `Buildings2`; zero console body tiles remain on `Front2`.
- Moved all Observation Window physical-shell tiles to `Back2`.
- Runtime console now draws radar animation only, not a full console body/frame.
- Removed the left signal lamp that intersected the interior travel gate.
- Added native `AmbientLight=70 70 70` and `AmbientNightLight=145 135 115` bridge lighting.
- Preserved four upgrade stations plus `TRAVEL`, `BOARD AIRSHIP`, and radar travel wiring.
- Frozen historical D3-F workflow to manual-only.

## Canonical D3-G validation/build provenance

Final successful run: `35287327146`  
Job: `105422447116`  
Package/source commit: `cd056a680ba50ee5d03b0f7d200537eb76e7f276`

Successful gates:

- D3-D historical gameplay/asset invariants: PASS, excluding only intentional `.70 -> .71` version identity
- D3-G asset/TMX validator: PASS
- no-legacy Window reuse guard: PASS
- render-depth contract: PASS
- Release compile: PASS
- package audit: PASS
- prerelease publish: PASS

## Package for Ron

Tag: `cardcha-0696d3g-test-cd056a68`  
Release ID: `391120631`  
Asset ID: `571374818`

Package:

`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.71_0696D3G_AssetSeparationNaturalCollisionDaylightRecovery_TEST.zip`

SHA256:

`05f367c54359223c882b2123cb4529f9eb04dc841e6cb5f099758504018437d8`

Release:

`https://github.com/ronvotri/Cardcha-Shardbound/releases/tag/cardcha-0696d3g-test-cd056a68`

Direct package:

`https://github.com/ronvotri/Cardcha-Shardbound/releases/download/cardcha-0696d3g-test-cd056a68/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.71_0696D3G_AssetSeparationNaturalCollisionDaylightRecovery_TEST.zip`

## Runtime retest priority

Ron should verify, in this order:

1. Room 1 collision no longer creates ghost/body desync.
2. Console beige/yellow rectangle is gone.
3. Observation Window and console no longer blanket-cover the Farmer.
4. Four upgrade stations remain visible/interactable.
5. TRAVEL and radar travel remain usable.
6. Lamp no longer intersects travel gate.
7. Daytime bridge is clearly brighter than night.
8. Forest gate blocks solid pieces but leaves center passage open.

## Important technical guards

Do not reintroduce:

- `player.Position = ...` as collision recovery;
- `LastSafePlayerPosition`;
- full console runtime frame/body replay;
- console body on `Front2`;
- `navigation_console_base.png` as the deck TMX console source;
- full `DrawDeckMarkers` replay around Farmer;
- one giant Forest-gate rectangle.

Preserve:

- four canonical upgrade station sockets `(4,8) (19,8) (7,11) (16,11)`;
- visible `UPGRADE` and `TRAVEL`;
- travel/radar handler wiring;
- center walking lanes.

## If Ron reports a runtime failure

Patch incrementally from D3-G. Do not restart D2 and do not redo D3-A/B/C/D/E/F.

Runtime screenshots/gameplay observations override static assumptions when they conflict.

## Copy-paste resume prompt

`Tiếp tục Cardcha từ 0696D3-G package .71 trên branch cardcha-alpha28-0696d2-window-environment-matrix. Đọc handoff/AIRSHIP_0696D3G_ASSET_SEPARATION_NATURAL_COLLISION_DAYLIGHT_RECOVERY.md, handoff/SESSION_HANDOFF_2026-09-18_CARDCHA_0696D3G.md và handoff/LATEST_CARDCHA_HANDOFF.md. D3-G source/asset/TMX/validator/CI/package đều PASS ở run 35287327146, source commit cd056a680ba50ee5d03b0f7d200537eb76e7f276, package .71 tag cardcha-0696d3g-test-cd056a68. Runtime vẫn RETEST REQUIRED. Preserve 4 upgrade stations + TRAVEL. Không dùng lại forced player-position blocker, console Front2 blanket, beige base hoặc full DrawDeckMarkers replay. Chỉ gọi Runtime PASS khi Ron test đúng package D3-G và xác nhận.`
