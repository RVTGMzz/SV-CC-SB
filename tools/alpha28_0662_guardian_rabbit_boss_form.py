from pathlib import Path
from PIL import Image, ImageDraw
import json, re

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.29'

# ---------------- version ----------------
manifest_path = ROOT / 'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['Version'] = VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

for rel in ['Cardcha.csproj', 'Directory.Build.targets']:
    p = ROOT / rel
    s = p.read_text(encoding='utf-8')
    s = re.sub(r'0\.3\.0-alpha\.28\.0\.4\.14\.4\.5\.12\.28', VERSION, s)
    p.write_text(s, encoding='utf-8')

# ---------------- Guardian Rabbit sprite sheet ----------------
# 4 directions x 4 walk/bob frames, native ChaCha 32x32 contract.
asset = ROOT / 'assets' / 'chacha_guardian_rabbit.png'
img = Image.new('RGBA', (128, 128), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

outline = (32, 45, 35, 255)
fur = (232, 224, 191, 255)
fur_shadow = (193, 188, 157, 255)
leaf_dark = (36, 89, 55, 255)
leaf = (68, 137, 73, 255)
leaf_light = (111, 185, 91, 255)
bark = (108, 76, 47, 255)
bark_light = (151, 109, 64, 255)
core = (122, 242, 118, 255)
core_hi = (225, 255, 174, 255)
eye = (35, 40, 35, 255)

# row: 0 down/front, 1 right, 2 up/back, 3 left
for row in range(4):
    for frame in range(4):
        ox, oy = frame * 32, row * 32
        bob = [0, -1, 0, 1][frame]
        step = [-1, 0, 1, 0][frame]

        # Soft shadow baked low in frame, compact body keeps ChaCha bunny-like rather than humanoid.
        d.ellipse((ox+8, oy+27, ox+24, oy+30), fill=(22, 34, 27, 95))

        if row in (0, 2):
            # Upright rabbit ears, slightly asymmetrical leaf-tipped silhouette.
            d.rounded_rectangle((ox+10, oy+2+bob, ox+14, oy+14+bob), radius=2, fill=outline)
            d.rounded_rectangle((ox+18, oy+1+bob, ox+22, oy+14+bob), radius=2, fill=outline)
            d.rounded_rectangle((ox+11, oy+3+bob, ox+13, oy+12+bob), radius=1, fill=fur_shadow if row == 2 else fur)
            d.rounded_rectangle((ox+19, oy+2+bob, ox+21, oy+12+bob), radius=1, fill=fur_shadow if row == 2 else fur)
            # Leaf tips on ears signal actual Verdant transformation.
            d.polygon([(ox+9,oy+5+bob),(ox+12,oy+1+bob),(ox+15,oy+6+bob)], fill=leaf)
            d.polygon([(ox+17,oy+4+bob),(ox+20,oy),(ox+23,oy+5+bob)], fill=leaf_light)
        elif row == 1:
            d.rounded_rectangle((ox+17, oy+3+bob, ox+23, oy+13+bob), radius=2, fill=outline)
            d.rounded_rectangle((ox+18, oy+4+bob, ox+22, oy+11+bob), radius=2, fill=fur)
            d.polygon([(ox+20,oy+3+bob),(ox+25,oy+5+bob),(ox+21,oy+8+bob)], fill=leaf_light)
            d.rounded_rectangle((ox+11, oy+5+bob, ox+16, oy+14+bob), radius=2, fill=outline)
            d.rounded_rectangle((ox+12, oy+6+bob, ox+15, oy+12+bob), radius=1, fill=fur_shadow)
        else:
            d.rounded_rectangle((ox+9, oy+3+bob, ox+15, oy+13+bob), radius=2, fill=outline)
            d.rounded_rectangle((ox+10, oy+4+bob, ox+14, oy+11+bob), radius=2, fill=fur)
            d.polygon([(ox+12,oy+3+bob),(ox+7,oy+5+bob),(ox+11,oy+8+bob)], fill=leaf_light)
            d.rounded_rectangle((ox+16, oy+5+bob, ox+21, oy+14+bob), radius=2, fill=outline)
            d.rounded_rectangle((ox+17, oy+6+bob, ox+20, oy+12+bob), radius=1, fill=fur_shadow)

        # Round head and stocky body, deliberately non-humanoid.
        d.ellipse((ox+8, oy+9+bob, ox+24, oy+23+bob), fill=outline)
        d.ellipse((ox+9, oy+10+bob, ox+23, oy+22+bob), fill=fur if row != 2 else fur_shadow)
        d.rounded_rectangle((ox+7, oy+17+bob, ox+25, oy+27+bob), radius=6, fill=outline)
        d.rounded_rectangle((ox+8, oy+18+bob, ox+24, oy+26+bob), radius=5, fill=fur_shadow if row == 2 else fur)

        # Leaf mantle/collar and bark shoulder plates.
        d.polygon([(ox+7,oy+17+bob),(ox+11,oy+14+bob),(ox+16,oy+18+bob),(ox+21,oy+14+bob),(ox+25,oy+17+bob),(ox+22,oy+21+bob),(ox+16,oy+19+bob),(ox+10,oy+21+bob)], fill=leaf_dark)
        d.polygon([(ox+9,oy+18+bob),(ox+12,oy+15+bob),(ox+15,oy+19+bob),(ox+11,oy+21+bob)], fill=leaf)
        d.polygon([(ox+23,oy+18+bob),(ox+20,oy+15+bob),(ox+17,oy+19+bob),(ox+21,oy+21+bob)], fill=leaf_light)
        d.rounded_rectangle((ox+6, oy+19+bob, ox+10, oy+24+bob), radius=1, fill=bark)
        d.line((ox+7,oy+20+bob,ox+9,oy+22+bob), fill=bark_light, width=1)
        d.rounded_rectangle((ox+22, oy+19+bob, ox+26, oy+24+bob), radius=1, fill=bark)
        d.line((ox+23,oy+20+bob,ox+25,oy+22+bob), fill=bark_light, width=1)

        # Stubby feet with walk motion.
        d.rounded_rectangle((ox+9+step, oy+25+bob, ox+15+step, oy+28+bob), radius=1, fill=outline)
        d.rounded_rectangle((ox+17-step, oy+25+bob, ox+23-step, oy+28+bob), radius=1, fill=outline)
        d.rectangle((ox+10+step, oy+25+bob, ox+14+step, oy+27+bob), fill=fur_shadow)
        d.rectangle((ox+18-step, oy+25+bob, ox+22-step, oy+27+bob), fill=fur_shadow)

        # Face/core by facing.
        if row == 0:
            d.rectangle((ox+12, oy+14+bob, ox+13, oy+15+bob), fill=eye)
            d.rectangle((ox+19, oy+14+bob, ox+20, oy+15+bob), fill=eye)
            d.rectangle((ox+15, oy+17+bob, ox+17, oy+18+bob), fill=(137,91,82,255))
            d.polygon([(ox+16,oy+20+bob),(ox+19,oy+23+bob),(ox+16,oy+26+bob),(ox+13,oy+23+bob)], fill=core, outline=core_hi)
            d.point((ox+16,oy+22+bob), fill=core_hi)
        elif row == 1:
            d.rectangle((ox+20, oy+14+bob, ox+21, oy+15+bob), fill=eye)
            d.polygon([(ox+18,oy+20+bob),(ox+21,oy+22+bob),(ox+18,oy+25+bob),(ox+16,oy+22+bob)], fill=core, outline=core_hi)
            d.ellipse((ox+6, oy+20+bob, ox+10, oy+24+bob), fill=leaf_light)
        elif row == 3:
            d.rectangle((ox+11, oy+14+bob, ox+12, oy+15+bob), fill=eye)
            d.polygon([(ox+14,oy+20+bob),(ox+16,oy+22+bob),(ox+14,oy+25+bob),(ox+11,oy+22+bob)], fill=core, outline=core_hi)
            d.ellipse((ox+22, oy+20+bob, ox+26, oy+24+bob), fill=leaf_light)
        else:
            # Back-facing guardian crest instead of a face.
            d.polygon([(ox+16,oy+13+bob),(ox+19,oy+17+bob),(ox+16,oy+20+bob),(ox+13,oy+17+bob)], fill=leaf_light)
            d.line((ox+16,oy+14+bob,ox+16,oy+19+bob), fill=core_hi, width=1)

img.save(asset)

# ---------------- WorldActorService: real transformed sprite ----------------
world_path = ROOT / 'Services' / 'WorldActorService.cs'
world = world_path.read_text(encoding='utf-8')
world = world.replace(
    '    public const string ChaChaMachineCharacterAsset = "Characters/Ronvotri.Cardcha_ChaCha_Machine";\n',
    '    public const string ChaChaMachineCharacterAsset = "Characters/Ronvotri.Cardcha_ChaCha_Machine";\n    public const string ChaChaGuardianCharacterAsset = "Characters/Ronvotri.Cardcha_ChaCha_GuardianRabbit";\n',
    1
)
world = world.replace(
    '    private const string ChaChaMachineSheetPath = "assets/chacha_machine.png";\n',
    '    private const string ChaChaMachineSheetPath = "assets/chacha_machine.png";\n    private const string ChaChaGuardianSheetPath = "assets/chacha_guardian_rabbit.png";\n',
    1
)
world = world.replace(
    '    private const float ChaChaBossNativeScale = 0.74f;\n',
    '    private const float ChaChaBossNativeScale = 0.82f;\n',
    1
)
world = world.replace(
    '        if (e.Name.IsEquivalentTo(ChaChaMachineCharacterAsset))\n            e.LoadFromModFile<Texture2D>(ChaChaMachineSheetPath, AssetLoadPriority.Medium);\n',
    '        if (e.Name.IsEquivalentTo(ChaChaMachineCharacterAsset))\n        {\n            e.LoadFromModFile<Texture2D>(ChaChaMachineSheetPath, AssetLoadPriority.Medium);\n            return;\n        }\n\n        if (e.Name.IsEquivalentTo(ChaChaGuardianCharacterAsset))\n            e.LoadFromModFile<Texture2D>(ChaChaGuardianSheetPath, AssetLoadPriority.Medium);\n',
    1
)
world = world.replace(
    '        string asset = machine ? ChaChaMachineCharacterAsset : ChaChaCharacterAsset;\n',
    '        string asset = machine\n            ? ChaChaMachineCharacterAsset\n            : (this.ChaChaBossVisualActive ? ChaChaGuardianCharacterAsset : ChaChaCharacterAsset);\n',
    1
)
old_set = '''    public void SetChaChaBossVisual(bool active)\n    {\n        this.ChaChaBossVisualActive = active;\n        NPC? actor = this.FindChaChaActor();\n        if (actor is not null)\n            actor.Scale = active ? ChaChaBossNativeScale : ChaChaNativeScale;\n    }\n'''
new_set = '''    public void SetChaChaBossVisual(bool active)\n    {\n        this.ChaChaBossVisualActive = active;\n        NPC? actor = this.FindChaChaActor();\n        if (actor is null)\n            return;\n\n        bool machineVisual = actor.Sprite is not null\n            && string.Equals(actor.Sprite.loadedTexture, ChaChaMachineCharacterAsset, StringComparison.OrdinalIgnoreCase);\n        if (!machineVisual)\n        {\n            string desired = active ? ChaChaGuardianCharacterAsset : ChaChaCharacterAsset;\n            int frame = actor.Sprite?.CurrentFrame ?? 0;\n            if (actor.Sprite is null\n                || actor.Sprite.SpriteWidth != 32\n                || actor.Sprite.SpriteHeight != 32\n                || !string.Equals(actor.Sprite.loadedTexture, desired, StringComparison.OrdinalIgnoreCase))\n            {\n                actor.Sprite = new AnimatedSprite(desired, Math.Clamp(frame, 0, 15), 32, 32);\n            }\n        }\n\n        actor.Scale = active ? ChaChaBossNativeScale : ChaChaNativeScale;\n    }\n'''
if old_set not in world:
    raise RuntimeError('WorldActorService SetChaChaBossVisual anchor missing')
world = world.replace(old_set, new_set, 1)
world_path.write_text(world, encoding='utf-8')

# ---------------- ChaChaBossFormService: Guardian Rabbit runtime ----------------
service = r'''using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Monsters;

namespace Cardcha.Services;

/// <summary>
/// ChaCha Boss Form runtime. Boss I unlocks Guardian Rabbit, an actual Verdant transformation
/// with a dedicated sprite and periodic root pulses. The global Boss Form contract remains
/// exactly 10 seconds and still spends the existing 100 Boss Energy charge.
/// </summary>
internal sealed class ChaChaBossFormService
{
    public const string GuardianRabbitFormId = "guardian_rabbit";
    public const int BossFormDurationMs = 10000;
    public const int GuardianRootPulseIntervalMs = 2000;
    public const int GuardianRootPulseDamage = 18;
    public const float GuardianRootPulseRadius = 176f;

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;
    private readonly BossEnergyService BossEnergy;
    private readonly WorldActorService WorldActors;
    private readonly ControllerProfileService Controller;

    private long ActiveUntil;
    private bool ReadyAnnounced;
    private Texture2D? AuraTexture;
    private long NextRootPulseAt;
    private long RootPulseVisualUntil;
    private long LastRootPulseAt;
    private bool DebugGuardianUnlock;

    public long GuardianPulseCount { get; private set; }
    public long GuardianPulseHits { get; private set; }
    public int LastPulseTargets { get; private set; }

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

    public bool GuardianRabbitUnlocked
        => this.DebugGuardianUnlock
           || this.Save.Data.Region1BossDefeated
           || this.Save.Data.BossCardsUnlocked?.Contains(BossCardService.VerdantCoreId) == true;

    public string ActiveFormId => this.IsActive ? GuardianRabbitFormId : string.Empty;
    public bool IsActive => this.ActiveUntil > Environment.TickCount64;
    public bool IsReady => !this.IsActive
                           && this.Save.Data.ChaChaLoaned
                           && this.GuardianRabbitUnlocked
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
            if (now >= this.NextRootPulseAt)
            {
                this.EmitGuardianRootPulse(now);
                this.NextRootPulseAt = now + GuardianRootPulseIntervalMs;
            }
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
            this.Monitor.Log("Guardian Rabbit READY: ChaCha Energy reached 100 and Boss I resonance is unlocked.", LogLevel.Info);
        }
    }

    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady || !this.IsReady || !this.CanAcceptActivationInput())
            return;

        if (e.Button == SButton.MouseLeft)
            return;

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
        // The user-approved persistent Boss Energy rectangle remains removed.
        // READY is signaled through ChaCha's aura/emote; activation stays on the semantic chord.
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
            scale *= 1.16f;

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

        // Root Pulse presentation: a quick broad Verdant bloom centered on transformed ChaCha.
        if (now < this.RootPulseVisualUntil)
        {
            float t = Math.Clamp((now - this.LastRootPulseAt) / 520f, 0f, 1f);
            float ringScale = 1.55f + 3.65f * t;
            float ringAlpha = (1f - t) * 0.34f;
            Color pulseColor = new(108, 224, 103);
            e.SpriteBatch.Draw(this.AuraTexture, center, null, pulseColor * ringAlpha, 0f, origin, ringScale, SpriteEffects.None, 0.985f);
            for (int i = 0; i < 8; i++)
            {
                float a = (float)(i * Math.PI / 4d + now * 0.0025d);
                float r = 26f + 72f * t;
                Vector2 p = center + new Vector2((float)Math.Cos(a) * r, (float)Math.Sin(a) * r * 0.62f);
                e.SpriteBatch.Draw(Game1.staminaRect, new Rectangle((int)p.X - 2, (int)p.Y - 1, 5, 3), pulseColor * ((1f - t) * 0.78f));
            }
        }
    }

    public bool TryActivate(string source)
    {
        if (!Context.IsWorldReady || !this.IsReady || !this.CanAcceptActivationInput())
            return false;

        if (!this.BossEnergy.TrySpend(BossEnergyService.MaxEnergy))
            return false;

        long now = Environment.TickCount64;
        this.ReadyAnnounced = false;
        this.ActiveUntil = now + BossFormDurationMs;
        this.NextRootPulseAt = now + 650;
        this.LastRootPulseAt = now;
        this.RootPulseVisualUntil = now + 520;
        this.BossEnergy.SetGainSuppressed(true);
        this.WorldActors.SetChaChaBossVisual(true);
        this.WorldActors.TriggerChaChaEmote(16);
        Game1.playSound("wand");
        Game1.showGlobalMessage(ModEntry.T("chacha.boss.guardian.activated"));
        this.Monitor.Log($"Guardian Rabbit activated via {source}; duration={BossFormDurationMs}ms, rootPulse={GuardianRootPulseDamage} every {GuardianRootPulseIntervalMs}ms.", LogLevel.Info);
        return true;
    }

    public bool DebugForceGuardianRabbit()
    {
        if (!Context.IsWorldReady)
            return false;
        this.EndBossForm("debug force");
        this.DebugGuardianUnlock = true;
        this.BossEnergy.DebugSetEnergy(BossEnergyService.MaxEnergy);
        this.ReadyAnnounced = false;
        return this.TryActivate("debug guardian-rabbit command");
    }

    public void EndBossForm(string reason)
    {
        bool wasActive = this.ActiveUntil > 0 || this.WorldActors.IsChaChaBossVisualActive;
        this.ActiveUntil = 0;
        this.NextRootPulseAt = 0;
        this.RootPulseVisualUntil = 0;
        this.BossEnergy.SetGainSuppressed(false);
        this.WorldActors.SetChaChaBossVisual(false);

        if (wasActive && Context.IsWorldReady)
        {
            Game1.playSound("smallSelect");
            this.WorldActors.TriggerChaChaEmote(32);
        }

        if (wasActive)
            this.Monitor.Log($"Guardian Rabbit ended ({reason}).", LogLevel.Trace);
    }

    public void OnDayStarted(object? sender, DayStartedEventArgs e)
        => this.ResetRuntime(clearDebugUnlock: true);

    public void OnReturnedToTitle(object? sender, ReturnedToTitleEventArgs e)
    {
        this.ResetRuntime(clearDebugUnlock: true);
        this.DisposeAuraTexture();
    }

    public void OnSaving()
        => this.EndBossForm("save");

    public void DebugPrimeReady()
    {
        if (!Context.IsWorldReady)
            return;
        this.EndBossForm("debug prime");
        this.DebugGuardianUnlock = true;
        this.BossEnergy.DebugSetEnergy(BossEnergyService.MaxEnergy);
        this.ReadyAnnounced = false;
    }

    public string Describe()
    {
        string chord = $"{this.Controller.GetLabel(ControllerAction.Confirm)}+{this.Controller.GetLabel(ControllerAction.Deselect)}";
        return $"Form={GuardianRabbitFormId} | Unlocked={this.GuardianRabbitUnlocked} (debug={this.DebugGuardianUnlock}) | " +
               $"Ready={this.IsReady} | Active={this.IsActive} | Remaining={this.SecondsRemaining:0.0}s | " +
               $"RootPulse={GuardianRootPulseDamage} dmg/{GuardianRootPulseIntervalMs / 1000d:0.#}s radius={GuardianRootPulseRadius:0}px | " +
               $"Pulses={this.GuardianPulseCount} Hits={this.GuardianPulseHits} LastTargets={this.LastPulseTargets} | " +
               $"AuraStage={this.EnergyAuraStage} | ControllerChord={chord} | Keyboard=LeftShift+A | {this.BossEnergy.Describe()}";
    }

    private void EmitGuardianRootPulse(long now)
    {
        this.LastRootPulseAt = now;
        this.RootPulseVisualUntil = now + 520;
        this.GuardianPulseCount++;
        this.LastPulseTargets = 0;

        NPC? actor = this.WorldActors.FindChaChaActor();
        Farmer? who = Game1.player;
        GameLocation? location = Game1.currentLocation;
        if (actor is null || who is null || location is null || actor.currentLocation != location)
            return;

        Vector2 center = actor.Position + new Vector2(16f, 16f);
        float radiusSq = GuardianRootPulseRadius * GuardianRootPulseRadius;
        List<Monster> targets = location.characters
            .OfType<Monster>()
            .Where(monster => monster.Health > 0
                              && Vector2.DistanceSquared(monster.Position + new Vector2(32f, 32f), center) <= radiusSq)
            .ToList();

        foreach (Monster monster in targets)
        {
            try
            {
                monster.takeDamage(GuardianRootPulseDamage, 0, 0, false, 0d, who);
                this.GuardianPulseHits++;
                this.LastPulseTargets++;
            }
            catch (Exception ex)
            {
                ModEntry.LogOnce("guardian-rabbit-root-pulse", $"Guardian Rabbit Root Pulse couldn't damage a target: {ex.Message}");
            }
        }

        Game1.playSound(targets.Count > 0 ? "leafrustle" : "dirtyHit");
    }

    private void ResetRuntime(bool clearDebugUnlock)
    {
        this.ActiveUntil = 0;
        this.ReadyAnnounced = false;
        this.NextRootPulseAt = 0;
        this.RootPulseVisualUntil = 0;
        this.LastRootPulseAt = 0;
        this.GuardianPulseCount = 0;
        this.GuardianPulseHits = 0;
        this.LastPulseTargets = 0;
        if (clearDebugUnlock)
            this.DebugGuardianUnlock = false;
        this.BossEnergy.SetGainSuppressed(false);
        this.WorldActors.SetChaChaBossVisual(false);
    }

    private bool CanAcceptActivationInput()
        => Game1.player is not null
           && Game1.player.health > 0
           && Game1.activeClickableMenu is null
           && !Game1.eventUp
           && !Game1.dialogueUp;

    private Color GetStageColor(int stage)
    {
        if (this.IsActive)
            return new Color(105, 224, 100);

        return stage switch
        {
            1 => new Color(242, 244, 255),
            2 => new Color(255, 226, 82),
            3 => new Color(255, 145, 45),
            4 => new Color(232, 54, 48),
            _ => new Color(126, 116, 145)
        };
    }

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
}
'''
(ROOT / 'Services' / 'ChaChaBossFormService.cs').write_text(service, encoding='utf-8')

# ---------------- i18n ----------------
def add_i18n(path: Path, values: dict):
    data = json.loads(path.read_text(encoding='utf-8'))
    data.update(values)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

add_i18n(ROOT/'i18n'/'default.json', {
    'chacha.boss.guardian.name': 'Guardian Rabbit',
    'chacha.boss.guardian.desc': 'ChaCha channels Verdant Guardian resonance for 10 seconds. Every 2 seconds, roots pulse around ChaCha and damage nearby monsters.',
    'chacha.boss.guardian.activated': 'ChaCha transformed into Guardian Rabbit! Verdant roots are answering the resonance.',
    'chacha.boss.guardian.locked': 'Guardian Rabbit awakens after Boss I: Verdant Guardian.'
})
add_i18n(ROOT/'i18n'/'vi.json', {
    'chacha.boss.guardian.name': 'Guardian Rabbit',
    'chacha.boss.guardian.desc': 'ChaCha cộng hưởng với Verdant Guardian trong 10 giây. Cứ mỗi 2 giây, rễ cây lại bùng lên quanh ChaCha và gây sát thương cho quái vật ở gần.',
    'chacha.boss.guardian.activated': 'ChaCha đã biến thành Guardian Rabbit! Rễ cây Verdant đang đáp lại cộng hưởng.',
    'chacha.boss.guardian.locked': 'Guardian Rabbit sẽ thức tỉnh sau khi đánh bại Boss I: Verdant Guardian.'
})

# ---------------- ModEntry debug + version text ----------------
mod_path = ROOT/'ModEntry.cs'
mod = mod_path.read_text(encoding='utf-8')
anchor = '        helper.ConsoleCommands.Add("cardcha_chacha_boss_status", "Show ChaCha Boss Form runtime state.", this.CommandChaChaBossStatus);\n'
if anchor not in mod:
    raise RuntimeError('ModEntry ChaCha boss command anchor missing')
mod = mod.replace(anchor, anchor + '        helper.ConsoleCommands.Add("cardcha_guardian_rabbit_test", "TEST ONLY: runtime-unlock and immediately activate Guardian Rabbit for 10 seconds.", (_, _) => this.Monitor.Log(this.ChaChaBossForm.DebugForceGuardianRabbit() ? "TEST: Guardian Rabbit activated for 10 seconds." : "TEST: Guardian Rabbit could not activate in the current game state.", LogLevel.Alert));\n', 1)
mod = mod.replace(
    'ChaCha Boss Form TEST primed to 100 ChaCha Energy. Use controller Confirm+Deselect (Switch B+Y), Left Shift+A, or click the READY ChaCha Energy bar.',
    'Guardian Rabbit TEST primed to 100 ChaCha Energy with a runtime-only unlock. Use controller Confirm+Deselect (Switch B+Y) or Left Shift+A.',
    1
)
mod = mod.replace(
    'Cardcha! 0.3.0-alpha.28.0.4.14.4.5.12.28 VERDANT CORE BOSS CARD RUNTIME TEST',
    'Cardcha! 0.3.0-alpha.28.0.4.14.4.5.12.29 GUARDIAN RABBIT BOSS FORM TEST',
    1
)
mod_path.write_text(mod, encoding='utf-8')

# ---------------- handoff ----------------
Path('handoff/ALPHA28_0662_GUARDIAN_RABBIT_BOSS_FORM.md').write_text(f'''# Alpha28 0662 - Guardian Rabbit Boss Form\n\nBuild: `{VERSION}`\nBranch: `cardcha-alpha28-0662-guardian-rabbit-boss-form`\nStatus: implementation candidate, in-game acceptance pending. 0660 and 0661 visual/gameplay acceptance are also still pending because the user continued before testing.\n\n## Guardian Rabbit\n- Boss I / Verdant resonance now unlocks ChaCha's first actual named Boss Form: `guardian_rabbit`.\n- Unlock derives from existing schema-19 Boss I state (`Region1BossDefeated` or `verdant_core` in `BossCardsUnlocked`). No save-schema migration.\n- The generic enlarged ChaCha placeholder is replaced by a dedicated 4-direction x 4-frame Guardian Rabbit sprite sheet.\n- Design canon: short, round rabbit body, long rabbit ears, leaf mantle, bark shoulder plates, glowing Verdant core. It is not humanoid and not cat-like.\n- Active draw scale is 0.82 native NPC scale.\n\n## Runtime\n- Boss Form duration stays locked at exactly 10 seconds.\n- Activation still spends exactly 100 Boss Energy.\n- Boss Energy gain scale stays locked at x1/3 and gain is suppressed while Boss Form is active, exactly as before.\n- Guardian Rabbit emits Root Pulse every 2 seconds while active.\n- Test pulse damage: 18 per target, radius 176 px. Balance is explicitly provisional for the later balance pass.\n- Root Pulse uses normal Monster.takeDamage routing so Cardcha death/drop observation remains compatible.\n- Active aura switches to Verdant green and each Root Pulse has a visible expanding leaf/root bloom.\n\n## Input / debug\n- Controller activation remains Confirm+Deselect.\n- Keyboard activation remains Left Shift+A.\n- `cardcha_chacha_boss_ready` now grants only a runtime debug unlock and primes 100 Energy.\n- `cardcha_guardian_rabbit_test` runtime-unlocks and immediately activates Guardian Rabbit for 10 seconds without changing save progression.\n- `cardcha_chacha_boss_status` reports unlock, active form, pulse count/hits and locked Energy telemetry.\n\n## Locked systems preserved\nSave schema 19, 20/40/60/80 milestones, 76 active normal-card audit / 80 stored base IDs, Boss Form 10 sec, Boss Energy x1/3, 0659 MiMi stair behavior, MiMi native profile + CC continuity, Region I Hunt Run 4-of-6, 0660 Verdant Colossus, 0661 Verdant Core Boss Card, Airship route/upgrades, controller mapping and Forest gate are unchanged.\n''', encoding='utf-8')
Path('handoff/LATEST_CARDCHA_HANDOFF.md').write_text(f'''# Latest Cardcha handoff\n\nCurrent branch: `cardcha-alpha28-0662-guardian-rabbit-boss-form`\nCurrent build: `{VERSION}`\n\nContinue from:\n`handoff/ALPHA28_0662_GUARDIAN_RABBIT_BOSS_FORM.md`\n\n0660/0661/0662 in-game acceptance is pending. Do not resume from stale `main`.\n''', encoding='utf-8')

print(json.dumps({
    'version': VERSION,
    'form': 'guardian_rabbit',
    'durationSeconds': 10,
    'energyCost': 100,
    'energyGainScaleLocked': '1/3',
    'rootPulseEverySeconds': 2,
    'rootPulseDamageTest': 18,
    'rootPulseRadiusPx': 176,
    'schema': 19,
    'sprite': '128x128 / 16 frames @ 32x32'
}, indent=2))
