# Cardcha alpha28.0.4.13 — Arcane Dock + Airship Bridge Visual Polish

Baseline: alpha28.0.4.12 PASS on branch `cardcha-alpha28-051-arcane-dock-airship-bridge`.

## Status
FINAL BUILD PASS for source/compile/package. In-game visual review still required.

- Branch: `cardcha-alpha28-052-arcane-dock-bridge-visual-polish`
- Materialized source commit: `0cc12ea`
- GitHub Actions run: `33494112364`
- Artifact ID: `9794987321`
- Build result: 0 errors, 37 pre-existing warnings
- Test package: `Cardcha_v0.3.0-alpha.28.0.4.13_ArcaneDock_BridgeVisualPolish_TEST.zip`
- Test package SHA-256: `a03ed99359cf358c8a5cfed5bdea29d948bdab009eb7ee13611480e59c0c2d8d`

## Scope
- Presentation-only polish for the Arcane Gate, Arcane Dock, and Airship Bridge.
- No changes to Forest collision/pathing.
- No changes to Airship unlock, fare, confirmation, Region I warp flow, or progression.
- No new binary art in this pass. Uses Cardcha-owned maps plus runtime pixel drawing so the build is easy to test and roll back.

## Implemented visual polish
- Forest Arcane Gate: layered portal depth, rune crown, paired crystal pylons, ambient sparkles.
- Arcane Dock: central summoning seal, animated mana lanes, floating route-console altar, deeper violet boarding portal, quieter return rune.
- Airship Bridge: panoramic day/night sky, moving clouds or stars, framed bridge windows, navigation dais, animated mana lane, side consoles, readable upgrade sockets.
- Arcane Dock interior remains free of a miniature Airship model.

## Regression locks verified by CI
- Approved magical-girl card icon atlas unchanged: `4d659e9a25b188ca7e5e0654aa1124ae562f28ca414236283fef1523df6700ee`.
- Cleaned Airship visual / animated-only propellers unchanged: `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- English card-title auto-fit preserved.
- MiMi Wizard Tower appointment bypass preserved.
- Magic Dust naming/localization preserved.
- Forest collision contract remains `CollisionEdits=NONE`.

## In-game test order
1. Verify Arcane Gate interaction still enters Arcane Dock.
2. Verify route console and violet boarding gate.
3. Verify Bridge helm still confirms and departs to Region I.
4. Verify Region I return lands on Bridge, then Dock, then Forest.
5. Review clipping, overlays covering farmer, glow strength, day/night bridge window, and console readability.

## Next build after visual PASS
Move to bespoke Cardcha pixel-art assets/tilesheet for Arcane Dock and Airship Bridge only after the runtime-polish layout is approved in game.
