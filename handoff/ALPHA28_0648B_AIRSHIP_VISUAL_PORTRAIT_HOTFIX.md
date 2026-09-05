# ALPHA28 0648B - Airship Visual + Portrait Hotfix

## Canonical branch
`cardcha-alpha28-0648b-airship-visual-portrait-hotfix`

## Build
- Version: `0.3.0-alpha.28.0.4.14.4.5.12.8`
- TEST package: `Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.8_AirshipVisualPortraitHotfix_TEST.zip`
- TEST SHA-256: `332b983014eba446e096376bdf8d57259f179c864e23f03ccd513cc19bda0873`
- Compiled `Cardcha.dll`: 761856 bytes

## CI
- Workflow: `.github/workflows/cardcha-alpha28-0648b-airship-visual-portrait-hotfix.yml`
- Successful run: `33984927134`
- Job: `101356582883`
- Artifact ID: `9974860879`
- Artifact name: `cardcha-alpha28-0648b-airship-visual-portrait-hotfix`
- Artifact digest: `sha256:ca55f2ea0ebe430fcddfde53907c6495a5b81617644cb6a26eeac5e471684c09`
- Materialization commit: `5cd78c8f0b8c61eb02efdbe038759cee472d2fc5`

## Acceptance fixes

### 1. Forest Arcane Gate stability
- Portal geometry no longer rotates/rebuilds as the farmer moves.
- Removed the moving cloud/sigil treatment inside the Forest gate aperture.
- The portal keeps a fixed arch, fixed magical glass lines and small stable runes.
- Gate aperture color follows the current time/weather palette.
- Locked gate location and normal 160px action-only Forest interaction remain unchanged.
- Forest collision is still not edited.

### 2. Airship/Sky Dock architecture now uses a vanilla Stardew shell
- `airship_deck.tmx` and `sky_dock_interior.tmx` use vanilla `townInterior` tiles for wall/floor shell.
- `airship_deck_stardew.png` and `sky_dock_stardew.png` are transparent decor sheets rather than full-room fake backdrops.
- Custom decor remains no-pickup.
- Invisible full-width collision bands from 0648A were removed. Buildings collision now exists only for visible walls/boundaries/consoles/machines/service props.
- Bottom exits remain exactly two tiles wide.

### 3. Sky Dock interaction readability
- Route board interaction is exact-action-tile instead of broad proximity.
- Boarding transition happens only on the visible boarding pad.
- Empty wall/floor presses no longer use the broad 176px proximity trigger.
- Forest return remains the visible bottom doorway.

### 4. Four independent Airship infrastructure stations
New physical sockets:
- Engine: `(4,8)`
- Navigation: `(19,8)`
- Hull: `(7,11)`
- Reactor: `(16,11)`

The center aisle is clear. Stations are distributed across the usable lower floor instead of forming two tight clumps.

`AirshipUpgradeMenu` is now single-system:
- pressing Engine opens Engine only;
- pressing Navigation opens Navigation only;
- pressing Hull opens Hull only;
- pressing Reactor opens Reactor only.

No row selector can jump from one physical station to another system inside the same panel. Upgrade costs/levels/save fields are unchanged.

### 5. Magical lighting/readability
- Airship bridge now renders warm pixel lamps, helm light, machine halos, sparks and ChaCha resonance light.
- Every machine has a readable active glow even at level 0; higher levels add more spark activity.
- The room remains warm wood/brass with teal/violet magic accents rather than full neon.

### 6. Flight cutscene follows world time/weather
The old fixed dark-blue screen, fake wooden stage and two straight cloud bars were removed.

Flight sky now resolves from:
- clear daytime;
- dawn;
- dusk;
- night with stars;
- rain;
- lightning with restrained flashes;
- snow;
- debris/windy weather.

The locked Airship exterior sprite and propeller motion remain unchanged.

