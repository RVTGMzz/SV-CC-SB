# Alpha28 0673 - Milestone Progression & Boss Route Integration

Build: `0.3.0-alpha.28.0.4.14.4.5.12.42`
Branch: `cardcha-alpha28-0673-milestone-progression-boss-route`
Status: CI/package pending. In-game acceptance for 0669-0672 remains pending.

## Scope
- Sky Dock route console becomes the real 40/60/80-card milestone route.
- Deck helm remains Region I Hunt Run access and is not hijacked by milestone bosses.
- Boss II requires real Boss I clear + 40 owned cards.
- Boss III requires Mirror Archive clear/unlock + Region III state + 60 owned cards.
- Boss IV MiMi requires Tricolor Resonance clear/unlock + Region IV state + 80 owned cards.
- First route-console interaction shows readiness; second interaction within 5 seconds departs.
- Existing Boss II/III/IV victory rewards continue to unlock Region III/IV and their Boss Cards.

## Regression guards
- Save schema remains 19.
- Boss HP, phase mechanics, 0671 authored PNG/TMX assets, and 0672 encounter-depth logic remain unchanged.
- Boss I / 0669 remains frozen pending player acceptance.
- `mimi_walk.png` remains locked.
- Card audit remains 76 active / 80 source.
