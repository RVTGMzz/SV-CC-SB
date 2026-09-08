# Alpha28 0664 - Verdant Arena / Intro / Camera / Sound Polish

Build: `0.3.0-alpha.28.0.4.14.4.5.12.31`
Branch: `cardcha-alpha28-0664-verdant-arena-cinematic-polish`
Status: implementation candidate, in-game acceptance pending. 0660-0663 acceptance remains pending because the user continued before testing.

## Arena polish
- No collision or room geometry changes. The existing 28x20 TMX is preserved; only its CardchaRegionVersion property is stamped to this build.
- Adds a subtle Cardcha-owned Verdant seal beneath the boss, four rooted obelisks outside the main fight lane, ambient green motes and a readable retreat glyph at the existing retreat tile.
- These are rendering-only assets and do not alter hitboxes, summon tiles or telegraph geometry.

## Intro polish
- Keeps the existing 1500 ms authoritative Intro state exactly unchanged.
- Adds cinematic letterbox bars, a centered VERDANT GUARDIAN title and bilingual subtitle, with fade-in/out inside that same 1500 ms window.
- Phase transitions receive a short centered resonance label without changing phase timing.

## Camera polish
- Presentation-only camera shake on intro footfall/core wake, phase shift, charge impact, root eruption, area slam and defeat.
- Camera offset is explicitly restored before each new tick and on warp/title cleanup so shake cannot accumulate into camera drift.
- Camera shake never writes boss/player positions or combat state.

## Sound polish
- Uses only vanilla cues already used safely by Cardcha/Stardew (`thudStep`, `leafrustle`, `discoverMineral`, `yoba`).
- Layered cues are keyed to authoritative states/elapsed time; no external audio dependency is added.

## Debug
- `cardcha_boss1_polish_status` reports arena state, active camera offset, shake count, sound cue count and last impact reason.
- Enter through `cardcha_test_boss1` to replay the normal intro automatically.

## Locked systems preserved
- Boss I HP 1300 and all attack damage/cooldowns remain unchanged.
- Boss Intro remains 1500 ms; defeat remains 2200 ms.
- 0660 Colossus visuals and heavy anchor unchanged.
- 0661 Verdant Core Boss Card unchanged.
- 0662 Guardian Rabbit stays exactly 10 sec and Boss Energy stays x1/3.
- 0663 Briarling/Leaf Wisp custom summon runtime and cap 4 unchanged.
- Save schema 19, 20/40/60/80 milestones, 76 active normal-card audit / 80 stored base IDs, MiMi stair/profile/CC work, Hunt Run, Airship route/upgrades and controller mapping unchanged.
