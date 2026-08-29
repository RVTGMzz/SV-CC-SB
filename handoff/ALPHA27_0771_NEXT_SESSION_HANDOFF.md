# Cardcha-Shardbound — Alpha27 0.7.7.1 next-session handoff

Updated: 2026-08-29

## Repository / branch safety

- Repo: `ronvotri/Cardcha-Shardbound`
- Active development branch: `cardcha-alpha27-mimi-real-npc`
- `main` is rollback baseline and must stay untouched unless the user explicitly asks to promote a milestone.
- `main` baseline currently points to commit `2fae8a1f8b54d7bc292d8ec7f3acc5f2867c6d5c` (`source: promote alpha26.5.3 baseline to main`).
- There is an accidental temporary branch named `Commit-directly-to-the-cardcha-alpha27-mimi-real-npc-branch` created from `main`, commit `94bc5be1d8ac4cc65c893cebbd5a48d220b3dd0f`. It contains four PNGs at repo root. DO NOT merge that branch into `main`. It can be deleted later after source/canonical verification.

## User workflow preference

The user does not want to repeatedly quit/re-enter Stardew Valley for micro-tests. Finish source changes, static validation, compile, package, and CI checks first; only then ask for one consolidated in-game test.

Before every TEST ZIP, state prerequisites, how to access/test, debug bypass if available, what to verify, and anything intentionally out of scope.

## Hard artwork rule

- NEVER proactively modify `src/Cardcha/assets/mimi_walk.png` unless the user explicitly requests it.
- Treat the latest user-approved `mimi_walk.png` as read-only artwork.
- `mimi_social_mugshot.png` is a dedicated Social/Friend-list asset and must remain isolated from world animation.
- Do not solve Social UI by carving/painting into `mimi_walk.png`.
- Pixel-art resizing must use nearest-neighbor; no blur/antialias.

## Latest CI milestone

`0.3.0-alpha.27.0.7.7` MiMi Attic Acceptance Polish compiled and packaged successfully.

- Workflow run: `33198254924`
- Artifact ID: `9696666852`
- Artifact: `cardcha-alpha27-077-attic-acceptance-polish`
- CI artifact digest: `sha256:f05bde47ee9189f359bd7f95f8bb957b6228610a422e3311264317744309e7ec`

The 0.7.7 source includes the attic acceptance pass: WizardHouse attic entrance placement pass, sofa/TV spacing pass, large bed rug, pirate/skull decoration removal, cleaner attic shell, strict TMX validation, MiMi social mugshot, and ChaCha portrait integration. These visual changes are still awaiting the user's consolidated in-game acceptance test.

Normal attic access requires MiMi meetup + 2 hearts. Runtime test bypass: `cardcha_test_attic`.

## Latest local hotfix — NOT YET canonical GitHub source

A local package was made as:

`Cardcha_v0.3.0-alpha.27.0.7.7.1_BroomAndBinderPreviewHotfix_TEST.zip`

SHA256:
`fa889b75df7760950d9f80b8b724d60dd8a0f9ec38ff9e8e68f5459d7f3f3f64`

This is NOT yet the canonical CI/source milestone. Do not assume GitHub source contains these two changes.

### Change A — new MiMi broom artwork

The user supplied and approved a new square `192x192` MiMi-on-broom sprite sheet. It is a 4x4 sheet, so each source frame is `48x48`.

The quick local 0.7.7.1 package adapted it to the existing `mimi_broom.png` layout (`128x192`, 4x4 frames of `32x48`) by nearest-neighbor resizing each 48x48 frame to 32x48.

IMPORTANT: this is a provisional compatibility adaptation and may squeeze the artwork horizontally. In the next session, inspect the broom animation code first. Prefer supporting the user's native 48x48 frames (or another non-distorting mapping) if the runtime can be changed safely. Do not alter `mimi_walk.png`.

Goal: the new user artwork becomes the canonical broom animation asset, isolated from normal walking animation.

### Change B — Binder preview line

User wants the line that renders as:

`(no translation:binder.status.preview)`

removed completely from Cardcha Binder card-detail UI.

The local 0.7.7.1 package only blanked `binder.status.preview`, `binder.status.pick`, and `binder.status.selected` in EN/VI i18n. That is NOT a robust final fix because an empty translation may itself be treated as missing and render `(no translation:...)`.

FINAL FIX REQUIRED: locate the Binder UI draw/status call and stop drawing/requesting `binder.status.preview` for that card-detail area. Do not merely blank the translation value.

