# Alpha 28 0690 — Airship Interior Visual Rebuild

## Source of truth
- Current implementation branch: `cardcha-alpha28-0690-airship-interior-visual-rebuild`
- Materialized source head: `181935d7b167a5e99986d237b637fa6de8dddd26`
- Materialized tree: `0de8d099498aa104d8f10b40e1551f50d0a06d55`
- Parent source-of-truth: `cardcha-alpha28-0688-hollow-curator-visual-identity-rebuild` @ `55157c903f0e45cd29df2711ac8e12b32d8fbb4f`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.57`
- Important: do **not** base future work on the rejected 0689 small-sprite prototype branch.

## Purpose
Replace the temporary/vanilla-looking Airship Deck + Sky Dock furniture language with the approved Cardcha wood/brass/purple/teal visual identity while respecting the repository rendering-depth contract.

## Approved visual direction
See `handoff/AIRSHIP_VISUAL_DIRECTION_APPROVED.md` before doing more Airship work.

Core direction:
- rich Stardew-style pixel furniture with clear outline/stroke, layered shading and readable materials;
- warm wood + brass/gold + purple Cardcha cloth + restrained teal light;
- hero props may use larger footprints instead of being forced into tiny icon-like sprites;
- do not create tiny art and upscale it as the production solution;
- dense detail is welcome as long as silhouettes and gameplay readability remain clear.

## 0690 Set 01 — integrated
- Route Notice Board: map-native physical art.
- Boarding Gate Arch: map-native physical art with open center lane.
- Signal Lamp: map-native physical art.
- Cargo Parcel Crate: map-native physical art.
- Observation Window: map-native body + 4 transparent moving-sky overlays.
- Navigation Command Console: map-native body + 4 transparent screen-state overlays.

Asset library:
`src/Cardcha/assets/airship_props/set01_redux/`

The two animated hero props keep their physical body fixed. Only sky/screen pixels animate.

## Rendering contract
- Static physical art is owned by `airship_deck.tmx` / `sky_dock_interior.tmx`.
- Runtime only draws transparent/transient sky, screen and glow pixels.
- Physical Airship props must not be reintroduced through `RenderedWorld`.
- Old 0677 vanilla furniture clutter is cleared from these two rooms.
- Boss and Region content inherited from 0688 is frozen by CI.

## Layout
### Sky Dock
- Route/service identity on the left.
- Boarding identity on the right.
- Center arrival/exit spine preserved.
- Route interaction and boarding bay remain reachable/readable.

### Airship Deck
- Observation wall at the top.
- Navigation console is the main hero/work prop.
- Lower doorway and central movement path preserved.
- Existing gameplay/upgrade sockets remain reachable.

## Approved but not yet integrated
The session also approved a broader Airship prop library for later passes. These are not production-integrated in 0690:
- Ticket Pedestal / ticket counter
- Route Map Plaque
- Dock Mooring Post
- Waiting Bench
- Route Control Desk
- Card-emblem parcel/mail locker
- Departures Schedule Board
- Luggage Cart
- Telescope / Observation Stand
- Tea Service Cart
- Airship Bookshelf / travel library
- Baggage Scale
- Station Clock + Bell
- Decorative folding screen
- Gramophone cabinet
- Mail/key cubby/locker

Future passes should choose a restrained subset. Do not cram the whole library into both rooms.

## CI / package
GitHub Actions run: `34615697771`

Workflow result: **SUCCESS**
- asset materializer: PASS
- TMX integration: PASS
- rendering-depth validator: PASS
- 0690 visual validator: PASS
- inherited Boss/Region freeze: PASS
- SMAPI build environment: PASS
- `dotnet build`: PASS
- package audit: PASS
- artifact upload: PASS

Artifact:
- ID: `10269809780`
- name: `cardcha-alpha28-0690-airship-interior-visual-rebuild`
- artifact digest: `sha256:9ed13547219a7548fae789618c324016e8942efee82b03e548c1f96041cb4c1d`

Inner TEST package:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.57_0690_AirshipInterior_VisualRebuild_TEST.zip`

Verified inner ZIP SHA256:
`ececc5136b0fcb13a5c6d45921acfc42ccca7098d12c34ed5bdb620d033bd142`

## Acceptance state
CI/compile/package validation is complete. **In-game visual acceptance remains pending** because Ron temporarily could not test and intends to test later.

Do not claim that 0690 has been visually accepted in-game until Ron actually reports the result.

## Next-session continuation
Before editing, read:
1. `AGENTS.md`
2. `handoff/LATEST_CARDCHA_HANDOFF.md`
3. this file
4. `handoff/AIRSHIP_VISUAL_DIRECTION_APPROVED.md`
5. `render_depth_audit.json`

If Ron says to continue immediately, the natural next build is:
`0691 — Airship Prop Set 02 / Harbor Furnishings Integration`

Keep it focused, map-native and composition-driven. After CI success, download the GitHub Actions artifact, extract the actual inner TEST ZIP, verify it, and attach that ZIP directly in chat.
