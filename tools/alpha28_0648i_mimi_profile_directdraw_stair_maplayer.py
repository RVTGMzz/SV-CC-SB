from pathlib import Path
import hashlib
import json

ROOT = Path('src/Cardcha')
BASE_VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.14'
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.15'
WALK_SHA256 = '04ff1cbf031c2be0a21f114b8f8eb6f8850bb800eeabd4c27df036d7b23d4fb7'
AIRSHIP_SHA256 = '1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132'

# Version metadata only; gameplay/save/card canon stays locked.
manifest = ROOT / 'manifest.json'
data = json.loads(manifest.read_text(encoding='utf-8-sig'))
if data['Version'] != BASE_VERSION:
    raise RuntimeError(f'Expected base {BASE_VERSION}, got {data["Version"]}')
data['Version'] = VERSION
manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

for rel in ['Cardcha.csproj', 'Directory.Build.targets']:
    p = ROOT / rel
    text = p.read_text(encoding='utf-8')
    if BASE_VERSION not in text:
        raise RuntimeError(f'{BASE_VERSION} missing from {rel}')
    p.write_text(text.replace(BASE_VERSION, VERSION), encoding='utf-8')

# Approved binary assets must remain byte-identical.
walk = ROOT / 'assets/mimi_walk.png'
if hashlib.sha256(walk.read_bytes()).hexdigest() != WALK_SHA256:
    raise RuntimeError('mimi_walk.png drifted')
airship = ROOT / 'assets/airship_visual.png'
if hashlib.sha256(airship.read_bytes()).hexdigest() != AIRSHIP_SHA256:
    raise RuntimeError('airship_visual.png drifted')

