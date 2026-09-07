# Alpha28 0655 - MiMi native profile + stair anchor fix

Branch: `cardcha-alpha28-0655-mimi-native-profile-stair-anchor-fix`

Build target: `0.3.0-alpha.28.0.4.14.4.5.12.22`

## Why 0654 was rejected
- Moving the WizardHouse stair anchor from x15 to x16 did not produce the requested slight visual nudge; x16 is the right-side wall/foreign-content column in the tested map and the ladder presentation regressed.
- MiMi remained oversized in Gift Log/Profile despite draw-scale interception, proving that continuing to patch AnimatedSprite.draw is the wrong abstraction.

## 0655 strategy reset
### Wizard stair
- Restore the known-good gameplay/collision/interaction anchor to `(15,15)`.
- Keep up/down on the same stair route.
- Shift only the pixels inside `mimi_attic_stairs.png` one source pixel right, which equals roughly four screen pixels at Stardew's map scale.
- Do not use x16 and do not move the stair into the wall.

### MiMi Gift Log/Profile
- Reuse Cardcha's existing `assets/mimi_npc.png`, already a native Stardew-style 64x128 sheet with 16x32 frames.
- `Characters/Ronvotri.Cardcha_MiMi_Profile` now loads that native sheet instead of the 32x48 `mimi_walk.png` sheet.
- `ProfileMenu._SetCharacter` substitutes a 16x32 AnimatedSprite for MiMi.
- Remove all MiMi AnimatedSprite.draw scaling/interception. Vanilla ProfileMenu now renders MiMi at its normal 4x path, matching ordinary NPC layout behavior such as Martin.
- `cardcha_mimi_profile_status` now reports native sprite substitutions instead of scale-hook hits.

## Regression guard
- 0653 strict TMX runtime compatibility fix retained.
- No attic furniture/layout, MiMi HOME/TV/LATE routine, story/friendship, Save schema 19, Boss I, Hunt Run, Airship, card canon, or controller profile changes.

## In-game acceptance pending
- Ladder should appear in the previous working column, visually nudged right but not inside the wall.
- Returning from the attic should use that same ladder route.
- MiMi Gift Log should render at a normal NPC-sized 16x32-frame/4x presentation, comfortably inside the portrait background.
