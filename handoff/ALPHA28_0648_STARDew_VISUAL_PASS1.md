# Alpha28 0648 - Stardew Visual Pass 1

## Canonical branch
`cardcha-alpha28-0648-stardew-visual-pass1`

## Build
- Version: `0.3.0-alpha.28.0.4.14.4.5.12.6`
- TEST package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.6_StardewVisualPass1_TEST.zip`
- TEST SHA-256: `5e709b95af46a4ac4b0ad237a43aca10c2396e22fe8e0ff601b05fcaca81e858`
- DLL size: `762880` bytes

## CI
- Workflow: `.github/workflows/cardcha-alpha28-0648-stardew-visual-pass1.yml`
- Run: `33976957299` SUCCESS
- Job: `101335236454` SUCCESS
- Artifact ID: `9972600991`
- Outer artifact digest: `sha256:43c0c0a94487b581b3e456bc59971b772bb80db962b7a2fa0849c3fbc5a6d775`
- Materialization commit: `2315fe1a135024416bf4ce9b8c28c76660681e3a`

## 0648 visual direction
`0648` is a visual-only polish pass on top of the physical/collision rebuild from 0647E. Gameplay route, upgrade logic/costs, card canon, MiMi logic and gate interaction rules are not redesigned here.

### Forest Arcane Gate
- Kept deterministic placement from 0647D/0647E.
- Kept `ForestGateUseDistance = 160f`.
- Kept `CollisionEdits=NONE` compatibility contract.
- Kept farmer-aware gate depth from 0647E.
- Reduced neon intensity.
- Shifted portal/gate palette toward muted violet, desaturated teal, warm brass and warmer stone.
- Reduced sparkle count and pylon height slightly for a less sci-fi silhouette.

### Sky Dock
Locked visual identity: **transit station / boarding dock**, never a domestic room.

Backdrop additions:
- warm riveted ceiling beam;
- large route/status board on the left;
- physical boarding gantry around the existing sky aperture on the right;
- central boarding lane with brass edging and repeated directional diamonds;
- utility crates, rope coil, tool rack and service cabinet painted into the map;
- central dock beacon;
- low service/rail details to reduce dead wall mass without cluttering the walking lane.

Runtime accents remain small and local:
- route-board status chips;
- boarding gantry lamps;
- utility corner lamps;
- warm doorway threshold.

No pickup Furniture objects are used.

### Airship Deck / Bridge
Locked visual identity: **cozy Stardew control room / airship bridge**.

Backdrop additions:
- stronger central helm console mass beneath the animated astrolabe;
- distinct left/right system consoles;
- four service pads aligned exactly with the four upgrade machines;
- dedicated ChaCha resonance equipment alcove;
- warmer central transit runner with brass edging;
- small wall placards, rivets and warm lamps;
- panoramic canopy preserved.

Runtime accents:
- warm window stars/reflections;
- small side-console indicators;
- muted animated helm;
- four level-aware upgrade machines at 112x112 display size;
- low-intensity machine level accents;
- muted ChaCha resonance accents.

## Upgrade machine atlas cleanup
`assets/airship_upgrade_visuals.png` was cleaned so each 96x96 cell no longer carries an edge-connected opaque purple rectangle. The machine silhouette and internal outlines remain, while neon cyan/purple accents were muted toward Stardew-compatible teal, blue and mauve.

## Materialized visual asset hashes
- `assets/airship_deck_stardew.png`
  - SHA-256: `b0fbe6046a2555c8c2a1ccf69e40bcd91592a38dd334162ed3c454b348e889f5`
  - size: 384x224
- `assets/sky_dock_stardew.png`
  - SHA-256: `9a261a09f633cbe37a5d2bf333b0d806fcff5cf777ce98e7da86258c63ad03d1`
  - size: 480x288
- `assets/airship_upgrade_visuals.png`
  - SHA-256: `f86b7b69f6a8305189eb9049a78fba115f6c508917dd914695b851426723a16f`
  - size: 384x384
- `assets/airship_visual_0648_audit.json`
  - SHA-256: `2c8bc7358d5089e6d39b0fd2796f64ca06572b1c10556e82d7ead074c151ada1`

## Physical/collision contracts preserved
- Airship TMX: 24x14, exactly 336 uint CSV tokens per layer.
- Sky Dock TMX: 30x18, exactly 540 uint CSV tokens per layer.
- Four upgrade stations remain collision-backed at `(5,9)`, `(18,9)`, `(8,10)`, `(15,10)`.
- Helm remains collision-backed at `(12,4)`.
- ChaCha alcove remains collision-backed at `(19,5)`.
- Central Airship transit lane remains walkable.
- Sky Dock route console remains physical while boarding/exit lanes remain walkable.
- No runtime pickup furniture is reintroduced.

## Locked regressions preserved
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit PASS.
- locked `airship_visual.png` SHA-256 unchanged: `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- Airship route remains `Forest -> Cardcha_SkyDockInterior -> Cardcha_AirshipDeck`.
- Airship upgrade menu/costs/levels unchanged.
- Deferred Airship gameplay bonuses remain disabled.
- MiMi portrait remains single-source `assets/mimi_portraits.png`; old runtime64/NPC portrait PNGs remain absent.
- MiMi home/TV/late movement anchors remain unchanged.

## Acceptance test
1. Install `.5.12.6` after deleting the old Cardcha folder and fully restart SMAPI.
2. `cardcha_version` must report `.5.12.6`.
3. Run `cardcha_test_gate`:
   - gate stays fixed;
   - palette is softer/warmer;
   - farmer depth remains correct.
4. Enter Sky Dock:
   - left side reads as route/status zone;
   - right side reads as boarding gantry;
   - central lane clearly leads between entrance and boarding;
   - utility props cannot be picked up;
   - room should not resemble MiMi's attic.
5. Run/use `cardcha_test_airship`:
   - central helm is the clear focal point;
   - left/right system consoles are visible;
   - all four upgrade machines are visually distinct and sit on matching service pads;
   - machines remain collision-backed and interact within the widened radius;
   - ChaCha resonance corner reads as equipment, not furniture;
   - central transit lane stays clear.

## Next
Do not redesign route/collision again unless a real in-game bug is reported. Next changes after 0648 acceptance should be screenshot-driven visual micro-polish only: spacing, local palette, prop density, or individual sprite readability.