# ---------------------------------------------------------------------------
# MiMi Gift Log/Profile root-cause fix.
# 0648H patched AnimatedSprite.draw overloads which expose a `scale` argument.
# ProfileMenu actually calls the three-argument draw(SpriteBatch, Vector2, float),
# whose implementation hardcodes scale=4. Patch that exact overload and replace
# ONLY MiMi's menu sprite draw with scale=2 (exactly 50%), centered in the same
# vanilla footprint. No asset resize, no new animation, no world-sprite impact.
# ---------------------------------------------------------------------------
profile_path = ROOT / 'Patches/MimiProfileMenuPatch.cs'
profile_path.write_text(r'''using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewValley;
using StardewValley.Menus;
using System.Reflection;

namespace Cardcha.Patches;

internal static class MimiProfileMenuPatch
{
    private const float VanillaProfileSpriteScale = 4f;
    private const float MimiProfileSpriteScale = 2f;

    private static readonly FieldInfo? AnimatedSpriteField = AccessTools.Field(typeof(ProfileMenu), "_animatedSprite");
    private static bool MimiProfileActive;

    public static void Apply(Harmony harmony)
    {
        MethodInfo? setCharacter = AccessTools.Method(
            typeof(ProfileMenu),
            "_SetCharacter",
            new[] { typeof(SocialPage.SocialEntry) }
        );

        MethodInfo? threeArgDraw = AccessTools.Method(
            typeof(AnimatedSprite),
            "draw",
            new[] { typeof(SpriteBatch), typeof(Vector2), typeof(float) }
        );

        if (setCharacter is null || AnimatedSpriteField is null)
        {
            ModEntry.StaticMonitor?.Log(
                "Could not install MiMi ProfileMenu character hook.",
                StardewModdingAPI.LogLevel.Warn
            );
            return;
        }

        harmony.Patch(
            setCharacter,
            postfix: new HarmonyMethod(typeof(MimiProfileMenuPatch), nameof(SetCharacterPostfix))
        );

        if (threeArgDraw is null)
        {
            ModEntry.StaticMonitor?.Log(
                "Could not install MiMi ProfileMenu direct-draw scale hook; the exact AnimatedSprite three-argument draw overload was not found.",
                StardewModdingAPI.LogLevel.Warn
            );
            return;
        }

        harmony.Patch(
            threeArgDraw,
            prefix: new HarmonyMethod(typeof(MimiProfileMenuPatch), nameof(ThreeArgDrawPrefix))
        );
    }

    private static void SetCharacterPostfix(ProfileMenu __instance, SocialPage.SocialEntry entry)
    {
        bool isMimi = entry.Character is NPC npc
            && string.Equals(npc.Name, WorldActorService.MimiNpcId, StringComparison.OrdinalIgnoreCase);

        MimiProfileActive = isMimi;
        if (!isMimi)
            return;

        try
        {
            AnimatedSprite sprite = new(WorldActorService.MimiProfileCharacterAsset, 0, 32, 48);
            sprite.faceDirection(2);
            AnimatedSpriteField?.SetValue(__instance, sprite);
        }
        catch (Exception ex)
        {
            ModEntry.StaticMonitor?.Log(
                $"MiMi ProfileMenu sprite substitution failed safely: {ex.Message}",
                StardewModdingAPI.LogLevel.Trace
            );
        }
    }

    /// <summary>
    /// ProfileMenu uses AnimatedSprite.draw(SpriteBatch, Vector2, float). That overload hardcodes
    /// a 4x sprite scale internally, so 0648H's scale-parameter hook could never affect it.
    /// Intercept exactly that call for MiMi's active ProfileMenu sprite, draw at 2x, then skip the
    /// vanilla 4x draw. The center offset keeps the half-size sprite visually centered in the same
    /// character frame instead of shrinking toward the top-left corner.
    /// </summary>
    private static bool ThreeArgDrawPrefix(AnimatedSprite __instance, object[] __args)
    {
        if (!MimiProfileActive
            || Game1.activeClickableMenu is not ProfileMenu profile
            || !ReferenceEquals(AnimatedSpriteField?.GetValue(profile), __instance))
        {
            return true;
        }

        if (__args.Length < 3
            || __args[0] is not SpriteBatch batch
            || __args[1] is not Vector2 screenPosition
            || __args[2] is not float layerDepth)
        {
            return true;
        }

        Texture2D texture = __instance.Texture;
        if (texture is null)
            return false;

        Rectangle source = __instance.SourceRect;
        float centerOffsetX = source.Width * (VanillaProfileSpriteScale - MimiProfileSpriteScale) / 2f;
        float centerOffsetY = source.Height * (VanillaProfileSpriteScale - MimiProfileSpriteScale) / 2f;
        Vector2 centeredPosition = screenPosition + new Vector2(centerOffsetX, centerOffsetY);

        SpriteEffects effects = SpriteEffects.None;
        var animation = __instance.CurrentAnimation;
        if (animation is not null
            && __instance.currentAnimationIndex >= 0
            && __instance.currentAnimationIndex < animation.Count
            && animation[__instance.currentAnimationIndex].flip)
        {
            effects = SpriteEffects.FlipHorizontally;
        }

        batch.Draw(
            texture,
            centeredPosition,
            source,
            Color.White,
            0f,
            Vector2.Zero,
            MimiProfileSpriteScale,
            effects,
            layerDepth
        );

        return false;
    }
}
''', encoding='utf-8')

# ---------------------------------------------------------------------------
# WizardHouse stair root-cause fix.
# RenderedWorld happens after characters, so any custom SpriteBatch draw there will
# always be on top of the farmer. 0648G/0648H tried to hide parts/all of the stair,
# which produced the visible slicing/disappearing reports. Stop custom-drawing it.
# Instead install the 16x64 stair as four real 16x16 tiles on the Buildings layer.
# Stardew then draws Buildings before characters, and Passable=T preserves walking.
# ---------------------------------------------------------------------------
visual_path = ROOT / 'Services/MimiAtticVisualService.cs'
visual = visual_path.read_text(encoding='utf-8')

if 'using xTile;' not in visual:
    visual = visual.replace(
        'using StardewValley.Objects;\n',
        'using StardewValley.Objects;\nusing xTile;\nusing xTile.Tiles;\n'
    )

old_field = '    private GameLocation? DecorAppliedLocation;\n'
new_field = '    private GameLocation? DecorAppliedLocation;\n    private xTile.Map? WizardStairAppliedMap;\n'
if old_field not in visual:
    raise RuntimeError('DecorAppliedLocation field anchor not found')
visual = visual.replace(old_field, new_field, 1)

