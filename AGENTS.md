# Cardcha Repository Rules

These rules apply to every Cardcha change in this repository. They are not optional polish notes.

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
