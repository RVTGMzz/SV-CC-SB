from pathlib import Path
import json
import re

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.1'


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def write(rel, text):
    (ROOT / rel).write_text(text, encoding='utf-8')


def replace_once(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'{label}: anchor not found')
    return text.replace(old, new, 1)


# Version locks.
manifest = ROOT / 'manifest.json'
data = json.loads(manifest.read_text(encoding='utf-8'))
data['Version'] = VERSION
manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

csproj = ROOT / 'Cardcha.csproj'
s = csproj.read_text(encoding='utf-8')
s = re.sub(r'<Version>[^<]+</Version>', f'<Version>{VERSION}</Version>', s, count=1)
csproj.write_text(s, encoding='utf-8')

(ROOT / 'Directory.Build.targets').write_text(f'''<Project>\n  <PropertyGroup>\n    <Version>{VERSION}</Version>\n  </PropertyGroup>\n\n  <!-- .4.14.4.1 ChaCha Energy aura + unified HUD + chord activation. -->\n  <Target Name="CardchaAlpha28041441Manifest" BeforeTargets="BeforeBuild">\n    <Exec Command="python3 -c &quot;from pathlib import Path; import re; p=Path(r'$(MSBuildProjectDirectory)/manifest.json'); s=p.read_text(encoding='utf-8'); s=re.sub(r'\\&quot;Version\\&quot;\\s*:\\s*\\&quot;[^\\&quot;]+\\&quot;', '\\&quot;Version\\&quot;: \\&quot;{VERSION}\\&quot;', s, count=1); p.write_text(s, encoding='utf-8')&quot;" />\n  </Target>\n</Project>\n''', encoding='utf-8')


# Controller semantic layer: expose semantic buttons as SMAPI SButton values.
s = read('Services/ControllerProfileService.cs')
if 'public SButton GetButton(ControllerAction action)' not in s:
    s = replace_once(
        s,
        '''    public bool IsSkip(Buttons button)\n        => button == this.GetRawButton(ControllerAction.Skip);\n\n''',
        '''    public bool IsSkip(Buttons button)\n        => button == this.GetRawButton(ControllerAction.Skip);\n\n    public SButton GetButton(ControllerAction action)\n        => this.GetRawButton(action) switch\n        {\n            Buttons.A => SButton.ControllerA,\n            Buttons.B => SButton.ControllerB,\n            Buttons.X => SButton.ControllerX,\n            Buttons.Y => SButton.ControllerY,\n            _ => SButton.None\n        };\n\n''',
        'Controller SButton semantic export'
    )
write('Services/ControllerProfileService.cs', s)


# Remove the old separate Boss Energy circular entry. ChaChaBossFormService owns the one unified bar.
s = read('UI/CombatHudRenderer.cs')
pattern = re.compile(
    r'\n        if \(this\.BossEnergy\.CurrentEnergy > 0\.001d \|\| this\.Loadout\.IsEquipped\("victory_charge"\)\)\n        \{\n            entries\.Add\(new HudEntry\(\n                Key: "boss_energy",.*?\n            \)\);\n        \}\n',
    re.S,
)
s, count = pattern.subn('\n', s, count=1)
if count == 0 and 'Key: "boss_energy"' in s:
    raise RuntimeError('Could not remove old Boss Energy circular HUD entry')
write('UI/CombatHudRenderer.cs', s)


