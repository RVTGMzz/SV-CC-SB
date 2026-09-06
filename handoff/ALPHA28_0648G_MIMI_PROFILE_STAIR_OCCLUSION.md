# Cardcha Alpha28 0648G Handoff

## Canonical branch
`cardcha-alpha28-0648g-mimi-profile-stair-occlusion`

## Build
- Version: `0.3.0-alpha.28.0.4.14.4.5.12.13`
- TEST: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.13_MiMiProfileStair_TEST.zip`
- TEST SHA-256: `b662b98e0f2f0b09c6e54545b661960bb182cc599e16848df940ba36208985e7`
- CI run: `34052689066` SUCCESS
- job: `101539006175` SUCCESS
- artifact ID: `9995030329`
- outer artifact digest: `sha256:c3e164c111d4439ec0a188dd2a5f99f6fae46fec31c3e7ee0ab2ca4014c73c36`
- materialized commit: `211356f01ef78f39bfaa59b90e967157bd5f70ff`

## Screenshot-driven fixes

### WizardHouse stair
- Previous fixed stair tile `(11,15)` was too far right.
- 0648G moves the same stair three tiles left to fixed tile `(8,15)`.
- No percentage/map-size search or dynamic relocation was reintroduced.
- The custom stair is still drawn from `assets/mimi_attic_stairs.png`.
- `RenderedWorld` cannot truly depth-sort a custom draw behind already-rendered characters, so the stair now draws as four 16x16 source segments (64x64 world pixels each).
- Any segment intersecting the visual body bounds of the farmer or a visible NPC is omitted for that frame. This prevents rungs from painting over heads/bodies while preserving the rest of the stair.
- Warp/collision behavior is unchanged.

### MiMi Profile / Gift Log body sprite
- User-provided `mimi_walk.png` was verified byte-identical to the canonical repo file.
- Exact `mimi_walk.png` SHA-256: `04ff1cbf031c2be0a21f114b8f8eb6f8850bb800eeabd4c27df036d7b23d4fb7`.
- Dimensions remain `128x192`, arranged as native Cardcha 32x48 frames.
- `MimiProfileMenuPatch` keeps its existing 32x48 AnimatedSprite sizing/scale behavior.
- `WorldActorService.MimiProfileCharacterAsset` now loads `assets/mimi_walk.png` instead of the ugly half-scale `assets/mimi_profile.png`.
- `assets/mimi_profile.png` is deleted and is absent from the TEST ZIP.
- No runtime rescaling/repainting of `mimi_walk.png` was added.

### MiMi small Social/Gift avatar
- 0648F accidentally changed `MugShotSourceRect` to `(8,0,16,24)`, cropping into a full 32x48 body frame and producing the broken/cut avatar.
- 0648G restores the dedicated UI slot appended to `mimi_walk_runtime.png`:
  `MugShotSourceRect = (0,192,16,24)`.
- `mimi_walk_runtime.png` remains `128x216`; the reserved 16x24 UI sprite at y=192 is preserved.

## Locked regression scope
0648G intentionally does NOT change:
- Airship architecture, route, visuals, machines, upgrade costs/levels or deferred bonuses.
- Forest Arcane Gate behavior/collision.
- MiMi HOME/TV/LATE routine logic.
- MiMi attic map/furniture layout.
- `mimi_walk.png` bytes.
- MiMi dialogue portrait sheet/lifecycle.
- Save schema 19, 76 active cards, Boss Form 10s, Boss Energy 1/3.

## Acceptance test
1. Fully replace the old Cardcha folder and restart SMAPI.
2. In WizardHouse, verify stair appears at the same height but about three tiles left of 0648F.
3. Walk directly in front of/through the stair visual and verify ladder rungs never paint over the farmer's face/body.
4. Open MiMi's Social/Profile/Gift Log screens.
5. Verify the full-body profile sprite now uses the sharp canonical `mimi_walk.png` scale instead of the tiny `mimi_profile.png` source.
6. Verify the small MiMi avatar is no longer the cut/oversized 0648F crop.
