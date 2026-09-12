# LATEST CARDCHA HANDOFF

Updated: 2026-09-12

## Current workstream

Continue on:

`cardcha-alpha28-0696-airship-concept-faithful-visible-integration`

The authoritative next-session handoff is:

`handoff/SESSION_HANDOFF_2026-09-12_0696_AIRSHIP_VISUAL_RECOVERY.md`

Read that file first before changing Airship assets, maps, placement, collision or validation.

## 0696 status

Airship 0696 is **WIP**.

Visual acceptance is:

`PENDING-RON-IN-GAME`

Do not call 0696 visually complete based on CI, package validation, file existence or TMX GID presence.

Current audit infrastructure on this branch:

- `tools/alpha28_0696_airship_set01_full_footprint_audit.py`
- `.github/workflows/cardcha-alpha28-0696-airship-set01-full-footprint-audit.yml`
- audit commit `aaef538641948ef6e76a79861b3c58d5320b68ba`
- CI wiring commit `22b340df59e6d10e27335e02384a3b992ef5208f`

The audit is evidence-only and must not be confused with production integration.

## Airship visual recovery rule

0693 was technically packaged but visually rejected because the approved room-density art was placed primarily on custom TMX `BackDecor`, while Ron's in-game screenshots still showed sparse/empty rooms.

Permanent lesson:

> asset exists + GIDs exist in TMX != player sees it in game

0696 must be rebuilt source-first:

- full-room concept = composition reference
- separated approved sprite PNGs = production art source-of-truth
- preserve authored style and multi-tile footprints
- use runtime-supported Stardew map layers/depth ownership
- base `Buildings` owns real collision cells
- supported visual suffix layers may carry nonblocking/depth art where appropriate
- `Front`/`Front2` for upper occluding portions where appropriate
- `RenderedWorld` remains VFX/animated-overlay only, never physical furniture recovery
- no blanket `BackDecor` -> `Buildings/Front` migration as the final architecture
- no arbitrary shrinking/redrawing of authored props

Planned authoritative data files:

- `handoff/AIRSHIP_SOURCE_PACK_0696.json`
- `handoff/AIRSHIP_ROOM_BLUEPRINT_0696.json`

Before packaging a TEST build, add preview/footprint validation capable of catching missing hero props, tiny scaling, wrong-side placement, unsupported layers, large unexpected empty zones and broken walk-through/collision topology.

## Source-pack note

During the previous chat Ron supplied `concept(1).rar` and `sprite(1).rar` containing 6 concept PNGs and 22 sprite PNGs. The chat environment could list RAR5 entries but could not extract them due to missing RAR tools.

If those exact files are not already recoverable from repo in the next session, ask Ron to upload the same folders as ZIP, with no rename required. Inventory the files before map edits.

## Production/test baseline

0695 remains the recoverable production/test baseline:

Branch:
`cardcha-alpha28-0695-region1-prop-integration`

Build:
`0.3.0-alpha.28.0.4.14.4.5.12.61`

Materialized source:
`39e13a370281b29f77d94be497603a3243edda41`

Handoff:
`handoff/ALPHA28_0695_REGION1_ENVIRONMENT_PROP_PRODUCTION_INTEGRATION.md`

Successful CI run:
`34655852302`

Artifact ID:
`10285408808`

Artifact SHA256:
`065ed6936c5d06479eb2927a7c2b717d359a598447f3b9f6e5c35bc57221bbac`

Inner TEST ZIP SHA256:
`fac7aaa1c9014aedfd0eba887a1b2bd46531fbb9f676ebd7896b15e321fce726`

0695 Region I technical status: PASS

0695 Region I visual status: PENDING unless Ron explicitly confirms it in game.

## Historical Airship evidence

Read as needed:

- `handoff/AIRSHIP_VISUAL_DIRECTION_APPROVED.md`
- `handoff/ALPHA28_0690_AIRSHIP_INTERIOR_VISUAL_REBUILD.md`
- `handoff/ALPHA28_0691_AIRSHIP_PROP_SET02_HARBOR_FURNISHINGS.md`
- `handoff/ALPHA28_0692_AIRSHIP_RGBA_GATE_RESTORE.md`
- `handoff/ALPHA28_0693_AIRSHIP_INTERIOR_DENSITY_REBUILD.md`

0693 historical build:
`0.3.0-alpha.28.0.4.14.4.5.12.60`

0693 materialized source:
`e235e33826dddbf158837d3f5cdbc6af505136b6`

0693 CI:
`34631829934`

0693 artifact ID:
`10275959178`

0693 inner TEST ZIP SHA256:
`7c7e572bec7ba682a91af519482922e6ec9cb80677ae1d731002fd83d2d0c649`

0693 visual status: **FAILED / NOT ACCEPTED**.

## Mandatory repo-wide visual guides

Before visual production work, read:

- `AGENTS.md`
- `CARDCHA_SPRITE_PRODUCTION_GUIDE.md`
- `CARDCHA_MAP_ROOM_CONSTRUCTION_GUIDE.md`
- `CARDCHA_CHARACTER_CREATURE_STYLE_GUIDE.md`

For Mimi/ChaCha style work also read:

- `handoff/MIMI_CHACHA_STYLE_REWORK_CHECKLIST.md`

Core acceptance rule across all of them:

**technical PASS != visual PASS**

Only Ron's explicit in-game visual acceptance closes a visual task.
