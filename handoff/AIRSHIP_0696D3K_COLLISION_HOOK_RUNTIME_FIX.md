# AIRSHIP 0696D3-K — COLLISION HOOK RUNTIME FIX

Updated: 2026-09-19

Repository: `RVTGMzz/SV-CC-SB`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`  
Version: `0.3.0-alpha.28.0.4.14.4.5.12.75`

## Status

**SOURCE / VALIDATOR / RELEASE COMPILE / PACKAGE AUDIT / PRERELEASE: PASS**  
**RUNTIME: RETEST REQUIRED**

## Runtime authority

Ron's SMAPI log from D3-J showed:

`0696D3-J couldn't resolve GameLocation.isCollidingPosition; Forest gate segmented collision was not installed.`

and the startup identity still incorrectly printed:

`Cardcha! 0.3.0-alpha.28.0.4.14.4.5.12.69 0686 HOLLOW CURATOR ARCHIVE RULE ADAPTATION TEST`

Therefore D3-J's second collision layer was not installed even though its TMX collision existed.

## D3-K fix

### Collision hook

D3-J used a hard-coded exact `GameLocation.isCollidingPosition` signature.

D3-K:
- scans all declared methods named `isCollidingPosition`;
- accepts bool-returning overloads whose first argument is `Microsoft.Xna.Framework.Rectangle`;
- patches every compatible overload;
- uses `MethodBase __originalMethod` + `object[] __args`;
- resolves `isFarmer` and `Character` from method metadata;
- keeps normal collision answers only;
- never changes `Farmer.Position`.

The D3-J map-owned collision footprints remain preserved.

### Startup version identity

The stale hard-coded `.69 / 0686` startup banner was removed.

The startup banner now reads `this.ModManifest.Version` and D3-K phase identity.

Expected runtime banner:

`Cardcha! 0.3.0-alpha.28.0.4.14.4.5.12.75 0696D3-K COLLISION HOOK RUNTIME FIX TEST`

Expected collision hook log:

`0696D3-K installed collision hooks on <N> GameLocation.isCollidingPosition overload(s).`

`N` must be greater than zero.

## CI provenance

Run: `35429945303`  
Job: `105862613287`  
Source/package commit: `4431c51f8f999779c39b9a41ce0d33c6020f4a0b`

All gates PASS:
- D3-K collision hook validator;
- no-legacy Window guard;
- render-depth guard;
- tracked-input non-mutation;
- SMAPI build environment;
- Release compile;
- D3-K package audit;
- CI evidence;
- prerelease publication.

## Canonical TEST package

Tag: `cardcha-0696d3k-test-4431c51f`

Release ID: `391985801`

Package:

`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.75_0696D3K_CollisionHookRuntimeFix_TEST.zip`

Asset ID: `574324632`

SHA256:

`be00e20fc67b5f08d784c55d5ebeba86abd3e2449d6d1832e31174ffad79f163`

Release:

`https://github.com/RVTGMzz/SV-CC-SB/releases/tag/cardcha-0696d3k-test-4431c51f`

Direct package:

`https://github.com/RVTGMzz/SV-CC-SB/releases/download/cardcha-0696d3k-test-4431c51f/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.75_0696D3K_CollisionHookRuntimeFix_TEST.zip`

## Runtime retest

Ron should first verify the SMAPI startup lines.

PASS prerequisite:
1. no `couldn't resolve GameLocation.isCollidingPosition` error;
2. collision-hook count is greater than zero;
3. startup banner says `.75 / 0696D3-K`.

Then deliberately test collision against the D3-J Room 1 + Room 2 footprints.

Only Ron's explicit in-game confirmation may promote Runtime PASS.
