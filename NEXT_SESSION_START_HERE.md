# NEXT SESSION — Cardcha Alpha.27

> **READ FIRST:** `docs/PROJECT_WORKING_RULES.md` and `handoff/ALPHA27_0771_NEXT_SESSION_HANDOFF.md`.
>
> The detailed, current handoff is now in `handoff/ALPHA27_0771_NEXT_SESSION_HANDOFF.md`. Treat that file as the authoritative continuation point for the next chat/session.

## Branch safety

- Repo: `ronvotri/Cardcha-Shardbound`
- Active development branch: `cardcha-alpha27-mimi-real-npc`
- `main` remains rollback baseline `v0.3.0-alpha.26.5.3` at commit `2fae8a1f8b54d7bc292d8ec7f3acc5f2867c6d5c`.
- Do **not** merge alpha.27 into `main` unless the user explicitly asks to promote a milestone.
- Ignore/do not merge the accidental temporary branch `Commit-directly-to-the-cardcha-alpha27-mimi-real-npc-branch`; it was created from `main` and contains PNGs at repo root.

## Current build state

Latest real CI milestone:
- `0.3.0-alpha.27.0.7.7 — MiMi Attic Acceptance Polish`
- Workflow run `33198254924`: SUCCESS
- Artifact ID `9696666852`

Latest local TEST hotfix:
- `0.3.0-alpha.27.0.7.7.1 — BroomAndBinderPreviewHotfix`
- SHA256 `fa889b75df7760950d9f80b8b724d60dd8a0f9ec38ff9e8e68f5459d7f3f3f64`
- IMPORTANT: 0.7.7.1 is local/package-only so far; it is not yet the canonical GitHub/CI source milestone.

## Immediate next work

1. Integrate the user's new MiMi broom sheet properly into source. Source image is 192x192, 4x4, 48x48 frames. Prefer a non-distorting runtime mapping; the quick local package squeezed frames to 32x48 for compatibility.
2. Remove the Binder `binder.status.preview` line at **source draw/request level**. Do not rely on an empty i18n string, because an empty translation can render as `(no translation:binder.status.preview)`.
3. NEVER proactively modify `src/Cardcha/assets/mimi_walk.png`; it is user-locked artwork unless the user explicitly requests a change.
4. Keep `mimi_social_mugshot.png` isolated from world animation.
5. Verify/clean stale canonical guard metadata only after real RGBA hash checks. Guard must fail closed and must not restore old art.
6. Run real CI, verify package, then ask the user for **one consolidated in-game test**, not repeated micro-tests.

## Consolidated test scope after CI

Use `cardcha_test_attic` to validate attic without changing friendship/story. Normal access remains MiMi meetup + 2 hearts.

Ask the user to verify in one session:
- WizardHouse attic stair/entrance placement;
- sofa/TV spacing and usability;
- rug under bed and pirate/skull decoration removal;
- continuous/tidy attic wall shell;
- attic enter/exit without TMX crash/lag;
- MiMi world animation unaffected by Social UI;
- Friend List mugshot visible/crisp and portrait size reasonable;
- ChaCha Resonance uses static `chacha_portrait.png`;
- reveal popup translation is correct;
- Binder preview status line is fully gone;
- new MiMi broom animation looks correct and is not horizontally distorted.

## Scope discipline

Do not start a major new feature until this visual/UI/social acceptance pass is approved. TV secret / full heart-event / ChaCha upgrade mechanics remain future work.
