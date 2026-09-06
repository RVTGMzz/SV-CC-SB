# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0648i-mimi-profile-directdraw-stair-maplayer`

Current build:
`0.3.0-alpha.28.0.4.14.4.5.12.15`

Read this FIRST when resuming from another chat:
`handoff/ALPHA28_0648I_MIMI_PROFILE_DIRECTDRAW_STAIR_MAPLAYER.md`

## Session status — 2026-09-07
- 0648I replaces failed 0648H for the two screenshot-driven visual issues only.
- CI architecture validation, compile and package audit are green.
- In-game acceptance is still pending for MiMi Profile/Gift Log half-size rendering and WizardHouse stair depth behavior.
- Do NOT return to 0648G/0648H visibility hacks for the Wizard stair. The stair is now map-layer architecture, not a post-world cosmetic draw.
- Do NOT reintroduce generic AnimatedSprite scale-overload scanning for MiMi. The active ProfileMenu path is explicitly the three-argument draw overload.

## Root-cause fixes now implemented
### MiMi Profile / Gift Log
- Canonical `assets/mimi_walk.png`, native 32x48 frames, no new asset.
- Exact `AnimatedSprite.draw(SpriteBatch, Vector2, float)` overload is intercepted only for the active MiMi ProfileMenu sprite.
- Vanilla 4x draw is replaced with a centered 2x draw, i.e. 50% relative size.
- World sprite and other NPC/menu draws are untouched.

### WizardHouse stair
- Approved anchor remains `(8,15)`.
- No `DrawStairMarker`, no per-rung omission, no whole-stair hiding, no character-overlap visibility logic.
- `mimi_attic_stairs.png` is installed as four real 16x16 tiles on the WizardHouse `Buildings` layer (x=8, y=11..14), with `Passable=T`.
- Corresponding `Front` tiles in the single stair column are cleared; Back art is preserved.
- Stardew now owns the draw order, so player/NPC sprites should naturally render in front of the stair while the full stair remains visible.

## Verified build
- workflow run: `34057497198` SUCCESS
- job: `101551951323` SUCCESS
- materialized source commit: `a46c507b116f052c67cd66c1cafcbfb03ab74e9b`
- artifact ID: `9996411295`
- outer artifact digest: `sha256:a4c00ed9e65e93ce1f73ad79be6b8e89acf6d3a9c04448b3da359b7c02037fa9`
- package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.15_MiMiDirectScaleStairMap_TEST.zip`
- package SHA-256: `eaa32dde60c1b2a1c9d6ebc81e5250d56aa1ef5b341c81f39c5325da82a4a04b`
- compiled DLL size: `763392` bytes

## Locked canon / regression guard
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit remains the locked active set.
- Forest Arcane Gate normal action distance remains 160px and Forest collision stays untouched.
- Locked `airship_visual.png` SHA remains `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- Airship route remains `Forest -> Cardcha_SkyDockInterior -> Cardcha_AirshipDeck`.
- Airship upgrade costs/levels/save fields and deferred gameplay bonuses unchanged.
- MiMi HOME/TV/LATE routine test preview, attic layout, progression and portrait architecture remain intact.
- Canonical `mimi_walk.png` SHA remains `04ff1cbf031c2be0a21f114b8f8eb6f8850bb800eeabd4c27df036d7b23d4fb7`.

## Next acceptance
Replace the old Cardcha folder completely and restart SMAPI. Test MiMi's `Danh Sách Quà Tặng` / Profile first: she should be exactly half the previous visual size and centered in the frame. Then walk toward/across/away from the WizardHouse stair: it must remain fully visible at all distances, with the player naturally appearing in front of it. No slicing, fading or disappearance is acceptable.
