#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('src/Cardcha')
OLD = '0.3.0-alpha.28.0.4.14.4.5.12.45.3'
NEW = '0.3.0-alpha.28.0.4.14.4.5.12.45.3.1'

for rel in ['manifest.json','Cardcha.csproj','Directory.Build.targets','ModEntry.cs']:
    p = ROOT / rel
    s = p.read_text(encoding='utf-8')
    if OLD not in s:
        raise SystemExit(f'{rel}: expected {OLD} missing')
    s = s.replace(OLD, NEW)
    s = s.replace('AIRSHIP TWO-ROOM NATIVE DECOR REBUILD TEST', '0677A SYSTEM RECHECK + AIRSHIP LIFECYCLE HOTFIX TEST')
    p.write_text(s, encoding='utf-8')

p = ROOT / 'Services/AirshipFoundationService.cs'
s = p.read_text(encoding='utf-8')

# Create physical Furniture/Object in lifecycle events, never while RenderedWorld is executing.
first = '''        this.EnsureDeckLocation();\n        this.EnsureSkyDockInteriorLocation();\n        this.EnsureRegion1Location();'''
replacement = '''        GameLocation? deck = this.EnsureDeckLocation();\n        GameLocation? dock = this.EnsureSkyDockInteriorLocation();\n        this.EnsureRegion1Location();\n        if (deck is not null) this.EnsureDeckVanillaFurniture(deck);\n        if (dock is not null) this.EnsureSkyDockVanillaFurniture(dock);'''
if s.count(first) < 2:
    raise SystemExit(f'expected SaveLoaded + DayStarted ensure anchors, found {s.count(first)}')
s = s.replace(first, replacement, 2)

old_dock_render = '''        if (location?.NameOrUniqueName.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase) == true)\n        {\n            this.EnsureSkyDockVanillaFurniture(location);\n            this.DrawSkyDockInteriorDetails(e.SpriteBatch, location);\n        }'''
old_deck_render = '''        if (location?.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase) == true)\n        {\n            this.EnsureDeckVanillaFurniture(location);\n            this.DrawDeckMarkers(e.SpriteBatch, location);\n        }'''
if old_dock_render not in s or old_deck_render not in s:
    raise SystemExit('RenderedWorld furniture mutation anchor missing')
s = s.replace(old_dock_render, '''        if (location?.NameOrUniqueName.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase) == true)\n            this.DrawSkyDockInteriorDetails(e.SpriteBatch, location);''', 1)
s = s.replace(old_deck_render, '''        if (location?.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase) == true)\n            this.DrawDeckMarkers(e.SpriteBatch, location);''', 1)

warp_anchor = '''    public void OnWarped(object? sender, WarpedEventArgs e)\n    {\n        if (!Context.IsWorldReady || !Context.IsMainPlayer)\n            return;\n'''
if warp_anchor not in s:
    raise SystemExit('OnWarped anchor missing')
s = s.replace(warp_anchor, warp_anchor + '''\n        if (e.NewLocation.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase))\n            this.EnsureDeckVanillaFurniture(e.NewLocation);\n        else if (e.NewLocation.NameOrUniqueName.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase))\n            this.EnsureSkyDockVanillaFurniture(e.NewLocation);\n''', 1)

# Conservative safety moat around four upgrade interaction sockets.
repositions = {
    'TryAddInteriorFurniture(deck, "(F)1120", 3, 7, heldId: "(F)1369");': 'TryAddInteriorFurniture(deck, "(F)1120", 1, 6, heldId: "(F)1369");',
    'TryAddInteriorFurniture(deck, "(F)704", 6, 10);': 'TryAddInteriorFurniture(deck, "(F)704", 3, 11);',
    'TryAddInteriorFurniture(deck, "(F)1132", 18, 7, heldId: "(F)1368");': 'TryAddInteriorFurniture(deck, "(F)1132", 21, 6, heldId: "(F)1368");',
    'TryAddInteriorFurniture(deck, "(F)1132", 15, 10, heldId: "(F)1368");': 'TryAddInteriorFurniture(deck, "(F)1132", 21, 11, heldId: "(F)1368");',
}
for old, new in repositions.items():
    if old not in s:
        raise SystemExit(f'missing furniture placement anchor: {old}')
    s = s.replace(old, new, 1)

