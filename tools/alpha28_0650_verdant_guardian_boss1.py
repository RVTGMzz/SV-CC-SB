from pathlib import Path
import json

ROOT = Path('src/Cardcha')
VERSION_OLD = '0.3.0-alpha.28.0.4.14.4.5.12.17'
VERSION_NEW = '0.3.0-alpha.28.0.4.14.4.5.12.18'

for junk in ['tmp.txt','tmp2.txt','tmp3.txt','tmp4.txt']:
    Path(junk).unlink(missing_ok=True)


def replace_once(path, old, new):
    p = Path(path)
    text = p.read_text()
    if old not in text:
        raise SystemExit(f'anchor missing in {path}: {old[:120]!r}')
    p.write_text(text.replace(old, new, 1))

# Version bump only. Save schema intentionally stays 19.
for rel in ['manifest.json', 'Cardcha.csproj', 'Directory.Build.targets']:
    p = ROOT / rel
    text = p.read_text()
    if VERSION_OLD not in text:
        raise SystemExit(f'version anchor missing: {rel}')
    p.write_text(text.replace(VERSION_OLD, VERSION_NEW))

# Persistent Boss I progression fields. No schema bump.
save_data = ROOT / 'Models/SaveData.cs'
text = save_data.read_text()
anchor = '''    public int AirshipReactorLevel { get; set; }\n\n    public string LastStateFingerprint { get; set; } = \"\";'''
insert = '''    public int AirshipReactorLevel { get; set; }\n\n    // alpha.28.0.4.14.4.5.12.18 — boss milestone persistence. Kept inside schema 19 so the\n    // pending MiMi/stair acceptance build does not receive an unrelated schema migration.\n    public bool Region1BossDefeated { get; set; }\n    public HashSet<string> BossCardsUnlocked { get; set; } = new(StringComparer.OrdinalIgnoreCase);\n    public string EquippedBossCardId { get; set; } = \"\";\n\n    public string LastStateFingerprint { get; set; } = \"\";'''
if anchor not in text:
    raise SystemExit('SaveData boss anchor missing')
save_data.write_text(text.replace(anchor, insert, 1))

# Clone/normalize the new fields, deliberately leave ComputeFingerprint canonical string unchanged
# to avoid false persistence warnings on existing schema-19 saves.
save_service = ROOT / 'Services/SaveService.cs'
text = save_service.read_text()
clone_anchor = '''            AirshipReactorLevel = d.AirshipReactorLevel,\n            LastStateFingerprint = d.LastStateFingerprint ?? \"\"'''
clone_new = '''            AirshipReactorLevel = d.AirshipReactorLevel,\n            Region1BossDefeated = d.Region1BossDefeated,\n            BossCardsUnlocked = new HashSet<string>(d.BossCardsUnlocked ?? new HashSet<string>(), StringComparer.OrdinalIgnoreCase),\n            EquippedBossCardId = d.EquippedBossCardId ?? \"\",\n            LastStateFingerprint = d.LastStateFingerprint ?? \"\"'''
if clone_anchor not in text:
    raise SystemExit('SaveService clone anchor missing')
text = text.replace(clone_anchor, clone_new, 1)
normalize_anchor = '''        this.Data.ActiveChaChaSkillId ??= \"\";\n        this.Data.LastStateFingerprint ??= \"\";'''
normalize_new = '''        this.Data.ActiveChaChaSkillId ??= \"\";\n        this.Data.BossCardsUnlocked ??= new HashSet<string>(StringComparer.OrdinalIgnoreCase);\n        this.Data.BossCardsUnlocked = new HashSet<string>(\n            this.Data.BossCardsUnlocked.Where(p => !string.IsNullOrWhiteSpace(p)),\n            StringComparer.OrdinalIgnoreCase\n        );\n        this.Data.EquippedBossCardId ??= \"\";\n        if (!string.IsNullOrWhiteSpace(this.Data.EquippedBossCardId)\n            && !this.Data.BossCardsUnlocked.Contains(this.Data.EquippedBossCardId))\n            this.Data.EquippedBossCardId = \"\";\n        this.Data.LastStateFingerprint ??= \"\";'''
if normalize_anchor not in text:
    raise SystemExit('SaveService normalize anchor missing')
text = text.replace(normalize_anchor, normalize_new, 1)
save_service.write_text(text)

# Portable machine: the temporary 20-card dialogue gift now waits for the actual Boss I clear,
# while Boss I can grant the reward immediately.
portable = ROOT / 'Services/PortableMachineService.cs'
text = portable.read_text()
old_ready = '''           && !this.IsAcquired\n           && this.UniqueCardCount >= FreeGiftCardMilestone;'''
new_ready = '''           && !this.IsAcquired\n           && this.UniqueCardCount >= FreeGiftCardMilestone\n           && this.Save.Data.Region1BossDefeated;'''
if old_ready not in text:
    raise SystemExit('Portable readiness anchor missing')
text = text.replace(old_ready, new_ready, 1)
old_grant = '''    /// <summary>Claim the current 20-unique-card milestone gift when the player next talks business with MiMi.\n    /// This direct gift is a compatibility bridge until the approved 20-card quest + boss reward is implemented.</summary>\n    public bool TryGrantMilestoneGift()\n    {\n        if (!this.IsMilestoneGiftReady)\n            return false;\n\n        this.Save.Data.PortableMachineGifted = true;\n        this.GivePortableItem();\n        this.Save.Save();\n\n        this.Monitor.Log(\n            $\"MiMi gifted the Portable Cardcha Machine at {this.UniqueCardCount} unique cards.\",\n            LogLevel.Info\n        );\n        return true;\n    }'''
new_grant = '''    /// <summary>Compatibility claim path after the 20-card Boss I clear.</summary>\n    public bool TryGrantMilestoneGift()\n    {\n        if (!this.IsMilestoneGiftReady)\n            return false;\n        return this.GrantRegion1BossReward();\n    }\n\n    /// <summary>First-clear Boss I reward. Safe when the player already owns the portable machine.</summary>\n    public bool GrantRegion1BossReward()\n    {\n        if (!Context.IsWorldReady || this.IsAcquired)\n            return false;\n\n        this.Save.Data.PortableMachineGifted = true;\n        this.GivePortableItem();\n        this.Save.Save();\n        this.Monitor.Log(\"Boss I granted the Portable Cardcha Machine.\", LogLevel.Info);\n        return true;\n    }'''
if old_grant not in text:
    raise SystemExit('Portable grant anchor missing')
portable.write_text(text.replace(old_grant, new_grant, 1))

