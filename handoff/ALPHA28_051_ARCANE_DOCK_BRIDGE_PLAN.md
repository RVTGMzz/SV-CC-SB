# Cardcha alpha28.0.4.12 — Arcane Dock + Airship Bridge Handoff

Baseline: alpha28.0.4.11 FINAL PASS on branch `cardcha-alpha28-050-magic-dust-ui-airship-fix`.

Branch: `cardcha-alpha28-051-arcane-dock-airship-bridge`

## Locked scope
- Keep Forest collision/pathing untouched.
- Re-theme the conflict-safe Forest boarding marker as an Arcane Gate / magical boarding point.
- Use the Cardcha-owned `Cardcha_SkyDockInterior` map as the first Arcane Dock implementation so no vanilla map tiles/collision are replaced.
- Arcane Dock visual language: magical summoning circle, crystals, runes, purple/blue/gold glow, route console, violet boarding gate.
- Preserve Region I unlock, fare, confirmation and flight cutscene behavior.
- Re-theme `Cardcha_AirshipDeck` as the actual Airship Bridge rather than showing a tiny fake Airship model inside a control room.
- Bridge direction: large sky-facing navigation area, magical navigation table/core, route helm, future upgrade interaction points.
- Preserve alpha28.0.4.11 regressions guards: Magic Dust, exact approved icon atlas, English UI auto-fit, MiMi Wizard Tower appointment bypass, cleaned airship/animated-only propeller.

## Implemented gameplay flow
`Forest Arcane Gate -> Arcane Dock -> violet boarding gate -> Airship Bridge -> navigation helm -> Region I flight`

Return flow:
`Region I -> return flight -> Airship Bridge -> Arcane Dock -> Forest`

Details:
- Forest Arcane Gate remains runtime overlay only; no Forest collision/path edits.
- Arcane Dock route console is informational and no longer launches the flight directly.
- Arcane Dock boarding bay now warps to `Cardcha_AirshipDeck` as the Airship Bridge.
- Airship Bridge helm owns Region I departure request / fare / confirmation flow.
- Bridge exit returns to Arcane Dock.
- Region I return flight tries Airship Bridge first, then Arcane Dock and Forest as compatibility fallbacks.

## Implemented runtime visuals
- Forest marker: rotating arcane sigils, crystal pylons, violet portal plane, gold/cyan runes.
- Arcane Dock: central summoning seal, magical route console, violet boarding gate, crystal pylons.
- The old miniature-Airship presentation is not drawn in the Arcane Dock anymore.
- Airship Bridge: wide sky-facing window, central arcane navigation table/core, route helm, dormant magical upgrade sockets.
- Dormant sockets visually foreshadow future Magic Dust Airship infrastructure upgrades.

This `.4.12` is intentionally the gameplay-safe skeleton first. Bespoke pixel-art polish can follow after in-game flow testing.

## Build-system correction found while implementing .4.12
`src/Cardcha/Directory.Build.targets` was still hard-coded to alpha28.0.4.11 and executed `tools/alpha28_411_finalize.py` on every build, silently reverting the new version during compile.

Fixed branch-locally:
- target version -> `0.3.0-alpha.28.0.4.12`
- prebuild finalizer -> `tools/alpha28_412_arcane_dock.py`

Do not restore the `.4.11` target on this branch.

## FINAL TEST BUILD STATUS
GitHub Actions run: `33468046526`
Result: **PASS**

Passed gates:
- alpha28.0.4.12 source acceptance
- dotnet compile: 0 errors
- generated source materialization
- alpha28.0.4.11 regression asset/UI/story guards
- package creation
- artifact upload

Package:
`Cardcha_v0.3.0-alpha.28.0.4.12_ArcaneDock_AirshipBridge_TEST.zip`

Package SHA-256:
`61414d2661962967ebbe787a632da152c9b9a5330afca3ae34a3d97fb78de4b1`

Verified inside package:
- manifest version: `0.3.0-alpha.28.0.4.12`
- `assets/card_icons.png` SHA-256: `4d659e9a25b188ca7e5e0654aa1124ae562f28ca414236283fef1523df6700ee`
- `assets/airship_visual.png` SHA-256: `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`
- `Cardcha.dll` SHA-256: `7a24bda852d5e503e554fad01ca074ee82915be88a21abd00773a0a0c32d31ad`
- `assets/airship_deck.tmx` SHA-256: `5d0c0978302d72a2d11c1e33c8af36a1aa20ea1203ada2d5d2b575111b6dc643`
- `assets/sky_dock_interior.tmx` SHA-256: `9e9f166a58d140523fb469050c2b95874755cb78c9051c02b8aec6cdf8b0b947`

## In-game test focus
1. Forest boarding point should visually read as an Arcane Gate and remain walk/path-safe on modded Forest maps.
2. Enter gate -> Arcane Dock.
3. Route console should show info only.
4. Violet boarding gate -> Airship Bridge.
5. Helm -> existing Region I fare/confirmation/departure flow.
6. Region I return -> Airship Bridge.
7. Bridge exit -> Arcane Dock -> Forest.
8. Confirm .4.11 features remain intact.

## Next after gameplay test
If the skeleton flow feels right, replace/polish runtime primitive visuals with bespoke Stardew-compatible magical pixel-art assets while preserving these map coordinates and gameplay contracts.
