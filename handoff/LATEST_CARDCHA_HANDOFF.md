# LATEST CARDCHA HANDOFF

Updated: 2026-09-20

Repository: `RVTGMzz/SV-CC-SB`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`  
Current TEST version: `0.3.0-alpha.28.0.4.14.4.5.12.76`  
Current phase: `0696D3-L Load-Safe Signature Probe`  
Current status: **D3-K RUNTIME FAIL (SAVE-LOAD STALL) / D3-L CI PASS / PACKAGE READY / RUNTIME RETEST REQUIRED**

## Read first

1. `handoff/AIRSHIP_0696D3L_LOAD_SAFE_SIGNATURE_PROBE.md`
2. `handoff/RUNTIME_PROOF_2026-09-20_CARDCHA_0696D3K.md` — historical hook-install proof only, not world-entry PASS
3. `handoff/AIRSHIP_0696D3K_COLLISION_HOOK_RUNTIME_FIX.md`
4. `handoff/AIRSHIP_0696D3J_COLLISION_LANES_CHECKPOINT.md`

## Corrected runtime authority

Ron explicitly reported that D3-K .75 never entered the playable game after selecting the save.

The supplied SMAPI log shows:
- D3-K installed 3 compatible `GameLocation.isCollidingPosition` hooks;
- the save and Cardcha maps started loading;
- the log ended during post-load initialization;
- no playable-world completion followed;
- no Cardcha exception was emitted before the stall.

Therefore D3-K is **Runtime FAIL: save-load stall**.

## D3-L correction

- removes the generic Harmony postfix from every `GameLocation.isCollidingPosition` overload;
- probes compatible overload signatures once at startup only;
- preserves Room 1 / Room 2 TMX Buildings collision;
- never writes `Farmer.Position`;
- intentionally defers the Forest gate's extra runtime collision layer until the safe runtime signature is known.

## D3-L CI / package

CI run: `35524984219`  
Job: `106115466452`  
Canonical source/package commit: `bcd10e92c79f2eaaef8ea3f99d9ce69455031df0`  
Conclusion: **SUCCESS**

Tag: `cardcha-0696d3l-test-bcd10e92`

Package:

`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.76_0696D3L_LoadSafeSignatureProbe_TEST.zip`

SHA256:

`751169899b02c9eab9a25ced539ad3f3b2481ba007e621eaa0b94a8053469f44`

Direct package:

`https://github.com/RVTGMzz/SV-CC-SB/releases/download/cardcha-0696d3l-test-bcd10e92/Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.76_0696D3L_LoadSafeSignatureProbe_TEST.zip`

## Runtime acceptance order

First and only initial question for D3-L: **does the same save reach the playable world?**

Expected startup evidence:

```text
0696D3-L collision signature probe [1]: ...
0696D3-L load-safe mode: observed <N> compatible GameLocation.isCollidingPosition overload(s); runtime collision Harmony postfix is intentionally disabled.
Cardcha! 0.3.0-alpha.28.0.4.14.4.5.12.76 0696D3-L LOAD-SAFE SIGNATURE PROBE TEST
```

If world entry succeeds, then use the captured signatures to decide whether a single lightweight Forest collision hook is needed. Only after world entry should Room 1 / Room 2 physical TMX collision be retested.

Do not call overall Runtime PASS yet.

Do not restart D2 and do not redo D3-A/B/C/D/E/F/G/H/I/J/K.
