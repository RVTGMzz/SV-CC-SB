from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / 'src' / 'Cardcha'
OLD_VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.3'
NEW_VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.4'


def read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding='utf-8')


# Version bump.
for rel in ('manifest.json', 'Cardcha.csproj', 'Directory.Build.targets'):
    p = CARDCHA / rel
    text = read(p)
    if NEW_VERSION not in text:
        if OLD_VERSION not in text:
            raise RuntimeError(f'missing version anchor in {rel}')
        text = text.replace(OLD_VERSION, NEW_VERSION)
        write(p, text)

# Gate: one deterministic owner, no runtime safe-tile search. Keep the user-approved
# farm-side placement near the blossom tree and restore the canonical 160px use distance.
service_path = CARDCHA / 'Services' / 'AirshipFoundationService.cs'
service = read(service_path)
service = service.replace('private const float ForestGateUseDistance = 320f;', 'private const float ForestGateUseDistance = 160f;')

old_resolver = '''    private Point ResolveSkyDockTile()\n    {\n        if (this.CachedSkyDockTile is Point cached)\n            return cached;\n\n        GameLocation? forest = Game1.getLocationFromName(SkyDockLocationName);\n        if (forest is null)\n        {\n            this.CachedSkyDockTile = new Point(6, 6);\n            return this.CachedSkyDockTile.Value;\n        }\n\n        Point farmWarp = this.ResolveForestFarmWarpTile();\n        int width = forest.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 120;\n        int height = forest.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 120;\n\n        Point preferred = new(\n            Math.Clamp(farmWarp.X - 7, 2, Math.Max(2, width - 3)),\n            Math.Clamp(farmWarp.Y + 2, 2, Math.Max(2, height - 3))\n        );\n\n        Point? safe = FindSafeDockTile(forest, preferred, farmWarp);\n        this.CachedSkyDockTile = safe ?? preferred;\n        return this.CachedSkyDockTile.Value;\n    }'''
new_resolver = '''    private Point ResolveSkyDockTile()\n    {\n        // .5.12.4: the Forest gate has exactly one owner and one deterministic anchor.\n        // Never search around transient objects/NPCs/farmer position here; that was the source\n        // of the visible gate "running" between nearby tiles. The -23,+10 offset preserves\n        // the accepted farm-side meadow placement immediately right of the blossom tree.\n        if (this.CachedSkyDockTile is Point cached)\n            return cached;\n\n        GameLocation? forest = Game1.getLocationFromName(SkyDockLocationName);\n        Point farmWarp = this.ResolveForestFarmWarpTile();\n        int width = forest?.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 120;\n        int height = forest?.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 120;\n\n        this.CachedSkyDockTile = new Point(\n            Math.Clamp(farmWarp.X - 23, 2, Math.Max(2, width - 3)),\n            Math.Clamp(farmWarp.Y + 10, 2, Math.Max(2, height - 4))\n        );\n        return this.CachedSkyDockTile.Value;\n    }'''
if old_resolver not in service:
    raise RuntimeError('ResolveSkyDockTile anchor block not found')
service = service.replace(old_resolver, new_resolver, 1)

# Debug warp must not invalidate/re-resolve the gate immediately before moving the farmer.
service = service.replace('        this.TestGateAccessActive = true;\n        this.CachedSkyDockTile = null;\n        Point dock = this.ResolveSkyDockTile();',
                          '        this.TestGateAccessActive = true;\n        Point dock = this.ResolveSkyDockTile();', 1)

