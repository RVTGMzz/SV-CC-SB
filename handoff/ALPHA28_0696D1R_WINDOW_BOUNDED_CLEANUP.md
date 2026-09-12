# Alpha 28 / 0696D1R — Observation Window Bounded Cleanup

## Status
- Branch: `cardcha-alpha28-0696d1-observation-window-source-cleanup`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.66`
- Baseline restored before cleanup: `0b13de1ac30dfa019061d3626c478c5460dab89f` (.64)
- Visual acceptance: **PENDING-RON-VISUAL**

## Why D1R exists
0696D1 `.65` is **VISUAL REJECTED by Ron**. The fuzzy matte cleanup clipped real left/right sprite detail, and the runtime frame was incorrectly hollowed even though the approved 0690 contract already provides four independent transparent moving-sky overlays.

## Locked D1R rules
- source-of-truth is restored from verified `.64` before every materialization;
- base stays exactly 160x80 and is never cropped or shifted;
- only exact known pale export-matte colors connected to the canvas edge may lose alpha;
- all non-matte base pixels must remain RGBA-identical;
- four animation overlays remain four separate 160x80 files;
- overlay repair changes only opaque pure-black export-mask pixels to transparent;
- non-black overlay pixels remain RGBA-identical;
- no strip packing, no neighbor spill, no aperture/hollow-frame cutout.

## Materialized evidence
- base matte pixels removed: **2558**
- overlay pure-black pixels removed by frame: **[0, 2324, 2072, 1820]**
- all five Window source files: **160x80**
- runtime contract for this isolated pass: TMX owns the static body; runtime cycles the four repaired transparent overlays.

## Scope lock
D1R does not rebuild the season/time/weather matrix and does not touch Navigation Console. Those remain D2 and D3.

## Next step
Ron visually checks the D1R preview/TEST. Only after Window source/animation geometry is accepted should D2 rebuild the environmental matrix from this clean four-overlay source.
