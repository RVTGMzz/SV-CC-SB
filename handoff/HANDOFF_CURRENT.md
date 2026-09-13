# CARDCHA CURRENT HANDOFF

Prepared: 2026-09-14 (Asia/Ho_Chi_Minh)
Repository: `ronvotri/Cardcha-Shardbound`
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`

## Current workstream

**0696D2 Observation Window / production decision after master recovery**

Safe runtime/build base:
`0.3.0-alpha.28.0.4.14.4.5.12.68`

Next candidate, intentionally **NOT materialized**:
`0.3.0-alpha.28.0.4.14.4.5.12.69`

Accepted independent D1S airship remains frozen:
- `src/Cardcha/assets/airship_props/set01_redux/window_runtime/observation_window_airship.png`
- 15x9 RGBA
- SHA256 `58caeabc94744ad04ae1f006c91e09bf9a55d5a211d53b426b12ca9d0dc1c9ce`

Navigation Console remains untouched/deferred.

## Master recovery is complete

The recovered Observation Window concept library has been merged into the active branch through PR #6.

Merge commit:
`bccbf1ecc6ec69570c9d136cd190510c9e8ed164`

Archive root:
`recovery/0696d2-concept-masters/`

Approved time-of-day masters are preserved under:
`recovery/0696d2-concept-masters/01_approved_time_of_day_masters/`

Full source mapping, dimensions, modes and SHA256 values:
- `SOURCE_NAME_MAP.md`
- `recovery/0696d2-concept-masters/MANIFEST_SHA256.csv`
- `handoff/AIRSHIP_0696D2_MASTER_RECOVERY_MERGED.md`

Do not restart source hunting. Source preservation is complete.

## Historical D2.1 production gate remains separate

The old exact 160x80 production byte identities are still unrecovered:

- morning: `9a8996ef0068057e774419d9d4597f44753951b3ec1ec519cd6771efaad7b5d0`
- noon: `fa0f00051febb62d107e4a1dc14a079dbfc8183659a73b9ed2ecfe5c4efb3aff`
- evening: `b94d30d18bacecc2c3f09971aec2d5951956490be8c7cad2243b4689c865a638`
- night: `f9d15f66485f514f4be8589ee29d45beabda87e357b1c1d3ffa7965855ed1990`

Do not confuse these with the recovered 1774x887 master SHA values.

## Staged implementation

Already prepared behind the production source gate:
- `tools/alpha28_0696d2_window_environment_matrix.py`
- `.github/workflows/cardcha-alpha28-0696d2-window-environment-matrix.yml`
- `tools/alpha28_0696d2_package_audit.py`
- `tools/validate_0696d2_no_legacy_overlay_reuse.py`
- `tools/alpha28_0696d2_recover_exact_sources.py`

## Current decision point

Ron must explicitly choose one path before production work continues:

1. **Historical exact recovery**: keep the old 160x80 SHA gate and wait for those exact old bytes; or
2. **Intentional D2.1 re-baseline**: derive a new canonical 160x80 set from the four preserved approved masters, record new SHA256 values, update the source gate deliberately, then continue `.69`.

Until Ron chooses:
- do not replace the historical source gate;
- do not write new production D2.1 sprites;
- do not build `.69`.

## Hard stop

No more recovery loops. The artwork source masters are safe in Git now. The blocker is a product/production policy choice, not missing concept art.
