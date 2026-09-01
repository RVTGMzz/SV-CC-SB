# Cardcha alpha28.0.4.12 — Arcane Dock + Airship Bridge Plan

Baseline: alpha28.0.4.11 FINAL PASS on branch `cardcha-alpha28-050-magic-dust-ui-airship-fix`.

## Locked next-step scope
- Keep Forest collision/pathing untouched.
- Re-theme the conflict-safe Forest boarding marker as an Arcane Gate / magical boarding point.
- Use the existing Cardcha-owned `Cardcha_SkyDockInterior` map as the first Arcane Dock implementation so no vanilla map tiles/collision need to be replaced.
- Arcane Dock visual language: magical summoning circle, crystals, runes, purple/blue/gold glow, route console, portal/boarding bay.
- Preserve current Region I unlock, fare, confirmation and flight cutscene behavior.
- Re-theme `Cardcha_AirshipDeck` presentation as the actual Airship Bridge rather than showing a tiny fake Airship model inside a control room.
- Bridge direction: large sky-facing navigation area, magical navigation table/core, route helm, future upgrade interaction points.
- Do not regress alpha28.0.4.11: Magic Dust, approved icon atlas, English UI auto-fit, MiMi Wizard Tower appointment bypass, cleaned airship/animated-only propeller.

## Build strategy
1. Create alpha28.0.4.12 branch from .4.11 final head.
2. Implement gameplay-safe Arcane Dock/Bridge skeleton with existing assets/runtime drawing first.
3. Compile and package test build.
4. Only after gameplay skeleton passes, add/polish bespoke pixel-art assets.
