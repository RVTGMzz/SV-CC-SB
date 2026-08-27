# Cardcha v0.3.0-alpha.13 recovery handoff

Prepared 2026-08-26 from the alpha.12 Binder Select + Resource Rail candidate.

## Candidate identity

- Version: `0.3.0-alpha.13`
- Build label: `Cardcha! v0.3.0-alpha.13 MIMI SHOP + FULL FLIGHT`
- Compile Hotfix 1 Full Windows Builder SHA-256: `d17447114037f3620dd59e31ce108577441868135d5ce81e6df48efd897812c1`
- Compile Hotfix 1 Source Snapshot SHA-256: `3688a89418fc269048368f80ef3abbf5a94bd23f14c162423c7bdca359975cc9`
- Official `mimi_broom.png` SHA-256: `d70d05f629f2c1c94ae97de15a74c62ab3390a4dcb14e559079f13a75de602f9`

## Exact user-approved scope

- Only pre-handoff mystery MiMi is `???`; after handoff/machine delivery portrait/dialogue/world name is MiMi.
- Portable purchase control must remain interactive while unowned; insufficient money should explain failure instead of presenting a dead gray button.
- Normal/Shiny Scrap buy/sell opens a `− / +` quantity chooser with confirm/cancel and controller support.
- Every active broom arrival starts beyond the current viewport and every broom departure reaches beyond the current viewport before the actor is hidden.
- User-supplied `mimi_broom.zip` is authoritative and replaces the old broom master.
- The revised broom art is slightly smaller inside the same 32x48 cells, so broom runtime scale is +10% relative to standing MiMi: `0.575f -> 0.6325f`. Do not resize the PNG itself.
- Alpha.12 Binder fixes remain active.
- Builder must clean `bin/obj` and verify the output ZIP manifest is exactly `0.3.0-alpha.13`.
- Test install should delete the old `Mods/Cardcha` directory first; do not merge over alpha.11/alpha.12.

## Compile Hotfix 1

The first user Windows compile of alpha.13 failed with one real error:

`CS7036` at `UI/CardchaMachineMenu.cs(227,45)` because the Machine -> Binder constructor call still used the old alpha.10/alpha.11 parameter list.

Fix applied:

- added the missing `this.Resources` argument immediately after `this.Save` in that `new CardchaBinderMenu(...)` call;
- re-audited every `new CardchaBinderMenu(...)` call site in `src/Cardcha`; all now match the constructor order `cards, save, resources, loadout, upgrades, renderer, onCloseToMachine, onLoadoutChanged, ...`;
- version remains `0.3.0-alpha.13` because no playable alpha.13 binary had been produced before this compile fix.

The analyzer warning `CS9057` and unused-field warning `CS0414` do not cause the build failure.

## Progression state preserved

- Current compatibility milestone remains 20 unique cards while testing.
- Approved future flow: 20 cards -> ChaCha info -> quest -> Boss -> Portable reward.
- Approved future flow: 40 cards -> quest/encounter -> ChaCha fuses stationary + portable machines -> Cardcha directly from Binder.

## Validation

Static validation passed for version consistency, 80-card registry, JSON/i18n, shop quantity markers, portable purchase state, MiMi identity markers, off-screen flight markers, new broom asset dimensions/checksum, +10% broom scale, and all Binder constructor call sites. Real Windows compilation is still required before declaring the hotfix playable.

Conversation artifacts:
- `Cardcha_v0.3.0-alpha.13_MimiShopFlight_CompileHotfix1_WindowsBuilder_FULL.zip`
- `Cardcha_v0.3.0-alpha.13_CompileHotfix1_SOURCE_SNAPSHOT.zip`
