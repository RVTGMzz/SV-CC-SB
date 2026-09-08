from pathlib import Path
from PIL import Image, ImageDraw
import json, re

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.31'

# ---------------- version ----------------
manifest_path = ROOT / 'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['Version'] = VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

for rel in ['Cardcha.csproj', 'Directory.Build.targets']:
    p = ROOT / rel
    s = p.read_text(encoding='utf-8')
    s = re.sub(r'0\.3\.0-alpha\.28\.0\.4\.14\.4\.5\.12\.30', VERSION, s)
    p.write_text(s, encoding='utf-8')

# Keep the TMX itself stable, only stamp the build/property version. No tile/collision changes in 0664.
tmx_path = ROOT / 'assets' / 'verdant_guardian_arena.tmx'
tmx = tmx_path.read_text(encoding='utf-8')
tmx = re.sub(r'(<property name="CardchaRegionVersion" value=")[^"]+(" />)', rf'\g<1>{VERSION}\2', tmx, count=1)
tmx_path.write_text(tmx, encoding='utf-8')

# ---------------- Cardcha-owned arena polish art ----------------
asset_dir = ROOT / 'assets' / 'bosses' / 'verdant_guardian' / 'arena'
asset_dir.mkdir(parents=True, exist_ok=True)

OUTLINE = (28, 43, 32, 255)
BARK = (97, 69, 45, 255)
BARK_HI = (145, 105, 63, 255)
STONE = (77, 89, 75, 255)
STONE_HI = (121, 137, 111, 255)
LEAF = (57, 132, 68, 255)
LEAF_HI = (116, 205, 98, 255)
CORE = (128, 244, 118, 255)
CORE_HI = (231, 255, 178, 255)

# A subtle arena seal, meant to sit under the boss and never replace combat telegraphs.
seal = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
d = ImageDraw.Draw(seal)
for r, alpha, width in [(57, 50, 2), (48, 82, 2), (34, 105, 2)]:
    d.ellipse((64-r, 64-r, 64+r, 64+r), outline=(112, 229, 108, alpha), width=width)
for angle in range(0, 360, 45):
    import math
    a = math.radians(angle)
    x1, y1 = 64 + int(math.cos(a)*38), 64 + int(math.sin(a)*38)
    x2, y2 = 64 + int(math.cos(a)*51), 64 + int(math.sin(a)*51)
    d.line((x1, y1, x2, y2), fill=(78, 174, 83, 95), width=2)
# root spokes and a crystalline heart motif
for pts in [
    [(64,22),(59,42),(64,50),(69,42)],
    [(106,64),(86,59),(78,64),(86,69)],
    [(64,106),(59,86),(64,78),(69,86)],
    [(22,64),(42,59),(50,64),(42,69)],
]:
    d.polygon(pts, fill=(67, 154, 73, 80))
d.polygon([(64,43),(76,59),(72,78),(64,87),(56,78),(52,59)], fill=(83, 186, 86, 105), outline=(181,245,146,135))
d.ellipse((60,58,68,66), fill=(228,255,178,155))
seal.save(asset_dir / 'verdant_arena_seal.png')

# Four rooted standing-stones around the outside of the fight space.
obelisk = Image.new('RGBA', (32, 64), (0, 0, 0, 0))
d = ImageDraw.Draw(obelisk)
d.ellipse((5,57,27,63), fill=(18,29,21,90))
d.polygon([(16,4),(24,13),(23,45),(19,54),(10,54),(7,45),(8,13)], fill=OUTLINE)
d.polygon([(16,6),(22,14),(21,43),(18,51),(11,51),(9,43),(10,14)], fill=STONE)
d.line((14,10,12,43), fill=STONE_HI, width=2)
d.line((18,14,20,36), fill=(56,72,58,255), width=1)
d.polygon([(16,18),(21,26),(16,34),(11,26)], fill=(65,145,72,255), outline=LEAF_HI)
d.line((16,19,16,33), fill=CORE_HI, width=1)
# roots hugging the base
d.line((12,49,6,58), fill=BARK, width=3)
d.line((18,49,26,58), fill=BARK, width=3)
d.line((14,50,11,61), fill=BARK_HI, width=2)
d.line((19,50,21,61), fill=BARK_HI, width=2)
d.polygon([(8,20),(4,17),(6,24)], fill=LEAF)
d.polygon([(23,28),(29,24),(26,31)], fill=LEAF_HI)
obelisk.save(asset_dir / 'verdant_arena_obelisk.png')

