using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Monsters;

namespace Cardcha.Services;

/// <summary>
/// 0660 visual-complete + Colossus pass. Combat timing remains authoritative in
/// VerdantGuardianBossService; this layer only maps state/elapsed time to Cardcha art and FX.
/// </summary>
internal sealed class VerdantGuardianVisualService
{
    private const int FrameSize = 64;
    private const float DrawScale = 8f; // user-approved x2 visual size from the 0652 4x prototype
    private const float FxScale = 3.25f;
    private static readonly Vector2 FrameOrigin = new(32f, 58f);
    private const string AssetRoot = "assets/bosses/verdant_guardian";

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly VerdantGuardianBossService Boss;
    private readonly Dictionary<string, Texture2D?> Textures = new(StringComparer.OrdinalIgnoreCase);
    private readonly HashSet<string> Failed = new(StringComparer.OrdinalIgnoreCase);
    private VerdantGuardianState LastState = VerdantGuardianState.Dormant;
    private int LastHealth = -1;
    private long HurtUntilMs;
    private long ChargeEndUntilMs;

    private sealed record Clip(string Key, string File, int Frames, int DurationMs, bool Loop);

    private static readonly Dictionary<string, Clip> Clips = new(StringComparer.OrdinalIgnoreCase)
    {
        ["idle"] = new("idle", "boss1_verdant_guardian_idle.png", 6, 1200, true),
        ["intro"] = new("intro", "boss1_verdant_guardian_intro_awaken.png", 10, 1500, false),
        ["swipe"] = new("swipe", "boss1_verdant_guardian_swipe_attack.png", 9, 700, false),
        ["root"] = new("root", "boss1_verdant_guardian_root_cast.png", 8, 900, false),
        ["summon"] = new("summon", "boss1_verdant_guardian_summon_cast.png", 10, 600, false),
        ["charge_prep"] = new("charge_prep", "boss1_verdant_guardian_charge_prep.png", 7, 900, false),
        ["charge_loop"] = new("charge_loop", "boss1_verdant_guardian_charge_loop.png", 3, 360, true),
        ["charge_end"] = new("charge_end", "boss1_verdant_guardian_charge_end.png", 4, 240, false),
        ["vine"] = new("vine", "boss1_verdant_guardian_vine_cast.png", 8, 900, false),
        ["slam"] = new("slam", "boss1_verdant_guardian_slam_attack.png", 11, 1100, false),
        ["phase"] = new("phase", "boss1_verdant_guardian_phase_shift.png", 12, 1600, false),
        ["hurt"] = new("hurt", "boss1_verdant_guardian_hurt.png", 3, 180, false),
        ["defeat"] = new("defeat", "boss1_verdant_guardian_defeat.png", 12, 2200, false),
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
        if (actor is null)
            return;

        long now = Environment.TickCount64;
        VerdantGuardianState state = this.Boss.VisualState;
        if (this.LastState == VerdantGuardianState.Charging && state == VerdantGuardianState.Decision)
            this.ChargeEndUntilMs = now + 240;
        if (this.LastHealth >= 0 && actor.Health < this.LastHealth && actor.Health > 0 && state == VerdantGuardianState.Decision)
            this.HurtUntilMs = now + 180;
        this.LastHealth = actor.Health;
        this.LastState = state;

        this.DrawCombatFx(e.SpriteBatch, state, now, actor);
        if (state == VerdantGuardianState.Victory)
            return;

        Clip clip = this.ResolveClip(state, now);
        Texture2D? texture = this.Load(clip.File);
        if (texture is null)
            return;

        long elapsed = clip.Key switch
        {
            "hurt" => Math.Max(0L, 180L - (this.HurtUntilMs - now)),
            "charge_end" => Math.Max(0L, 240L - (this.ChargeEndUntilMs - now)),
            _ => Math.Max(0L, now - this.Boss.VisualStateStartedAtMs),
        };
        int frame = ResolveFrame(clip, elapsed);
        Rectangle source = new(frame * FrameSize, 0, FrameSize, FrameSize);
        if (source.Right > texture.Width || source.Bottom > texture.Height)
        {
            this.LogFailureOnce(clip.File, $"sheet dimensions {texture.Width}x{texture.Height} cannot supply frame {frame}/{clip.Frames}");
            return;
        }

        Vector2 feetWorld = actor.Position + new Vector2(32f, 58f);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, feetWorld);
        float phaseScale = this.Boss.VisualPhase switch { 1 => 1f, 2 => 1.025f, _ => 1.05f };
        Color tint = this.Boss.VisualPhase switch
        {
            1 => new Color(242, 238, 220),
            2 => new Color(230, 244, 210),
            _ => new Color(224, 248, 198),
        };

