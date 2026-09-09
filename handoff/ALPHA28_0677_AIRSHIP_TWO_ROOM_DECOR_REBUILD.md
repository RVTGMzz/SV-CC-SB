# Cardcha alpha28 — 0677 Airship Two-Room Decor Rebuild

## Source of truth
- Branch: `cardcha-alpha28-0677-airship-two-room-decor-rebuild`
- Build: `0.3.0-alpha.28.0.4.14.4.5.12.45.3`
- Base: 0676B world-depth safety contract.

## User acceptance problem
The two Airship rooms looked too empty, generic and test-like to be worth testing. 0677 is a room-composition rebuild, not a small prop sprinkle.

## Bridge
- Native Stardew furniture only for physical decor.
- Clear central walking spine.
- Navigation/reference wall, engine/hull workshop, resonance/reactor side, rugs, lamps, plants, windows and storage.
- Four upgrade sockets remain gameplay-authoritative.

## Dock / waiting hall
- Service/Lost & Found zone, route desk, boarding/luggage side and waiting nook.
- Lost & Found is a real Cardcha-owned Chest at the existing interaction tile.
- Center arrival/exit corridor and boarding bay remain open.

## Depth contract
- Old full-room BackDecor image layer disabled.
- No solid room prop restored through RenderedWorld.
- Physical room detail is Furniture/Object/TMX owned.
- Magical cues remain VFX-only.

## Frozen
No card balance, boss balance, progression, fare, save schema, MiMi art, ChaCha mechanics, or Region gameplay changes.

## Acceptance
1. `cardcha_test_airship`: Bridge must read as a furnished flying workshop/bridge, not an empty rectangle.
2. Walk center spine and all four upgrade sockets; native occlusion must remain correct.
3. Return to Dock: service, route, waiting and boarding zones must be visually distinct.
4. Lost & Found chest must be visible at its actual interaction position.
