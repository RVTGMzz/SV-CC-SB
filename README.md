# Cardcha! v0.1.17-alpha.11.41 — Circular HUD

This builder replaces the wide top-center Cardcha combat rows with compact circular buff slots.

## New in 11.41
- Cardcha combat HUD stays at **top-center**, but now displays up to **3 circular icons in one horizontal row**.
- No persistent long effect names are drawn across the screen.
- Timed effects show a large integer countdown directly on the circle (`5 → 4 → 3 → 2 → 1`).
- Timed effects also use a small depleting dot-ring around the circle so remaining duration is readable at a glance.
- Hover a circle with the mouse, or touch it, to show a tooltip with:
  - card/effect name;
  - `BUFF`, `READY`, or `ACTIVATED` state;
  - effect description;
  - remaining duration/cooldown when relevant;
  - current stacks for Chain Hunter.
- Visual state language is compact:
  - normal BUFF = gold ring;
  - READY = green ring + check mark;
  - ACTIVATED = purple pulsing ring + exclamation mark.
- Existing fade/slide and priority remain: `ACTIVATED > READY > BUFF`.
- Existing portable-machine UI and ChaCha fetch animation remain unchanged.

## Assets
No official Cardcha art assets were edited. The circular HUD mask is generated at runtime by code.

## Build
Run `BUILD_CARDCHA.bat` with Stardew Valley + SMAPI fully closed. Expected loaded build:

`Cardcha! v0.1.17-alpha.11.41 CIRCULAR HUD ACTIVE`
