# Cardcha alpha28 — 0676B Region Layering + Extraction + Gate Hotfix

## Source of truth
- Branch: `cardcha-alpha28-0676b-region-layering-extraction-hotfix`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.45.2`
- Base: accepted only as code baseline from 0676A; 0676/0676A visual acceptance is **FAILED/PENDING** after in-game screenshots.

## Why 0676B exists
In-game screenshots exposed three concrete presentation regressions:
1. Region III/IV paths formed giant yellow rectangles/crosses/ziczags and read like test arenas.
2. Terrain/decor/enemy overlays rendered from `RenderedWorld` could paint over Farmer/NPC sprites, including art intended to sit under feet.
3. The Forest Airship gate art was visibly offset from its gameplay interaction/route anchor.

CI success is not visual acceptance. User screenshots remain the acceptance authority.

## 0676B fixes
### Region III/IV map cleanup
- Rebuild `region3_mirrorwild.tmx` as sparse organic trails + open combat clearings.
- Rebuild `region4_resonance_verge.tmx` as compact three-spoke resonance trails + open combat clearings.
- Remove giant perimeter rectangles and X/ziczag compositions.
- Ground identity must live in TMX/map layers, not post-world overlays.

### World-depth architecture
- Expedition proxy AI/hitbox remains vanilla Monster underneath.
- Patch the declared `Monster.draw(SpriteBatch)` once.
- Marked expedition enemies render their authored Cardcha sprite at the Monster's normal draw slot, then suppress only the vanilla proxy sprite.
- Legacy post-world `DrawEnemyIdentity` is suppressed to prevent double/late rendering.
- Legacy post-world terrain/decor `DrawRegionIdentity` is suppressed.
- The only late world cue allowed is a small extraction bracket marker, and it hides whenever Farmer/NPC is close enough to overlap it.

### Airship gate anchor
- Override `AirshipFoundationService.DrawSkyDock(SpriteBatch, Point)`.
- Pin the authored gate's bottom-center to the exact dock interaction tile center-bottom.
- Remove old `Y + 70`, origin offset and ~1.48x scaling drift.
- Farmer depth ordering remains controlled through `Farmer.draw` prefix/postfix.

## Frozen gameplay/progression
No balance changes in 0676B:
- save schema 19
- 80 source cards / 76 active normal cards
- Region III expedition: 3 waves, 47 Scrap + 3 Shiny full clear, fare 500g
- Region IV expedition: 3 waves, 69 Scrap + 6 Shiny full clear, fare 1000g
- milestone bosses remain 40 / 60 / 80 cards
- Region I Hunt Run unchanged
- Boss I frozen balance unchanged
- `mimi_walk.png` untouched

## Permanent visual rules
1. Static ground/decor MUST be authored into TMX/map layers. Never paint physical floor scenery in `RenderedWorld` after actors.
2. Dynamic actor art MUST render at the actor's real world-depth slot.
3. Late world markers must disappear before they can cover Farmer/NPC/ChaCha.
4. Visual and interaction anchors must share one authoritative tile/coordinate source.
5. Never solve readability by merely enlarging sprites or props.
6. Do not call a visual pass accepted from CI alone. Require in-game screenshot acceptance.

## Consolidated acceptance test
Use one package and check:
1. `cardcha_test_region3`: Farmer can stand/walk over trail areas without ground/decor covering the sprite; map no longer reads as a giant yellow frame/X.
2. `cardcha_test_region4`: same checks; region must remain visually distinct from Region III.
3. Clear all 3 waves (`cardcha_expedition_clear` may accelerate testing), then confirm south extraction flow returns to Airship and banks rewards.
4. `cardcha_test_gate`: authored gate is centered on the route/interaction anchor and no longer visibly shifted.

Do not branch into new visual work until these screenshots are reviewed.