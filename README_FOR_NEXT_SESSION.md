# README FOR NEXT SESSION — Cardcha 0696D2

Updated: 2026-09-14
Repository: `ronvotri/Cardcha-Shardbound`
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`

## Start here

Read first:
- `SOURCE_NAME_MAP.md`
- `handoff/AIRSHIP_0696D2_MASTER_RECOVERY_MERGED.md`
- `handoff/HANDOFF_CURRENT.md`

Safe base remains `.68`.
`.69` is still blocked.

## Recovery status

The Observation Window concept/master library has been recovered and merged into this branch through PR #6.

Merge commit:
`bccbf1ecc6ec69570c9d136cd190510c9e8ed164`

Archive root:
`recovery/0696d2-concept-masters/`

The four approved Morning / Noon / Evening / Night masters are now preserved in-repo under:
`recovery/0696d2-concept-masters/01_approved_time_of_day_masters/`

Full dimensions, source-name mapping and SHA256 values are recorded in:
- `SOURCE_NAME_MAP.md`
- `recovery/0696d2-concept-masters/MANIFEST_SHA256.csv`

Do not restart source hunting.

## Decision point

The old exact 160x80 production SHA set is still unrecovered and remains distinct from the recovered master hashes.

Ron must explicitly choose one path before production work continues:

1. keep historical exact-byte recovery active; or
2. intentionally re-baseline D2.1 from the preserved approved masters and record a new canonical 160x80 SHA set.

Until that choice is made:
- do not replace the historical gate;
- do not modify production runtime source paths;
- do not build `.69`.
