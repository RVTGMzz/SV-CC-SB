# Cardcha alpha28 0648I handoff — MiMi Profile direct draw + Wizard stair map layer

## Branch / build
- Branch: `cardcha-alpha28-0648i-mimi-profile-directdraw-stair-maplayer`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.15`
- Base: 0648H (`0.3.0-alpha.28.0.4.14.4.5.12.14`)
- Materialized source commit: `a46c507b116f052c67cd66c1cafcbfb03ab74e9b`

## Why 0648H failed in-game
1. **MiMi Gift Log/Profile stayed 100% size.** 0648H scanned and patched `AnimatedSprite.draw` overloads which expose a named `scale` argument, but `ProfileMenu` actually uses the three-argument `draw(SpriteBatch, Vector2, float)` overload. That overload hardcodes sprite scale `4f`, so 0648H's multiplier never touched the active draw path.
2. **WizardHouse stair vanished completely on approach.** 0648H intentionally returned without drawing the stair whenever the character bounds overlapped it. That removed the 0648G per-rung slicing but simply replaced it with whole-sprite disappearance. The architectural problem was drawing the stair in `RenderedWorld`, after Stardew had already drawn characters.

## 0648I fixes
### MiMi Gift Log / Profile
- Keep canonical `assets/mimi_walk.png` and native 32x48 animation frames.
- Keep the same ProfileMenu sprite substitution.
- Patch the exact `AnimatedSprite.draw(SpriteBatch, Vector2, float)` overload used by ProfileMenu.
- For the active MiMi ProfileMenu sprite only, skip the vanilla 4x draw and issue the same sprite draw at 2x, i.e. exactly 50% relative size.
- Add a center offset so the smaller sprite remains centered in the same vanilla character footprint instead of shrinking toward the top-left.
- No new animation, no resized/repainted asset, no world-sprite impact.

### WizardHouse stair
- Keep the approved stair anchor `(8,15)` unchanged.
- Remove `DrawStairMarker`, `IntersectsVisibleCharacter`, `GetCharacterVisualBounds`, per-rung hiding, and whole-sprite hiding.
- Install `assets/mimi_attic_stairs.png` as a runtime xTile tilesheet (`1x4` 16x16 tiles).
- Place four real stair tiles on the WizardHouse `Buildings` layer at x=8, y=11..14.
- Set each stair tile `Passable=T` so it doesn't become a collision wall.
- Clear only the corresponding `Front` tiles in that single stair column; Back/wall art stays untouched.
- Because the stair is now part of the map's normal layer stack, Stardew draws Buildings before characters and the farmer/NPC can naturally appear in front of the stair. No proximity visibility logic remains.
- Runtime map object tracking ensures the stair is reinstalled if the WizardHouse map object is reloaded/replaced.

## Build verification
- Workflow run: `34057497198` SUCCESS
- Job: `101551951323` SUCCESS
- Architecture validator: PASS
- Compile: PASS
- Package audit: PASS
- Artifact ID: `9996411295`
- Outer artifact digest: `sha256:a4c00ed9e65e93ce1f73ad79be6b8e89acf6d3a9c04448b3da359b7c02037fa9`
- Package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.15_MiMiDirectScaleStairMap_TEST.zip`
- Package SHA-256: `eaa32dde60c1b2a1c9d6ebc81e5250d56aa1ef5b341c81f39c5325da82a4a04b`
- Compiled DLL size: `763392` bytes

## Locked regression guard
- Save schema 19 unchanged.
- Boss Form 10 seconds unchanged.
- Boss Energy gain scale 1/3 unchanged.
- 76/76 active cards unchanged.
- Forest Arcane Gate normal action distance 160px unchanged.
- Airship route, costs, levels, save fields, assets and deferred bonuses unchanged.
- `airship_visual.png` SHA-256 remains `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- MiMi HOME/TV/LATE routine, attic layout, progression and portrait architecture unchanged.
- `mimi_walk.png` SHA-256 remains `04ff1cbf031c2be0a21f114b8f8eb6f8850bb800eeabd4c27df036d7b23d4fb7`.

## In-game acceptance still required
Replace the old Cardcha folder completely and restart SMAPI. Test exactly:
1. `Danh Sách Quà Tặng` / Profile: MiMi should render at half the previous visual size, centered inside the same portrait frame.
2. WizardHouse stair: walk toward, across, and away from the stair. The stair must stay fully present at all times; the player should naturally render in front of it. No partial slicing and no whole-sprite disappearance.

If either item fails, debug that exact architecture before touching any other Cardcha systems.
