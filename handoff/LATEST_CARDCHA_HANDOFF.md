# Latest Cardcha Handoff

Current source-of-truth branch: `cardcha-alpha28-0692-airship-rgba-gate-restore`

Current build: `0.3.0-alpha.28.0.4.14.4.5.12.59`

Current handoff: `handoff/ALPHA28_0692_AIRSHIP_RGBA_GATE_RESTORE.md`

Parent source-of-truth: `cardcha-alpha28-0691-airship-prop-set02-harbor-furnishings` @ `91b9166e915f0b50a3dd23b0cb5e8fb888191974`

Materialized source head: `4f443db19f05183a101c9ac4af9b8905b19b9f5f`

Authoritative successful CI run: `34628000033`
Artifact ID: `10275895244`
Artifact digest: `sha256:0c267f59d307a263c684975f97a23be4f85f1a2d15150b71fba9c04606e72627`
Verified inner TEST ZIP SHA256: `0952bf1747e90908e31ebb8fda6bc5a28403d20e5b98586a9f0f00ca8cada695`

Status: **0692 CI / compile / package PASS.** The Airship physical prop path is normalized to RGBA and the outdoor boarding gate farmer-depth path is restored. In-game visual acceptance remains **PENDING** until Ron tests build `.59`.

Approved Airship visual direction remains: `handoff/AIRSHIP_VISUAL_DIRECTION_APPROVED.md`.
Do not use the rejected 0689 small-sprite prototype branch as a base.

Recommended next design task if Ron says continue before another Airship visual test:
`0693 — Region I / Map 1 Environment Prop Visual Rebuild CONCEPT PASS`.

Reason: Ron explicitly wanted the two Airship rooms handled first, then a return to Map 1 where the current `region1_environment_decor.png` 8-cell placeholder atlas is visually crude and also still listed as rendering-depth debt. Concept approval should happen before replacing those physical props in production.

New-session startup order:
1. Read `AGENTS.md`.
2. Read this file.
3. Read `handoff/ALPHA28_0692_AIRSHIP_RGBA_GATE_RESTORE.md`.
4. Read `handoff/AIRSHIP_VISUAL_DIRECTION_APPROVED.md`.
5. Read `render_depth_audit.json`.
6. Preserve 0692 Airship visibility fixes while moving the next visual-design work to Region I / Map 1.
