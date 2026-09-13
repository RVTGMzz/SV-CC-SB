# AIRSHIP 0696D2 External Source Recovery: Google Drive Audit

Date: 2026-09-14
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
Pre-audit HEAD: `e24f9423bec305bfb81f3de730534d1ac297bfc3`
Scope: exact D2.1 source recovery only. GitHub Actions/artifact provenance was intentionally not re-audited.

## Purpose

Test the remaining authoritative-external-source route against the currently connected Google Drive surface without weakening the four-file exact SHA gate.

Required D2.1 SHA256 identities remain:

- morning: `9a8996ef0068057e774419d9d4597f44753951b3ec1ec519cd6771efaad7b5d0`
- noon: `fa0f00051febb62d107e4a1dc14a079dbfc8183659a73b9ed2ecfe5c4efb3aff`
- evening: `b94d30d18bacecc2c3f09971aec2d5951956490be8c7cad2243b4689c865a638`
- night: `f9d15f66485f514f4be8589ee29d45beabda87e357b1c1d3ffa7965855ed1990`

No candidate is accepted by name or visual similarity. Only exact byte/hash identity can close the gate.

## Exact-name / project searches

Drive searches were performed for the remaining provenance aliases and production terminology:

- `concept(1).rar` -> no result
- `sprite(1).rar` -> no result
- `concept rar` -> no result
- `window_scene_default` -> no result
- `airship` -> no result
- `0696` -> no result
- `Cardcha` -> only Cardcha design/tracker documents surfaced; no D2.1 PNG, source archive, export folder, or Cardcha asset pack

A broad `window` search returned unrelated documents/folders and no Cardcha/D2.1 source candidate.

## Root Drive archive check

The visible root Drive listing was inspected directly.

Archive-like files visible there were unrelated and predated D2.1:

- `DragonSword.Awakening.v1.0.10_LinkNeverDie.Com.rar` — created 2026-09-08
- `New folder.rar` — created 2026-09-03
- `GameFiles.zip` — created 2026-09-03

No visible root archive named `concept(1).rar`, `sprite(1).rar`, or otherwise plausibly tied to Cardcha 0696/D2.1 was present.

The root listing also contained the Cardcha Master Design Bible and BaseSet80 tracker, confirming Cardcha-related Drive content is indexed, but no corresponding Cardcha source-art archive/folder surfaced.

## False-positive folders inspected

### `sprites`

A Drive search for `sprite` surfaced a folder named `sprites`.
Direct folder inspection showed only:

- `fireside-journal.png`
- `earl-grey-tea.png`

This is unrelated Stardew/Fireside content and is not a Cardcha source lead.

### `Hình ảnh`

A date-oriented Drive search surfaced a folder named `Hình ảnh` created on 2026-09-12.
Direct inspection showed Steam-style art files:

- `icon.png`
- `Logo.png`
- `Wide Capsule.png`
- `hero.png`
- `Capsule.png`

Its parent folder is `Doraemon Monopoly`, alongside `Doraemon Cờ Tỷ phú.rar`. Therefore it is unrelated to Cardcha D2.1.

### `stardew valley`

The visible direct children are mod/localization folders such as PelipperTown, Ownership Marker, Evelyn's Fireside Tales, PokeFarmRetextures, and SDV-Radiance. No Cardcha folder/source pack is present in that visible set.

## Expanded generic-export-name sweep

Because image-generation/export files can survive under generic names instead of production names, a second sweep searched image metadata for:

- `morning`
- `noon`
- `evening`
- `night`
- `sunset`
- `moon`
- `sky`
- `dawn`
- `day`
- `stars`
- `clear`
- `morning clear`
- `noon clear`
- `evening clear`
- `night clear`
- `ChatGPT Image`
- `imagegen`

Most searches returned no plausible D2.1 image. `day` returned unrelated design/media assets. `dawn` returned a Stardew item-style asset (`dawn_stone_stardew.png`) and was rejected by provenance/name before download.

Three image files were plausible enough by title to download as exact bytes and inspect directly:

| Drive title | Exact downloaded SHA256 | Dimensions / mode | D2.1 result |
|---|---|---|---|
| `normal_morning_sun.png` | `09a9ab17bf17d774e8aaa4840729ba681b9d744d0c99cdf05685c02892226bd7` | `640x464 RGBA` | reject: wrong size and wrong SHA |
| `cool-night.png` | `62179a3f8cef2871c2e4d41128c41a7178e2ccf1487af63f83c05e69abe2abec` | `1024x32 RGB` | reject: wrong size, mode and SHA |
| `moonlit.png` | `1820cb32c385f445ffb854ab9941d4263eb609a269ec07d784d7d2fbff72782f` | `1024x32 RGB` | reject: wrong size, mode and SHA |

The raw bytes were inspected without resize/re-encode/editing. None are production D2.1 sources.

## Date/MIME sweep

Drive was also queried directly by metadata rather than filename:

- MIME: `image/png`
- created: `2026-09-13T00:00:00Z <= createdTime < 2026-09-14T00:00:00Z`

Result: **0 PNG files** on the currently accessible active Drive surface for that D2.1 approval/materialization date.

This removes the main filename-independent active-Drive recovery path for an image exported or uploaded on the approval day.

## Trash sweep

The Drive Trash surface was checked separately so a source uploaded and later deleted would not be missed.

Targeted trashed-file searches:

- `concept` -> 0
- `sprite` -> 0
- `Cardcha` -> 0
- `airship` -> 0

A filename-independent trashed-PNG query for files created during `2026-09-12T00:00:00Z -> 2026-09-14T00:00:00Z` also returned **0 files**.

Therefore no source-pack alias, Cardcha/Airship candidate, or D2.1-date PNG survives in the currently accessible Drive Trash surface.

## Result

**0 authoritative D2.1 source candidates found on the currently accessible Google Drive active or Trash surfaces.**

No file was installed, transformed, re-encoded, resized, recolored, or used as a substitute. No `.69` materialization was attempted.

Downloaded generic-name candidates were only hash/dimension/mode inspected and rejected. Nothing was copied into production paths.

## Recovery state after this audit

The following routes are now documented as exhausted or nonproductive unless new evidence appears:

- Git history/live 0696 branches/path history
- surviving `.63 -> .68` artifacts
- all concept/integration GitHub Actions runs
- File Library targeted/date-range searches
- recoverable conversation metadata/personal-context source-id trace
- connected Google Drive exact-name/project/archive search
- connected Google Drive generic image-name search
- connected Google Drive 2026-09-13 active PNG MIME/date search
- connected Google Drive Trash exact-name and 2026-09-12/13 PNG sweep

The remaining legitimate source route is still an authoritative external/local copy not presently exposed through the connected repository/File Library/Drive surfaces, especially:

1. original D2.1 image-generation/export attachment bytes from the original chat/session;
2. a local-machine copy of `concept(1).rar` / `sprite(1).rar`;
3. another local archive/folder/export whose extracted files independently match all four authoritative SHA256 values.

## Hard gate unchanged

Do not materialize `.69` until all four exact byte streams are recovered and pass:

```bash
python3 tools/alpha28_0696d2_recover_exact_sources.py /path/to/candidates
python3 tools/alpha28_0696d2_recover_exact_sources.py /path/to/candidates --install
python3 tools/alpha28_0696d2_window_environment_matrix.py --check-source
```

Only then continue `--apply -> --validate -> compile -> package audit -> .69 TEST -> Ron visual acceptance`.
