# Cardcha Alpha 28 - 0681 Hollow Curator Records You

Branch: `cardcha-alpha28-0681-hollow-curator-records-you`  
Build: `0.3.0-alpha.28.0.4.14.4.5.12.49`

## Purpose

0680 established a 6-9 node branching Forgotten Archive run and recorded five readable tendencies. 0681 makes that observation matter in the Region II boss fight without hard-countering the player's build.

## Curator Records You

At the real Region II Archive Seal, the current runtime record is transferred to Hollow Curator before the boss warp. The record contains risk, precision, pressure, recovery, mirror, nodes reached and the dominant tag. It is runtime-only; save schema remains 19.

Hollow Curator phase 1 remains Observation. At the transition to phase 2 the boss reveals the dominant record. Phases 2/3 bias one extra signature attack into the existing attack pool:

- Risk -> Archive Collapse: two clear danger zones, stronger damage.
- Precision -> Perfect Margin: narrow current + remembered strike with a longer tell.
- Pressure -> Compression Pulse: broad but lower-damage pressure field.
- Recovery -> Restoration Echo: modest Curator heal plus a small danger zone; it does not disable player healing.
- Mirror -> Mirror Catalogue: current, secondary and previous-position echo.
- Neutral -> existing Mirror Echo behavior.

The old adaptation stack remains capped at 3. Record attacks complement rather than replace the normal boss kit.

## Hollow Curator visual auth pass

The old four-frame atlas is replaced by a native 48x64-frame atlas with 18 frames across 9 animation families:

1. idle / hover
2. observe / adaptation
3. risk
4. precision
5. pressure
6. recovery
7. mirror
8. Curator's Truth / phase transition
9. defeat collapse

The approved Curator silhouette is preserved. No sprite enlargement beyond the existing 1.95 world scale was introduced. Boss art still renders at Monster.draw actor depth; physical art never returns to RenderedWorld.

## Debug

- `cardcha_test_region2` - normal 6-9 node run.
- `cardcha_region2_rogue_status` - run node/record status.
- `cardcha_expedition_clear` - clear a combat node quickly.
- `cardcha_test_boss2_record risk`
- `cardcha_test_boss2_record precision`
- `cardcha_test_boss2_record pressure`
- `cardcha_test_boss2_record recovery`
- `cardcha_test_boss2_record mirror`
- `cardcha_test_boss2_record neutral`
- `cardcha_boss_milestone_status` - includes the active Curator record.

## Frozen contracts

- Region II run length remains 6-9 nodes.
- Region II fare remains 250g.
- Boss II remains 2200 HP and rewards Mirror Archive.
- Boss II remains the 40-card Region II milestone.
- Region III/IV gameplay and rewards unchanged.
- Boss III/IV art unchanged.
- MiMi `mimi_walk.png` untouched.
- Save schema 19; 80 source / 76 normal cards.
- Repository rendering-depth contract remains mandatory.

## Acceptance

CI proves static/compile/package only. In-game acceptance should verify: record transfer from a real Region II run, correct phase-2 reveal, signature telegraph fairness, animation readability, actor-depth occlusion and no duplicate proxy art.
