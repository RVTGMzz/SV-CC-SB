# Cardcha alpha28.0.4.13 — Arcane Dock + Airship Bridge Visual Polish

Baseline: alpha28.0.4.12 PASS on branch `cardcha-alpha28-051-arcane-dock-airship-bridge`.

## Scope
- Presentation-only polish for the Arcane Gate, Arcane Dock, and Airship Bridge.
- No changes to Forest collision/pathing.
- No changes to Airship unlock, fare, confirmation, Region I warp flow, or progression.
- No new binary art in this pass. Use Cardcha-owned maps plus runtime pixel drawing so the build is easy to test and roll back.

## Visual targets
- Forest Arcane Gate: layered portal depth, rune crown, paired crystal pylons, ambient sparkles.
- Arcane Dock: central summoning seal, animated mana lanes, floating route-console altar, deeper violet boarding portal, quieter return rune.
- Airship Bridge: panoramic day/night sky, moving clouds or stars, framed bridge windows, navigation dais, animated mana lane, side consoles, readable upgrade sockets.
- Keep the interior free of a miniature Airship model.

## Regression locks
- Keep approved magical-girl card icon atlas unchanged.
- Keep cleaned Airship visual / animated-only propellers unchanged.
- Keep English card-title auto-fit.
- Keep MiMi Wizard Tower appointment bypass.
- Keep Magic Dust naming/localization.

## Test order
1. Compile and package alpha28.0.4.13.
2. Verify Arcane Gate interaction still enters Arcane Dock.
3. Verify route console and violet boarding gate.
4. Verify Bridge helm still confirms and departs to Region I.
5. Verify Region I return lands on Bridge, then Dock, then Forest.
6. Visual review for clipping, overlays covering farmer, and excessive glow.
