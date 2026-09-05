from pathlib import Path
import json

ROOT = Path('src/Cardcha')
VERSION_OLD = '0.3.0-alpha.28.0.4.14.4.5.11.3'
VERSION_NEW = '0.3.0-alpha.28.0.4.14.4.5.12'


def replace_once(path: Path, old: str, new: str):
    text = path.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'missing expected block in {path}: {old[:160]!r}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')


def csv_layer(rows):
    # Keep commas between rows, but never emit a terminal comma: TMXTile parses every split token as UInt32.
    return ',\n'.join(','.join(str(v) for v in row) for row in rows)


def build_room_tmx(width: int, height: int, role: str, profile: str, version_property: str) -> str:
    back = [[0 for _ in range(width)] for _ in range(height)]
    buildings = [[0 for _ in range(width)] for _ in range(height)]
    front = [[0 for _ in range(width)] for _ in range(height)]

    left, right = 1, width - 2
    door_left, door_right = width // 2 - 1, width // 2

    # Vanilla townInterior shell. The old full-room custom PNG is intentionally gone.
    for x in range(left, right + 1):
        back[1][x] = 171
        back[2][x] = 171
        back[3][x] = 113
        back[4][x] = 200

    for y in range(5, height - 1):
        for x in range(left, right + 1):
            pair = (232, 233) if y % 2 else (264, 265)
            back[y][x] = pair[(x - left) % 2]

    # A two-tile threshold extends one row into the black surround, like a normal Stardew doorway.
    for x in (door_left, door_right):
        pair = (232, 233) if (height - 1) % 2 else (264, 265)
        back[height - 1][x] = pair[(x - left) % 2]

    buildings[1][left] = 155
    buildings[1][right] = 156
    buildings[2][left] = 187
    buildings[2][right] = 188
    for x in range(left + 1, right):
        buildings[2][x] = 81
    for x in range(left, right + 1):
        buildings[3][x] = 113

    for y in range(4, height - 1):
        buildings[y][left] = 68
        buildings[y][right] = 69

    boundary_y = height - 2
    for x in range(left, right + 1):
        if x not in (door_left, door_right):
            buildings[boundary_y][x] = 1
            front[boundary_y][x] = 166
    front[boundary_y][right] = 167

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" renderorder="right-down" width="{width}" height="{height}" tilewidth="16" tileheight="16" infinite="0" nextlayerid="4" nextobjectid="1">
 <properties>
  <property name="{version_property}" value="alpha.28.0.4.14.4.5.12"/>
  <property name="CardchaAirshipRole" value="{role}"/>
  <property name="CardchaVisualProfile" value="{profile}"/>
  <property name="CardchaArchitecture" value="vanilla-townInterior-shell|real-buildings-collision|two-tile-doorway|no-room-sized-backdrop"/>
 </properties>
 <tileset firstgid="1" name="townInterior" tilewidth="16" tileheight="16" tilecount="2176" columns="32">
  <image source=".townInterior.png" width="512" height="1088"/>
 </tileset>
 <layer id="1" name="Back" width="{width}" height="{height}">
  <data encoding="csv">
{csv_layer(back)}
  </data>
 </layer>
 <layer id="2" name="Buildings" width="{width}" height="{height}">
  <data encoding="csv">
{csv_layer(buildings)}
  </data>
 </layer>
 <layer id="3" name="Front" width="{width}" height="{height}">
  <data encoding="csv">
{csv_layer(front)}
  </data>
 </layer>
