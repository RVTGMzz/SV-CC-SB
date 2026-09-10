using Cardcha.Services;
using HarmonyLib;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewValley;
using StardewValley.Monsters;
using System.Reflection;

namespace Cardcha.Patches;

/// <summary>
/// 0676B world-depth correctness hotfix.
///
/// Region II/III/IV previously rendered authored enemies, terrain and decor from RenderedWorld.
/// That event runs after Stardew has already drawn the Farmer/NPC layer, so even art intended
/// to sit on the ground could cover characters. The fix is architectural rather than another
/// offset tweak:
///  - expedition enemy art is drawn from Monster.draw, at the proxy's normal world-depth slot;
///  - the old post-world enemy renderer is suppressed to prevent double drawing;
///  - the old post-world biome overlay is replaced by a tiny extraction marker only;
///  - the extraction marker disappears whenever the local Farmer/NPC is close enough to overlap it.
///
/// Static terrain/decor must be authored into map layers in the next visual pass, never painted
/// over the finished world from RenderedWorld again.
/// </summary>
internal static class RegionExpeditionProxyDrawPatch
{
    private const float EnemyWorldScale = 4f;
    private const float MarkerActorSafetyRadius = 108f;

    private const string Region2EnemyAtlasPath = "assets/region2_forgotten_archive_enemies.png";
    private const string Region3EnemyAtlasPath = "assets/region3_mirrorwild_enemies.png";
    private const string Region4EnemyAtlasPath = "assets/region4_resonance_enemies.png";

    private static Texture2D? Region2EnemyAtlas;
    private static Texture2D? Region3EnemyAtlas;
    private static Texture2D? Region4EnemyAtlas;
    private static bool Region2AtlasFailed;
    private static bool Region3AtlasFailed;
    private static bool Region4AtlasFailed;

    public static void Apply(Harmony harmony)
    {
        MethodInfo? monsterDraw = AccessTools.DeclaredMethod(typeof(Monster), "draw", new[] { typeof(SpriteBatch) });
        if (monsterDraw is null || monsterDraw.DeclaringType != typeof(Monster))
            throw new MissingMethodException("Could not resolve the draw(SpriteBatch) implementation declared by Monster.");

        harmony.Patch(
            monsterDraw,
            prefix: new HarmonyMethod(typeof(RegionExpeditionProxyDrawPatch), nameof(MonsterDrawPrefix))
        );

        MethodInfo? oldEnemyDraw = AccessTools.DeclaredMethod(typeof(RegionExpeditionService), "DrawEnemyIdentity");
        if (oldEnemyDraw is null)
            throw new MissingMethodException("Could not resolve RegionExpeditionService.DrawEnemyIdentity.");
        harmony.Patch(
            oldEnemyDraw,
            prefix: new HarmonyMethod(typeof(RegionExpeditionProxyDrawPatch), nameof(SkipLegacyPostWorldEnemyDraw))
        );

        MethodInfo? oldRegionDraw = AccessTools.DeclaredMethod(typeof(RegionExpeditionService), "DrawRegionIdentity");
        if (oldRegionDraw is null)
            throw new MissingMethodException("Could not resolve RegionExpeditionService.DrawRegionIdentity.");
        harmony.Patch(
            oldRegionDraw,
            prefix: new HarmonyMethod(typeof(RegionExpeditionProxyDrawPatch), nameof(RegionIdentityPrefix))
        );

        ModEntry.StaticMonitor?.Log(
            "0676B expedition depth guard active: actors use Monster.draw ordering; RenderedWorld terrain/decor overlays are disabled.",
            StardewModdingAPI.LogLevel.Info
        );
    }

    private static bool MonsterDrawPrefix(Monster __instance, SpriteBatch b)
    {
        if (!__instance.modData.ContainsKey(RegionExpeditionService.EnemyMarkerKey))
            return true;

        DrawAuthoredEnemy(b, __instance);
        return false;
    }

    private static bool SkipLegacyPostWorldEnemyDraw()
        => false;

    private static bool RegionIdentityPrefix(SpriteBatch batch, GameLocation location, ExpeditionRegion region)
    {
        DrawSafeExtractionMarker(batch, location, region);
        return false;
    }

    private static void DrawAuthoredEnemy(SpriteBatch batch, Monster monster)
    {
        if (!monster.modData.TryGetValue(RegionExpeditionService.EnemyRoleKey, out string? role)
            || string.IsNullOrWhiteSpace(role))
        {
            return;
        }

        ExpeditionRegion? region = ResolveRegion(monster.currentLocation ?? Game1.currentLocation);
        if (region is null)
            return;

        Texture2D? atlas = GetEnemyAtlas(region.Value);
        int roleIndex = RoleIndex(region.Value, role);
        Vector2 world = monster.Position + new Vector2(32f, 64f);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
        float layer = Math.Clamp((world.Y + 32f) / 10000f, 0f, 0.94f);
        bool floating = role is "ink_moth" or "mirror_wisp" or "ignis_echo" or "aether_mite";
        float bob = floating
            ? (float)Math.Sin(Environment.TickCount64 / 210d + monster.GetHashCode() * 0.01) * 4f
            : 0f;

        batch.Draw(
            Game1.staminaRect,
            new Rectangle((int)local.X - 31, (int)local.Y - 8, 62, 8),
            Color.Black * 0.20f
        );

        if (atlas is null || roleIndex < 0)
        {
            Color fallback = region switch
            {
                ExpeditionRegion.ForgottenArchive => new Color(187, 164, 122),
                ExpeditionRegion.Mirrorwild => new Color(139, 201, 226),
                _ => new Color(203, 137, 211),
            };
            batch.Draw(
                Game1.staminaRect,
                new Rectangle((int)local.X - 18, (int)local.Y - 52, 36, 48),
                fallback * 0.82f
            );
            return;
        }

        int frame = (int)((Environment.TickCount64 / 280L + Math.Abs(monster.GetHashCode())) % 2L);
        Rectangle src = new((roleIndex * 2 + frame) * 32, 0, 32, 32);
        batch.Draw(
            atlas,
            local + new Vector2(0f, bob),
            src,
            Color.White,
            0f,
            new Vector2(16f, 28f),
            EnemyWorldScale,
            SpriteEffects.None,
            layer
        );
    }

