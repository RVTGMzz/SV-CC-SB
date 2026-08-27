# Cardcha v0.3.0-alpha.11 recovery handoff

This handoff preserves the exact semantic delta for the alpha.11 candidate prepared on 2026-08-26.

## Baseline

- Repository: `ronvotri/Cardcha-Shardbound`
- Branch used for development: `binder-v0.3-alpha1`
- Confirmed alpha.10 source baseline commit: `b58f5e929c1433c5a4cbf4726d2bfd64e6548251`
- Baseline message: `feat: update Cardcha v0.3.0-alpha.10`

## Candidate

- Local semantic candidate commit: `928e6d44b5ae8b46a2f618c985fb2c95d3ce21fe`
- Message: `feat: Cardcha v0.3.0-alpha.11 Binder input and full flash`
- Target version/build label: `Cardcha! v0.3.0-alpha.11 BINDER INPUT + FULL FLASH`

The source files on this GitHub branch may still show alpha.10 because the candidate was prepared in an offline working tree without shell GitHub credentials. The exact patch is preserved in four ordered files here:

1. `handoff/alpha11_recovery_part1.patch`
2. `handoff/alpha11_recovery_part2.patch`
3. `handoff/alpha11_recovery_part3.patch`
4. `handoff/alpha11_recovery_part4.patch`

To reconstruct the candidate, concatenate those four files in order into one `.patch`, reset/check out baseline commit `b58f5e929c1433c5a4cbf4726d2bfd64e6548251`, then apply the combined patch.

## Alpha.11 scope

- Binder Favorite / Equip / Upgrade actions work with controller A and keyboard Enter/Space.
- B/Escape closes/returns; A never closes the Binder.
- Double mouse click or double confirm on the same card within 600ms toggles equip/unequip.
- Gacha ritual/reveal uses full-cell/full-panel flash instead of a tiny local flicker.
- Portable milestone EN/VI is synchronized to 20 unique cards.
- Visible `Túi đồ` and `Bộ bài đang dùng` text is removed.
- `Trang x/y` stays in its current footer position; compact `Đã khám phá x/80 lá` is placed to its left.
- Five normal slots + Boss + ChaCha/Secret are equal-size enlarged circles.
- Boss uses Mythic border, no BOSS text.
- ChaCha/Secret uses pink border, no SECRET text.
- Vietnamese rarity tabs were widened to reduce clipping.

## Progression design recorded, not fully implemented in alpha.11

- 20 unique cards → ChaCha info begins unlocking → quest → Boss encounter → Portable Machine reward.
- 40 unique cards → quest/encounter → ChaCha absorbs/fuses stationary + portable machines → direct Cardcha access from Binder.
- Current direct 20-card portable gift is only a temporary compatibility bridge until that quest/Boss flow is coded.

## Validation

Static validation passed for JSON/card registry/version consistency and the modified C# structure. A real Windows compile with Stardew Valley + SMAPI references is still required before treating alpha.11 as a playable build.

Conversation artifact name: `Cardcha_v0.3.0-alpha.11_BinderInputFullFlash_WindowsBuilder_FULL.zip`.