</map>
'''


# Version bump.
for rel in ['manifest.json', 'Cardcha.csproj', 'Directory.Build.targets']:
    p = ROOT / rel
    text = p.read_text(encoding='utf-8')
    if VERSION_NEW not in text:
        if VERSION_OLD not in text:
            raise SystemExit(f'expected version not found in {p}')
        text = text.replace(VERSION_OLD, VERSION_NEW)
        p.write_text(text, encoding='utf-8')

# Rebuild both Cardcha-owned Airship rooms from vanilla Stardew tiles.
(ROOT / 'assets/airship_deck.tmx').write_text(
    build_room_tmx(
        24, 14,
        'airship-bridge|navigation-core|upgrade-stations|arcane-dock-return',
        'stardew-airship-bridge|vanilla-shell|warm-wood|small-cardcha-accents',
        'CardchaAirshipVersion'
    ), encoding='utf-8'
)
(ROOT / 'assets/sky_dock_interior.tmx').write_text(
    build_room_tmx(
        30, 18,
        'arcane-dock|route-console|boarding-bay|forest-return',
        'stardew-airship-dock|vanilla-shell|warm-wood|service-room|small-cardcha-accents',
        'CardchaSkyDockVersion'
    ), encoding='utf-8'
)

service = ROOT / 'Services/AirshipFoundationService.cs'
text = service.read_text(encoding='utf-8')

if 'using StardewValley.Objects;' not in text:
    text = text.replace('using StardewValley.Monsters;\n', 'using StardewValley.Monsters;\nusing StardewValley.Objects;\n', 1)

text = text.replace(
'''    private const float BoardingUseDistance = 128f;\n    private const float ForestGateUseDistance = 320f;''',
'''    private const float BoardingUseDistance = 160f;\n    private const float ForestGateUseDistance = 320f;\n    private const string InteriorDecorMarkerKey = "Ronvotri.Cardcha/AirshipInteriorDecor";\n    private const string InteriorDecorVersion = "alpha.28.0.4.14.4.5.12";''', 1)

text = text.replace(
'''    private bool TestGateAccessActive;''',
'''    private bool TestGateAccessActive;\n    private GameLocation? DeckDecorAppliedLocation;\n    private GameLocation? SkyDockDecorAppliedLocation;''', 1)

# Furniture must be installed before the lightweight Cardcha accents draw.
text = text.replace(
'''        if (location?.NameOrUniqueName.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase) == true)\n            this.DrawSkyDockInteriorDetails(e.SpriteBatch, location);\n\n        if (location?.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase) == true)\n            this.DrawDeckMarkers(e.SpriteBatch, location);''',
'''        if (location?.NameOrUniqueName.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase) == true)\n        {\n            this.EnsureSkyDockVanillaFurniture(location);\n            this.DrawSkyDockInteriorDetails(e.SpriteBatch, location);\n        }\n\n        if (location?.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase) == true)\n        {\n            this.EnsureDeckVanillaFurniture(location);\n            this.DrawDeckMarkers(e.SpriteBatch, location);\n        }''', 1)

# Replace exact-dot auto transitions with broad doorway/boarding zones.
old_transition = '''        if (location.NameOrUniqueName.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase))\n        {\n            Point bay = ResolveSkyDockInteriorBayTile(location);\n            Point exit = ResolveSkyDockInteriorExitTile(location);\n            if (playerTile == bay)\n                return this.WarpToAirshipBridge();\n\n            if (playerTile == exit)\n            {\n                this.ReturnToSkyDockExterior();\n                return true;\n            }\n\n            return false;\n        }\n\n        if (location.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase))\n        {\n            Point exit = ResolveDeckExitTile(location);\n            if (playerTile == exit)\n                return this.WarpToSkyDockInterior();\n        }'''
new_transition = '''        if (location.NameOrUniqueName.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase))\n        {\n            Point bay = ResolveSkyDockInteriorBayTile(location);\n            if (IsPortalZone(playerTile, bay, radiusX: 1, radiusY: 1))\n                return this.WarpToAirshipBridge();\n\n            if (IsBottomDoorwayZone(location, playerTile))\n            {\n                this.ReturnToSkyDockExterior();\n                return true;\n            }\n\n            return false;\n        }\n\n        if (location.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase))\n        {\n            if (IsBottomDoorwayZone(location, playerTile))\n                return this.WarpToSkyDockInterior();\n        }'''
if old_transition not in text:
    raise SystemExit('exact transition block not found')
text = text.replace(old_transition, new_transition, 1)

# Fixed arrival and exit anchors. No FindClearTileNear means the visible doorway cannot appear to move as the player approaches.
text = text.replace(
'''    private static Point ResolveSkyDockInteriorArrivalTile(GameLocation interior)\n    {\n        int width = interior.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 30;\n        int height = interior.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 18;\n        return FindClearTileNear(interior, new Point(width / 2, Math.Max(2, height - 4)));\n    }''',
'''    private static Point ResolveSkyDockInteriorArrivalTile(GameLocation interior)\n    {\n        int width = interior.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 30;\n        int height = interior.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 18;\n        return new Point(width / 2, Math.Max(5, height - 4));\n    }''', 1)

text = text.replace(
'''    private static Point ResolveDeckArrivalTile(GameLocation deck)\n    {\n        int width = deck.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 24;\n        int height = deck.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 14;\n        Point preferred = new(width / 2, Math.Max(2, height - 4));\n        return FindClearTileNear(deck, preferred);\n    }''',
'''    private static Point ResolveDeckArrivalTile(GameLocation deck)\n    {\n        int width = deck.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 24;\n        int height = deck.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 14;\n        return new Point(width / 2, Math.Max(5, height - 4));\n    }''', 1)

# Add room-zone helpers + vanilla furniture just before the upgrade socket resolver.
insert_before = '    private static (AirshipUpgradeSystem System, Point Tile)[] ResolveDeckUpgradeSockets()'
if insert_before not in text:
    raise SystemExit('upgrade socket insertion point missing')
helpers = r'''    private static bool IsPortalZone(Point playerTile, Point center, int radiusX, int radiusY)
        => Math.Abs(playerTile.X - center.X) <= radiusX
           && Math.Abs(playerTile.Y - center.Y) <= radiusY;

    private static bool IsBottomDoorwayZone(GameLocation location, Point playerTile)
    {
        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 24;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 14;
        int center = width / 2;
        return playerTile.Y >= height - 2
            && (playerTile.X == center - 1 || playerTile.X == center);
    }

    private void EnsureDeckVanillaFurniture(GameLocation deck)
    {
        if (ReferenceEquals(this.DeckDecorAppliedLocation, deck))
            return;
        this.DeckDecorAppliedLocation = deck;
        ClearInteriorDecor(deck);

        // Vanilla furniture provides authentic Stardew scale, collision, shadows, and depth.
        // Cardcha-only machinery remains a small overlay rather than a room-sized illustration.
        TryAddInteriorFurniture(deck, "(F)1614", 5, 1);   // windows
        TryAddInteriorFurniture(deck, "(F)1614", 11, 1);
        TryAddInteriorFurniture(deck, "(F)1614", 17, 1);
        TryAddInteriorFurniture(deck, "(F)1289", 2, 5);   // service shelves
        TryAddInteriorFurniture(deck, "(F)704", 20, 5);   // storage cabinet
        TryAddInteriorFurniture(deck, "(F)1443", 4, 5);   // warm lamps
        TryAddInteriorFurniture(deck, "(F)1443", 19, 5);
        TryAddInteriorFurniture(deck, "(F)1456", 9, 5);   // helm rug
        TryAddInteriorFurniture(deck, "(F)1120", 7, 6, heldId: "(F)1368");
        TryAddInteriorFurniture(deck, "(F)1120", 15, 6, heldId: "(F)1362");
        deck.modData[InteriorDecorMarkerKey] = InteriorDecorVersion;
    }

    private void EnsureSkyDockVanillaFurniture(GameLocation dock)
    {
        if (ReferenceEquals(this.SkyDockDecorAppliedLocation, dock))
            return;
        this.SkyDockDecorAppliedLocation = dock;
        ClearInteriorDecor(dock);

        TryAddInteriorFurniture(dock, "(F)1614", 5, 1);
        TryAddInteriorFurniture(dock, "(F)1614", 14, 1);
        TryAddInteriorFurniture(dock, "(F)1614", 23, 1);
        TryAddInteriorFurniture(dock, "(F)1289", 2, 5);
        TryAddInteriorFurniture(dock, "(F)704", 26, 5);
        TryAddInteriorFurniture(dock, "(F)1443", 11, 5);
        TryAddInteriorFurniture(dock, "(F)1443", 19, 5);
        TryAddInteriorFurniture(dock, "(F)1120", 7, 6, heldId: "(F)1368");
        TryAddInteriorFurniture(dock, "(F)1623", 4, 11);
        TryAddInteriorFurniture(dock, "(F)432", 3, 13, rotation: 2);
        TryAddInteriorFurniture(dock, "(F)1461", 12, 11);
        dock.modData[InteriorDecorMarkerKey] = InteriorDecorVersion;
    }

    private static void ClearInteriorDecor(GameLocation location)
    {
        foreach (Furniture old in location.furniture
                     .Where(f => f.modData.ContainsKey(InteriorDecorMarkerKey))
                     .ToList())
        {
            location.furniture.Remove(old);
        }
    }

    private static void TryAddInteriorFurniture(
        GameLocation location,
        string itemId,
        int x,
        int y,
        int rotation = 0,
        string? heldId = null)
    {
        try
        {
            Furniture item = ItemRegistry.Create<Furniture>(itemId).SetPlacement(x, y, rotation);
            item.modData[InteriorDecorMarkerKey] = InteriorDecorVersion;
            if (heldId is not null)
                item.SetHeldObject(ItemRegistry.Create<Furniture>(heldId));
            location.furniture.Add(item);
        }
        catch
        {
            // A changed vanilla furniture ID should never make a Cardcha room unloadable.
        }
    }

