# LATEST CARDCHA HANDOFF

Updated: 2026-09-14

## Start here

Primary source of truth:
`handoff/HANDOFF_CURRENT.md`

Repository:
`ronvotri/Cardcha-Shardbound`

Branch:
`cardcha-alpha28-0696d2-window-environment-matrix`

Current workstream:
**0696D2 Window Environment Matrix / exact D2.1 source recovery**

Safe base:
`0.3.0-alpha.28.0.4.14.4.5.12.68`

Next candidate, **NOT MATERIALIZED**:
`0.3.0-alpha.28.0.4.14.4.5.12.69`

## Read these evidence files

- `handoff/HANDOFF_CURRENT.md`
- `handoff/AIRSHIP_0696D2_SOURCE_RECOVERY_STATUS.md`
- `handoff/AIRSHIP_0696D2_D21_VISUAL_SOURCE_TRACE.md`
- `handoff/AIRSHIP_0696D2_RECOVERY_SCANNER_ARTIFACT_RETEST.json`
- `handoff/AIRSHIP_0696D2_CONCEPT_ACTIONS_EXHAUSTIVE_AUDIT.json`
- `handoff/AIRSHIP_0696D2_EXTERNAL_SOURCE_GOOGLE_DRIVE_AUDIT.md`
- `handoff/AIRSHIP_0696D2_EXTERNAL_SOURCE_CANVA_AUDIT.md`
- `handoff/AIRSHIP_0696D2_LOCAL_MATERIALIZER_TRACE.md`
- `handoff/AIRSHIP_0696D2_PREIMPLEMENTATION_CHECKPOINT.md`

## Exact gate

Required SHA256:

- morning: `9a8996ef0068057e774419d9d4597f44753951b3ec1ec519cd6771efaad7b5d0`
- noon: `fa0f00051febb62d107e4a1dc14a079dbfc8183659a73b9ed2ecfe5c4efb3aff`
- evening: `b94d30d18bacecc2c3f09971aec2d5951956490be8c7cad2243b4689c865a638`
- night: `f9d15f66485f514f4be8589ee29d45beabda87e357b1c1d3ffa7965855ed1990`

All four must be exact PNG / 160x80 / RGBA byte streams.

Do not resize, redraw, recolor, re-encode, regenerate, upscale, or substitute them. Do not reuse legacy observation overlays as D2 source art.

## Continuation

Do not repeat recovery routes already marked exhausted in `HANDOFF_CURRENT.md` unless new evidence appears.

The next valid action is to obtain an authoritative external/local candidate source and run:

```bash
python3 tools/alpha28_0696d2_recover_exact_sources.py /path/to/candidates
```

Only after all four exact SHA256 values are recovered:

`--install -> --check-source -> --apply -> --validate -> compile -> package audit -> .69 TEST -> Ron visual acceptance`

Navigation Console remains deferred.