        int shadowWidth = 255 + this.Boss.VisualPhase * 18;
        Rectangle shadow = new((int)local.X - shadowWidth/2, (int)local.Y - 22, shadowWidth, 42);
        e.SpriteBatch.Draw(Game1.staminaRect, shadow, Color.Black * 0.32f);

        float layer = Math.Clamp((actor.Position.Y + 128f) / 10000f, 0f, 0.99f);
        e.SpriteBatch.Draw(texture, local, source, tint, 0f, FrameOrigin, DrawScale * phaseScale, SpriteEffects.None, layer);

        if (state != VerdantGuardianState.Defeated)
        {
            Texture2D? glow = this.Load("boss1_verdant_guardian_core_glow.png");
            if (glow is not null && glow.Width >= FrameSize * 6 && glow.Height >= FrameSize)
            {
                int glowFrame = (int)((now / 115L) % 6L);
                Rectangle glowSource = new(glowFrame * FrameSize, 0, FrameSize, FrameSize);
                float glowAlpha = this.Boss.VisualPhase switch { 1 => 0.42f, 2 => 0.68f, _ => 0.94f };
                e.SpriteBatch.Draw(glow, local, glowSource, Color.White * glowAlpha, 0f, FrameOrigin,
                    DrawScale * phaseScale, SpriteEffects.None, Math.Min(0.995f, layer + 0.0005f));
            }
        }

