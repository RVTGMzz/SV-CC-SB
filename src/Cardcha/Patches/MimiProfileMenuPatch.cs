using Cardcha.Services;
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
