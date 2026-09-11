# Cardcha Sprite Production Guide

This document is the permanent source-of-truth for any Cardcha work that creates, edits, imports, rebuilds, scales, tiles, places, or validates sprites and physical visual assets.

**Mandatory rule:** every future sprite-related change MUST follow this guide before implementation begins.

The purpose is to prevent a recurring failure mode: an approved source sprite or concept is treated as loose inspiration, then redrawn, rescaled, rearranged, or repackaged until the in-game result no longer resembles the approved design.

---

## Core principle

**Approved source art is production art, not a reference to reinterpret.**

If Ron supplies or approves a sprite/concept:

- preserve its visual language, silhouette, proportions, palette, and composition;
- do not redraw it merely to make implementation easier;
- do not scale it down just because it spans many Stardew tiles;
- do not replace it with a procedurally generated approximation;
- do not move major visual groups away from the approved concept composition without explicit approval;
- do not claim a visual pass is successful merely because an asset file, GID, or tileset exists.

If an asset is too large for the current map composition, fix the map composition, footprint, tiling, layer ownership, or collision design first. Scaling the art is not the default solution.

---

# Required six-step sprite workflow

## Step 1 - Lock the source art inventory

Before touching production TMX/code, create or update a **Source Pack / asset manifest** for the visual pass.

For Airship, this includes at minimum:

- gate;
- reception / board;
- window;
- console;
- luggage cart;
- bench;
- lamp;
- crate;
- approved full-room concepts.

For every source asset record:

- asset name;
- source file path;
- SHA256 when the asset is approved/locked;
- pixel dimensions;
- intended tile footprint at native resolution;
- target room/map;
- intended TMX/native layer ownership;
- collision ownership / whether it blocks movement;
- source concept / screenshot association;
- approval status.

### Source-lock rule

Once an asset is approved, use its checksum as a guard where practical. A production script should fail if the locked source asset drifts unexpectedly.

Do not silently regenerate a different-looking asset under the same filename.

---

## Step 2 - Do not rescale or redraw approved art by default

Allowed operations:

- crop genuinely unused transparent canvas;
- preserve or pad transparent canvas when required for alignment;
- split the art onto a 16x16 Stardew tile grid;
- separate visual portions into `Buildings` / `Front` where depth requires it;
- define collision independently from transparent visual regions;
- convert file encoding/color mode without changing visible pixels;
- make technical alpha fixes that preserve appearance.

Not allowed without explicit approval:

- shrinking a large prop simply to make it fit fewer tiles;
- enlarging a small sprite until pixel structure becomes coarse or alien to Stardew;
- redrawing the silhouette;
- reinterpreting the source into a different prop/layout;
- replacing an approved hand-authored sprite with generated placeholder art;
- changing proportions, composition, palette, or decorative hierarchy merely to satisfy a script.

### Stardew scale rule

Stardew uses a 16x16 map tile grid. This does **not** mean a prop must be visually one tile large.

A 112x96 gate is naturally a 7x6-tile visual asset. A large window, counter, console, shrine, bookcase, machine, or arch may span many tiles. Multi-tile props are normal.

Tile the sprite faithfully instead of shrinking it.

---

## Step 3 - Follow the approved full-room concept composition

When a room concept has been approved, the production TMX should preserve the same visual structure.

Examples:

- reception/desk remains on the intended side;
- gate remains in the intended boarding area;
- window remains the hero wall feature where approved;
- console remains in the intended navigation zone;
- waiting/luggage clusters retain their intended room relationship;
- negative/open space remains intentional rather than becoming accidental emptiness.

Do not take an approved dense room concept and reduce it to several isolated props in a mostly empty vanilla shell.

### Composition contract

Before integration, record the major prop zones/anchors from the approved concept. Validation should ensure the final map still contains those major groups in the expected regions.

If the approved composition conflicts with gameplay anchors, stop and redesign the layout consciously. Do not silently delete or move the visual group.

---

## Step 4 - Validate what is actually visible, not only what exists

A validator that only proves these facts is insufficient:

- file exists;
- PNG dimensions are correct;
- tileset exists;
- GID exists somewhere in a layer.

Sprite validation must also prove:

- the expected prop occupies its complete intended footprint;
- non-transparent source tiles are represented at the expected map cells;
- the prop is owned by a Stardew-rendered/native layer or entity;
- physical art is not stranded in an unsupported/custom layer that the real game does not display;
- the correct source asset is referenced;
- approved source hashes have not drifted;
- collision matches the visible base and not the transparent canvas;
- the prop is not accidentally hidden under another map layer;
- the map does not contain only a fragment of a multi-tile sprite;
- the final room composition contains the required hero/major prop groups.

### Rendering ownership rule

Physical art must follow `AGENTS.md` and `CARDCHA_RENDERING_DEPTH_CONTRACT.md`.

Prefer Stardew-native/map-native ownership such as:

