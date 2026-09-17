# 0696D3-G Asset Separation + Natural Collision + Daylight Recovery

Updated: 2026-09-18

Repository: `ronvotri/Cardcha-Shardbound`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`

## Status

**CI / STATIC / RELEASE BUILD / PACKAGE / PRERELEASE: PASS**  
**RUNTIME: RETEST REQUIRED**

D3-G is now a real source + asset + TMX + validator + CI/package checkpoint.

Do **not** call Runtime PASS until Ron tests the exact D3-G TEST package below in Stardew Valley and explicitly confirms the runtime checklist.

## Runtime authority

Newest runtime authority remains Ron's 2026-09-18 in-game feedback after D3-F:

1. D3-F forced blocking caused ghost/shadow movement while the Farmer body was held back.
2. The two giant Room 2 props still blanket-covered the player.
3. The navigation console still showed a beige/yellow opaque slab.
4. A signal lamp intersected the interior travel gate.
5. The bridge remained too dark during daytime.
6. The Forest gate needed segmented collision on solid wood/posts while keeping the center passage open.

D3-F is therefore historical **CI PASS / Runtime FAIL** provenance only.

Do not restart D2. Do not redo D3-A/B/C/D/E/F.

## D3-G implementation

### 1. Forced Farmer-position correction removed

`src/Cardcha/Patches/AirshipGateDepthPatch.cs` no longer contains:

- `LastSafePlayerPosition`
- `EnforceD3FPhysicalFootprints`
- `BuildD3FBlockedRects`
- `PrepareD3FDeckMap`
- any `player.Position = ...` collision correction

Room 1 / Room 2 use native TMX collision wherever Cardcha owns the map.

The Forest gate cannot own the Forest TMX, so D3-G hooks Stardew's collision query and returns collision only for conservative solid gate segments. It never teleports, pins, or rewinds the Farmer.

### 2. Real transparent console production asset

New production asset:

`src/Cardcha/assets/airship_props/set01_redux/navigation_console_body_d3g.png`

The file is 112x80 RGBA. CI measured:

- 3,254 fully transparent pixels
- 5,706 visible pixels

The deck TMX no longer references `navigation_console_base.png`.

All 35 console tiles `5100..5134` now belong to `Buildings2`.

There are **zero** console tiles left on `Front2`.

Runtime console drawing now owns only:

- radar glow
- radar sweep
- radar pings

No full console frame/body is replayed at runtime.

### 3. Observation Window depth ownership corrected

All 50 Observation Window physical-shell tiles `5000..5049` moved from `Buildings2` to `Back2`.

The runtime Window pass remains environment/airship animation only. The physical shell is map architecture instead of a giant foreground blanket.

### 4. Natural TMX collision

Deck collision uses the existing `CardchaCollision0690` / tile `5400` / `Passable=F` contract.

D3-G keeps collision only on believable solid bases:

- travel gate: solid side segments, center lane open;
- console: lower solid base only;
- four upgrade stations: grounded base rows only;
- central walking spine remains open.

Sky Dock Room 1 keeps its existing native `5400` footprints for the route board, bench, boarding posts and cargo/service objects. The D3-F runtime reposition guard is gone.

### 5. Interior gate/lamp composition fixed

The left signal-lamp tiles at the interior TRAVEL gate footprint were removed.

The dedicated travel gate is now the dominant landmark at the canonical travel socket.

### 6. Daylight recovery uses native map lighting

`airship_deck.tmx` now declares:

- `AmbientLight = 70 70 70`
- `AmbientNightLight = 145 135 115`

This uses Stardew's location-lighting system instead of painting a giant translucent bright rectangle over the room.

Static validation proves the day/night property contract. Ron's runtime retest remains authoritative for whether the resulting daytime brightness is visually acceptable.

### 7. Four upgrade stations + TRAVEL preserved

Canonical station sockets remain:

- `(4,8)`
- `(19,8)`
- `(7,11)`
- `(16,11)`

Visible `UPGRADE`, `TRAVEL`, and `BOARD AIRSHIP` affordances remain in the D3-G pass.

Travel/radar gameplay handler wiring remains preserved.

## D3-G validators

Static/asset/TMX validator:

`tools/alpha28_0696d3g_asset_separation_natural_collision_daylight.py`

Package audit:

`tools/alpha28_0696d3g_package_audit.py`

The D3-G validator rejects:

- reintroduction of forced `player.Position` collision correction;
- console tiles returning to `Front2`;
- console production asset losing real transparency;
- Window shell returning to foreground ownership;
- closed travel-gate center collision;
- loss of the four stations or TRAVEL;
- runtime full-console body/frame replay;
- loss of native day/night lighting properties.

## Historical regression policy

D3-D remains immutable historical evidence at version `.70`.

The D3-G workflow runs the D3-D report and requires every historical gameplay/asset invariant to remain true. The only accepted D3-D report differences are the three intentional version-identity checks:

- `versionManifest70`
- `versionCsproj70`
- `versionTargets70`

D3-A/B/C validators remain PASS inside that historical report.

D3-F workflow is frozen to `workflow_dispatch` only because D3-G intentionally removed the forced-position architecture its validator expected.

## D3-G CI provenance

Final successful workflow run: `35287327146`  
Successful job: `105422447116`  
Package/source commit: `cd056a680ba50ee5d03b0f7d200537eb76e7f276`

Workflow:

`.github/workflows/cardcha-alpha28-0696d3g-asset-separation-natural-collision-daylight.yml`

Verified in the successful run:

- historical D3-D gameplay/asset invariants: PASS
- D3-G asset/TMX/collision/daylight validator: PASS
- no-legacy Window overlay guard: PASS
- render-depth contract: PASS
- validator non-mutation guard: PASS
- Release compile: PASS
- D3-G package audit: PASS
- CI evidence generation: PASS
- GitHub prerelease publication: PASS

CI success is **not** Runtime PASS.

## D3-G TEST package

Version:

`0.3.0-alpha.28.0.4.14.4.5.12.71`

Prerelease tag:

`cardcha-0696d3g-test-cd056a68`

Release ID:

`391120631`

Release URL:

`https://github.com/ronvotri/Cardcha-Shardbound/releases/tag/cardcha-0696d3g-test-cd056a68`

