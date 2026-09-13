# CARDCHA CURRENT HANDOFF

Prepared: 2026-09-14 (Asia/Ho_Chi_Minh)
Repository: `ronvotri/Cardcha-Shardbound`
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
Pre-handoff branch HEAD: `996b032a74652476847f550c0bcd1dd03bcce263`

## Resume instruction

Continue Cardcha from this file and `handoff/LATEST_CARDCHA_HANDOFF.md` on branch `cardcha-alpha28-0696d2-window-environment-matrix`.

Current workstream is **0696D2 Window Environment Matrix / exact D2.1 source recovery**. The runtime/resolver/package path is staged, but `.69` is intentionally blocked until the four exact approved D2.1 environment PNG byte streams are recovered.

Do **not** redo completed GitHub Actions provenance audits, the existing File Library sweep, the completed connected-Drive sweep, or generate substitute artwork.

## Frozen safe base

Current safe runtime/build base:

`0.3.0-alpha.28.0.4.14.4.5.12.68`

Next candidate, **not materialized**:

`0.3.0-alpha.28.0.4.14.4.5.12.69`

Accepted independent D1S airship:

- path: `src/Cardcha/assets/airship_props/set01_redux/window_runtime/observation_window_airship.png`
- dimensions: `15x9 RGBA`
- SHA256: `58caeabc94744ad04ae1f006c91e09bf9a55d5a211d53b426b12ca9d0dc1c9ce`

Navigation Console remains untouched/deferred.

## Exact D2.1 source gate

Required production files:

- `src/Cardcha/assets/airship_props/set01_redux/window_runtime/window_scene_default_morning_clear.png`
- `src/Cardcha/assets/airship_props/set01_redux/window_runtime/window_scene_default_noon_clear.png`
- `src/Cardcha/assets/airship_props/set01_redux/window_runtime/window_scene_default_evening_clear.png`
- `src/Cardcha/assets/airship_props/set01_redux/window_runtime/window_scene_default_night_clear.png`

Each source must be exact PNG / 160x80 / RGBA and match:

- morning: `9a8996ef0068057e774419d9d4597f44753951b3ec1ec519cd6771efaad7b5d0`
- noon: `fa0f00051febb62d107e4a1dc14a079dbfc8183659a73b9ed2ecfe5c4efb3aff`
- evening: `b94d30d18bacecc2c3f09971aec2d5951956490be8c7cad2243b4689c865a638`
- night: `f9d15f66485f514f4be8589ee29d45beabda87e357b1c1d3ffa7965855ed1990`

Never redraw, regenerate, resize, recolor, re-encode, upscale, or substitute these images. Never reuse legacy `observation_window_overlay_2.png`, `_3.png`, or `_4.png` as D2 environments.

## What is already staged

Main implementation tool:

`tools/alpha28_0696d2_window_environment_matrix.py`

It already contains:

- exact source SHA gate;
- 160x80 PNG/RGBA validation;
- four clear time buckets;
- D1S ship hash freeze;
- D2 resolver/runtime materialization;
- `.68 -> .69` version transition;
- D2 manifest update;
- validation report generation.

Workflow:

`.github/workflows/cardcha-alpha28-0696d2-window-environment-matrix.yml`

Package audit:

`tools/alpha28_0696d2_package_audit.py`

Legacy-overlay guard:

`tools/validate_0696d2_no_legacy_overlay_reuse.py`

Exact-source recovery scanner:

`tools/alpha28_0696d2_recover_exact_sources.py`

The recovery scanner can recursively inspect loose PNGs, directories, ZIPs, nested ZIPs and RARs when 7-Zip is available. It matches only the four authoritative SHA256 values. `--install` refuses to write production files unless all four exact sources are found, and copies bytes without image transformation.

## Recovery work already exhausted

Do not repeat these investigations unless genuinely new evidence appears:

1. current Git lineage and exact target-path history;
2. all four relevant live 0696 branches;
3. `.65` D1 package;
4. `.68` D1S package;
5. all 160x80 PNGs inside `.68`;
6. File Library searches for filenames, hashes, archive names, visual descriptors and date-range uploads;
7. recoverable conversation metadata around D2.1 visual approval/source identifiers;
8. surviving `.63 -> .68` Actions artifacts using the recursive scanner;
9. all **14** Actions runs on `cardcha-alpha28-0696-airship-concept-faithful-visible-integration`;
10. connected Google Drive exact archive/project search;
11. connected Google Drive generic image/export-name sweep;
12. connected Google Drive PNG MIME/date sweep for 2026-09-13;
13. D2 branch commit window around the original local-materializer step;
14. current sandbox residue check;
15. public shared-chat URL fetch/index attempt.

Concept/integration Actions audit result:

- 14 total runs enumerated;
- 5 successful runs had surviving package artifacts;
- recursive scan traversed 10 ZIP layers;
- 837 PNGs inspected;
- 38 PNGs were 160x80;
- 9 unique 160x80 hashes;
- **0/4 approved D2 SHA matches**;
- 9 failed runs individually checked;
- 8 failed runs had no artifact;
- the only surviving failed-run artifact was a pre-0696A full-footprint audit containing one 660x1160 PNG;
- therefore concept-branch GitHub Actions is **EXHAUSTED as a recovery source**.

