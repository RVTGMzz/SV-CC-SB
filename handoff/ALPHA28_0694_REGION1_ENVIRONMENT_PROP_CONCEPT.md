# Alpha 28 0694 - Region I Environment Prop Visual Rebuild - CONCEPT PASS

## Status
**CONCEPT ONLY - APPROVAL REQUIRED BEFORE PRODUCTION INTEGRATION**

This pass deliberately does not modify runtime code, production TMX maps, gameplay anchors, collision, encounters, rewards, or the current `region1_environment_decor.png` production asset.

## Source of truth
- Concept branch: `cardcha-alpha28-0694-region1-environment-prop-concept`
- Production baseline: `cardcha-alpha28-0693-airship-interior-density-rebuild` @ `c438d8664538e0b64212d2566f47188294effe93`
- Airship 0693 remains the current production baseline until Ron accepts the in-game Airship result.

## Why this pass exists
0692 already identified Region I / Map 1 as the next planned visual-design task after Airship work: replace the crude `region1_environment_decor.png` placeholder language with a richer Stardew-faithful, map-native prop set.

Current audit confirms the reason:
- `Region1StardewDecorRenderer` loads one 256x32 atlas containing eight 32x32 cells.
- Each Hunt Run room receives six scaled sprites selected from that atlas.
- Those sprites are painted from `Display.RenderedWorld` through `AirshipFoundationService.OnRenderedWorld`.
- That is legacy physical-world rendering debt under the repository depth contract.
- The six Hunt Run TMX maps are 28x20, vanilla-only, with empty `Front` layers and only sparse vanilla blocking shapes.
- The result is readable but visually thin, repetitive, and too dependent on post-world decoration.

0694 therefore defines the replacement language before any production map is touched.

## Locked gameplay geometry
The visual rebuild must preserve these gameplay anchors and their surrounding readable space:
- room size: 28x20 tiles;
- arrival zone: near `(14,17)` through `FindClearTileNear`;
- retreat / return anchor: `(14,18)`;
- left route choice: `(9,2)`;
- right route choice: `(19,2)`;
- boss branch anchor: `(14,2)`;
- boon choices: `(7,5)`, `(14,5)`, `(21,5)`;
- rare encounter / lost-cache focus: around `(14,10)`;
- central combat and traversal lane must remain open enough for monsters, controller movement and route readability.

No concept prop is allowed to visually impersonate one of those interaction anchors.

## Approved visual target proposed for Ron
Region I should read as **a magical Stardew forest expedition**, not a generic green arena and not a high-fantasy temple pack.

The visual grammar should stay inside Stardew's world:
- squat, readable silhouettes;
- wood, moss, roots, field stone, mushrooms and handmade trail markers;
- small magical accents instead of giant glowing architecture;
- irregular organic clustering rather than symmetric screen-wide bands;
- edge density with an intentionally breathable combat center;
- stronger room identity without making six unrelated biomes.

### Palette direction
- moss / fern green;
- dark bark and warm stump brown;
- muted field-stone gray-green;
- small cream mushroom highlights;
- restrained teal / lavender Cardcha magic only on special route or shrine props;
- no neon wash, broad procedural rectangles, or full-screen tint.

## Prop family proposal
The production set should be built as native 16px-aligned TMX tiles or compact multi-tile groups. Target: **7 core families**, with variants rather than one giant repeated object.

### P01 - Moss Root Cluster
- low roots, fern leaves, tiny ground shoots;
- 1x1 and 2x1 variants;
- primarily `Back` when purely ground-level;
- taller root tips may use `Buildings` / `Front` only where the physical footprint agrees;
- workhorse edge filler for Verdant Clearing and Hollow Grove.

### P02 - Fallen Log / Stump Workset
- stump, chopped hollow, short fallen log, log-with-mushrooms;
- 1x1, 2x1 and one 2x2 hero variant;
- warm Stardew wood colors;
- solid versions own collision through map tiles, never invisible blockers;
- used sparingly so rooms do not become obstacle mazes.

### P03 - Fern / Mushroom Forage Cluster
- ferns, clover, small mushroom rings, berry-like forest dots;
- mostly `Back`, zero collision;
- 1x1 micro-variants break repetition without gameplay noise;
- supports Verdant Clearing, Moss Creek and Briar Thicket.

### P04 - Mossy Field-Stone Ruin
- broken stone pair, cracked low wall, half-buried marker stone;
- 1x1 / 2x1 / 2x2;
- gray-green with soft moss, no cathedral silhouette;
- main identity family for Old Ruins;
- large pieces stay perimeter-biased and never wall off the center.

### P05 - Trail Sign / Expedition Marker
- handmade wood sign, tied cloth, hanging charm, tiny Cardcha route rune;
- 1x2 visual silhouette with a narrow physical base;
- supports navigation language without replacing runtime route-choice markers;
- route rune remains subtle until production interaction logic explicitly owns it.

### P06 - Briar / Hollow Growth
- thorny bush edge, root arch fragment, hollow shrub mass;
- compact 1x1 / 2x1 variants;
- darker values than P01 to create room-specific pressure;
- no large arch across player lanes;
- primary family for Briar Thicket and Hollow Grove.

