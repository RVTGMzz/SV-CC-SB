# Cardcha Repository Rules

These rules apply to every Cardcha change in this repository. They are not optional polish notes.

## Mandatory sprite-production guide

Any change that creates, edits, imports, rebuilds, scales, tiles, places, or validates sprites/physical visual assets **MUST read and follow `CARDCHA_SPRITE_PRODUCTION_GUIDE.md` before implementation begins**.

This is a repository-wide rule, not an Airship-only convention.

In particular:

- approved source art is production source-of-truth, not loose reference material;
- do not redraw or rescale approved art for implementation convenience;
- large Stardew props should use faithful multi-tile footprints rather than being shrunk merely to reduce tile count;
- approved room concepts must retain their major composition in production maps;
- sprite integration must be validated for actual visible footprint/render ownership, not only file/GID presence;
- use proven Stardew/xTile/native rendering patterns before inventing a new map-layer convention;
- CI success is technical acceptance only; visual acceptance remains PENDING until Ron approves the real in-game result.

If a sprite task cannot satisfy the guide cleanly, stop and document the conflict instead of silently reinterpreting the source art.

## Mandatory room / map construction guide

Any change that creates, rebuilds, expands, decorates, frames, or visually polishes an interior, hub, expedition room, dungeon, boss arena, or any other playable map **MUST read and follow `CARDCHA_MAP_ROOM_CONSTRUCTION_GUIDE.md` before implementation begins**.

This is also repository-wide, not Airship-only.

In particular:

- build the room/map shell or environmental frame before decorating it;
- indoor rooms need a coherent Stardew-like perimeter: back wall, side boundaries, lower floor edge, and integrated exits/openings;
- expedition/dungeon/boss maps need an equivalent environmental frame using the biome itself, such as foliage, trees, cliffs, rocks, ruins, water edges, roots, snow banks, or other appropriate terrain masses;
- do not start from a giant empty rectangular floor and try to create believability by scattering props afterward;
- negative space must be intentional and framed, not accidental emptiness;
- props must belong to architectural or environmental zones instead of floating independently in open floor;
- visible boundaries and collision must agree;
- before inventing a new map language, study comparable vanilla Stardew maps and established high-quality Stardew mods for structural patterns, without copying third-party art;
- map work should proceed in passes: reference/topology -> shell/frame -> faithful composition -> polish -> in-game acceptance;
- CI success is technical acceptance only; visual map acceptance remains PENDING until Ron approves the real in-game result.

If a map/room task cannot satisfy this guide cleanly, stop and document the conflict instead of hiding a weak shell with extra props or invisible blockers.

## Mandatory character / creature Stardew style guide

Any change that creates, rebuilds, animates, replaces, renders, or visually validates an NPC, companion, mascot, pet, monster, boss, summon, or other character-like world actor **MUST read and follow `CARDCHA_CHARACTER_CREATURE_STYLE_GUIDE.md` before implementation begins**.

Character work must be judged in Stardew context, not on a transparent sprite sheet alone.

Before an actor visual can be called final:

- research at least two relevant vanilla Stardew actor/creature references where practical;
- compare target scale, proportions, silhouette economy, detail density, palette/value range, outline/shading language, feet/ground anchor, frame layout, and animation cadence;
- preserve Cardcha identity while translating the world sprite into Stardew's visual language;
- do not rely on bitmap shrinking to convert oversized/high-detail art into a Stardew actor;
- test the actor beside the Farmer and at least one relevant vanilla NPC/creature in a real map;
- check movement/action frames in context, not only idle art;
- treat a "different game" look as a visual FAIL even when the isolated sprite is attractive;
- keep visual acceptance PENDING until Ron approves the real in-game result.

**Mimi and ChaCha are currently flagged as mandatory STYLE AUDIT / REWORK CANDIDATES.** Their existing art must not be treated as visually final merely because it is already implemented. Follow `handoff/MIMI_CHACHA_STYLE_REWORK_CHECKLIST.md` before rebuilding them.

