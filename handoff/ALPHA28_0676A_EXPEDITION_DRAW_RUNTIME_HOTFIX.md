# Alpha28 0676A - Expedition Draw Runtime Hotfix

Build: `0.3.0-alpha.28.0.4.14.4.5.12.45.1`  
Branch: `cardcha-alpha28-0676a-expedition-draw-runtime-hotfix`
Status: runtime launch hotfix for the 0675/0676 Region Expedition proxy draw patch; in-game acceptance pending.

## Confirmed regression
0676 could fail during `GameLoop.GameLaunched` with Harmony:
`You can only patch implemented methods/constructors. Patch the declared method Monster::draw(SpriteBatch) instead.`

Root cause: `RegionExpeditionProxyDrawPatch.Apply()` resolved `draw(SpriteBatch)` through `GreenSlime`, `Bat`, and `Bug`. Those expedition proxy classes inherit the implementation from `Monster`, so Harmony rejected the inherited MethodInfo when it was presented as a subclass patch target.

## 0676A fix
- Patch `AccessTools.DeclaredMethod(typeof(Monster), "draw", new[] { typeof(SpriteBatch) })` exactly once.
- Prefix still suppresses vanilla rendering only for monsters carrying `RegionExpeditionService.EnemyMarkerKey`.
- AI, hitbox, damage, targetability, death and drops remain owned by the real monster proxy.
- No `isInvisible` workaround is introduced.

## Frozen 0676 contract
- Region III/IV authored enemy atlases remain unchanged.
- Region III/IV terrain/decor/maps remain unchanged.
- Region III remains 47 Scrap + 3 Shiny; Region IV remains 69 Scrap + 6 Shiny.
- Fares remain 500g / 1000g.
- Boss milestones remain 40 / 60 / 80 cards.
- Save schema remains 19.
- MiMi, Airship, Boss I-IV, Region I and locked assets are unchanged.

## Acceptance
1. Launch game with only the 0676A package replacing the previous Cardcha folder.
2. Confirm Cardcha no longer throws in `GameLoop.GameLaunched`.
3. Enter `cardcha_test_region3` and verify authored enemies render while vanilla Bat/Bug/Slime art stays hidden.
4. Verify those enemies still move, take damage and die.
5. Repeat with `cardcha_test_region4`.
