# CARDCHA 0696D3-L — LOAD-SAFE SIGNATURE PROBE

Updated: 2026-09-20

Version: 0.3.0-alpha.28.0.4.14.4.5.12.76
Branch: `cardcha-alpha28-0696d2-window-environment-matrix`

## Runtime authority

Ron reported that D3-K .75 could not enter the game after selecting the save.
The SMAPI log proves D3-K installed 3 collision hooks and then loaded Cardcha maps, but the log ends during post-load initialization without reaching a playable world and without a Cardcha exception.

Therefore D3-K is **RUNTIME FAIL: SAVE-LOAD STALL**. Hook installation was not world-entry PASS.

## D3-L correction

- No Harmony postfix is installed on `GameLocation.isCollidingPosition`.
- Compatible overload signatures are logged once at startup.
- Room 1 and Room 2 retain the D3-J/K TMX Buildings collision.
- Forced-position / `Farmer.Position` correction remains forbidden.
- Forest segmented runtime collision is deferred until the exact runtime signature evidence is captured safely.

## Runtime acceptance

1. The save reaches the playable world.
2. The D3-L signature probe lines appear.
3. Then Room 1 / Room 2 physical collision can be retested.
4. Do not call overall Runtime PASS yet; Forest runtime collision still needs a later lightweight-hook decision.

Do not restart D2 and do not redo D3-A/B/C/D/E/F/G/H/I/J/K.
