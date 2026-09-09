using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Monsters;

namespace Cardcha.Services;

/// <summary>
/// 0663 dedicated Cardcha visuals for Verdant Guardian summons. Runtime monsters remain
/// stable GreenSlime/Bug proxies, but their vanilla art is hidden and never presented to players.
/// </summary>
internal sealed class VerdantGuardianSummonVisualService
{
    private const int FrameSize = 32;
    private const string AssetRoot = "assets/bosses/verdant_guardian/summons";
    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly VerdantGuardianBossService Boss;
    private readonly Dictionary<string, Texture2D?> Textures = new(StringComparer.OrdinalIgnoreCase);
    private readonly HashSet<string> Failed = new(StringComparer.OrdinalIgnoreCase);

    public VerdantGuardianSummonVisualService(IModHelper helper, IMonitor monitor, VerdantGuardianBossService boss)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Boss = boss;
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        if (!this.Boss.IsInArena)
            return;

        long now = Environment.TickCount64;
        this.DrawSummonPortals(e.SpriteBatch, now);
        foreach (Monster add in this.Boss.VisualAdds)
            this.DrawSummon(e.SpriteBatch, add, now);
    }

    private void DrawSummonPortals(SpriteBatch batch, long now)
    {
        if (this.Boss.VisualState != VerdantGuardianState.SummonAdds)
            return;
        Texture2D? portal = this.Load("summon_portal.png");
        if (portal is null || portal.Width < 128 || portal.Height < 32)
            return;

        long elapsed = Math.Max(0L, now - this.Boss.VisualStateStartedAtMs);
        int frame = Math.Clamp((int)(elapsed * 4 / 600L), 0, 3);
        Rectangle src = new(frame * FrameSize, 0, FrameSize, FrameSize);
        Point[] tiles = this.Boss.VisualSummonTargets;
        string[] kinds = this.Boss.VisualSummonKinds;
        for (int i = 0; i < tiles.Length; i++)
        {
            Point tile = tiles[i];
            Vector2 world = new(tile.X * 64f + 32f, tile.Y * 64f + 45f);
            Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
            Color tint = i < kinds.Length && string.Equals(kinds[i], VerdantGuardianBossService.LeafWispId, StringComparison.OrdinalIgnoreCase)
                ? new Color(206, 255, 182)
                : new Color(145, 229, 105);
            batch.Draw(portal, local, src, tint, 0f, new Vector2(16f, 16f), 3.7f, SpriteEffects.None,
                Math.Clamp((world.Y + 16f) / 10000f, 0f, 0.985f));
        }
    }

    private void DrawSummon(SpriteBatch batch, Monster add, long now)
    {
        if (!add.modData.TryGetValue(VerdantGuardianBossService.BossAddTypeKey, out string? kind))
            return;

        bool wisp = string.Equals(kind, VerdantGuardianBossService.LeafWispId, StringComparison.OrdinalIgnoreCase);
        string file = wisp ? "leaf_wisp.png" : "briarling.png";
        Texture2D? texture = this.Load(file);
        if (texture is null || texture.Width < 128 || texture.Height < 128)
            return;

        int row = add.FacingDirection switch
        {
            2 => 0,
            1 => 1,
            0 => 2,
            3 => 3,
            _ => 0,
        };
        int phaseOffset = Math.Abs(add.GetHashCode()) % 4;
        int frame = (int)((now / (wisp ? 120L : 155L) + phaseOffset) % 4L);
        Rectangle src = new(frame * FrameSize, row * FrameSize, FrameSize, FrameSize);

        float floatBob = wisp ? (float)Math.Sin((now + phaseOffset * 83L) / 150d) * 5f : 0f;
        Vector2 feet = add.Position + new Vector2(32f, wisp ? 38f + floatBob : 53f);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, feet);
        float scale = wisp ? 2.05f : 2.20f;
        float layer = Math.Clamp((add.Position.Y + 96f) / 10000f, 0f, 0.99f);

        Rectangle shadow = new((int)local.X - (wisp ? 24 : 31), (int)local.Y - 5, wisp ? 48 : 62, wisp ? 9 : 12);
        batch.Draw(Game1.staminaRect, shadow, Color.Black * (wisp ? 0.18f : 0.27f));
        batch.Draw(texture, local, src, Color.White, 0f, new Vector2(16f, 27f), scale, SpriteEffects.None, layer);

        // Summons are real killable enemies. A compact bar confirms hits without prop-like clutter.
        float hp = add.MaxHealth <= 0 ? 0f : Math.Clamp(add.Health / (float)add.MaxHealth, 0f, 1f);
        int hpW = wisp ? 38 : 44;
        int hpX = (int)local.X - hpW / 2;
        int hpY = (int)local.Y + 5;
        batch.Draw(Game1.staminaRect, new Rectangle(hpX, hpY, hpW, 4), Color.Black * 0.62f);
        batch.Draw(Game1.staminaRect, new Rectangle(hpX + 1, hpY + 1, Math.Max(1, (int)((hpW - 2) * hp)), 2), new Color(178, 224, 122) * 0.90f);

        if (wisp)
        {
            float pulse = 0.35f + 0.18f * (float)Math.Abs(Math.Sin(now / 120d));
            int r = 9 + (int)(3 * Math.Abs(Math.Sin(now / 140d)));
            batch.Draw(Game1.staminaRect, new Rectangle((int)local.X-r, (int)local.Y-48-r, r*2, r*2), new Color(137, 247, 126) * pulse);
            batch.Draw(texture, local, src, Color.White * 0.86f, 0f, new Vector2(16f, 27f), scale, SpriteEffects.None, Math.Min(0.995f, layer + 0.0003f));
        }
    }

    public void OnReturnedToTitle(object? sender, ReturnedToTitleEventArgs e)
    {
        foreach (Texture2D? texture in this.Textures.Values)
            texture?.Dispose();
        this.Textures.Clear();
        this.Failed.Clear();
    }

    public string Describe()
    {
        string living = string.Join(",", this.Boss.VisualAdds.Select(m =>
            m.modData.TryGetValue(VerdantGuardianBossService.BossAddTypeKey, out string? kind) ? kind : "unknown"));
        return $"CustomSummons=ON | Living=[{living}] | Pending={this.Boss.VisualSummonTargets.Length} | EngineActorsVisible=YES | ProxyDrawHidden=YES | Killable=YES | FailedAssets={this.Failed.Count}";
    }

    private Texture2D? Load(string file)
    {
        if (this.Textures.TryGetValue(file, out Texture2D? cached)) return cached;
        if (this.Failed.Contains(file)) return null;
        try
        {
            Texture2D texture = this.Helper.ModContent.Load<Texture2D>($"{AssetRoot}/{file}");
            this.Textures[file] = texture;
            return texture;
        }
        catch (Exception ex)
        {
            if (this.Failed.Add(file))
                this.Monitor.Log($"Verdant summon visual asset '{file}' unavailable: {ex.GetType().Name}: {ex.Message}", LogLevel.Warn);
            this.Textures[file] = null;
            return null;
        }
    }
}
