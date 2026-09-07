using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Monsters;

namespace Cardcha.Services;

/// <summary>
/// Alpha28 0652 visual-only animation layer for Verdant Guardian.
/// Combat timing stays authoritative in VerdantGuardianBossService; this class only observes
/// state/elapsed time and draws Cardcha-owned sprite sheets over the vanilla gameplay proxy.
/// Missing/corrupt art fails soft: the proxy remains visible and the fight stays playable.
/// </summary>
internal sealed class VerdantGuardianVisualService
{
    private const int FrameSize = 64;
    private const float DrawScale = 4f;
    private static readonly Vector2 FrameOrigin = new(32f, 58f);
    private const string AssetRoot = "assets/bosses/verdant_guardian";

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly VerdantGuardianBossService Boss;
    private readonly Dictionary<string, Texture2D?> Textures = new(StringComparer.OrdinalIgnoreCase);
    private readonly HashSet<string> Failed = new(StringComparer.OrdinalIgnoreCase);

    private sealed record Clip(string Key, string File, int Frames, int DurationMs, bool Loop);

    private static readonly Dictionary<string, Clip> Clips = new(StringComparer.OrdinalIgnoreCase)
    {
        ["idle"] = new("idle", "boss1_verdant_guardian_idle.png", 6, 900, true),
        ["intro"] = new("intro", "boss1_verdant_guardian_intro_awaken.png", 10, 1500, false),
        ["swipe"] = new("swipe", "boss1_verdant_guardian_swipe_attack.png", 9, 700, false),
        ["root"] = new("root", "boss1_verdant_guardian_root_cast.png", 8, 900, false),
    };

    public VerdantGuardianVisualService(IModHelper helper, IMonitor monitor, VerdantGuardianBossService boss)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Boss = boss;
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        if (!this.Boss.IsInArena)
            return;

        Monster? actor = this.Boss.VisualBoss;
        if (actor is null || actor.Health <= 0)
            return;

        Clip clip = ResolveClip(this.Boss.VisualState);
        Texture2D? texture = this.Load(clip.File);
        if (texture is null)
            return;

        long elapsed = Math.Max(0L, Environment.TickCount64 - this.Boss.VisualStateStartedAtMs);
        int frame = ResolveFrame(clip, elapsed);
        Rectangle source = new(frame * FrameSize, 0, FrameSize, FrameSize);
        if (source.Right > texture.Width || source.Bottom > texture.Height)
        {
            this.LogFailureOnce(clip.File, $"sheet dimensions {texture.Width}x{texture.Height} cannot supply frame {frame}/{clip.Frames}");
            return;
        }

        Vector2 feetWorld = actor.Position + new Vector2(32f, 58f);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, feetWorld);
        float phaseScale = this.Boss.VisualPhase switch { 1 => 1f, 2 => 1.035f, _ => 1.07f };
        Color tint = this.Boss.VisualPhase switch
        {
            1 => Color.White,
            2 => new Color(244, 255, 238),
            _ => new Color(236, 255, 222),
        };

        Rectangle shadow = new((int)local.X - 70, (int)local.Y - 17, 140, 32);
        e.SpriteBatch.Draw(Game1.staminaRect, shadow, Color.Black * 0.22f);

        e.SpriteBatch.Draw(
            texture,
            local,
            source,
            tint,
            0f,
            FrameOrigin,
            DrawScale * phaseScale,
            SpriteEffects.None,
            Math.Clamp((actor.Position.Y + 128f) / 10000f, 0f, 0.99f)
        );

        Texture2D? glow = this.Load("boss1_verdant_guardian_core_glow.png");
        if (glow is not null && glow.Width >= FrameSize * 6 && glow.Height >= FrameSize)
        {
            int glowFrame = (int)((Environment.TickCount64 / 110L) % 6L);
            Rectangle glowSource = new(glowFrame * FrameSize, 0, FrameSize, FrameSize);
            float glowAlpha = this.Boss.VisualPhase switch { 1 => 0.55f, 2 => 0.72f, _ => 0.92f };
            e.SpriteBatch.Draw(
                glow,
                local,
                glowSource,
                Color.White * glowAlpha,
                0f,
                FrameOrigin,
                DrawScale * phaseScale,
                SpriteEffects.None,
                Math.Clamp((actor.Position.Y + 129f) / 10000f, 0f, 0.995f)
            );
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
        Clip clip = ResolveClip(this.Boss.VisualState);
        string loaded = string.Join(",", this.Textures.Where(p => p.Value is not null).Select(p => p.Key));
        return $"State={this.Boss.VisualState} | Clip={clip.Key} | Phase={this.Boss.VisualPhase} | Scale={DrawScale:0.##}x | Loaded=[{loaded}] | Failed={this.Failed.Count}";
    }

    private Texture2D? Load(string file)
    {
        if (this.Textures.TryGetValue(file, out Texture2D? cached))
            return cached;
        if (this.Failed.Contains(file))
            return null;

        try
        {
            Texture2D texture = this.Helper.ModContent.Load<Texture2D>($"{AssetRoot}/{file}");
            this.Textures[file] = texture;
            return texture;
        }
        catch (Exception ex)
        {
            this.LogFailureOnce(file, $"{ex.GetType().Name}: {ex.Message}");
            return null;
        }
    }

    private void LogFailureOnce(string file, string reason)
    {
        if (!this.Failed.Add(file))
            return;
        this.Textures[file] = null;
        this.Monitor.Log($"Verdant Guardian visual asset '{file}' unavailable; vanilla boss proxy remains as fallback. {reason}", LogLevel.Warn);
    }

    private static Clip ResolveClip(VerdantGuardianState state)
        => state switch
        {
            VerdantGuardianState.Intro => Clips["intro"],
            VerdantGuardianState.SwipeTelegraph => Clips["swipe"],
            VerdantGuardianState.RootSpikesTelegraph => Clips["root"],
            _ => Clips["idle"],
        };

    private static int ResolveFrame(Clip clip, long elapsedMs)
    {
        if (clip.Frames <= 1)
            return 0;
        if (clip.Loop)
        {
            long duration = Math.Max(1, clip.DurationMs);
            long local = elapsedMs % duration;
            return Math.Clamp((int)(local * clip.Frames / duration), 0, clip.Frames - 1);
        }

        long clamped = Math.Clamp(elapsedMs, 0L, Math.Max(1, clip.DurationMs) - 1L);
        return Math.Clamp((int)(clamped * clip.Frames / Math.Max(1, clip.DurationMs)), 0, clip.Frames - 1);
    }
}