# Exit/retreat glyph, intentionally calm and readable rather than flashy.
retreat = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
d = ImageDraw.Draw(retreat)
d.ellipse((6,34,58,54), outline=(111, 219, 116, 115), width=2)
d.ellipse((14,39,50,50), outline=(171, 242, 142, 130), width=2)
d.polygon([(32,17),(40,30),(35,30),(35,42),(29,42),(29,30),(24,30)], fill=(123, 224, 112, 150), outline=(222,255,182,180))
d.polygon([(15,41),(8,37),(11,45)], fill=(62, 139, 68, 135))
d.polygon([(49,41),(56,37),(53,45)], fill=(91, 177, 78, 135))
retreat.save(asset_dir / 'verdant_retreat_glyph.png')

# ---------------- cinematic / camera / sound polish service ----------------
service = r'''using Microsoft.Xna.Framework;
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
'''
(ROOT / 'Services' / 'VerdantGuardianArenaPolishService.cs').write_text(service, encoding='utf-8')

# ---------------- ModEntry wiring ----------------
mod_path = ROOT / 'ModEntry.cs'
mod = mod_path.read_text(encoding='utf-8')
mod = mod.replace(
    '    private VerdantGuardianSummonVisualService VerdantSummons = null!;\n',
    '    private VerdantGuardianSummonVisualService VerdantSummons = null!;\n    private VerdantGuardianArenaPolishService VerdantArenaPolish = null!;\n',
    1
)
mod = mod.replace(
    '        this.VerdantSummons = new VerdantGuardianSummonVisualService(helper, this.Monitor, this.VerdantGuardian);\n',
    '        this.VerdantSummons = new VerdantGuardianSummonVisualService(helper, this.Monitor, this.VerdantGuardian);\n        this.VerdantArenaPolish = new VerdantGuardianArenaPolishService(helper, this.Monitor, this.VerdantGuardian);\n',
    1
)
mod = mod.replace(
    '        helper.Events.GameLoop.UpdateTicked += this.VerdantGuardian.OnUpdateTicked;\n',
    '        helper.Events.GameLoop.UpdateTicked += this.VerdantGuardian.OnUpdateTicked;\n        helper.Events.GameLoop.UpdateTicked += this.VerdantArenaPolish.OnUpdateTicked;\n',
    1
)
mod = mod.replace(
    '        helper.Events.GameLoop.ReturnedToTitle += this.VerdantSummons.OnReturnedToTitle;\n',
    '        helper.Events.GameLoop.ReturnedToTitle += this.VerdantSummons.OnReturnedToTitle;\n        helper.Events.GameLoop.ReturnedToTitle += this.VerdantArenaPolish.OnReturnedToTitle;\n',
    1
)
mod = mod.replace(
    '        helper.Events.Display.RenderedHud += this.VerdantGuardian.OnRenderedHud;\n',
    '        helper.Events.Display.RenderedHud += this.VerdantGuardian.OnRenderedHud;\n        helper.Events.Display.RenderedHud += this.VerdantArenaPolish.OnRenderedHud;\n',
    1
)
mod = mod.replace(
    '        helper.Events.Display.RenderedWorld += this.VerdantGuardian.OnRenderedWorld;\n',
    '        helper.Events.Display.RenderedWorld += this.VerdantArenaPolish.OnRenderedWorld;\n        helper.Events.Display.RenderedWorld += this.VerdantGuardian.OnRenderedWorld;\n',
    1
)
mod = mod.replace(
    '        helper.Events.Player.Warped += this.VerdantGuardian.OnWarped;\n',
    '        helper.Events.Player.Warped += this.VerdantGuardian.OnWarped;\n        helper.Events.Player.Warped += this.VerdantArenaPolish.OnWarped;\n',
    1
)
mod = mod.replace(
    '        helper.ConsoleCommands.Add("cardcha_boss1_visual_status", "Show Verdant Guardian visual animation state.", (_, _) => this.Monitor.Log(this.VerdantGuardianVisual.Describe(), LogLevel.Alert));\n',
    '        helper.ConsoleCommands.Add("cardcha_boss1_visual_status", "Show Verdant Guardian visual animation state.", (_, _) => this.Monitor.Log(this.VerdantGuardianVisual.Describe(), LogLevel.Alert));\n        helper.ConsoleCommands.Add("cardcha_boss1_polish_status", "Show Verdant arena cinematic/camera/sound polish state.", (_, _) => this.Monitor.Log(this.VerdantArenaPolish.Describe(), LogLevel.Alert));\n',
    1
)
mod = mod.replace(
    '0.3.0-alpha.28.0.4.14.4.5.12.30 VERDANT CUSTOM SUMMONS TEST',
    '0.3.0-alpha.28.0.4.14.4.5.12.31 VERDANT ARENA CINEMATIC POLISH TEST',
    1
)
mod_path.write_text(mod, encoding='utf-8')

