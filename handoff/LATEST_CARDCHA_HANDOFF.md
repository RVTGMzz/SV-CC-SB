# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0648j-mimi-texture-scale-stair-wallblock`

Current build:
`0.3.0-alpha.28.0.4.14.4.5.12.16`

Read this FIRST when resuming from another chat:
`handoff/ALPHA28_0648J_MIMI_TEXTURE_SCALE_STAIR_WALLBLOCK.md`

## Session status — 2026-09-07
- 0648J replaces 0648I for the two remaining screenshot-driven issues only.
- CI static validation, SMAPI compile, materialization and package audit are green.
- In-game acceptance is pending for MiMi Profile/Gift Log 50% rendering and the right-wall solid WizardHouse stair.

## Current implementation
### MiMi Profile / Gift Log
- Canonical `assets/mimi_walk.png`, native 32x48 frames, no new image/animation.
- Exact `AnimatedSprite.draw(SpriteBatch, Vector2, float)` overload is intercepted.
- Scale gating no longer depends on `MimiProfileActive`, current-menu state, or `_animatedSprite` reference equality.
- MiMi is detected directly from her profile/world character texture names and the vanilla 4x profile draw is replaced with a centered 2x draw (50%).
- World MiMi uses a different AnimatedSprite draw overload and remains unchanged.

### WizardHouse stair
- Anchor moved to `(15,15)` to match the right-wall strip beside the fireplace in the user's screenshot.
- Stair remains four real 16x16 `Buildings` layer tiles.
- `Passable=T` is removed, so the stair is solid and cannot be walked through.
- No RenderedWorld stair draw, proximity hiding, slicing, fading, or disappearance logic remains.
- Attic interaction/warp follows the same `(15,15)` anchor.

## Verified build
- workflow run: `34071322412` SUCCESS
- job: `101589087127` SUCCESS
- materialized source commit: `46efd58e7739962b3196815d553768d93b6964d9`
- artifact ID: `10000553550`
- outer artifact digest: `sha256:11f3d739ad531c5ead3f2dbd66aa9198cd14889a74760dc60f959b36f14e17a9`
- package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.16_MiMiScale50_StairWallBlock_TEST.zip`
- package SHA-256: `397a02cf79d325cb04f1585510eb83ca8a86f50d766694b0431b3ab01b2a5328`
- compiled DLL size: `762880` bytes

## Locked canon / regression guard
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit remains the locked active set.
- Forest Arcane Gate normal action distance remains 160px and Forest collision stays untouched.
- Locked `airship_visual.png` SHA remains `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- Airship route remains `Forest -> Cardcha_SkyDockInterior -> Cardcha_AirshipDeck`.
- Airship upgrade costs/levels/save fields and deferred gameplay bonuses unchanged.
- MiMi HOME/TV/LATE routine, attic layout, progression, portrait architecture, save schema and card canon remain intact.
- Canonical `mimi_walk.png` SHA remains `04ff1cbf031c2be0a21f114b8f8eb6f8850bb800eeabd4c27df036d7b23d4fb7`.

## Next acceptance
Replace the old Cardcha folder completely and restart SMAPI. Test MiMi's `Danh Sách Quà Tặng` first: she should visibly shrink to 50% and remain centered. Then test the WizardHouse stair: it should sit at the right wall, remain fully visible, block walking through it, and still allow attic interaction from in front of the stair.
