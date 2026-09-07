# Cardcha handoff — 0648J MiMi texture scale + Wizard stair wall block

Current branch: `cardcha-alpha28-0648j-mimi-texture-scale-stair-wallblock`

Current build: `0.3.0-alpha.28.0.4.14.4.5.12.16`

## Why 0648J exists
In-game acceptance of 0648I showed two remaining issues:
1. MiMi in Profile / Gift Log still appeared at the previous visual size.
2. The WizardHouse stair should sit against the right wall and behave as a solid object instead of being walk-through.

## 0648J implementation
### MiMi Profile / Gift Log
- Keep canonical `assets/mimi_walk.png`; no resized/repainted asset and no new animation.
- Keep native 32x48 frames.
- Patch the exact `AnimatedSprite.draw(SpriteBatch, Vector2, float)` overload used by ProfileMenu.
- Remove all dependence on `MimiProfileActive`, `Game1.activeClickableMenu`, and `_animatedSprite` reference equality for the scale decision.
- The hook now identifies MiMi directly by her character/profile texture names:
  - `Characters/Ronvotri.Cardcha_MiMi_Profile`
  - `Characters/Ronvotri.Cardcha_MiMi`
- Vanilla 4x draw is replaced by centered 2x draw, i.e. exactly 50% relative scale.
- MiMi world rendering uses a different AnimatedSprite overload, so the world actor is not affected.

### WizardHouse stair
- Stair anchor moved from `(8,15)` to `(15,15)` to sit on the narrow right-wall strip beside the fireplace shown in the acceptance screenshot.
- The visual remains four real 16x16 tiles on the WizardHouse `Buildings` layer.
- Removed `Passable=T`; these Buildings tiles are intentionally solid now.
- Player can no longer walk through the stair. Interaction/warp uses the same resolved `(15,15)` anchor.
- No RenderedWorld stair drawing, character overlap checks, slicing, fading, or disappearance logic.

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
- 76/76 active card audit remains locked.
- Forest Arcane Gate normal action distance remains 160px and Forest collision stays untouched.
- Airship visual SHA remains `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- Airship route remains `Forest -> Cardcha_SkyDockInterior -> Cardcha_AirshipDeck`.
- MiMi HOME/TV/LATE routine, attic layout, progression, save schema and card canon are untouched.
- Canonical `mimi_walk.png` SHA remains `04ff1cbf031c2be0a21f114b8f8eb6f8850bb800eeabd4c27df036d7b23d4fb7`.

## Next acceptance
Replace the old Cardcha folder completely and restart SMAPI. Test only:
1. MiMi Profile / `Danh Sách Quà Tặng`: expected centered 50% visual size.
2. WizardHouse stair: expected right-wall placement around x=15, full visibility, solid collision, and working attic interaction from in front of the stair.
