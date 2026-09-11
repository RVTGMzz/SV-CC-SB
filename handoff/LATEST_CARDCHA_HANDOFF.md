# Latest Cardcha Handoff

Current development branch: `cardcha-alpha28-0696-airship-concept-faithful-visible-integration`

Current production / TEST baseline: `cardcha-alpha28-0695-region1-prop-integration`

Current production build: `0.3.0-alpha.28.0.4.14.4.5.12.61`

Current production materialized source head: `39e13a370281b29f77d94be497603a3243edda41`

Current production handoff: `handoff/ALPHA28_0695_REGION1_ENVIRONMENT_PROP_PRODUCTION_INTEGRATION.md`

0696 status: **WIP Airship visual recovery.** Ron supplied the missing/approved sprite + full-room concept source and explicitly locked a repository-wide sprite-production workflow before further integration continues.

## Permanent sprite rule

Every future task that creates, edits, imports, rebuilds, scales, tiles, places, or validates sprites/physical visual assets MUST read and follow:

`CARDCHA_SPRITE_PRODUCTION_GUIDE.md`

`AGENTS.md` now makes this requirement repository-wide and mandatory.

Key permanent rules:
- approved source art is production source-of-truth, not loose inspiration;
- no unapproved redraw/rescale for implementation convenience;
- large Stardew props use faithful multi-tile footprints instead of being shrunk merely to reduce tile count;
- preserve approved full-room composition;
- validate actual visible footprint/render ownership, not only file/GID presence;
- research proven Stardew/xTile/native modding patterns before inventing a new rendering convention;
- use an inventory pass, faithful integration pass, then polish pass;
- CI is technical acceptance only; visual acceptance requires Ron's in-game confirmation.

## Existing production verification

Authoritative 0695 successful CI run: `34655852302`

Artifact ID: `10285408808`

Artifact digest: `sha256:065ed6936c5d06479eb2927a7c2b717d359a598447f3b9f6e5c35bc57221bbac`

Verified inner TEST ZIP SHA256: `fac7aaa1c9014aedfd0eba887a1b2bd46531fbb9f676ebd7896b15e321fce726`

0695 Region I in-game visual acceptance remains **PENDING**.

Airship 0693/0696 visual acceptance remains **PENDING**. Do not claim the Airship concept-to-game gap is solved until Ron tests the actual corrected package and approves it.
