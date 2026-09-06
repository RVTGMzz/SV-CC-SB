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
