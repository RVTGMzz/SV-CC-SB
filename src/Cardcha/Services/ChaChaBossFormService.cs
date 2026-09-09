using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Monsters;

namespace Cardcha.Services;

/// <summary>
/// ChaCha Boss Form runtime. 0672 gives Guardian/Mirror/Trinity/Resonance distinct combat pulses
/// with a dedicated sprite and periodic root pulses. The global Boss Form contract remains
/// exactly 10 seconds and still spends the existing 100 Boss Energy charge.
/// </summary>
internal sealed class ChaChaBossFormService
{
    public const string GuardianRabbitFormId = "guardian_rabbit";
    public const string MirrorRabbitFormId = "mirror_rabbit";
    public const string TrinityRabbitFormId = "trinity_rabbit";
    public const string ResonanceRabbitFormId = "resonance_rabbit";
    public const int BossFormDurationMs = 10000;
    public const int GuardianRootPulseIntervalMs = 2000;
    public const int GuardianRootPulseDamage = 14;
    public const float GuardianRootPulseRadius = 176f;
    public const int MirrorPulseDamage = 12;
    public const int TrinityPulseDamage = 13;
    public const int ResonancePulseDamage = 16;

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
    private string ActiveVisualFormId = GuardianRabbitFormId;
    private int TrinityPulseIndex;

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

    public string ActiveFormId => this.IsActive ? this.ActiveVisualFormId : string.Empty;
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
            this.WorldActors.SetChaChaBossVisual(true, this.ActiveVisualFormId);
            if (now >= this.NextRootPulseAt)
            {
                this.EmitGuardianRootPulse(now);
                this.NextRootPulseAt = now + this.CurrentPulseIntervalMs();
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
            this.Monitor.Log($"ChaCha Boss Form READY: next={this.ResolvePreferredFormId()}, Energy=100.", LogLevel.Info);
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
            Color pulseColor = this.CurrentPulseColor();
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
        this.ActiveVisualFormId = this.ResolvePreferredFormId();
        this.ActiveUntil = now + BossFormDurationMs;
        this.NextRootPulseAt = now + 650;
        this.LastRootPulseAt = now;
        this.RootPulseVisualUntil = now + 520;
        this.TrinityPulseIndex = 0;
        this.BossEnergy.SetGainSuppressed(true);
        this.WorldActors.SetChaChaBossVisual(true, this.ActiveVisualFormId);
        this.WorldActors.TriggerChaChaEmote(16);
        Game1.playSound("wand");
        Game1.showGlobalMessage($"ChaCha • {this.DescribeFormName(this.ActiveVisualFormId)}!");
        this.Monitor.Log($"ChaCha Boss Form {this.ActiveVisualFormId} activated via {source}; duration={BossFormDurationMs}ms, rootPulse={GuardianRootPulseDamage} every {GuardianRootPulseIntervalMs}ms.", LogLevel.Info);
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
            this.Monitor.Log($"ChaCha Boss Form {this.ActiveVisualFormId} ended ({reason}).", LogLevel.Trace);
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
        string preferred = this.ResolvePreferredFormId();
        return $"Form={preferred} | ActiveForm={this.ActiveFormId} | Unlocked={this.GuardianRabbitUnlocked} (debug={this.DebugGuardianUnlock}) | " +
               $"Ready={this.IsReady} | Active={this.IsActive} | Remaining={this.SecondsRemaining:0.0}s | " +
               $"Pulse={this.CurrentPulseDamage()} dmg/{this.CurrentPulseIntervalMs() / 1000d:0.##}s radius={this.CurrentPulseRadius():0}px | " +
               $"Pulses={this.GuardianPulseCount} Hits={this.GuardianPulseHits} LastTargets={this.LastPulseTargets} | " +
               $"AuraStage={this.EnergyAuraStage} | ControllerChord={chord} | Keyboard=LeftShift+A | {this.BossEnergy.Describe()}";
    }

    private string ResolvePreferredFormId()
    {
        HashSet<string>? unlocked = this.Save.Data.BossCardsUnlocked;
        if (unlocked?.Contains(MilestoneBossService.MimiBossCardId) == true) return ResonanceRabbitFormId;
        if (unlocked?.Contains(MilestoneBossService.TricolorBossCardId) == true) return TrinityRabbitFormId;
        if (unlocked?.Contains(MilestoneBossService.MirrorArchiveBossCardId) == true) return MirrorRabbitFormId;
        return GuardianRabbitFormId;
    }