Package:

`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.71_0696D3G_AssetSeparationNaturalCollisionDaylightRecovery_TEST.zip`

Package asset ID:

`571374818`

Package size:

`3,630,187 bytes`

Package SHA256:

`05f367c54359223c882b2123cb4529f9eb04dc841e6cb5f099758504018437d8`

Direct package URL:

`https://github.com/ronvotri/Cardcha-Shardbound/releases/download/cardcha-0696d3g-test-cd056a68/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.71_0696D3G_AssetSeparationNaturalCollisionDaylightRecovery_TEST.zip`

## Ron runtime retest checklist

1. Room 1: movement around route board, bench, boarding posts and cargo feels like native collision. No ghost/shadow movement with the Farmer body pinned.
2. Room 2: the Observation Window / upper shell no longer blanket-overlays the Farmer.
3. Room 2: the navigation console no longer blanket-overlays the Farmer.
4. Console: no beige/yellow rectangular matte remains around the machine.
5. Console/radar: radar remains visually alive and still functions as an alternate travel control.
6. Four upgrade stations remain visible, reachable from natural adjacent tiles, and open the correct upgrade menus.
7. `TRAVEL` remains visible/actionable and starts the existing travel flow.
8. The left lamp no longer passes through the interior travel gate.
9. Daytime bridge is clearly brighter/readable than night.
10. Forest gate: solid posts/wood cannot be walked through, while the intended center lane remains passable and the interaction remains reachable.
11. No new absurd-distance interaction or blocked central walking lane appears.

Only Ron's successful in-game retest of this exact package may change D3-G to Runtime PASS.

## Resume instruction

Resume from **0696D3-G package `.71` / CI PASS / Runtime RETest Required**.

Do not restart D2. Do not redo D3-A/B/C/D/E/F. Do not restore forced player-position correction, the legacy beige console base, console `Front2` blanket ownership, or the full `DrawDeckMarkers` replay.

If Ron reports a remaining runtime issue, patch incrementally from D3-G using the screenshot/gameplay observation as authority.
