# CARDCHA 0696D3-K — RUNTIME STARTUP PROOF

Updated: 2026-09-20

Repository: `RVTGMzz/SV-CC-SB`  
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`  
Version: `0.3.0-alpha.28.0.4.14.4.5.12.75`

## Status

**CI / package: PASS**  
**D3-K startup + collision-hook installation: PASS**  
**Physical Room 1 / Room 2 collision acceptance: RETEST STILL REQUIRED**

## Ron runtime log authority

Ron supplied a fresh SMAPI 4.5.2 / Stardew Valley 1.6.15 runtime log on 2026-09-20.

The D3-K resolver blocker from D3-J is fixed.

Observed:

```text
[23:53:06 INFO  Cardcha!] 0696D3-K installed collision hooks on 3 GameLocation.isCollidingPosition overload(s).
[23:53:06 INFO  Cardcha!] 0696D3-K active: forced-position blocking removed; TMX/native collision, transparent console layering, explicit upgrade stations and travel affordances are authoritative.
[23:53:06 INFO  Cardcha!] Cardcha! 0.3.0-alpha.28.0.4.14.4.5.12.75 0696D3-K COLLISION HOOK RUNTIME FIX TEST
```

The old failure was absent:

```text
couldn't resolve GameLocation.isCollidingPosition
```

No Cardcha ERROR/WARN was present in the supplied log.

The save also loaded both Cardcha maps successfully:

```text
Created Cardcha_AirshipDeck from Cardcha-owned alpha.28 foundation map.
Created Cardcha_SkyDockInterior as Cardcha-owned Arcane Dock layout.
```

## Important limit of this proof

The supplied log ends almost immediately after save/map load. It does not contain a deliberate Room 1 / Room 2 walk-through or another runtime marker proving each physical footprint was tested.

Therefore do NOT promote overall Runtime PASS yet.

Next action is only the physical collision retest against the existing D3-J/D3-K contract:
- Room 1 props + BOARD AIRSHIP center throat;
- Room 2 navigation console, TRAVEL sides/center, four UPGRADE bases, lamp, two Resonance machines;
- confirm runner/rug lanes remain open;
- confirm no ghost-body / forced-position behavior.

Do not restart D2 and do not redo D3-A/B/C/D/E/F/G/H/I/J.
