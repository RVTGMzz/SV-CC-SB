from pathlib import Path
import hashlib
import json

ROOT = Path('src/Cardcha')
BASE_VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.13'
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.14'
WALK_SHA256 = '04ff1cbf031c2be0a21f114b8f8eb6f8850bb800eeabd4c27df036d7b23d4fb7'
AIRSHIP_SHA256 = '1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132'

# Version metadata only. Do not touch gameplay/save/progression data.
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

# Binary guardrails. This hotfix must not repaint/resize the approved sprites.
walk = ROOT / 'assets/mimi_walk.png'
walk_hash = hashlib.sha256(walk.read_bytes()).hexdigest()
if walk_hash != WALK_SHA256:
    raise RuntimeError(f'mimi_walk.png drifted: {walk_hash}')

airship = ROOT / 'assets/airship_visual.png'
airship_hash = hashlib.sha256(airship.read_bytes()).hexdigest()
if airship_hash != AIRSHIP_SHA256:
    raise RuntimeError(f'airship_visual.png drifted: {airship_hash}')

# MiMi Gift Log / Profile: keep canonical 32x48 animation frames and backing sheet,
# but halve only the final AnimatedSprite draw-scale while MiMi's ProfileMenu is active.
# This is code-only scaling: no new animation, no asset mutation, no world-sprite impact.
profile_path = ROOT / 'Patches/MimiProfileMenuPatch.cs'
profile_path.write_text(r'''using Cardcha.Services;
using HarmonyLib;
using StardewValley;
using StardewValley.Menus;
using System.Reflection;

namespace Cardcha.Patches;

internal static class MimiProfileMenuPatch
{
    private const float MimiProfileScaleMultiplier = 0.5f;
    private static readonly FieldInfo? AnimatedSpriteField = AccessTools.Field(typeof(ProfileMenu), "_animatedSprite");
    private static bool MimiProfileActive;

    public static void Apply(Harmony harmony)
    {
        MethodInfo? target = AccessTools.Method(
            typeof(ProfileMenu),
            "_SetCharacter",
            new[] { typeof(SocialPage.SocialEntry) }
        );

        if (target is null || AnimatedSpriteField is null)
        {
            ModEntry.StaticMonitor?.Log("Could not install MiMi ProfileMenu sprite-size patch.", StardewModdingAPI.LogLevel.Warn);
            return;
        }

        harmony.Patch(
            target,
            postfix: new HarmonyMethod(typeof(MimiProfileMenuPatch), nameof(Postfix))
        );

        int scaledDrawOverloads = 0;
        foreach (MethodInfo drawMethod in typeof(AnimatedSprite)
                     .GetMethods(BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)
                     .Where(method => string.Equals(method.Name, "draw", StringComparison.OrdinalIgnoreCase)
                         && method.GetParameters().Any(parameter => parameter.ParameterType == typeof(float)
                             && string.Equals(parameter.Name, "scale", StringComparison.OrdinalIgnoreCase))))
        {
            harmony.Patch(
                drawMethod,
                prefix: new HarmonyMethod(typeof(MimiProfileMenuPatch), nameof(ScaleDrawPrefix))
            );
            scaledDrawOverloads++;
        }

        if (scaledDrawOverloads == 0)
        {
            ModEntry.StaticMonitor?.Log(
                "MiMi ProfileMenu could not find an AnimatedSprite draw overload with a scale argument; vanilla scale will be used safely.",
                StardewModdingAPI.LogLevel.Warn
            );
        }
    }

    private static void Postfix(ProfileMenu __instance, SocialPage.SocialEntry entry)
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

    private static void ScaleDrawPrefix(AnimatedSprite __instance, MethodBase __originalMethod, object[] __args)
    {
        if (!MimiProfileActive
            || Game1.activeClickableMenu is not ProfileMenu profile
            || !ReferenceEquals(AnimatedSpriteField?.GetValue(profile), __instance))
        {
            return;
        }

        ParameterInfo[] parameters = __originalMethod.GetParameters();
        for (int i = 0; i < parameters.Length && i < __args.Length; i++)
        {
            ParameterInfo parameter = parameters[i];
            if (parameter.ParameterType != typeof(float)
                || !string.Equals(parameter.Name, "scale", StringComparison.OrdinalIgnoreCase)
                || __args[i] is not float scale)
            {
                continue;
            }

            __args[i] = scale * MimiProfileScaleMultiplier;
            return;
        }
    }
}
''', encoding='utf-8')

