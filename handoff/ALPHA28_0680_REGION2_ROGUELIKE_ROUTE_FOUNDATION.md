# Cardcha Alpha 28 - 0680 Region II Roguelike Route Foundation

Branch: `cardcha-alpha28-0680-region2-roguelike-route-foundation`  
Build: `0.3.0-alpha.28.0.4.14.4.5.12.48`

## Locked design correction

Region II run length is now **6-9 nodes**, intentionally similar to Region I's overall run length. This does NOT mean copying Region I room logic. Region II keeps the Forgotten Archive identity: branching choices, observation, recording, reflection and optional risk before Hollow Curator.

The earlier user example of 2-3 maps / 2-3 waves remains illustrative only, not a hard requirement.

## 0680 runtime

A dedicated `Region2RoguelikeRunService` now owns Region II runtime after the existing Airship/permission layer lands the player in the Forgotten Archive. Region III/IV remain on `RegionExpeditionService`.

- Run target: deterministic 6-9 nodes.
- Node types: Combat, Ambush, Elite, Mirror Choice, Archive Event, Cache, Restoration, Cursed Archive, Boss Gate, Final Cache.
- Route choices are generated between nodes; the same fixed 3-wave sequence is gone for Region II.
- Boss Gate may be offered from node 6 onward when Boss I is really clear and 40 cards are owned.
- Choosing to go deeper keeps offering higher-risk alternatives until the target depth.
- If under 40 cards, the run ends in a deep cache/extraction instead of Boss II.
- Checkpoints at nodes 3 and 6 bank route rewards.
- Early emergency extraction loses only currently unbanked rewards; checkpointed rewards remain safe.
- Entering Hollow Curator banks remaining Region II route rewards before the arena warp.

## Curator observation foundation

0680 records a small transparent runtime profile for the current run:

- risk route choices;
- clean combat clears;
- heavy damage / pressure clears;
- restoration choices;
- mirror interactions.

This is not yet wired into Hollow Curator attacks. It is the data foundation for the next encounter-auth pass. The current dominant record is exposed in `cardcha_region2_rogue_status` and at the Boss Gate.

## Rendering contract

No new physical prop is drawn from `RenderedWorld`. Region II enemies continue using authored 32px sprites through the existing `Monster.draw` proxy suppression path. Static physical art remains TMX-owned.

## Test

1. `cardcha_test_region2` starts a normal 6-9 node test run without mutating progression.
2. Use `cardcha_expedition_clear` on combat/ambush/elite/cursed nodes.
3. Verify route choices vary and non-combat nodes do not require fake enemies.
4. Verify node 3/6 checkpoint banking.
5. Verify early extraction loses unbanked rewards only.
6. `cardcha_test_region2_bossgate` starts directly at a test-ready node 6 Archive Seal; save progression remains unchanged.
7. `cardcha_region2_rogue_status` shows run depth, route type, rewards and Curator record.
8. Real 40-card progression must still require Boss I before Hollow Curator.

## Frozen contracts

Save schema 19; 80 source / 76 normal cards; Region II Airship fare 250g; Boss II 2200 HP; Region III/IV gameplay; MiMi locked art; 0678 Boss II-IV actor-depth art; Airship accepted assets; repository rendering-depth contract.

In-game acceptance remains pending. 0680 is the roguelike route foundation, not the final Hollow Curator behavior/animation pass.
