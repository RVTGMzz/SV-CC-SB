# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0648h-mimi-gift-scale-stair-overlap`

Current build:
`0.3.0-alpha.28.0.4.14.4.5.12.14`

Read this FIRST when resuming from another chat:
`handoff/ALPHA28_0648H_MIMI_GIFT_SCALE_STAIR_OVERLAP.md`

## Session status — 2026-09-07
- 0648H is the current verified TEST candidate, branched directly from accepted 0648G source/handoff.
- CI compile, static scope validation and package audit are green.
- In-game acceptance is pending only for the two screenshot-driven follow-ups reported after 0648G: MiMi Profile/Gift Log 50% menu scale and WizardHouse stair overlap behavior.
- Do NOT return to older 0648/0648F/0648G branches for new work unless explicitly debugging lineage.
- If these two visual checks pass, keep 0648H as the canonical base for the next Cardcha feature.

## Current verified state
- WizardHouse stair position remains fixed at `(8,15)`.
- Per-rung stair slicing from 0648G is removed. The full stair is drawn as one sprite when clear, and the whole cosmetic stair is hidden for a frame if a visible character overlaps it.
- MiMi Profile/Gift Log still uses canonical `assets/mimi_walk.png` with native 32x48 frames, but only the active MiMi ProfileMenu draw scale is multiplied by `0.5f` in code.
- No new animation/image asset was created for that scale change.
- `assets/mimi_profile.png` remains deleted.
- MiMi small Social/Gift avatar remains `MugShotSourceRect=(0,192,16,24)` using the dedicated UI slot in `mimi_walk_runtime.png`.
- Canonical `mimi_walk.png` SHA-256 remains `04ff1cbf031c2be0a21f114b8f8eb6f8850bb800eeabd4c27df036d7b23d4fb7`.
- Airship, Forest Gate, MiMi HOME/TV/LATE routine, attic layout, progression, save schema and card canon are untouched.

## Verified build
- workflow run: `34056026351` SUCCESS
- job: `101547965770` SUCCESS
- materialized source commit: `59eab2ff14eb40d5df7ec7836265ed2879842dcd`
- artifact ID: `9995980744`
- outer artifact digest: `sha256:a911200bef7d7db14a5df9a0e65b29ad3c87660b313512f7a291dce6a3110429`
- package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.14_MiMiGiftScaleStair_TEST.zip`
- package SHA-256: `547950a9c8a9ddb3e662b742843a1098d1a80a175aa7ad8752e174f54261a959`
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
- MiMi HOME/TV/LATE routine test preview remains intact.

## Next acceptance
Replace the old Cardcha folder completely and restart SMAPI. First test MiMi's `Danh Sách Quà Tặng` / Profile/Gift Log at the new 50% menu scale, then walk into/out of the WizardHouse stair visual. The stair may disappear completely during overlap, but must no longer be sliced into missing rungs. Do not modify Airship/Gate/routine systems unless a new in-game report specifically points there.
