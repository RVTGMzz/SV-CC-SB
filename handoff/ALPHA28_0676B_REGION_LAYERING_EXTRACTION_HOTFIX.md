# Cardcha alpha28 — 0676B Region Layering + Extraction + World-Depth Safety Hotfix

## Source of truth
- Branch: `cardcha-alpha28-0676b-region-layering-extraction-hotfix`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.45.2`
- Base: accepted only as code baseline from 0676A; 0676/0676A visual acceptance is **FAILED/PENDING** after in-game screenshots.

## Why 0676B exists
In-game screenshots exposed a repeated rendering-ownership regression, not isolated offsets:
1. Region III/IV paths formed giant yellow rectangles/crosses/ziczags and read like test arenas.
2. Terrain/decor/enemy overlays rendered from `RenderedWorld` could paint over Farmer/NPC sprites, including art intended to sit under feet.
3. The Forest Airship gate art was visibly offset from its gameplay interaction/route anchor.
4. Region I's physical Boss gate/wall overlay visibly covered the Farmer.
5. Audit then confirmed the same architectural debt in Airship fake furniture/decor and several boss/summon/Totem authored-body renderers.

CI success is not visual acceptance. User screenshots remain the acceptance authority.

## Repository-wide non-negotiable depth contract
The rule is now permanent and machine-enforced, not a note remembered by one chat session:

- `AGENTS.md` — repository rule read by future development agents.
- `CARDCHA_RENDERING_DEPTH_CONTRACT.md` — visual ownership matrix + acceptance checklist.
- `render_depth_audit.json` — machine-readable audit of every current `RenderedWorld` subscriber.
- `tools/validate_render_depth_contract.py` — CI validator; a new `RenderedWorld` subscriber must be audited before the build may compile.

Core rule: **no physical Cardcha world object may be painted from `Display.RenderedWorld`.**

- ground/path/terrain => TMX/map-owned layer;
- furniture/rocks/trees/gates/architecture => TMX, `Furniture`, `Object`, terrain feature, or native world entity;
- boss/summon/Totem/enemy body => its actor draw slot;
- `RenderedWorld` => transient VFX/non-physical cues only.

A `layerDepth` number inside `RenderedWorld` does not restore Stardew's already-completed actor/world sort.

## 0676B immediate safety fixes
### Region III/IV
- Rebuilt Region III/IV map composition away from giant perimeter rectangles/X/ziczag patterns.
- Expedition proxy AI/hitbox remains vanilla Monster underneath.
- Marked expedition enemies render from the declared `Monster.draw(SpriteBatch)` slot.
- Legacy post-world enemy body and terrain/decor renderers are suppressed.
- Extraction cue is non-physical and hides when an actor approaches.

### Forest Airship gate
- Legacy post-world `DrawSkyDock` gate is suppressed entirely.
- Gate is injected around the local Farmer draw using the service's authoritative interaction tile and before/after-player decision.
- No duplicate post-world gate is permitted.

### Confirmed unsafe static overlays suppressed until native migration
0676B disables these physical post-world renderers rather than shipping another object that can cover actors:
- `AirshipFoundationService.DrawRegion1Details` — includes the screenshot-failing Region I gate/wall/path/pad.
- `Region1StardewDecorRenderer.Draw` — trees/rocks/decor.
- `AirshipInteriorStardewRenderer.DrawDeckStardewDecor`.
- `AirshipInteriorStardewRenderer.DrawDockStardewDecor`.
- `AirshipInteriorStardewRenderer.DrawUpgradeStations` physical machine bodies.

These visuals may return only after being rebuilt as TMX/native Furniture/Object/world entities.

## Remaining audited combat-actor depth debt
Do **not** resume feature expansion until the next depth migration handles these authored physical bodies:
- Verdant Guardian boss body;
- Briarling / Leaf Wisp bodies;
- Verdant Totem/obelisk bodies;
- Boss II / III / IV authored actor bodies.

Their gameplay remains intact. The next depth pass must move body rendering to the actor's own draw slot while leaving telegraphs/particles as VFX.

## Additional runtime guard
`VerdantGuardianProxyDrawPatch` now resolves the method declared by `Monster`, not inherited `GreenSlime.draw`, matching the runtime-safe pattern learned from the 0676A Harmony crash.

## Frozen gameplay/progression
No balance changes in 0676B:
- save schema 19
- 80 source cards / 76 active normal cards
- Region III expedition: 3 waves, 47 Scrap + 3 Shiny full clear, fare 500g
- Region IV expedition: 3 waves, 69 Scrap + 6 Shiny full clear, fare 1000g
- milestone bosses remain 40 / 60 / 80 cards
- Region I Hunt Run gameplay unchanged
- Boss I frozen balance unchanged
- `mimi_walk.png` untouched

## Permanent visual acceptance rules
For every physical Cardcha visual, test:
1. Farmer south/in front.
2. Farmer north/behind.
3. Farmer same/adjacent interaction tile.
4. ChaCha/NPC/companion nearby.
5. visual footprint matches collision/action footprint.
6. no ground/decor pixel paints over feet/body.
7. no solid prop remains permanently above every actor.
8. no vanilla proxy + authored sprite duplicate.

A screenshot failure means visual acceptance = **FAIL**, even when CI is green.

## Consolidated 0676B acceptance test
Use one package and check:
1. Region I / Boss approach: the old black gate/wall overlay must no longer swallow Farmer.
2. `cardcha_test_gate`: Forest Airship gate must sort naturally around Farmer and remain aligned to interaction.
3. `cardcha_test_airship`: no fake post-world furniture/machine body may paint over Farmer/NPC.
4. `cardcha_test_region3`: no post-world terrain/decor covers actors; map no longer reads as giant yellow frame/X.
5. `cardcha_test_region4`: same, while remaining distinct from Region III.
6. Clear all 3 waves (`cardcha_expedition_clear` may accelerate testing), then confirm extraction/return still works.

Do not call 0676B visually accepted until screenshots confirm it.
