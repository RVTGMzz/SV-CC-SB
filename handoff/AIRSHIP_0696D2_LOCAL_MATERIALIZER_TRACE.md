# AIRSHIP 0696D2 Local Materializer Trace

Date: 2026-09-14
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
Purpose: trace the last known local/sandbox materialization step for the approved D2.1 Observation Window backgrounds without recreating or substituting source art.

## Recovered conversation clue

Recoverable conversation context for 2026-09-13 contains two important assistant-side statements before the D2 checkpoint:

- around `05:58 UTC`: the four approved images would be handled through a **hash-checked materializer** because the GitHub connector could not directly accept local PNG bytes;
- around `06:00 UTC`: the four main Morning/Noon/Evening/Night scenes were described as standardized to production `160x80`, with background-only art and source hashes checkpointed.

The user then explicitly requested a GitHub checkpoint first, followed by materializing the four full-quality PNGs, wiring the resolver, and building `.69`.

This is evidence that an exact-byte local/sandbox preparation step existed in the original chat workflow even though the production PNG bytes never entered Git history.

## Branch time-window audit

The D2 branch commit collection was queried directly for:

`2026-09-13T05:30:00Z -> 2026-09-13T06:40:00Z`

Result: exactly one commit exists on the current D2 lineage in that interval:

- `1ad582226c3966d31afa688b030df24f74f4be3e`
- timestamp: `2026-09-13T06:29:33Z`
- message: `docs: checkpoint 0696D2 environment matrix before implementation`
- parent: `d83ae7d107023968c20fa119584cbe7c4949b9fb` (D1S `.68`)

Existing provenance audit already proves that `1ad582...` adds only `handoff/AIRSHIP_0696D2_PREIMPLEMENTATION_CHECKPOINT.md`; it does not add PNGs, a materializer script, source archive, local path, or attachment identifier.

Repository code/commit searches for `materializer`, `materialize`, and `D2.1` did not expose a committed helper or hidden implementation commit.

Therefore the hash-checked materializer referenced in conversation was not preserved as a committed D2-branch file between the approved visual step and checkpoint.

## Shared conversation surface

The previously supplied shared ChatGPT URL was tested as a direct public recovery surface. The web fetch did not expose the conversation payload, and searching the share identifier did not produce an indexed copy.

No attachment ID, image-generation output ID, sandbox path, source filename, or download URL could be recovered from that public share route.

## Current sandbox residue check

The active sandbox `/mnt/data` was enumerated after the new external-source sweep.

It contains only the three Google Drive image candidates downloaded during the 2026-09-14 audit:

- `normal_morning_sun.png`
- `cool-night.png`
- `moonlit.png`

All three are independently rejected in `AIRSHIP_0696D2_EXTERNAL_SOURCE_GOOGLE_DRIVE_AUDIT.md` by exact size/mode/SHA inspection. No prior-session Cardcha D2.1 source file is mounted in the current sandbox.

## Conclusion

The strongest remaining explanation is now:

1. the approved D2.1 image bytes existed in a **transient original-chat/local sandbox or image-generation/export context**;
2. a hash-checked local materialization/preparation step was performed or prepared there;
3. only the final SHA256 identities and visual approval state survived into repository metadata;
4. the original byte streams, local materializer inputs, and source attachment identifiers were not committed and are not present in the current sandbox.

This conclusion does **not** authorize regeneration from the visual description. Exact SHA identity remains mandatory.

## Exact gate remains unchanged

Required production SHA256 values:

- morning: `9a8996ef0068057e774419d9d4597f44753951b3ec1ec519cd6771efaad7b5d0`
- noon: `fa0f00051febb62d107e4a1dc14a079dbfc8183659a73b9ed2ecfe5c4efb3aff`
- evening: `b94d30d18bacecc2c3f09971aec2d5951956490be8c7cad2243b4689c865a638`
- night: `f9d15f66485f514f4be8589ee29d45beabda87e357b1c1d3ffa7965855ed1990`

Only recovery of all four exact byte streams can unlock:

`recover scanner -> --install -> --check-source -> --apply -> --validate -> compile -> package audit -> .69 TEST -> Ron visual acceptance`
