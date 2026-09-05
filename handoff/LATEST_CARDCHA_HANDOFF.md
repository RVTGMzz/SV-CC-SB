# Latest Cardcha handoff

Current development branch:
`cardcha-alpha28-0648b-airship-visual-portrait-hotfix`

Current build:
`0.3.0-alpha.28.0.4.14.4.5.12.8`

Read this FIRST when resuming from another chat:
`handoff/ALPHA28_0648B_AIRSHIP_VISUAL_PORTRAIT_HOTFIX.md`

Previous handoffs:
- `handoff/ALPHA28_0648A_AIRSHIP_MIMI_ACCEPTANCE_HOTFIX.md`
- `handoff/ALPHA28_0648_STARDew_VISUAL_PASS1.md`
- `handoff/ALPHA28_0647E_AIRSHIP_PHYSICAL_DEPTH_REBUILD.md`
- `handoff/ALPHA28_0647D_FIXED_GATE_STATION_IDENTITY.md`
- `handoff/ALPHA28_0647C_AIRSHIP_TMX_CSV_HOTFIX.md`
- `handoff/ALPHA28_0647B_MIMI_PORTRAIT_RUNTIME_HOTFIX.md`
- `handoff/ALPHA28_0647A_MIMI_PORTRAIT_UNIFICATION.md`

## Current verified state
- `.5.12.8` is the screenshot-driven 0648B visual architecture + portrait lifecycle hotfix.
- Forest Arcane Gate no longer rotates/rebuilds portal sigils/clouds as the player moves. The arch is stable and the aperture uses a time/weather-aware palette.
- Airship Deck and Sky Dock now use vanilla `townInterior` tiles as their real wall/floor shell. Cardcha PNGs are transparent decor sheets rather than full-room fake textures.
- The broad invisible collision rows from 0648A were removed. Collision is restricted to visible walls, boundaries, consoles, machines and service props.
- Sky Dock route board and boarding gate use exact visible interaction points. Auto transition happens only on the visible boarding pad.
- Airship infrastructure sockets are separated: Engine `(4,8)`, Navigation `(19,8)`, Hull `(7,11)`, Reactor `(16,11)`. Center aisle is clear.
- Each physical Airship machine now opens a one-system-only upgrade panel. Upgrade costs, max level and persisted fields are unchanged.
- Airship bridge adds visible warm pixel lamps, helm glow, machine halos/sparks and ChaCha resonance lighting.
- Flight cutscene sky follows time/weather: day, dawn, dusk, night/stars, rain, lightning, snow, debris/wind.
- MiMi portrait no longer stores a service-owned runtime Texture2D. `mimi_portraits.png` remains the master source, while live dialogue uses the current GameContent-owned `Portraits/Ronvotri.Cardcha_MiMi` texture and reloads if disposed.
- Cardcha no longer calls the WizardHouse tile-clearing stair helper. The attic marker chooses a deterministic clear position without deleting WizardHouse `Buildings`/`Front` tiles.

## Verified build
- workflow run: `33984927134` SUCCESS
- job: `101356582883` SUCCESS
- materialization commit: `5cd78c8f0b8c61eb02efdbe038759cee472d2fc5`
- artifact ID: `9974860879`
- outer artifact digest: `sha256:ca55f2ea0ebe430fcddfde53907c6495a5b81617644cb6a26eeac5e471684c09`
- package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.8_AirshipVisualPortraitHotfix_TEST.zip`
- package SHA-256: `332b983014eba446e096376bdf8d57259f179c864e23f03ccd513cc19bda0873`
- compiled DLL size: `761856` bytes

## Materialized visual hashes
- `airship_deck_stardew.png`: `dd1355a99d299218743e36f36686e9b71ef9d987cb29a35e15edac98f5ff43a9`
- `sky_dock_stardew.png`: `9887e074f9579b38e077174da2ed1f04d5d4a598aa8149406eab8ba306c133e8`
- `airship_upgrade_visuals.png`: `54e685feb0e8611c69c5e07f840ad8f43282c7edb53f04ec0ffb8931ed64b861`
- `mimi_portraits.png`: `550a823b2481dd6b54530e3bae2525016f178932f547692501ba64b3206f17e0`

## Locked canon / regression guard
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active card audit remains the locked active set.
- Forest Arcane Gate normal action distance remains 160px and Forest collision stays untouched.
- locked `airship_visual.png` SHA unchanged: `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- Airship route remains `Forest -> Cardcha_SkyDockInterior -> Cardcha_AirshipDeck`.
- Airship upgrade costs/levels/save fields and deferred gameplay bonuses unchanged.
- MiMi 0648A HOME/TV/LATE routine test preview remains intact.

## Next action
Delete/replace the entire old Cardcha folder and fully restart SMAPI. Test the stable Forest gate, Sky Dock visible boarding pad, Airship center aisle + four separate machine panels, magical lighting, time/weather flight scene, MiMi dialogue portrait, and WizardHouse decoration integrity. A full restart is especially important because older builds may already have removed WizardHouse tiles in the current runtime session.