# Boss service.
boss_service = r'''using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Monsters;

namespace Cardcha.Services;

internal enum VerdantGuardianState
{
    Dormant,
    Intro,
    Decision,
    SwipeTelegraph,
    RootSpikesTelegraph,
    SummonAdds,
    ChargeTelegraph,
    Charging,
    VineTrapTelegraph,
    VineTrapActive,
    AreaSlamTelegraph,
    PhaseTransition,
    Defeated,
    Victory
}

internal enum VerdantGuardianAttack
{
    Swipe,
    RootSpikes,
    SummonAdds,
    Charge,
    VineTrap,
    AreaSlam
}

/// <summary>
/// Boss I functional vertical slice. The body intentionally uses a vanilla GreenSlime proxy until
/// approved custom art is authored; routing, telegraphs, phases, damage, save flags and rewards are real.
/// </summary>
internal sealed class VerdantGuardianBossService
{
    public const string LocationName = "Cardcha_VerdantGuardianArena";
    public const string MapAssetName = "Maps/Cardcha_VerdantGuardianArena";
    public const string BossCardId = "verdant_core";
    public const string BossMarkerKey = "Ronvotri.Cardcha/VerdantGuardian";
    public const string BossAddMarkerKey = "Ronvotri.Cardcha/VerdantGuardianAdd";
    public static readonly Point PlayerArrivalTile = new(14, 17);

    private const string MapPath = "assets/verdant_guardian_arena.tmx";
    private const int BossMaxHealth = 1300;
    private const int IntroDurationMs = 1500;
    private const int PhaseTransitionDurationMs = 1600;
    private const int VictoryReturnDelayMs = 3500;
    private const int SwipeTelegraphMs = 700;
    private const int RootTelegraphMs = 900;
    private const int SummonTelegraphMs = 600;
    private const int ChargeTelegraphMs = 900;
    private const int ChargeDurationMs = 720;
    private const int VineTelegraphMs = 900;
    private const int VineActiveMs = 2500;
    private const int SlamTelegraphMs = 1100;
    private const int MaxActiveAdds = 4;
    private const float ChargePixelsPerTick = 17f;

    private static readonly Point BossSpawnTile = new(14, 7);
    private static readonly Point RetreatTile = new(14, 18);
    private static readonly Point[] AddSpawnTiles = { new(5, 5), new(22, 5), new(5, 14), new(22, 14) };

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;
    private readonly PortableMachineService PortableMachine;
    private readonly Dictionary<VerdantGuardianAttack, long> CooldownUntil = new();

    private bool CreationFailed;
    private bool LoggedCreation;
    private Monster? BossProxy;
    private VerdantGuardianState State = VerdantGuardianState.Dormant;
    private VerdantGuardianAttack? LastAttack;
    private int Phase = 1;
    private int PendingPhase;
    private long StateStartedAtMs;
    private long NextDecisionAtMs;
    private long VictoryReturnAtMs;
    private bool AttackApplied;
    private bool VictoryHandled;
    private Point[] RootTargets = Array.Empty<Point>();
    private Point VineTarget;
    private Vector2 ChargeDirection;
    private Random EncounterRandom = new(1);

    public VerdantGuardianBossService(IModHelper helper, IMonitor monitor, SaveService save, PortableMachineService portableMachine)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
        this.PortableMachine = portableMachine;
    }

    public bool IsInArena => Context.IsWorldReady
        && Game1.currentLocation?.NameOrUniqueName.Equals(LocationName, StringComparison.OrdinalIgnoreCase) == true;

    public void OnAssetRequested(object? sender, AssetRequestedEventArgs e)
    {
        if (e.NameWithoutLocale.IsEquivalentTo(MapAssetName))
            e.LoadFromModFile<xTile.Map>(MapPath, AssetLoadPriority.Exclusive);
    }

    public void OnSaveLoaded()
    {
        this.ResetRuntime(removeActors: true);
        this.EnsureLocation();
    }

    public void OnDayStarted(object? sender, DayStartedEventArgs e)
    {
        this.ResetRuntime(removeActors: true);
        this.CreationFailed = false;
        this.EnsureLocation();
    }

    public void OnReturnedToTitle(object? sender, ReturnedToTitleEventArgs e)
    {
        this.ResetRuntime(removeActors: true);
        this.CreationFailed = false;
        this.LoggedCreation = false;
    }

    public void OnWarped(object? sender, WarpedEventArgs e)
    {
        if (!Context.IsWorldReady)
            return;
        if (e.NewLocation.NameOrUniqueName.Equals(LocationName, StringComparison.OrdinalIgnoreCase))
        {
            this.StartEncounter(e.NewLocation);
            return;
        }
        if (e.OldLocation?.NameOrUniqueName.Equals(LocationName, StringComparison.OrdinalIgnoreCase) == true)
            this.ResetRuntime(removeActors: true);
    }

    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!this.IsInArena || !e.Button.IsActionButton() || Game1.activeClickableMenu is not null || Game1.dialogueUp || Game1.eventUp)
            return;
        Point tile = PlayerTile();
        if (Math.Abs(tile.X - RetreatTile.X) > 1 || Math.Abs(tile.Y - RetreatTile.Y) > 1)
            return;
        this.Helper.Input.Suppress(e.Button);
        Game1.showGlobalMessage(ModEntry.T("boss.verdant.retreat"));
        this.ReturnToRegion1();
    }

    public void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)
    {
        if (!this.IsInArena || Game1.activeClickableMenu is not null || Game1.dialogueUp || Game1.eventUp)
            return;

        long now = Environment.TickCount64;
        if (this.State == VerdantGuardianState.Victory)
        {
            if (this.VictoryReturnAtMs > 0 && now >= this.VictoryReturnAtMs)
                this.ReturnToRegion1();
            return;
        }

        Monster? boss = this.ResolveBoss();
        if (boss is null || boss.Health <= 0)
        {
            this.HandleVictory(now);
            return;
        }

        if (this.State != VerdantGuardianState.PhaseTransition)
        {
            if (this.Phase == 1 && boss.Health <= (int)(boss.MaxHealth * 0.70f))
            {
                this.BeginPhaseTransition(2, now);
                return;
            }
            if (this.Phase == 2 && boss.Health <= (int)(boss.MaxHealth * 0.35f))
            {
                this.BeginPhaseTransition(3, now);
                return;
            }
        }

        switch (this.State)
        {
            case VerdantGuardianState.Intro:
                if (now - this.StateStartedAtMs >= IntroDurationMs) this.EnterDecision(now, 400);
                break;
            case VerdantGuardianState.Decision:
                if (now >= this.NextDecisionAtMs) this.SelectNextAttack(now);
                break;
            case VerdantGuardianState.SwipeTelegraph:
                if (now - this.StateStartedAtMs >= SwipeTelegraphMs)
                {
                    if (!this.AttackApplied && DistanceTiles(BossCenter(boss), PlayerCenter()) <= 2.35f) DamagePlayer(10, boss);
                    this.AttackApplied = true;
                    this.CompleteAttack(now);
                }
                break;
            case VerdantGuardianState.RootSpikesTelegraph:
                if (now - this.StateStartedAtMs >= RootTelegraphMs)
                {
                    if (!this.AttackApplied && this.RootTargets.Contains(PlayerTile())) DamagePlayer(8, boss);
                    this.AttackApplied = true;
                    this.CompleteAttack(now);
                }
                break;
            case VerdantGuardianState.SummonAdds:
                if (now - this.StateStartedAtMs >= SummonTelegraphMs)
                {
                    if (!this.AttackApplied) this.SpawnAdds();
                    this.AttackApplied = true;
                    this.CompleteAttack(now);
                }
                break;
            case VerdantGuardianState.ChargeTelegraph:
                if (now - this.StateStartedAtMs >= ChargeTelegraphMs)
                {
                    this.State = VerdantGuardianState.Charging;
                    this.StateStartedAtMs = now;
                    this.AttackApplied = false;
                    Game1.playSound("clubswipe");
                }
                break;
            case VerdantGuardianState.Charging:
                this.UpdateCharge(boss, now);
                break;
            case VerdantGuardianState.VineTrapTelegraph:
                if (now - this.StateStartedAtMs >= VineTelegraphMs)
                {
                    this.State = VerdantGuardianState.VineTrapActive;
                    this.StateStartedAtMs = now;
                    this.AttackApplied = false;
                    Game1.playSound("dirtyHit");
                }
                break;
            case VerdantGuardianState.VineTrapActive:
                if (!this.AttackApplied && this.PlayerInsideVineZone())
                {
                    this.AttackApplied = true;
                    DamagePlayer(4, boss);
                    Game1.player.Halt();
                }
                if (now - this.StateStartedAtMs >= VineActiveMs) this.CompleteAttack(now);
                break;
            case VerdantGuardianState.AreaSlamTelegraph:
                if (now - this.StateStartedAtMs >= SlamTelegraphMs)
                {
                    if (!this.AttackApplied && DistanceTiles(BossCenter(boss), PlayerCenter()) <= 4.1f) DamagePlayer(16, boss);
                    this.AttackApplied = true;
                    Game1.playSound("explosion");
                    this.CompleteAttack(now);
                }
                break;
            case VerdantGuardianState.PhaseTransition:
                boss.Position = BossSpawnPosition();
                if (now - this.StateStartedAtMs >= PhaseTransitionDurationMs)
                {
                    this.Phase = Math.Clamp(this.PendingPhase, 1, 3);
                    this.PendingPhase = 0;
                    Game1.showGlobalMessage(ModEntry.T($"boss.verdant.phase.{this.Phase}"));
                    this.EnterDecision(now, 500);
                }
                break;
        }
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        if (!this.IsInArena) return;
        Monster? boss = this.ResolveBoss();
        if (boss is not null && boss.Health > 0)
        {
            Vector2 core = Game1.GlobalToLocal(Game1.viewport, BossCenter(boss));
            float pulse = 0.72f + 0.18f * (float)Math.Sin(Environment.TickCount64 / 120d);
            int size = 14 + this.Phase * 4;
            Color c = this.Phase switch { 1 => new Color(78,214,105), 2 => new Color(112,238,79), _ => new Color(180,255,116) };
            e.SpriteBatch.Draw(Game1.staminaRect, new Rectangle((int)core.X - size, (int)core.Y - 3, size * 2, 6), c * pulse);
            e.SpriteBatch.Draw(Game1.staminaRect, new Rectangle((int)core.X - 3, (int)core.Y - size, 6, size * 2), c * pulse);
        }

        switch (this.State)
        {
            case VerdantGuardianState.RootSpikesTelegraph:
                foreach (Point tile in this.RootTargets) DrawTileTelegraph(e.SpriteBatch, tile, new Color(96,224,98) * 0.48f);
                break;
            case VerdantGuardianState.VineTrapTelegraph:
                DrawZoneTelegraph(e.SpriteBatch, this.VineTarget, 1, new Color(85,190,74) * 0.38f);
                break;
            case VerdantGuardianState.VineTrapActive:
                DrawZoneTelegraph(e.SpriteBatch, this.VineTarget, 1, new Color(68,145,58) * 0.62f);
                break;
            case VerdantGuardianState.AreaSlamTelegraph:
                if (boss is not null) DrawRadiusTelegraph(e.SpriteBatch, BossCenter(boss), 4.1f, new Color(199,245,111) * 0.34f);
                break;
            case VerdantGuardianState.SwipeTelegraph:
                if (boss is not null) DrawRadiusTelegraph(e.SpriteBatch, BossCenter(boss), 2.35f, new Color(245,210,94) * 0.26f);
                break;
            case VerdantGuardianState.ChargeTelegraph:
                if (boss is not null) DrawChargeLane(e.SpriteBatch, BossCenter(boss), this.ChargeDirection);
                break;
        }
    }

    public void OnRenderedHud(object? sender, RenderedHudEventArgs e)
    {
        if (!this.IsInArena || this.State == VerdantGuardianState.Dormant) return;
        Monster? boss = this.ResolveBoss();
        if (boss is null || boss.Health <= 0) return;

        int width = Math.Min(620, Game1.uiViewport.Width - 80);
        int x = (Game1.uiViewport.Width - width) / 2;
        int y = 28;
        Rectangle outer = new(x, y, width, 34);
        Rectangle inner = new(x + 4, y + 4, width - 8, 26);
        float ratio = Math.Clamp(boss.Health / (float)Math.Max(1, boss.MaxHealth), 0f, 1f);
        Rectangle fill = new(inner.X, inner.Y, (int)(inner.Width * ratio), inner.Height);
        e.SpriteBatch.Draw(Game1.staminaRect, outer, Color.Black * 0.78f);
        e.SpriteBatch.Draw(Game1.staminaRect, inner, new Color(44,57,41) * 0.92f);
        e.SpriteBatch.Draw(Game1.staminaRect, fill, new Color(92,197,91) * 0.96f);
        string title = $"{ModEntry.T("boss.verdant.name")}  •  {ModEntry.T("boss.verdant.phase", new { phase = this.Phase })}";
        Vector2 size = Game1.smallFont.MeasureString(title);
        e.SpriteBatch.DrawString(Game1.smallFont, title, new Vector2(Game1.uiViewport.Width / 2f - size.X / 2f, y + 7), Color.White);
    }

    public void PrepareForSave()
    {
        if (this.IsInArena) this.ReturnToRegion1();
    }

    public string DebugEnterArena()
    {
        if (!Context.IsWorldReady) return "Verdant Guardian TEST unavailable: load a save first.";
        GameLocation? arena = this.EnsureLocation();
        if (arena is null) return "Verdant Guardian TEST couldn't create the arena.";
        Game1.warpFarmer(LocationName, PlayerArrivalTile.X, PlayerArrivalTile.Y, 0);
        return "Verdant Guardian TEST: entered Boss I arena without changing the 20-card gate or clear flags.";
    }

    public string Describe()
    {
        Monster? boss = this.ResolveBoss();
        string hp = boss is null ? "none" : $"{Math.Max(0,boss.Health)}/{Math.Max(1,boss.MaxHealth)}";
        string unlocked = string.Join(",", this.Save.Data.BossCardsUnlocked ?? new HashSet<string>());
        return $"Arena={this.IsInArena} | State={this.State} | Phase={this.Phase} | HP={hp} | Cleared={this.Save.Data.Region1BossDefeated} | BossCards=[{unlocked}] | EquippedBoss={this.Save.Data.EquippedBossCardId}";
    }

    private GameLocation? EnsureLocation()
    {
        if (!Context.IsWorldReady || this.CreationFailed) return null;
        GameLocation? existing = Game1.getLocationFromName(LocationName);
        if (existing is not null) return existing;
        try
        {
            GameLocation arena = new(MapAssetName, LocationName);
            Game1.locations.Add(arena);
            if (!this.LoggedCreation)
            {
                this.LoggedCreation = true;
                this.Monitor.Log("Created Cardcha_VerdantGuardianArena for Boss I.", LogLevel.Info);
            }
            return arena;
        }
        catch (Exception ex)
        {
            this.CreationFailed = true;
            this.Monitor.Log($"Couldn't create Verdant Guardian arena: {ex.GetType().Name}: {ex.Message}", LogLevel.Error);
            return null;
        }
    }

    private void StartEncounter(GameLocation arena)
    {
        this.RemoveBossActors(arena);
        GreenSlime proxy = new(BossSpawnPosition(), 0) { MaxHealth = BossMaxHealth, Health = BossMaxHealth, Speed = 0 };
        proxy.modData[BossMarkerKey] = "verdant-guardian";
        arena.characters.Add(proxy);
        this.BossProxy = proxy;
        this.Phase = 1;
        this.PendingPhase = 0;
        this.State = VerdantGuardianState.Intro;
        this.StateStartedAtMs = Environment.TickCount64;
        this.NextDecisionAtMs = this.StateStartedAtMs + IntroDurationMs;
        this.VictoryReturnAtMs = 0;
        this.AttackApplied = false;
        this.VictoryHandled = false;
        this.RootTargets = Array.Empty<Point>();
        this.CooldownUntil.Clear();
        this.LastAttack = null;
        int seed = unchecked((int)Game1.uniqueIDForThisGame + Game1.Date.TotalDays * 7919 + this.Save.Data.AirshipFlightsTaken * 104729);
        this.EncounterRandom = new Random(seed);
        Game1.playSound("discoverMineral");
        Game1.showGlobalMessage(ModEntry.T("boss.verdant.intro"));
        this.Monitor.Log($"Verdant Guardian encounter started. seed={seed}, HP={BossMaxHealth}.", LogLevel.Info);
    }

    private Monster? ResolveBoss()
    {
        if (this.BossProxy is not null) return this.BossProxy;
        this.BossProxy = Game1.getLocationFromName(LocationName)?.characters.OfType<Monster>().FirstOrDefault(m => m.modData.ContainsKey(BossMarkerKey));
        return this.BossProxy;
    }

    private void BeginPhaseTransition(int targetPhase, long now)
    {
        this.PendingPhase = targetPhase;
        this.State = VerdantGuardianState.PhaseTransition;
        this.StateStartedAtMs = now;
        this.AttackApplied = false;
        this.RootTargets = Array.Empty<Point>();
        Game1.playSound("discoverMineral");
        Game1.showGlobalMessage(ModEntry.T($"boss.verdant.transition.{targetPhase}"));
    }

    private void SelectNextAttack(long now)
    {
        List<VerdantGuardianAttack> candidates = new();
        this.AddIfReady(candidates, VerdantGuardianAttack.Swipe, now, 1);
        this.AddIfReady(candidates, VerdantGuardianAttack.RootSpikes, now, 1);
        this.AddIfReady(candidates, VerdantGuardianAttack.SummonAdds, now, 1);
        this.AddIfReady(candidates, VerdantGuardianAttack.Charge, now, 2);
        this.AddIfReady(candidates, VerdantGuardianAttack.VineTrap, now, 2);
        this.AddIfReady(candidates, VerdantGuardianAttack.AreaSlam, now, 3);
        if (candidates.Count == 0) { this.NextDecisionAtMs = now + 180; return; }
        if (candidates.Count > 1 && this.LastAttack is VerdantGuardianAttack last) candidates.Remove(last);
        VerdantGuardianAttack selected = candidates[this.EncounterRandom.Next(candidates.Count)];
        this.LastAttack = selected;
        this.CooldownUntil[selected] = now + CooldownMs(selected, this.Phase);
        this.BeginAttack(selected, now);
    }

    private void AddIfReady(List<VerdantGuardianAttack> list, VerdantGuardianAttack attack, long now, int minPhase)
    {
        if (this.Phase < minPhase) return;
        if (!this.CooldownUntil.TryGetValue(attack, out long until) || now >= until) list.Add(attack);
    }

    private void BeginAttack(VerdantGuardianAttack attack, long now)
    {
        this.StateStartedAtMs = now;
        this.AttackApplied = false;
        switch (attack)
        {
            case VerdantGuardianAttack.Swipe:
                this.State = VerdantGuardianState.SwipeTelegraph; Game1.playSound("Cowboy_gunload"); break;
            case VerdantGuardianAttack.RootSpikes:
                this.RootTargets = BuildRootTargets(PlayerTile(), this.Phase); this.State = VerdantGuardianState.RootSpikesTelegraph; Game1.playSound("leafrustle"); break;
            case VerdantGuardianAttack.SummonAdds:
                this.State = VerdantGuardianState.SummonAdds; Game1.playSound("leafrustle"); break;
            case VerdantGuardianAttack.Charge:
                this.ChargeDirection = PlayerCenter() - BossCenter(this.ResolveBoss());
                if (this.ChargeDirection.LengthSquared() < 0.001f) this.ChargeDirection = Vector2.UnitY; else this.ChargeDirection.Normalize();
                this.State = VerdantGuardianState.ChargeTelegraph; Game1.playSound("clubswipe"); break;
            case VerdantGuardianAttack.VineTrap:
                this.VineTarget = ClampArenaTile(PlayerTile()); this.State = VerdantGuardianState.VineTrapTelegraph; Game1.playSound("leafrustle"); break;
            case VerdantGuardianAttack.AreaSlam:
                this.State = VerdantGuardianState.AreaSlamTelegraph; Game1.playSound("thudStep"); break;
        }
    }

    private void UpdateCharge(Monster boss, long now)
    {
        Vector2 next = boss.Position + this.ChargeDirection * ChargePixelsPerTick;
        next.X = Math.Clamp(next.X, 3 * 64f, 24 * 64f);
        next.Y = Math.Clamp(next.Y, 3 * 64f, 15 * 64f);
        boss.Position = next;
        if (!this.AttackApplied && DistanceTiles(BossCenter(boss), PlayerCenter()) <= 1.15f)
        {
            this.AttackApplied = true;
            DamagePlayer(14, boss);
        }
        if (now - this.StateStartedAtMs >= ChargeDurationMs) this.CompleteAttack(now);
    }

    private void CompleteAttack(long now)
    {
        this.RootTargets = Array.Empty<Point>();
        this.AttackApplied = false;
        this.EnterDecision(now, DecisionGapMs(this.Phase));
    }

    private void EnterDecision(long now, int delayMs)
    {
        this.State = VerdantGuardianState.Decision;
        this.StateStartedAtMs = now;
        this.NextDecisionAtMs = now + delayMs;
    }

    private void SpawnAdds()
    {
        GameLocation? arena = Game1.currentLocation;
        if (arena is null) return;
        int living = arena.characters.OfType<Monster>().Count(m => m.Health > 0 && m.modData.ContainsKey(BossAddMarkerKey));
        int desired = this.Phase == 1 ? 2 : 3;
        int spawnCount = Math.Min(desired, Math.Max(0, MaxActiveAdds - living));
        if (spawnCount <= 0) return;
        Point[] points = AddSpawnTiles.OrderBy(_ => this.EncounterRandom.Next()).Take(spawnCount).ToArray();
        for (int i = 0; i < points.Length; i++)
        {
            Vector2 pos = new(points[i].X * 64f, points[i].Y * 64f);
            Monster add = (i + this.Phase) % 2 == 0 ? new GreenSlime(pos, 0) : new Bug(pos, 0);
            add.MaxHealth = this.Phase switch { 1 => 45, 2 => 60, _ => 75 };
            add.Health = add.MaxHealth;
            add.modData[BossAddMarkerKey] = this.Phase.ToString();
            arena.characters.Add(add);
        }
    }

    private void HandleVictory(long now)
    {
        if (this.VictoryHandled) return;
        this.VictoryHandled = true;
        this.State = VerdantGuardianState.Defeated;
        this.StateStartedAtMs = now;
        this.RemoveAdds();
        bool firstClear = !this.Save.Data.Region1BossDefeated;
        if (firstClear)
        {
            this.Save.Data.Region1BossDefeated = true;
            this.Save.Data.BossCardsUnlocked ??= new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            this.Save.Data.BossCardsUnlocked.Add(BossCardId);
            if (string.IsNullOrWhiteSpace(this.Save.Data.EquippedBossCardId)) this.Save.Data.EquippedBossCardId = BossCardId;
            this.Save.Data.AirshipHighestRegionUnlocked = Math.Max(2, this.Save.Data.AirshipHighestRegionUnlocked);
            bool portableGranted = this.PortableMachine.GrantRegion1BossReward();
            this.Save.Save();
            Game1.playSound("yoba");
            Game1.showGlobalMessage(ModEntry.T("boss.verdant.victory.first", new { card = ModEntry.T("boss.verdant.card.name"), portable = portableGranted ? ModEntry.T("boss.verdant.reward.portable") : "" }));
        }
        else
        {
            Game1.playSound("questcomplete");
            Game1.showGlobalMessage(ModEntry.T("boss.verdant.victory.rematch"));
        }
        this.State = VerdantGuardianState.Victory;
        this.VictoryReturnAtMs = now + VictoryReturnDelayMs;
        this.Monitor.Log($"Verdant Guardian defeated. firstClear={firstClear}, bossCard={BossCardId}, regionUnlock={this.Save.Data.AirshipHighestRegionUnlocked}.", LogLevel.Info);
    }

    private void ReturnToRegion1()
    {
        if (!Context.IsWorldReady) return;
        GameLocation? hub = Game1.getLocationFromName(AirshipFoundationService.Region1LocationName);
        if (hub is null) return;
        this.RemoveBossActors(Game1.getLocationFromName(LocationName));
        this.State = VerdantGuardianState.Dormant;
        this.VictoryReturnAtMs = 0;
        Game1.warpFarmer(AirshipFoundationService.Region1LocationName, 20, 4, 2);
    }

    private void ResetRuntime(bool removeActors)
    {
        if (removeActors) this.RemoveBossActors(Game1.getLocationFromName(LocationName));
        this.BossProxy = null;
        this.State = VerdantGuardianState.Dormant;
        this.LastAttack = null;
        this.Phase = 1;
        this.PendingPhase = 0;
        this.StateStartedAtMs = 0;
        this.NextDecisionAtMs = 0;
        this.VictoryReturnAtMs = 0;
        this.AttackApplied = false;
        this.VictoryHandled = false;
        this.RootTargets = Array.Empty<Point>();
        this.VineTarget = Point.Zero;
        this.ChargeDirection = Vector2.Zero;
        this.CooldownUntil.Clear();
    }

    private void RemoveBossActors(GameLocation? arena)
    {
        if (arena is null) return;
        foreach (NPC actor in arena.characters.Where(n => n.modData.ContainsKey(BossMarkerKey) || n.modData.ContainsKey(BossAddMarkerKey)).ToList()) arena.characters.Remove(actor);
    }

    private void RemoveAdds()
    {
        GameLocation? arena = Game1.getLocationFromName(LocationName);
        if (arena is null) return;
        foreach (NPC actor in arena.characters.Where(n => n.modData.ContainsKey(BossAddMarkerKey)).ToList()) arena.characters.Remove(actor);
    }

    private static int CooldownMs(VerdantGuardianAttack attack, int phase) => attack switch
    {
        VerdantGuardianAttack.Swipe => phase switch { 1 => 2200, 2 => 1800, _ => 1500 },
        VerdantGuardianAttack.RootSpikes => phase switch { 1 => 5200, 2 => 4500, _ => 3600 },
        VerdantGuardianAttack.SummonAdds => phase switch { 1 => 16000, 2 => 14000, _ => 12500 },
        VerdantGuardianAttack.Charge => phase == 2 ? 7000 : 5600,
        VerdantGuardianAttack.VineTrap => phase == 2 ? 8500 : 6500,
        VerdantGuardianAttack.AreaSlam => 7200,
        _ => 2500
    };

    private static int DecisionGapMs(int phase) => phase switch { 1 => 700, 2 => 550, _ => 400 };

    private static Point[] BuildRootTargets(Point center, int phase)
    {
        List<Point> targets = new() { ClampArenaTile(center), ClampArenaTile(new Point(center.X - 2, center.Y)), ClampArenaTile(new Point(center.X + 2, center.Y)) };
        if (phase >= 2) { targets.Add(ClampArenaTile(new Point(center.X, center.Y - 2))); targets.Add(ClampArenaTile(new Point(center.X, center.Y + 2))); }
        if (phase >= 3) { targets.Add(ClampArenaTile(new Point(center.X - 2, center.Y - 2))); targets.Add(ClampArenaTile(new Point(center.X + 2, center.Y + 2))); }
        return targets.Distinct().ToArray();
    }

    private static Point ClampArenaTile(Point p) => new(Math.Clamp(p.X, 2, 25), Math.Clamp(p.Y, 2, 16));
    private bool PlayerInsideVineZone() { Point p = PlayerTile(); return Math.Abs(p.X - this.VineTarget.X) <= 1 && Math.Abs(p.Y - this.VineTarget.Y) <= 1; }
    private static Point PlayerTile() => new((int)(Game1.player.Position.X / 64f), (int)(Game1.player.Position.Y / 64f));
    private static Vector2 PlayerCenter() => Game1.player.Position + new Vector2(32f, 32f);
    private static Vector2 BossSpawnPosition() => new(BossSpawnTile.X * 64f, BossSpawnTile.Y * 64f);
    private static Vector2 BossCenter(Monster? boss) => boss is null ? BossSpawnPosition() + new Vector2(32f, 32f) : boss.Position + new Vector2(32f, 32f);
    private static float DistanceTiles(Vector2 a, Vector2 b) => Vector2.Distance(a, b) / 64f;
    private static void DamagePlayer(int damage, Monster damager) { if (Game1.player.health > 0) Game1.player.takeDamage(damage, false, damager); }

    private static void DrawTileTelegraph(SpriteBatch b, Point tile, Color color) => DrawWorldRect(b, new Rectangle(tile.X * 64, tile.Y * 64, 64, 64), color);
    private static void DrawZoneTelegraph(SpriteBatch b, Point center, int radiusTiles, Color color) => DrawWorldRect(b, new Rectangle((center.X-radiusTiles)*64, (center.Y-radiusTiles)*64, (radiusTiles*2+1)*64, (radiusTiles*2+1)*64), color);
    private static void DrawRadiusTelegraph(SpriteBatch b, Vector2 centerWorld, float radiusTiles, Color color) { int r = (int)(radiusTiles * 64f); DrawWorldRect(b, new Rectangle((int)centerWorld.X-r, (int)centerWorld.Y-r, r*2, r*2), color); }
    private static void DrawChargeLane(SpriteBatch b, Vector2 startWorld, Vector2 direction)
    {
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, startWorld);
        Vector2 end = local + direction * 480f;
        for (int i = 1; i <= 12; i++)
        {
            Vector2 p = Vector2.Lerp(local, end, i / 12f);
            b.Draw(Game1.staminaRect, new Rectangle((int)p.X - 9, (int)p.Y - 9, 18, 18), new Color(235,205,82) * 0.42f);
        }
    }
    private static void DrawWorldRect(SpriteBatch b, Rectangle world, Color color)
    {
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, new Vector2(world.X, world.Y));
        b.Draw(Game1.staminaRect, new Rectangle((int)local.X, (int)local.Y, world.Width, world.Height), color);
    }
}
'''
(ROOT / 'Services/VerdantGuardianBossService.cs').write_text(boss_service)

