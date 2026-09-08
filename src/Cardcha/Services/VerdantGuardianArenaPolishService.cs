using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// 0664 presentation-only pass for Boss I. Arena dressing, intro title, camera impact and
/// layered vanilla sound cues live here so the authoritative boss state machine and balance
/// values remain untouched.
/// </summary>
internal sealed class VerdantGuardianArenaPolishService
{
    private const string ArenaAssetRoot = "assets/bosses/verdant_guardian/arena";
    private static readonly Point RetreatTile = new(14, 18);
    private static readonly Point[] ObeliskTiles =
    {
        new(3, 3), new(24, 3), new(3, 16), new(24, 16)
    };

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly VerdantGuardianBossService Boss;
    private readonly Dictionary<string, Texture2D?> Textures = new(StringComparer.OrdinalIgnoreCase);
    private readonly HashSet<string> Failed = new(StringComparer.OrdinalIgnoreCase);
    private readonly Random CameraRandom = new(0x664C0DE);

    private VerdantGuardianState LastState = VerdantGuardianState.Dormant;
    private Point AppliedCameraOffset = Point.Zero;
    private long ShakeUntilMs;
    private int ShakeMagnitude;
    private bool IntroLeafCue;
    private bool IntroCoreCue;
    private bool PhaseCoreCue;
    private bool DefeatLeafCue;
    private bool DefeatCoreCue;
    private bool DefeatFinalCue;

    public long CameraShakeCount { get; private set; }
    public long SoundCueCount { get; private set; }
    public string LastSoundCue { get; private set; } = "none";
    public string LastImpact { get; private set; } = "none";

