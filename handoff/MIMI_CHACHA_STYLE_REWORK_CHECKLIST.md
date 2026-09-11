# Mimi & ChaCha Stardew Style Rework Checklist

## Status
**STYLE AUDIT / REWORK CANDIDATES — NOT YET REDRAWN**

Ron reports that both Mimi and ChaCha currently feel visually disconnected from Stardew Valley. They are therefore mandatory style-audit/rework candidates before their character art can be treated as final.

This document is a planning/audit contract only. It does **not** claim that either character has already been redrawn or accepted.

The permanent governing guide is:

`CARDCHA_CHARACTER_CREATURE_STYLE_GUIDE.md`

---

# Shared goal

Preserve each character's identity and role while translating the world sprite into Stardew Valley's actor language.

The target is not "generic Stardew" and not "erase Cardcha personality".

The target is:

> recognizable Mimi / ChaCha identity, rebuilt so the character looks native beside the Farmer, villagers, pets, monsters, and Cardcha maps.

---

# Phase 1 — Inventory pass

For **Mimi** and **ChaCha** separately:

- [ ] Locate every current world sprite sheet.
- [ ] Locate portraits / UI art if present.
- [ ] Locate idle / walk / directional animation sheets.
- [ ] Locate combat / reaction / special-action sheets.
- [ ] Locate overlays, glows, particles, shadows, or proxy visuals.
- [ ] Record file path for every asset.
- [ ] Record pixel dimensions.
- [ ] Record frame dimensions / frame count / layout.
- [ ] Record alpha mode and SHA256.
- [ ] Identify the runtime class / draw owner for every world sprite.
- [ ] Confirm collision / hitbox / interaction footprint.
- [ ] Capture current in-game screenshots beside Farmer.
- [ ] Capture at least one screenshot beside a relevant vanilla actor/creature.

Do not start the redraw until this inventory is complete enough to avoid losing a required animation state.

---

# Phase 2 — Identity lock

Before simplifying the visual style, record what must survive.

## Mimi

- [ ] Signature silhouette cues recorded.
- [ ] Signature colors recorded.
- [ ] Personality/readability cues recorded.
- [ ] Role-specific motifs recorded.
- [ ] Any combat/boss readability requirements recorded.
- [ ] Elements that currently make Mimi feel non-Stardew identified explicitly.

## ChaCha

- [ ] Signature silhouette cues recorded.
- [ ] Signature colors recorded.
- [ ] Personality/readability cues recorded.
- [ ] Companion/mascot role cues recorded.
- [ ] Movement/interaction readability requirements recorded.
- [ ] Elements that currently make ChaCha feel non-Stardew identified explicitly.

The rebuild may simplify execution but must not silently redesign their identities.

---

# Phase 3 — Stardew reference pass

Choose vanilla reference peers by **role**, not just by superficial shape.

For each character:

- [ ] Select at least two relevant Stardew vanilla reference actors/creatures where practical.
- [ ] Record visible gameplay footprint.
- [ ] Record head/body/limb proportion observations.
- [ ] Record silhouette density.
- [ ] Record palette/value/saturation behavior.
- [ ] Record outline/shading economy.
- [ ] Record feet/ground anchor behavior.
- [ ] Record directional frame layout.
- [ ] Record idle/walk/action cadence.

High-quality Stardew mods may be consulted for implementation patterns, but vanilla Stardew remains the primary style anchor. Do not copy another mod's character art.

---

# Phase 4 — Rebuild target

For Mimi and ChaCha separately:

1. [ ] Choose intentional target world-sprite dimensions.
2. [ ] Draw/rebuild silhouette thumbnails at target gameplay scale.
3. [ ] Validate silhouette beside Farmer before detailed rendering.
4. [ ] Translate palette toward Stardew-compatible saturation/value range while preserving signature colors.
5. [ ] Reduce illustration-level micro-detail.
6. [ ] Use compact, readable shading clusters.
7. [ ] Lock feet/origin/ground contact.
8. [ ] Build base idle frame.
9. [ ] Build required directional frames.
10. [ ] Build walk animation.
11. [ ] Build interaction/reaction animation where relevant.
12. [ ] Build combat/special frames where relevant.
13. [ ] Integrate through actor-native draw ownership.
14. [ ] Verify collision / interaction against visible footprint.
15. [ ] Capture in-game side-by-side comparison screenshots.

Do **not** simply bitmap-shrink the current oversized/high-detail art until it becomes muddy. If style translation is necessary, rebuild deliberately for the target dimensions.

---

# Mimi-specific acceptance checklist

Mimi PASS requires:

- [ ] Recognizable as Mimi without relying on tiny decorative details.
- [ ] No "different pixel-art game" effect beside Farmer/NPCs.
- [ ] Boss/combat readability preserved where applicable.
- [ ] Silhouette remains readable during movement/combat.
- [ ] Palette does not overpower normal Stardew environments.
- [ ] Attack/reaction animation remains readable at gameplay scale.
- [ ] Actor depth/feet anchoring is correct.
- [ ] No proxy + authored sprite duplication.
- [ ] Ron approves the real in-game screenshots/result.

Until all applicable items pass, Mimi remains **STYLE REWORK PENDING**.

---

# ChaCha-specific acceptance checklist

ChaCha PASS requires:

- [ ] Recognizable as ChaCha immediately at gameplay scale.
- [ ] Companion/mascot personality survives simplification.
- [ ] Scale feels natural beside Farmer and vanilla small actors/creatures.
- [ ] No sticker/glossy/high-detail mismatch against Stardew maps.
- [ ] Idle/walk cadence feels compatible with Stardew.
- [ ] Directional proportions remain consistent.
- [ ] Feet/origin/shadow feel grounded.
- [ ] Companion interaction/collision remains correct.
- [ ] Ron approves the real in-game screenshots/result.

Until all applicable items pass, ChaCha remains **STYLE REWORK PENDING**.

---

# Required comparison board before final acceptance

For each rebuilt character, create an acceptance board or equivalent screenshot set containing:

- current/old sprite;
- rebuilt sprite at 1x pixel scale;
- rebuilt sprite at actual in-game presentation scale;
- beside Farmer;
- beside a relevant vanilla actor/creature;
- on at least one normal Stardew map;
- on a Cardcha map;
- representative idle/walk/action frames.

This board is evidence for review, not automatic acceptance.

---

# Non-goals

- no personality rewrite;
- no lore rewrite;
- no gameplay rebalance merely because the sprite is rebuilt;
- no collision expansion solely to match oversized art;
- no new rendering owner outside the established actor/depth contract;
- no visual acceptance claim before Ron tests/approves the in-game result.
