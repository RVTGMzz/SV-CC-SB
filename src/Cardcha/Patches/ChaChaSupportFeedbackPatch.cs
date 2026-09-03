using System.Reflection;
using System.Runtime.CompilerServices;
using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace Cardcha.Patches;

/// <summary>
/// .5.6.1.3 readability pass for ChaCha Support Cast.
/// Core probabilities/effects stay untouched. This patch only makes successful casts unmistakable:
/// a short world pulse, the relevant skill icons, a compact combat readout, and a persistent shield
/// badge while Bunny Aegis is active.
/// </summary>
internal static class ChaChaSupportFeedbackPatch
{
    private const int FeedbackDurationMs = 3200;

    private static readonly FieldInfo? LastHealField = AccessTools.Field(typeof(ChaChaSupportCastService), "LastHeal");
    private static readonly FieldInfo? LastStaminaField = AccessTools.Field(typeof(ChaChaSupportCastService), "LastStamina");
    private static readonly FieldInfo? LastVisualShieldField = AccessTools.Field(typeof(ChaChaSupportCastService), "LastVisualShield");
    private static readonly FieldInfo? LastVisualSpiritField = AccessTools.Field(typeof(ChaChaSupportCastService), "LastVisualSpirit");
    private static readonly FieldInfo? LastVisualLuckField = AccessTools.Field(typeof(ChaChaSupportCastService), "LastVisualLuck");

    private static long FeedbackUntilMs;
    private static int LastHeal;
    private static float LastStamina;
    private static bool LastShield;
    private static bool LastSpirit;
    private static bool LastLuck;
    private static int LastShieldPercent;
    private static Texture2D? SkillIcons;
    private static bool SkillIconsFailed;

    [ModuleInitializer]
    internal static void Initialize()
    {
        Harmony harmony = new("Ronvotri.Cardcha.ChaChaSupportFeedback05613");

        var performCast = AccessTools.Method(typeof(ChaChaSupportCastService), "PerformCast");
        var castPostfix = AccessTools.Method(typeof(ChaChaSupportFeedbackPatch), nameof(AfterPerformCast));
        if (performCast is not null && castPostfix is not null)
            harmony.Patch(performCast, postfix: new HarmonyMethod(castPostfix));

        var renderedWorld = AccessTools.Method(typeof(ChaChaSupportCastService), nameof(ChaChaSupportCastService.OnRenderedWorld));
        var worldPostfix = AccessTools.Method(typeof(ChaChaSupportFeedbackPatch), nameof(AfterRenderedWorld));
        if (renderedWorld is not null && worldPostfix is not null)
            harmony.Patch(renderedWorld, postfix: new HarmonyMethod(worldPostfix));
    }

    private static void AfterPerformCast(ChaChaSupportCastService __instance, bool __result)
    {
        if (!__result || !Context.IsWorldReady || Game1.player is null)
            return;

        LastHeal = LastHealField?.GetValue(__instance) is int heal ? heal : 0;
        LastStamina = LastStaminaField?.GetValue(__instance) is float stamina ? stamina : 0f;
        LastShield = LastVisualShieldField?.GetValue(__instance) is bool shield && shield;
        LastSpirit = LastVisualSpiritField?.GetValue(__instance) is bool spirit && spirit;
        LastLuck = LastVisualLuckField?.GetValue(__instance) is bool luck && luck;
        LastShieldPercent = LastShield ? (int)Math.Round(__instance.CurrentShieldReduction * 100d) : 0;
        FeedbackUntilMs = Environment.TickCount64 + FeedbackDurationMs;

        List<string> effects = new();
        effects.Add(LastHeal > 0 ? $"+{LastHeal} HP" : "HP đầy");
        if (LastShield)
            effects.Add($"Khiên {LastShieldPercent}%");
        if (LastSpirit)
            effects.Add($"+{LastStamina:0} STA");
        if (LastLuck)
            effects.Add("+1 Luck");

        Game1.showGlobalMessage("ChaCha ✦ " + string.Join("  •  ", effects));
    }