# Replace the domestic furniture passes with station/bridge-only utility furniture. No couch,
# dresser, plant, bookcase, or home rug language. Wall-mounted/console mass remains sparse so
# the Cardcha machinery renderer defines the room identity rather than home decor.
start = service.index('    private void EnsureDeckVanillaFurniture(GameLocation deck)')
end = service.index('    private static void ClearInteriorDecor(GameLocation location)', start)
new_furniture = r'''    private void EnsureDeckVanillaFurniture(GameLocation deck)
    {
        if (ReferenceEquals(this.DeckDecorAppliedLocation, deck))
            return;
        this.DeckDecorAppliedLocation = deck;
        ClearInteriorDecor(deck);

        // Bridge only: windows + two compact instrument tables. No domestic storage/seating.
        TryAddInteriorFurniture(deck, "(F)1614", 5, 1);
        TryAddInteriorFurniture(deck, "(F)1614", 11, 1);
        TryAddInteriorFurniture(deck, "(F)1614", 17, 1);
        TryAddInteriorFurniture(deck, "(F)1120", 3, 5, heldId: "(F)1368");
        TryAddInteriorFurniture(deck, "(F)1120", 19, 5, heldId: "(F)1362");
        deck.modData[InteriorDecorMarkerKey] = "alpha.28.0.4.14.4.5.12.4-bridge";
    }

    private void EnsureSkyDockVanillaFurniture(GameLocation dock)
    {
        if (ReferenceEquals(this.SkyDockDecorAppliedLocation, dock))
            return;
        this.SkyDockDecorAppliedLocation = dock;
        ClearInteriorDecor(dock);

        // Transit/workshop station only. Keep the central boarding lane clear and remove every
        // living-room cue that made this room resemble MiMi's attic.
        TryAddInteriorFurniture(dock, "(F)1614", 5, 1);
        TryAddInteriorFurniture(dock, "(F)1614", 14, 1);
        TryAddInteriorFurniture(dock, "(F)1614", 23, 1);
        TryAddInteriorFurniture(dock, "(F)1120", 4, 6, heldId: "(F)1368");
        TryAddInteriorFurniture(dock, "(F)1120", 24, 6, heldId: "(F)1362");
        dock.modData[InteriorDecorMarkerKey] = "alpha.28.0.4.14.4.5.12.4-dock";
    }

'''
service = service[:start] + new_furniture + service[end:]
write(service_path, service)

# Retire the old Harmony relocation brain entirely. Keep a tiny regression marker so CI and
# future readers know the 160px/no-collision contract without installing any runtime patch.
patch_path = CARDCHA / 'Patches' / 'AirshipGateRelocationPatch.cs'
write(patch_path, '''namespace Cardcha.Patches;\n\n/// <summary>\n/// .5.12.4 regression marker only. Forest gate placement is owned exclusively by\n/// AirshipFoundationService.ResolveSkyDockTile. No Harmony relocation/flood-fill is installed.\n/// </summary>\ninternal static class AirshipGateRelocationPatch\n{\n    internal const float CanonicalGateUseDistance = 160f;\n    internal const string CollisionPolicy = "CollisionEdits=NONE";\n}\n''')

# Renderer: make Sky Dock read as a transit bay and Airship Deck as a bridge, while staying
# hard-edged/pixel aligned and avoiding floor overlays that would paint over the farmer.
renderer_path = CARDCHA / 'Services' / 'AirshipInteriorStardewRenderer.cs'
renderer = read(renderer_path)

old_sky = '''    public static bool TryDrawSkyDock(SpriteBatch batch, GameLocation dock)\n    {\n        if (batch is null || dock is null)\n            return false;\n\n        float phase = (float)(Environment.TickCount64 / 1000.0);\n\n        // Route console and boarding bay keep small Cardcha accents; the exit is a fixed\n        // two-tile threshold instead of a pulsing dot the farmer must stand on exactly.\n        DrawConsoleLamp(batch, new Point(10, 7), new Color(194, 132, 70), new Color(170, 105, 223), phase);\n        DrawConsoleLamp(batch, new Point(24, 7), new Color(194, 132, 70), new Color(78, 193, 211), -phase);\n        DrawDoorwayThreshold(batch, new Point(15, 16), new Color(88, 208, 224) * 0.42f);\n        return true;\n    }'''
new_sky = '''    public static bool TryDrawSkyDock(SpriteBatch batch, GameLocation dock)\n    {\n        if (batch is null || dock is null)\n            return false;\n\n        float phase = (float)(Environment.TickCount64 / 1000.0);\n\n        // Distinct transit-station silhouette: route board on the left, boarding gantry on the\n        // right, and a central overhead dock beacon. All pieces live against the upper wall so\n        // they cannot paint over the farmer's walking lane.\n        DrawDockWallPanel(batch, new Point(6, 4), widthTiles: 7, new Color(170, 105, 223), phase);\n        DrawDockWallPanel(batch, new Point(20, 4), widthTiles: 7, new Color(78, 193, 211), -phase);\n        DrawDockBeacon(batch, new Point(15, 4), phase);\n        DrawConsoleLamp(batch, new Point(10, 6), new Color(194, 132, 70), new Color(170, 105, 223), phase);\n        DrawConsoleLamp(batch, new Point(24, 6), new Color(194, 132, 70), new Color(78, 193, 211), -phase);\n        DrawDoorwayThreshold(batch, new Point(15, 16), new Color(88, 208, 224) * 0.42f);\n        return true;\n    }'''
if old_sky not in renderer:
    raise RuntimeError('TryDrawSkyDock block not found')
