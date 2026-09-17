# 0696D3-G Asset Separation + Natural Collision + Daylight Recovery

Updated: 2026-09-18

Repository: `ronvotri/Cardcha-Shardbound`
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`

## Status

**NEXT IMPLEMENTATION / RUNTIME AUTHORITY**

D3-F static validation, Release compile, package audit, and prerelease publication all passed, but Ron's 2026-09-18 in-game retest demonstrates that D3-F is **RUNTIME FAIL**.

Do not call Runtime PASS until Ron tests a new D3-G package in Stardew Valley and explicitly confirms the runtime acceptance criteria below.

## Authority

This document records Ron's newest runtime feedback from six in-game screenshots captured after testing the D3-F TEST package. This runtime evidence overrides any older D3-D, D3-E, or D3-F assumption that conflicts with it.

Do not restart D2. Do not redo D3-A/B/C/D/E/F. D3-F remains historical provenance only. Continue incrementally from the current branch with D3-G.

## D3-F provenance

Successful D3-F workflow run: `35247550568`

Successful D3-F job: `105291478417`

D3-F workflow/source package commit: `76471e8de7160449d882dfc416b15c34d4db61ea`

D3-F source-fix commit: `d3c35cb595ef32f3f9970f747c3bfd4a84fe2a79`

D3-F prerelease tag: `cardcha-0696d3f-test-76471e8d`

D3-F release ID: `390886558`

D3-F package:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.70_0696D3F_PhysicalBlockingTravelDepthRecovery_TEST.zip`

D3-F package asset ID: `570641822`

D3-F package SHA256:
`7811763b5a8263f13dc5cb11d9dad6657223cbb7529a0e4c423591ed11f998f4`

D3-F proved that the project can compile/package and that upgrade/travel affordances can be surfaced. It did **not** prove runtime visual/collision acceptance.

## Ron runtime failures after D3-F

### 1. Room 1 blocker implementation causes a ghost/body desync effect

When the player moves into newly blocked visual footprints, the movement/visual correction behaves unnaturally: the moving shadow/ghost-like visual continues while the Farmer body appears held behind. This is visibly wrong and must not be normalized as acceptable collision behavior.

D3-G must remove the coarse forced-position blocker approach. Collision should feel native to Stardew and be owned by map collision wherever possible.

### 2. Room 2 still has two giant props that blanket-overlay the player

The two largest visual masses remain wrong in runtime:

- the large upper Observation Window / shell composition;
- the large central navigation-console / helm workstation.

They still read as floating foreground slabs that cover the Farmer rather than grounded room architecture with correct front/back relationships.

D3-G must not solve this by replaying one giant runtime overlay before or after the Farmer. The assets/layers need to be split and authored into the correct map-depth ownership.

### 3. Navigation console is still NOT background-separated

Ron explicitly rejected the current presentation again: the central console still carries a large opaque light beige/yellow rectangular background behind the machine.

This is not the `RadarBackground` runtime layer anymore. D3-E already stopped rendering `state.RadarBackground`, and D3-F attempted to clear base console tiles at runtime, yet the opaque rectangle remains in game.

Therefore D3-G must treat this as an **asset/map authoring problem**, not another runtime masking problem.

Required direction:

- inspect the actual RGBA/alpha of `navigation_console_base.png` and `console_runtime/navigation_console_frame.png`;
- create/use a genuinely transparent cleaned console asset;
- remove the beige/yellow backing from the production sprite itself;
- update TMX tile usage/layers accordingly;
- keep only intended machine pixels plus radar animation;
- do not rely on a runtime tile-clearing hack as the production fix.

### 4. Lamp visually intersects the travel gate

A signal lamp/column overlaps or appears to pass through the travel gate. The composition looks physically impossible.

D3-G must move, remove, or re-layer that lamp so the gate is visually clean. The travel gate is the higher-priority landmark.

### 5. Daytime Airship room remains too dark

Even during daytime the room reads nearly as dark as night. Window time-of-day state alone is not enough.

D3-G must identify the actual room/location lighting/tint source and make the overall bridge room visibly lighter during daytime while retaining atmospheric evening/night states.

Do not fake this solely by brightening the Window image.

### 6. Outdoor gate still allows walking through visually solid sections

Ron wants selective blocking for the solid wood/post segments. The player should not walk straight through obvious solid parts of the gate, but the center passage must remain usable.

D3-G must use conservative segmented collision:

- block solid left/right posts and clearly solid wood sections;
- preserve the intended central lane;
- avoid one large rectangular blocker;
- avoid forced repositioning that creates the Room 1 ghost/body effect.

## Improvements from D3-F that must be preserved

