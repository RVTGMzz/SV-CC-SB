# LATEST CARDCHA HANDOFF

Updated: 2026-09-14

## Start here

Read these first, in order:

1. `README_FOR_NEXT_SESSION.md`
2. `SOURCE_NAME_MAP.md`
3. `handoff/AIRSHIP_0696D2_MASTER_RECOVERY_MERGED.md`
4. `handoff/HANDOFF_CURRENT.md`

Repository: `ronvotri/Cardcha-Shardbound`
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`

Current workstream: **0696D2 Observation Window**.

Safe base: `.68`
Next candidate: `.69` is still not materialized.

## Recovery status

The recovered Observation Window concept library has been merged into the active branch through PR #6.

Merge commit:
`bccbf1ecc6ec69570c9d136cd190510c9e8ed164`

Archive root:
`recovery/0696d2-concept-masters/`

The approved Morning / Noon / Evening / Night 1774x887 RGBA masters are preserved in-repo. Source mapping and hashes are recorded in `SOURCE_NAME_MAP.md` and the recovery manifest.

Do not restart image recovery.

## Current decision point

The historical exact 160x80 production SHA set is still unrecovered.

Ron must choose explicitly:

1. continue historical exact-byte recovery; or
2. intentionally re-baseline D2.1 from the preserved approved masters and create a new canonical 160x80 SHA set.

Until Ron chooses, do not replace the production gate and do not build `.69`.

Navigation Console remains deferred.