'''
text = text.replace(insert_before, helpers + insert_before, 1)

# Reset decor references when returning to title.
text = text.replace(
'''        this.LoggedRegion1Creation = false;\n    }''',
'''        this.LoggedRegion1Creation = false;\n        this.DeckDecorAppliedLocation = null;\n        this.SkyDockDecorAppliedLocation = null;\n    }''', 1)

service.write_text(text, encoding='utf-8')

# Lightweight renderer: static geometry only. Remove pulsing/moving exit dots and fake room-window life.
renderer = ROOT / 'Services/AirshipInteriorStardewRenderer.cs'
rtext = renderer.read_text(encoding='utf-8')
rtext = rtext.replace(
'''        DrawDeckWindowLife(batch, phase);\n        DrawHelmAccent(batch, phase);\n        DrawUpgradeStations(batch, save, phase);\n        DrawChaChaPedestalAccent(batch, phase);\n        DrawFloorMarker(batch, new Point(12, 12), new Color(89, 210, 226) * 0.48f, phase * 0.7f);''',
'''        DrawHelmAccent(batch, phase);\n        DrawUpgradeStations(batch, save, phase);\n        DrawChaChaPedestalAccent(batch, phase);\n        DrawDoorwayThreshold(batch, new Point(12, 12), new Color(89, 210, 226) * 0.42f);''', 1)
rtext = rtext.replace(
'''        // Route console, boarding arch, and return tile get tiny pixel-like accents only.\n        DrawConsoleLamp(batch, new Point(10, 7), new Color(194, 132, 70), new Color(170, 105, 223), phase);\n        DrawConsoleLamp(batch, new Point(24, 7), new Color(194, 132, 70), new Color(78, 193, 211), -phase);\n        DrawFloorMarker(batch, new Point(15, 16), new Color(88, 208, 224) * 0.48f, phase * 0.7f);''',
'''        // Route console and boarding bay keep small Cardcha accents; the exit is a fixed\n        // two-tile threshold instead of a pulsing dot the farmer must stand on exactly.\n        DrawConsoleLamp(batch, new Point(10, 7), new Color(194, 132, 70), new Color(170, 105, 223), phase);\n        DrawConsoleLamp(batch, new Point(24, 7), new Color(194, 132, 70), new Color(78, 193, 211), -phase);\n        DrawDoorwayThreshold(batch, new Point(15, 16), new Color(88, 208, 224) * 0.42f);''', 1)

