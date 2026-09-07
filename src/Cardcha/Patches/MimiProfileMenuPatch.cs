using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewValley;
using StardewValley.Menus;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>
/// Keeps MiMi's Gift Log/Profile preview inside the same visual envelope as vanilla NPCs.
/// 0654 adds a caller-context guard around ProfileMenu.draw so the scale correction no longer
/// depends on AnimatedSprite.loadedTexture string identity, which proved unreliable in-game.
/// </summary>
internal static class MimiProfileMenuPatch
{
    private const float VanillaProfileSpriteScale = 4f;
    private const float MimiProfileSpriteScale = 2f;
    private const float MimiTargetRenderedWidth = 64f;
    private const float MimiTargetRenderedHeight = 112f;
    private static readonly FieldInfo? AnimatedSpriteField = AccessTools.Field(typeof(ProfileMenu), "_animatedSprite");

    [ThreadStatic]
    private static bool DrawingMimiProfile;

    private static int ProfileGuardHits;
    private static int ScaledDrawHits;

    public static void Apply(Harmony harmony)
    {
        MethodInfo? setCharacter = AccessTools.Method(
            typeof(ProfileMenu),
            "_SetCharacter",
            new[] { typeof(SocialPage.SocialEntry) }
        );
        MethodInfo? profileDraw = AccessTools.Method(
            typeof(ProfileMenu),
            nameof(ProfileMenu.draw),
            new[] { typeof(SpriteBatch) }
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
                "MiMi ProfileMenu sprite substitution hook was not found; caller-context scale hook remains active.",
                StardewModdingAPI.LogLevel.Warn
            );
        }

        if (profileDraw is not null)
        {
            harmony.Patch(
                profileDraw,
                prefix: new HarmonyMethod(typeof(MimiProfileMenuPatch), nameof(ProfileDrawPrefix)),
                postfix: new HarmonyMethod(typeof(MimiProfileMenuPatch), nameof(ProfileDrawPostfix))
            );
        }
        else
        {
            ModEntry.StaticMonitor?.Log(
                "Could not install MiMi ProfileMenu caller-context guard.",
                StardewModdingAPI.LogLevel.Error
            );
        }

        if (threeArgDraw is null)
        {
            ModEntry.StaticMonitor?.Log(
                "Could not install MiMi ProfileMenu fitted AnimatedSprite draw hook.",
                StardewModdingAPI.LogLevel.Error
            );
            return;
        }

        harmony.Patch(
            threeArgDraw,
            prefix: new HarmonyMethod(typeof(MimiProfileMenuPatch), nameof(ThreeArgDrawPrefix))
        );
    }

    private static void ProfileDrawPrefix(ProfileMenu __instance)
    {
        DrawingMimiProfile = IsMimiCurrent(__instance);
        if (DrawingMimiProfile)
            ProfileGuardHits++;
    }

    private static void ProfileDrawPostfix()
    {
        DrawingMimiProfile = false;
    }

    private static void SetCharacterPostfix(ProfileMenu __instance, SocialPage.SocialEntry entry)
    {
        if (entry.Character is not NPC npc || !IsMimiName(npc.Name))
            return;

        try
        {
            // A dedicated 32x48 profile sprite prevents the world actor's runtime Scale value from
            // leaking into menu presentation. Drawing size itself is still normalized below.
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
        // Primary rule: when ProfileMenu itself says the selected character is MiMi, normalize the
        // one AnimatedSprite portrait draw regardless of how SMAPI normalized its texture name.
        // Texture ownership is retained only as a safe fallback for older menu call paths.
        if (!DrawingMimiProfile && !IsMimiProfileTexture(__instance))
            return true;

        Texture2D texture = __instance.Texture;
        if (texture is null)
            return false;

        Rectangle source = __instance.SourceRect;
        if (source.Width <= 0 || source.Height <= 0)
            return false;

        // Fit to a vanilla-NPC-sized envelope rather than blindly multiplying the custom 32x48
        // frame. For MiMi's canonical 32x48 frame this resolves to 2x: 64x96 rendered pixels.
        float fitScale = Math.Min(
            MimiProfileSpriteScale,
            Math.Min(MimiTargetRenderedWidth / source.Width, MimiTargetRenderedHeight / source.Height)
        );

        // ProfileMenu computes screenPosition as if every NPC were drawn at vanilla 4x. Recenter
        // against that original envelope, both horizontally and vertically, so MiMi is not pinned
        // to the upper-left after being reduced.
        float centerOffsetX = source.Width * (VanillaProfileSpriteScale - fitScale) / 2f;
        float centerOffsetY = source.Height * (VanillaProfileSpriteScale - fitScale) / 2f;
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
            fitScale,
            effects,
            layerDepth
        );
        ScaledDrawHits++;
        return false;
    }

    internal static string Describe()
        => $"MiMiProfileGuardHits={ProfileGuardHits} | ScaledDrawHits={ScaledDrawHits} | Active={DrawingMimiProfile} | Target={MimiTargetRenderedWidth:0}x{MimiTargetRenderedHeight:0} | MaxScale={MimiProfileSpriteScale:0.##}";

    private static bool IsMimiCurrent(ProfileMenu menu)
        => menu.Current?.Character is NPC npc && IsMimiName(npc.Name);

    private static bool IsMimiProfileTexture(AnimatedSprite sprite)
    {
        string? loaded = sprite.loadedTexture;
        string? requested = sprite.textureName.Value;
        return IsMimiTextureName(loaded) || IsMimiTextureName(requested);
    }

    private static bool IsMimiTextureName(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
            return false;

        string normalized = value.Replace('\\', '/').Trim();
        string profile = WorldActorService.MimiProfileCharacterAsset.Replace('\\', '/');
        string world = WorldActorService.MimiCharacterAsset.Replace('\\', '/');
        return normalized.Equals(profile, StringComparison.OrdinalIgnoreCase)
            || normalized.Equals(world, StringComparison.OrdinalIgnoreCase)
            || normalized.EndsWith("/Ronvotri.Cardcha_MiMi_Profile", StringComparison.OrdinalIgnoreCase)
            || normalized.EndsWith("/Ronvotri.Cardcha_MiMi", StringComparison.OrdinalIgnoreCase);
    }

    private static bool IsMimiName(string? value)
        => string.Equals(value, WorldActorService.MimiNpcId, StringComparison.OrdinalIgnoreCase)
           || string.Equals(value, "MiMi", StringComparison.OrdinalIgnoreCase);
}