# One source of truth for ChaCha energy aura, HUD and activation input.
boss_form = r'''using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;

namespace Cardcha.Services;

/// <summary>
/// Runtime-only ChaCha Boss Form foundation.
/// ChaCha visibly charges through four aura stages, owns one unified Energy HUD, and activates
/// through a semantic controller chord, Left Shift+A on keyboard, or a click on the READY bar.
/// This foundation intentionally grants no combat stat bonuses yet.
/// </summary>
internal sealed class ChaChaBossFormService
{
    public const int BossFormDurationMs = 10000;

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;
    private readonly BossEnergyService BossEnergy;
    private readonly WorldActorService WorldActors;
    private readonly ControllerProfileService Controller;

    private long ActiveUntil;
    private bool ReadyAnnounced;
    private Texture2D? AuraTexture;

    public ChaChaBossFormService(
        IModHelper helper,
        IMonitor monitor,
        SaveService save,
        BossEnergyService bossEnergy,
        WorldActorService worldActors,
        ControllerProfileService controller)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
        this.BossEnergy = bossEnergy;
        this.WorldActors = worldActors;
        this.Controller = controller;
    }

    public bool IsActive => this.ActiveUntil > Environment.TickCount64;
    public bool IsReady => !this.IsActive
                           && this.Save.Data.ChaChaLoaned
                           && this.BossEnergy.CurrentEnergy >= BossEnergyService.MaxEnergy - 0.001d;

    public double SecondsRemaining
        => this.IsActive ? Math.Max(0d, (this.ActiveUntil - Environment.TickCount64) / 1000d) : 0d;

    public int EnergyAuraStage
    {
        get
        {
            if (this.IsActive || this.IsReady)
                return 4;
            double energy = this.BossEnergy.CurrentEnergy;
            if (energy >= 75d) return 3;
            if (energy >= 50d) return 2;
            if (energy >= 25d) return 1;
            return 0;
        }
    }

    public void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)
    {
        if (!Context.IsWorldReady)
            return;

        long now = Environment.TickCount64;
        if (this.ActiveUntil > 0 && now >= this.ActiveUntil)
        {
            this.EndBossForm("timer");
            return;
        }

        if (this.IsActive)
        {
            this.WorldActors.SetChaChaBossVisual(true);
            return;
        }

        this.WorldActors.SetChaChaBossVisual(false);

        if (!this.IsReady)
        {
            this.ReadyAnnounced = false;
            return;
        }

        if (!this.ReadyAnnounced)
        {
            this.ReadyAnnounced = true;
            Game1.playSound("yoba");
            this.WorldActors.TriggerChaChaEmote(56);
            this.Monitor.Log("ChaCha Boss Form READY: ChaCha Energy reached 100.", LogLevel.Info);
        }
    }

    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady || !this.IsReady || !this.CanAcceptActivationInput())
            return;

        if (e.Button == SButton.MouseLeft)
        {
            Vector2 cursor = this.Helper.Input.GetCursorPosition().ScreenPixels;
            if (this.GetEnergyHudRect().Contains((int)cursor.X, (int)cursor.Y))
            {
                this.Helper.Input.Suppress(e.Button);
                this.TryActivate("ChaCha Energy HUD click");
            }
            return;
        }

        SButton confirm = this.Controller.GetButton(ControllerAction.Confirm);
        SButton deselect = this.Controller.GetButton(ControllerAction.Deselect);
        bool controllerCandidate = e.Button == confirm || e.Button == deselect;
        bool controllerChord = controllerCandidate
                               && confirm != SButton.None
                               && deselect != SButton.None
                               && this.Helper.Input.IsDown(confirm)
                               && this.Helper.Input.IsDown(deselect);

        if (controllerChord)
        {
            this.Helper.Input.Suppress(confirm);
            this.Helper.Input.Suppress(deselect);
            this.TryActivate($"{this.Controller.GetLabel(ControllerAction.Confirm)}+{this.Controller.GetLabel(ControllerAction.Deselect)} controller chord");
            return;
        }

        bool keyboardCandidate = e.Button == SButton.A || e.Button == SButton.LeftShift;
        bool keyboardChord = keyboardCandidate
                             && this.Helper.Input.IsDown(SButton.LeftShift)
                             && this.Helper.Input.IsDown(SButton.A);
        if (keyboardChord)
        {
            this.Helper.Input.Suppress(SButton.LeftShift);
            this.Helper.Input.Suppress(SButton.A);
            this.TryActivate("Left Shift+A keyboard chord");
        }
    }

    public void OnRenderedHud(object? sender, RenderedHudEventArgs e)
    {
        if (!Context.IsWorldReady || !this.Save.Data.ChaChaLoaned || Game1.activeClickableMenu is not null)
            return;

        Rectangle rect = this.GetEnergyHudRect();
        long now = Environment.TickCount64;
        float pulse = 0.5f + 0.5f * (float)Math.Sin(now / 135d);

        Color stageColor = this.GetStageColor(this.EnergyAuraStage);
        Color panel = new Color(36, 31, 48) * 0.91f;
        Color border = this.IsReady
            ? Color.Lerp(new Color(220, 55, 48), Color.White, pulse * 0.55f)
            : this.IsActive
                ? new Color(235, 80, 66)
                : stageColor * 0.92f;

        e.SpriteBatch.Draw(Game1.staminaRect, rect, panel);
        DrawBorder(e.SpriteBatch, rect, border, this.IsReady ? 3 : 2);

        string title = this.IsActive
            ? ModEntry.T("chacha.boss.active")
            : ModEntry.T("chacha.energy.label");
        string value = this.IsActive
            ? $"{this.SecondsRemaining:0.0}s"
            : $"{this.BossEnergy.CurrentEnergy:0.#}/{BossEnergyService.MaxEnergy:0}";

        e.SpriteBatch.DrawString(Game1.smallFont, title, new Vector2(rect.X + 12, rect.Y + 7), Color.White, 0f, Vector2.Zero, 0.76f, SpriteEffects.None, 1f);
        Vector2 valueSize = Game1.smallFont.MeasureString(value) * 0.76f;
        e.SpriteBatch.DrawString(Game1.smallFont, value, new Vector2(rect.Right - 12 - valueSize.X, rect.Y + 7), Color.White, 0f, Vector2.Zero, 0.76f, SpriteEffects.None, 1f);

        Rectangle track = new(rect.X + 12, rect.Y + 29, rect.Width - 24, 12);
        e.SpriteBatch.Draw(Game1.staminaRect, track, new Color(16, 14, 21) * 0.96f);
        double ratio = this.IsActive
            ? Math.Clamp(this.SecondsRemaining / (BossFormDurationMs / 1000d), 0d, 1d)
            : Math.Clamp(this.BossEnergy.CurrentEnergy / BossEnergyService.MaxEnergy, 0d, 1d);
        int fillWidth = Math.Clamp((int)Math.Round(track.Width * ratio), 0, track.Width);
        if (fillWidth > 0)
        {
            Color fill = this.IsReady
                ? stageColor * (0.76f + pulse * 0.24f)
                : stageColor;
            e.SpriteBatch.Draw(Game1.staminaRect, new Rectangle(track.X, track.Y, fillWidth, track.Height), fill);
        }

        string detail;
        if (this.IsActive)
        {
            detail = ModEntry.T("chacha.boss.timer", new { seconds = this.SecondsRemaining.ToString("0.0") });
        }
        else if (this.IsReady)
        {
            string chord = $"{this.Controller.GetLabel(ControllerAction.Confirm)}+{this.Controller.GetLabel(ControllerAction.Deselect)}";
            detail = ModEntry.T("chacha.boss.hint.combo", new { controller = chord });
        }
        else
        {
            detail = ModEntry.T("chacha.energy.charging");
        }

        Vector2 detailSize = Game1.smallFont.MeasureString(detail);
        float detailScale = Math.Min(0.61f, (rect.Width - 24f) / Math.Max(1f, detailSize.X));
        e.SpriteBatch.DrawString(
            Game1.smallFont,
            detail,
            new Vector2(rect.Center.X - detailSize.X * detailScale / 2f, rect.Bottom - 17),
            this.IsReady ? Color.White : new Color(220, 213, 230),
            0f,
            Vector2.Zero,
            detailScale,
            SpriteEffects.None,
            1f
        );
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        if (!Context.IsWorldReady || !this.Save.Data.ChaChaLoaned)
            return;

        int stage = this.EnergyAuraStage;
        if (stage <= 0)
            return;

        NPC? actor = this.WorldActors.FindChaChaActor();
        if (actor is null || actor.isInvisible.Value || actor.currentLocation != Game1.currentLocation)
            return;

        this.EnsureAuraTexture();
        if (this.AuraTexture is null)
            return;

        Vector2 center = Game1.GlobalToLocal(Game1.viewport, actor.Position + new Vector2(16f, 17f));
        long now = Environment.TickCount64;
        float pulse = stage >= 4
            ? 0.88f + 0.12f * (float)Math.Sin(now / 105d)
            : 0.96f + 0.04f * (float)Math.Sin(now / 240d);

        float scale = (stage switch { 1 => 1.18f, 2 => 1.30f, 3 => 1.43f, _ => 1.62f }) * pulse;
        if (this.IsActive)
            scale *= 1.10f;

        Color color = this.GetStageColor(stage);
        float alpha = stage switch { 1 => 0.23f, 2 => 0.30f, 3 => 0.38f, _ => 0.48f };
        Vector2 origin = new(this.AuraTexture.Width / 2f, this.AuraTexture.Height / 2f);

        e.SpriteBatch.Draw(this.AuraTexture, center, null, color * alpha, 0f, origin, scale, SpriteEffects.None, 0.99f);
        e.SpriteBatch.Draw(this.AuraTexture, center, null, color * (alpha * 0.52f), 0f, origin, scale * 0.72f, SpriteEffects.None, 0.99f);

        int sparks = stage + (stage >= 4 ? 3 : 1);
        for (int i = 0; i < sparks; i++)
        {
            float phase = (float)(now * (stage >= 4 ? 0.006 : 0.0035) + i * 2.11);
            float radius = 29f + stage * 4f + i * 2f;
            Vector2 p = center + new Vector2((float)Math.Cos(phase) * radius, (float)Math.Sin(phase * 1.13f) * radius * 0.62f);
            int size = stage >= 4 && i % 2 == 0 ? 3 : 2;
            Color spark = color * (0.45f + 0.18f * (float)Math.Abs(Math.Sin(phase)));
            e.SpriteBatch.Draw(Game1.staminaRect, new Rectangle((int)p.X - size, (int)p.Y, size * 2 + 1, 1), spark);
            e.SpriteBatch.Draw(Game1.staminaRect, new Rectangle((int)p.X, (int)p.Y - size, 1, size * 2 + 1), spark);
        }
    }

    public bool TryActivate(string source)
    {
        if (!Context.IsWorldReady || !this.IsReady || !this.CanAcceptActivationInput())
            return false;

        if (!this.BossEnergy.TrySpend(BossEnergyService.MaxEnergy))
            return false;

        this.ReadyAnnounced = false;
        this.ActiveUntil = Environment.TickCount64 + BossFormDurationMs;
        this.BossEnergy.SetGainSuppressed(true);
        this.WorldActors.SetChaChaBossVisual(true);
        this.WorldActors.TriggerChaChaEmote(16);
        Game1.playSound("wand");
        Game1.showGlobalMessage(ModEntry.T("chacha.boss.activated"));
        this.Monitor.Log($"ChaCha Boss Form activated via {source}; duration={BossFormDurationMs}ms.", LogLevel.Info);
        return true;
    }

    public void EndBossForm(string reason)
    {
        bool wasActive = this.ActiveUntil > 0 || this.WorldActors.IsChaChaBossVisualActive;
        this.ActiveUntil = 0;
        this.BossEnergy.SetGainSuppressed(false);
        this.WorldActors.SetChaChaBossVisual(false);

        if (wasActive && Context.IsWorldReady)
        {
            Game1.playSound("smallSelect");
            this.WorldActors.TriggerChaChaEmote(32);
        }

        if (wasActive)
            this.Monitor.Log($"ChaCha Boss Form ended ({reason}).", LogLevel.Trace);
    }

    public void OnDayStarted(object? sender, DayStartedEventArgs e)
        => this.ResetRuntime();

    public void OnReturnedToTitle(object? sender, ReturnedToTitleEventArgs e)
    {
        this.ResetRuntime();
        this.DisposeAuraTexture();
    }

    public void OnSaving()
        => this.EndBossForm("save");

    public void DebugPrimeReady()
    {
        if (!Context.IsWorldReady)
            return;
        this.EndBossForm("debug prime");
        this.BossEnergy.DebugSetEnergy(BossEnergyService.MaxEnergy);
        this.ReadyAnnounced = false;
    }

    public string Describe()
    {
        string chord = $"{this.Controller.GetLabel(ControllerAction.Confirm)}+{this.Controller.GetLabel(ControllerAction.Deselect)}";
        return $"Ready={this.IsReady} | Active={this.IsActive} | Remaining={this.SecondsRemaining:0.0}s | " +
               $"AuraStage={this.EnergyAuraStage} | ControllerChord={chord} | Keyboard=LeftShift+A | {this.BossEnergy.Describe()}";
    }

    private void ResetRuntime()
    {
        this.ActiveUntil = 0;
        this.ReadyAnnounced = false;
        this.BossEnergy.SetGainSuppressed(false);
        this.WorldActors.SetChaChaBossVisual(false);
    }

    private bool CanAcceptActivationInput()
        => Game1.player is not null
           && Game1.player.health > 0
           && Game1.activeClickableMenu is null
           && !Game1.eventUp
           && !Game1.dialogueUp;

    private Rectangle GetEnergyHudRect()
    {
        const int width = 318;
        const int height = 58;
        int x = Math.Max(12, (Game1.uiViewport.Width - width) / 2);
        int y = Math.Clamp(108, 72, Math.Max(72, Game1.uiViewport.Height - height - 120));
        return new Rectangle(x, y, width, height);
    }

    private Color GetStageColor(int stage)
        => stage switch
        {
            1 => new Color(242, 244, 255),
            2 => new Color(255, 226, 82),
            3 => new Color(255, 145, 45),
            4 => new Color(232, 54, 48),
            _ => new Color(126, 116, 145)
        };

    private void EnsureAuraTexture()
    {
        if (this.AuraTexture is not null && !this.AuraTexture.IsDisposed)
            return;

        const int size = 64;
        Texture2D texture = new(Game1.staminaRect.GraphicsDevice, size, size);
        Color[] pixels = new Color[size * size];
        Vector2 center = new((size - 1) / 2f, (size - 1) / 2f);
        float radius = size / 2f;
        for (int y = 0; y < size; y++)
        {
            for (int x = 0; x < size; x++)
            {
                float distance = Vector2.Distance(new Vector2(x, y), center) / radius;
                float opacity = Math.Clamp(1f - distance, 0f, 1f);
                opacity = opacity * opacity * 0.88f;
                pixels[y * size + x] = Color.White * opacity;
            }
        }
        texture.SetData(pixels);
        this.AuraTexture = texture;
    }

    private void DisposeAuraTexture()
    {
        if (this.AuraTexture is null)
            return;
        try { this.AuraTexture.Dispose(); } catch { }
        this.AuraTexture = null;
    }

    private static void DrawBorder(SpriteBatch batch, Rectangle rect, Color color, int thickness)
    {
        batch.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Y, rect.Width, thickness), color);
        batch.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Bottom - thickness, rect.Width, thickness), color);
        batch.Draw(Game1.staminaRect, new Rectangle(rect.X, rect.Y, thickness, rect.Height), color);
        batch.Draw(Game1.staminaRect, new Rectangle(rect.Right - thickness, rect.Y, thickness, rect.Height), color);
    }
}
'''
write('Services/ChaChaBossFormService.cs', boss_form)