    public VerdantGuardianArenaPolishService(IModHelper helper, IMonitor monitor, VerdantGuardianBossService boss)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Boss = boss;
    }

    public void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)
    {
        // Never accumulate offsets. Remove only the offset this service applied on its previous tick.
        this.RestoreCameraOffset();

        if (!Context.IsWorldReady || !this.Boss.IsInArena)
        {
            this.ResetEncounterFlags();
            return;
        }

        long now = Environment.TickCount64;
        VerdantGuardianState state = this.Boss.VisualState;
        if (state != this.LastState)
        {
            this.OnStateChanged(this.LastState, state, now);
            this.LastState = state;
        }

        long elapsed = Math.Max(0L, now - this.Boss.VisualStateStartedAtMs);
        switch (state)
        {
            case VerdantGuardianState.Intro:
                if (!this.IntroLeafCue && elapsed >= 480)
                {
                    this.IntroLeafCue = true;
                    this.PlayCue("leafrustle");
                }
                if (!this.IntroCoreCue && elapsed >= 1050)
                {
                    this.IntroCoreCue = true;
                    this.PlayCue("discoverMineral");
                    this.TriggerShake(5, 280, "intro-core-awaken");
                }
                break;

            case VerdantGuardianState.PhaseTransition:
                if (!this.PhaseCoreCue && elapsed >= 760)
                {
                    this.PhaseCoreCue = true;
                    this.PlayCue("discoverMineral");
                    this.TriggerShake(5, 360, "phase-core-pulse");
                }
                break;

            case VerdantGuardianState.Defeated:
                if (!this.DefeatLeafCue && elapsed >= 420)
                {
                    this.DefeatLeafCue = true;
                    this.PlayCue("leafrustle");
                }
                if (!this.DefeatCoreCue && elapsed >= 1120)
                {
                    this.DefeatCoreCue = true;
                    this.PlayCue("discoverMineral");
                    this.TriggerShake(4, 300, "defeat-core-release");
                }
                if (!this.DefeatFinalCue && elapsed >= 1850)
                {
                    this.DefeatFinalCue = true;
                    this.PlayCue("yoba");
                }
                break;
        }

        this.ApplyCameraShake(now);
    }

    private void OnStateChanged(VerdantGuardianState previous, VerdantGuardianState current, long now)
    {
        if (current == VerdantGuardianState.Intro)
        {
            this.IntroLeafCue = false;
            this.IntroCoreCue = false;
            this.PlayCue("thudStep");
            this.TriggerShake(3, 320, "intro-footfall");
        }

        if (current == VerdantGuardianState.PhaseTransition)
        {
            this.PhaseCoreCue = false;
            this.PlayCue("leafrustle");
            this.TriggerShake(4, 520, "phase-shift");
        }

        if (current == VerdantGuardianState.Defeated)
        {
            this.DefeatLeafCue = false;
            this.DefeatCoreCue = false;
            this.DefeatFinalCue = false;
            this.TriggerShake(8, 520, "guardian-collapse");
        }

        // Impact shakes are presentation only and are keyed off the authoritative state exit.
        if (previous == VerdantGuardianState.Charging && current == VerdantGuardianState.Decision)
        {
            this.PlayCue("thudStep");
            this.TriggerShake(7, 220, "charge-impact");
        }
        else if (previous == VerdantGuardianState.AreaSlamTelegraph && current == VerdantGuardianState.Decision)
        {
            this.PlayCue("thudStep");
            this.TriggerShake(9, 280, "area-slam-impact");
        }
        else if (previous == VerdantGuardianState.RootSpikesTelegraph && current == VerdantGuardianState.Decision)
        {
            this.TriggerShake(3, 160, "root-erupt");
        }
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        if (!Context.IsWorldReady || !this.Boss.IsInArena)
            return;

        this.DrawArenaSeal(e.SpriteBatch);
        this.DrawObelisks(e.SpriteBatch);
        this.DrawRetreatGlyph(e.SpriteBatch);
        this.DrawAmbientMotes(e.SpriteBatch);
    }

    public void OnRenderedHud(object? sender, RenderedHudEventArgs e)
    {
        if (!Context.IsWorldReady || !this.Boss.IsInArena)
            return;

        if (this.Boss.VisualState == VerdantGuardianState.Intro)
            this.DrawIntroPresentation(e.SpriteBatch);
        else if (this.Boss.VisualState == VerdantGuardianState.PhaseTransition)
            this.DrawPhasePresentation(e.SpriteBatch);
    }

    public void OnWarped(object? sender, WarpedEventArgs e)
    {
        this.RestoreCameraOffset();
        if (!e.NewLocation.NameOrUniqueName.Equals(VerdantGuardianBossService.LocationName, StringComparison.OrdinalIgnoreCase))
            this.ResetEncounterFlags();
    }

    public void OnReturnedToTitle(object? sender, ReturnedToTitleEventArgs e)
    {
        this.RestoreCameraOffset();
        foreach (Texture2D? texture in this.Textures.Values)
            texture?.Dispose();
        this.Textures.Clear();
        this.Failed.Clear();
        this.ResetEncounterFlags();
    }

    public string Describe()
        => $"Arena={this.Boss.IsInArena} | State={this.Boss.VisualState} | Phase={this.Boss.VisualPhase} | " +
           $"CameraShakeActive={Environment.TickCount64 < this.ShakeUntilMs} | AppliedOffset={this.AppliedCameraOffset.X},{this.AppliedCameraOffset.Y} | " +
           $"ShakeCount={this.CameraShakeCount} | SoundCues={this.SoundCueCount} | LastSound={this.LastSoundCue} | LastImpact={this.LastImpact} | " +
           $"ArenaSeal=ON | Obelisks=4 | Motes=ON | IntroBars=ON";

    private void DrawArenaSeal(SpriteBatch batch)
    {
        Texture2D? texture = this.Load("verdant_arena_seal.png");
        if (texture is null)
            return;

        Vector2 world = new(14 * 64f + 32f, 8 * 64f + 24f);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
        long now = Environment.TickCount64;
        float pulse = 0.84f + 0.08f * (float)Math.Sin(now / 310d);
        float alpha = this.Boss.VisualPhase switch { 1 => 0.22f, 2 => 0.30f, _ => 0.38f };
        batch.Draw(texture, local, null, Color.White * alpha, 0f,
            new Vector2(texture.Width / 2f, texture.Height / 2f), 3.25f * pulse, SpriteEffects.None, 0.035f);
    }

    private void DrawObelisks(SpriteBatch batch)
    {
        Texture2D? texture = this.Load("verdant_arena_obelisk.png");
        if (texture is null)
            return;

        for (int i = 0; i < ObeliskTiles.Length; i++)
        {
            Point tile = ObeliskTiles[i];
            Vector2 world = new(tile.X * 64f + 32f, tile.Y * 64f + 64f);
            Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
            float alpha = 0.72f + 0.10f * (float)Math.Sin(Environment.TickCount64 / 360d + i);
            batch.Draw(texture, local, null, Color.White * alpha, 0f,
                new Vector2(texture.Width / 2f, texture.Height), 2.8f, SpriteEffects.None,
                Math.Clamp((world.Y + 48f) / 10000f, 0f, 0.94f));
        }
    }

    private void DrawRetreatGlyph(SpriteBatch batch)
    {
        Texture2D? texture = this.Load("verdant_retreat_glyph.png");
        if (texture is null)
            return;

        Vector2 world = new(RetreatTile.X * 64f + 32f, RetreatTile.Y * 64f + 35f);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
        float pulse = 0.90f + 0.08f * (float)Math.Sin(Environment.TickCount64 / 250d);
        batch.Draw(texture, local, null, Color.White * 0.62f, 0f,
            new Vector2(32f, 32f), 1.65f * pulse, SpriteEffects.None, 0.08f);
    }

    private void DrawAmbientMotes(SpriteBatch batch)
    {
        long now = Environment.TickCount64;
        Color[] palette =
        {
            new Color(146, 233, 116),
            new Color(204, 245, 155),
            new Color(91, 178, 80)
        };

        for (int i = 0; i < 16; i++)
        {
            double phase = now * 0.00045 + i * 1.91;
            float x = 3.2f * 64f + (float)((Math.Sin(phase * 0.71 + i) + 1d) * 0.5d) * 21.5f * 64f;
            float y = 2.2f * 64f + (float)((Math.Cos(phase * 0.57 + i * 0.43) + 1d) * 0.5d) * 13.8f * 64f;
            Vector2 local = Game1.GlobalToLocal(Game1.viewport, new Vector2(x, y));
            int size = 2 + (i % 3);
            float alpha = 0.20f + 0.16f * (float)Math.Abs(Math.Sin(phase));
            Color c = palette[i % palette.Length] * alpha;
            batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - size, (int)local.Y, size * 2 + 1, 1), c);
            batch.Draw(Game1.staminaRect, new Rectangle((int)local.X, (int)local.Y - size, 1, size * 2 + 1), c);
        }
    }

    private void DrawIntroPresentation(SpriteBatch batch)
    {
        long elapsed = Math.Max(0L, Environment.TickCount64 - this.Boss.VisualStateStartedAtMs);
        float fadeIn = Math.Clamp(elapsed / 220f, 0f, 1f);
        float fadeOut = 1f - Math.Clamp((elapsed - 1210f) / 290f, 0f, 1f);
        float alpha = Math.Clamp(fadeIn * fadeOut, 0f, 1f);
        if (alpha <= 0.01f)
            return;

        int barH = Math.Clamp(Game1.uiViewport.Height / 10, 58, 104);
        batch.Draw(Game1.staminaRect, new Rectangle(0, 0, Game1.uiViewport.Width, barH), Color.Black * (0.90f * alpha));
        batch.Draw(Game1.staminaRect, new Rectangle(0, Game1.uiViewport.Height - barH, Game1.uiViewport.Width, barH), Color.Black * (0.90f * alpha));

        string title = ModEntry.T("boss.verdant.cinematic.title");
        string subtitle = ModEntry.T("boss.verdant.cinematic.subtitle");
        Vector2 titleSize = Game1.dialogueFont.MeasureString(title);
        Vector2 subtitleSize = Game1.smallFont.MeasureString(subtitle);
        float centerX = Game1.uiViewport.Width / 2f;
        float titleY = barH + 18f;
        batch.DrawString(Game1.dialogueFont, title, new Vector2(centerX - titleSize.X / 2f + 2f, titleY + 2f), Color.Black * (0.75f * alpha));
        batch.DrawString(Game1.dialogueFont, title, new Vector2(centerX - titleSize.X / 2f, titleY), new Color(214, 244, 181) * alpha);
        batch.DrawString(Game1.smallFont, subtitle, new Vector2(centerX - subtitleSize.X / 2f, titleY + titleSize.Y + 4f), new Color(168, 211, 147) * alpha);
    }

    private void DrawPhasePresentation(SpriteBatch batch)
    {
        long elapsed = Math.Max(0L, Environment.TickCount64 - this.Boss.VisualStateStartedAtMs);
        if (elapsed > 1000)
            return;
        float alpha = 1f - Math.Clamp(elapsed / 1000f, 0f, 1f);
        string text = ModEntry.T("boss.verdant.cinematic.phase", new { phase = Math.Min(3, this.Boss.VisualPhase + 1) });
        Vector2 size = Game1.smallFont.MeasureString(text);
        Vector2 pos = new(Game1.uiViewport.Width / 2f - size.X / 2f, 78f);
        batch.Draw(Game1.staminaRect, new Rectangle((int)pos.X - 18, (int)pos.Y - 7, (int)size.X + 36, (int)size.Y + 14), new Color(18, 39, 25) * (0.72f * alpha));
        batch.DrawString(Game1.smallFont, text, pos, new Color(183, 239, 149) * alpha);
    }

    private void TriggerShake(int magnitude, int durationMs, string reason)
    {
        long now = Environment.TickCount64;
        this.ShakeMagnitude = Math.Max(this.ShakeMagnitude, magnitude);
        this.ShakeUntilMs = Math.Max(this.ShakeUntilMs, now + Math.Max(1, durationMs));
        this.CameraShakeCount++;
        this.LastImpact = reason;
    }

    private void ApplyCameraShake(long now)
    {
        if (now >= this.ShakeUntilMs || this.ShakeMagnitude <= 0)
        {
            this.ShakeMagnitude = 0;
            return;
        }

        double remaining = Math.Clamp((this.ShakeUntilMs - now) / 520d, 0.2d, 1d);
        int magnitude = Math.Max(1, (int)Math.Round(this.ShakeMagnitude * remaining));
        int dx = this.CameraRandom.Next(-magnitude, magnitude + 1);
        int dy = this.CameraRandom.Next(-magnitude, magnitude + 1);
        Game1.viewport.X += dx;
        Game1.viewport.Y += dy;
        this.AppliedCameraOffset = new Point(dx, dy);
    }

    private void RestoreCameraOffset()
    {
        if (this.AppliedCameraOffset == Point.Zero)
            return;
        Game1.viewport.X -= this.AppliedCameraOffset.X;
        Game1.viewport.Y -= this.AppliedCameraOffset.Y;
        this.AppliedCameraOffset = Point.Zero;
    }

    private void PlayCue(string cue)
    {
        if (!Context.IsWorldReady)
            return;
        try
        {
            Game1.playSound(cue);
            this.SoundCueCount++;
            this.LastSoundCue = cue;
        }
        catch (Exception ex)
        {
            this.Monitor.Log($"Verdant arena polish couldn't play cue '{cue}': {ex.Message}", LogLevel.Trace);
        }
    }

    private Texture2D? Load(string file)
    {
        if (this.Textures.TryGetValue(file, out Texture2D? cached))
            return cached;
        if (this.Failed.Contains(file))
            return null;
        try
        {
            Texture2D texture = this.Helper.ModContent.Load<Texture2D>($"{ArenaAssetRoot}/{file}");
            this.Textures[file] = texture;
            return texture;
        }
        catch (Exception ex)
        {
            this.Failed.Add(file);
            this.Textures[file] = null;
            this.Monitor.Log($"Verdant arena polish asset '{file}' unavailable: {ex.Message}", LogLevel.Warn);
            return null;
        }
    }

    private void ResetEncounterFlags()
    {
        this.LastState = VerdantGuardianState.Dormant;
        this.IntroLeafCue = false;
        this.IntroCoreCue = false;
        this.PhaseCoreCue = false;
        this.DefeatLeafCue = false;
        this.DefeatCoreCue = false;
        this.DefeatFinalCue = false;
        this.ShakeUntilMs = 0;
        this.ShakeMagnitude = 0;
        this.AppliedCameraOffset = Point.Zero;
    }
}
