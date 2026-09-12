# Alpha 28 / 0696A — Airship Visible Architecture Recovery

## Status
- Branch: `cardcha-alpha28-0696-airship-concept-faithful-visible-integration`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.62`
- Technical scope: repo-recovered approved Set01 + Set02 physical art only
- Visual acceptance: **PENDING-RON-IN-GAME**
- Full 0696 composition: **WIP / external source pack still pending**

## What 0696A fixes
- removes production dependence on custom `BackDecor`;
- removes the rejected 0693 full-room density atlas from active map placement;
- points production tilesets back to the exact separated approved source PNGs already present in repo;
- restores complete native-size footprints at their approved historical anchors;
- uses `Buildings2` for nonblocking physical art behind actors;
- uses `Front2` only for upper depth/occlusion slices;
- keeps gameplay collision on base `Buildings` through the transparent collision primitive;
- preserves the boarding-gate center opening and Sky Dock x=14..16 travel spine;
- keeps Observation Window / Navigation Console runtime overlays VFX-only.

## Source gap
The previous session recorded `concept(1).rar` (6 PNGs) and `sprite(1).rar` (22 PNGs), but those exact external source packs are not recoverable from the repo. 0696A does not invent replacements. Missing approved library/telescope/rug/service-detail zones remain explicitly pending in `handoff/AIRSHIP_ROOM_BLUEPRINT_0696.json`.

## Acceptance rule
This build can prove the rendering architecture and exact recovered prop footprints. It **cannot** be called the final 0696 visual pass until Ron tests it in game and the missing approved source pack is restored for the remaining composition.