# Replace animated floor-marker method with a static two-tile threshold.
old_marker = '''    private static void DrawFloorMarker(SpriteBatch batch, Point tile, Color color, float phase)\n    {\n        Vector2 c = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 43f);\n        int s = 7 + (int)MathF.Round((MathF.Sin(phase * 2f) + 1f) * 1.5f);\n        DrawDiamond(batch, c, s, color);\n    }'''
new_marker = '''    private static void DrawDoorwayThreshold(SpriteBatch batch, Point tile, Color color)\n    {\n        // Static geometry: approaching the doorway must never make the marker appear to slide.\n        Vector2 c = WorldToScreen(tile.X * 64f, tile.Y * 64f + 54f);\n        DrawRect(batch, new Rectangle((int)c.X - 64, (int)c.Y, 128, 3), color);\n        DrawDiamond(batch, new Vector2(c.X - 54f, c.Y + 1f), 4, color * 0.82f);\n        DrawDiamond(batch, new Vector2(c.X + 54f, c.Y + 1f), 4, color * 0.82f);\n    }'''
if old_marker not in rtext:
    raise SystemExit('floor marker method not found')
rtext = rtext.replace(old_marker, new_marker, 1)
renderer.write_text(rtext, encoding='utf-8')

print('alpha28 0647 generated')