### 7. MiMi disposed portrait crash
Root cause was Cardcha retaining a service-owned runtime `Texture2D` while the same portrait was also exposed through GameContent. A content invalidation could dispose the texture while a later DialogueBox still referenced it.

0648B:
- removes cached `MasterPortraitSheet` / `RuntimePortraitSheet` fields;
- keeps `assets/mimi_portraits.png` as the single master source;
- the compatibility portrait asset is freshly generated for GameContent ownership;
- Cardcha dialogue requests the live `Portraits/Ronvotri.Cardcha_MiMi` GameContent texture;
- if a returned portrait is already disposed, the cache is invalidated and reloaded before opening DialogueBox.

This specifically targets the reported `ObjectDisposedException` involving SpaceCore/PelipperTown patched portrait drawing.

### 8. WizardHouse destructive tile edit removed
0648A and earlier called `PrepareWizardStairArea()` every rendered frame, clearing `Buildings` and `Front` tiles around Cardcha's attic entrance. This could visibly cut WizardHouse or another mod's decoration.

0648B no longer calls that destructive helper. The attic marker instead chooses a deterministic clear right-half floor position and is cached, without deleting WizardHouse tiles.

A full SMAPI restart is required after installing 0648B so WizardHouse reloads cleanly from content after an older build may already have removed runtime tiles.

## Independent package verification
- Manifest version verified `.5.12.8`.
- DLL exists and is 761856 bytes.
- Airship Deck map: `24x14`, layers `Back`, `BackDecor`, `Buildings`, `Front`.
- Sky Dock map: `30x18`, same layer model.
- Both `Back` layers contain only vanilla tile GIDs `<4096`.
- Both `BackDecor` layers use custom transparent decor GIDs `>=4096`.
- Airship bottom openings: `[11,12]` only.
- Sky Dock bottom openings: `[14,15]` only.
- Locked `airship_visual.png` SHA remains `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`.
- `mimi_portraits.png` is present and remains the master portrait source.

Materialized visual hashes:
- `airship_deck_stardew.png`: `dd1355a99d299218743e36f36686e9b71ef9d987cb29a35e15edac98f5ff43a9`
- `sky_dock_stardew.png`: `9887e074f9579b38e077174da2ed1f04d5d4a598aa8149406eab8ba306c133e8`
- `airship_upgrade_visuals.png`: `54e685feb0e8611c69c5e07f840ad8f43282c7edb53f04ec0ffb8931ed64b861`
- `mimi_portraits.png`: `550a823b2481dd6b54530e3bae2525016f178932f547692501ba64b3206f17e0`

## Locked canon / regression guard
- Save schema 19.
- Boss Form duration 10 seconds.
- Boss Energy gain scale 1/3.
- 76/76 active cards remain the active set.
- Airship exterior locked SHA unchanged.
- Route remains `Forest -> Cardcha_SkyDockInterior -> Cardcha_AirshipDeck`.
- Upgrade costs/levels/save fields unchanged.
- Deferred Airship gameplay bonuses remain disabled.
- MiMi normal home/TV/late routine and TEST clock preview from 0648A remain intact.

## In-game acceptance test
1. Fully restart SMAPI after replacing the old Cardcha folder.
2. `cardcha_test_gate`: walk around the Forest gate and confirm its visual geometry is stable.
3. Enter Sky Dock: pressing empty floor/walls must do nothing. Step onto the visible boarding pad to transition.
4. `cardcha_test_airship`: verify center aisle is clear and no invisible floor blockers remain.
5. Interact with each of the four machines. Each panel must contain only that one system.
6. Verify lamps, machine glow/sparks, helm glow and ChaCha resonance lighting are visible.
7. Start an Airship flight at day/night and confirm the scene uses matching sky treatment; rain/snow/lightning/debris should use matching weather particles when naturally active.
8. Talk to MiMi and confirm no disposed portrait crash.
9. Visit WizardHouse after a full restart and confirm Cardcha no longer cuts existing room decoration.
