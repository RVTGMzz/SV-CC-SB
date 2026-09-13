# AIRSHIP 0696D2 Master Recovery Merged

Date: 2026-09-14
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`

## Status

Recovered Observation Window source library has been merged into the active 0696D2 workstream via PR #6.

Merge commit:
`bccbf1ecc6ec69570c9d136cd190510c9e8ed164`

Recovered archive root:
`recovery/0696d2-concept-masters/`

## Approved time-of-day masters now preserved in-repo

- Morning: `01_approved_time_of_day_masters/observation_window_master_morning.png`
  - 1774x887 RGBA
  - SHA256 `e42ce1e1199f30ac8d30ab592ecbec01b9176388ed2a6572b68005b812e2bc85`
- Noon: `01_approved_time_of_day_masters/observation_window_master_noon.png`
  - 1774x887 RGBA
  - SHA256 `c6f99df25a7dee04d0aeab8f1d9ac928a7e6dcb1af43db092187e1ad7831ae9e`
- Evening: `01_approved_time_of_day_masters/observation_window_master_evening.png`
  - 1774x887 RGBA
  - SHA256 `650adec1a8d08631d02b31a59c45bc3dda96a49706a68feea3508996ee2a4fbe`
- Night: `01_approved_time_of_day_masters/observation_window_master_night.png`
  - 1774x887 RGBA
  - SHA256 `7788da7428b7a808794c2ba14716c1ed0c25b59a3f2990f1d6c8437a92b55ee8`

Manifest:
`recovery/0696d2-concept-masters/MANIFEST_SHA256.csv`

## Additional preserved sets

The merged recovery library also contains:

- weather concepts;
- seasonal concepts;
- additional variants;
- earlier concepts with airship baked into the background.

These are source/archive assets only. They are not automatically approved production runtime sprites.

## Production gate remains separate

The historical 160x80 D2.1 SHA set is still unrecovered and has not been silently replaced.

`.69` remains unmaterialized.

## Decision point

Source preservation is complete. Do not perform more source hunting unless new provenance appears.

Next work requires Ron to choose explicitly between:

1. continue exact historical 160x80 byte recovery, or
2. re-baseline D2.1 from the four preserved approved masters and record a new canonical 160x80 production SHA set.

Until that choice is made, do not change the production gate or build `.69`.