- Four upgrade stations are now visible.
- Upgrade affordances are visible and interactions must remain usable.
- A visible `TRAVEL` affordance exists and should remain understandable.
- Travel/radar gameplay handler wiring must remain intact unless a cleaner single-authority interaction route is introduced.
- D3-E/D3-F radar runtime layers should not restore the rejected opaque yellow/static radar backing.

## D3-G implementation direction

### A. True console asset separation

Inspect the source PNGs pixel/alpha data first. Materialize a cleaned transparent navigation-console body. If the current base image is flattened against a beige matte, remove the matte into alpha and preserve only intended machine pixels.

Recommended production split:

1. console body/base on a grounded map layer such as `Buildings` / `Buildings2` as appropriate;
2. only a narrow true front lip/foreground portion on `Front` / `Front2` if needed for natural player occlusion;
3. radar glow/sweep/pings remain runtime animation over the transparent/map-native console body;
4. no full-console runtime overlay.

### B. Proper Room 2 layer ownership

Re-author the two giant Room 2 props rather than patching their entire draw call around Farmer rendering.

The Observation Window/shell should behave as room architecture. Only pixels that physically belong in front of a Farmer should be on a front layer.

The central console should have a grounded collision footprint and a small, deliberate front occlusion area at most. The whole workstation must never blanket-cover the player.

### C. Native/natural collision

Prefer TMX-native collision through the existing `Buildings` layer / Cardcha blocker tile contract (`CardchaCollision0690`, tile 5400) instead of runtime correction of `Game1.player.Position`.

Use narrow footprints that correspond to the visible solid base of each object. Do not block empty visual space above tall sprites.

Room 1 should allow natural movement around the notice board, bench, cargo, and boarding gate without the D3-F ghost/body desync artifact.

### D. Gate composition and collision

Outdoor gate:
- block only solid posts/segments;
- leave the central entrance clear;
- keep interaction/transition reachable.

Interior travel gate:
- remove/reposition the intersecting lamp;
- keep the gate visually dominant and readable;
- retain travel affordance without clutter.

### E. Daylight recovery

Trace the room lighting source in code/map/runtime state. D3-G needs an explicit daytime bridge-lighting contract, for example:

- morning/noon: clearly brighter room ambience;
- evening: warmer/dimmer transition;
- night: current atmospheric dark presentation is acceptable if readable.

The exact implementation should follow Stardew's location-lighting mechanics rather than painting a giant translucent rectangle over the room.

## D3-G runtime acceptance criteria

1. Room 1 collision feels native. No ghost/shadow movement while the Farmer body is pinned behind.
2. The central navigation console has a genuinely transparent background. No beige/yellow rectangle remains around it.
3. The two giant Room 2 props no longer blanket-overlay the player.
4. Player can move naturally around Room 2, with only believable solid-base collision and deliberate foreground occlusion.
5. All four upgrade stations remain visible and interactable.
6. Travel remains visible and actionable.
7. The lamp no longer visually passes through the travel gate.
8. Daytime bridge interior is visibly lighter than night.
9. Outdoor gate solid posts/wood cannot be walked through, while the intended center passage remains usable.
10. No interaction becomes reachable through obvious walls or from absurd distance as a side effect.
11. Only Ron's successful in-game retest can change D3-G to Runtime PASS.

## CI / packaging constraints

- Continue using GitHub-hosted Ubuntu workflow. Do not switch to self-hosted runner unless Ron explicitly asks later.
- GitHub Actions artifact storage quota was full during D3-E/D3-F, so publish TEST packages through a GitHub prerelease while that remains true.
- Static validator, compile, package audit, and prerelease publication may be reported separately as PASS if actually verified.
- None of those are Runtime PASS.

## Next implementation order

1. Inspect console PNG alpha/background and materialize the cleaned transparent asset.
2. Re-author console and Observation Window map layer ownership.
3. Replace D3-F forced runtime blocker/reposition logic with native TMX collision footprints.
4. Fix outdoor gate segmented collision and interior gate/lamp composition.
5. Implement daytime bridge lighting recovery.
6. Preserve/verify all four upgrade stations and travel interaction.
7. Add a D3-G validator that rejects the stale D3-E full-overlay architecture and the D3-F forced-position blocking architecture.
8. Build and publish a fresh D3-G TEST prerelease.
9. Keep status `RUNTIME RETEST REQUIRED` until Ron tests in game.

## Resume instruction

Resume from **0696D3-G**, using this document and Ron's 2026-09-18 screenshots as current authority.

Do not restart D2 or redo D3-A/B/C/D/E/F. Do not attempt another runtime-only mask for the console beige background. Do not retain forced player-position correction as the collision solution. Fix the source asset, map layers, native collision, gate composition, and room lighting at their actual ownership layers.
