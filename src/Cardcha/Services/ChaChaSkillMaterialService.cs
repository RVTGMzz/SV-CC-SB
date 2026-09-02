using Cardcha.UI;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace Cardcha.Services;

internal readonly record struct ChaChaUpgradeQuote(int MaterialCost, int DustCost, int NextLevel);

/// <summary>
/// Physical exploration materials + the Airship ChaCha Resonance Pedestal.
/// Region materials stay in the backpack so the loop is tangible: find them in a custom region,
/// bring them home to the Airship, then spend them together with Magic Dust at the pedestal.
/// </summary>
internal sealed class ChaChaSkillMaterialService
{
    public const string VitalDewdropId = "Ronvotri.Cardcha_VitalDewdrop";
    public const string MoonshieldShardId = "Ronvotri.Cardcha_MoonshieldShard";
    public const string BreezeFeatherId = "Ronvotri.Cardcha_BreezeFeather";
    public const string FortuneCoinId = "Ronvotri.Cardcha_FortuneCoin";

    public const string Region2LocationName = "Cardcha_Region2";
    public const string Region3LocationName = "Cardcha_Region3";
    public const string Region4LocationName = "Cardcha_Region4";

    // Alpha economy knobs. Centralized intentionally so balancing later never requires rewiring UI/save logic.
    public static readonly int[] UpgradeMaterialCosts = { 3, 5, 8, 12 };
    public static readonly int[] UpgradeDustCosts = { 5, 10, 15, 25 };

    private const double RegularRegionMaterialChance = 0.18d;
    private const double BossRegionMaterialChance = 1.00d;
    private static readonly Point StationTile = new(19, 5);

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;
    private readonly ChaChaSkillService Skills;
    private readonly ControllerProfileService Controller;

    private Texture2D? MaterialTexture;
    private bool MaterialTextureFailed;
    private long LastStationPulseMs;

