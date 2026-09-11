# Cardcha Character & Creature Stardew Style Guide

This document is the permanent source-of-truth for any Cardcha work that creates, edits, imports, rebuilds, animates, renders, or validates character/creature sprites.

It applies repository-wide to:

- NPCs;
- companions;
- mascots;
- pets;
- monsters;
- bosses;
- summons;
- combat proxies with authored visuals;
- animated character-like world actors.

**Mandatory rule:** a character sprite is not accepted merely because it looks attractive in isolation. It must look visually native beside Stardew Valley actors and environments at real gameplay scale.

---

## Core principle

**Every character or creature must be translated into Stardew Valley's visual language before it can be considered final.**

Cardcha may keep its own identity, colors, motifs, personalities, and fantasy ideas, but the finished actor must still look as though it belongs in the same game world as the Farmer, villagers, pets, monsters, and vanilla environments.

A beautiful sprite that looks imported from a different pixel-art game is a visual failure for Cardcha.

---

# Mandatory reference research before finalization

Before finalizing any new or rebuilt actor sprite, select and document relevant Stardew Valley references.

Use at least **two relevant vanilla references** whenever practical.

Suggested reference classes:

- human / humanoid NPC -> villagers, Farmer animation language, comparable vanilla humanoids;
- pet / companion -> cat, dog, horse, Junimo, or the closest role/scale analogue;
- monster -> vanilla monster with a comparable footprint or movement role;
- boss / large creature -> multiple vanilla monsters plus actor-scale references, because Stardew has fewer direct boss equivalents;
- summon / helper -> Junimo, pet, monster, or other small actor with a comparable gameplay role.

High-quality Stardew mods may also be researched for implementation patterns, scale, animation layout, and world integration, but:

- do not copy another mod's art;
- do not use another mod as permission to abandon Stardew's visual language;
- prefer vanilla Stardew as the primary style anchor.

For the chosen references, record where useful:

- visible in-game dimensions;
- body / head / limb proportions;
- silhouette economy;
- palette/value range;
- outline behavior;
- shading density;
- feet / ground anchor;
- directional frame layout;
- idle / walk / attack cadence;
- collision footprint relative to visible sprite.

---

# Required visual audit dimensions

Every actor visual pass must explicitly consider all of the following.

## 1. In-game footprint and scale

- Judge the sprite at the real Stardew gameplay zoom/scale, not only on a transparent canvas.
- The actor must not feel unusually huge, tiny, or over-rendered compared with nearby vanilla actors unless gameplay intentionally requires that scale.
- Visual footprint and gameplay footprint must make sense together.

## 2. Body proportions

- Head/body/limb proportions should be compatible with Stardew's readable, compact sprite language.
- Avoid anatomy that only works at illustration scale but becomes awkward at gameplay scale.
- Preserve identity cues while translating proportions into a Stardew-compatible form.

## 3. Silhouette readability

- The character should be recognizable from its outer shape at normal gameplay size.
- Major identity features should survive without relying on tiny decorative pixels.
- Avoid noisy silhouettes with too many thin protrusions or ornamental fragments.

## 4. Detail density / pixel economy

- Do not pack illustration-level detail into a sprite that will be seen at Stardew scale.
- Prioritize face/hair/body/role-defining motifs over micro-detail.
- If details vanish when shown at real gameplay size, they should not carry critical identity information.

## 5. Palette and value harmony

- Saturation, contrast, and brightness should sit comfortably beside Stardew Valley actors and backgrounds.
- Cardcha signature colors may remain, but avoid excessive neon, glossy highlights, or hyper-saturated accents that detach the actor from the world.
- Important body regions must remain readable against common Stardew backgrounds.

## 6. Outline and shading language

- Avoid heavy rendering, excessive gradients, or high-frequency highlight/shadow patterns that make the actor look from another pixel-art game.
- Use compact shading groups and readable clusters appropriate to Stardew-scale sprites.
- Preserve enough contrast to read clearly without turning the sprite into a sticker.

## 7. Feet / ground anchoring / depth

- The actor must look planted on the tile/world surface.
- Foot position, origin, shadow, and draw depth must agree.
- Walking near furniture, walls, terrain, Farmer, NPCs, and monsters must not create a floating or pasted-on appearance.

