# Alpha 28 / 0696A — Airship Visible Architecture Recovery

## Status
- Branch: `cardcha-alpha28-0696-airship-concept-faithful-visible-integration`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.62`
- Materialized source head: `e6d84d22e59030dc38eb37902d32424d50902814`
- Authoritative successful workflow run: `34685463138`
- Artifact ID: `10295536254`
- Artifact digest: `sha256:46fa1682ebebcc7aae0c03d2126c6bc6001b51a87e01d9fab3d831ab8b27d7f6`
- Verified inner TEST ZIP SHA256: `b22a90d02a8835d87b7b54206bf0362af07ae898ead3ddb358fd0ae1ff022301`
- Technical scope: repo-recovered approved Set01 + Set02 physical art only
- Technical validation: **PASS**
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

## Exact recovered production coverage
### Airship Deck
- Observation Window: 50 / 50 occupied source cells represented.
- Navigation Console: 35 / 35.
- Left Signal Lamp: 6 / 6.
- Right Signal Lamp: 6 / 6.
- Blueprint collision cells: 14.

### Sky Dock
- Route Notice Board: 25 / 25.
- Departures Schedule Board: 24 / 24.
- Signal Lamp: 6 / 6.
- Boarding Gate: 42 / 42.
- Waiting Bench: 18 / 18.
- Luggage Cart: 16 / 16.
- Cargo Parcel Crate: 9 / 9.
- Blueprint collision cells: 50.
- Gate walk-through opening independently inspected in the packaged TMX: no nonzero base `Buildings` tiles in x=21..25, y=5..8.

## Runtime layer contract now materialized
Both Airship maps now contain:
`Back`, `Back2`, `Buildings`, `Buildings2`, `Front`, `Front2`.

`BackDecor` is absent from production maps and marked deprecated for Airship physical art.

The full-room 0693 density tilesets are absent from the packaged Airship maps.

## Validation evidence
The authoritative 0696A workflow passed:
- exact repo-source inventory: 18 exact assets, 0 missing;
- source-first TMX integration;
- repository render-depth contract;
- exact footprint / anchor / depth-layer validator;
- collision and protected-lane validator;
- deterministic Deck and Sky Dock previews;
- unrelated boss / Region freeze;
- SMAPI compile;
- package audit;
- artifact upload.

The downloaded workflow artifact was independently unpacked after CI. The inner TEST ZIP SHA256 matched its `.sha256` file exactly. Packaged manifest version is `.62`; `Cardcha.dll` has a valid PE header and is 1,019,392 bytes.

## TEST package
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.62_0696A_AirshipVisibleArchitectureRecovery_TEST.zip`

SHA256:
`b22a90d02a8835d87b7b54206bf0362af07ae898ead3ddb358fd0ae1ff022301`

## Source gap
The previous session recorded `concept(1).rar` (6 PNGs) and `sprite(1).rar` (22 PNGs), but those exact external source packs are not recoverable from the repo. 0696A does not invent replacements. Missing approved library/telescope/rug/service-detail zones remain explicitly pending in `handoff/AIRSHIP_ROOM_BLUEPRINT_0696.json`.

## Acceptance rule
This build proves the rendering architecture and exact recovered prop footprints. It **cannot** be called the final 0696 visual pass until Ron tests it in game and the missing approved source pack is restored for the remaining composition.

Technical PASS does not imply visual acceptance.