If character identity and Stardew compatibility conflict, stop and document the tradeoff for review instead of silently replacing the character or accepting a visually disconnected result.

## Rendering depth is a gameplay contract

### NON-NEGOTIABLE RULE: physical world art must never be painted from `Display.RenderedWorld`

`RenderedWorld` runs after Stardew Valley has already drawn the map and world actors. A later `SpriteBatch.Draw(..., layerDepth)` does **not** restore normal Stardew occlusion. Physical art drawn there can cover the Farmer, NPCs, ChaCha, companions, monsters, or other actors.

Therefore the following MUST NOT be implemented as `RenderedWorld` overlays:

- ground terrain, paths, floor patches, puddles, grass mats;
- trees, rocks, bushes, crystals, ruins, pillars, obelisks;
- doors, gates, arches, bridges, railings, walls;
- furniture, tables, chests, crates, shelves, machines, consoles;
- boss bodies, summons, totems, combat actors;
- any static prop intended to exist physically inside the map.

### Correct rendering owner by visual type

1. **Ground / floor / terrain**
   - MUST live in TMX map layers or another pre-world map-owned mechanism.
   - It must render below actors by construction.

2. **Static physical props**
   - Prefer TMX `Buildings` / `Front` layers, Stardew `Object`, `Furniture`, terrain feature, or another native map entity.
   - Tall props that should occlude actors must use Stardew-native layer ordering, not a post-world overlay.

3. **Combat actors**
   - Bosses, summons, totems, and authored enemy sprites MUST render in the actor's own draw slot (`Monster.draw`, NPC draw, or equivalent) so Stardew sorts them with the Farmer/NPC layer.
   - If a vanilla proxy supplies AI/hitbox, suppress only the proxy art and draw the authored art from that same actor draw call.
   - Never use `isInvisible` merely to hide proxy art if it can affect targeting or combat lifecycle.

4. **VFX / non-physical cues**
   - `RenderedWorld` is allowed only for transient non-physical effects such as sparks, pulses, telegraphs, particles, camera-safe markers, or short-lived impact flashes.
   - Such VFX must not resemble a solid object and must not obscure an actor.
   - Large markers must disappear or reduce opacity when overlapping the Farmer/NPC.

5. **HUD / text**
   - Persistent status belongs in HUD space.
   - World text must use actor-safe offsets/lanes and must not sit directly on top of a Farmer/NPC sprite.

## Anchor contract

Visual and gameplay anchors MUST be the same source of truth.

- A gate sprite must be positioned from the exact interaction/warp tile used by gameplay.
- A totem sprite must follow the exact proxy/hitbox position used for damage.
- An extraction marker must resolve from the exact extraction tile.
- Do not maintain a separate hard-coded visual coordinate for the same object.

For bottom-anchored sprites, the default contract is:

`world = (tile.X * 64 + 32, tile.Y * 64 + 64)`

with an origin at the bottom-center of the source sprite, unless the asset explicitly documents a different footprint.

## Scale contract

- Do not enlarge small pixel sprites until they look broken or occupy unrelated tiles.
- Physical sprite footprint must match the gameplay footprint.
- A one-tile prop should not visually occupy three or four tiles unless gameplay collision/interaction also reflects that size.

## Required visual acceptance

CI compile success is NOT visual acceptance.

Every visual/world pass must be checked for:

- Farmer in front of the prop;
- Farmer behind the prop;
- Farmer standing on the same tile / immediately adjacent;
- at least one NPC/companion near the prop;
- controller/action interaction alignment;
- no ground/decor pixels painting over actor feet/body;
- no giant sprite footprint unrelated to collision;
- no duplicate visual (proxy art + authored art).

If screenshots show incorrect occlusion, the pass is **FAIL** even if CI is green.

## Regression policy

A fix for one screenshot must not be implemented as another per-object magic offset if the root cause is rendering ownership/depth. Fix the rendering architecture first.

See `CARDCHA_RENDERING_DEPTH_CONTRACT.md` for the audit checklist and implementation matrix.
