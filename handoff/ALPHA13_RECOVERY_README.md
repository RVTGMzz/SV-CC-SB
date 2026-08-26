# Cardcha v0.3.0-alpha.13 recovery handoff

Prepared 2026-08-26 from the alpha.12 Binder Select + Resource Rail candidate.

## Candidate identity

- Version: `0.3.0-alpha.13`
- Build label: `Cardcha! v0.3.0-alpha.13 MIMI SHOP + FULL FLIGHT`
- Full Windows Builder artifact SHA-256: `1185b383d6c86c72c61a18af501e13ab9cfd8f18b9c82bbbf0a3bb6f7c324149`
- Source snapshot artifact SHA-256: `7ac088607566edc3a340c49fd4b5dc90c4b06c034b5d82349908bee44cc2d75a`
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

## Progression state preserved

- Current compatibility milestone remains 20 unique cards while testing.
- Approved future flow: 20 cards -> ChaCha info -> quest -> Boss -> Portable reward.
- Approved future flow: 40 cards -> quest/encounter -> ChaCha fuses stationary + portable machines -> Cardcha directly from Binder.

## Validation

Static validation passed 22/22 checks for version consistency, 80-card registry, JSON/i18n, shop quantity markers, portable purchase state, MiMi identity markers, off-screen flight markers, new broom asset dimensions/checksum, and +10% broom scale. Real Windows compilation is still required before declaring the candidate playable.