- TMX `Buildings`;
- TMX `Front` where intentional occlusion is required;
- map/terrain layers that are confirmed to render in Stardew;
- native `Object`, `Furniture`, terrain feature, or actor ownership when appropriate.

Do not invent a custom TMX layer and assume Stardew will render it. Verify the target layer/owner against actual Stardew/xTile behavior or a known working mod pattern first.

---

## Step 5 - Test visually as early as possible

Do not wait until a large branch is complete before checking visual output.

For every meaningful sprite integration pass:

1. generate a deterministic preview/render of the TMX composition where possible;
2. compare it directly with the approved source concept;
3. inspect the real game as soon as a TEST package exists;
4. stop the pass if the room is unexpectedly empty, proportions drift, a hero prop is fragmented, or the silhouette no longer matches the source.

### Visual acceptance rule

CI is technical acceptance only.

**Visual acceptance requires Ron's in-game confirmation.**

A green workflow does not mean the sprite pass is visually correct.

Screenshots from the actual game override assumptions made by validators or preview tools.

---

## Step 6 - Fewer passes, higher fidelity

Preferred workflow:

1. **Inventory pass** - lock all source art, dimensions, hashes, footprints, target layers, collision, and concept associations.
2. **Faithful integration pass** - place the exact approved art into real Stardew rendering ownership without redesigning it.
3. **Polish pass** - only after in-game screenshots prove the base integration is faithful; adjust collision edges, occlusion splits, minor spacing, and technical cleanup.

Avoid repeated loops of:

- generate new approximation;
- package;
- discover it looks different;
- generate another approximation.

If visual fidelity is wrong, return to the source art and rendering architecture rather than creating a new interpretation.

---

# Research-before-invention rule

Before inventing a new sprite/map integration technique, check how Stardew Valley itself or established Stardew mods solve the same class of problem.

For unfamiliar visual ownership, research should answer at least:

- which xTile/TMX layers Stardew actually renders and in what order;
- how large multi-tile props are normally authored;
- how `Buildings` and `Front` are used for depth and walk-behind behavior;
- how collision is separated from visual transparency;
- whether a native `Object`, `Furniture`, terrain feature, or actor is more appropriate than raw map art;
- whether the proposed technique is proven in-game, not just theoretically valid XML.

Do not substitute a newly invented repository convention for known Stardew behavior unless there is a documented technical reason.

---

# Permanent do / do-not summary

## DO

- use the approved sprite as the source-of-truth;
- preserve native visible pixels whenever possible;
- use multi-tile footprints for large props;
- split depth layers without changing the design;
- keep visual and collision ownership explicit;
- lock approved assets with hashes/manifests;
- validate exact footprint and composition;
- test in the real game early;
- research working Stardew/xTile patterns before inventing a new one;
- mark visual acceptance PENDING until Ron confirms screenshots/gameplay.

## DO NOT

- treat approved art as loose inspiration;
- redraw or regenerate it for convenience;
- shrink it merely to reduce tile count;
- enlarge tiny art until the style breaks;
- repack unrelated props into an unreadable atlas without a clear manifest;
- call an asset integrated just because it exists in the ZIP;
- use unsupported/custom layers without proving they render;
- let CI declare visual acceptance;
- silently change room composition away from the approved concept.

---

# Mandatory checklist for every future sprite PR/branch

Before code/TMX changes:

- [ ] Source assets inventoried.
- [ ] Approved asset hashes recorded where appropriate.
- [ ] Native dimensions recorded.
- [ ] Native tile footprint recorded.
- [ ] Room/map target recorded.
- [ ] Layer/rendering owner selected from a proven Stardew path.
- [ ] Collision owner/footprint recorded.
- [ ] Approved concept composition recorded.

Before packaging:

- [ ] No unapproved scaling/redraw occurred.
- [ ] Every required non-transparent sprite region is placed.
- [ ] Complete multi-tile footprints are present.
- [ ] Physical art uses a confirmed visible/native rendering owner.
- [ ] Collision matches visible bases.
- [ ] Major room composition matches the approved concept.
- [ ] Deterministic preview inspected where possible.
- [ ] Technical CI passes.
- [ ] Visual acceptance is still marked PENDING unless Ron explicitly approved the in-game result.

After in-game test:

- [ ] Ron checked visual density and composition.
- [ ] Ron checked scale/proportion against source art.
- [ ] Ron checked front/behind occlusion.
- [ ] Ron checked movement/collision/interaction.
- [ ] Only after that may the visual pass be marked ACCEPTED.

---

# Relationship to repository rules

This guide supplements, and does not replace:

- `AGENTS.md`;
- `CARDCHA_RENDERING_DEPTH_CONTRACT.md`;
- current branch handoff/source-of-truth documents.

If there is a conflict, preserve the stricter rule and stop for explicit review rather than silently weakening either contract.