# WizardHouse stair: the 0648G per-rung omission made the stair sprite appear sliced
# wherever the farmer crossed it. Preserve the exact fixed tile (8,15), but switch
# visibility atomically: draw the whole 16x64 stair, or hide the whole stair for the
# frame when a visible character overlaps it. No partial/rung cutting remains.
visual_path = ROOT / 'Services/MimiAtticVisualService.cs'
visual = visual_path.read_text(encoding='utf-8')
start = visual.index('    private void DrawStairMarker(SpriteBatch batch, GameLocation location, Point tile)')
end = visual.index('    private static AtticLayout GetLayout', start)
replacement = '''    private void DrawStairMarker(SpriteBatch batch, GameLocation location, Point tile)\n    {\n        try\n        {\n            Texture2D staircase = this.Helper.ModContent.Load<Texture2D>(StairSpritePath);\n            Vector2 world = new(tile.X * 64f, (tile.Y - 4) * 64f);\n            Rectangle worldRect = new((int)world.X, (int)world.Y, 64, 256);\n\n            // RenderedWorld occurs after Stardew draws characters, so a custom stair cannot be\n            // truly depth-sorted behind them here. 0648G hid individual 64px rungs, which made\n            // the ladder visibly slice itself around the farmer. Keep visibility atomic instead:\n            // while a character overlaps the stair, hide the complete cosmetic stair for that\n            // frame; once clear, render the complete stair again. The warp/collision is untouched.\n            if (IntersectsVisibleCharacter(location, worldRect))\n                return;\n\n            Vector2 screen = Game1.GlobalToLocal(Game1.viewport, world);\n            Rectangle source = new(0, 0, 16, 64);\n            batch.Draw(staircase, screen, source, Color.White, 0f, Vector2.Zero, 4f, SpriteEffects.None, 0.01f);\n        }\n        catch\n        {\n            // The warp remains functional if the cosmetic marker cannot be loaded.\n        }\n    }\n\n    private static bool IntersectsVisibleCharacter(GameLocation location, Rectangle stairBounds)\n    {\n        if (Game1.player.currentLocation == location\n            && stairBounds.Intersects(GetCharacterVisualBounds(Game1.player)))\n        {\n            return true;\n        }\n\n        foreach (NPC npc in location.characters)\n        {\n            if (npc.isInvisible.Value)\n                continue;\n            if (stairBounds.Intersects(GetCharacterVisualBounds(npc)))\n                return true;\n        }\n\n        return false;\n    }\n\n    private static Rectangle GetCharacterVisualBounds(Character character)\n    {\n        int x = (int)character.Position.X - 8;\n        int y = (int)character.Position.Y - 96;\n        return new Rectangle(x, y, 80, 160);\n    }\n\n'''
visual = visual[:start] + replacement + visual[end:]
visual_path.write_text(visual, encoding='utf-8')

# Guard that the screenshot-approved stair coordinate itself was not moved.
home = (ROOT / 'Services/MimiHomeService.cs').read_text(encoding='utf-8')
a = home.index('internal static Point ResolvePreferredWizardStairTile')
b = home.index('private static Point ResolveWizardLandingTile', a)
if 'return new Point(8, 15);' not in home[a:b]:
    raise RuntimeError('Wizard stair tile (8,15) drifted')

print(json.dumps({
    'version': VERSION,
    'mimiGiftProfileScaleMultiplier': 0.5,
    'profileFrameSize': [32, 48],
    'profileAsset': 'assets/mimi_walk.png',
    'wizardStairTile': [8, 15],
    'stairOcclusion': 'whole-sprite visibility, no per-rung slicing',
    'mimiWalkSha256': WALK_SHA256,
    'airshipVisualSha256': AIRSHIP_SHA256,
}, indent=2))
