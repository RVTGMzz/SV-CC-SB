# Alpha28 0652 — Verdant Guardian visual prototype

Branch: `cardcha-alpha28-0652-verdant-visual-prototype`

Build target: `0.3.0-alpha.28.0.4.14.4.5.12.19`

Status: implementation candidate; in-game visual acceptance pending.

## Scope
- Adds Cardcha-owned 64x64/frame pixel sprite sheets for Verdant Guardian: idle, intro awaken, swipe, root cast, plus core-glow overlay.
- Adds `VerdantGuardianVisualService`, a read-only animation/render layer.
- Existing `VerdantGuardianBossService` remains authoritative for state transitions, cooldowns, damage timing, phases, victory, rewards and save flags.
- The vanilla Green Slime actor remains the gameplay/collision proxy underneath this first visual pass. Custom art is drawn over it; if any visual asset fails to load, the fight safely falls back to the proxy.
- No SaveData schema changes.

## Locked visual contract
- Frame size: 64x64.
- Feet anchor: (32,58).
- Initial world draw scale: 4x.
- Phase 2/3 use only subtle scale/tint/glow increases, not separate redesigned body sheets.
- Animation art never changes combat timing.

## Current implemented clips
- `idle`: 6 frames, looping.
- `intro_awaken`: 10 frames, driven across the existing 1500 ms Intro state.
- `swipe_attack`: 9 frames, driven across the existing 700 ms SwipeTelegraph state.
- `root_cast`: 8 frames, driven across the existing 900 ms RootSpikesTelegraph state.
- Other boss states intentionally fall back to idle in 0652 until their approved sheets are authored.

## Test focus
1. `cardcha_test_boss1` enters the arena.
2. Boss should visibly read as a large ancient tree guardian instead of only a slime proxy.
3. Confirm idle loops without drifting from the proxy collision position.
4. Confirm Intro, Swipe and Root change with their matching state.
5. Confirm hit timing/damage remains identical to 0650.
6. Confirm missing/corrupt visual assets fail soft instead of breaking the fight.
7. Phase 2/3 glow should visibly intensify without changing gameplay.

## Not yet final
- Slime proxy suppression is not claimed complete in this pass.
- Summon, Charge, Vine, Slam, PhaseShift, Hurt and Defeat custom sheets remain future visual work.
- Sprite silhouette/palette/scale need real in-game acceptance before being called final art.
