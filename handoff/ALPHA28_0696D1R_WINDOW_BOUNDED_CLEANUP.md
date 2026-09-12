# Alpha 28 / 0696D1R — Observation Window Bounded Cleanup FINAL

## Status
- Branch: `cardcha-alpha28-0696d1-observation-window-source-cleanup`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.67`
- Baseline restored every run: `0b13de1ac30dfa019061d3626c478c5460dab89f` (.64)
- Visual acceptance: **PENDING-RON-VISUAL**

## Rejections incorporated
- `.65` rejected: fuzzy matte cleanup clipped real sprite and hollowed the window.
- internal `.66` was not promoted after self-review found detached edge fragments still visible on the checkerboard preview.

## Final D1R contract
- full Window remains exactly 160x80; no crop or shift;
- exact outer matte removal only;
- detached alpha components touching the canvas edge are removed only when they are separate from the main Window component and <= 256 pixels;
- main Window component is never modified by edge-bleed cleanup;
- 4 animation overlays remain 4 independent 160x80 files;
- pure-black overlay export masks become alpha=0 only;
- no hollow aperture and no sprite-strip packing.

## Evidence
- matte pixels removed: **2558**
- detached edge bleed removed: **101 px** in `[{'pixels': 59, 'bbox': [0, 63, 5, 79]}, {'pixels': 38, 'bbox': [0, 33, 3, 51]}, {'pixels': 4, 'bbox': [0, 8, 1, 12]}]`
- overlay black-mask pixels removed: **[0, 2324, 2072, 1820]**
- remaining detached edge components: **0**

D2/D3 remain frozen. Technical PASS does not equal visual PASS.