# ModEntry: inject controller, render aura in world, and bump visible build text.
s = read('ModEntry.cs')
s = s.replace(
    '            helper, this.Monitor, this.Save, this.BossEnergy, this.WorldActors\n',
    '            helper, this.Monitor, this.Save, this.BossEnergy, this.WorldActors, this.Controller\n'
)
if 'helper.Events.Display.RenderedWorld += this.ChaChaBossForm.OnRenderedWorld;' not in s:
    s = replace_once(
        s,
        '        helper.Events.Display.RenderedWorld += this.Story.OnRenderedWorld;\n',
        '        helper.Events.Display.RenderedWorld += this.Story.OnRenderedWorld;\n        helper.Events.Display.RenderedWorld += this.ChaChaBossForm.OnRenderedWorld;\n',
        'Boss Form world aura event'
    )
s = re.sub(
    r'Cardcha! v0\.3\.0-alpha\.28\.0\.4\.14\.4(?:\.\d+)? CHACHA BOSS FORM FOUNDATION TEST',
    f'Cardcha! v{VERSION} CHACHA ENERGY AURA + CHORD TEST',
    s
)
s = s.replace(
    '"Cardcha! v0.3.0-alpha.28.0.4.14.4 CHACHA BOSS FORM FOUNDATION TEST"',
    f'"Cardcha! v{VERSION} CHACHA ENERGY AURA + CHORD TEST"'
)
write('ModEntry.cs', s)


# Translation copy.
updates = {
    'default.json': {
        'chacha.energy.label': 'CHACHA ENERGY',
        'chacha.energy.charging': 'Boss Form charge',
        'chacha.boss.hint.combo': 'READY  •  {{controller}} / SHIFT+A / CLICK',
    },
    'vi.json': {
        'chacha.energy.label': 'NĂNG LƯỢNG CHACHA',
        'chacha.energy.charging': 'Đang tích năng lượng Boss Form',
        'chacha.boss.hint.combo': 'SẴN SÀNG  •  {{controller}} / SHIFT+A / CLICK',
    },
}
for lang, values in updates.items():
    p = ROOT / 'i18n' / lang
    obj = json.loads(p.read_text(encoding='utf-8'))
    obj.update(values)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print(f'Applied ChaCha energy aura + unified HUD + chord activation for {VERSION}')