        if (state == VerdantGuardianState.Defeated)
            this.DrawReleasedCore(e.SpriteBatch, now, actor, layer);
    }

    private Clip ResolveClip(VerdantGuardianState state, long now)
    {
        if (state == VerdantGuardianState.Decision && now < this.HurtUntilMs)
            return Clips["hurt"];
        if (state == VerdantGuardianState.Decision && now < this.ChargeEndUntilMs)
            return Clips["charge_end"];
        return state switch
        {
            VerdantGuardianState.Intro => Clips["intro"],
            VerdantGuardianState.SwipeTelegraph => Clips["swipe"],
            VerdantGuardianState.RootSpikesTelegraph => Clips["root"],
            VerdantGuardianState.SummonAdds => Clips["summon"],
            VerdantGuardianState.ChargeTelegraph => Clips["charge_prep"],
            VerdantGuardianState.Charging => Clips["charge_loop"],
            VerdantGuardianState.VineTrapTelegraph => Clips["vine"],
            VerdantGuardianState.VineTrapActive => Clips["vine"],
            VerdantGuardianState.AreaSlamTelegraph => Clips["slam"],
            VerdantGuardianState.PhaseTransition => Clips["phase"],
            VerdantGuardianState.Defeated => Clips["defeat"],
            _ => Clips["idle"],
        };
    }

    private void DrawCombatFx(SpriteBatch batch, VerdantGuardianState state, long now, Monster actor)
    {
        long elapsed = Math.Max(0L, now - this.Boss.VisualStateStartedAtMs);
        switch (state)
        {
            case VerdantGuardianState.RootSpikesTelegraph:
                foreach (Point tile in this.Boss.VisualRootTargets)
                {
                    Vector2 center = new(tile.X * 64f + 32f, tile.Y * 64f + 34f);
                    this.DrawFx(batch, "fx_boss1_root_warning.png", 4, elapsed, 900, center, 1.45f, 0.82f);
                    if (elapsed >= 650)
                        this.DrawFx(batch, "fx_boss1_root_erupt.png", 5, elapsed - 650, 250, center, 1.75f, 0.94f);
                }
                break;
            case VerdantGuardianState.SummonAdds:
                this.DrawFx(batch, "fx_boss1_leaf_burst.png", 6, elapsed, 600, this.Boss.VisualBossCenter, 2.25f, 0.86f);
                break;
            case VerdantGuardianState.VineTrapTelegraph:
            case VerdantGuardianState.VineTrapActive:
                Point vine = this.Boss.VisualVineTarget;
                this.DrawFx(batch, "fx_boss1_vine_trap.png", 6, elapsed, state == VerdantGuardianState.VineTrapActive ? 900 : 900,
                    new Vector2(vine.X * 64f + 32f, vine.Y * 64f + 32f), 2.5f, state == VerdantGuardianState.VineTrapActive ? 0.92f : 0.62f);
                break;
            case VerdantGuardianState.AreaSlamTelegraph:
                this.DrawFx(batch, "fx_boss1_slam_warning.png", 4, elapsed, 900, this.Boss.VisualBossCenter, 4.2f, 0.64f);
                if (elapsed >= 820)
                    this.DrawFx(batch, "fx_boss1_slam_shockwave.png", 5, elapsed - 820, 280, this.Boss.VisualBossCenter, 4.7f, 0.88f);
                break;
            case VerdantGuardianState.PhaseTransition:
                this.DrawFx(batch, "fx_boss1_phase_pulse.png", 6, elapsed, 1600, this.Boss.VisualBossCenter, 4.6f, 0.78f);
                this.DrawFx(batch, "fx_boss1_leaf_burst.png", 6, elapsed, 800, this.Boss.VisualBossCenter, 2.8f, 0.86f);
                break;
        }

        if (this.Boss.VisualPhase >= 2 && state is not VerdantGuardianState.Defeated and not VerdantGuardianState.Victory)
        {
            long aura = now % 1400L;
            float alpha = this.Boss.VisualPhase == 2 ? 0.18f : 0.30f;
            this.DrawFx(batch, "fx_boss1_phase_pulse.png", 6, aura, 1400, this.Boss.VisualBossCenter,
                this.Boss.VisualPhase == 2 ? 3.5f : 4.1f, alpha);
        }
    }

    private void DrawReleasedCore(SpriteBatch batch, long now, Monster actor, float layer)
    {
        Texture2D? fx = this.Load("fx_boss1_core_release.png");
        if (fx is null) return;
        long elapsed = Math.Max(0L, now - this.Boss.VisualStateStartedAtMs);
        int frame = Math.Clamp((int)(elapsed * 6 / 2200), 0, 5);
        Rectangle src = new(frame * FrameSize, 0, FrameSize, FrameSize);
        Vector2 world = actor.Position + new Vector2(32f, 18f - Math.Min(82f, elapsed * 0.035f));
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
        batch.Draw(fx, local, src, Color.White, 0f, new Vector2(32,32), 4.2f, SpriteEffects.None, Math.Min(0.999f, layer + 0.001f));
    }

    private void DrawFx(SpriteBatch batch, string file, int frames, long elapsed, int duration, Vector2 worldCenter, float scale, float alpha)
    {
        Texture2D? texture = this.Load(file);
        if (texture is null || texture.Width < frames * FrameSize) return;
        int frame = Math.Clamp((int)((elapsed % Math.Max(1,duration)) * frames / Math.Max(1,duration)), 0, frames-1);
        Rectangle src = new(frame * FrameSize, 0, FrameSize, FrameSize);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, worldCenter);
        batch.Draw(texture, local, src, Color.White * alpha, 0f, new Vector2(32,32), scale, SpriteEffects.None,
            Math.Clamp((worldCenter.Y + 64f) / 10000f, 0f, 0.985f));
    }

    public void OnReturnedToTitle(object? sender, ReturnedToTitleEventArgs e)
    {
        foreach (Texture2D? texture in this.Textures.Values) texture?.Dispose();
        this.Textures.Clear();
        this.Failed.Clear();
        this.LastState = VerdantGuardianState.Dormant;
        this.LastHealth = -1;
        this.HurtUntilMs = 0;
        this.ChargeEndUntilMs = 0;
    }

    public string Describe()
    {
        Clip clip = this.ResolveClip(this.Boss.VisualState, Environment.TickCount64);
        string loaded = string.Join(",", this.Textures.Where(p => p.Value is not null).Select(p => p.Key));
        return $"State={this.Boss.VisualState} | Clip={clip.Key} | Phase={this.Boss.VisualPhase} | Scale={DrawScale:0.##}x | Colossus=ON | ProxyHidden=ON | Loaded=[{loaded}] | Failed={this.Failed.Count}";
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
            this.LogFailureOnce(file, $"{ex.GetType().Name}: {ex.Message}");
            return null;
        }
    }

    private void LogFailureOnce(string file, string reason)
    {
        if (!this.Failed.Add(file)) return;
        this.Textures[file] = null;
        this.Monitor.Log($"Verdant Guardian visual asset '{file}' unavailable. {reason}", LogLevel.Warn);
    }

    private static int ResolveFrame(Clip clip, long elapsedMs)
    {
        if (clip.Frames <= 1) return 0;
        if (clip.Loop)
        {
            long duration = Math.Max(1, clip.DurationMs);
            return Math.Clamp((int)((elapsedMs % duration) * clip.Frames / duration), 0, clip.Frames - 1);
        }
        long clamped = Math.Clamp(elapsedMs, 0L, Math.Max(1, clip.DurationMs) - 1L);
        return Math.Clamp((int)(clamped * clip.Frames / Math.Max(1, clip.DurationMs)), 0, clip.Frames - 1);
    }
}
