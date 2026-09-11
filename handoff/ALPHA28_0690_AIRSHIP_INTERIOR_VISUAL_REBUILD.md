# Alpha 28 0690 — Airship Interior Visual Rebuild

Source-of-truth parent: `55157c903f0e45cd29df2711ac8e12b32d8fbb4f` (0688)

Build: `0.3.0-alpha.28.0.4.14.4.5.12.57`

## Purpose
Replace the temporary/vanilla-looking Airship Deck + Sky Dock furniture language with the approved Cardcha wood/brass/purple/teal visual identity.

## 0690 Set 01
- Route Notice Board: map-native physical art.
- Boarding Gate Arch: map-native physical art with open center lane.
- Signal Lamp: map-native physical art.
- Cargo Parcel Crate: map-native physical art.
- Observation Window: map-native body + VFX-only moving sky panes.
- Navigation Command Console: map-native body + VFX-only four-state screen.

## Rendering contract
- Static physical art is owned by `airship_deck.tmx` / `sky_dock_interior.tmx`.
- Runtime only draws transparent sky/screen pixels.
- Old 0677 vanilla furniture clutter is cleared from these two rooms.
- Boss and Region content inherited from 0688 is frozen by CI.

## Layout
Sky Dock: route/service identity left, boarding gate right, center arrival/exit spine preserved.
Airship Deck: observation wall at top, navigation console centered on the existing helm role, lower doorway preserved.

## Acceptance state
CI/compile/package validation is authoritative for this handoff. In-game visual acceptance is pending Ron's later test.
