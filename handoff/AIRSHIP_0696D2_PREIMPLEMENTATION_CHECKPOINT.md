# Airship 0696D2 pre-implementation checkpoint

Branch: `cardcha-alpha28-0696d2-window-environment-matrix`
Base commit before D2.1 implementation: `d83ae7d107023968c20fa119584cbe7c4949b9fb`

## Locked D2.1 scope

- Build target: `.69` clear-weather window environment matrix.
- Approved production background set: **morning / noon / evening / night** only for this pass.
- Every background is native **160x80 RGBA PNG**.
- Use the approved full-quality pixels as production source-of-truth. Do not redraw, rescale, quantize, recolor, or procedurally approximate them for implementation convenience.
- Background art must contain **no baked-in airship**.
- Preserve the `.68` airship as an **independent sprite/runtime layer** above the selected environment background.
- Do **not** restore legacy matrix/column behavior or `overlay_2/3/4` as environment scenery.
- Technical CI success does not equal visual acceptance. Final visual acceptance stays **PENDING-RON-VISUAL** until tested in-game.

## Locked source inventory

| State | Native size | Mode | SHA256 |
| --- | --- | --- | --- |
| morning | 160x80 | RGBA | `9a8996ef0068057e774419d9d4597f44753951b3ec1ec519cd6771efaad7b5d0` |
| noon | 160x80 | RGBA | `fa0f00051febb62d107e4a1dc14a079dbfc8183659a73b9ed2ecfe5c4efb3aff` |
| evening | 160x80 | RGBA | `b94d30d18bacecc2c3f09971aec2d5951956490be8c7cad2243b4689c865a638` |
| night | 160x80 | RGBA | `f9d15f66485f514f4be8589ee29d45beabda87e357b1c1d3ffa7965855ed1990` |

Intended ownership: non-colliding Airship window/environment visual background, behind the existing independent `.68` ship sprite. These files do not own gameplay collision.

## Next implementation gate

1. Materialize the four exact full-quality PNGs into the branch and record/validate hashes.
2. Wire the runtime resolver to select one clear-weather background by time state while preserving the `.68` independent ship layer.
3. Add/update deterministic validation for dimensions, hashes, state coverage, and absence of legacy environment overlay reuse.
4. Update CI/package target to `.69`, run CI, and inspect the produced TEST package.