    public ChaChaSkillMaterialService(
        IModHelper helper,
        IMonitor monitor,
        SaveService save,
        ChaChaSkillService skills,
        ControllerProfileService controller)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
        this.Skills = skills;
        this.Controller = controller;
    }

    public static IReadOnlyList<string> MaterialIds { get; } = new[]
    {
        VitalDewdropId,
        MoonshieldShardId,
        BreezeFeatherId,
        FortuneCoinId
    };

    public static string GetMaterialIdForSkill(string skillId)
        => skillId switch
        {
            ChaChaSkillService.VitalSkillId => VitalDewdropId,
            ChaChaSkillService.GuardSkillId => MoonshieldShardId,
            ChaChaSkillService.SpiritSkillId => BreezeFeatherId,
            ChaChaSkillService.LuckSkillId => FortuneCoinId,
            _ => ""
        };

    public static int GetSkillIndex(string skillId)
        => skillId switch
        {
            ChaChaSkillService.VitalSkillId => 0,
            ChaChaSkillService.GuardSkillId => 1,
            ChaChaSkillService.SpiritSkillId => 2,
            ChaChaSkillService.LuckSkillId => 3,
            _ => -1
        };

    public static string GetSkillIdForIndex(int index)
        => index switch
        {
            0 => ChaChaSkillService.VitalSkillId,
            1 => ChaChaSkillService.GuardSkillId,
            2 => ChaChaSkillService.SpiritSkillId,
            3 => ChaChaSkillService.LuckSkillId,
            _ => ""
        };

    public static int GetRegionForSkill(string skillId)
        => GetSkillIndex(skillId) + 1;

    public int CountMaterial(string materialId)
    {
        if (!Context.IsWorldReady || string.IsNullOrWhiteSpace(materialId))
            return 0;

        string qualified = $"(O){materialId}";
        int total = 0;
        foreach (Item? item in Game1.player.Items)
        {
            if (item is not null && item.QualifiedItemId.Equals(qualified, StringComparison.OrdinalIgnoreCase))
                total = checked(total + Math.Max(0, item.Stack));
        }
        return total;
    }

    public ChaChaUpgradeQuote? GetUpgradeQuote(string skillId)
    {
        if (!this.Skills.HasSkill(skillId))
            return null;

        int level = this.Skills.GetLevel(skillId);
        if (level <= 0 || level >= ChaChaSkillService.MaxSkillLevel)
            return null;

        int index = Math.Clamp(level - 1, 0, UpgradeMaterialCosts.Length - 1);
        return new ChaChaUpgradeQuote(
            UpgradeMaterialCosts[index],
            UpgradeDustCosts[index],
            level + 1
        );
    }

    public bool TryUpgrade(string skillId, out string status)
    {
        if (!Context.IsWorldReady)
        {
            status = ModEntry.T("chacha.station.status.load-save");
            return false;
        }

        if (!this.Skills.HasSkill(skillId))
        {
            status = ModEntry.T("chacha.station.status.skill-locked", new { region = Math.Max(1, GetRegionForSkill(skillId)) });
            return false;
        }

        int level = this.Skills.GetLevel(skillId);
        if (level >= ChaChaSkillService.MaxSkillLevel)
        {
            status = ModEntry.T("chacha.station.status.max");
            return false;
        }

        ChaChaUpgradeQuote quote = this.GetUpgradeQuote(skillId)!.Value;
        string materialId = GetMaterialIdForSkill(skillId);
        int haveMaterial = this.CountMaterial(materialId);
        int haveDust = Math.Max(0, this.Save.Data.SuspiciousDust);

        if (haveMaterial < quote.MaterialCost || haveDust < quote.DustCost)
        {
            status = ModEntry.T("chacha.station.status.not-enough", new
            {
                material = haveMaterial,
                materialNeed = quote.MaterialCost,
                dust = haveDust,
                dustNeed = quote.DustCost
            });
            return false;
        }

        if (!RemovePhysicalObject(materialId, quote.MaterialCost))
        {
            status = ModEntry.T("chacha.station.status.consume-failed");
            return false;
        }

        this.Save.Data.SuspiciousDust = Math.Max(0, haveDust - quote.DustCost);
        if (!this.Skills.ApplyUpgradeFromStation(skillId))
        {
            // This path should never happen after the preflight checks. Return the material rather
            // than silently eating an item if a future migration changes skill state mid-action.
            GivePhysicalObject(materialId, quote.MaterialCost);
            this.Save.Data.SuspiciousDust = haveDust;
            status = ModEntry.T("chacha.station.status.consume-failed");
            return false;
        }

        this.Save.Save();
        this.Skills.TriggerCastPresentation();
        Game1.playSound("reward");
        status = ModEntry.T("chacha.station.status.upgraded", new { level = quote.NextLevel });
        return true;
    }

    public void TryDrop(GameLocation location, Vector2 position, Farmer? killer, EnemyLootScale scale)
    {
        if (!Context.IsWorldReady || killer?.IsLocalPlayer != true || !this.Save.Data.ChaChaLoaned)
            return;

        string materialId = ResolveMaterialForLocation(location.NameOrUniqueName);
        if (string.IsNullOrWhiteSpace(materialId))
            return;

        double chance = scale == EnemyLootScale.BossLike
            ? BossRegionMaterialChance
            : RegularRegionMaterialChance;
        if (Game1.random.NextDouble() >= chance)
            return;

        Item item = ItemRegistry.Create($"(O){materialId}");
        Game1.createItemDebris(item, position, -1, location);
        this.Monitor.Log(
            $"ChaCha region material dropped: {materialId} in {location.NameOrUniqueName} (profile={scale}, chance={chance:P0}).",
            LogLevel.Trace
        );
    }

    public void GiveAllForDebug(int amount)
    {
        if (!Context.IsWorldReady)
            return;

        amount = Math.Clamp(amount, 1, 999);
        foreach (string id in MaterialIds)
            GivePhysicalObject(id, amount);
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        if (!Context.IsWorldReady
            || !this.Save.Data.AirshipUnlocked
            || !this.Save.Data.ChaChaLoaned
            || Game1.currentLocation?.NameOrUniqueName.Equals(AirshipFoundationService.DeckLocationName, StringComparison.OrdinalIgnoreCase) != true)
        {
            return;
        }

        this.DrawStation(e.SpriteBatch);
    }

    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady
            || !this.Save.Data.AirshipUnlocked
            || !this.Save.Data.ChaChaLoaned
            || !e.Button.IsActionButton()
            || Game1.activeClickableMenu is not null
            || Game1.dialogueUp
            || Game1.eventUp
            || Game1.currentLocation?.NameOrUniqueName.Equals(AirshipFoundationService.DeckLocationName, StringComparison.OrdinalIgnoreCase) != true)
        {
            return;
        }

        Point player = new((int)(Game1.player.Position.X / 64f), (int)(Game1.player.Position.Y / 64f));
        Point action = GetActionTile(player);
        bool near = Math.Abs(player.X - StationTile.X) <= 1 && Math.Abs(player.Y - StationTile.Y) <= 1;
        if (!near && action != StationTile)
            return;

        this.Helper.Input.Suppress(e.Button);
        Game1.playSound("smallSelect");
        Game1.activeClickableMenu = new ChaChaSkillUpgradeMenu(this.Save, this.Skills, this, this.Controller);
    }

    public string Describe()
    {
        string counts = string.Join(", ", MaterialIds.Select(id => $"{id}={this.CountMaterial(id)}"));
        return $"AirshipStation={StationTile.X},{StationTile.Y} | RegionDropRegular={RegularRegionMaterialChance:P0} | " +
               $"RegionDropBoss={BossRegionMaterialChance:P0} | Materials[{counts}]";
    }

    private static string ResolveMaterialForLocation(string? locationName)
    {
        if (string.IsNullOrWhiteSpace(locationName))
            return "";

        if (locationName.Equals(AirshipFoundationService.Region1LocationName, StringComparison.OrdinalIgnoreCase))
            return VitalDewdropId;
        if (locationName.Equals(Region2LocationName, StringComparison.OrdinalIgnoreCase))
            return MoonshieldShardId;
        if (locationName.Equals(Region3LocationName, StringComparison.OrdinalIgnoreCase))
            return BreezeFeatherId;
        if (locationName.Equals(Region4LocationName, StringComparison.OrdinalIgnoreCase))
            return FortuneCoinId;
        return "";
    }

    private void DrawStation(SpriteBatch batch)
    {
        this.TryLoadMaterialTexture();

        Vector2 center = Game1.GlobalToLocal(
            Game1.viewport,
            new Vector2(StationTile.X * 64f + 32f, StationTile.Y * 64f + 34f)
        );
        double seconds = Game1.currentGameTime.TotalGameTime.TotalSeconds;
        float pulse = 0.55f + 0.20f * (float)Math.Sin(seconds * 2.4);
        Color violet = new Color(210, 130, 255) * (0.48f + pulse * 0.30f);
        Color cyan = new Color(103, 235, 244) * (0.45f + pulse * 0.30f);
        Color gold = new Color(255, 221, 130) * 0.92f;

        // Presentation-only Airship furniture. No map tile/collision is changed.
        DrawRect(batch, new Rectangle((int)center.X - 42, (int)center.Y + 20, 84, 18), new Color(37, 31, 49) * 0.92f);
        DrawRect(batch, new Rectangle((int)center.X - 33, (int)center.Y + 4, 66, 20), new Color(70, 55, 91) * 0.96f);
        DrawRect(batch, new Rectangle((int)center.X - 25, (int)center.Y - 3, 50, 9), gold * 0.78f);
        DrawDiamond(batch, center + new Vector2(0f, 1f), 20f + pulse * 4f, violet);
        DrawDiamond(batch, center + new Vector2(0f, 1f), 11f + pulse * 2f, cyan);

        if (this.MaterialTexture is not null)
        {
            for (int i = 0; i < 4; i++)
            {
                float phase = (float)(seconds * 0.72 + i * MathHelper.PiOver2);
                Vector2 p = center + new Vector2((float)Math.Cos(phase) * 48f, -27f + (float)Math.Sin(phase) * 13f);
                Rectangle source = new(i * 32, 0, 32, 32);
                batch.Draw(
                    this.MaterialTexture,
                    p,
                    source,
                    Color.White * (0.74f + pulse * 0.20f),
                    0f,
                    new Vector2(16f, 16f),
                    0.72f,
                    SpriteEffects.None,
                    1f
                );
            }
        }

        Point player = new((int)(Game1.player.Position.X / 64f), (int)(Game1.player.Position.Y / 64f));
        if (Math.Abs(player.X - StationTile.X) <= 2 && Math.Abs(player.Y - StationTile.Y) <= 2)
        {
            string text = ModEntry.T("chacha.station.world-label");
            Vector2 size = Game1.smallFont.MeasureString(text);
            batch.DrawString(
                Game1.smallFont,
                text,
                new Vector2(center.X - size.X / 2f, center.Y - 76f),
                Color.White * 0.90f,
                0f,
                Vector2.Zero,
                1f,
                SpriteEffects.None,
                1f
            );
        }

        this.LastStationPulseMs = Environment.TickCount64;
    }

    private void TryLoadMaterialTexture()
    {
        if (this.MaterialTexture is not null || this.MaterialTextureFailed)
            return;

        try
        {
            this.MaterialTexture = Game1.content.Load<Texture2D>(ItemAssetService.ChaChaSkillMaterialsTextureAsset);
        }
        catch (Exception ex)
        {
            this.MaterialTextureFailed = true;
            this.Monitor.Log($"Could not load ChaCha skill material UI texture: {ex.Message}", LogLevel.Warn);
        }
    }

    private static bool RemovePhysicalObject(string objectId, int requested)
    {
        if (!Context.IsWorldReady || requested <= 0)
            return requested <= 0;

        int available = 0;
        string qualified = $"(O){objectId}";
        foreach (Item? item in Game1.player.Items)
        {
            if (item is not null && item.QualifiedItemId.Equals(qualified, StringComparison.OrdinalIgnoreCase))
                available += Math.Max(0, item.Stack);
        }
        if (available < requested)
            return false;

        int remaining = requested;
        for (int i = 0; i < Game1.player.Items.Count && remaining > 0; i++)
        {
            Item? item = Game1.player.Items[i];
            if (item is null || !item.QualifiedItemId.Equals(qualified, StringComparison.OrdinalIgnoreCase))
                continue;

            int take = Math.Min(remaining, Math.Max(0, item.Stack));
            item.Stack -= take;
            remaining -= take;
            if (item.Stack <= 0)
                Game1.player.Items[i] = null;
        }
        return remaining == 0;
    }

    private static void GivePhysicalObject(string objectId, int amount)
    {
        if (!Context.IsWorldReady || amount <= 0)
            return;

        int remaining = amount;
        while (remaining > 0)
        {
            int stack = Math.Min(999, remaining);
            Item item = ItemRegistry.Create($"(O){objectId}");
            item.Stack = stack;
            Item? leftover = Game1.player.addItemToInventory(item);
            if (leftover is not null && Game1.currentLocation is not null)
                Game1.createItemDebris(leftover, Game1.player.Position, -1, Game1.currentLocation);
            remaining -= stack;
        }
    }

    private static Point GetActionTile(Point player)
        => Game1.player.FacingDirection switch
        {
            0 => new Point(player.X, player.Y - 1),
            1 => new Point(player.X + 1, player.Y),
            2 => new Point(player.X, player.Y + 1),
            3 => new Point(player.X - 1, player.Y),
            _ => player
        };

    private static void DrawRect(SpriteBatch batch, Rectangle rect, Color color)
        => batch.Draw(Game1.staminaRect, rect, color);

    private static void DrawDiamond(SpriteBatch batch, Vector2 center, float radius, Color color)
    {
        int r = Math.Max(2, (int)Math.Round(radius));
        for (int y = -r; y <= r; y += Math.Max(2, r / 8))
        {
            int half = Math.Max(1, r - Math.Abs(y));
            batch.Draw(Game1.staminaRect, new Rectangle((int)center.X - half, (int)center.Y + y, half * 2, 2), color * 0.34f);
        }
    }
}
