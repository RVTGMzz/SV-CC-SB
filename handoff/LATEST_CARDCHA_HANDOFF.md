# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0648g-mimi-profile-stair-occlusion`

Current build:
`0.3.0-alpha.28.0.4.14.4.5.12.13`

Read this FIRST when resuming from another chat:
`handoff/ALPHA28_0648G_MIMI_PROFILE_STAIR_OCCLUSION.md`

## Current verified state
- Screenshot-driven WizardHouse stair placement is fixed at `(8,15)`, three tiles left of 0648F.
- Stair rendering is split into four tile-sized segments with character-body occlusion so the post-world custom draw cannot paint over the farmer/NPC body.
- MiMi Profile/Gift Log animated sprite keeps the existing 32x48 menu scaling but now loads the canonical `assets/mimi_walk.png` directly.
- `assets/mimi_profile.png` is deleted and absent from the package.
- MiMi small Social/Gift avatar restores `MugShotSourceRect=(0,192,16,24)`, using the dedicated UI slot already appended to `mimi_walk_runtime.png`.
- User-provided `mimi_walk.png` is byte-identical to repo canonical SHA-256 `04ff1cbf031c2be0a21f114b8f8eb6f8850bb800eeabd4c27df036d7b23d4fb7`.
- Portrait dialogue architecture from 0648F remains unchanged.
- Airship, Forest Gate, MiMi HOME/TV/LATE routine, attic layout, progression, save schema and card canon are untouched.

## Verified build
- workflow run: `34052689066` SUCCESS
- job: `101539006175` SUCCESS
- materialization commit: `211356f01ef78f39bfaa59b90e967157bd5f70ff`
- artifact ID: `9995030329`
- outer artifact digest: `sha256:c3e164c111d4439ec0a188dd2a5f99f6fae46fec31c3e7ee0ab2ca4014c73c36`
- package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.13_MiMiProfileStair_TEST.zip`
- package SHA-256: `b662b98e0f2f0b09c6e54545b661960bb182cc599e16848df940ba36208985e7`
- compiled DLL size: `761344` bytes

## Locked canon / regression guard
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit remains the locked active set.
- Forest Arcane Gate normal action distance remains 160px and Forest collision stays untouched.
- Locked `airship_visual.png` SHA remains `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- Airship route remains `Forest -> Cardcha_SkyDockInterior -> Cardcha_AirshipDeck`.
- Airship upgrade costs/levels/save fields and deferred gameplay bonuses unchanged.
- MiMi HOME/TV/LATE routine test preview remains intact.

## Next acceptance
Replace the old Cardcha folder completely and restart SMAPI. Test the WizardHouse stair position/occlusion, MiMi small avatar, and MiMi Profile/Gift Log full-body sprite first. Do not modify Airship/Gate/routine systems unless a new in-game report specifically points there.