    private string DescribeFormName(string id) => id switch
    {
        MirrorRabbitFormId => "Mirror Rabbit",
        TrinityRabbitFormId => "Trinity Rabbit",
        ResonanceRabbitFormId => "Resonance Rabbit",
        _ => "Guardian Rabbit",
    };

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

        int damage = this.CurrentPulseDamage();
        float radius = this.CurrentPulseRadius();
        int bonusDamage = 0;
        int heal = 0;

        if (this.ActiveVisualFormId == MirrorRabbitFormId)
        {
            bonusDamage = 6;
        }
        else if (this.ActiveVisualFormId == TrinityRabbitFormId)
        {
            this.TrinityPulseIndex = (this.TrinityPulseIndex + 1) % 3;
            if (this.TrinityPulseIndex == 0)
                damage = 19;
            else if (this.TrinityPulseIndex == 1)
                heal = 5;
            else
                radius = 232f;
        }
        else if (this.ActiveVisualFormId == ResonanceRabbitFormId)
        {
            bonusDamage = 5;
            heal = 3;
            radius = 224f;
        }

        Vector2 center = actor.Position + new Vector2(16f, 16f);
        float radiusSq = radius * radius;
        List<Monster> targets = location.characters
            .OfType<Monster>()
            .Where(monster => monster.Health > 0
                              && Vector2.DistanceSquared(monster.Position + new Vector2(32f, 32f), center) <= radiusSq)
            .ToList();

        foreach (Monster monster in targets)
        {
            try
            {
                monster.takeDamage(damage, 0, 0, false, 0d, who);
                if (bonusDamage > 0 && monster.Health > 0)
                    monster.takeDamage(bonusDamage, 0, 0, false, 0d, who);
                this.GuardianPulseHits++;
                this.LastPulseTargets++;
            }
            catch (Exception ex)
            {
                ModEntry.LogOnce("chacha-boss-form-pulse", $"ChaCha Boss Form pulse couldn't damage a target: {ex.Message}");
            }
        }

        if (heal > 0 && who.health > 0)
            who.health = Math.Min(who.maxHealth, who.health + heal);

        Game1.playSound(this.ActiveVisualFormId switch
        {
            MirrorRabbitFormId => "wand",
            TrinityRabbitFormId when this.TrinityPulseIndex == 1 => "leafrustle",
            ResonanceRabbitFormId => "discoverMineral",
            _ => targets.Count > 0 ? "leafrustle" : "dirtyHit",
        });
    }

    private int CurrentPulseDamage() => this.ActiveVisualFormId switch
    {
        MirrorRabbitFormId => MirrorPulseDamage,
        TrinityRabbitFormId => TrinityPulseDamage,
        ResonanceRabbitFormId => ResonancePulseDamage,
        _ => GuardianRootPulseDamage,
    };

    private int CurrentPulseIntervalMs() => this.ActiveVisualFormId switch
    {
        MirrorRabbitFormId => 1900,
        TrinityRabbitFormId => 1800,
        ResonanceRabbitFormId => 1700,
        _ => GuardianRootPulseIntervalMs,
    };

    private float CurrentPulseRadius() => this.ActiveVisualFormId switch
    {
        MirrorRabbitFormId => 192f,
        TrinityRabbitFormId => 188f,
        ResonanceRabbitFormId => 224f,
        _ => GuardianRootPulseRadius,
    };

    private Color CurrentPulseColor() => this.ActiveVisualFormId switch
    {
        MirrorRabbitFormId => new Color(174, 154, 255),
        TrinityRabbitFormId => this.TricolorPulseColor(),
        ResonanceRabbitFormId => new Color(238, 171, 255),
        _ => new Color(108, 224, 103),
    };

    private Color TricolorPulseColor() => this.TrinityPulseIndex switch
    {
        0 => new Color(238, 92, 78),
        1 => new Color(99, 210, 118),
        _ => new Color(89, 148, 241),
    };

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
        this.ActiveVisualFormId = GuardianRabbitFormId;
        this.TrinityPulseIndex = 0;
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
            return this.CurrentPulseColor();

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
