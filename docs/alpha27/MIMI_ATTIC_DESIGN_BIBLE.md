# MiMi Attic Design Bible

**Milestone target:** Alpha.27 visual pass

## Core role

MiMi's attic is **her real home**, not her main shop.

It exists to show MiMi's private life, connect MiMi/ChaCha/Cardcha/Scrap lore, support friendship progression, and host later small secrets/events.

- Community Center = public workplace later.
- MiMi Attic = private home / character / secrets.

## Tone

Warm, lived-in, slightly messy, eccentric, cozy, and a little mysterious.

Avoid horror, sterile laboratory vibes, generic Wizard-room aesthetics, and over-clean villager-bedroom styling.

Target feeling:
> A strange but cozy hidden room belonging to someone clever, secretive, and unexpectedly cute.

## Five locked zones

### 1. Entrance / stair landing

- staircase from Wizard House;
- small landing/rug;
- simple prop near the stairs;
- should not expose every secret immediately.

### 2. Research / work desk

- wooden desk;
- notes/papers;
- Cardboard Scrap / loose card fragments;
- small machine/device;
- jars, crystals, batteries, tools, books.

This is the Cardcha/Scrap/MiMi-brain zone.

### 3. Bed / personal corner

- small bed;
- slightly untidy blanket/pillow;
- bedside lamp;
- modest storage/personal props.

This makes MiMi feel like a real person who actually lives there.

### 4. TV / secret relaxation zone

- TV;
- chair/cushion/tiny sofa;
- low table;
- snacks/drink/magazines/notes;
- slightly tucked-away placement.

This zone is reserved for the later **17:30 secret routine** and MiMi's hidden romance/shipping side.

### 5. ChaCha / upgrade corner

- cushion/perch for ChaCha;
- odd components;
- tiny prototype stand/device;
- visual hints of Card Dust storage.

This is the natural future home of ChaCha upgrade interactions.

## Recommended room flow

- Bottom/lower side: entrance.
- Left: research desk.
- Right: bed/personal corner.
- Upper/deeper corner: TV/secret zone.
- Near desk/side wall: ChaCha corner.

The TV zone should feel more private and not be the first thing visible on entry.

## Heart progression

- 0–1 hearts: attic locked.
- 2 hearts: access unlocked.
- 4 hearts: more personal room dialogue/inspectables.
- 6 hearts: 17:30 private TV routine becomes eligible.
- 8+ hearts: deeper MiMi/ChaCha/Card Dust/Community Center hooks.

## 17:30 secret direction

At higher friendship (target: 6 hearts), the player can occasionally find MiMi around 17:30 privately watching TV with a romance/drama/shipping vibe.

Tone: cute, awkward, lightly comedic, never turning MiMi into a joke character.

Desired read:
> MiMi has a secret soft side.

## Interaction philosophy

The attic should not become a second shop stuffed with menus.

Primary purpose:
- atmosphere;
- character development;
- relationship progression;
- inspect/lore/event points.

Possible later secondary gameplay:
- ChaCha upgrades via Card Dust;
- scrap/card inspection flavor;
- small one-off exchanges;
- event triggers.

## Inspectable groundwork

Recommended first inspect points:
- research desk;
- TV zone;
- ChaCha corner.

Possible flavor direction:
- desk: strange notes, arrows, and warnings about ChaCha;
- TV: warm remote/snacks, mildly incriminating evidence;
- ChaCha corner: suspiciously engineered for maximum comfort.

## Technical rules

- Stable location ID remains `Cardcha_MiMiAttic`.
- Do not rename it later when map art changes.
- Do not replace the entire Wizard House map just to add access.
- Use a staircase/access injection strategy for compatibility.
- Custom attic map/decor may replace the current placeholder interior without changing the location ID or save references.

## Implementation phases

### Phase 1 — Foundation
- location exists;
- warp works;
- MiMi can live there;
- access unlocks at 2 hearts.

### Phase 2 — Visual foundation
- custom/coherent attic layout;
- all five zones readable;
- MiMi personality visible in props.

### Phase 3 — Light interactions
- inspect points;
- room-specific dialogue;
- environmental storytelling.

### Phase 4 — Secrets/events
- 17:30 routine;
- heart-event hooks;
- ChaCha/Card Dust functions.

## Canon summary

Locked:
- MiMi's real home is the attic above Wizard House.
- It is not her main shop.
- Entry unlocks at 2 hearts.
- Five zones: entrance, research desk, bed, TV secret zone, ChaCha/upgrade corner.
- Secret/private TV/romance side appears later.
- 6 hearts is the recommended first stronger private-life reveal.
