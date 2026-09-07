# Alpha28 0653 - TMX runtime compatibility fix

Branch: `cardcha-alpha28-0653-tmx-runtime-compat-fix`

Build target: `0.3.0-alpha.28.0.4.14.4.5.12.20`

## Why this patch exists
In-game SMAPI testing exposed `TMXTile.TMXData.decode -> UInt32.Parse` failures when loading all six Region I Hunt Run rooms and the Verdant Guardian arena. The generated CSV layers ended with a comma immediately before `</data>`, producing an empty final token. XML/Tiled parsing tolerated the files, but Stardew/SMAPI's TMXTile runtime parser did not.

The `.vi` suffix visible in SMAPI asset names is locale resolution and was not the cause.

## Fix
- Removed only the final trailing comma from each CSV `<data>` block in the 7 affected TMX maps.
- Repaired CSV blocks: 21.
- Added a strict regression validator that emulates the failing parser contract: every comma-separated token must be a non-empty UInt32 and each layer must contain exactly width x height tiles.
- No map layout, collision, Hunt Run route logic, Boss I AI, rewards, save schema, card balance, MiMi, Airship, or visual animation timing changed.

## Acceptance
CI/static/compile/package acceptance only until a fresh in-game SMAPI test confirms both Hunt Run room loading and `Cardcha_VerdantGuardianArena` loading without ContentLoadException.
