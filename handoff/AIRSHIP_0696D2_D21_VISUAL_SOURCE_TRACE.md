# AIRSHIP 0696D2 D2.1 Visual Source Trace

Date: 2026-09-13
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
Purpose: preserve the remaining provenance trail for the four approved D2.1 Observation Window environment images without weakening the exact-byte gate.

## What was visually approved

Conversation provenance recovered for 2026-09-13 shows that D2.1 had four time-of-day backgrounds visually approved before implementation:

- morning: soft pale blue
- noon: clear / brightest blue
- evening: orange-purple sunset
- night: deep blue with moon/stars

Ron approved the direction around 03:32 UTC with “đẹp đó”. The production instruction was to normalize the four approved backgrounds to 160x80, keep the airship as an independent sprite, and connect the time resolver before D2.2 weather work.

By about 06:24 UTC, the explicit instruction was to materialize the four full-quality PNGs into the branch, wire the resolver, then proceed to CI/package `.69`.

Important: the recoverable conversation index does **not** expose the original attachment IDs, image-generation output IDs, filenames, sandbox paths, download links, or original PNG byte streams.

## Exact production fingerprints retained in repository metadata

All four required source files must be PNG / 160x80 / RGBA and must match exactly:

| State | Required SHA256 |
|---|---|
| morning | `9a8996ef0068057e774419d9d4597f44753951b3ec1ec519cd6771efaad7b5d0` |
| noon | `fa0f00051febb62d107e4a1dc14a079dbfc8183659a73b9ed2ecfe5c4efb3aff` |
| evening | `b94d30d18bacecc2c3f09971aec2d5951956490be8c7cad2243b4689c865a638` |
| night | `f9d15f66485f514f4be8589ee29d45beabda87e357b1c1d3ffa7965855ed1990` |

These fingerprints are the only authoritative production identity currently recoverable for the four approved D2.1 images.

## Sep 12 external archive source-pack distinction

The preceding 0696 source documentation records two direct user uploads:

- `concept(1).rar`, expected 6 PNG
- `sprite(1).rar`, expected 22 PNG

The environment at that time could inspect archive headers but could not extract the RAR contents. The 28 inner PNG filenames were therefore never captured in repository metadata.

No evidence currently proves that the four D2.1 approved time backgrounds were byte-identical members of those RARs. Treat the Sep 12 source pack and the Sep 13 D2.1 visual approval trail as related provenance leads, not as interchangeable proof.

## Checkpoint -> staged implementation chronology

D2 checkpoint commit:

- `1ad582226c3966d31afa688b030df24f74f4be3e`
- adds only `handoff/AIRSHIP_0696D2_PREIMPLEMENTATION_CHECKPOINT.md`
- parent is D1S `.68` commit `d83ae7d107023968c20fa119584cbe7c4949b9fb`

First implementation-staging commit:

- `e902c1c915a69dc6c9e3f5a53728399653bf8fa8`
- `build: stage 0696D2 exact-source resolver and .69 package gate`
- timestamp: `2026-09-13T07:45:51Z`
- direct parent: `1ad582226c3966d31afa688b030df24f74f4be3e`

The initial `alpha28_0696d2_window_environment_matrix.py` contains only repository-relative target paths plus the four approved SHA256 values. It contains no `/mnt/data`, `/tmp`, external URL, attachment identifier, source directory, export alias, or other transient-source pointer.

Therefore there is no hidden Git commit between the checkpoint and staged implementation that can recover the approved image bytes.

## Post-checkpoint commit audit

Comparing `1ad582...` through code HEAD `d461e06...` yields exactly five implementation/hardening commits and only four changed files:

- `.github/workflows/cardcha-alpha28-0696d2-window-environment-matrix.yml`
- `tools/alpha28_0696d2_package_audit.py`
- `tools/alpha28_0696d2_window_environment_matrix.py`
- `tools/validate_0696d2_no_legacy_overlay_reuse.py`

The later commits only harden CI/package/legacy-overlay validation. No PNG, archive, preview source, local-path note, source-root variable, or alternate asset alias is introduced.

Relevant commits:

- `e902c1c915a69dc6c9e3f5a53728399653bf8fa8` staged exact source gate/resolver/package flow
- `b5dcafbf01d5d390f46c54501cba6599e593cde9` hardened workflow/package audit
- `c10dbd4ea329469eef9bc95b606757edcfcae3a6` self-tested workflow trigger definition
- `a9d7a07298de70d44ba946689b7003bfa12dd429` hardened legacy overlay guard
- `d461e06af63760e881e33a1d386b3eb8ae8d5f8c` fixed overlay-4 guard spelling

## File Library / retrievable-context result

A focused 2026-09-13 File Library search using Cardcha/Airship/Observation Window plus the approved visual descriptors returned unrelated project files and no D2.1 PNG/image-generation asset.

A targeted conversation-context trace recovered the visual approval and production intent, but not a usable binary/file identifier.

## Current conclusion

The most likely provenance gap is now narrowed to a transient in-chat visual-generation/export step between D2.1 visual approval and the later Git checkpoint. The repository retained the exact SHA256 identities, but the currently accessible repository, Actions artifacts, File Library, and recoverable conversation metadata do not expose the original four PNG byte streams.

This does **not** justify recreating the images from their visual description. Recreating, resizing, recoloring, re-encoding, or substituting an image would produce different bytes and fail the authoritative SHA gate.

## Safe next action

Only one of these closes the gate safely:

1. recover the original D2.1 image-generation/export attachment bytes from the original chat/session or an authoritative local copy; or
2. recover an authoritative archive/file whose four extracted PNGs independently match all four required SHA256 values.

Once exact bytes are recovered:

`check-source -> apply -> validate -> compile -> package audit -> .69 TEST -> Ron visual acceptance`

Until then, `.69` remains intentionally unmaterialized and the D1S ship / Navigation Console invariants remain frozen.
