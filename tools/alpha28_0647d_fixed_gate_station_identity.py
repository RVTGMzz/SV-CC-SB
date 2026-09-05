from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src" / "Cardcha"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.3"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.4"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def replace_region(text: str, start_token: str, end_token: str, replacement: str) -> str:
    start = text.index(start_token)
    end = text.index(end_token, start)
    return text[:start] + replacement + "\n\n" + text[end:]


# Version bump.
for rel in ("manifest.json", "Cardcha.csproj", "Directory.Build.targets"):
    p = CARDCHA / rel
    text = read(p)
    if NEW_VERSION not in text:
        if OLD_VERSION not in text:
            raise RuntimeError(f"missing version anchor in {rel}")
        write(p, text.replace(OLD_VERSION, NEW_VERSION))

# -----------------------------------------------------------------------------
# Forest gate: one deterministic owner, one deterministic tile.
# -----------------------------------------------------------------------------
service_path = CARDCHA / "Services" / "AirshipFoundationService.cs"
service = read(service_path)
service = service.replace(
    "private const float ForestGateUseDistance = 320f;",
    "private const float ForestGateUseDistance = 160f;",
)

resolver = r'''    private Point ResolveSkyDockTile()
    {
        // .5.12.4: one authoritative, deterministic Forest gate anchor.
        // No runtime safe-tile search, flood-fill, or farmer/NPC occupancy is allowed to move it.
        // The -23,+10 offset preserves the accepted farm-side meadow placement immediately
        // right of the pink blossom tree.
        if (this.CachedSkyDockTile is Point cached)
            return cached;

        GameLocation? forest = Game1.getLocationFromName(SkyDockLocationName);
        Point farmWarp = this.ResolveForestFarmWarpTile();
        int width = forest?.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 120;
        int height = forest?.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 120;

        this.CachedSkyDockTile = new Point(
            Math.Clamp(farmWarp.X - 23, 2, Math.Max(2, width - 3)),
            Math.Clamp(farmWarp.Y + 10, 2, Math.Max(2, height - 4))
        );
        return this.CachedSkyDockTile.Value;
    }'''
service = replace_region(
    service,
    "    private Point ResolveSkyDockTile()",
    "    private Point ResolveForestFarmWarpTile()",
    resolver,
)

# The TEST command may warp the farmer, but it must never invalidate/re-roll gate placement.
service = service.replace(
    "        this.TestGateAccessActive = true;\n        this.CachedSkyDockTile = null;\n        Point dock = this.ResolveSkyDockTile();",
    "        this.TestGateAccessActive = true;\n        Point dock = this.ResolveSkyDockTile();",
)

# Remove the living-room vocabulary from both Airship-owned rooms. The bridge keeps only
# windows + two instrument tables; the station keeps a clear central transit lane.
furniture = r'''    private void EnsureDeckVanillaFurniture(GameLocation deck)
    {
        if (ReferenceEquals(this.DeckDecorAppliedLocation, deck))
            return;
        this.DeckDecorAppliedLocation = deck;
        ClearInteriorDecor(deck);

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

        TryAddInteriorFurniture(dock, "(F)1614", 5, 1);
        TryAddInteriorFurniture(dock, "(F)1614", 14, 1);
        TryAddInteriorFurniture(dock, "(F)1614", 23, 1);
        TryAddInteriorFurniture(dock, "(F)1120", 4, 6, heldId: "(F)1368");
        TryAddInteriorFurniture(dock, "(F)1120", 24, 6, heldId: "(F)1362");
        dock.modData[InteriorDecorMarkerKey] = "alpha.28.0.4.14.4.5.12.4-dock";
    }'''
service = replace_region(
    service,
    "    private void EnsureDeckVanillaFurniture(GameLocation deck)",
    "    private static void ClearInteriorDecor(GameLocation location)",
    furniture,
)
write(service_path, service)

# The old Harmony relocation patch was a second placement brain. Retire it entirely.
patch_path = CARDCHA / "Patches" / "AirshipGateRelocationPatch.cs"
write(
    patch_path,
    '''namespace Cardcha.Patches;\n\n/// <summary>\n/// .5.12.4 regression marker only. Forest gate placement is owned exclusively by\n/// AirshipFoundationService.ResolveSkyDockTile. No Harmony relocation/flood-fill is installed.\n/// </summary>\ninternal static class AirshipGateRelocationPatch\n{\n    internal const float CanonicalGateUseDistance = 160f;\n    internal const string CollisionPolicy = "CollisionEdits=NONE";\n}\n''',
)

# -----------------------------------------------------------------------------
# Airship room identity: station != home, bridge != home.
# -----------------------------------------------------------------------------
renderer_path = CARDCHA / "Services" / "AirshipInteriorStardewRenderer.cs"
renderer = read(renderer_path)

sky_method = r'''    public static bool TryDrawSkyDock(SpriteBatch batch, GameLocation dock)
    {
        if (batch is null || dock is null)
            return false;

        float phase = (float)(Environment.TickCount64 / 1000.0);

        // Transit-station silhouette: route board left, boarding gantry right, dock beacon center.
        // These stay on the upper wall and never cover the farmer's walking lane.
        DrawDockWallPanel(batch, new Point(6, 4), 7, new Color(170, 105, 223), phase);
        DrawDockWallPanel(batch, new Point(20, 4), 7, new Color(78, 193, 211), -phase);
        DrawDockBeacon(batch, new Point(15, 4), phase);
        DrawConsoleLamp(batch, new Point(10, 6), new Color(194, 132, 70), new Color(170, 105, 223), phase);
        DrawConsoleLamp(batch, new Point(24, 6), new Color(194, 132, 70), new Color(78, 193, 211), -phase);
        DrawDoorwayThreshold(batch, new Point(15, 16), new Color(88, 208, 224) * 0.42f);
        return true;
    }'''
renderer = replace_region(
    renderer,
    "    public static bool TryDrawSkyDock(SpriteBatch batch, GameLocation dock)",
    "    private static void DrawDeckWindowLife(SpriteBatch batch, float phase)",
    sky_method,
)

# Strengthen Airship Bridge identity without drawing a room-sized custom backdrop.
deck_start = renderer.index("    public static bool TryDrawDeck(SpriteBatch batch, GameLocation deck, SaveService save)")
deck_end = renderer.index("    public static bool TryDrawSkyDock", deck_start)
deck = renderer[deck_start:deck_end]
needle = "        DrawHelmAccent(batch, phase);"
if "DrawBridgeWallPanel(batch" not in deck:
    deck = deck.replace(
        needle,
        "        DrawBridgeWallPanel(batch, new Point(4, 4), new Color(89, 205, 218), phase);\n"
        "        DrawBridgeWallPanel(batch, new Point(19, 4), new Color(177, 106, 225), -phase);\n"
        + needle,
        1,
    )
renderer = renderer[:deck_start] + deck + renderer[deck_end:]

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
    }'''
if "private static void DrawDockWallPanel" not in renderer:
    insert = renderer.index("    private static void DrawConsoleLamp(")
    renderer = renderer[:insert] + helpers + "\n\n" + renderer[insert:]
write(renderer_path, renderer)

print(f"Prepared Cardcha {NEW_VERSION}: deterministic Forest gate + distinct Sky Dock/Airship identity.")
