# Cardcha Map & Room Construction Guide

This document is the permanent source-of-truth for any Cardcha work that creates, rebuilds, expands, decorates, frames, or visually polishes rooms, interiors, dungeons, expedition maps, boss arenas, hubs, or other playable map spaces.

**Mandatory rule:** every future room/map visual pass MUST read and follow this guide before implementation begins.

This guide complements `CARDCHA_SPRITE_PRODUCTION_GUIDE.md`. The sprite guide governs the fidelity of individual assets. This guide governs how those assets become a believable Stardew Valley space.

---

# Core principle

**A playable map must read as a complete place, not as a flat floor with props dropped on top.**

The map needs a coherent visual boundary, environmental framing, authored negative space, and a composition that feels native to Stardew Valley.

The surrounding frame is part of the room design. It is not optional decoration added after furniture is placed.

---

# 1. Build the room/map shell before decorating

Before placing hero props or small decor, establish the architectural or environmental shell.

For an indoor room, define first:

- back wall / upper wall mass;
- left and right visual boundaries;
- floor edge / lower boundary;
- entrances, exits, doors and openings;
- wall trims, beams, pillars or structural transitions where appropriate;
- intentional black/out-of-map void only where Stardew itself would plausibly show it.

For an outdoor, expedition, dungeon, cave or boss map, the same principle applies, but the frame may be environmental instead of architectural.

Examples of environmental framing:

- forest: tree canopy, dense shrubs, roots, leaves, cliff vegetation;
- cave: rock walls, ledges, stalagmites, shadowed stone masses;
- ruins: broken masonry, roots, collapsed walls, rubble;
- mountain: cliffs, boulders, ledges, snow banks;
- swamp: reeds, dark water edges, mud banks, mangrove/root walls;
- magical zone: terrain mass first, restrained magical accents second;
- boss arena: environmental boundary that communicates arena limits without looking like an artificial rectangle.

Do not begin with a giant empty floor and try to fix the space afterward by sprinkling props into it.

---

# 2. Every playable space needs a readable frame

## Indoor framing rule

A room should visually read as a contained Stardew interior.

The player should be able to understand at a glance:

- where the room begins and ends;
- which surface is floor;
- which areas are walls or non-playable space;
- where exits/openings are;
- how the room is structurally held together.

Avoid the failure mode where a large rectangular floor floats in a black void with props standing on it like stickers.

A compact, deliberate perimeter usually reads more naturally than a huge exposed floor rectangle.

## Outdoor / dungeon / boss framing rule

Outdoor and combat maps do not need a wooden wall frame, but they still need a **visual enclosure language**.

Use the environment itself to form the frame:

- trees and foliage;
- cliff faces;
- stone walls;
- water edges;
- roots;
- ruins;
- snow banks;
- canyon walls;
- corrupted/magical terrain masses when appropriate.

The frame may be irregular and organic. It should not look like a perfect rectangle unless the fiction actually calls for one.

The goal is the same as indoors: the playable area must feel authored and grounded rather than floating in empty space.

---

# 3. Research before designing a new map language

Before inventing a new room shell, dungeon border, boss-arena frame, or environmental composition, research how **Stardew Valley itself** and established high-quality Stardew mods solve a similar space.

At minimum, check:

- one or more comparable vanilla Stardew interiors/maps;
- one or more established Stardew mods with a similar environment or room type when available;
- how their playable boundary is communicated;
- wall/floor proportions;
- edge density;
- doorway/warp presentation;
- how much open space they leave for movement;
- how collision and visible boundary agree;
- where foreground occlusion is used;
- how environmental objects transition into map edges.

Research is for **structural reference**, not for copying another creator's proprietary art.

Do not invent a repository-specific visual convention when a proven Stardew-native pattern already exists unless there is a documented reason.

---

# 4. Composition order is mandatory

Build maps in this order:

1. **Gameplay topology**
   - entrances/exits;
   - warps;
   - combat/traversal lanes;
   - interaction anchors;
   - boss footprint / encounter space;
   - controller-friendly access.

2. **Map shell / environmental frame**
   - walls, cliffs, trees, rock masses, water edges, room perimeter;
   - architectural/environmental structure.

3. **Hero visual zones**
   - gate, console, shrine, boss focal area, major desk, major window, landmark, altar, bridge, etc.

4. **Secondary functional props**
   - benches, shelves, carts, tables, signs, crates, lamps, machines.

5. **Ground/support detail**
   - rugs, plants, mushrooms, small stones, papers, roots, floor wear, decals.

