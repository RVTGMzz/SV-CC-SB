# Cardcha Alpha28 0648H Handoff

## Canonical test branch
`cardcha-alpha28-0648h-mimi-gift-scale-stair-overlap`

## Build
- Version: `0.3.0-alpha.28.0.4.14.4.5.12.14`
- TEST: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.14_MiMiGiftScaleStair_TEST.zip`
- TEST SHA-256: `547950a9c8a9ddb3e662b742843a1098d1a80a175aa7ad8752e174f54261a959`
- CI run: `34056026351` SUCCESS
- job: `101547965770` SUCCESS
- artifact ID: `9995980744`
- outer artifact digest: `sha256:a911200bef7d7db14a5df9a0e65b29ad3c87660b313512f7a291dce6a3110429`
- materialized source commit: `59eab2ff14eb40d5df7ec7836265ed2879842dcd`
- compiled DLL size: `762880` bytes

## Screenshot-driven fixes from 0648G

### MiMi Gift Log / Profile scale
- No new MiMi animation or image asset was created.
- Canonical `assets/mimi_walk.png` remains byte-identical, SHA-256 `04ff1cbf031c2be0a21f114b8f8eb6f8850bb800eeabd4c27df036d7b23d4fb7`.
- Profile/Gift Log still substitutes the same native 32x48 `AnimatedSprite` backed by `assets/mimi_walk.png`.
- `MimiProfileMenuPatch` now intercepts only the active MiMi ProfileMenu AnimatedSprite draw call and multiplies its final `scale` argument by `0.5f`.
- World MiMi, dialogue portraits, `mimi_walk_runtime.png`, small Social/Gift avatar and all existing animation sheets are unchanged.
- `assets/mimi_profile.png` remains deleted.

### WizardHouse stair overlap
- Stair placement remains fixed at `(8,15)` exactly as accepted for position in 0648G.
- 0648G's four independent 64px rung segments are removed because they visibly sliced the stair sprite as the farmer crossed it.
- 0648H renders the full 16x64 stair as one sprite when clear.
- If a visible farmer/NPC body overlaps the stair visual bounds, the entire cosmetic stair is hidden for that frame instead of removing individual rungs.
- Warp/collision behavior is unchanged.

## Verification
- 0648H static scope validator: PASS.
- SMAPI compile: PASS.
- package audit: PASS.
- packaged `mimi_walk.png`: canonical SHA confirmed.
- packaged `airship_visual.png`: locked SHA `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132` confirmed.
- In-game visual acceptance is pending for MiMi 50% Profile/Gift scale and whole-stair overlap behavior.

## Locked regression scope
0648H does NOT change:
- Save schema 19.
- 76/76 active cards.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- Forest Arcane Gate normal action distance 160px or Forest collision.
- Airship architecture, route, locked visual, machines, upgrades, costs, levels, save fields or deferred bonuses.
- MiMi HOME/TV/LATE routine.
- MiMi attic map/furniture layout.
- MiMi small Social/Gift avatar crop `(0,192,16,24)`.
- MiMi dialogue portrait lifecycle.

## Next acceptance
1. Fully replace the installed Cardcha folder and restart SMAPI.
2. Open MiMi's `Danh Sách Quà Tặng` / Profile / Gift Log and verify her full-body sprite is visually 50% of the 0648G size while staying sharp and animated.
3. Verify normal world MiMi size/animation and the small Social/Gift avatar are unchanged.
4. In WizardHouse, approach/cross the stair at `(8,15)`. The stair may disappear as one complete cosmetic sprite during overlap, but must no longer be sliced rung-by-rung around the farmer.
5. Step clear of the stair and verify the complete stair returns immediately.
