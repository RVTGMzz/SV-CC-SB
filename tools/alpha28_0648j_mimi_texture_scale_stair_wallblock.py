from pathlib import Path
import hashlib
import json

ROOT = Path('src/Cardcha')
BASE_VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.15'
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.16'
WALK_SHA256 = '04ff1cbf031c2be0a21f114b8f8eb6f8850bb800eeabd4c27df036d7b23d4fb7'
AIRSHIP_SHA256 = '1821ee869759a924f7ff2b6821aaeb64b80a000d84c46f207a578d3a1e771132'

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

if hashlib.sha256((ROOT / 'assets/mimi_walk.png').read_bytes()).hexdigest() != WALK_SHA256:
    raise RuntimeError('mimi_walk.png drifted')
if hashlib.sha256((ROOT / 'assets/airship_visual.png').read_bytes()).hexdigest() != AIRSHIP_SHA256:
    raise RuntimeError('airship_visual.png drifted')

profile = ROOT / 'Patches/MimiProfileMenuPatch.cs'
profile.write_text(r'''using Cardcha.Services;
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

        if (setCharacter is not null && AnimatedSpriteField is not null)
        {
            harmony.Patch(
                setCharacter,
                postfix: new HarmonyMethod(typeof(MimiProfileMenuPatch), nameof(SetCharacterPostfix))
            );
        }
        else
        {
            ModEntry.StaticMonitor?.Log(
                "MiMi ProfileMenu sprite substitution hook was not found; texture-owned scale hook remains active.",
                StardewModdingAPI.LogLevel.Warn
            );
        }

        if (threeArgDraw is null)
        {
            ModEntry.StaticMonitor?.Log(
                "Could not install MiMi ProfileMenu 50% texture-owned draw hook.",
                StardewModdingAPI.LogLevel.Error
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
        if (entry.Character is not NPC npc || !IsMimiName(npc.Name))
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

    private static bool ThreeArgDrawPrefix(AnimatedSprite __instance, SpriteBatch b, Vector2 screenPosition, float layerDepth)
    {
        if (!IsMimiProfileTexture(__instance))
            return true;

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

        b.Draw(
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

    private static bool IsMimiProfileTexture(AnimatedSprite sprite)
    {
        string? loaded = sprite.loadedTexture;
        string? requested = sprite.textureName.Value;
        return IsMimiTextureName(loaded) || IsMimiTextureName(requested);
    }

    private static bool IsMimiTextureName(string? value)
        => string.Equals(value, WorldActorService.MimiProfileCharacterAsset, StringComparison.OrdinalIgnoreCase)
           || string.Equals(value, WorldActorService.MimiCharacterAsset, StringComparison.OrdinalIgnoreCase);

    private static bool IsMimiName(string? value)
        => string.Equals(value, WorldActorService.MimiNpcId, StringComparison.OrdinalIgnoreCase)
           || string.Equals(value, "MiMi", StringComparison.OrdinalIgnoreCase);
}
''', encoding='utf-8')

home_path = ROOT / 'Services/MimiHomeService.cs'
home = home_path.read_text(encoding='utf-8')
old = 'return new Point(8, 15);'
new = 'return new Point(15, 15);'
if old not in home:
    raise RuntimeError('0648I Wizard stair coordinate not found')
home = home.replace(old, new, 1)
home_path.write_text(home, encoding='utf-8')

visual_path = ROOT / 'Services/MimiAtticVisualService.cs'
visual = visual_path.read_text(encoding='utf-8')
passable = '                stairTile.Properties["Passable"] = "T";\n'
if passable not in visual:
    raise RuntimeError('0648I Passable=T stair property not found')
visual = visual.replace(passable, '', 1)
visual = visual.replace(
    '// vanilla Front tile can paint over the ladder. Back/wall art remains untouched.',
    '// vanilla Front tile can paint over the ladder. The Buildings tile itself stays solid.'
)
visual_path.write_text(visual, encoding='utf-8')

print(json.dumps({
    'version': VERSION,
    'mimiProfileScale': 2.0,
    'mimiProfileRelativeToVanilla': 0.5,
    'mimiScaleDetection': ['Characters/Ronvotri.Cardcha_MiMi_Profile', 'Characters/Ronvotri.Cardcha_MiMi'],
    'wizardStairTile': [15, 15],
    'wizardStairCollision': 'solid Buildings tiles; no Passable=T',
    'mimiWalkSha256': WALK_SHA256,
    'airshipVisualSha256': AIRSHIP_SHA256,
}, indent=2))