# Arena: 28x20, circular stone clearing inside a solid vanilla-tile border, open south retreat lane.
def csv(rows):
    return '\n'.join(','.join(str(v) for v in row) + ',' for row in rows)

w, h = 28, 20
back = []
buildings = []
front = [[0] * w for _ in range(h)]
for y in range(h):
    brow = []
    grow = []
    for x in range(w):
        dx = x - 13.5
        dy = y - 9.0
        stone = dx * dx / 75.0 + dy * dy / 48.0 <= 1.0
        brow.append(457 if stone else (382 if (x + y * 3) % 31 == 0 else 381))
        border = x == 0 or x == w - 1 or y == 0 or y == h - 1
        if y == h - 1 and x in (13, 14):
            border = False
        pillar = (x, y) in {(5,5),(22,5),(5,14),(22,14)}
        grow.append(381 if border or pillar else 0)
    back.append(brow)
    buildings.append(grow)

arena = f'''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" renderorder="right-down" width="{w}" height="{h}" tilewidth="16" tileheight="16" infinite="0" nextlayerid="4" nextobjectid="1">
 <properties>
  <property name="Outdoors" value="T" />
  <property name="CardchaRegionVersion" value="{VERSION_NEW}" />
  <property name="CardchaRegionRole" value="region1-boss-arena|verdant-guardian|boss1" />
  <property name="CardchaAssetPolicy" value="cardcha-owned-map|vanilla-tiles-only|no-third-party-assets" />
 </properties>
 <tileset firstgid="1" name="spring_outdoorsTileSheet" tilewidth="16" tileheight="16" tilecount="1975" columns="25">
  <image source=".spring_outdoorsTileSheet.png" width="400" height="1264" />
 </tileset>
 <layer id="1" name="Back" width="{w}" height="{h}"><data encoding="csv">\n{csv(back)}\n</data></layer>
 <layer id="2" name="Buildings" width="{w}" height="{h}"><data encoding="csv">\n{csv(buildings)}\n</data></layer>
 <layer id="3" name="Front" width="{w}" height="{h}"><data encoding="csv">\n{csv(front)}\n</data></layer>
</map>\n'''
(ROOT / 'assets/verdant_guardian_arena.tmx').write_text(arena)