    private static void DrawSafeExtractionMarker(SpriteBatch batch, GameLocation location, ExpeditionRegion region)
    {
        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 40;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 28;
        Point extract = new(width / 2, Math.Max(3, height - 3));
        Vector2 world = new(extract.X * 64f + 32f, extract.Y * 64f + 32f);

        // RenderedWorld is allowed only for this non-physical cue. If an actor approaches,
        // remove the cue entirely instead of ever letting it paint over a sprite again.
        if (Game1.player?.currentLocation == location
            && Vector2.Distance(Game1.player.Position + new Vector2(32f, 32f), world) < MarkerActorSafetyRadius)
        {
            return;
        }

        foreach (NPC actor in location.characters)
        {
            if (Vector2.Distance(actor.Position + new Vector2(32f, 32f), world) < MarkerActorSafetyRadius)
                return;
        }

        Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
        Color accent = region switch
        {
            ExpeditionRegion.ForgottenArchive => new Color(208, 174, 112),
            ExpeditionRegion.Mirrorwild => new Color(143, 187, 226),
            _ => new Color(197, 135, 218),
        };
        float pulse = 0.50f + 0.12f * (float)Math.Sin(Environment.TickCount64 / 240d);
        Color c = accent * pulse;

        const int arm = 19;
        const int thickness = 3;
        const int half = 24;

        // Four corner brackets communicate an extraction zone without a giant floor overlay.
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - half, (int)local.Y - half, arm, thickness), c);
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - half, (int)local.Y - half, thickness, arm), c);
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X + half - arm, (int)local.Y - half, arm, thickness), c);
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X + half - thickness, (int)local.Y - half, thickness, arm), c);
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - half, (int)local.Y + half - thickness, arm, thickness), c);
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - half, (int)local.Y + half - arm, thickness, arm), c);
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X + half - arm, (int)local.Y + half - thickness, arm, thickness), c);
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X + half - thickness, (int)local.Y + half - arm, thickness, arm), c);
    }

    private static ExpeditionRegion? ResolveRegion(GameLocation? location)
    {
        string? name = location?.NameOrUniqueName;
        if (name?.Equals(RegionExpeditionService.Region2LocationName, StringComparison.OrdinalIgnoreCase) == true)
            return ExpeditionRegion.ForgottenArchive;
        if (name?.Equals(RegionExpeditionService.Region3LocationName, StringComparison.OrdinalIgnoreCase) == true)
            return ExpeditionRegion.Mirrorwild;
        if (name?.Equals(RegionExpeditionService.Region4LocationName, StringComparison.OrdinalIgnoreCase) == true)
            return ExpeditionRegion.ResonanceVerge;
        return null;
    }

    private static Texture2D? GetEnemyAtlas(ExpeditionRegion region)
    {
        try
        {
            if (region == ExpeditionRegion.ForgottenArchive)
            {
                if (Region2AtlasFailed)
                    return null;
                return Region2EnemyAtlas ??= ModEntry.StaticHelper?.ModContent.Load<Texture2D>(Region2EnemyAtlasPath);
            }
            if (region == ExpeditionRegion.Mirrorwild)
            {
                if (Region3AtlasFailed)
                    return null;
                return Region3EnemyAtlas ??= ModEntry.StaticHelper?.ModContent.Load<Texture2D>(Region3EnemyAtlasPath);
            }

            if (Region4AtlasFailed)
                return null;
            return Region4EnemyAtlas ??= ModEntry.StaticHelper?.ModContent.Load<Texture2D>(Region4EnemyAtlasPath);
        }
        catch (Exception ex)
        {
            if (region == ExpeditionRegion.ForgottenArchive)
                Region2AtlasFailed = true;
            else if (region == ExpeditionRegion.Mirrorwild)
                Region3AtlasFailed = true;
            else
                Region4AtlasFailed = true;

            ModEntry.StaticMonitor?.Log(
                $"0676B expedition enemy atlas unavailable for {region}: {ex.GetType().Name}: {ex.Message}",
                StardewModdingAPI.LogLevel.Warn
            );
            return null;
        }
    }

    private static int RoleIndex(ExpeditionRegion region, string role)
        => region switch
        {
            ExpeditionRegion.ForgottenArchive => role switch
            {
                "ink_moth" => 0,
                "paper_scarab" => 1,
                "dust_slime" => 2,
                "archive_warden" => 3,
                _ => -1,
            },
            ExpeditionRegion.Mirrorwild => role switch
            {
                "mirror_wisp" => 0,
                "glass_scarab" => 1,
                "echo_slime" => 2,
                "mirror_sentinel" => 3,
                _ => -1,
            },
            _ => role switch
            {
                "ignis_echo" => 0,
                "vita_husk" => 1,
                "aether_mite" => 2,
                "resonant_prime" => 3,
                _ => -1,
            }
        };
}
