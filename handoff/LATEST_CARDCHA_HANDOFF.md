# LATEST CARDCHA HANDOFF

Updated: 2026-09-20

Repository: `RVTGMzz/SV-CC-SB`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`  
Current TEST version: `0.3.0-alpha.28.0.4.14.4.5.12.76`  
Current phase: `0696D3-L Load-Safe Signature Probe`  
Current status: **D3-L WORLD ENTRY CONFIRMED / ROOM 1 LIGHTING FAIL / ROOM 2 UPGRADE COLLISION + LAYER FAIL / D3-M NARROW FIX NEXT**

## Read first

1. `handoff/RUNTIME_FEEDBACK_2026-09-29_D3L_ROOM_COLLISION_LIGHTING.md`
2. `handoff/AIRSHIP_0696D3L_LOAD_SAFE_SIGNATURE_PROBE.md`
3. `handoff/RUNTIME_PROOF_2026-09-20_CARDCHA_0696D3K.md` — historical hook-install proof only, not world-entry PASS
4. `handoff/AIRSHIP_0696D3K_COLLISION_HOOK_RUNTIME_FIX.md`
5. `handoff/AIRSHIP_0696D3J_COLLISION_LANES_CHECKPOINT.md`

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


## 2026-09-28 runtime update

Ron tested the canonical D3-L .76 package. Startup proved:
- all three `GameLocation.isCollidingPosition` signatures were discovered;
- D3-L installed **no** runtime collision Harmony postfix;
- Cardcha reached save-load work and completed its main persistence audit / runtime map creation.

The process still hard-exited before playable world with no managed Cardcha exception.

Do **not** open D3-M for the old collision hook theory yet.

The same runtime also loaded Team Up 6.7.44.41, whose capture guard still installed 89 Pelipper capture/catch/pokeball Harmony prefixes. A Team Up 6.7.44.42 isolation build now disables that broad scan (hooks=0) while keeping Cardcha .76 unchanged.

Current Cardcha action: **hold D3-L .76 constant while Team Up .42 is runtime-tested**.


## 2026-09-29 in-game room authority

Ron supplied live screenshots confirming the current setup now reaches the playable world.

This closes the earlier **world-entry blocker**, but D3-L is still **not Runtime PASS** because the screenshots expose three in-world failures:

1. **Room 1 lighting fail**  
   The room is almost completely black and ordinary navigation/props are barely readable.

2. **Room 2 UPGRADE collision fail**  
   The Farmer can stand directly on an UPGRADE pedestal. UPGRADE bodies must be solid in TMX and remain interactable from an adjacent lane.

3. **Room 2 layer/draw-order fail**  
   Environment/front-layer content can visually cover the player/companion incorrectly.

New authority:
`handoff/RUNTIME_FEEDBACK_2026-09-29_D3L_ROOM_COLLISION_LIGHTING.md`

Next patch should be narrow:
`0696D3-M Room Lighting + TMX Collision + Layer Order Runtime Fix`

Do not reintroduce the broad collision Harmony postfix and do not restore forced Farmer.Position correction.