# Airship boss sigil now enters the real Boss I arena at 20 cards.
airship = ROOT / 'Services/AirshipFoundationService.cs'
text = airship.read_text()
old = '''        if (Touches(action, bossSigil) || PlayerIsNear(bossSigil))\n        {\n            this.Helper.Input.Suppress(e.Button);\n            Game1.drawObjectDialogue(ModEntry.T(\"airship.region1.boss.staging\"));\n        }'''
new = '''        if (Touches(action, bossSigil) || PlayerIsNear(bossSigil))\n        {\n            this.Helper.Input.Suppress(e.Button);\n            int owned = this.Save.Data.OwnedCards?.Count ?? 0;\n            if (owned < Region1GateCardRequirement)\n            {\n                Game1.drawObjectDialogue(ModEntry.T(\"airship.region1.gate.locked\", new { cards = owned, required = Region1GateCardRequirement }));\n                return;\n            }\n\n            GameLocation? arena = Game1.getLocationFromName(VerdantGuardianBossService.LocationName);\n            if (arena is null)\n            {\n                Game1.drawObjectDialogue(ModEntry.T(\"boss.verdant.arena.unavailable\"));\n                return;\n            }\n\n            Game1.playSound(\"wand\");\n            Game1.warpFarmer(\n                VerdantGuardianBossService.LocationName,\n                VerdantGuardianBossService.PlayerArrivalTile.X,\n                VerdantGuardianBossService.PlayerArrivalTile.Y,\n                0\n            );\n        }'''
if old not in text:
    raise SystemExit('Airship boss staging anchor missing')