old_method = '''private static void TryAddInteriorFurniture(\n    GameLocation location,\n    string itemId,\n    int x,\n    int y,\n    int rotation = 0,\n    string? heldId = null)\n{\n    try\n    {\n        Furniture item = ItemRegistry.Create<Furniture>(itemId).SetPlacement(x, y, rotation);\n        item.modData[InteriorDecorMarkerKey] = InteriorDecorVersion;\n        if (heldId is not null)\n            item.SetHeldObject(ItemRegistry.Create<Furniture>(heldId));\n        location.furniture.Add(item);\n    }\n    catch\n    {\n        // A changed vanilla furniture ID must never make either Airship room unloadable.\n    }\n}\n'''
new_method = '''private static void TryAddInteriorFurniture(\n    GameLocation location,\n    string itemId,\n    int x,\n    int y,\n    int rotation = 0,\n    string? heldId = null)\n{\n    Furniture item;\n    try\n    {\n        item = ItemRegistry.Create<Furniture>(itemId).SetPlacement(x, y, rotation);\n    }\n    catch (Exception ex)\n    {\n        ModEntry.StaticMonitor?.Log($"0677A skipped invalid Airship furniture {itemId} at {x},{y}: {ex.GetType().Name}: {ex.Message}", StardewModdingAPI.LogLevel.Warn);\n        return;\n    }\n\n    item.modData[InteriorDecorMarkerKey] = InteriorDecorVersion;\n    if (heldId is not null)\n    {\n        try\n        {\n            item.SetHeldObject(ItemRegistry.Create<Furniture>(heldId));\n        }\n        catch (Exception ex)\n        {\n            ModEntry.StaticMonitor?.Log($"0677A kept Airship furniture {itemId} but skipped held decor {heldId}: {ex.GetType().Name}", StardewModdingAPI.LogLevel.Trace);\n        }\n    }\n    location.furniture.Add(item);\n}\n'''
if old_method not in s:
    raise SystemExit('TryAddInteriorFurniture method anchor missing')
s = s.replace(old_method, new_method, 1)

# Add room health telemetry to existing cardcha_airship_status.
describe_anchor = 'return $"GateTest={this.TestGateAccessActive} | " +'
if describe_anchor not in s:
    raise SystemExit('Describe anchor missing')
telemetry = '''GameLocation? deckRoom = Game1.getLocationFromName(DeckLocationName);\n        GameLocation? dockRoom = Game1.getLocationFromName(SkyDockInteriorLocationName);\n        int deckFurniture = deckRoom?.furniture.Count(f => f.modData.ContainsKey(InteriorDecorMarkerKey)) ?? 0;\n        int dockFurniture = dockRoom?.furniture.Count(f => f.modData.ContainsKey(InteriorDecorMarkerKey)) ?? 0;\n        bool lostFoundPresent = false;\n        if (dockRoom is not null)\n        {\n            Point lfTile = ResolveSkyDockLostFoundTile(dockRoom);\n            lostFoundPresent = dockRoom.Objects.TryGetValue(new Vector2(lfTile.X, lfTile.Y), out StardewValley.Object? lf) && lf is Chest;\n        }\n        '''
s = s.replace(describe_anchor, telemetry + describe_anchor, 1)
status_fragment = '$"DeckExists={deckExists} | InteriorExists={interiorExists} | Region1Exists={region1Exists} | Flights='
if status_fragment not in s:
    raise SystemExit('Describe status fragment missing')
s = s.replace(status_fragment, '$"DeckExists={deckExists} | InteriorExists={interiorExists} | Region1Exists={region1Exists} | NativeDecor=Bridge:{deckFurniture},Dock:{dockFurniture},LostFound:{lostFoundPresent} | Flights=', 1)

p.write_text(s, encoding='utf-8')

Path('handoff/ALPHA28_0677A_SYSTEM_RECHECK_HOTFIX.md').write_text('''# Cardcha alpha28 — 0677A System Recheck + Airship Lifecycle Hotfix\n\nBuild: `0.3.0-alpha.28.0.4.14.4.5.12.45.3.1`\nBranch: `cardcha-alpha28-0677a-system-recheck-hotfix`\n\n## Recheck scope\n- startup/Harmony targets\n- Airship Bridge/Dock native decor lifecycle and interaction lanes\n- 40/60/80 milestone route\n- Region III/IV wave/extraction loop\n- render-depth contract\n- map CSV and package/version consistency\n\n## Concrete fixes found during recheck\n1. Native Airship furniture was being created from `RenderedWorld`; it now initializes on save/day/warp lifecycle instead.\n2. Four large furniture origins sat too close to Engine/Navigation/Hull/Reactor interaction sockets; they were moved outside a conservative safety moat.\n3. Optional held-table decoration failure could discard an otherwise valid base furniture item; held-decor failure is now non-fatal and logged.\n4. `cardcha_airship_status` now reports Cardcha-owned native furniture counts and Lost & Found chest presence.\n\n## Known remaining visual debt\nBoss I body/summons/Totems and Boss II-IV authored bodies still use legacy post-world actor drawing. This is tracked by the repository render-depth audit and is NOT accepted yet.\n\nNo balance, card progression, fare, save schema, MiMi art, ChaCha mechanics, boss thresholds, or expedition rewards changed.\n''', encoding='utf-8')
Path('handoff/LATEST_CARDCHA_HANDOFF.md').write_text('''# Latest Cardcha Handoff\n\nCurrent branch: `cardcha-alpha28-0677a-system-recheck-hotfix`\nCurrent build: `0.3.0-alpha.28.0.4.14.4.5.12.45.3.1`\nContinue from: `handoff/ALPHA28_0677A_SYSTEM_RECHECK_HOTFIX.md`\n\n0677A is a system recheck/hardening pass over 0677. Rendering depth contract remains mandatory. Boss actor post-world rendering remains known debt pending a dedicated migration and screenshot acceptance.\n''', encoding='utf-8')

print('0677A generator complete')