# ---------------- i18n ----------------
def add_i18n(path: Path, values: dict):
    data = json.loads(path.read_text(encoding='utf-8'))
    data.update(values)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

add_i18n(ROOT / 'i18n' / 'default.json', {
    'boss.verdant.cinematic.title': 'VERDANT GUARDIAN',
    'boss.verdant.cinematic.subtitle': 'Ancient roots stir beneath the arena.',
    'boss.verdant.cinematic.phase': 'VERDANT RESONANCE • PHASE {{phase}}'
})
add_i18n(ROOT / 'i18n' / 'vi.json', {
    'boss.verdant.cinematic.title': 'VERDANT GUARDIAN',
    'boss.verdant.cinematic.subtitle': 'Những bộ rễ cổ xưa đang thức giấc dưới đấu trường.',
    'boss.verdant.cinematic.phase': 'CỘNG HƯỞNG VERDANT • PHASE {{phase}}'
})

# ---------------- handoff ----------------
Path('handoff/ALPHA28_0664_VERDANT_ARENA_CINEMATIC_POLISH.md').write_text(f'''# Alpha28 0664 - Verdant Arena / Intro / Camera / Sound Polish\n\nBuild: `{VERSION}`\nBranch: `cardcha-alpha28-0664-verdant-arena-cinematic-polish`\nStatus: implementation candidate, in-game acceptance pending. 0660-0663 acceptance remains pending because the user continued before testing.\n\n## Arena polish\n- No collision or room geometry changes. The existing 28x20 TMX is preserved; only its CardchaRegionVersion property is stamped to this build.\n- Adds a subtle Cardcha-owned Verdant seal beneath the boss, four rooted obelisks outside the main fight lane, ambient green motes and a readable retreat glyph at the existing retreat tile.\n- These are rendering-only assets and do not alter hitboxes, summon tiles or telegraph geometry.\n\n## Intro polish\n- Keeps the existing 1500 ms authoritative Intro state exactly unchanged.\n- Adds cinematic letterbox bars, a centered VERDANT GUARDIAN title and bilingual subtitle, with fade-in/out inside that same 1500 ms window.\n- Phase transitions receive a short centered resonance label without changing phase timing.\n\n## Camera polish\n- Presentation-only camera shake on intro footfall/core wake, phase shift, charge impact, root eruption, area slam and defeat.\n- Camera offset is explicitly restored before each new tick and on warp/title cleanup so shake cannot accumulate into camera drift.\n- Camera shake never writes boss/player positions or combat state.\n\n## Sound polish\n- Uses only vanilla cues already used safely by Cardcha/Stardew (`thudStep`, `leafrustle`, `discoverMineral`, `yoba`).\n- Layered cues are keyed to authoritative states/elapsed time; no external audio dependency is added.\n\n## Debug\n- `cardcha_boss1_polish_status` reports arena state, active camera offset, shake count, sound cue count and last impact reason.\n- Enter through `cardcha_test_boss1` to replay the normal intro automatically.\n\n## Locked systems preserved\n- Boss I HP 1300 and all attack damage/cooldowns remain unchanged.\n- Boss Intro remains 1500 ms; defeat remains 2200 ms.\n- 0660 Colossus visuals and heavy anchor unchanged.\n- 0661 Verdant Core Boss Card unchanged.\n- 0662 Guardian Rabbit stays exactly 10 sec and Boss Energy stays x1/3.\n- 0663 Briarling/Leaf Wisp custom summon runtime and cap 4 unchanged.\n- Save schema 19, 20/40/60/80 milestones, 76 active normal-card audit / 80 stored base IDs, MiMi stair/profile/CC work, Hunt Run, Airship route/upgrades and controller mapping unchanged.\n''', encoding='utf-8')

Path('handoff/LATEST_CARDCHA_HANDOFF.md').write_text(f'''# Latest Cardcha handoff\n\nCurrent branch: `cardcha-alpha28-0664-verdant-arena-cinematic-polish`\nCurrent build: `{VERSION}`\n\nContinue from:\n`handoff/ALPHA28_0664_VERDANT_ARENA_CINEMATIC_POLISH.md`\n\n0660/0661/0662/0663/0664 in-game acceptance is pending. Do not resume from stale `main`.\n''', encoding='utf-8')

print(json.dumps({
    'version': VERSION,
    'arena': 'seal + 4 obelisks + motes + retreat glyph',
    'introMs': 1500,
    'camera': 'restored-offset shake',
    'sound': ['thudStep', 'leafrustle', 'discoverMineral', 'yoba'],
    'balanceChanged': False,
    'schema': 19
}, indent=2))