### P07 - Card Shrine Relic Set
- small stone pedestal, card-shaped carved slab, offering bowl, two low rune stones;
- restrained lavender / teal highlight;
- Stardew-scale, village-handmade-meets-old-forest rather than ornate RPG altar;
- primary hero family for Card Shrine;
- central shrine composition must leave `(14,10)` usable for rare encounter semantics when that node type appears.

## Six-room identity plan
All six rooms share the same material family, but each receives a different composition signature.

### Room 1 - Verdant Clearing
**Read:** welcoming forest opening.
- P01 + P03 dominate outer edges;
- one P02 stump/log cluster in a corner;
- open center remains broad;
- density target: light-medium;
- silhouette should feel soft and rounded.

### Room 2 - Moss Creek
**Read:** damp trail beside an implied creek bed.
- P01 + P03 with elongated low ground clusters;
- P02 log fragment only at an edge, never as a fake traversable bridge;
- more blue-green plants and stones, but no screen-wide water stripe unless TMX terrain itself owns water;
- density target: medium.

### Room 3 - Old Ruins
**Read:** forest reclaiming a forgotten field structure.
- P04 is dominant;
- P01 grows into and around stone pieces;
- one P05 marker can sell the expedition route;
- asymmetrical broken-wall corners, center still combat-readable;
- density target: medium-high at perimeter, low in center.

### Room 4 - Briar Thicket
**Read:** tighter, hostile growth without shrinking combat space.
- P06 + P03 dominate;
- thorn masses sit on existing blocked / perimeter geometry first;
- no decorative briar may create a visual fake collider inside the open lane;
- density target: visually high, physically conservative.

### Room 5 - Hollow Grove
**Read:** old, shadowed grove with larger organic silhouettes.
- P01 + P02 + P06;
- one hollow stump / root hero piece on a side;
- darker bark and moss, small mushroom highlights;
- density target: medium-high, with clear central negative space.

### Room 6 - Card Shrine
**Read:** a small magical forest destination, still unmistakably Stardew.
- P07 hero cluster with P04 support stones;
- P01 / P03 soften the perimeter;
- magical color is localized to shrine details only;
- route / boss / boon anchors at north must remain visually dominant when runtime markers appear;
- density target: medium, compositionally deliberate rather than busy.

## Placement grammar
Production integration should follow these rules:

1. **Edge-first density**
   - Put most tall / solid props in outer 3-5 tile bands or on already-blocked shapes.
   - Keep the center visually calmer for combat.

2. **No six-room stamp pattern**
   - Do not reuse the current six hard-coded decor points as a template.
   - Each room receives an authored placement signature.

3. **Ground detail before tall prop**
   - Use `Back` micro-clusters to add richness cheaply.
   - Add tall `Buildings` / `Front` silhouettes only where they improve identity.

4. **Physical ownership must be honest**
   - If a prop blocks movement, its map collision footprint matches its visible base.
   - If it does not block movement, it must not visually look like a solid wall across a lane.

5. **Front layer is selective**
   - Use it for small upper foliage / branch overlap only where walk-behind behavior is intentional.
   - Do not plaster foreground over the player.

6. **Runtime markers stay readable**
   - Route, boss, boon, extraction and rare-event markers keep clear contrast and breathing space.

## Production architecture proposal for the next implementation pass
After visual approval, the implementation branch should:
- introduce a new Cardcha-owned Region I prop tilesheet with 16px tile alignment and transparency;
- attach it directly to all six `region1_rooms/*.tmx` maps;
- author room-specific `Back`, `Buildings`, and selective `Front` placements;
- migrate desired physical decor out of `Region1StardewDecorRenderer.Draw`;
- remove or suppress that physical post-world renderer once TMX coverage is complete;
- keep only legitimate VFX in `RenderedWorld`;
- freeze all gameplay anchor functions and run topology;
- keep `region1_hunting.tmx` main hub/map work separate unless a screenshot proves it also needs the same pass.

## Acceptance checklist before implementation is called visually complete
For every Hunt Run room:
- screenshot shows a distinct room identity at a glance;
- center combat lane remains readable;
- north route / boss anchors remain readable;
- south arrival / retreat remains readable;
- rare center tile is not swallowed by a hero prop;
- walk in front of a tall prop: no Z anomaly;
- walk behind intended foreground: correct partial occlusion;
- same-tile edge cases do not cover farmer incorrectly;
- controller route interaction remains easy;
- monsters do not visually disappear behind broad post-world sprites;
- save / reload does not duplicate props because physical art is map-owned;
- no `Display.RenderedWorld` physical environment art remains for these rooms.

## Explicit non-goals for 0694
- no Airship redesign;
- no Airship acceptance claim;
- no Region I gameplay rebalance;
- no new encounters, rewards or route logic;
- no boss redesign;
- no production TMX mutation before Ron approves this visual concept;
- no third-party art dependency.

## Approval decision requested
Before production integration, Ron only needs to decide whether this overall Region I language is correct:

> **Stardew forest expedition with denser organic perimeter props, room-specific identities, small handmade / magical accents, and an intentionally open combat center.**

If approved, the next production pass should build the real tilesheet and migrate the six room compositions into TMX while deleting the legacy physical post-world decor path.
