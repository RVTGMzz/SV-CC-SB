# Latest Cardcha Handoff

Current branch: `cardcha-alpha28-0676b-region-layering-extraction-hotfix`
Current build: `0.3.0-alpha.28.0.4.14.4.5.12.45.2`
Continue from: `handoff/ALPHA28_0676B_REGION_LAYERING_EXTRACTION_HOTFIX.md`

0676B exists because 0676/0676A failed in-game visual acceptance and the follow-up audit proved the recurring overlap bug was repository-wide rendering ownership debt, not an isolated coordinate error.

Permanent repository contract files now apply to every future Cardcha visual change:
- `AGENTS.md`
- `CARDCHA_RENDERING_DEPTH_CONTRACT.md`
- `render_depth_audit.json`
- `tools/validate_render_depth_contract.py`

Core rule: physical Cardcha world content must not be painted from `Display.RenderedWorld`; ground belongs to maps, static props to native map/object/furniture ownership, and combat bodies to actor draw slots. `RenderedWorld` is VFX-only.

0676B currently suppresses confirmed unsafe static post-world overlays for Region I and Airship interiors and migrates Region III/IV actor rendering. Remaining audited combat-body debt (Boss I body, summons, Totems, Boss II/III/IV bodies) must be migrated before new feature expansion.

0676B CI/build success is not visual acceptance. Require in-game screenshot review. Do not resume from stale `main`, 0676, 0676A, or earlier branches.