old_draw_call = '            this.DrawStairMarker(e.SpriteBatch, location, stair);'
new_draw_call = '            this.EnsureWizardStairMapTiles(location, stair);'
if old_draw_call not in visual:
    raise RuntimeError('0648H DrawStairMarker call not found')
visual = visual.replace(old_draw_call, new_draw_call, 1)

start = visual.index('    private static void PrepareWizardStairArea(GameLocation location, Point tile)')
end = visual.index('    private static AtticLayout GetLayout', start)
replacement = '''    private void EnsureWizardStairMapTiles(GameLocation location, Point tile)\n    {\n        try\n        {\n            xTile.Map? map = location.Map;\n            if (map is null || ReferenceEquals(this.WizardStairAppliedMap, map))\n                return;\n\n            var buildings = map.GetLayer("Buildings");\n            if (buildings is null)\n                return;\n\n            const string tileSheetId = "z_cardcha_mimi_attic_stairs";\n            TileSheet? stairSheet = map.GetTileSheet(tileSheetId);\n            if (stairSheet is null)\n            {\n                string imageSource = this.Helper.ModContent.GetInternalAssetName(StairSpritePath).Name;\n                stairSheet = new TileSheet(\n                    tileSheetId,\n                    map,\n                    imageSource,\n                    new xTile.Dimensions.Size(1, 4),\n                    new xTile.Dimensions.Size(16, 16)\n                );\n                map.AddTileSheet(stairSheet);\n\n                // The WizardHouse map is already live when this runtime-only progression gate\n                // installs the stair, so load the newly added tilesheet into the map display device.\n                map.LoadTileSheets(Game1.mapDisplayDevice);\n            }\n\n            var front = map.GetLayer("Front");\n            int x = tile.X;\n\n            for (int segment = 0; segment < 4; segment++)\n            {\n                int y = tile.Y - 4 + segment;\n                if (x < 0 || y < 0 || x >= buildings.LayerWidth || y >= buildings.LayerHeight)\n                    continue;\n\n                // Clear only the same foreground column the old cosmetic stair occupied so no\n                // vanilla Front tile can paint over the ladder. Back/wall art remains untouched.\n                if (front is not null\n                    && x < front.LayerWidth\n                    && y < front.LayerHeight)\n                {\n                    front.Tiles[x, y] = null;\n                }\n\n                StaticTile stairTile = new(buildings, stairSheet, BlendMode.Alpha, segment);\n                stairTile.Properties["Passable"] = "T";\n                buildings.Tiles[x, y] = stairTile;\n            }\n\n            // Track the actual map object, not location.modData: map tiles themselves are runtime\n            // content and must be reinstalled if another mod reloads/replaces the WizardHouse map.\n            this.WizardStairAppliedMap = map;\n        }\n        catch (Exception ex)\n        {\n            ModEntry.StaticMonitor?.Log(\n                $"WizardHouse MiMi stair map-layer install failed safely: {ex.Message}",\n                StardewModdingAPI.LogLevel.Warn\n            );\n        }\n    }\n\n'''
visual = visual[:start] + replacement + visual[end:]
visual_path.write_text(visual, encoding='utf-8')

# Coordinate/canon guards.
home = (ROOT / 'Services/MimiHomeService.cs').read_text(encoding='utf-8')
a = home.index('internal static Point ResolvePreferredWizardStairTile')
b = home.index('private static Point ResolveWizardLandingTile', a)
if 'return new Point(8, 15);' not in home[a:b]:
    raise RuntimeError('Wizard stair tile (8,15) drifted')

print(json.dumps({
    'version': VERSION,
    'mimiProfileDrawHook': 'AnimatedSprite.draw(SpriteBatch, Vector2, float)',
    'mimiProfileVanillaScale': 4.0,
    'mimiProfileScale': 2.0,
    'mimiProfileRelativeScale': 0.5,
    'wizardStairTile': [8, 15],
    'wizardStairRendering': '4 real Buildings-layer tiles, Passable=T; no RenderedWorld sprite draw',
    'mimiWalkSha256': WALK_SHA256,
    'airshipVisualSha256': AIRSHIP_SHA256,
}, indent=2))
