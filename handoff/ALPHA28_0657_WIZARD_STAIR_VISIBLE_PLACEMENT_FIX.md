# Alpha28 0657 - Wizard stair visible placement fix

Branch: `cardcha-alpha28-0657-wizard-stair-visible-placement-fix`

Build target: `0.3.0-alpha.28.0.4.14.4.5.12.24`

## User-reported regression
- In 0655/0656 the WizardHouse ladder is not visibly present in the intended right-side interior strip.
- Do not infer a new left/right tile from the screenshot. The last visibly working presentation was the pre-0655 art on the x15 route.

## 0657 fix
- Keep the canonical Wizard stair gameplay anchor `(15,15)` so ascent, collision/interaction and return landing remain one route.
- Restore `mimi_attic_stairs.png` byte-for-byte to the pre-0655 / 0653 visible artwork. Remove the rejected one-source-pixel PNG nudge.
- Replace the map-reference-only render cache with verification of all four real Buildings-layer stair segments.
- If a live WizardHouse map mutates/reloads and any segment disappears, reinstall the four ladder tiles.
- Clear only `Front`, `AlwaysFront`, and `Front2` at those four stair cells so foreign foreground content cannot completely cover the ladder. Back/floor art is untouched.
- Continue using real map tiles, not a post-world overlay, so the ladder stays in normal Stardew world draw order.

## Preserved from 0656
- Community Center MiMi work tile cache / ghosting fix.
- Community Center continuity dialogue and route cache refresh.
- MiMi Gift Log native 16x32 profile sprite pipeline.
- 0653 strict TMX runtime compatibility fix.

## In-game acceptance pending
- Ladder must be clearly visible inside WizardHouse in the right-side strip near the wall.
- Ladder must not require a separate invisible exit route.
- Entering and returning from the attic must use the same stair route.