renderer = renderer.replace(old_sky, new_sky, 1)

# Strengthen bridge identity with two wall panels flanking the helm.
old_deck_tail = '''        DrawHelmAccent(batch, phase);\n        DrawUpgradeStations(batch, save, phase);\n        DrawChaChaPedestalAccent(batch, phase);\n        DrawDoorwayThreshold(batch, new Point(12, 12), new Color(89, 210, 226) * 0.42f);'''
new_deck_tail = '''        DrawBridgeWallPanel(batch, new Point(4, 4), new Color(89, 205, 218), phase);\n        DrawBridgeWallPanel(batch, new Point(19, 4), new Color(177, 106, 225), -phase);\n        DrawHelmAccent(batch, phase);\n        DrawUpgradeStations(batch, save, phase);\n        DrawChaChaPedestalAccent(batch, phase);\n        DrawDoorwayThreshold(batch, new Point(12, 12), new Color(89, 210, 226) * 0.42f);'''
if old_deck_tail not in renderer:
    raise RuntimeError('deck render tail not found')
renderer = renderer.replace(old_deck_tail, new_deck_tail, 1)

insert_at = renderer.index('    private static void DrawConsoleLamp(')
helpers = r'''    private static void DrawDockWallPanel(SpriteBatch batch, Point centerTile, int widthTiles, Color accent, float phase)
    {
        Vector2 c = WorldToScreen(centerTile.X * 64f + 32f, centerTile.Y * 64f + 10f);
        int w = Math.Max(3, widthTiles) * 44;
        Rectangle outer = new((int)c.X - w / 2, (int)c.Y - 34, w, 54);
        DrawRect(batch, outer, new Color(47, 34, 37) * 0.96f);
        DrawRect(batch, new Rectangle(outer.X + 5, outer.Y + 5, outer.Width - 10, outer.Height - 10), new Color(104, 63, 47) * 0.94f);
        DrawRect(batch, new Rectangle(outer.X + 12, outer.Y + 12, outer.Width - 24, 7), new Color(194, 132, 70) * 0.82f);
        float glow = 0.55f + 0.12f * MathF.Sin(phase * 1.8f);
        for (int i = 0; i < 4; i++)
        {
            int x = outer.X + 20 + i * Math.Max(28, (outer.Width - 44) / 4);
            DrawRect(batch, new Rectangle(x, outer.Y + 28, 18, 6), (i % 2 == 0 ? accent : new Color(88, 208, 224)) * glow);
        }
    }

    private static void DrawDockBeacon(SpriteBatch batch, Point tile, float phase)
    {
        Vector2 c = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f - 2f);
        Color brass = new Color(205, 148, 73) * 0.88f;
        Color cyan = new Color(90, 214, 226) * (0.52f + 0.10f * MathF.Sin(phase * 2f));
        DrawRect(batch, new Rectangle((int)c.X - 20, (int)c.Y - 24, 40, 8), new Color(48, 31, 36) * 0.95f);
        DrawRect(batch, new Rectangle((int)c.X - 14, (int)c.Y - 20, 28, 3), brass);
        DrawDiamond(batch, c + new Vector2(0f, -31f), 6, cyan);
    }

    private static void DrawBridgeWallPanel(SpriteBatch batch, Point tile, Color accent, float phase)
    {
        Vector2 c = WorldToScreen(tile.X * 64f + 32f, tile.Y * 64f + 8f);
        Rectangle body = new((int)c.X - 56, (int)c.Y - 30, 112, 46);
        DrawRect(batch, body, new Color(49, 33, 37) * 0.96f);
        DrawRect(batch, new Rectangle(body.X + 5, body.Y + 5, body.Width - 10, body.Height - 10), new Color(113, 68, 49) * 0.92f);
        DrawRect(batch, new Rectangle(body.X + 14, body.Y + 12, 36, 7), new Color(86, 177, 192) * 0.72f);
        DrawRect(batch, new Rectangle(body.X + 58, body.Y + 12, 36, 7), accent * (0.58f + 0.10f * MathF.Sin(phase * 1.7f)));
        DrawRect(batch, new Rectangle(body.X + 18, body.Y + 27, 76, 3), new Color(205, 148, 73) * 0.78f);
    }

'''
renderer = renderer[:insert_at] + helpers + renderer[insert_at:]
write(renderer_path, renderer)

print(f'Prepared Cardcha {NEW_VERSION}: fixed deterministic Forest gate and separated Airship/Sky Dock visual identity from MiMi attic.')
