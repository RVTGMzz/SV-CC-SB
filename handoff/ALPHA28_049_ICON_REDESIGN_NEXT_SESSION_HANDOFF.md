# Cardcha Alpha.28.0.4.9 — Icon Redesign Next-Session Handoff

Updated: 2026-08-31

## Start here

Continue on branch:

`cardcha-alpha28-049-icon-stroke-spacing-locked`

Canonical tested source commit before this handoff:

`b09d1c6e39d5f865ea54f8350c5ba5322edd257f`

Current mod version:

`0.3.0-alpha.28.0.4.9`

Next-session prompt:

> Continue Cardcha from `handoff/ALPHA28_049_ICON_REDESIGN_NEXT_SESSION_HANDOFF.md`.

## Last known-good build

- Package: `Cardcha_v0.3.0-alpha.28.0.4.9_PastelTarotIconOnlyStroke_TEST.zip`
- Package SHA-256: `87e7f2e971d7c5ec830cd882ca06f4b0cf12d0a0320a0261d714b8ca6ddb2b7a`
- GitHub Actions run: `33362216671`
- Result: PASS
- Current `src/Cardcha/assets/card_icons.png` SHA-256: `8d1596a6942f8689b1d40c0148c4a551b9a2d41665e6cfe26fd3cf7f7343c736`

The `.4.9` asset is safe and drop-in compatible, but it is **not the user's final selected artwork**. It is a softened/recolored version of the original icons with an internal warm stroke.

## User's final visual correction

The user wants the actual pastel tarot artwork from the selected design reference, not merely recolored original artwork.

Use these committed references:

- Desired artwork reference: `handoff/assets/alpha28_desired_pastel_icons_70.png`
- Exact original layout reference: `handoff/assets/alpha28_original_card_icons_80.png`

Reference hashes:

- Desired 70-icon reference SHA-256: `f827fdf051706ce15fb06e092796be42867839602dd1c4d504f6326c92645a90`
- Original 80-icon sheet SHA-256: `c313ea2f80f8ca2363e7341120a44ba8913ea85c24c25d8b692ad98b399c1d11`

## Blocking mismatch — do not guess

The selected design reference contains only:

- 14 rows × 5 columns = 70 icons

The original Cardcha sheet contains:

- 16 rows × 5 columns = 80 icons

Therefore the final 10 designs (the last two rows) are missing. No final asset or new build was made from the selected reference.

At the start of the next session, ask the user to choose one of these before editing:

1. Supply the missing 10 designed icons.
2. Use the selected design for the first 70 icons and retain the existing last 10.
3. Generate/redesign the missing 10 in the exact selected style.

## Locked sprite-sheet constraints

The final `card_icons.png` must satisfy all of the following:

- Exact canvas: `320 × 1024`.
- Exact grid: 5 columns × 16 rows.
- Exact cell size: `64 × 64`.
- Preserve original icon order and corresponding cell positions from the 80-icon reference.
- Each redesigned motif must be fitted to the matching original icon footprint/center so the file can be replaced directly.
- Genuine RGBA transparency outside motifs.
- No baked checkerboard.
- No square/card backgrounds.
- No per-cell frames, ribbons, plaques, or corner decorations.
- Stroke follows the icon silhouette only.
- Stroke should be warm brown/muted gold, balanced with Stardew Valley's palette.
- Prevent pixels from bleeding into neighboring 64×64 cells.
- Do not change Binder coordinate logic or add runtime compensation for artwork alignment.

## Recommended implementation order

1. Resolve the missing 10-icon decision with the user.
2. Extract the 70 selected motifs from the desired reference and remove its baked checkerboard/background.
3. Process each icon independently, in row-major order.
4. Fit each motif to the corresponding original icon's center and footprint inside its 64×64 cell.
5. Add/retain the final 10 icons according to the user's decision.
6. Export a genuine transparent RGBA `320×1024` sheet.
7. Validate all 80 cells for ordering, bounds, centers, alpha, and cross-cell bleed.
8. Show the final sheet to the user before replacing the repository asset.
9. Only after approval, create the next version/branch (suggested `.4.10`) and run CI/package validation.

## Regression guards

This next task is visual-only until the user approves the completed 80-icon sheet. Do not modify:

- Airship flight animation or final airship design.
- Airship Deck, Sky Dock Interior, or Region I maps.
- Binder/controller input behavior.
- MiMi assets or behavior.
- Flight fees, Boss Gate, combat drops, Scrap, or card-drop logic.

Keep `.4.9` as the fallback tested build until the redesigned 80-icon asset is complete and approved.