## 8. Face and expression readability

- Expressions must be readable at gameplay scale.
- Do not depend on illustration-sized facial detail.
- Portrait art and world sprites may carry different levels of detail, but their identity must remain coherent.

## 9. Animation language

- Idle, walk, reaction, attack, hurt, casting, or special-action frames should follow a cadence that feels compatible with Stardew.
- Avoid overly fluid or elaborate animation that makes the character visually belong to a different game unless an explicit gameplay moment calls for it.
- Directional frames must remain consistent in proportions and grounding.

## 10. Context fit

The final judgment happens **inside a real Stardew scene**.

A sprite must be checked:

- beside the Farmer;
- beside at least one vanilla NPC/creature when relevant;
- against a normal Stardew map background;
- near Cardcha map art;
- while moving, not only while idle.

If the actor looks foreign to the scene, the pass fails even if the isolated sprite sheet is attractive.

---

# No careless bitmap scaling

For actor sprites, simple bitmap shrinking is not a substitute for style translation.

If existing art is oversized or over-detailed:

- preserve the character's identity, personality, signature colors, silhouette cues, and role-defining motifs;
- choose a target Stardew-compatible footprint intentionally;
- rebuild/redraw the sprite deliberately for that footprint when needed;
- simplify details consciously instead of shrinking until they become visual noise;
- preserve animation consistency across all directions/states.

Unlike approved environment props, character art may require an explicit **style rebuild** because proportion, anatomy, and animation language need to be translated for Stardew. Such a rebuild must preserve character identity rather than inventing a different character.

---

# Required actor workflow

## Pass 1 - Inventory and identity lock

Before drawing:

- locate every current sprite sheet / portrait / animation / overlay / effect for the actor;
- record file paths, dimensions, frame layout/count, hashes, and runtime draw owner;
- capture current in-game screenshots beside vanilla actors;
- document identity elements that must survive the rebuild.

## Pass 2 - Stardew reference study

- choose relevant vanilla actor references;
- record target scale / footprint;
- identify palette/detail/outline/animation benchmarks;
- decide which existing details are essential and which should be simplified.

## Pass 3 - Silhouette and base sprite

- produce target-size silhouette/base idle sprite first;
- validate proportion and scale before building full animation sheets;
- test the base sprite inside a real map early.

## Pass 4 - Directional and action animation

Only after base scale/style is approved:

- complete required directional frames;
- idle/walk;
- interaction/reaction;
- combat/special frames where relevant;
- actor-native draw/depth integration.

## Pass 5 - In-game comparison and polish

- capture side-by-side context screenshots;
- inspect grounding, depth, palette, detail density, and motion;
- polish only after the actor already reads as part of Stardew.

---

# Acceptance evidence required

Before a character/creature visual pass can be called complete, provide or inspect where applicable:

- idle beside Farmer;
- idle beside at least one relevant vanilla NPC/creature;
- front/side/back directions if the actor uses them;
- walk animation in a real map;
- action/combat/special animation when applicable;
- same actor against at least one normal Stardew background;
- depth/occlusion near physical map props;
- gameplay collision/interaction alignment.

**CI success is technical acceptance only.**

**Visual acceptance remains PENDING until Ron approves the real in-game result.**

---

# Pass / fail rule

An actor sprite PASSES only when:

- it no longer produces a "different game" effect;
- scale feels natural beside vanilla actors;
- silhouette is readable at real gameplay size;
- palette and contrast sit comfortably in Stardew scenes;
- detail density is appropriate;
- feet / origin / depth feel grounded;
- animation cadence is coherent with Stardew;
- collision and interaction match the visible body/role;
- character identity is preserved;
- Ron approves the in-game visual result.

If any of those fail, the actor remains a style-rework candidate.

---

# Relationship to other repository rules

This guide supplements:

- `CARDCHA_SPRITE_PRODUCTION_GUIDE.md`;
- `CARDCHA_MAP_ROOM_CONSTRUCTION_GUIDE.md`;
- `AGENTS.md`;
- `CARDCHA_RENDERING_DEPTH_CONTRACT.md`;
- current handoff/source-of-truth documents.

For characters and creatures, `CARDCHA_SPRITE_PRODUCTION_GUIDE.md` alone is not sufficient. This character/creature guide is also mandatory.