airship.write_text(text.replace(old, new, 1))

# ModEntry wiring.
mod = ROOT / 'ModEntry.cs'
text = mod.read_text()
text = text.replace('''    private AirshipFoundationService Airship = null!;\n    private CardTestLabService CardLab = null!;''', '''    private AirshipFoundationService Airship = null!;\n    private VerdantGuardianBossService VerdantGuardian = null!;\n    private CardTestLabService CardLab = null!;''', 1)
text = text.replace('''        this.Airship = new AirshipFoundationService(helper, this.Monitor, this.Save, this.Controller);\n        this.CardLab = new CardTestLabService(this.Cards, this.Save, this.Combat);''', '''        this.Airship = new AirshipFoundationService(helper, this.Monitor, this.Save, this.Controller);\n        this.VerdantGuardian = new VerdantGuardianBossService(helper, this.Monitor, this.Save, this.PortableMachine);\n        this.CardLab = new CardTestLabService(this.Cards, this.Save, this.Combat);''', 1)
text = text.replace('''        helper.Events.Content.AssetRequested += this.Airship.OnAssetRequested;\n        helper.Events.Content.AssetRequested += this.CardArena.OnAssetRequested;''', '''        helper.Events.Content.AssetRequested += this.Airship.OnAssetRequested;\n        helper.Events.Content.AssetRequested += this.VerdantGuardian.OnAssetRequested;\n        helper.Events.Content.AssetRequested += this.CardArena.OnAssetRequested;''', 1)
text = text.replace('''        helper.Events.GameLoop.DayStarted += this.ChaChaSupport.OnDayStarted;\n        helper.Events.GameLoop.TimeChanged += this.Mystery.OnTimeChanged;''', '''        helper.Events.GameLoop.DayStarted += this.ChaChaSupport.OnDayStarted;\n        helper.Events.GameLoop.DayStarted += this.VerdantGuardian.OnDayStarted;\n        helper.Events.GameLoop.TimeChanged += this.Mystery.OnTimeChanged;''', 1)
text = text.replace('''        helper.Events.GameLoop.UpdateTicked += this.CardArena.OnUpdateTicked;\n        helper.Events.GameLoop.UpdateTicked += this.ChaChaBossForm.OnUpdateTicked;''', '''        helper.Events.GameLoop.UpdateTicked += this.CardArena.OnUpdateTicked;\n        helper.Events.GameLoop.UpdateTicked += this.VerdantGuardian.OnUpdateTicked;\n        helper.Events.GameLoop.UpdateTicked += this.ChaChaBossForm.OnUpdateTicked;''', 1)
text = text.replace('''        helper.Events.GameLoop.ReturnedToTitle += this.CardArena.OnReturnedToTitle;\n        helper.Events.Display.RenderedHud += this.OnRenderedHud;''', '''        helper.Events.GameLoop.ReturnedToTitle += this.CardArena.OnReturnedToTitle;\n        helper.Events.GameLoop.ReturnedToTitle += this.VerdantGuardian.OnReturnedToTitle;\n        helper.Events.Display.RenderedHud += this.OnRenderedHud;''', 1)
text = text.replace('''        helper.Events.Display.RenderedHud += this.ChaChaSupport.OnRenderedHud;\n        helper.Events.Display.RenderedWorld += this.Story.OnRenderedWorld;''', '''        helper.Events.Display.RenderedHud += this.ChaChaSupport.OnRenderedHud;\n        helper.Events.Display.RenderedHud += this.VerdantGuardian.OnRenderedHud;\n        helper.Events.Display.RenderedWorld += this.Story.OnRenderedWorld;''', 1)
text = text.replace('''        helper.Events.Display.RenderedWorld += this.Airship.OnRenderedWorld;\n        helper.Events.Display.MenuChanged += this.BookTab.OnMenuChanged;''', '''        helper.Events.Display.RenderedWorld += this.Airship.OnRenderedWorld;\n        helper.Events.Display.RenderedWorld += this.VerdantGuardian.OnRenderedWorld;\n        helper.Events.Display.MenuChanged += this.BookTab.OnMenuChanged;''', 1)
text = text.replace('''        helper.Events.Input.ButtonPressed += this.Airship.OnButtonPressed;\n        helper.Events.Input.ButtonPressed += this.CardLabOverlay.OnButtonPressed;''', '''        helper.Events.Input.ButtonPressed += this.Airship.OnButtonPressed;\n        helper.Events.Input.ButtonPressed += this.VerdantGuardian.OnButtonPressed;\n        helper.Events.Input.ButtonPressed += this.CardLabOverlay.OnButtonPressed;''', 1)
text = text.replace('''        helper.Events.Player.Warped += this.Airship.OnWarped;\n        helper.Events.Player.Warped += this.CardArena.OnWarped;''', '''        helper.Events.Player.Warped += this.Airship.OnWarped;\n        helper.Events.Player.Warped += this.VerdantGuardian.OnWarped;\n        helper.Events.Player.Warped += this.CardArena.OnWarped;''', 1)
text = text.replace('''        helper.ConsoleCommands.Add(\"cardcha_test_airship_flyby\", \"TEST ONLY: replay the pre-MiMi Farm Airship flyby without changing save progression.\", this.CommandTestAirshipFlyby);''', '''        helper.ConsoleCommands.Add(\"cardcha_test_airship_flyby\", \"TEST ONLY: replay the pre-MiMi Farm Airship flyby without changing save progression.\", this.CommandTestAirshipFlyby);\n        helper.ConsoleCommands.Add(\"cardcha_test_boss1\", \"TEST ONLY: enter the Verdant Guardian arena without changing the 20-card gate.\", (_, _) => this.Monitor.Log(this.VerdantGuardian.DebugEnterArena(), LogLevel.Alert));\n        helper.ConsoleCommands.Add(\"cardcha_boss1_status\", \"Show Verdant Guardian runtime/save state.\", (_, _) => this.Monitor.Log(this.VerdantGuardian.Describe(), LogLevel.Alert));''', 1)
text = text.replace('''        this.Airship.OnSaveLoaded();\n        (int storageNormal, int storageShiny) = this.Resources.SyncStorageModeOnLoad();''', '''        this.Airship.OnSaveLoaded();\n        this.VerdantGuardian.OnSaveLoaded();\n        (int storageNormal, int storageShiny) = this.Resources.SyncStorageModeOnLoad();''', 1)
text = text.replace('''        this.CardArena.PrepareForSave();\n        this.CardLab.EndSession();''', '''        this.VerdantGuardian.PrepareForSave();\n        this.CardArena.PrepareForSave();\n        this.CardLab.EndSession();''', 1)
text = text.replace('''Cardcha! 0.3.0-alpha.28.0.4.14.4.5.6.1 READABILITY + PROGRESSION + MIMI STYLE TEST''', f'''Cardcha! {VERSION_NEW} VERDANT GUARDIAN BOSS I TEST''', 1)
mod.write_text(text)

