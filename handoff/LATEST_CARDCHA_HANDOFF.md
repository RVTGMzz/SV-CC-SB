# LATEST CARDCHA HANDOFF

Updated: 2026-09-13

## Current workstream
`cardcha-alpha28-0696d2-window-environment-matrix`

Current safe base:
`0.3.0-alpha.28.0.4.14.4.5.12.68`

Next build candidate, **NOT YET MATERIALIZED**:
`0.3.0-alpha.28.0.4.14.4.5.12.69`

Current source-recovery handoffs:
- `handoff/AIRSHIP_0696D2_SOURCE_RECOVERY_STATUS.md`
- `handoff/AIRSHIP_0696D2_D21_VISUAL_SOURCE_TRACE.md`
- `handoff/AIRSHIP_0696D2_RECOVERY_SCANNER_ARTIFACT_RETEST.json`

Current recovery tool:
`tools/alpha28_0696d2_recover_exact_sources.py`

## Status
- 0696D1S `.68` is the frozen safe base for the independent moving airship sprite.
- Accepted D1S airship remains `observation_window_airship.png`, 15x9 RGBA, SHA256 `58caeabc94744ad04ae1f006c91e09bf9a55d5a211d53b426b12ca9d0dc1c9ce`.
- 0696D2.1 visual direction was approved for four clear time states: morning, noon, evening, night.
- D2 runtime/resolver/package implementation is staged behind an exact-source hard gate.
- The four approved production PNGs must each be exact PNG / 160x80 / RGBA byte streams matching their recorded SHA256 values.
- Repository history, all four live 0696 branches, exact target path history, File Library search, recoverable conversation metadata, and surviving GitHub Actions artifacts `.63` through `.68` have been audited.
- Recursive recovery scanner retest across eight `.63 -> .68` artifacts found **0/4 approved SHA matches** with no scanner warnings.
- The source provenance gap is narrowed to an external/transient D2.1 visual-generation/export source or another authoritative source copy not currently present in repository-accessible storage.
- `.69` must remain unmaterialized until all four exact bytes are recovered.
- Navigation Console remains untouched/deferred.

## Exact 0696D2 source gate

Required SHA256:
- morning: `9a8996ef0068057e774419d9d4597f44753951b3ec1ec519cd6771efaad7b5d0`
- noon: `fa0f00051febb62d107e4a1dc14a079dbfc8183659a73b9ed2ecfe5c4efb3aff`
- evening: `b94d30d18bacecc2c3f09971aec2d5951956490be8c7cad2243b4689c865a638`
- night: `f9d15f66485f514f4be8589ee29d45beabda87e357b1c1d3ffa7965855ed1990`

Do not upscale, redraw, recolor, re-encode, regenerate, or substitute these sources. Do not reuse legacy `observation_window_overlay_2/3/4.png` as D2 environment art.

## Recovery scanner

The recovery scanner accepts loose PNGs, directories, ZIPs, nested ZIPs, and RARs when `7z`/`7zz`/`7za` is available. It identifies source only by the authoritative SHA256 fingerprints and verifies a 160x80 RGBA8 PNG header contract.

Examples:

```bash
python3 tools/alpha28_0696d2_recover_exact_sources.py /path/to/candidates
python3 tools/alpha28_0696d2_recover_exact_sources.py concept.rar sprite.rar
python3 tools/alpha28_0696d2_recover_exact_sources.py /path/to/candidates --install
```

`--install` refuses to write production targets unless all four exact source byte streams have been found.

## Continuation order
1. Recover an authoritative candidate source/archive/local export from the original D2.1 visual session or another exact copy.
2. Run `alpha28_0696d2_recover_exact_sources.py` against it.
3. Only when all four SHA256 values match, use `--install` for exact byte copies.
4. Run `tools/alpha28_0696d2_window_environment_matrix.py --check-source`.
5. Run D2 `--apply` and `--validate`.
6. Compile Cardcha Release.
7. Run `.69` package audit and create the `.69` TEST package.
8. Ron performs in-game visual acceptance.
9. Only after D2.1 acceptance, proceed to later weather/season expansion and D3 Navigation Console work.

## Hard stop
Do **not** fake progress by creating a `.69` package from legacy 128x42 matrix art or regenerated lookalikes. The current blocker is exact source recovery, not runtime implementation.
