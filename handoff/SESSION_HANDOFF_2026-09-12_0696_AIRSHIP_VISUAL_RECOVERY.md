# Cardcha 0696 Airship Visual Recovery — Session Handoff

Date: 2026-09-12
Status: WIP, visual acceptance is **PENDING-RON-IN-GAME**

## 1. Resume point

Continue on branch:

`cardcha-alpha28-0696-airship-concept-faithful-visible-integration`

Branch head at the moment this handoff was prepared:

`22b340df59e6d10e27335e02384a3b992ef5208f`

Latest two 0696 audit commits before this handoff:

- `aaef538641948ef6e76a79861b3c58d5320b68ba` — `audit: add 0696 Airship Set01 full-footprint audit`
- `22b340df59e6d10e27335e02384a3b992ef5208f` — `ci: run 0696 Airship Set01 full-footprint audit`

The audit implementation is:

`tools/alpha28_0696_airship_set01_full_footprint_audit.py`

The CI workflow is:

`.github/workflows/cardcha-alpha28-0696-airship-set01-full-footprint-audit.yml`

The audit is intentionally evidence-only. It does not edit TMX or artwork. It measures Set01 Redux assets, resolves their production TMX tilesets, and checks whether occupied 16x16 source cells are represented as coherent full-footprint placements on runtime-visible map layers.

Expected audit evidence paths when run:

- `handoff/AIRSHIP_SET01_FULL_FOOTPRINT_AUDIT_0696.json`
- `handoff/ALPHA28_0696_AIRSHIP_SET01_FULL_FOOTPRINT_AUDIT.md`
- `handoff/AIRSHIP_SET01_FULL_FOOTPRINT_AUDIT_0696.png`

Do **not** infer visual acceptance from the audit or CI result.

## 2. Production baseline that must remain recoverable

Production/test baseline is still 0695:

Branch:

`cardcha-alpha28-0695-region1-prop-integration`

Build:

`0.3.0-alpha.28.0.4.14.4.5.12.61`

Materialized source:

`39e13a370281b29f77d94be497603a3243edda41`

Successful CI run:

`34655852302`

Artifact ID:

`10285408808`

Artifact SHA256:

`065ed6936c5d06479eb2927a7c2b717d359a598447f3b9f6e5c35bc57221bbac`

Inner TEST ZIP SHA256:

`fac7aaa1c9014aedfd0eba887a1b2bd46531fbb9f676ebd7896b15e321fce726`

0695 Region I technical integration passed, but its visual acceptance remains pending unless Ron explicitly confirms it in game.

## 3. Why 0696 exists

0693 Airship was technically packaged and validated, but Ron's in-game screenshots showed both Airship rooms still nearly empty compared with the approved concepts.

0693 branch:

`cardcha-alpha28-0693-airship-interior-density-rebuild`

Build:

`0.3.0-alpha.28.0.4.14.4.5.12.60`

Materialized source:

`e235e33826dddbf158837d3f5cdbc6af505136b6`

Successful CI run:

`34631829934`

Artifact ID:

`10275959178`

Inner TEST ZIP SHA256:

`7c7e572bec7ba682a91af519482922e6ec9cb80677ae1d731002fd83d2d0c649`

**Visual verdict: FAILED / NOT ACCEPTED.**

The approved concept composition was not the problem. The integration path was.

## 4. Root cause already established

`tools/alpha28_0693_airship_interior_density_rebuild.py` sliced the approved room-density imagery into 16x16 chunks and placed those GIDs mainly onto a custom TMX layer named `BackDecor` in:

- `src/Cardcha/assets/airship_deck.tmx`
- `src/Cardcha/assets/sky_dock_interior.tmx`

The package and validators could therefore prove that assets and GIDs existed, while Ron's actual game still did not show the intended room density.

Permanent lesson:

> asset exists + GIDs exist in TMX != player sees it in game

Do not assume an arbitrary custom layer is runtime-visible merely because it is present in TMX.

Current Stardew map research used for 0696:

- `Back` for terrain/basic background
- `Buildings` for physical/solid map objects and collision ownership
- `Paths` for path/flooring type layers
- `Front` for actor-aware foreground/upper object portions
- `AlwaysFront` only for deliberate always-over-player foreground
- extra visual render layers should use supported vanilla-layer naming/offset conventions such as `Back2`, `Buildings2`, `Front2` when appropriate
- map tile cell is 16x16

