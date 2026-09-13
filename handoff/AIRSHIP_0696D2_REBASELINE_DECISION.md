# AIRSHIP 0696D2 Re-baseline Decision

Date: 2026-09-14
Decision: **APPROVED**

Ron explicitly chose D2.1 re-baseline from the recovered approved master artwork.

## Canonical source policy

The four files under:

`recovery/0696d2-concept-masters/01_approved_time_of_day_masters/`

are now the canonical visual source masters for Morning, Noon, Evening and Night.

They remain immutable source bytes. Production 160x80 PNGs are generated deterministically from them with:

- Pillow `11.3.0`
- full-frame resize from `1774x887` to `160x80`
- no crop
- RGBA
- LANCZOS resampling
- PNG optimize disabled
- compression level 9
- no source metadata copied

The exact generated production SHA256 set is recorded by:

`handoff/AIRSHIP_0696D2_REBASELINE_CANONICAL.json`

## Historical SHA policy

The previously recorded 160x80 SHA256 values remain preserved as **historical lost byte identities**. They are not claimed to have been recovered and no new file may impersonate those hashes.

## Frozen invariants

- safe base before D2 remains `.68`
- accepted D1S airship remains unchanged
- Navigation Console remains deferred
- weather and seasonal runtime rollout remains deferred
- `.69` requires deterministic source validation, compile, package audit and Ron visual acceptance