## Canonical visual/source-sync situation

The active branch already contains these files at the correct paths:

- `src/Cardcha/assets/card_icons.png`
- `src/Cardcha/assets/chacha_follow.png`
- `src/Cardcha/assets/chacha_machine.png`
- `src/Cardcha/assets/mimi_walk.png`
- `src/Cardcha/assets/chacha_portrait.png`

The accidental branch upload placed four PNGs at repo root, but their Git blob SHAs matched the active branch copies for `card_icons`, `chacha_follow`, `chacha_machine`, and `mimi_walk`. Therefore do NOT merge the accidental branch.

Some canonical guard metadata is stale. In particular `build_assets/canonical_sprites/STATUS.txt` and `.pending_four_visuals` still say four visuals are pending. `SOURCE_SYNC_TARGETS.txt` lists `chacha_follow`, `chacha_machine`, `card_icons`, `chacha_portrait`.

Approved RGBA hashes recorded in `build_assets/canonical_sprites/APPROVED_HASHES_077.txt` are:

- `chacha_follow.png` `b2f975ad72249cda5c5629e4476b7fe25da4a333d62ef2675444ea7ac8a038b4`
- `chacha_machine.png` `12079224049ae520159c783b3e464ac204256f04092540981b4d4fe8ba9a32e1`
- `card_icons.png` `b2a8c9f0a0f46ef8efb55c7d7bdacb9157934e287c33873f885056fc1e2e799b`
- `chacha_portrait.png` `088c8b0599d3deda2ba0c87066948c970bdccc38398611a290acb6d936a2133f`
- `mimi_walk.png` `b3e2beebef6d9d4f9c830c9a70534eb96b1bf147581bc128c23808a7dd669a53`
- `mimi_social_mugshot.png` `99a617596e0965bc88c741138cef2930520af32aac597981d7084ef2629ec5b9`

Before changing guard metadata, verify actual RGBA hashes on the active branch. Guard should fail closed rather than restore old art. `mimi_walk.png` and `mimi_social_mugshot.png` should remain verify-only / non-destructive.

## MiMi social / portrait state

- Dedicated `mimi_social_mugshot.png` target is 16x24.
- User earlier exported it at 1.5x due Canva limits; downscale to x1 with nearest-neighbor only.
- Friend-list mugshot must not disappear and must not corrupt world animation.
- User requested MiMi's larger social/gift portrait to appear about 4/7 of the previous oversized presentation.
- ChaCha main Resonance avatar must use `assets/chacha_portrait.png`, not `chacha_follow.png`.

## Attic visual checklist still awaiting user acceptance

In one consolidated game test, ask the user to check:

1. WizardHouse attic entrance/stair appears at the requested upper-right nook and feels like a vanilla Stardew stair/ladder.
2. Green sofa is close enough to wall, farther from TV, and remains usable.
3. Large rug sits under bed; pirate/skull flag is gone / bed looks appropriate.
4. Attic wall shell and corners are continuous and tidy like a normal Stardew interior.
5. `cardcha_test_attic` enters/exits without TMX crash or lag loop.
6. MiMi world animation is unchanged by Social UI work.
7. MiMi Friend List mugshot is visible/crisp and portrait sizing is reasonable.
8. ChaCha Resonance uses the static approved portrait.
9. Reveal popup no longer shows missing `reveal.info.close` translation.
10. Binder no longer shows the preview status line requested for removal.
11. New MiMi broom animation looks correct in all directions/frames and is not horizontally distorted.

## Recommended next-session order

1. Read this file and `docs/PROJECT_WORKING_RULES.md`.
2. Fetch current head of `cardcha-alpha27-mimi-real-npc`; do not work from `main`.
3. Inspect broom animation code and integrate the new 192x192 / 48x48-frame user sheet without distorting it if possible.
4. Remove the Binder `binder.status.preview` draw/request at source level.
5. Leave `mimi_walk.png` untouched.
6. Verify/clean canonical guard metadata only after actual RGBA hash checks; do not let infrastructure delay the gameplay TEST again.
7. Build via real CI, package one TEST ZIP, verify DLL/manifest/i18n/TMX/assets, then ask the user for one consolidated in-game test.

## Scope discipline

Do not start a major new feature until this visual/UI/social regression pass is accepted. TV secret remains future content (6 hearts, around 17:30 hook) and is not part of this acceptance build.
