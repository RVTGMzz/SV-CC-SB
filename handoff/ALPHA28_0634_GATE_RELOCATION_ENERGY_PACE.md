# Cardcha alpha28-0634 — Gate Relocation + Boss Energy Pace

## Branch / build

- Active branch: `cardcha-alpha28-0634-gate-relocation-energy-pace`
- Test version: `0.3.0-alpha.28.0.4.14.4.5.3`
- CI source commit: `e1ffac20e38433aab8916ec9b6b5a92045e7824b`
- Workflow run: `33707896553` — SUCCESS
- Artifact ID: `9875887465`
- Artifact digest: `sha256:63d71c12e273cf3f11a985941b0658703d345e919b1f9436f70d083b85406876`
- Test ZIP: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.3_GateRelocation_EnergyPace_TEST.zip`
- Test ZIP SHA-256: `f7c3842045fcf65c6ebd1f467f7402ba2915125e780d38a6cc7cd304deabf26e`

## User decision: Forest Arcane Gate

The user rejected the previous compatibility feel where a blocked gate area could be compensated by a very wide 320px action radius.

New rule:

1. Keep rejecting unsafe placement geometry, including static `Buildings` and `Front` layer tiles from map overhauls.
2. First search only a compact local pocket near the Farm entrance.
3. If that pocket is blocked, relocate the gate to a clearly different Forest zone.
4. If curated alternate zones fail, sweep distinct map sectors with small local searches instead of growing one huge radius around the original spot.
5. Clamp the old Forest-gate 320px interaction reach to 160px. Do not restore a giant invisible activation bubble as fallback.
6. Require at least one clear approach tile directly in front of the 3x3 gate footprint.
7. Forest collision/tile edits remain NONE.

Implementation is isolated in `src/Cardcha/Patches/AirshipGateRelocationPatch.cs` so the existing Airship foundation remains rollback-safe.

## User decision: ChaCha Boss Energy

Boss Energy was filling too quickly. All real combat-sourced Energy gain is now multiplied by `1/3`, making READY take approximately 3x longer under the same combat pattern.

- 100 Energy READY threshold unchanged.
- Boss Form duration remains 10 seconds.
- Victory Charge keeps the same relative percentage bonus, but its resulting Energy is also scaled by `1/3` with the rest of the gain event.
- Debug fill command remains available for UI/Boss Form testing and is not slowed.
- Save schema remains 19.

## Regression locks verified in CI

- 76/76 card auto audit PASS.
- `airship_visual.png` unchanged, SHA-256 `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- `items.png` unchanged, SHA-256 `95029fb703777305b097136f6b12c0eae6f021fde6070f03424943463ea3e3e4`.
- `chacha_skill_materials.png` unchanged, SHA-256 `76261133b2df191f516af74f4e866bddcf171c1a0739e269579994a40b15dfc7`.
- `chacha_skill_icons.png` unchanged, SHA-256 `d36f5cef2d409a1b3b1c123bb02957131393473cc7e4a4ea1b326514a6cab036`.
- Compile PASS + package PASS.

## Runtime acceptance still needed

CI proves compile/package/static contracts only. User should verify in game that a modded Forest with blocked local gate geometry visibly relocates the gate to a usable alternate area, that 160px reach feels natural, and that Boss Energy pacing is roughly 3x slower in real combat.
