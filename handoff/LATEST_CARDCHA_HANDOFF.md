# LATEST CARDCHA HANDOFF

Updated: 2026-09-14

## Start here in a new chat

Primary handoff:
`handoff/HANDOFF_CURRENT.md`

Repository:
`ronvotri/Cardcha-Shardbound`

Branch:
`cardcha-alpha28-0696d2-window-environment-matrix`

Current workstream:
**0696D2 Window Environment Matrix / exact D2.1 source recovery**

Current safe base:
`0.3.0-alpha.28.0.4.14.4.5.12.68`

Next build candidate, **NOT YET MATERIALIZED**:
`0.3.0-alpha.28.0.4.14.4.5.12.69`

## Current source-recovery handoffs

- `handoff/HANDOFF_CURRENT.md`
- `handoff/AIRSHIP_0696D2_SOURCE_RECOVERY_STATUS.md`
- `handoff/AIRSHIP_0696D2_D21_VISUAL_SOURCE_TRACE.md`
- `handoff/AIRSHIP_0696D2_RECOVERY_SCANNER_ARTIFACT_RETEST.json`
- `handoff/AIRSHIP_0696D2_CONCEPT_ACTIONS_EXHAUSTIVE_AUDIT.json`
- `handoff/AIRSHIP_0696D2_PREIMPLEMENTATION_CHECKPOINT.md`

Current recovery tool:
`tools/alpha28_0696d2_recover_exact_sources.py`

## Status

- 0696D1S `.68` remains the frozen safe base for the independent moving airship sprite.
- Accepted D1S airship remains `observation_window_airship.png`, 15x9 RGBA, SHA256 `58caeabc94744ad04ae1f006c91e09bf9a55d5a211d53b426b12ca9d0dc1c9ce`.
- 0696D2.1 visual direction was approved for four clear time states: morning, noon, evening, night.
- D2 runtime/resolver/package implementation is staged behind an exact-source hard gate.
- The four approved production PNGs must each be exact PNG / 160x80 / RGBA byte streams matching their recorded SHA256 values.
- Repository history, all relevant live 0696 branches, exact target path history, File Library search, recoverable conversation metadata, `.63 -> .68` artifacts, and all 14 concept/integration Actions runs have been audited.
- Concept/integration Actions recovery is **EXHAUSTED**: 5 successful artifact sets plus failed runs were checked; 837 PNGs were traversed recursively, including 38 files at 160x80 and 9 unique 160x80 hashes; result **0/4 approved D2 SHA matches**.
- Earlier `.63 -> .68` recursive recovery scans also found **0/4 approved SHA matches**.
- The remaining provenance gap is external/transient: original D2.1 image-generation/export bytes, `concept(1).rar`, `sprite(1).rar`, or another authoritative local copy.
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

The scanner accepts loose PNGs, directories, ZIPs, nested ZIPs, and RARs when `7z`/`7zz`/`7za` is available. It identifies sources only by the authoritative SHA256 fingerprints and verifies a 160x80 RGBA8 PNG header contract.

```bash
python3 tools/alpha28_0696d2_recover_exact_sources.py /path/to/candidates
python3 tools/alpha28_0696d2_recover_exact_sources.py concept.rar sprite.rar
python3 tools/alpha28_0696d2_recover_exact_sources.py /path/to/candidates --install
```

`--install` refuses to write production targets unless all four exact source byte streams have been found.

## Continuation order

1. Read `handoff/HANDOFF_CURRENT.md` first.
2. **Do not re-audit GitHub Actions or existing `.63 -> .68` artifacts. Those routes are exhausted and documented.**
3. Recover an authoritative external/local candidate source, especially original D2.1 export bytes or the source RARs.
4. Run `alpha28_0696d2_recover_exact_sources.py` against it.
5. Only when all four SHA256 values match, use `--install`.
6. Run `tools/alpha28_0696d2_window_environment_matrix.py --check-source`.
7. Run D2 `--apply` and `--validate`.
8. Compile Cardcha Release.
9. Run `.69` package audit and create `.69` TEST.
10. Ron performs in-game visual acceptance.
11. Only after D2.1 PASS proceed to later weather/season expansion and D3 Navigation Console.

## Hard stop

Do **not** fake progress by creating `.69` from legacy 128x42 matrix art or regenerated lookalikes. The current blocker is exact source recovery, not runtime implementation.
