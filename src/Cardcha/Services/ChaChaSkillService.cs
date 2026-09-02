using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// Persistent ChaCha normal-form skill foundation.
/// Skills are exploration rewards, independent from Mythic Echo/Boss Form.
/// This pass deliberately leaves the first skill's healing balance uncommitted until the
/// previously-agreed values are recovered/confirmed; discovery, equip, level persistence and
/// ChaCha cast presentation are real and testable now.
/// </summary>
internal sealed class ChaChaSkillService
{
    public const string VitalSkillId = "vital_blessing";
    public const int MaxSkillLevel = 5;
    private const int CastVisualDurationMs = 1050;

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;
    private readonly WorldActorService WorldActors;

    private long CastVisualUntilMs;
    private Point? CachedRegion1RelicTile;

    public ChaChaSkillService(IModHelper helper, IMonitor monitor, SaveService save, WorldActorService worldActors)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
        this.WorldActors = worldActors;
    }

    public bool HasSkill(string id)
        => this.Save.Data.ChaChaSkillsFound.Contains(id);

    public int GetLevel(string id)
        => this.HasSkill(id)
            ? Math.Clamp(this.Save.Data.ChaChaSkillLevels.TryGetValue(id, out int level) ? level : 1, 1, MaxSkillLevel)
            : 0;

    public bool IsActive(string id)
        => this.HasSkill(id)
           && string.Equals(this.Save.Data.ActiveChaChaSkillId, id, StringComparison.OrdinalIgnoreCase);

    public string ActiveSkillId => this.Save.Data.ActiveChaChaSkillId ?? "";

    public bool DiscoverVitalSkill(bool showPresentation = true)
    {
        if (!Context.IsWorldReady || !this.Save.Data.ChaChaLoaned)
            return false;

        bool newlyFound = this.Save.Data.ChaChaSkillsFound.Add(VitalSkillId);
        if (!this.Save.Data.ChaChaSkillLevels.ContainsKey(VitalSkillId))
            this.Save.Data.ChaChaSkillLevels[VitalSkillId] = 1;

        // First discovered normal-form skill equips automatically so the player immediately
        // understands that it belongs to ChaCha rather than the five Cardcha card slots.
        if (string.IsNullOrWhiteSpace(this.Save.Data.ActiveChaChaSkillId))
            this.Save.Data.ActiveChaChaSkillId = VitalSkillId;

        this.Save.Save();

        if (showPresentation)
        {
            this.TriggerCastPresentation();
            Game1.playSound("discoverMineral");
            Game1.showGlobalMessage(ModEntry.T(newlyFound ? "chacha.skill.vital.found" : "chacha.skill.vital.already"));
        }

        if (newlyFound)
            this.Monitor.Log("ChaCha skill discovered: vital_blessing from Region I exploration.", LogLevel.Info);

        return newlyFound;
    }

    public bool SetActive(string id)
    {
        if (!this.HasSkill(id))
            return false;

        this.Save.Data.ActiveChaChaSkillId = id;
        this.Save.Save();
        Game1.playSound("smallSelect");
        return true;
    }

    /// <summary>
    /// TEST-only level setter. Real Magic Dust upgrade costs remain intentionally uncommitted
    /// until the approved heal-level table is restored. This lets UI/persistence be tested now.
    /// </summary>
    public bool DebugSetLevel(string id, int level)
    {
        if (!this.HasSkill(id))
            return false;

        this.Save.Data.ChaChaSkillLevels[id] = Math.Clamp(level, 1, MaxSkillLevel);
        this.Save.Save();
        this.TriggerCastPresentation();
        return true;
    }

    public void TriggerCastPresentation()
    {
        if (!Context.IsWorldReady || !this.Save.Data.ChaChaLoaned)
            return;

        this.CastVisualUntilMs = Environment.TickCount64 + CastVisualDurationMs;
        this.WorldActors.TriggerChaChaEmote(56);
        Game1.playSound("wand");
    }

    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady
            || !this.Save.Data.ChaChaLoaned
            || this.HasSkill(VitalSkillId)
            || !e.Button.IsActionButton()
            || Game1.activeClickableMenu is not null
            || Game1.dialogueUp
            || Game1.eventUp
            || Game1.currentLocation?.NameOrUniqueName.Equals(AirshipFoundationService.Region1LocationName, StringComparison.OrdinalIgnoreCase) != true)
        {
            return;
        }

        Point relic = this.ResolveRegion1RelicTile(Game1.currentLocation);
        Point action = GetActionTile();
        Point player = new((int)(Game1.player.Position.X / 64f), (int)(Game1.player.Position.Y / 64f));
        bool near = Math.Abs(player.X - relic.X) <= 1 && Math.Abs(player.Y - relic.Y) <= 1;
        if (!near && action != relic)
            return;

        this.Helper.Input.Suppress(e.Button);
        this.DiscoverVitalSkill(showPresentation: true);
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        if (!Context.IsWorldReady || !this.Save.Data.ChaChaLoaned)
            return;

        if (!this.HasSkill(VitalSkillId)
            && Game1.currentLocation?.NameOrUniqueName.Equals(AirshipFoundationService.Region1LocationName, StringComparison.OrdinalIgnoreCase) == true)
        {
            this.DrawRegion1Relic(e.SpriteBatch, this.ResolveRegion1RelicTile(Game1.currentLocation));
        }

        if (Environment.TickCount64 < this.CastVisualUntilMs)
            this.DrawCastPresentation(e.SpriteBatch);
    }

    public void OnWarped(object? sender, WarpedEventArgs e)
    {
        if (!e.NewLocation.NameOrUniqueName.Equals(AirshipFoundationService.Region1LocationName, StringComparison.OrdinalIgnoreCase))
            this.CachedRegion1RelicTile = null;
    }

    public void OnReturnedToTitle(object? sender, ReturnedToTitleEventArgs e)
    {
        this.CastVisualUntilMs = 0;
        this.CachedRegion1RelicTile = null;
    }

    public string Describe()
        => $"Found=[{string.Join(',', this.Save.Data.ChaChaSkillsFound.OrderBy(p => p, StringComparer.OrdinalIgnoreCase))}] | " +
           $"Active={this.ActiveSkillId} | VitalLv={this.GetLevel(VitalSkillId)}/{MaxSkillLevel} | " +
           "HealBalance=UNLOCKED_FOR_DESIGN (runtime heal not enabled yet)";

    private Point ResolveRegion1RelicTile(GameLocation location)
    {
        if (this.CachedRegion1RelicTile is Point cached)
            return cached;

        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 40;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 28;
        Point preferred = new(Math.Clamp(6, 2, Math.Max(2, width - 3)), Math.Clamp(height - 6, 8, Math.Max(8, height - 3)));

        for (int radius = 0; radius <= 6; radius++)
        {
            for (int y = Math.Max(8, preferred.Y - radius); y <= Math.Min(height - 3, preferred.Y + radius); y++)
            {
                for (int x = Math.Max(2, preferred.X - radius); x <= Math.Min(width - 3, preferred.X + radius); x++)
                {
                    Vector2 tile = new(x, y);
                    try
                    {
                        if (!location.IsTileBlockedBy(tile) && !location.Objects.ContainsKey(tile))
                        {
                            this.CachedRegion1RelicTile = new Point(x, y);
                            return this.CachedRegion1RelicTile.Value;
                        }
                    }
                    catch
                    {
                    }
                }
            }
        }

        this.CachedRegion1RelicTile = preferred;
        return preferred;
    }

    private void DrawRegion1Relic(SpriteBatch batch, Point tile)
    {
        Vector2 center = Game1.GlobalToLocal(Game1.viewport, new Vector2(tile.X * 64f + 32f, tile.Y * 64f + 31f));
        double seconds = Game1.currentGameTime.TotalGameTime.TotalSeconds;
        float pulse = 0.72f + 0.18f * (float)Math.Sin(seconds * 3.4);
        Color mint = new Color(142, 255, 199) * pulse;
        Color white = Color.White * (0.58f + pulse * 0.26f);

        for (int ring = 0; ring < 3; ring++)
        {
            float radius = 18f + ring * 9f + (float)Math.Sin(seconds * 2.2 + ring) * 2f;
            DrawDiamond(batch, center, radius, mint * (0.72f - ring * 0.14f));
        }

        DrawDiamond(batch, center, 11f, white);
        for (int i = 0; i < 5; i++)
        {
            float phase = (float)(seconds * 1.8 + i * MathHelper.TwoPi / 5f);
            Vector2 p = center + new Vector2((float)Math.Cos(phase) * 38f, (float)Math.Sin(phase) * 21f);
            batch.Draw(Game1.staminaRect, new Rectangle((int)p.X - 2, (int)p.Y - 2, 5, 5), white);
        }
    }

    private void DrawCastPresentation(SpriteBatch batch)
    {
        NPC? chacha = this.WorldActors.FindChaChaActor();
        if (chacha is null || chacha.isInvisible.Value || chacha.currentLocation != Game1.currentLocation)
            return;

        long now = Environment.TickCount64;
        float remaining = Math.Clamp((this.CastVisualUntilMs - now) / (float)CastVisualDurationMs, 0f, 1f);
        float progress = 1f - remaining;
        Vector2 chachaCenter = Game1.GlobalToLocal(Game1.viewport, chacha.Position + new Vector2(16f, 18f));
        Vector2 playerCenter = Game1.GlobalToLocal(Game1.viewport, Game1.player.Position + new Vector2(32f, 35f));
        Color mint = new Color(129, 255, 194) * (0.72f * remaining);
        Color gold = new Color(255, 226, 128) * (0.58f * remaining);

        float castRadius = 18f + progress * 32f;
        DrawDiamond(batch, chachaCenter, castRadius, mint);
        DrawDiamond(batch, chachaCenter, castRadius * 0.62f, gold);

        for (int i = 0; i < 6; i++)
        {
            float t = Math.Clamp(progress * 1.45f - i * 0.045f, 0f, 1f);
            Vector2 p = Vector2.Lerp(chachaCenter, playerCenter, t);
            p.Y -= (float)Math.Sin(t * Math.PI) * (18f + i * 2f);
            int s = i % 2 == 0 ? 3 : 2;
            batch.Draw(Game1.staminaRect, new Rectangle((int)p.X - s, (int)p.Y - s, s * 2 + 1, s * 2 + 1), mint * (0.42f + 0.08f * i));
        }

        if (progress > 0.46f)
        {
            float bloom = Math.Clamp((progress - 0.46f) / 0.54f, 0f, 1f);
            DrawDiamond(batch, playerCenter, 14f + bloom * 31f, gold * (1f - bloom * 0.55f));
        }
    }

    private static Point GetActionTile()
    {
        Point player = new((int)(Game1.player.Position.X / 64f), (int)(Game1.player.Position.Y / 64f));
        return Game1.player.FacingDirection switch
        {
            0 => new Point(player.X, player.Y - 1),
            1 => new Point(player.X + 1, player.Y),
            2 => new Point(player.X, player.Y + 1),
            3 => new Point(player.X - 1, player.Y),
            _ => player
        };
    }

    private static void DrawDiamond(SpriteBatch batch, Vector2 center, float radius, Color color)
    {
        int r = Math.Max(2, (int)Math.Round(radius));
        for (int y = -r; y <= r; y += Math.Max(2, r / 7))
        {
            int half = Math.Max(1, r - Math.Abs(y));
            batch.Draw(Game1.staminaRect, new Rectangle((int)center.X - half, (int)center.Y + y, half * 2, 2), color * 0.34f);
        }
    }
}