# i18n additions.
def add_i18n(path, values):
    p = ROOT / 'i18n' / path
    data = json.loads(p.read_text())
    data.update(values)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

add_i18n('default.json', {
    'airship.region1.boss.staging': 'BOSS I // The Verdant Guardian is waiting beyond the sigil.',
    'boss.verdant.name': 'VERDANT GUARDIAN',
    'boss.verdant.phase': 'PHASE {{phase}}',
    'boss.verdant.phase.1': 'Verdant Guardian — Awakening',
    'boss.verdant.phase.2': 'Verdant Guardian — Enraged Roots',
    'boss.verdant.phase.3': 'Verdant Guardian — Heart of the Grove',
    'boss.verdant.intro': 'The ancient grove stirs. Something enormous wakes beneath the roots...',
    'boss.verdant.transition.2': 'The roots tear through the old stone. The Guardian is enraged!',
    'boss.verdant.transition.3': 'The emerald core opens. The Heart of the Grove is fully awake!',
    'boss.verdant.victory.first': 'BOSS I CLEARED! Boss Card unlocked: {{card}}. Region II resonance detected. {{portable}}',
    'boss.verdant.victory.rematch': 'Verdant Guardian defeated again. The grove settles back into silence.',
    'boss.verdant.card.name': 'Verdant Core',
    'boss.verdant.reward.portable': 'Portable Cardcha Machine obtained!',
    'boss.verdant.retreat': 'You retreat from the Ancient Grove. The Guardian lets the roots close behind you.',
    'boss.verdant.arena.unavailable': 'The Verdant Guardian arena cannot stabilize right now. Reload the day and try again.'
})