Collision and tile properties must not be delegated to a decorative suffix layer when the base layer is the actual gameplay owner.

## 5. Approved Airship composition target

The full-room concept remains the composition reference. Individual approved sprite PNGs are the production art source-of-truth.

### Airship Deck

Target composition:

- large bookshelf / work library on the left
- observation/nav panels across upper center/right
- telescope/workstation on far right
- substantial helm/desk/console cluster around center-upper area
- large purple Cardcha rug/table/console in center
- cabinets, carts, plants and lived-in perimeter detail
- clear routes to exits and gameplay anchors

The room must feel dense around the perimeter without turning the central walk route into clutter.

### Sky Dock

Target composition:

- substantial departure/schedule board and service desk cluster on the left
- waiting bench/table nook lower-left
- purple runway/spine through the center
- large authored boarding/window/gate structure on the right
- luggage/cargo cluster lower-right
- plants and station details throughout
- useful negative space, but never the huge empty-floor look from the rejected in-game screenshots

Reference documents already in repo:

- `handoff/AIRSHIP_VISUAL_DIRECTION_APPROVED.md`
- `handoff/ALPHA28_0690_AIRSHIP_INTERIOR_VISUAL_REBUILD.md`
- `handoff/ALPHA28_0691_AIRSHIP_PROP_SET02_HARBOR_FURNISHINGS.md`
- `handoff/ALPHA28_0692_AIRSHIP_RGBA_GATE_RESTORE.md`
- `handoff/ALPHA28_0693_AIRSHIP_INTERIOR_DENSITY_REBUILD.md`

## 6. Exact sprite rule for 0696

Ron explicitly wants the separated authored sprites to be used rather than a tiny clustered reinterpretation.

Known Set01 Redux source files include:

- `boarding_gate_arch.png`
- `cargo_parcel_crate.png`
- `collision_blocker.png`
- `navigation_console_base.png`
- `navigation_console_overlay_1.png` through overlay variants
- `observation_window_base.png`
- `observation_window_overlay_1.png` through overlay variants
- plus the remaining Set01 Redux files in `src/Cardcha/assets/airship_props/set01_redux/`

The current audit also treats these static families as production evidence targets where applicable:

- `route_notice_board.png`
- `boarding_gate_arch.png`
- `signal_lamp.png`
- `cargo_parcel_crate.png`
- `observation_window_base.png`
- `navigation_console_base.png`
- `collision_blocker.png`

Overlays are runtime-owned where intentionally animated. Do not convert moving/VFX overlays into physical collision art.

## 7. Scale and footprint contract

A large sprite is allowed to be a large multi-tile prop. Do not redesign it just to force it into one or two map cells.

For every authored sprite:

1. preserve original silhouette, palette, materials and detail hierarchy;
2. calculate original dimensions and alpha bounds;
3. crop only meaningless transparent padding while preserving its anchor;
4. pad to the 16px grid if needed without changing art scale;
5. determine intended world footprint from the composition;
6. split depth logically across supported map layers;
7. put collision only on physical contact/support cells;
8. keep walk-through openings genuinely passable;
9. use nearest-neighbor resize only if a resize is truly necessary and explicitly survives style review;
10. if a different size is needed but scaling damages the style, author a proper size-specific variant rather than auto-reinterpreting the design.

Example: an approximately 112x96 boarding gate should be treated as roughly a 7x6 visual footprint. Its side posts/bollards can block, its central opening stays passable, and the high arch/banner portion can live on a foreground layer. Do not shrink the entire gate into a toy-sized prop.

## 8. Rendering architecture contract

Physical environment art must be map/TMX/native world art.

`RenderedWorld` is for VFX/animated overlays only.

Never restore missing physical furniture by drawing it again in `Display.RenderedWorld`.

Recommended 0696 split:

- floor/rug details: `Back2` where appropriate
- nonblocking body/decor behind actor: supported building-order visual layer such as `Buildings2` where appropriate
- real collision/contact cells: base `Buildings`
- tall upper sections that should occlude correctly: `Front` / `Front2`
- rare deliberate foreground only: `AlwaysFront`

The exact layer choice must be verified against the actual Stardew/xTile runtime behavior, not guessed from XML existence.

## 9. What NOT to do next session

