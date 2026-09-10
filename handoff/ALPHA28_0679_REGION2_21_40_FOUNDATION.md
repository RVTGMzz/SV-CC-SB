# Cardcha Alpha 28 - 0679 Region II 21-40 Foundation

Branch: `cardcha-alpha28-0679-region2-21-40-foundation`  
Build: `0.3.0-alpha.28.0.4.14.4.5.12.47`

## Corrected progression architecture

Boss II/III/IV are the bosses of Region II/III/IV respectively. They are not one shared gameplay destination.
0679 implements the missing Region II progression band:

- Boss I real clear unlocks Region II.
- 21-39 cards: Airship route console offers Region II • Forgotten Archive as the active progression biome.
- Region II currently has 3 combat waves and extraction.
- Region II fare uses the existing 250g fare constant.
- At 40 cards, the Airship lands in Region II Boss Approach instead of teleporting directly to Hollow Curator.
- The physical north Archive Seal is the Boss II entrance.
- Boss II arena remains a separate arena location, but it is entered from Region II, so Hollow Curator is now the Region II boss.

## Region II identity

Forgotten Archive is an outdoor fantasy archive ruin: parchment, ink, mirror fragments, broken shelves, archive stone and a north seal.
All physical terrain/decor is authored into TMX layers. No Region II physical prop is painted from RenderedWorld.

Enemies use vanilla Monster proxies only for AI/hitbox/combat; authored 32px Cardcha sprites are injected at Monster.draw:
- Ink Moth
- Paper Scarab
- Dust Slime
- Archive Warden (wave 3 elite)

## Rewards

Region II full clear: 34 Scrap + 1 Shiny (7/11/16 Scrap; Shiny only on wave 3).
Region III and IV reward contracts remain unchanged.

## Test

1. `cardcha_test_region2` - normal Region II 3-wave foundation run regardless of real unlocks.
2. `cardcha_expedition_clear` - clear current wave quickly.
3. Verify south extraction banks 34 Scrap + 1 Shiny on full clear.
4. `cardcha_test_region2_bossgate` - Region II Boss Approach test.
5. Walk north to the Archive Seal and interact. In real progression it requires Boss I clear + 40 cards. Debug approach is runtime-only and must not mutate persistent progression.
6. `cardcha_test_boss2` remains available for direct boss visual testing.

## Important: 0679 is a foundation, not the final Region II loop

The current single-map / three-wave structure should **not** be treated as the locked final design.

The next Region II direction is documented in:

`handoff/REGION2_ROGUELIKE_DESIGN_DIRECTION.md`

Key intent:

- Region II should become a replayable branching roguelike route rather than a linear mini-campaign.
- User examples such as “2-3 maps / 2-3 waves” are discussion examples, not hard requirements.
- Future work should use design judgment and may challenge the example if a better structure serves replayability.
- Candidate runs should mix combat, elites, events, rewards, Mirror choices, curses, shortcuts and Boss Gate decisions rather than repeating fixed waves.
- Forgotten Archive’s signature identity is observation / recording / reflection.
- Hollow Curator should be foreshadowed during the run and eventually react to a small set of readable player tendencies recorded during that run.
- More boss animation frames are not sufficient by themselves; animation should support actual states, telegraphs, recording, reflection, phase transitions and defeat presentation.

The acceptance question for the future roguelike pass is whether a second Region II run feels meaningfully different enough to make the player curious about a third.

## Frozen contracts

Save schema 19; 80 source / 76 normal cards; Boss II 2200 HP; Region III/IV gameplay/rewards; Boss III/IV milestone logic; MiMi locked art; Airship visual/decor; rendering-depth repository contract.

In-game screenshot acceptance remains pending.
