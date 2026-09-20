# LATEST CARDCHA HANDOFF

Updated: 2026-09-20

Repository: `RVTGMzz/SV-CC-SB`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`  
Current TEST version: `0.3.0-alpha.28.0.4.14.4.5.12.76`  
Current phase: `0696D3-L Load-Safe Signature Probe`  
Current status: **D3-K RUNTIME FAIL (SAVE-LOAD STALL) / D3-L SOURCE READY / CI RUNNING**

## Read first

1. `handoff/AIRSHIP_0696D3L_LOAD_SAFE_SIGNATURE_PROBE.md`
2. `handoff/RUNTIME_PROOF_2026-09-20_CARDCHA_0696D3K.md` — historical hook-install proof only, not world-entry PASS
3. `handoff/AIRSHIP_0696D3K_COLLISION_HOOK_RUNTIME_FIX.md`
4. `handoff/AIRSHIP_0696D3J_COLLISION_LANES_CHECKPOINT.md`

## Corrected runtime authority

Ron explicitly reported that D3-K .75 never entered the playable game after selecting the save.

The log shows:
- D3-K installed 3 compatible `GameLocation.isCollidingPosition` hooks;
- the save and Cardcha maps started loading;
- the log ended during post-load initialization;
- no playable-world completion followed;
- no Cardcha exception was emitted before the stall.

Therefore D3-K is **Runtime FAIL: save-load stall**.

## D3-L

- removes the generic Harmony postfix from every `GameLocation.isCollidingPosition` overload;
- probes compatible overload signatures once at startup only;
- preserves Room 1 / Room 2 TMX Buildings collision;
- never writes `Farmer.Position`;
- intentionally defers the Forest gate's extra runtime collision layer until the safe runtime signature is known.

First D3-L runtime acceptance: **the save must reach the playable world**.

Do not restart D2 and do not redo D3-A/B/C/D/E/F/G/H/I/J/K.
