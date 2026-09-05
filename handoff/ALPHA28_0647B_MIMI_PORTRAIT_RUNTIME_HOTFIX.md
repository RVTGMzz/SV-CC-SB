# ALPHA28 0647B: MiMi Portrait Runtime Hotfix

Branch:
`cardcha-alpha28-0647b-mimi-portrait-runtime-hotfix`

Build:
`0.3.0-alpha.28.0.4.14.4.5.12.2`

Package:
`Cardcha_v0.3.0-alpha.28.0.4.14.4.5.12.2_MiMiPortraitRuntimeHotfix_TEST.zip`

Package SHA-256:
`40610ef4041fa357dd107e32efad7e077cf98990b8593e5c0915c44d4531f14c`

## Root cause fixed
0647A removed the old 64px PNG from the package and correctly made `MimiMysteryTownService` derive the native 64px compatibility sheet in memory from `assets/mimi_portraits.png`. However, `WorldActorService` still registered an older competing handler for `Portraits/Ronvotri.Cardcha_MiMi` first and tried to load the deleted `assets/mimi_portraits_runtime64.png` through `LoadFromModFile`, causing SMAPI `SContentLoadException` at runtime.

0647B removes that competing `WorldActorService` portrait loader. `WorldActorService` may still request the logical `Portraits/Ronvotri.Cardcha_MiMi` game-content asset, but `MimiMysteryTownService` is now the single owner that supplies it from the master-derived in-memory compatibility texture.

## Verified portrait state
- only on-disk MiMi portrait source in the packaged mod: `assets/mimi_portraits.png`
- `assets/mimi_portraits_runtime64.png`: absent
- `assets/mimi_npc_portraits.png`: absent
- final compiled `Cardcha.dll` contains no UTF-8 or UTF-16 reference to either obsolete filename
- final compiled `Cardcha.dll` does contain the canonical `assets/mimi_portraits.png` reference
- story and world dialogue retain nearest-neighbour master-derived compatibility sheets; no averaging blur reintroduced

## CI verification
- workflow run: `33959901128` SUCCESS
- job: `101289848996` SUCCESS
- materialization commit: `b0c9bb1f2b65952d45b32e5e06656ecacdbd9e62`
- artifact ID: `9967595697`
- outer artifact digest: `sha256:dc9bd5b68ab514c93b3d7646534a758c3ecad6d23ac2ea104d2dbe3324c8414c`
- source ownership validation PASS
- compile PASS
- compiled DLL portrait-path audit PASS
- package PASS

## Inherited 0647A movement state
- Home anchor `(10,6)`
- TV anchor `(5,9)`
- Late anchor `(13,7)`
- open-floor wander pools retained
- blocked-tile fallback retained
- `RoutineState` and `WanderTarget` diagnostics retained

## Locked canon / regression guard
- Save schema 19
- Boss Form duration 10 seconds
- Boss Energy gain scale 1/3
- 76/76 active card audit PASS
- Forest Arcane Gate action distance 160px and `CollisionEdits=NONE`
- locked `airship_visual.png` SHA-256 remains `1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132`
- 0647 Airship/Sky Dock room architecture preserved
- Airship route, upgrade menu/costs and deferred gameplay bonuses unchanged

## Acceptance test
1. Replace the previous Cardcha folder with this build and restart SMAPI so no old DLL remains loaded.
2. Load a save and talk to MiMi in any world/social/home dialogue context. There should be no `mimi_portraits_runtime64.png` load error.
3. Test Attic `home`, `tv`, and `late` routine states and verify the 0647A movement behavior still works.
4. If any portrait error remains, capture the first Cardcha error block from the SMAPI log; the final DLL itself has already been verified free of the obsolete paths.
