# CARDCHA CURRENT HANDOFF

Prepared: 2026-09-14 (Asia/Ho_Chi_Minh)
Repository: `ronvotri/Cardcha-Shardbound`
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`

## Current workstream

**0696D2 Window Environment Matrix / exact D2.1 source recovery**

Safe runtime/build base:
`0.3.0-alpha.28.0.4.14.4.5.12.68`

Next candidate, intentionally **NOT materialized**:
`0.3.0-alpha.28.0.4.14.4.5.12.69`

Accepted independent D1S airship remains frozen:

- `src/Cardcha/assets/airship_props/set01_redux/window_runtime/observation_window_airship.png`
- 15x9 RGBA
- SHA256 `58caeabc94744ad04ae1f006c91e09bf9a55d5a211d53b426b12ca9d0dc1c9ce`

Navigation Console remains untouched/deferred.

## Exact D2.1 source gate

Required production files:

- `src/Cardcha/assets/airship_props/set01_redux/window_runtime/window_scene_default_morning_clear.png`
- `src/Cardcha/assets/airship_props/set01_redux/window_runtime/window_scene_default_noon_clear.png`
- `src/Cardcha/assets/airship_props/set01_redux/window_runtime/window_scene_default_evening_clear.png`
- `src/Cardcha/assets/airship_props/set01_redux/window_runtime/window_scene_default_night_clear.png`

Required SHA256:

- morning: `9a8996ef0068057e774419d9d4597f44753951b3ec1ec519cd6771efaad7b5d0`
- noon: `fa0f00051febb62d107e4a1dc14a079dbfc8183659a73b9ed2ecfe5c4efb3aff`
- evening: `b94d30d18bacecc2c3f09971aec2d5951956490be8c7cad2243b4689c865a638`
- night: `f9d15f66485f514f4be8589ee29d45beabda87e357b1c1d3ffa7965855ed1990`

Each must be exact PNG / 160x80 / RGBA byte streams.

Never redraw, regenerate, resize, recolor, re-encode, upscale, substitute, or reuse legacy observation overlays as D2 source art.

## Staged implementation

Already prepared behind the exact-source gate:

- `tools/alpha28_0696d2_window_environment_matrix.py`
- `.github/workflows/cardcha-alpha28-0696d2-window-environment-matrix.yml`
- `tools/alpha28_0696d2_package_audit.py`
- `tools/validate_0696d2_no_legacy_overlay_reuse.py`
- `tools/alpha28_0696d2_recover_exact_sources.py`

The recovery scanner only accepts authoritative SHA matches and refuses `--install` unless all four exact sources are present.

## Recovery closure

Primary recovery closure checkpoint:

`handoff/AIRSHIP_0696D2_ACCESSIBLE_SURFACES_EXHAUSTED.md`

All recovery surfaces currently accessible to this chat/tooling environment have been checked and documented without finding the four source byte streams.

Do **not** repeat these routes unless genuinely new evidence appears:

- Git lineage / target-path history / live 0696 branches;
- `.63 -> .68` package and artifact recovery;
- GitHub Actions concept/integration runs;
- File Library searches;
- recoverable conversation/personal-context provenance searches;
- connected Google Drive active + Trash searches;
- connected Gmail attachment searches;
- connected Canva design/folder searches;
- current sandbox residue;
- shared-chat public URL route;
- D2 materializer commit-window audit;
- GitHub Issues/PR/Releases collaboration surfaces;
- indexed public-web SHA/filename/archive searches.

Important provenance clue: conversation context proves a **hash-checked local materializer** was referenced immediately before the D2 checkpoint, but no helper/source bytes/path/attachment ID were committed. The strongest remaining explanation is a transient original-chat/local-sandbox/image-export step whose inputs were never persisted to currently accessible storage.

## Evidence files

- `handoff/LATEST_CARDCHA_HANDOFF.md`
- `handoff/AIRSHIP_0696D2_ACCESSIBLE_SURFACES_EXHAUSTED.md`
- `handoff/AIRSHIP_0696D2_SOURCE_RECOVERY_STATUS.md`
- `handoff/AIRSHIP_0696D2_D21_VISUAL_SOURCE_TRACE.md`
- `handoff/AIRSHIP_0696D2_RECOVERY_SCANNER_ARTIFACT_RETEST.json`
- `handoff/AIRSHIP_0696D2_CONCEPT_ACTIONS_EXHAUSTIVE_AUDIT.json`
- `handoff/AIRSHIP_0696D2_EXTERNAL_SOURCE_GOOGLE_DRIVE_AUDIT.md`
- `handoff/AIRSHIP_0696D2_EXTERNAL_SOURCE_CANVA_AUDIT.md`
- `handoff/AIRSHIP_0696D2_EXTERNAL_SOURCE_PUBLIC_WEB_AUDIT.md`
- `handoff/AIRSHIP_0696D2_GITHUB_NONACTIONS_SURFACE_AUDIT.md`
- `handoff/AIRSHIP_0696D2_LOCAL_MATERIALIZER_TRACE.md`
- `handoff/AIRSHIP_0696D2_PREIMPLEMENTATION_CHECKPOINT.md`

## Next allowed action

A genuinely new authoritative source must enter the workflow, especially one of:

- original D2.1 image-generation/export bytes from the old chat/session or local Downloads;
- a local-machine copy of `concept(1).rar` / `sprite(1).rar`;
- another original archive/folder/export;
- a newly connected storage location that actually contains those original files.

When a candidate exists:

```bash
python3 tools/alpha28_0696d2_recover_exact_sources.py /path/to/candidates
```

Only if all four exact SHA256 values are found:

```bash
python3 tools/alpha28_0696d2_recover_exact_sources.py /path/to/candidates --install
python3 tools/alpha28_0696d2_window_environment_matrix.py --check-source
python3 tools/alpha28_0696d2_window_environment_matrix.py --apply
python3 tools/alpha28_0696d2_window_environment_matrix.py --validate
```

Then:

`compile -> package audit -> .69 TEST -> Ron in-game visual acceptance`

## Hard stop

Until new authoritative source bytes are supplied or connected, further searches of already audited surfaces are duplicate work and must not be used to simulate progress.

`.69` remains intentionally unmaterialized.
