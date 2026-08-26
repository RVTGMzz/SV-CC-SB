# NEXT SESSION — Cardcha v0.3.0-alpha.21 Gacha Controller + Full Flash

## Current candidate
- Version: `0.3.0-alpha.21`
- Build label: `Cardcha! v0.3.0-alpha.21 GACHA CONTROLLER + FULL FLASH`
- Baseline: alpha.20 Control Hints.

## Exact alpha.21 fixes
1. `CardchaPullAnimationMenu`: controller face buttons no longer all call Skip. **B only** skips the ritual; A/X/Y are consumed and do nothing during the ritual.
2. Gacha skip hint now follows the most recent input family: controller shows `B: Bỏ qua / B: Skip`; keyboard/mouse shows `Enter/Space / click`.
3. Enter/Space skip from keyboard; Escape is consumed so it cannot unexpectedly pop the ritual menu through base handling.
4. Stationary full-panel pulse widened from 2380–2700ms to 980–2720ms. Portable widened from 2860–3240ms to 1180–3260ms.
5. Every resonance pulse now overlays the **entire large ritual panel** and repaints the outer gold frame, instead of reading visually like only the small machine/card rectangle is flashing.

## Test first
- Start a pull with controller. Press A, X, Y: ritual must continue. Press B: ritual skips.
- After any controller face-button press, bottom-right hint must show controller text, never mouse text.
- Move mouse/click or use keyboard: hint switches back to keyboard/mouse text.
- During resonance, brightness/color pulses must visibly fill the whole large gold-bordered panel.
- Regression: reveal result screen still opens and persisted pull result does not reroll.

## Artifacts
- `Cardcha_v0.3.0-alpha.21_GachaControllerFlash_WindowsBuilder_FULL.zip`
- `Cardcha_v0.3.0-alpha.21_SOURCE_SNAPSHOT.zip`

Targeted static validation passed in the container; real Windows compile with Stardew/SMAPI references is still required.