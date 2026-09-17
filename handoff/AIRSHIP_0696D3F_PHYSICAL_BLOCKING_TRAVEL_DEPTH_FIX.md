# AIRSHIP 0696D3-F PHYSICAL BLOCKING / TRAVEL / DEPTH FIX

Updated: 2026-09-17

Repository: `ronvotri/Cardcha-Shardbound`
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
TEST version: `0.3.0-alpha.28.0.4.14.4.5.12.70`
Status: **RUNTIME RETEST REQUIRED**

## Runtime authority

This checkpoint is driven by Ron's 2026-09-17 in-game screenshots and supersedes D3-E runtime acceptance.

Observed failures in D3-E:

1. The exterior Forest gate allowed the player to stand inside visual posts/arch geometry.
2. Floor 1 / Sky Dock large props allowed visually impossible player overlap.
3. Floor 2 / Airship bridge still behaved like a floating blanket overlay over the player.
4. The four upgrade stations/pedestals were not visibly present.
5. The navigation console still appeared with the rejected yellow/static base because that base was map-native in `Buildings2`, not the ambient radar-background layer already removed by D3-E.
6. There was no obvious visual place to board the airship or trigger travel.

D3-E therefore remains a historical checkpoint only. It is not Runtime PASS.

## D3-F architecture

D3-F intentionally stops replaying the whole `AirshipFoundationService.DrawDeckMarkers` pass before the player.

`AirshipGateDepthPatch` now suppresses the legacy deck-marker pass entirely and owns a narrow pre-Farmer presentation pass containing only:

- observation Window + transparent radar ambient animation,
- the dedicated travel gate / `TRAVEL` pad,
- four explicit upgrade stations.

This removes the broad room-2 overlay ownership that caused props to float over the player.

## Physical no-enter footprints

D3-F installs a local-player physical-footprint guard before rendering. It remembers the last safe Farmer position and restores it if movement enters Cardcha-owned prop geometry.

This is deliberately runtime-local rather than rewriting Forest map collision, preserving compatibility with Forest/map-overhaul mods.

### Airship bridge / room 2

Blocked footprints:

- navigation console lower body: `x=9..15, y=8..10`
- Engine station: `x=3..5, y=8..9`
- Navigation station: `x=18..20, y=8..9`
- Hull station: `x=6..8, y=11`
- Reactor station: `x=15..17, y=11`
- travel-gate side posts: left `x=2..3, y=4..6`, right `x=5..6, y=4..6`

The travel-gate center remains open and actionable.

### Sky Dock / room 1

Blocked footprints:

- route/notice-board wall cluster: `x=2..13, y=4..5`
- waiting bench: `x=2..7, y=9..10`
- boarding-gate side posts: left `x=21..22, y=4..7`, right `x=26..27, y=4..7`
- right cargo/service cluster: `x=22..25, y=10..12`

The boarding center around canonical bay `(23,8)` remains open.

### Forest gate

The Forest map is not edited. D3-F resolves the current dynamic Cardcha gate anchor and blocks only the two visual post zones around it while leaving the center/approach lane usable.

## Navigation console yellow-base correction

D3-E correctly stopped drawing `state.RadarBackground`, but the screenshot proved the yellow/static body was still present because `navigation_console_base.png` is authored into `airship_deck.tmx` layer `Buildings2`.

D3-F resolves that actual source by clearing only the live navigation-console 7x5 map footprint:

- `Buildings2`
- `x=9..15`
- `y=5..9`

The underlying repository TMX remains unchanged. Runtime then draws only the transparent console frame plus radar glow/sweep/pings.

## Upgrade-station recovery

D3-F renders four upgrade stations explicitly at the canonical sockets:

- Engine `(4,8)`
- Navigation `(19,8)`
- Hull `(7,11)`
- Reactor `(16,11)`

