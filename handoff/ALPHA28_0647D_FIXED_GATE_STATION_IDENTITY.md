# Cardcha alpha28 0647D Fixed Gate + Station Identity

## Branch
`cardcha-alpha28-0647d-fixed-gate-station-identity`

## Build
`0.3.0-alpha.28.0.4.14.4.5.12.4`

Package:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.4_FixedGateStationIdentity_TEST.zip`

Package SHA-256:
`8f80946661ba0cc6b85c0aa0ac1a972121529e65282ee2f2ff1556ed19cfe382`

## User-reported regressions addressed
1. Forest Arcane Gate visibly changed/moved position while approaching.
2. Sky Dock interior was visually easy to mistake for MiMi's attic/home.
3. Airship-owned rooms had too much domestic furniture language after the 0647 vanilla-shell pass.

## Forest gate ownership fix
Root cause was duplicate placement authority:
- `AirshipFoundationService.ResolveSkyDockTile()` performed a runtime safe-tile search.
- `AirshipGateRelocationPatch` then Harmony-postprocessed every resolved tile with another flood-fill/reachable-anchor search.

0647D removes the second runtime placement brain entirely. `AirshipGateRelocationPatch` is now an inert regression marker and installs no runtime hook.

`ResolveSkyDockTile()` is deterministic relative to the Forest Farm warp:
- X = `farmWarp.X - 23`
- Y = `farmWarp.Y + 10`
- clamped only to map bounds

The gate no longer uses transient farmer/NPC/object occupancy or flood-fill to choose its visual tile.

Canonical interaction distance is restored to 160px.
`CollisionEdits=NONE` remains locked.

`cardcha_test_gate` no longer clears/re-rolls `CachedSkyDockTile` immediately before warping the farmer.

## Route contract
Route remains intentionally:
`Forest Arcane Gate -> Cardcha_SkyDockInterior -> Cardcha_AirshipDeck`

The reported apparent warp to MiMi's house was visual confusion, not a location-ID routing bug. `AirshipFoundationService` has no `Cardcha_MiMiAttic` route reference.

## Sky Dock / Airship identity pass
Kept the collision-safe 0647 vanilla TMX shell and the valid 0647C CSV files.

Removed domestic/living-room furniture cues from Sky Dock:
- couch
- dresser/storage-home arrangement
- bookcase
- home rugs
- living-room lamps
- plant/decor arrangement

Sky Dock now keeps a clear central transit lane and only sparse instrument tables/windows, while runtime wall details add:
- left route/service panel
- right boarding/gantry panel
- central dock beacon
- fixed bottom doorway threshold

Airship Deck now emphasizes bridge identity with:
- left/right wall instrument panels
- central helm
- four existing upgrade stations
- ChaCha pedestal accent
- no couch/home arrangement

No room-sized custom backdrop was reintroduced.

## Regressions preserved
- 0647C TMX CSV parser fix remains valid:
  - Airship: 336/336 UInt32 tokens per layer
  - Sky Dock: 540/540 UInt32 tokens per layer
  - zero empty tokens
  - zero trailing commas
- 0647B MiMi portrait runtime fix remains intact.
- only `assets/mimi_portraits.png` is on disk.
- MiMi home/TV/late movement anchors and diagnostics remain intact.
- Save schema 19.
- Boss Form 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- locked Airship exterior SHA256 unchanged:
  `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`
- Airship upgrade costs/levels/route progression unchanged.
- deferred Airship gameplay bonuses remain disabled.

## Verified CI
Workflow run: `33962944082` SUCCESS
Job: `101297906920` SUCCESS
Materialization commit: `2f37ebe7abb2fad9298c55149a464291fa00e599`
Artifact ID: `9968514179`
Outer artifact digest:
`sha256:c77424cf2a6941be2c7e6731f2d202ff9c530d2a295e186ecf58bba877dbff73`

Independent artifact verification:
- manifest version `.5.12.4`
- DLL present, 760832 bytes
- Airship/Sky Dock TMX token counts valid
- only `mimi_portraits.png` exists for MiMi portrait assets
- compiled DLL contains canonical portrait path and no obsolete portrait paths
- exact inner TEST SHA256 matches `8f809466...fe382`

## Acceptance test
1. Fully replace old Cardcha mod folder and restart SMAPI.
2. Run `cardcha_test_gate`.
3. Walk around/away/toward the gate several times. The gate world tile must remain fixed.
4. Use the gate. It should enter `Cardcha_SkyDockInterior`.
5. Confirm the station reads as a transit/workshop bay, not MiMi's attic.
6. Walk into the boarding bay zone to reach `Cardcha_AirshipDeck`.
7. Confirm the deck reads as a bridge/control room and the four upgrade stations remain available.
