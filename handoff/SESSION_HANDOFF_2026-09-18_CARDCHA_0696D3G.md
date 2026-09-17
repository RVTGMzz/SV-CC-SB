# SESSION HANDOFF — 2026-09-18 — CARDCHA 0696D3-G

Repository: `ronvotri/Cardcha-Shardbound`
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`

## Resume authority

Read in this order:

1. `handoff/AIRSHIP_0696D3G_ASSET_SEPARATION_NATURAL_COLLISION_DAYLIGHT_RECOVERY.md`
2. `handoff/LATEST_CARDCHA_HANDOFF.md`
3. `handoff/AIRSHIP_0696D3F_PHYSICAL_BLOCKING_TRAVEL_DEPTH_RECOVERY.md`
4. `handoff/AIRSHIP_0696D3E_RUNTIME_INTERACTION_RENDER_DEPTH_FIX.md`

Newest authority is Ron's 2026-09-18 in-game D3-F runtime feedback. The six screenshots and the observations captured in the D3-G authority document override older static validators or visual assumptions when they conflict.

## Current status

- D3-F CI/static/build/package: **PASS**.
- D3-F in-game runtime acceptance: **FAIL**.
- Current phase: **0696D3-G Asset Separation + Natural Collision + Daylight Recovery**.
- Runtime status: **RETEST REQUIRED after a new D3-G package exists**.
- Do not call Runtime PASS until Ron tests and explicitly confirms.

## Proven D3-F build provenance

Workflow run: `35247550568`
Job: `105291478417`
Workflow/package source commit: `76471e8de7160449d882dfc416b15c34d4db61ea`
Source-fix commit: `d3c35cb595ef32f3f9970f747c3bfd4a84fe2a79`
Prerelease tag: `cardcha-0696d3f-test-76471e8d`
Release ID: `390886558`
Package asset ID: `570641822`
Package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.70_0696D3F_PhysicalBlockingTravelDepthRecovery_TEST.zip`
Package SHA256: `7811763b5a8263f13dc5cb11d9dad6657223cbb7529a0e4c423591ed11f998f4`

## What D3-F improved and must not regress

- Four upgrade stations are visible.
- `UPGRADE` affordances exist.
- `TRAVEL` affordance exists.
- Travel/radar handler wiring exists.
- D3-E runtime `RadarBackground` draw is already removed.
- D3-E stale workflow was frozen manual-only so it does not generate false-red CI against D3-F/D3-G architecture.

## What D3-F failed at runtime

### Room 1 collision

The runtime physical blocker/recovery implementation creates a visually broken movement state where the moving shadow/ghost-like component can continue while the Farmer body appears pinned. This feels unlike native Stardew collision.

Do not preserve this approach. Remove forced player-position correction from production collision handling and author conservative TMX collision footprints instead.

### Room 2 depth

The two largest props still blanket-overlay the Farmer:

- the large Observation Window / upper room composition;
- the central navigation-console / helm workstation.

Do not fix them by replaying or suppressing the whole room render pass around Farmer drawing. Re-author their actual map-layer ownership and, where necessary, split assets into body/back/front components.

### Console background

The central console still has a large opaque light beige/yellow rectangle. This remains after D3-E removed `state.RadarBackground` and after D3-F attempted runtime map-tile clearing.

This proves the remaining background belongs to the production asset/map composition, not the runtime radar-background layer.

D3-G must inspect and clean the actual console sprite alpha, then use the cleaned asset in TMX/map layering. Do not add another runtime mask.

### Gate/lamp composition

A signal lamp/column visually passes through the travel gate. Move/remove/re-layer it so the gate reads cleanly.

### Daylight

The Airship bridge remains very dark during daytime. Fix room/location lighting itself, not just the window scene.

### Outdoor gate collision

The player can still walk through obvious solid wood/post sections. Add selective segmented collision to solid pieces while keeping the central passage usable. Do not use one giant rectangular blocker.

## High-priority files to inspect next

