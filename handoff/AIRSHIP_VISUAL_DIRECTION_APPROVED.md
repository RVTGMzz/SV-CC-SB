# Airship Visual Direction — Approved

This file captures the visual direction approved by Ron during the 0690 Airship work so a new chat/session can continue without falling back to the rejected prototype look.

## Source of truth
- Current implementation branch: `cardcha-alpha28-0690-airship-interior-visual-rebuild`
- Current materialized head: `181935d7b167a5e99986d237b637fa6de8dddd26`
- Current build: `0.3.0-alpha.28.0.4.14.4.5.12.57`
- Parent source-of-truth: 0688 at `55157c903f0e45cd29df2711ac8e12b32d8fbb4f`
- Do **not** use the 0689 small-sprite prototype branch as a base. Its tiny/native-16px approach was explicitly rejected.

## Approved Stardew fidelity target
Ron provided an in-game Stardew interior reference and rejected props that looked like simplified icons/placeholders. The approved direction is:
- Rich, layered pixel art with readable outlines/strokes.
- Strong material separation: warm wood, brass/gold hardware, cloth, glass, paper, foliage.
- Clear inner shading and highlight hierarchy, not flat blocks.
- Dense but readable detailing comparable to high-quality Stardew interior furniture.
- Cardcha identity accents: purple cloth/banners, brass/gold trim, teal magical/technical light.
- Large props may use larger footprints. Do not force important objects into 1x1/2x2 if that destroys their detail.
- Do not draw tiny art first and upscale it as the production solution. Preserve the approved large-detail look and integrate at an appropriate world footprint.
- Silhouette and depth must remain readable at gameplay zoom.

## Animation direction
Two hero props are deliberately alive, not static decoration:

### Observation Window
- Static physical frame/body belongs to the map.
- Sky/cloud content animates independently.
- Clouds drift horizontally.
- Passing airship/floating-island variation is desirable.
- The frame/plant/cabinet anchor must not move between frames.

### Navigation Command Console
- Static physical console/body belongs to the map.
- Screen overlay cycles through readable states.
- Approved state language: route view -> scanning -> new contact/warning -> destination lock.
- Buttons/glow may pulse lightly, but the physical desk must not jitter.

## Rendering/depth rule
- Physical furniture and architecture must be map-native/TMX-owned.
- `RenderedWorld` is only for transparent/transient overlays such as moving sky pixels, screen pixels, glow, telegraphs, etc.
- Do not reintroduce physical Airship props through post-world drawing.
- Keep gameplay anchors and visual anchors aligned.

## 0690 Set 01 — integrated
These are already production-integrated in build `.57`:
- Route Notice Board
- Boarding Gate Arch
- Signal Lamp
- Cargo Parcel Crate
- Observation Window, static body + 4 animation overlays
- Navigation Command Console, static body + 4 screen overlays

Physical bodies are integrated into:
- `src/Cardcha/assets/airship_deck.tmx`
- `src/Cardcha/assets/sky_dock_interior.tmx`

Asset library:
- `src/Cardcha/assets/airship_props/set01_redux/`

Old 0677 vanilla furniture clutter for these two rooms is intentionally cleared by the 0690 implementation.

## Approved library — not yet integrated
The following concepts were approved during the same session and are candidates for the next Airship pass. They are **not yet production-integrated** unless a later handoff says otherwise:
- Ticket Pedestal / ticket counter
- Route Map Plaque / large route board
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
- Decorative folding screen / divider
- Gramophone cabinet
- Mail/key cubby/locker

The next pass should select only the props needed for composition. Do not cram every approved prop into both rooms.

## Composition principles for the two Airship rooms
### Sky Dock
- Left/service side: route/ticket/info/lost-and-found language.
- Right/boarding side: gate/luggage/mooring language.
- Keep center arrival/exit spine open.
- Existing route interaction and boarding bay must remain readable and reachable.

### Airship Deck
- Top wall: observation/navigation identity.
- Navigation console should read as a hero prop, not a tiny desk.
- Preserve lower doorway and main movement spine.
- Keep upgrade/gameplay sockets reachable.
- Favor a lived-in flying workshop / expedition hub, not a showroom grid.

## Do-not-regress list
- No tiny icon-like production props as the main visual solution.
- No arbitrary nearest-neighbor upscale used to fake detail.
- No vanilla-furniture clutter layered over the new Cardcha set.
- No physical furniture in `RenderedWorld`.
- No visual changes to Boss II/III/IV or Region content as a side effect of Airship work.
- Do not claim in-game visual acceptance until Ron tests it later.

## Recommended next build
If Ron says "tiếp" in the next session, continue from 0690 and make a focused Airship pass, most naturally:

`0691 — Airship Prop Set 02 / Harbor Furnishings Integration`

Suggested scope:
- choose a restrained subset of the approved Set 02/library,
- integrate them map-native into Sky Dock and/or Deck,
- keep all 0690 interaction lanes and anchors,
- validate TMX + render-depth + compile,
- package TEST,
- download the GitHub Actions artifact and attach the actual inner TEST ZIP in chat.

Do not require an immediate in-game test before continuing development. Ron intends to test later; mark visual acceptance as pending until then.