add_i18n('vi.json', {
    'airship.region1.boss.staging': 'BOSS I // Verdant Guardian đang chờ phía sau ấn chú.',
    'boss.verdant.name': 'VERDANT GUARDIAN',
    'boss.verdant.phase': 'GIAI ĐOẠN {{phase}}',
    'boss.verdant.phase.1': 'Verdant Guardian — Thức Tỉnh',
    'boss.verdant.phase.2': 'Verdant Guardian — Cuồng Nộ Rễ Cây',
    'boss.verdant.phase.3': 'Verdant Guardian — Trái Tim Khu Rừng',
    'boss.verdant.intro': 'Khu rừng cổ khẽ rung chuyển. Một thứ khổng lồ đang thức giấc dưới những tầng rễ...',
    'boss.verdant.transition.2': 'Rễ cây xé toạc nền đá cổ. Verdant Guardian đã nổi giận!',
    'boss.verdant.transition.3': 'Lõi lục bảo mở tung. Trái Tim Khu Rừng đã hoàn toàn thức tỉnh!',
    'boss.verdant.victory.first': 'ĐÃ HẠ BOSS I! Mở khóa Boss Card: {{card}}. Đã phát hiện cộng hưởng của Khu Vực II. {{portable}}',
    'boss.verdant.victory.rematch': 'Verdant Guardian lại bị đánh bại. Khu rừng dần trở về yên tĩnh.',
    'boss.verdant.card.name': 'Verdant Core',
    'boss.verdant.reward.portable': 'Đã nhận Máy Cardcha Cầm Tay!',
    'boss.verdant.retreat': 'Bạn rút khỏi Khu Rừng Cổ. Verdant Guardian để những tầng rễ khép lại phía sau.',
    'boss.verdant.arena.unavailable': 'Đấu trường Verdant Guardian hiện chưa thể ổn định. Hãy tải lại ngày rồi thử lại.'
})