- `src/Cardcha/Services/AirshipFoundationService.cs`
- `src/Cardcha/Services/AirshipInteriorStardewRenderer.cs`
- `src/Cardcha/Services/AirshipAmbientAnimationService.cs`
- `src/Cardcha/Patches/AirshipGateDepthPatch.cs`
- `src/Cardcha/Patches/WorldPhysicalOverlaySafetyPatch.cs`
- `src/Cardcha/assets/airship_deck.tmx`
- `src/Cardcha/assets/sky_dock_interior.tmx`
- `src/Cardcha/assets/airship_props/set01_redux/navigation_console_base.png`
- `src/Cardcha/assets/airship_props/set01_redux/console_runtime/navigation_console_frame.png`
- `src/Cardcha/assets/airship_props/set01_redux/airship_ambient_manifest.json`
- `src/Cardcha/assets/airship_props/set01_redux/boarding_gate_arch.png`

## Technical facts already established

- Deck map is 24x14.
- Sky Dock interior is 30x18.
- Navigation console base occupies a 7x5 TMX footprint.
- `AirshipAmbientAnimationService.DrawNavigationConsole` currently draws only radar glow/sweep/pings plus frame, not `state.RadarBackground`.
- Therefore the remaining beige rectangle must be traced to map/base sprite content or another flattened production layer.
- Cardcha already has a native blocker tileset contract: `CardchaCollision0690` / tile 5400 / `Passable=F`.
- D3-G should prefer this map-native collision model over runtime forced Farmer repositioning.
- D3-F upgrade stations are now visible and should stay that way.

## D3-G implementation sequence

1. Inspect actual PNG alpha/background of console source assets.
2. Materialize a real transparent console asset, preserving only intended machine pixels.
3. Re-author `airship_deck.tmx` console/Observation Window layer ownership so only genuinely foreground pixels can occlude Farmer.
4. Remove coarse runtime physical-blocker/player-position correction added by D3-F.
5. Add conservative TMX-native collision footprints for Room 1/Room 2 solid bases.
6. Add segmented outdoor gate collision for solid posts/wood, central lane open.
7. Fix interior travel gate/lamp overlap.
8. Trace and fix daytime bridge lighting/tint.
9. Verify four upgrade stations and travel/radar interaction are preserved.
10. Add D3-G static validator and package audit that explicitly reject stale D3-E full overlay ownership and stale D3-F forced-position collision.
11. Build on GitHub-hosted Ubuntu and publish a D3-G TEST prerelease while Actions artifact quota remains full.
12. Ask Ron for in-game retest. Only then may Runtime PASS be considered.

## CI constraints

- Use GitHub-hosted `ubuntu-latest`.
- Do not switch to self-hosted runner unless Ron explicitly asks later.
- Actions artifact storage quota was full, so continue publishing TEST ZIPs via GitHub prerelease unless the quota situation is deliberately changed.
- D3-F workflow is historical once D3-G workflow exists; freeze it manual-only if its path triggers start producing stale red status, following the same pattern already used for D3-E.

## Do not do

- Do not restart 0696D2.
- Do not redo D3-A/B/C/D/E/F.
- Do not call Runtime PASS from static CI/build/package evidence.
- Do not add another runtime beige-background mask.
- Do not replay the entire `DrawDeckMarkers` pass around Farmer drawing.
- Do not keep the D3-F forced player-position blocker as the collision solution.
- Do not remove the now-visible four upgrade stations or travel affordance while fixing visuals.

## Copy-paste resume prompt for the next chat

`Tiếp tục Cardcha từ 0696D3-G trên branch cardcha-alpha28-0696d2-window-environment-matrix. Đọc handoff/AIRSHIP_0696D3G_ASSET_SEPARATION_NATURAL_COLLISION_DAYLIGHT_RECOVERY.md, handoff/SESSION_HANDOFF_2026-09-18_CARDCHA_0696D3G.md và handoff/LATEST_CARDCHA_HANDOFF.md. Authority mới nhất là runtime feedback của Ron sau D3-F: Room 1 blocker gây hiệu ứng bóng/hồn đi nhưng xác Farmer bị giữ lại; hai prop lớn Room 2 vẫn đè player; navigation console vẫn còn nền beige/vàng và phải tách nền asset thật; cột đèn xuyên cổng; phòng ban ngày vẫn quá tối; cổng ngoài cần collision từng khúc ở phần gỗ/trụ nhưng giữ lối giữa. D3-F CI PASS nhưng Runtime FAIL. Preserve 4 upgrade stations + TRAVEL. Làm D3-G thành patch thật + asset/TMX thật + validator/CI/package mới. Không restart D2, không redo D3-A/B/C/D/E/F, không dùng lại forced player-position blocker, và chỉ gọi Runtime PASS khi Ron test package D3-G rồi xác nhận.`