- Do not declare 0696 complete because CI is green.
- Do not claim the rooms match concept without Ron testing them in game.
- Do not mechanically move every `BackDecor` tile to `Buildings`/`Front` and treat that as the final architecture.
- Do not flatten the full-room concept bitmap into a replacement for the separated sprite source pack.
- Do not arbitrarily redraw, simplify or shrink authored props.
- Do not use runtime `RenderedWorld` to fake missing physical room decor.
- Do not use `collision_blocker.png` as though it were a single multi-tile authored furniture sprite. It is a repeated collision primitive.
- Do not let validators pass merely because a file or GID exists. They must validate actual visible footprint, room side, scale and supported rendering layers.

## 10. Source-pack state at chat boundary

Ron uploaded two RAR archives during the session:

- `concept(1).rar`
- `sprite(1).rar`

The session environment could list their RAR5 headers but could not extract them because no working `unrar`, `7z`, `unar` or `bsdtar` was available and the environment had no internet package retrieval.

Header inventory:

- concept archive: 6 PNGs
- sprite archive: 22 PNGs

If those exact images are needed in a future session and are not otherwise present in repo, ask Ron to upload the same two folders as ZIP. Do not ask him to rename them.

Once ZIP is available, inventory every PNG with dimensions, mode, alpha bbox, nontransparent pixel count and SHA256, then visually classify them before changing the map.

## 11. Planned authoritative 0696 data model

Create or update these machine-readable files before final integration:

`handoff/AIRSHIP_SOURCE_PACK_0696.json`

For each asset record:

- source file
- SHA256
- original dimensions
- alpha visual bounds
- preserved anchor/padding
- proposed tile footprint
- scale factor, ideally 1.0
- room
- exact placement x/y
- layer slices
- collision cells
- animation overlays
- concept reference
- status: exact / needs-crop / needs-authored-resize / missing / stale

And:

`handoff/AIRSHIP_ROOM_BLUEPRINT_0696.json`

This should lock the two room compositions, prop identities, exact anchors, walk routes, collision topology and depth ownership.

No silent substitute assets.

## 12. Preview/validation requirement before Ron tests

Build a preview renderer/validator for the actual TMX visual layers before packaging.

It should fail before packaging if it detects obvious problems such as:

- missing hero props
- prop footprint far smaller than source/blueprint expectation
- wrong side of room
- large unexpected empty zones relative to blueprint
- unsupported/non-rendering layer ownership
- lost walk-through openings
- collision rectangle covering decorative transparent/upper pixels

The goal is to catch another “beautiful concept in package, empty room in game” failure before Ron has to discover it manually.

## 13. Permanent guides that MUST be read first

Before any sprite/map/actor visual work, read:

- `AGENTS.md`
- `CARDCHA_SPRITE_PRODUCTION_GUIDE.md`
- `CARDCHA_MAP_ROOM_CONSTRUCTION_GUIDE.md`
- `CARDCHA_CHARACTER_CREATURE_STYLE_GUIDE.md`

For Mimi/ChaCha style work also read:

- `handoff/MIMI_CHACHA_STYLE_REWORK_CHECKLIST.md`

These are repo-wide contracts, not suggestions.

## 14. Recommended first actions in the next chat

1. Checkout/read branch `cardcha-alpha28-0696-airship-concept-faithful-visible-integration` and this handoff.
2. Read the permanent visual guides and `AIRSHIP_VISUAL_DIRECTION_APPROVED.md`.
3. Inspect the current Set01 full-footprint audit script/workflow and retrieve its latest run/evidence if available.
4. If Ron supplies ZIP source packs, inventory all 28 images before map edits.
5. Build `AIRSHIP_SOURCE_PACK_0696.json`.
6. Build `AIRSHIP_ROOM_BLUEPRINT_0696.json` using approved concept composition and historical 0690/0691 anchors where valid.
7. Rewrite/refine 0696 integration to use exact separated sprites on runtime-supported Stardew layers with selective base-layer collision.
8. Add preview composition/footprint validation.
9. Only then package a TEST build.
10. Ron tests both Airship rooms in game. Only Ron's explicit approval changes visual status from PENDING to PASS.

## 15. Acceptance status at handoff

- 0695 Region I technical: PASS
- 0695 Region I visual: PENDING
- 0693 Airship technical/package: PASS historically
- 0693 Airship visual: FAILED / NOT ACCEPTED
- 0696 Airship audit infrastructure: PRESENT
- 0696 Airship final integration: WIP
- 0696 Airship visual: PENDING-RON-IN-GAME

Do not collapse these statuses into a single “done” flag.
