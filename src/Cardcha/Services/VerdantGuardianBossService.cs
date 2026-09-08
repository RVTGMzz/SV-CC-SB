using Microsoft.Xna.Framework;
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
    Victory,
    TotemStagger
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
/// Boss I functional vertical slice. A vanilla GreenSlime remains the gameplay/collision proxy;
/// 0652 overlays Cardcha-owned custom art while routing, telegraphs, phases, damage, save flags and rewards remain authoritative here.
/// </summary>
internal sealed class VerdantGuardianBossService
{
    public const string LocationName = "Cardcha_VerdantGuardianArena";
    public const string MapAssetName = "Maps/Cardcha_VerdantGuardianArena";
    public const string BossCardId = "verdant_core";
    public const string BossMarkerKey = "Ronvotri.Cardcha/VerdantGuardian";
    public const string BossAddMarkerKey = "Ronvotri.Cardcha/VerdantGuardianAdd";
    public const string BossAddTypeKey = "Ronvotri.Cardcha/VerdantGuardianAddType";
    public const string TotemMarkerKey = "Ronvotri.Cardcha/VerdantSeedTotem";
    public const string TotemIndexKey = "Ronvotri.Cardcha/VerdantSeedTotemIndex";
    public const string BriarlingId = "briarling";
    public const string LeafWispId = "leaf_wisp";
    public static readonly Point PlayerArrivalTile = new(14, 17);

    private const string MapPath = "assets/verdant_guardian_arena.tmx";
    // 0665 Region I balance candidate. Phase 1 teaches the moves, Phase 2/3 add pressure.
    private const int BossMaxHealth = 1600;
    private const int SwipeDamageP1 = 10;
    private const int SwipeDamageP2 = 12;
    private const int SwipeDamageP3 = 14;
    private const int RootDamageP1 = 8;
    private const int RootDamageP2 = 10;
    private const int RootDamageP3 = 12;
    private const int ChargeDamageP1 = 14;
    private const int ChargeDamageP2 = 16;
    private const int ChargeDamageP3 = 19;
    private const int VineDamageP1 = 4;
    private const int VineDamageP2 = 5;
    private const int VineDamageP3 = 7;
    private const int SlamDamageP1 = 16;
    private const int SlamDamageP2 = 18;
    private const int SlamDamageP3 = 22;
    private const float HeavyRecoilCapPixels = 18f;
    private const float HeavyRecenterFactor = 0.22f;
    private const int IntroDurationMs = 1500;
    private const int PhaseTransitionDurationMs = 1600;
    private const int VictoryReturnDelayMs = 3500;
    private const int DefeatSequenceDurationMs = 2200;
    private const int SwipeTelegraphMs = 700;
    private const int RootTelegraphMs = 900;
    private const int SummonTelegraphMs = 600;
    private const int ChargeTelegraphMs = 900;
    private const int ChargeDurationMs = 720;
    private const int VineTelegraphMs = 900;
    private const int VineActiveMs = 2500;
    private const int SlamTelegraphMs = 1100;
    private const int MaxActiveAdds = 4;
    private const int TotemMaxHealth = 90;
    private const int TotemStaggerDurationMs = 1200;
    private const float ChargePixelsPerTick = 17f;

    private static readonly Point BossSpawnTile = new(14, 7);
    private static readonly Point RetreatTile = new(14, 18);
    private static readonly Point[] AddSpawnTiles = { new(5, 5), new(22, 5), new(5, 14), new(22, 14) };
    private static readonly Point[] TotemTiles = { new(3, 3), new(24, 3), new(3, 16), new(24, 16) };

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
    private Point[] PendingSummonTiles = Array.Empty<Point>();
    private string[] PendingSummonKinds = Array.Empty<string>();
    private Point VineTarget;
    private Vector2 ChargeDirection;
    private Vector2 HeavyAnchor;
    private Random EncounterRandom = new(1);
    private int LastLivingTotemCount;
    private long LastTotemHitAtMs;
    private int LastTotemHitIndex = -1;