# Build handoff and latest pointer.
handoff = f'''# Alpha.28 0650 — Verdant Guardian Boss I functional prototype\n\nStatus: implementation candidate; in-game acceptance pending.\n\n## Product\n- Region I Boss Gate at 20 unique cards now enters `Cardcha_VerdantGuardianArena`.\n- Functional Boss I state machine: 3 phases, six attacks, telegraphs, HUD HP bar, adds, charge, retreat and victory return.\n- First clear persists `Region1BossDefeated`, unlocks/equips `verdant_core`, unlocks Region II hook, and grants Portable Cardcha Machine if not already owned.\n- Boss body is deliberately a vanilla GreenSlime proxy in this build. Approved custom Verdant Guardian art is a separate art pass; do not mistake the proxy for final visual canon.\n\n## Locked technical contract\nSee `handoff/VERDANT_GUARDIAN_TECHNICAL_SPEC.md` and `handoff/BOSS_CONCEPT_CANON.md`.\n\n## Balance\nHP/damage/cooldowns are provisional. Tune only after in-game feel testing.\n\n## Regression guard\n- Save schema remains 19.\n- Boss Form duration remains 10s.\n- Boss Energy gain remains 1/3.\n- 76/76 active-card audit untouched.\n- Forest gate/Airship visuals/routes untouched.\n- 0648J MiMi Profile/Gift Log scale and Wizard stair are still pending in-game acceptance.\n'''
Path('handoff/ALPHA28_0650_VERDANT_GUARDIAN_BOSS1.md').write_text(handoff)
latest = f'''# Latest Cardcha handoff\n\nCurrent development branch:\n`cardcha-alpha28-0650-verdant-guardian-boss1`\n\nCurrent build:\n`{VERSION_NEW}`\n\nRead first:\n- `handoff/ALPHA28_0650_VERDANT_GUARDIAN_BOSS1.md`\n- `handoff/VERDANT_GUARDIAN_TECHNICAL_SPEC.md`\n- `handoff/BOSS_CONCEPT_CANON.md`\n\n## Current acceptance state\n- Verdant Guardian Boss I functional prototype: CI/compile candidate, in-game acceptance pending.\n- Region I Hunt Run 4-of-6 remains part of the route into the existing 20-card gate.\n- 0648J MiMi Gift/Profile 50% + Wizard stair remains pending; do not silently mark accepted.\n\n## Locked regression guard\nSave schema 19; Boss Form 10 sec; Boss Energy 1/3; 76/76 active cards; Forest Arcane Gate and collision; Airship route/visual; MiMi HOME/TV/LATE; card canon.\n'''
Path('handoff/LATEST_CARDCHA_HANDOFF.md').write_text(latest)

print('0650 generator complete')
