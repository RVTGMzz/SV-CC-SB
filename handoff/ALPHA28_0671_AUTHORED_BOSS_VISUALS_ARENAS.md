# Alpha28 0671 - Authored Boss Visuals & Arenas

Build: `0.3.0-alpha.28.0.4.14.4.5.12.40`
Branch: `cardcha-alpha28-0671-authored-boss-visuals-arenas`
Status: CI/package and in-game acceptance pending.

## Scope
- Boss II/III/IV use authored PNG sprite sheets instead of procedural rectangle/diamond silhouettes.
- Boss II/III/IV each route to a distinct TMX arena.
- Each arena receives authored world-space decorative tiles.
- ChaCha Boss Form visual evolves Guardian -> Mirror -> Trinity -> Resonance from unlocked boss cards.
- Boss Form duration remains 10 seconds and the current Root Pulse gameplay stays unchanged in 0671.

## Visual assets
- Hollow Curator: 2 frames at 48x64.
- Ignis/Vita/Aether: three 48x48 forms.
- Unified Resonance: 2 frames at 64x64.
- MiMi Resonance Master: 3 frames at 64x64.
- Mirror / Trinity / Resonance Rabbit: 32x32-frame 4-direction sheets.

## Regression guards
- 0670 HP/state/reward logic remains intact.
- Save schema remains 19.
- Boss I / 0669 code remains untouched while acceptance is pending.
- `mimi_walk.png` remains locked.
- Card audit remains 76 active / 80 source.
