# LATEST CARDCHA HANDOFF

Updated: 2026-09-20

Repository: `RVTGMzz/SV-CC-SB`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`  
Current TEST version: `0.3.0-alpha.28.0.4.14.4.5.12.75`  
Current phase: `0696D3-K Collision Hook Runtime Fix`  
Current status: **CI PASS / PACKAGE READY / STARTUP+HOOK RUNTIME PASS / PHYSICAL COLLISION RETEST REQUIRED**

## Read first

1. `handoff/RUNTIME_PROOF_2026-09-20_CARDCHA_0696D3K.md`
2. `handoff/NEXT_CHAT_PROMPT_2026-09-19_CARDCHA_0696D3K.md`
3. `handoff/REPOSITORY_RELOCATION_2026-09-19.md`
4. `handoff/AIRSHIP_0696D3K_COLLISION_HOOK_RUNTIME_FIX.md`
5. `handoff/SESSION_HANDOFF_2026-09-19_CARDCHA_0696D3K.md`
6. `handoff/AIRSHIP_0696D3J_COLLISION_LANES_CHECKPOINT.md`
7. `handoff/REPOSITORY_RELOCATION_CI_RECHECK_2026-09-19.md`

## Newest runtime authority

Ron's 2026-09-20 SMAPI 4.5.2 / Stardew Valley 1.6.15 log confirms D3-K fixed the D3-J resolver failure.

Observed:

```text
0696D3-K installed collision hooks on 3 GameLocation.isCollidingPosition overload(s).
Cardcha! 0.3.0-alpha.28.0.4.14.4.5.12.75 0696D3-K COLLISION HOOK RUNTIME FIX TEST
```

The old failure is absent:

```text
couldn't resolve GameLocation.isCollidingPosition
```

No Cardcha ERROR/WARN appears in the supplied log.

The save also successfully created:
- `Cardcha_AirshipDeck`
- `Cardcha_SkyDockInterior`

This proves startup identity + Harmony hook installation at runtime.

It does **not** yet prove every authored physical collision footprint because the supplied log ends shortly after save/map load and contains no deliberate Room 1 / Room 2 collision walk-through.

## D3-K

- dynamically scans compatible `GameLocation.isCollidingPosition` overloads;
- runtime confirmed **3 compatible overloads patched**;
- patches bool-returning overloads whose first parameter is XNA Rectangle;
- generic postfix resolves `isFarmer` and `Character` from actual method metadata;
- preserves D3-J TMX/native collision footprints;
- never rewinds or sets Farmer.Position;
- startup banner uses `ModManifest.Version`;
- current identity is `.75 / 0696D3-K`.

## CI / package

Run: `35429945303`  
Job: `105862613287`  
Source/package commit: `4431c51f8f999779c39b9a41ce0d33c6020f4a0b`

Tag: `cardcha-0696d3k-test-4431c51f`

Package:

`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.75_0696D3K_CollisionHookRuntimeFix_TEST.zip`

SHA256:

`be00e20fc67b5f08d784c55d5ebeba86abd3e2449d6d1832e31174ffad79f163`

Release:

`https://github.com/RVTGMzz/SV-CC-SB/releases/tag/cardcha-0696d3k-test-4431c51f`

Direct package:

`https://github.com/RVTGMzz/SV-CC-SB/releases/download/cardcha-0696d3k-test-4431c51f/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.75_0696D3K_CollisionHookRuntimeFix_TEST.zip`

## Remaining runtime acceptance

Do not open D3-L merely for the old resolver issue. That issue is runtime-confirmed fixed.

Use the same canonical D3-K .75 package and deliberately walk into the Room 1 + Room 2 props.

Only explicit in-game confirmation of the physical collision contract may promote overall Runtime PASS.

Do not restart D2 and do not redo D3-A/B/C/D/E/F/G/H/I/J.
