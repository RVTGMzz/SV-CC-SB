# Alpha 28 / 0696D.1 — Observation Window Source Cleanup

## Status
- Branch: `cardcha-alpha28-0696d1-observation-window-source-cleanup`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.65`
- Scope: Observation Window source only
- Technical validation: **PASS when CI validates this materialized output**
- Visual acceptance: **PENDING-RON-VISUAL**

## Why this pass exists
Ron rejected the remaining pale/yellow rectangle around the Observation Window. Inspection confirmed the rectangle is not merely a debug overlay: `observation_window_base.png` itself contains a large opaque export matte connected to the canvas edge.

## D1 rule
This pass is deliberately narrow. It does **not** rebuild the 80 environment states and does **not** touch Navigation Console cleanup. Those are separate passes D2 and D3.

## What D1 changes
- preserves the exact 160x80 footprint;
- preserves every RGB pixel of the approved Observation Window artwork;
- changes alpha only for border-connected pixels near the known matte palette;
- rebuilds `window_runtime/observation_window_frame.png` from the cleaned source;
- preserves the current aperture mask and 80-state environment matrix for D2;
- leaves Navigation Console source untouched for D3.

## Cleanup evidence
- opaque matte pixels made transparent: **2625**
- transparent pixels before: **163**
- transparent pixels after: **2788**
- RGB SHA before: `26acf10d234fc6bdb26334df2efaf84ee663ef9a4798b7cb673dd2b5c9ff51e5`
- RGB SHA after: `26acf10d234fc6bdb26334df2efaf84ee663ef9a4798b7cb673dd2b5c9ff51e5`
- RGB identity preserved: **TRUE**

## Non-goals
- no console cleanup;
- no environment-matrix repaint/rebuild;
- no layer/collision redesign;
- no room-shell change;
- no rescale or redraw.

## Next pass
After Ron confirms the source/frame matte is gone, continue with **0696D.2 — Window Environment Matrix Rebuild**, using this clean source as the only allowed frame/base input.
