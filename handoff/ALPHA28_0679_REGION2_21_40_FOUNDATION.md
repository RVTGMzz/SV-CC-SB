# Cardcha Alpha 28 - 0679 Region II 21-40 Foundation

Branch: `cardcha-alpha28-0679-region2-21-40-foundation`  
Build: `0.3.0-alpha.28.0.4.14.4.5.12.47`

## Corrected progression architecture

Boss II/III/IV are the bosses of Region II/III/IV respectively. They are not one shared gameplay destination.
0679 implements the missing Region II progression band:

- Boss I real clear unlocks Region II.
- 21-39 cards: Airship route console offers Region II • Forgotten Archive as the active progression biome.
- Region II has 3 combat waves and extraction.
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

1. `cardcha_test_region2` - normal Region II 3-wave run regardless of real unlocks.
2. `cardcha_expedition_clear` - clear current wave quickly.
3. Verify south extraction banks 34 Scrap + 1 Shiny on full clear.
4. `cardcha_test_region2_bossgate` - Region II Boss Approach test.
5. Walk north to the Archive Seal and interact. In real progression it requires Boss I clear + 40 cards. Debug approach bypasses only the Region II entry, not persistent save progression.
6. `cardcha_test_boss2` remains available for direct boss visual testing.

## Frozen contracts

Save schema 19; 80 source / 76 normal cards; Boss II 2200 HP; Region III/IV gameplay/rewards; Boss III/IV milestone logic; MiMi locked art; Airship visual/decor; rendering-depth repository contract.

In-game screenshot acceptance remains pending.
