# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-055-card-runtime-audit`

Current build:
`0.3.0-alpha.28.0.4.14.2`

Read this FIRST when resuming from another chat:
`handoff/ALPHA28_055_CARD_RUNTIME_AUDIT.md`

Full per-card audit table:
`docs/CARD_RUNTIME_AUDIT_ALPHA28_055.md`

Then read prior Airship transfer context if needed:
- `handoff/ALPHA28_054_AIRSHIP_UX_HOTFIX.md`
- `handoff/CURRENT_CHAT_HANDOFF_ALPHA28_053_2026-09-01.md`

Current acceptance status:
- `.4.11`: user reported in-game test OK.
- `.4.12`: CI/build PASS, no separate explicit full user acceptance recorded.
- `.4.13`: CI/build PASS, no separate explicit full user acceptance recorded.
- `.4.14`: first in-game test revealed controller/readability/boarding-point/auto-transition UX issues.
- `.4.14.1`: Airship UX hotfix compile/regression/package PASS; awaiting full in-game acceptance.
- `.4.14.2`: user required a full audit of ALL cards. All 76 active Base Set IDs were audited. Initial result was 50 PASS / 12 CLARIFY / 14 BUG. Remediation source acceptance, compile, regression and package all PASS.

`.4.14.2` fixes/aligned every unambiguous card-runtime finding except **#20 Victory Charge**, which depends on a Boss Energy system that does not yet exist. The TEST build explicitly labels Victory Charge inactive instead of inventing a hidden substitute effect.

Legacy Mythic IDs 77–80 remain migration-only/hidden and are not active Binder/gacha cards.

Do not start permanent Airship upgrade effects/balance during this card-runtime validation pass. Preserve `.4.14.1` Airship UX fixes and `CollisionEdits=NONE`.
