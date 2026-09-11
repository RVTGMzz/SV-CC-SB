# 0689 Airship Prop Set 01 - game-ready sprite staging

Branch: `cardcha-alpha28-0689-airship-prop-set01-game-ready`
Base: 0688 materialized source `55157c903f0e45cd29df2711ac8e12b32d8fbb4f`

## Purpose
Convert the approved Airship Rooms Prop Set 01 concept direction into native-scale Stardew-compatible pixel assets before any map re-layout work begins.

## Approved props
- Route Notice Board: 2x2 tiles / 32x32 px
- Boarding Gate Arch: 4x3 tiles / 64x48 px
- Observation Window: 4x2 tiles / 64x32 px
- Navigation Command Console: 3x2 tiles / 48x32 px
- Signal Lamp: 1x1 tile / 16x16 px
- Cargo Parcel Crate: 1x1 tile / 16x16 px

## Visual rules
Warm wood, brass/gold fittings, Cardcha purple diamond motifs and restrained teal accents. The game-ready sprites intentionally use fewer colors and fewer tiny details than the presentation concepts so silhouettes remain readable at native game scale.

## Rendering ownership
These are physical props. Final placement must be TMX/native map layer or native Furniture/Object ownership. They must not be introduced as physical art through `RenderedWorld`.

## Scope
This branch stages Set 01 art and atlas metadata only. It does not yet re-layout the Sky Dock or Airship Deck maps. Map composition happens after the prop library is approved/completed.
