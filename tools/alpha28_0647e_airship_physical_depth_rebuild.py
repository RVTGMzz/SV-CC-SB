from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
CARDCHA = ROOT / "src" / "Cardcha"
ASSETS = CARDCHA / "assets"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.4"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.5"
BACKDROP_GID = 4096


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def replace_region(text: str, start_token: str, end_token: str, replacement: str) -> str:
    start = text.index(start_token)
    end = text.index(end_token, start)
    return text[:start] + replacement.rstrip() + "\n\n" + text[end:]


def csv_layer(values, width):
    rows = []
    for y in range(len(values) // width):
        rows.append(",".join(str(v) for v in values[y*width:(y+1)*width]))
    return "\n".join(rows)


def build_backdrop_tmx(width: int, height: int, image_name: str, role: str, profile: str, blocked: set[tuple[int,int]], bottom_open: set[int]) -> str:
    total = width * height
    back = [BACKDROP_GID + i for i in range(total)]
    buildings = [0] * total
    front = [0] * total

    # Physical shell. The visual comes from the Cardcha backdrop; duplicate the exact same tile
    # on Buildings where we need collision, so there is no extra visible rectangle or fake prop.
    physical = set(blocked)
    for x in range(width):
        physical.add((x, 0))
        physical.add((x, 1))
        physical.add((x, 2))
        physical.add((x, 3))
        if x not in bottom_open:
            physical.add((x, height - 1))
    for y in range(height):
        physical.add((0, y))
        physical.add((width - 1, y))

    for x, y in physical:
        if 0 <= x < width and 0 <= y < height:
            buildings[y * width + x] = BACKDROP_GID + y * width + x

    props = f''' <properties>\n  <property name="CardchaAirshipVersion" value="alpha.28.0.4.14.4.5.12.5"/>\n  <property name="CardchaAirshipRole" value="{role}"/>\n  <property name="CardchaVisualProfile" value="{profile}"/>\n  <property name="CardchaArchitecture" value="cardcha-backdrop|physical-buildings-collision|dynamic-machines|no-pickup-props"/>\n </properties>'''
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" renderorder="right-down" width="{width}" height="{height}" tilewidth="16" tileheight="16" infinite="0" nextlayerid="4" nextobjectid="1">
{props}
 <tileset firstgid="1" name="townInterior" tilewidth="16" tileheight="16" tilecount="2176" columns="32">
  <image source=".townInterior.png" width="512" height="1088"/>
 </tileset>
 <tileset firstgid="{BACKDROP_GID}" name="cardchaPhysicalBackdrop_{Path(image_name).stem}" tilewidth="16" tileheight="16" tilecount="{total}" columns="{width}">
  <image source="{image_name}" width="{width*16}" height="{height*16}"/>
 </tileset>
 <layer id="1" name="Back" width="{width}" height="{height}">
  <data encoding="csv">\n{csv_layer(back, width)}\n  </data>
 </layer>
 <layer id="2" name="Buildings" width="{width}" height="{height}">
  <data encoding="csv">\n{csv_layer(buildings, width)}\n  </data>
 </layer>
 <layer id="3" name="Front" width="{width}" height="{height}">
  <data encoding="csv">\n{csv_layer(front, width)}\n  </data>
 </layer>
</map>\n'''


# Version bump.
for rel in ("manifest.json", "Cardcha.csproj", "Directory.Build.targets"):
    p = CARDCHA / rel
    text = read(p)
    if NEW_VERSION not in text:
        if OLD_VERSION not in text:
            raise RuntimeError(f"missing version anchor in {rel}")
        write(p, text.replace(OLD_VERSION, NEW_VERSION))

# -----------------------------------------------------------------------------
# Rebuild Airship maps as physical Cardcha rooms instead of empty vanilla shells.
# -----------------------------------------------------------------------------
deck_blocked = set()
# Helm / navigation dais.
for y in (4, 5):
    for x in range(10, 15):
        deck_blocked.add((x, y))
# Left and right bridge consoles.
for y in (6, 7):
    for x in range(3, 7):
        deck_blocked.add((x, y))
    for x in range(17, 21):
        deck_blocked.add((x, y))
# Four upgrade machines. Footprints intentionally exceed the animated 112px sprites so the
# post-world glow can never overlap a walkable player tile.
for y in (8, 9):
    for x in range(4, 7):
        deck_blocked.add((x, y))
    for x in range(17, 20):
        deck_blocked.add((x, y))
for y in (9, 10):
    for x in range(7, 10):
        deck_blocked.add((x, y))
    for x in range(14, 17):
        deck_blocked.add((x, y))
# ChaCha resonance alcove.
for y in (4, 5, 6):
    for x in range(18, 21):
        deck_blocked.add((x, y))

write(ASSETS / "airship_deck.tmx", build_backdrop_tmx(
    24, 14, "airship_deck_stardew.png",
    "airship-bridge|navigation-core|upgrade-stations|chacha-resonance|arcane-dock-return",
    "stardew-airship-bridge|warm-wood-brass|panoramic-canopy|physical-machinery",
    deck_blocked,
    {11, 12, 13},
))

dock_blocked = set()
# Route/status console at left.
for y in (5, 6, 7):
    for x in range(7, 12):
        dock_blocked.add((x, y))
# Boarding aperture: physical side posts, center lane remains walkable.
for y in range(4, 9):
    for x in (21, 22, 26, 27):
        dock_blocked.add((x, y))
# Service cabinet / mechanical wall mass.
for y in range(8, 13):
    for x in (3, 4, 25, 26):
        dock_blocked.add((x, y))

write(ASSETS / "sky_dock_interior.tmx", build_backdrop_tmx(
    30, 18, "sky_dock_stardew.png",
    "arcane-dock|route-console|boarding-bay|forest-return",
    "stardew-airship-dock|service-platform|physical-console|boarding-aperture",
    dock_blocked,
    {14, 15, 16},
))

# -----------------------------------------------------------------------------
# AirshipFoundationService: remove pickup furniture, widen visible-machine interaction, and let
# a farmer draw Harmony patch own gate depth instead of RenderedWorld painting over the player.
# -----------------------------------------------------------------------------
service_path = CARDCHA / "Services" / "AirshipFoundationService.cs"
service = read(service_path)
service = service.replace('private const string InteriorDecorVersion = "alpha.28.0.4.14.4.5.12";',
                          'private const string InteriorDecorVersion = "alpha.28.0.4.14.4.5.12.5";')
service = service.replace(
    '        if ((this.Save.Data.AirshipUnlocked || this.TestGateAccessActive) && IsSkyDockLocation(location))\n            this.DrawSkyDock(e.SpriteBatch, this.ResolveSkyDockTile());\n\n',
    '',
)
service = service.replace('if (Touches(action, helm) || PlayerIsNear(helm))',
                          'if (Touches(action, helm) || PlayerIsNear(helm, 160f))', 1)
service = service.replace('if (!Touches(action, tile) && !PlayerIsNear(tile))',
                          'if (!Touches(action, tile) && !PlayerIsNear(tile, 176f))', 1)
service = service.replace('if (Touches(interiorAction, route) || PlayerIsNear(route))',
                          'if (Touches(interiorAction, route) || PlayerIsNear(route, 176f))', 1)
service = service.replace('if (Touches(interiorAction, bay) || PlayerIsNear(bay))',
                          'if (Touches(interiorAction, bay) || PlayerIsNear(bay, 176f))', 1)

# Exterior return/test landing must never spawn the farmer inside the arch art.
service = service.replace('Point landing = FindClearTileNear(forest, new Point(dock.X, dock.Y + 3));',
                          'Point landing = ResolveForestGateLandingTile(forest, dock);', 1)
service = service.replace('Point landing = FindClearTileNear(forest, new Point(dock.X, dock.Y + 2));',
                          'Point landing = ResolveForestGateLandingTile(forest, dock);', 1)

# Pickup/movable furniture is banned from Cardcha-owned Airship rooms. The map/backdrop and
# runtime station atlas now carry all visual identity; this also removes the 750g small crystal.
furniture = r'''    private void EnsureDeckVanillaFurniture(GameLocation deck)
    {
        if (ReferenceEquals(this.DeckDecorAppliedLocation, deck))
            return;
        this.DeckDecorAppliedLocation = deck;
        ClearInteriorDecor(deck);
        deck.modData[InteriorDecorMarkerKey] = InteriorDecorVersion + "-physical-bridge-no-pickups";
    }

    private void EnsureSkyDockVanillaFurniture(GameLocation dock)
    {
        if (ReferenceEquals(this.SkyDockDecorAppliedLocation, dock))
            return;
        this.SkyDockDecorAppliedLocation = dock;
        ClearInteriorDecor(dock);
        dock.modData[InteriorDecorMarkerKey] = InteriorDecorVersion + "-physical-dock-no-pickups";
    }'''
service = replace_region(
    service,
    "    private void EnsureDeckVanillaFurniture(GameLocation deck)",
    "    private static void ClearInteriorDecor(GameLocation location)",
    furniture,
)

# Add gate-depth hooks + guaranteed exterior landing helper before the location helpers.
gate_helpers = r'''    internal bool CanDrawForestGateForLocalPlayer()
    {
        if (!Context.IsWorldReady || Game1.currentLocation is null)
            return false;
        return (this.Save.Data.AirshipUnlocked || this.TestGateAccessActive)
            && IsSkyDockLocation(Game1.currentLocation);
    }

    internal bool ShouldDrawForestGateAfterPlayer(Farmer farmer)
    {
        if (!this.CanDrawForestGateForLocalPlayer() || farmer is null)
            return false;
        Point dock = this.ResolveSkyDockTile();
        int playerTileY = (int)(farmer.Position.Y / 64f);
        // Above/behind the threshold: arch is foreground. At or below the threshold: farmer is
        // physically in front, so the gate must be queued before the farmer draw call.
        return playerTileY <= dock.Y + 1;
    }

    internal void DrawForestGateAtFarmerDepth(SpriteBatch batch)
    {
        if (!this.CanDrawForestGateForLocalPlayer())
            return;
        this.DrawSkyDock(batch, this.ResolveSkyDockTile());
    }

    private static Point ResolveForestGateLandingTile(GameLocation forest, Point dock)
    {
        Point[] candidates =
        {
            new(dock.X, dock.Y + 4), new(dock.X - 1, dock.Y + 4), new(dock.X + 1, dock.Y + 4),
            new(dock.X, dock.Y + 3), new(dock.X - 1, dock.Y + 3), new(dock.X + 1, dock.Y + 3),
            new(dock.X - 2, dock.Y + 3), new(dock.X + 2, dock.Y + 3),
        };
        foreach (Point p in candidates)
        {
            try
            {
                Vector2 v = new(p.X, p.Y);
                if (!forest.IsTileBlockedBy(v)
                    && !forest.Objects.ContainsKey(v)
                    && !forest.terrainFeatures.ContainsKey(v))
                    return p;
            }
            catch { }
        }
        return FindClearTileNear(forest, new Point(dock.X, dock.Y + 4));
    }'''
insert_token = "    private static bool IsSkyDockLocation(GameLocation? location)"
idx = service.index(insert_token)
service = service[:idx] + gate_helpers + "\n\n" + service[idx:]
write(service_path, service)

# -----------------------------------------------------------------------------
# Renderer: only dynamic machinery/light accents remain post-world. Room architecture lives in
# map Back/Buildings layers and has collision, so no giant rectangle can paint over the farmer.
# -----------------------------------------------------------------------------
renderer_path = CARDCHA / "Services" / "AirshipInteriorStardewRenderer.cs"
renderer = read(renderer_path)
# Remove 0647D wall-panel calls; the restored Cardcha room architecture replaces them.
renderer = re.sub(r'\s*DrawBridgeWallPanel\(batch, new Point\(4, 4\).*?;\n', '\n', renderer)
renderer = re.sub(r'\s*DrawBridgeWallPanel\(batch, new Point\(19, 4\).*?;\n', '\n', renderer)
renderer = re.sub(r'\s*DrawDockWallPanel\(batch, new Point\(6, 4\).*?;\n', '\n', renderer)
renderer = re.sub(r'\s*DrawDockWallPanel\(batch, new Point\(20, 4\).*?;\n', '\n', renderer)
renderer = re.sub(r'\s*DrawDockBeacon\(batch, new Point\(15, 4\), phase\);\n', '\n', renderer)
# Bigger, readable upgrade machines. Collision footprint is deliberately larger than this sprite.
renderer = renderer.replace('Rectangle shadow = new((int)center.X - 48, (int)center.Y + 26, 96, 14);',
                            'Rectangle shadow = new((int)center.X - 56, (int)center.Y + 31, 112, 15);')
renderer = renderer.replace('Rectangle dst = new((int)center.X - 48, (int)center.Y - 61, 96, 96);',
                            'Rectangle dst = new((int)center.X - 56, (int)center.Y - 76, 112, 112);')
write(renderer_path, renderer)

# -----------------------------------------------------------------------------
# Gate depth patch: draw the procedural gate immediately around the LOCAL farmer draw call.
# -----------------------------------------------------------------------------
patch_path = CARDCHA / "Patches" / "AirshipGateDepthPatch.cs"
write(patch_path, r'''using HarmonyLib;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewValley;
using Cardcha.Services;

namespace Cardcha.Patches;

internal static class AirshipGateDepthPatch
{
    private static AirshipFoundationService? Service;

    internal static void Apply(Harmony harmony, AirshipFoundationService service, IMonitor monitor)
    {
        Service = service;
        var draw = AccessTools.Method(typeof(Farmer), "draw", new[] { typeof(SpriteBatch) });
        if (draw is null)
        {
            monitor.Log("Airship gate depth patch couldn't find Farmer.draw(SpriteBatch); gate rendering was disabled instead of falling back to player-covering RenderedWorld drawing.", LogLevel.Error);
            return;
        }
        harmony.Patch(
            draw,
            prefix: new HarmonyMethod(typeof(AirshipGateDepthPatch), nameof(BeforeFarmerDraw)),
            postfix: new HarmonyMethod(typeof(AirshipGateDepthPatch), nameof(AfterFarmerDraw))
        );
    }

    private static void BeforeFarmerDraw(Farmer __instance, SpriteBatch b)
    {
        AirshipFoundationService? service = Service;
        if (service is null || __instance != Game1.player || !service.CanDrawForestGateForLocalPlayer())
            return;
        if (!service.ShouldDrawForestGateAfterPlayer(__instance))
            service.DrawForestGateAtFarmerDepth(b);
    }

    private static void AfterFarmerDraw(Farmer __instance, SpriteBatch b)
    {
        AirshipFoundationService? service = Service;
        if (service is null || __instance != Game1.player || !service.CanDrawForestGateForLocalPlayer())
            return;
        if (service.ShouldDrawForestGateAfterPlayer(__instance))
            service.DrawForestGateAtFarmerDepth(b);
    }
}
''')

# Explicit patch registration in ModEntry, using the same main Harmony instance as other patches.
mod_path = CARDCHA / "ModEntry.cs"
mod = read(mod_path)
needle = "        MimiProfileMenuPatch.Apply(harmony);"
call = "        MimiProfileMenuPatch.Apply(harmony);\n        AirshipGateDepthPatch.Apply(harmony, this.Airship, this.Monitor);"
if "AirshipGateDepthPatch.Apply" not in mod:
    if needle not in mod:
        raise RuntimeError("ModEntry patch anchor missing")
    mod = mod.replace(needle, call, 1)
write(mod_path, mod)

print(f"Prepared Cardcha {NEW_VERSION}: restored physical Airship/Sky Dock architecture, collision-backed machines, no pickup props, and farmer-aware gate depth.")