    public VerdantGuardianBossService(IModHelper helper, IMonitor monitor, SaveService save, PortableMachineService portableMachine)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
        this.PortableMachine = portableMachine;
    }

    public bool IsInArena => Context.IsWorldReady
        && Game1.currentLocation?.NameOrUniqueName.Equals(LocationName, StringComparison.OrdinalIgnoreCase) == true;

    // 0652 visual layer: read-only snapshot. Combat state remains owned exclusively by this service.
    internal VerdantGuardianState VisualState => this.State;
    internal int VisualPhase => this.Phase;
    internal long VisualStateStartedAtMs => this.StateStartedAtMs;
    internal Monster? VisualBoss => this.ResolveBoss();
    internal Point[] VisualRootTargets => this.RootTargets;
    internal Point[] VisualSummonTargets => this.PendingSummonTiles;
    internal string[] VisualSummonKinds => this.PendingSummonKinds;
    internal Monster[] VisualAdds => Game1.getLocationFromName(LocationName)?.characters.OfType<Monster>()
        .Where(m => m.Health > 0 && m.modData.ContainsKey(BossAddMarkerKey)).ToArray() ?? Array.Empty<Monster>();
    internal Monster[] VisualTotems => Game1.getLocationFromName(LocationName)?.characters.OfType<Monster>()
        .Where(m => m.Health > 0 && m.modData.ContainsKey(TotemMarkerKey)).ToArray() ?? Array.Empty<Monster>();
    internal long VisualLastTotemHitAtMs => this.LastTotemHitAtMs;
    internal int VisualLastTotemHitIndex => this.LastTotemHitIndex;
    internal Point VisualVineTarget => this.VineTarget;
    internal Vector2 VisualChargeDirection => this.ChargeDirection;
    internal Vector2 VisualBossCenter => BossCenter(this.ResolveBoss());

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
        this.UpdateTotemAnchors();
        this.ObserveTotemBreaks(now);
        if (this.State == VerdantGuardianState.Victory)
        {
            if (this.VictoryReturnAtMs > 0 && now >= this.VictoryReturnAtMs)
                this.ReturnToRegion1();
            return;
        }

        Monster? boss = this.ResolveBoss();
        if (boss is null || boss.Health <= 0)
        {
            if (this.State != VerdantGuardianState.Defeated)
                this.BeginDefeat(now);
            else if (now - this.StateStartedAtMs >= DefeatSequenceDurationMs)
                this.CompleteVictory(now);
            return;
        }

        // 0665 heavy-body tuning: allow a tiny hit reaction, but never cumulative wall-pinning.
        // HeavyAnchor only moves through Cardcha-owned motion (Charge/phase recenter).
        if (this.State != VerdantGuardianState.Charging && this.State != VerdantGuardianState.PhaseTransition)
            this.ApplyHeavyRecoil(boss);

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
                    if (!this.AttackApplied && DistanceTiles(BossCenter(boss), PlayerCenter()) <= 2.35f) DamagePlayer(PhaseDamage(SwipeDamageP1, SwipeDamageP2, SwipeDamageP3, this.Phase), boss);
                    this.AttackApplied = true;
                    this.CompleteAttack(now);
                }
                break;
            case VerdantGuardianState.RootSpikesTelegraph:
                if (now - this.StateStartedAtMs >= RootTelegraphMs)
                {
                    if (!this.AttackApplied && this.RootTargets.Contains(PlayerTile())) DamagePlayer(PhaseDamage(RootDamageP1, RootDamageP2, RootDamageP3, this.Phase), boss);
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
                    DamagePlayer(PhaseDamage(VineDamageP1, VineDamageP2, VineDamageP3, this.Phase), boss);
                    Game1.player.Halt();
                }
                if (now - this.StateStartedAtMs >= VineActiveMs) this.CompleteAttack(now);
                break;
            case VerdantGuardianState.AreaSlamTelegraph:
                if (now - this.StateStartedAtMs >= SlamTelegraphMs)
                {
                    if (!this.AttackApplied && DistanceTiles(BossCenter(boss), PlayerCenter()) <= 4.1f) DamagePlayer(PhaseDamage(SlamDamageP1, SlamDamageP2, SlamDamageP3, this.Phase), boss);
                    this.AttackApplied = true;
                    Game1.playSound("explosion");
                    this.CompleteAttack(now);
                }
                break;
            case VerdantGuardianState.TotemStagger:
                boss.Position = this.HeavyAnchor;
                if (now - this.StateStartedAtMs >= TotemStaggerDurationMs)
                    this.EnterDecision(now, 420);
                break;
            case VerdantGuardianState.PhaseTransition:
                boss.Position = BossSpawnPosition();
                this.HeavyAnchor = boss.Position;
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

    public string DebugSummonWave()
    {
        if (!this.IsInArena) return "Verdant summon TEST unavailable: enter Boss I arena first.";
        this.RemoveAdds();
        this.PrepareSummonPlan();
        string planned = string.Join(",", this.PendingSummonKinds);
        this.SpawnAdds();
        return $"Verdant summon TEST spawned phase {this.Phase}: [{planned}]. Vanilla proxy art is hidden; Cardcha summon visuals are active.";
    }

    public string Describe()
    {
        Monster? boss = this.ResolveBoss();
        string hp = boss is null ? "none" : $"{Math.Max(0,boss.Health)}/{Math.Max(1,boss.MaxHealth)}";
        string unlocked = string.Join(",", this.Save.Data.BossCardsUnlocked ?? new HashSet<string>());
        string adds = string.Join(",", this.VisualAdds.Select(m => m.modData.TryGetValue(BossAddTypeKey, out string? kind) ? kind : "unknown"));
        return $"Arena={this.IsInArena} | State={this.State} | Phase={this.Phase} | HP={hp} | Balance=0665 | Adds=[{adds}] | Cleared={this.Save.Data.Region1BossDefeated} | BossCards=[{unlocked}] | EquippedBoss={this.Save.Data.EquippedBossCardId}";
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
        this.SpawnTotems(arena);
        this.HeavyAnchor = proxy.Position;
        this.Phase = 1;
        this.PendingPhase = 0;
        this.State = VerdantGuardianState.Intro;
        this.StateStartedAtMs = Environment.TickCount64;
        this.NextDecisionAtMs = this.StateStartedAtMs + IntroDurationMs;
        this.VictoryReturnAtMs = 0;
        this.AttackApplied = false;
        this.VictoryHandled = false;
        this.LastLivingTotemCount = 4;
        this.LastTotemHitAtMs = 0;
        this.LastTotemHitIndex = -1;
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
        this.PendingSummonTiles = Array.Empty<Point>();
        this.PendingSummonKinds = Array.Empty<string>();
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
        this.CooldownUntil[selected] = now + this.GetAttackCooldownMs(selected, this.Phase);
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
                this.PrepareSummonPlan();
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
        this.HeavyAnchor = next;
        if (!this.AttackApplied && DistanceTiles(BossCenter(boss), PlayerCenter()) <= 1.15f)
        {
            this.AttackApplied = true;
            DamagePlayer(PhaseDamage(ChargeDamageP1, ChargeDamageP2, ChargeDamageP3, this.Phase), boss);
        }
        if (now - this.StateStartedAtMs >= ChargeDurationMs) this.CompleteAttack(now);
    }

    private void CompleteAttack(long now)
    {
        this.RootTargets = Array.Empty<Point>();
        this.PendingSummonTiles = Array.Empty<Point>();
        this.PendingSummonKinds = Array.Empty<string>();
        this.AttackApplied = false;
        this.EnterDecision(now, DecisionGapMs(this.Phase));
    }

    private void EnterDecision(long now, int delayMs)
    {
        this.State = VerdantGuardianState.Decision;
        this.StateStartedAtMs = now;
        this.NextDecisionAtMs = now + delayMs;
    }

    private void PrepareSummonPlan()
    {
        GameLocation? arena = Game1.currentLocation;
        if (arena is null)
        {
            this.PendingSummonTiles = Array.Empty<Point>();
            this.PendingSummonKinds = Array.Empty<string>();
            return;
        }

        int living = arena.characters.OfType<Monster>()
            .Count(m => m.Health > 0 && m.modData.ContainsKey(BossAddMarkerKey));
        int desired = this.Phase == 1 ? 2 : 3;
        int spawnCount = Math.Min(desired, Math.Max(0, MaxActiveAdds - living));
        if (spawnCount <= 0)
        {
            this.PendingSummonTiles = Array.Empty<Point>();
            this.PendingSummonKinds = Array.Empty<string>();
            return;
        }

        this.PendingSummonTiles = AddSpawnTiles
            .OrderBy(_ => this.EncounterRandom.Next())
            .Take(spawnCount)
            .ToArray();

        string[] phasePool = this.Phase switch
        {
            1 => new[] { BriarlingId, BriarlingId },
            2 => new[] { BriarlingId, LeafWispId, BriarlingId },
            _ => new[] { LeafWispId, BriarlingId, LeafWispId },
        };
        this.PendingSummonKinds = Enumerable.Range(0, spawnCount)
            .Select(i => phasePool[i % phasePool.Length])
            .ToArray();
    }

    private void SpawnAdds()
    {
        GameLocation? arena = Game1.currentLocation;
        if (arena is null) return;
        if (this.PendingSummonTiles.Length == 0) this.PrepareSummonPlan();

        int count = Math.Min(this.PendingSummonTiles.Length, this.PendingSummonKinds.Length);
        for (int i = 0; i < count; i++)
        {
            Point point = this.PendingSummonTiles[i];
            string kind = this.PendingSummonKinds[i];
            Vector2 pos = new(point.X * 64f, point.Y * 64f);
            Monster add;
            if (string.Equals(kind, LeafWispId, StringComparison.OrdinalIgnoreCase))
            {
                add = new Bug(pos, 0);
                add.MaxHealth = this.Phase switch { 1 => 34, 2 => 46, _ => 58 };
                add.Speed = this.Phase switch { 1 => 4, 2 => 5, _ => 5 };
            }
            else
            {
                add = new GreenSlime(pos, 0);
                add.MaxHealth = this.Phase switch { 1 => 50, 2 => 68, _ => 84 };
                add.Speed = this.Phase switch { 1 => 2, 2 => 3, _ => 3 };
                kind = BriarlingId;
            }

            add.Health = add.MaxHealth;
            add.modData[BossAddMarkerKey] = this.Phase.ToString();
            add.modData[BossAddTypeKey] = kind;
            // Hide only the vanilla proxy art. AI, collision, damage and death routing remain native/stable.
            add.isInvisible.Value = true;
            arena.characters.Add(add);
        }

        if (count > 0) Game1.playSound("debuffSpell");
        this.PendingSummonTiles = Array.Empty<Point>();
        this.PendingSummonKinds = Array.Empty<string>();
    }

    private void BeginDefeat(long now)
    {
        if (this.State == VerdantGuardianState.Defeated || this.State == VerdantGuardianState.Victory) return;
        this.State = VerdantGuardianState.Defeated;
        this.StateStartedAtMs = now;
        this.RemoveAdds();
        this.RemoveTotems();
        Game1.playSound("thudStep");
    }

    private void CompleteVictory(long now)
    {
        if (this.VictoryHandled) return;
        this.VictoryHandled = true;
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
        this.Monitor.Log($"Verdant Guardian defeat sequence complete. firstClear={firstClear}, bossCard={BossCardId}, regionUnlock={this.Save.Data.AirshipHighestRegionUnlocked}.", LogLevel.Info);
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
        this.PendingSummonTiles = Array.Empty<Point>();
        this.PendingSummonKinds = Array.Empty<string>();
        this.VineTarget = Point.Zero;
        this.ChargeDirection = Vector2.Zero;
        this.HeavyAnchor = Vector2.Zero;
        this.LastLivingTotemCount = 0;
        this.LastTotemHitAtMs = 0;
        this.LastTotemHitIndex = -1;
        this.CooldownUntil.Clear();
    }

    private void RemoveBossActors(GameLocation? arena)
    {
        if (arena is null) return;
        foreach (NPC actor in arena.characters.Where(n => n.modData.ContainsKey(BossMarkerKey) || n.modData.ContainsKey(BossAddMarkerKey) || n.modData.ContainsKey(TotemMarkerKey)).ToList()) arena.characters.Remove(actor);
    }

    private void RemoveAdds()
    {
        GameLocation? arena = Game1.getLocationFromName(LocationName);
        if (arena is null) return;
        foreach (NPC actor in arena.characters.Where(n => n.modData.ContainsKey(BossAddMarkerKey)).ToList()) arena.characters.Remove(actor);
    }

    private void SpawnTotems(GameLocation arena)
    {
        for (int i = 0; i < TotemTiles.Length; i++)
        {
            Point tile = TotemTiles[i];
            GreenSlime proxy = new(new Vector2(tile.X * 64f, tile.Y * 64f), 0) { MaxHealth = TotemMaxHealth, Health = TotemMaxHealth, Speed = 0 };
            proxy.modData[TotemMarkerKey] = "verdant-seed-totem";
            proxy.modData[TotemIndexKey] = i.ToString();
            proxy.isInvisible.Value = false;
            arena.characters.Add(proxy);
        }
    }

    private void UpdateTotemAnchors()
    {
        GameLocation? arena = Game1.getLocationFromName(LocationName); if (arena is null) return;
        foreach (Monster totem in arena.characters.OfType<Monster>().Where(m => m.Health > 0 && m.modData.ContainsKey(TotemMarkerKey)))
        {
            if (!totem.modData.TryGetValue(TotemIndexKey, out string? raw) || !int.TryParse(raw, out int index)) index = 0;
            index = Math.Clamp(index, 0, TotemTiles.Length - 1); Point tile = TotemTiles[index];
            totem.Position = new Vector2(tile.X * 64f, tile.Y * 64f); totem.Speed = 0; totem.Halt();
        }
    }

    private void ObserveTotemBreaks(long now)
    {
        if (this.State is VerdantGuardianState.Dormant or VerdantGuardianState.Defeated or VerdantGuardianState.Victory) return;
        int living = this.GetLivingTotemCount();
        if (living < this.LastLivingTotemCount)
        {
            int broken = this.LastLivingTotemCount - living; Game1.playSound("woodWhack");
            Game1.showGlobalMessage(ModEntry.T("boss.verdant.totem.broken", new { remaining = living }));
            this.Monitor.Log($"Verdant Seed Totem broken x{broken}; remaining={living}; barrier={this.GetTotemDamageReductionPercent()}%.", LogLevel.Trace);
            if (living == 0)
            {
                this.State = VerdantGuardianState.TotemStagger; this.StateStartedAtMs = now; this.AttackApplied = false;
                this.RootTargets = Array.Empty<Point>(); this.PendingSummonTiles = Array.Empty<Point>(); this.PendingSummonKinds = Array.Empty<string>();
                Game1.playSound("explosion"); Game1.showGlobalMessage(ModEntry.T("boss.verdant.totem.all-broken"));
            }
        }
        this.LastLivingTotemCount = living;
    }

    internal int ModifyBossIncomingDamage(int damage)
    {
        if (damage <= 0) return damage; int reduction = this.GetTotemDamageReductionPercent();
        return reduction <= 0 ? damage : Math.Max(1, (int)Math.Round(damage * (1d - reduction / 100d), MidpointRounding.AwayFromZero));
    }

    internal void NotifyTotemHit(Monster monster, int previousHealth)
    {
        if (!monster.modData.ContainsKey(TotemMarkerKey) || previousHealth <= monster.Health) return;
        this.LastTotemHitAtMs = Environment.TickCount64;
        if (monster.modData.TryGetValue(TotemIndexKey, out string? raw) && int.TryParse(raw, out int index)) this.LastTotemHitIndex = Math.Clamp(index, 0, TotemTiles.Length - 1);
    }

    internal int GetLivingTotemCount() => Game1.getLocationFromName(LocationName)?.characters.OfType<Monster>().Count(m => m.Health > 0 && m.modData.ContainsKey(TotemMarkerKey)) ?? 0;
    internal int GetTotemDamageReductionPercent() => this.GetLivingTotemCount() switch { >= 4 => 15, 3 => 10, 2 => 6, 1 => 3, _ => 0 };

    private int GetAttackCooldownMs(VerdantGuardianAttack attack, int phase)
    {
        int ms = CooldownMs(attack, phase);
        if (this.GetLivingTotemCount() >= 2 && attack is VerdantGuardianAttack.RootSpikes or VerdantGuardianAttack.VineTrap) ms = (int)Math.Round(ms * 0.92d);
        return ms;
    }

    private void RemoveTotems()
    {
        GameLocation? arena = Game1.getLocationFromName(LocationName); if (arena is null) return;
        foreach (NPC actor in arena.characters.Where(n => n.modData.ContainsKey(TotemMarkerKey)).ToList()) arena.characters.Remove(actor);
    }

    private static int CooldownMs(VerdantGuardianAttack attack, int phase) => attack switch
    {
        // Slightly more breathing room than the raw prototype. Pressure still rises each phase,
        // but the player should read the animation rather than get chain-locked by attack roulette.
        VerdantGuardianAttack.Swipe => phase switch { 1 => 2400, 2 => 2000, _ => 1700 },
        VerdantGuardianAttack.RootSpikes => phase switch { 1 => 5600, 2 => 4800, _ => 4000 },
        VerdantGuardianAttack.SummonAdds => phase switch { 1 => 17000, 2 => 14500, _ => 13000 },
        VerdantGuardianAttack.Charge => phase == 2 ? 7200 : 6000,
        VerdantGuardianAttack.VineTrap => phase == 2 ? 8800 : 7000,
        VerdantGuardianAttack.AreaSlam => 7600,
        _ => 2600
    };

    private static int DecisionGapMs(int phase) => phase switch { 1 => 750, 2 => 600, _ => 450 };

    private void ApplyHeavyRecoil(Monster boss)
    {
        Vector2 displacement = boss.Position - this.HeavyAnchor;
        float length = displacement.Length();
        if (length <= 0.05f)
        {
            boss.Position = this.HeavyAnchor;
            return;
        }

        if (length > HeavyRecoilCapPixels)
            displacement = displacement / length * HeavyRecoilCapPixels;

        Vector2 clamped = this.HeavyAnchor + displacement;
        boss.Position = Vector2.Lerp(clamped, this.HeavyAnchor, HeavyRecenterFactor);
    }

    private static int PhaseDamage(int p1, int p2, int p3, int phase)
        => phase <= 1 ? p1 : phase == 2 ? p2 : p3;

    public string DescribeBalance()
        => $"0665 Region I Balance | HP={BossMaxHealth} | Damage P1/P2/P3: Swipe={SwipeDamageP1}/{SwipeDamageP2}/{SwipeDamageP3}, " +
           $"Root={RootDamageP1}/{RootDamageP2}/{RootDamageP3}, Charge={ChargeDamageP1}/{ChargeDamageP2}/{ChargeDamageP3}, " +
           $"Vine={VineDamageP1}/{VineDamageP2}/{VineDamageP3}, Slam={SlamDamageP1}/{SlamDamageP2}/{SlamDamageP3} | " +
           $"HeavyRecoilCap={HeavyRecoilCapPixels:0}px Recenter={HeavyRecenterFactor:0.00} | AddsMax={MaxActiveAdds} | Totems={this.GetLivingTotemCount()}/4 Barrier={this.GetTotemDamageReductionPercent()}% TotemHP={TotemMaxHealth}";

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
