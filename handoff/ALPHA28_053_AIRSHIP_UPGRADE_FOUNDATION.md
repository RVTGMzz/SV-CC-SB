# Cardcha alpha28.0.4.14 - Airship Upgrade Foundation

Baseline: alpha28.0.4.13 visual polish PASS.
Branch: `cardcha-alpha28-053-airship-upgrade-foundation`
Final successful Actions run: `33498632897`

## Chat transfer note — 2026-09-01
The user is moving to a new ChatGPT conversation because the current chat is near its limit.

For complete context from `.4.11` through `.4.14`, binary locks, user-test status, build lessons, and exact next steps, read FIRST:
`handoff/CURRENT_CHAT_HANDOFF_ALPHA28_053_2026-09-01.md`

Quick pointer also exists at:
`handoff/LATEST_CARDCHA_HANDOFF.md`

Important acceptance state at transfer: `.4.14` is CI/build/package PASS but has NOT yet received the user's first in-game acceptance test. Do not assume the upgrade interaction/persistence is user-approved until the next chat receives the test result.

## Implemented
- New dedicated `AirshipUpgradeMenu` UI.
- Four interactive Airship Bridge infrastructure sockets:
  - Aether Engine
  - Navigation Core
  - Hull & Shield
  - Arcane Reactor
- Each system has persistent levels 0 through 3.
- Save schema bumped from 16 to 17.
- Upgrade levels are normalized and included in persistence fingerprinting.
- Upgrades spend the existing player-facing Magic Dust resource while preserving the internal `SuspiciousDust` save field for compatibility.
- Provisional TEST costs are 5, 10, 20 Magic Dust for levels 1, 2, 3.
- Bridge socket visuals react immediately to persistent level: stronger system color, taller crystal, pips, rune at level 2, sparkles at level 3.
- `cardcha_give_dust [amount]` added as TEST-only console helper. Default amount is 50.
- `cardcha_airship_status` now reports all four infrastructure levels.

## Intentionally NOT enabled yet
- No travel speed bonus.
- No fare discount.
- No Region unlock changes.
- No combat stat bonus.
- No boss gating based on upgrades.

The .4.14 goal is to validate UI, interaction, Magic Dust spending, save/load persistence and visual feedback before balancing gameplay bonuses and final costs.

## Regression locks confirmed by CI
- Approved magical-girl icon atlas unchanged: SHA-256 `4d659e9a25b188ca7e5e0654aa1124ae562f28ca414236283fef1523df6700ee`.
- Clean Airship visual unchanged: SHA-256 `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- MiMi Wizard Tower appointment bypass retained.
- English card-title auto-fit retained.
- Arcane Gate / Arcane Dock / Airship Bridge / Region I flow retained.
- Region I fare remains 100g and gate card requirement remains 20.
- Forest collision edits remain NONE.

## Build QA
Inner package: `Cardcha_v0.3.0-alpha.28.0.4.14_AirshipUpgradeFoundation_TEST.zip`
Inner package SHA-256: `5cb1c41b3dc6a805de8b661598e417368785abf7d1b013f94502598a67e37f12`
Manifest version verified: `0.3.0-alpha.28.0.4.14`
Compile: PASS.
Source acceptance: PASS.
Final regression gate: PASS.
Package: PASS.

## Test checklist
1. Enter Airship Bridge.
2. Press action near each of the four infrastructure sockets.
3. Confirm the dedicated upgrade menu opens focused on the corresponding system.
4. If needed, run `cardcha_give_dust 100` for TEST currency.
5. Upgrade one system from 0 -> 1 -> 2 -> 3 and confirm Magic Dust decreases 5, then 10, then 20.
6. Confirm the Bridge socket becomes visually brighter/more elaborate after each level.
7. Save, exit, reload and confirm levels and remaining Magic Dust persist.
8. Confirm helm departure to Region I and Region I return flow still work exactly as .4.13.

## Next decision after user test
- Approve or change the permanent cost curve.
- Decide real gameplay effects for Engine, Navigation, Hull/Shield and Reactor.
- Only then connect upgrades to Region II / route range / fare / combat survivability / MiMi story progression.
