# Latest Cardcha Handoff

Current development branch: `cardcha-alpha28-0696-airship-concept-faithful-visible-integration`

Current production / TEST baseline: `cardcha-alpha28-0695-region1-prop-integration`

Current production build: `0.3.0-alpha.28.0.4.14.4.5.12.61`

Current production materialized source head: `39e13a370281b29f77d94be497603a3243edda41`

Current production handoff: `handoff/ALPHA28_0695_REGION1_ENVIRONMENT_PROP_PRODUCTION_INTEGRATION.md`

0696 status: **WIP Airship visual recovery.** Ron supplied the approved sprite + concept source, locked a permanent sprite-production workflow, added a permanent repository-wide room/map construction rule, and then added a mandatory Stardew-style audit rule for all character/creature sprites.

## Permanent sprite rule

Every future task that creates, edits, imports, rebuilds, scales, tiles, places, or validates sprites/physical visual assets MUST read and follow:

`CARDCHA_SPRITE_PRODUCTION_GUIDE.md`

Key permanent sprite rules:
- approved source art is production source-of-truth, not loose inspiration;
- no unapproved redraw/rescale for implementation convenience;
- large Stardew props use faithful multi-tile footprints instead of being shrunk merely to reduce tile count;
- preserve approved full-room composition;
- validate actual visible footprint/render ownership, not only file/GID presence;
- research proven Stardew/xTile/native modding patterns before inventing a new rendering convention;
- use an inventory pass, faithful integration pass, then polish pass;
- CI is technical acceptance only; visual acceptance requires Ron's in-game confirmation.

## Permanent room / map construction rule

Every future task that creates, rebuilds, expands, decorates, frames, or visually polishes an interior, hub, expedition map, dungeon, boss arena, or any other playable map MUST read and follow:

`CARDCHA_MAP_ROOM_CONSTRUCTION_GUIDE.md`

This applies to Airship and every future Cardcha map.

Key permanent map rules:
- build the room/map shell or environmental frame **before** props;
- indoor rooms need a coherent Stardew-style perimeter: back wall, side boundaries, lower floor edge, integrated entrances/exits;
- expedition/dungeon/boss maps use the biome/environment as their frame instead of automatically using a wooden rectangle: foliage/trees for forests, cliffs/rocks for caves and mountains, ruins/roots for ancient areas, water/reeds for wet biomes, etc.;
- a boss arena should feel carved out of its environment rather than placed as a rectangle on a black canvas;
- do not start with a giant empty floor and try to fake density by scattering props;
- negative space must be intentional and visually framed;
- props should belong to architectural/environmental zones instead of floating independently;
- visible boundaries and collision must agree;
- before creating a new map language, study comparable vanilla Stardew maps and established high-quality Stardew mods for structural patterns, without copying third-party art;
- required pass order: reference/topology -> shell/frame -> faithful composition -> polish -> in-game acceptance;
- CI is technical acceptance only; map visual acceptance remains PENDING until Ron explicitly approves the actual in-game result.

## Permanent character / creature Stardew style rule

Every future task that creates, rebuilds, animates, replaces, renders, or visually validates an NPC, companion, mascot, pet, monster, boss, summon, or other animated world actor MUST read and follow:

`CARDCHA_CHARACTER_CREATURE_STYLE_GUIDE.md`

Key permanent actor rules:
- a character is judged inside a Stardew scene, not only on a transparent sprite sheet;
- before finalization, study at least two relevant vanilla Stardew actor/creature references where practical;
- compare real gameplay scale, body proportions, silhouette economy, detail density, palette/value range, outline/shading, ground anchoring, frame layout, and animation cadence;
- preserve Cardcha identity/personality while translating the actor into Stardew's visual language;
- do not bitmap-shrink oversized/high-detail character art as a substitute for a deliberate target-size rebuild;
- test beside Farmer and relevant vanilla actors/creatures in a real map;
- if the sprite produces a "different game" effect, the visual pass is FAIL even if the isolated art looks good;
- CI is technical acceptance only; actor visual acceptance remains PENDING until Ron approves the in-game result.

### Mimi / ChaCha status

Mimi and ChaCha are now explicitly flagged as:

**STYLE AUDIT / REWORK CANDIDATES — VISUAL FINALITY NOT ACCEPTED YET**

Specific governing checklist:

`handoff/MIMI_CHACHA_STYLE_REWORK_CHECKLIST.md`

No Mimi or ChaCha redraw is claimed in this documentation pass. Their next visual work must begin with asset/runtime inventory + identity lock + Stardew reference study before any final sprite sheet is produced.

`AGENTS.md` now makes the sprite guide, room/map guide, and character/creature style guide mandatory repository-wide.

## Existing production verification

Authoritative 0695 successful CI run: `34655852302`

Artifact ID: `10285408808`

Artifact digest: `sha256:065ed6936c5d06479eb2927a7c2b717d359a598447f3b9f6e5c35bc57221bbac`

Verified inner TEST ZIP SHA256: `fac7aaa1c9014aedfd0eba887a1b2bd46531fbb9f676ebd7896b15e321fce726`

0695 Region I in-game visual acceptance remains **PENDING**.

Airship 0693/0696 visual acceptance remains **PENDING**. Do not claim the Airship concept-to-game gap is solved until Ron tests the actual corrected package and approves it.