    private static void AfterRenderedWorld(ChaChaSupportCastService __instance, object? sender, RenderedWorldEventArgs e)
    {
        if (!Context.IsWorldReady || Game1.player is null)
            return;

        Vector2 center = Game1.GlobalToLocal(Game1.viewport, Game1.player.Position + new Vector2(32f, 32f));
        double seconds = Game1.currentGameTime.TotalGameTime.TotalSeconds;

        // Persistent visual badge for Bunny Aegis during its full 20-second lifetime.
        if (__instance.IsShieldActive)
        {
            float pulse = 0.88f + 0.10f * (float)Math.Sin(seconds * 5.2);
            DrawRing(e.SpriteBatch, center, 42f + pulse * 4f, new Color(113, 205, 255) * 0.58f, 3f);
            DrawRing(e.SpriteBatch, center, 34f + pulse * 2f, new Color(245, 164, 239) * 0.34f, 2f);
            DrawModuleIcon(e.SpriteBatch, 1, center + new Vector2(-25f, -76f), 30, 0.88f);
        }

        long now = Environment.TickCount64;
        if (now >= FeedbackUntilMs)
            return;

        float remaining = Math.Clamp((FeedbackUntilMs - now) / (float)FeedbackDurationMs, 0f, 1f);
        float appear = Math.Min(1f, (1f - remaining) * 4f);
        float alpha = Math.Min(1f, remaining * 1.6f) * appear;
        float burst = 1f + (1f - remaining) * 0.45f;

        // Large initial pulse. It lasts long enough to be readable in combat but never blocks movement.
        DrawRing(e.SpriteBatch, center, 50f * burst, new Color(255, 224, 128) * (0.56f * alpha), 4f);
        DrawRing(e.SpriteBatch, center, 64f * burst, new Color(190, 122, 246) * (0.38f * alpha), 3f);

        for (int i = 0; i < 8; i++)
        {
            float phase = (float)(seconds * 4.0 + i * MathHelper.TwoPi / 8f);
            Vector2 p = center + new Vector2((float)Math.Cos(phase) * 54f, (float)Math.Sin(phase) * 28f - 6f);
            int s = i % 2 == 0 ? 7 : 5;
            e.SpriteBatch.Draw(Game1.staminaRect, new Rectangle((int)p.X - s / 2, (int)p.Y - s / 2, s, s), new Color(255, 219, 104) * (0.78f * alpha));
        }

        List<int> modules = new() { 0 };
        if (LastShield) modules.Add(1);
        if (LastSpirit) modules.Add(2);
        if (LastLuck) modules.Add(3);

        int iconSize = 38;
        int gap = 7;
        int totalWidth = modules.Count * iconSize + Math.Max(0, modules.Count - 1) * gap;
        float startX = center.X - totalWidth / 2f + iconSize / 2f;
        float iconY = center.Y - 106f - (1f - remaining) * 8f;
        for (int i = 0; i < modules.Count; i++)
            DrawModuleIcon(e.SpriteBatch, modules[i], new Vector2(startX + i * (iconSize + gap), iconY), iconSize, alpha);

        string readout = BuildReadout();
        Vector2 textSize = Game1.smallFont.MeasureString(readout) * 0.86f;
        Vector2 textPos = new(center.X - textSize.X / 2f, iconY + 27f);
        e.SpriteBatch.DrawString(Game1.smallFont, readout, textPos + new Vector2(2f, 2f), Color.Black * (0.70f * alpha), 0f, Vector2.Zero, 0.86f, SpriteEffects.None, 1f);
        e.SpriteBatch.DrawString(Game1.smallFont, readout, textPos, Color.White * alpha, 0f, Vector2.Zero, 0.86f, SpriteEffects.None, 1f);
    }

    private static string BuildReadout()
    {
        List<string> parts = new();
        parts.Add(LastHeal > 0 ? $"+{LastHeal} HP" : "HP MAX");
        if (LastShield) parts.Add($"SHIELD {LastShieldPercent}%");
        if (LastSpirit) parts.Add($"+{LastStamina:0} STA");
        if (LastLuck) parts.Add("+1 LUCK");
        return string.Join("  •  ", parts);
    }

    private static void DrawModuleIcon(SpriteBatch batch, int moduleIndex, Vector2 center, int size, float alpha)
    {
        TryLoadIcons();
        Rectangle dest = new((int)center.X - size / 2, (int)center.Y - size / 2, size, size);
        batch.Draw(Game1.staminaRect, new Rectangle(dest.X - 3, dest.Y - 3, dest.Width + 6, dest.Height + 6), new Color(30, 22, 38) * (0.78f * alpha));
        batch.Draw(Game1.staminaRect, new Rectangle(dest.X - 1, dest.Y - 1, dest.Width + 2, dest.Height + 2), new Color(227, 171, 87) * (0.72f * alpha));

        if (SkillIcons is not null)
        {
            Rectangle source = new(Math.Clamp(moduleIndex, 0, 3) * 32, 0, 32, 32);
            batch.Draw(SkillIcons, dest, source, Color.White * alpha);
        }
        else
        {
            batch.Draw(Game1.staminaRect, dest, new Color(177, 105, 221) * (0.78f * alpha));
        }
    }

    private static void TryLoadIcons()
    {
        if (SkillIcons is not null || SkillIconsFailed || ModEntry.StaticHelper is null)
            return;

        try
        {
            SkillIcons = ModEntry.StaticHelper.ModContent.Load<Texture2D>("assets/chacha_skill_icons.png");
        }
        catch (Exception ex)
        {
            SkillIconsFailed = true;
            ModEntry.StaticMonitor?.Log($"ChaCha support feedback icons unavailable: {ex.Message}", LogLevel.Warn);
        }
    }

    private static void DrawRing(SpriteBatch batch, Vector2 center, float radius, Color color, float thickness)
    {
        const int Segments = 28;
        Vector2 previous = center + new Vector2(radius, 0f);
        for (int i = 1; i <= Segments; i++)
        {
            float angle = MathHelper.TwoPi * i / Segments;
            Vector2 current = center + new Vector2((float)Math.Cos(angle) * radius, (float)Math.Sin(angle) * radius * 0.58f);
            DrawLine(batch, previous, current, thickness, color);
            previous = current;
        }
    }

    private static void DrawLine(SpriteBatch batch, Vector2 start, Vector2 end, float thickness, Color color)
    {
        Vector2 delta = end - start;
        float length = delta.Length();
        if (length <= 0.1f)
            return;
        float rotation = (float)Math.Atan2(delta.Y, delta.X);
        batch.Draw(Game1.staminaRect, start, null, color, rotation, Vector2.Zero, new Vector2(length, Math.Max(1f, thickness)), SpriteEffects.None, 1f);
    }
}