6. **Foreground/occlusion polish**
   - `Front` / proven foreground ownership only where it improves depth and does not hide gameplay.

Never reverse this order by filling an empty floor with props before the room/map shell exists.

---

# 5. Negative space must be intentional

Open space is necessary for Stardew movement and combat, but open space must look authored.

Good negative space:

- creates a clear central lane;
- gives hero props breathing room;
- preserves controller movement;
- supports combat readability;
- is framed by walls/environment so it feels like part of a place.

Bad negative space:

- giant uninterrupted floor fields;
- empty corners caused by missing art;
- a room whose only sense of structure comes from the screen edge;
- combat arenas with no environmental framing;
- visual emptiness justified after the fact as "gameplay space".

If a room feels empty, first inspect the shell/frame and composition before adding random props.

---

# 6. Props must belong to the room, not float inside it

Props should visually connect to architecture or environment.

Examples:

- a schedule board belongs on/against a wall zone;
- a bookshelf belongs in a wall/corner composition;
- a bench anchors to a waiting zone;
- a gate integrates into the room boundary or boarding structure;
- an observation window is part of the wall shell, not a poster floating over floor;
- a shrine belongs to a deliberate clearing / ruin composition;
- a telescope belongs to a lookout/window zone;
- a boss landmark should emerge from the arena's environmental language.

Avoid evenly scattering props across open floor solely to increase density.

Cluster by function and visual purpose.

---

# 7. Boundary and collision must agree

The visible map frame should communicate where the player can and cannot go.

Rules:

- visible solid wall/rock/tree mass should normally correspond to non-walkable space;
- do not rely on invisible collision to create a boundary that looks open;
- do not draw a visually solid barrier over a tile that gameplay expects the player to cross;
- exits/openings must visually align with warps and traversal anchors;
- boss arena limits must be readable before the player collides with them;
- narrow passages must remain controller-friendly.

If technical collision and visible framing disagree, fix the map architecture instead of hiding the issue with blockers.

---

# 8. Indoor room framing standard

For Stardew-style interiors, prefer a compact room silhouette with a deliberate perimeter.

Before accepting an interior, verify:

- back wall has enough visual weight to anchor furniture;
- side boundaries visually close the room;
- lower floor edge is intentionally shaped;
- entrance/exit is integrated into that edge;
- room proportions do not leave excessive dead floor;
- wall-mounted props are truly in wall zones;
- large furniture groups sit naturally against wall/corner zones;
- the room reads well even if all small decor is temporarily hidden.

**Shell test:** if the map still looks like a believable room with small props removed, the shell is doing its job.

---

# 9. Expedition / dungeon / boss-map framing standard

For non-interior maps, replace architectural framing with biome/environment framing.

Before accepting an expedition or boss map, verify:

- the playable space has a clear environmental silhouette;
- the outer 2-5 tile bands are used deliberately to establish biome identity where map size permits;
- transitions between terrain and boundary are natural rather than abrupt black cutoffs;
- major environmental masses are asymmetrical enough to feel organic unless symmetry is intentional;
- boss/encounter center remains readable;
- camera view does not expose huge meaningless voids around the active arena;
- the boundary material matches the biome/story: leaves for forest, stone for ruins/cave, etc.;
- environmental frame does not consume necessary combat space.

A boss arena should feel carved out of a real environment, not like a rectangle placed on a black canvas.

---

# 10. Visual scale must be judged against the whole room

Follow `CARDCHA_SPRITE_PRODUCTION_GUIDE.md` for individual sprite fidelity.

For map composition specifically:

- do not shrink hero props merely because the room shell is too small;
- do not enlarge the room into a giant empty box merely because a prop is large;
- adjust the room proportions and composition as a system;
- preserve the approved visual hierarchy: hero prop > secondary furniture > micro-decor;
- compare player/NPC scale against furniture and architecture before packaging.

When scale conflicts appear, stop and solve the composition deliberately instead of applying arbitrary image scaling.

---

# 11. Preview the shell before the full decoration pass

For every meaningful map rebuild, produce/check visuals in stages where possible:

## Shell preview
Shows:
- floor;
- walls/environmental frame;
- entrances/exits;
- major collision silhouette;
- no small decor required.

The shell must already look coherent.

## Composition preview
Adds:
- hero props;
- major furniture/landmarks;
- functional zones.

The map must already resemble the approved concept at this stage.

## Polish preview
Adds:
- plants;
- lamps;
- clutter;
- rugs;
- small environmental accents;
- selective foreground.