The renderer reads the actual persisted upgrade levels. If `airship_upgrade_visuals.png` cannot load, a visible fallback machine/plinth is drawn instead of silently hiding the station.

Each station also gets an `UPGRADE` label for this TEST phase so runtime presence and interaction are unambiguous.

## Travel affordance

Two explicit visual affordances are now rendered:

- Room 1 / Sky Dock bay `(23,8)`: `BOARD AIRSHIP`
- Room 2 / Airship travel gate `(4,5)`: `TRAVEL`

The existing gameplay handlers remain authoritative. Radar/helm remains an alternate travel control by normalizing its interaction footprint to the existing travel-gate handler.

## Source / CI identity

D3-F main source patch commit:
`d3c35cb595ef32f3f9970f747c3bfd4a84fe2a79`

D3-F validator commit:
`e1f3a8f6820536d9038be34fd2233cf86a1b3d94`

D3-F package-audit commit:
`3153d7e796a118ab78c4229f2ec5db539f53fcbd`

D3-F workflow/package source commit:
`76471e8de7160449d882dfc416b15c34d4db61ea`

Final successful workflow run:
`35247550568`

Successful job:
`105291478417`

CI result:

- historical D3-D regression: PASS
- D3-F physical blocking / travel / depth validator: PASS
- no-legacy Window overlay guard: PASS
- render-depth contract: PASS
- Release compile: PASS
- D3-F TEST package audit: PASS
- GitHub prerelease publication: PASS

The old D3-E push workflow was frozen to manual-only after D3-F success so it cannot report fake failures for the superseding architecture.

D3-E workflow-freeze commit:
`97d4dc54a9db07c109f71aa6544e8d2cde942253`

## TEST package

Prerelease tag:
`cardcha-0696d3f-test-76471e8d`

Release ID:
`390886558`

Release URL:
`https://github.com/ronvotri/Cardcha-Shardbound/releases/tag/cardcha-0696d3f-test-76471e8d`

Package:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.70_0696D3F_PhysicalBlockingTravelDepthRecovery_TEST.zip`

Package asset ID:
`570641822`

Package digest:
`sha256:7811763b5a8263f13dc5cb11d9dad6657223cbb7529a0e4c423591ed11f998f4`

Direct package URL:
`https://github.com/ronvotri/Cardcha-Shardbound/releases/download/cardcha-0696d3f-test-76471e8d/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.70_0696D3F_PhysicalBlockingTravelDepthRecovery_TEST.zip`

## Ron runtime retest checklist

1. Forest gate: walk into both side posts. The Farmer must not stand inside the gate art; the center approach must remain usable.
2. Room 1: try to enter the notice-board cluster, waiting bench, boarding-gate posts and right cargo/service cluster. The Farmer must not visually overlap those physical props.
3. Room 1: verify a visible `BOARD AIRSHIP` pad exists at the right-side boarding gate and entering/interacting with that bay reaches the Airship bridge.
4. Room 2: try to enter the big navigation console, four station footprints and travel-gate posts. The Farmer must not stand inside those objects.
5. Room 2 radar: the large yellow/static 7x5 navigation-console base must be gone; the transparent radar/frame/animation must remain readable.
6. Verify all four upgrade stations are visibly present and each opens the intended upgrade menu from a natural adjacent tile.
7. Verify the dedicated `TRAVEL` pad at the left travel gate is obvious and starts the existing travel flow. Radar must also remain a valid alternate travel control.
8. Verify the center walking spine and bottom doorway remain traversable. Blocking must not feel excessively large.
9. Only Ron's successful in-game retest may change D3-F to Runtime PASS.

## Resume instruction

Resume from D3-F, not D3-E.

Do not restart D2. Do not redo D3-A/B/C/D. Do not restore the D3-E blanket `DrawDeckMarkers` replay. Do not restore the map-native yellow/static navigation-console base.

If Ron reports a remaining issue, patch incrementally from D3-F and keep the exact screenshot/runtime behavior as authority.