Earlier `.63 -> .68` scanner retest also found **0/4 approved SHA matches**.

## Google Drive external-source audit

Exact archive/project searches and generic image-name searches produced no authoritative source.

Three generic-name candidates were downloaded as exact bytes and rejected without transformation:

- `normal_morning_sun.png` -> `640x464 RGBA`, SHA256 `09a9ab17bf17d774e8aaa4840729ba681b9d744d0c99cdf05685c02892226bd7`
- `cool-night.png` -> `1024x32 RGB`, SHA256 `62179a3f8cef2871c2e4d41128c41a7178e2ccf1487af63f83c05e69abe2abec`
- `moonlit.png` -> `1024x32 RGB`, SHA256 `1820cb32c385f445ffb854ab9941d4263eb609a269ec07d784d7d2fbff72782f`

All fail the 160x80 RGBA / authoritative-SHA contract.

A filename-independent Drive query for PNGs created on 2026-09-13 returned **0 files** on the currently accessible Drive surface.

## Local materializer trace

Recoverable conversation context adds a useful provenance clue:

- around `2026-09-13 05:58 UTC`, the assistant said the approved images would go through a **hash-checked materializer** because the GitHub connector could not directly accept local PNG bytes;
- around `06:00 UTC`, the four Morning/Noon/Evening/Night scenes were described as standardized to production `160x80` with source hashes checkpointed.

Direct D2-branch commit enumeration for `05:30 -> 06:40 UTC` found exactly one commit:

- `1ad582226c3966d31afa688b030df24f74f4be3e`
- `2026-09-13T06:29:33Z`
- `docs: checkpoint 0696D2 environment matrix before implementation`

Existing provenance audit proves that commit adds only the checkpoint document, not PNGs, a helper/materializer, archive, local path, or attachment ID.

Repository searches for `materializer`, `materialize`, and `D2.1` exposed no committed helper. The strongest surviving interpretation is that the exact source/preparation step lived only in the original chat/local sandbox or image-generation/export context and was never persisted to Git.

The current `/mnt/data` contains only the three newly downloaded Drive false-positive candidates above; no prior-session D2.1 source residue exists there.

The previously supplied shared ChatGPT URL did not expose a retrievable public conversation payload or indexed copy, so no attachment/image-generation identifier was recovered from that route.

## Provenance clue still relevant

Earlier source documentation mentions direct user uploads:

- `concept(1).rar`, expected 6 PNGs;
- `sprite(1).rar`, expected 22 PNGs.

Those archives were not successfully extracted in the original environment, so inner filenames/bytes were never preserved in Git metadata.

Separately, D2.1 had four visual states approved in chat on 2026-09-13:

- morning: pale blue;
- noon: brightest clear blue;
- evening: orange-purple sunset;
- night: deep blue with moon/stars.

The exact four SHA fingerprints survived, but the original attachment/image-export byte streams do not currently exist in repository/File Library/connected-Drive/current-sandbox-accessible storage.

## Key evidence files

Read these before doing more recovery work:

- `handoff/LATEST_CARDCHA_HANDOFF.md`
- `handoff/AIRSHIP_0696D2_SOURCE_RECOVERY_STATUS.md`
- `handoff/AIRSHIP_0696D2_D21_VISUAL_SOURCE_TRACE.md`
- `handoff/AIRSHIP_0696D2_RECOVERY_SCANNER_ARTIFACT_RETEST.json`
- `handoff/AIRSHIP_0696D2_CONCEPT_ACTIONS_EXHAUSTIVE_AUDIT.json`
- `handoff/AIRSHIP_0696D2_EXTERNAL_SOURCE_GOOGLE_DRIVE_AUDIT.md`
- `handoff/AIRSHIP_0696D2_LOCAL_MATERIALIZER_TRACE.md`
- `handoff/AIRSHIP_0696D2_PREIMPLEMENTATION_CHECKPOINT.md`

## Next allowed action

The remaining safe recovery route is an **authoritative external/local source copy not presently exposed through the repository, File Library, connected Google Drive, shared-chat public surface, or current sandbox**, especially:

- original D2.1 image-generation/export attachment bytes from the original chat/session;
- a local-machine copy of `concept(1).rar` / `sprite(1).rar`;
- another local archive/folder/export that might contain the exact approved files.

When a candidate source appears, run:

```bash
python3 tools/alpha28_0696d2_recover_exact_sources.py /path/to/candidates
```

Only if all four exact hashes are found:

```bash
python3 tools/alpha28_0696d2_recover_exact_sources.py /path/to/candidates --install
python3 tools/alpha28_0696d2_window_environment_matrix.py --check-source
python3 tools/alpha28_0696d2_window_environment_matrix.py --apply
python3 tools/alpha28_0696d2_window_environment_matrix.py --validate
```

Then:

1. compile Cardcha Release;
2. package `.69` TEST;
3. run `alpha28_0696d2_package_audit.py`;
4. preserve D1S ship and Navigation Console invariants;
5. Ron performs in-game visual acceptance;
6. only after D2.1 visual PASS proceed to later weather/season work and D3 Navigation Console.

## Hard stop

Do not create a fake `.69` using legacy 128x42 backgrounds or regenerated lookalikes. Current blocker is **exact source recovery**, not implementation.