Do not use polish to disguise a weak shell.

---

# 12. Visual validator requirements

CI/map validation should not merely prove that TMX files parse.

Where practical, validate:

- map dimensions and layer structure;
- entrances/exits and gameplay anchors;
- expected boundary occupancy / environmental frame zones;
- no accidental huge unframed floor region;
- complete hero-prop footprints;
- wall-mounted props are positioned in intended wall zones;
- collision agrees with visible boundaries;
- required center lane / combat space remains open;
- approved concept zones still exist;
- render preview can be generated deterministically;
- preview does not expose missing chunks or unsupported layers.

CI remains technical acceptance only. In-game screenshots decide visual acceptance.

---

# 13. Permanent map workflow

For every new room/map or major rebuild:

## Pass 1 - Reference & topology
- identify vanilla Stardew and established mod references;
- lock gameplay anchors and intended biome/room role;
- define target map size/proportions.

## Pass 2 - Shell / frame
- construct walls or environmental boundary;
- integrate exits/warps;
- verify collision and playable silhouette;
- review a shell-only preview.

## Pass 3 - Faithful composition
- place approved hero art using `CARDCHA_SPRITE_PRODUCTION_GUIDE.md`;
- establish functional clusters and room zones;
- preserve approved concept hierarchy.

## Pass 4 - Polish
- add secondary props and micro-detail;
- add selective foreground depth;
- remove dead zones and visual noise without breaking gameplay.

## Pass 5 - In-game acceptance
- test real camera framing;
- walk all boundaries;
- test entrances/warps;
- test actor occlusion;
- test controller movement;
- test combat if applicable;
- compare screenshots against concept/reference goals.

Do not mark the visual pass accepted until Ron explicitly approves the in-game result.

---

# 14. Permanent do / do-not summary

## DO

- build shell/frame before props;
- make every space feel grounded and contained;
- use architectural framing indoors;
- use environmental framing outdoors/dungeons/boss arenas;
- research vanilla Stardew and established mods before inventing layout conventions;
- keep collision visually honest;
- preserve deliberate negative space;
- cluster props by function;
- preview shell, composition and polish separately;
- keep gameplay anchors frozen during visual passes unless explicitly redesigning gameplay.

## DO NOT

- start from a giant empty rectangular floor;
- leave rooms floating in black void without a deliberate Stardew-like boundary;
- scatter props randomly to simulate density;
- use invisible blockers to compensate for visually open map edges;
- turn every dungeon/boss arena into the same rectangular frame;
- use wooden room framing for biomes where leaves, cliffs, rocks, ruins or water make more sense;
- enlarge the map merely to fit oversized art without rethinking composition;
- shrink approved sprites simply to make a weak room shell work;
- copy another mod's art; reference structural solutions only;
- let CI success substitute for in-game visual review.

---

# Mandatory checklist for every future room/map branch

Before implementation:

- [ ] Read `CARDCHA_MAP_ROOM_CONSTRUCTION_GUIDE.md`.
- [ ] Read `CARDCHA_SPRITE_PRODUCTION_GUIDE.md` if sprites/props are involved.
- [ ] Identify comparable vanilla Stardew references.
- [ ] Identify established mod references where useful.
- [ ] Record map purpose / biome / room role.
- [ ] Lock gameplay anchors and traversal requirements.
- [ ] Define the intended architectural or environmental frame.

Before prop integration:

- [ ] Shell is visually coherent on its own.
- [ ] Entrances/exits are integrated into the shell.
- [ ] Collision matches visible boundaries.
- [ ] Negative space is deliberate, not accidental emptiness.
- [ ] Hero prop zones are defined.

Before packaging:

- [ ] Room/map does not read as a flat floor floating in void.
- [ ] Indoor perimeter or environmental frame is complete.
- [ ] Major prop clusters belong to the architecture/environment.
- [ ] Full approved sprite footprints are preserved.
- [ ] Gameplay lanes/anchors remain readable.
- [ ] Deterministic preview inspected where possible.
- [ ] Technical CI passes.
- [ ] Visual acceptance remains PENDING until Ron approves the actual game result.

---

# Relationship to repository rules

This guide supplements, and does not replace:

- `AGENTS.md`;
- `CARDCHA_SPRITE_PRODUCTION_GUIDE.md`;
- `CARDCHA_RENDERING_DEPTH_CONTRACT.md`;
- current branch handoff/source-of-truth documents.

If rules conflict, preserve the stricter contract and stop for review instead of silently weakening map quality or gameplay correctness.
