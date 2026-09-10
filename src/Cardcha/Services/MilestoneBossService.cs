using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Monsters;

namespace Cardcha.Services;

internal enum MilestoneBossKind
{
    HollowCurator = 2,
    TricolorResonance = 3,
    Mimi = 4,
}

internal enum MilestoneBossState
{
    Dormant,
    Intro,
    Decision,
    Telegraph,
    PhaseTransition,
    Defeated,
    Victory,
}

/// <summary>
/// 0678 visual-completion pass for the 40/60/80-card milestone bosses.
/// Boss II, III and IV deliberately share one small state-machine owner so milestone rules,
/// reward persistence and regression guards stay consistent while authored art/arenas can evolve later.
/// </summary>
internal sealed class MilestoneBossService
{
    public const string BossMarkerKey = "Ronvotri.Cardcha/MilestoneBoss";
    public const string BossRoleKey = "Ronvotri.Cardcha/MilestoneBossRole";

    public const string HollowCuratorLocationName = "Cardcha_HollowCuratorArena";
    public const string HollowCuratorMapAssetName = "Maps/Cardcha_HollowCuratorArena";
    public const string TricolorLocationName = "Cardcha_TricolorResonanceArena";
    public const string TricolorMapAssetName = "Maps/Cardcha_TricolorResonanceArena";
    public const string MimiLocationName = "Cardcha_MimiResonanceArena";
    public const string MimiMapAssetName = "Maps/Cardcha_MimiResonanceArena";

    public const string MirrorArchiveBossCardId = "mirror_archive";
    public const string TricolorBossCardId = "tricolor_resonance";
    public const string MimiBossCardId = "mimis_resonance";

    private const string HollowCuratorMapPath = "assets/boss2_hollow_curator_arena.tmx";
    private const string TricolorMapPath = "assets/boss3_tricolor_resonance_arena.tmx";
    private const string MimiMapPath = "assets/boss4_mimi_resonance_arena.tmx";
    private const string HollowCuratorIdleTexturePath = "assets/bosses/milestone/hollow_curator/idle.png";
    private const string HollowCuratorDriftTexturePath = "assets/bosses/milestone/hollow_curator/drift.png";
    private const string HollowCuratorObserveTexturePath = "assets/bosses/milestone/hollow_curator/observe.png";
    private const string HollowCuratorCastTexturePath = "assets/bosses/milestone/hollow_curator/cast.png";
    private const string HollowCuratorPageVolleyTexturePath = "assets/bosses/milestone/hollow_curator/page_volley.png";
    private const string HollowCuratorMirrorTexturePath = "assets/bosses/milestone/hollow_curator/mirror.png";
    private const string HollowCuratorAdaptTexturePath = "assets/bosses/milestone/hollow_curator/adapt.png";
    private const string HollowCuratorHurtTexturePath = "assets/bosses/milestone/hollow_curator/hurt.png";
    private const string HollowCuratorTransitionTexturePath = "assets/bosses/milestone/hollow_curator/transition.png";
    private const string HollowCuratorDefeatTexturePath = "assets/bosses/milestone/hollow_curator/defeat.png";
    private const string HollowArenaTexturePath = "assets/bosses/milestone/hollow_curator_arena_tiles.png";
    private const string TricolorGuardiansTexturePath = "assets/bosses/milestone/tricolor_guardians.png";
    private const string TricolorUnifiedTexturePath = "assets/bosses/milestone/tricolor_unified.png";
    private const string TricolorArenaTexturePath = "assets/bosses/milestone/tricolor_arena_tiles.png";
    private const string MimiTexturePath = "assets/bosses/milestone/mimi_resonance_master.png";
    private const string MimiArenaTexturePath = "assets/bosses/milestone/mimi_arena_tiles.png";
    private const int HollowCuratorMaxHealth = 2200;
    private const int TricolorGuardianMaxHealth = 780;
    private const int TricolorUnifiedMaxHealth = 1650;
    private const int MimiMaxHealth = 3600;
    private const int IntroDurationMs = 1300;
    private const int PhaseTransitionMs = 1050;
    private const int DefeatDurationMs = 1800;
    private const int VictoryReturnMs = 3200;

    private static readonly Point ArrivalTile = new(14, 17);
    private static readonly Point RetreatTile = new(14, 18);
    private static readonly Point PrimaryTile = new(14, 7);
    private static readonly (string Role, Point Tile)[] TricolorGuardianTiles =
    {
        ("ignis", new Point(8, 8)),
        ("vita", new Point(14, 6)),
        ("aether", new Point(20, 8)),
    };

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;
    private readonly Random Rng = new(0x670B055);
    private Func<int, int, string, string>? ExpeditionRouteAction;

    private MilestoneBossKind? CurrentKind;
    private MilestoneBossState State = MilestoneBossState.Dormant;
    private int Phase = 1;
    private int PendingPhase;
    private int CurrentAttack = -1;
    private long StateStartedAtMs;
    private long NextDecisionAtMs;
    private long VictoryReturnAtMs;
    private Point AttackTargetTile;
    private Point AttackTargetTile2;
    private bool AttackApplied;
    private bool VictoryHandled;
    private int CuratorAdaptationStacks;
    private CuratorRunRecord PendingCuratorRecord = CuratorRunRecord.Neutral;
    private CuratorRunRecord ActiveCuratorRecord = CuratorRunRecord.Neutral;
    private bool HasPendingCuratorRecord;
    private bool CuratorRecordRevealed;
    private string PendingCuratorArchiveRule = "none";
    private string ActiveCuratorArchiveRule = "none";
    private bool HasPendingCuratorArchiveRule;
    private int DecisionSerial;
    private long RouteConfirmUntilMs;
    private MilestoneBossKind? RouteConfirmKind;
    private const long RouteConfirmWindowMs = 5000L;
    private Point EchoTargetTile;
    private Point EchoTargetTile2;
    private int MimiCadenceIndex;
    private int TricolorMotionSerial;
    private int LastCuratorVisualHealth = -1;
    private long CuratorHurtUntilMs;

    public MilestoneBossService(IModHelper helper, IMonitor monitor, SaveService save)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
    }

    public void BindExpeditionRouteHandler(Func<int, int, string, string> handler)
        => this.ExpeditionRouteAction = handler;

    public void SetNextHollowCuratorRecord(CuratorRunRecord record)
    {
        this.PendingCuratorRecord = record ?? CuratorRunRecord.Neutral;
        this.HasPendingCuratorRecord = true;
        this.Monitor.Log($"0681 Hollow Curator pending run record: {this.PendingCuratorRecord.Describe()}.", LogLevel.Trace);
    }

    public void SetNextHollowCuratorArchiveRule(string? archiveRule)
    {
        this.PendingCuratorArchiveRule = NormalizeCuratorArchiveRule(archiveRule);
        this.HasPendingCuratorArchiveRule = this.PendingCuratorArchiveRule != "none";
        this.Monitor.Log($"0686 Hollow Curator pending Archive Rule: {this.PendingCuratorArchiveRule}.", LogLevel.Trace);
    }

    public string DebugEnterBoss2WithRecord(string? tag)
    {
        CuratorRunRecord record = CuratorRunRecord.Debug(tag);
        this.SetNextHollowCuratorArchiveRule("none");
        this.SetNextHollowCuratorRecord(record);
        return this.DebugEnterBoss(2) + $" Curator record={record.Tag}; ArchiveRule=none.";
    }

    public bool IsInArena => this.ResolveCurrentKind(Game1.currentLocation) is not null;
    internal MilestoneBossKind? VisualKind => this.CurrentKind;
    internal MilestoneBossState VisualState => this.State;
    internal int VisualPhase => this.Phase;

    public void OnAssetRequested(object? sender, AssetRequestedEventArgs e)
    {
        if (e.NameWithoutLocale.IsEquivalentTo(HollowCuratorMapAssetName))
        {
            e.LoadFromModFile<xTile.Map>(HollowCuratorMapPath, AssetLoadPriority.Exclusive);
            return;
        }
        if (e.NameWithoutLocale.IsEquivalentTo(TricolorMapAssetName))
        {
            e.LoadFromModFile<xTile.Map>(TricolorMapPath, AssetLoadPriority.Exclusive);
            return;
        }
        if (e.NameWithoutLocale.IsEquivalentTo(MimiMapAssetName))
            e.LoadFromModFile<xTile.Map>(MimiMapPath, AssetLoadPriority.Exclusive);
    }

    public void OnSaveLoaded(object? sender, SaveLoadedEventArgs e)
    {
        this.ResetRuntime(removeActors: true);
        this.EnsureAllLocations();
    }

    public void OnDayStarted(object? sender, DayStartedEventArgs e)
    {
        this.ResetRuntime(removeActors: true);
        this.EnsureAllLocations();
    }

    public void OnReturnedToTitle(object? sender, ReturnedToTitleEventArgs e)
        => this.ResetRuntime(removeActors: true);

    public void OnWarped(object? sender, WarpedEventArgs e)
    {
        MilestoneBossKind? incoming = this.ResolveCurrentKind(e.NewLocation);
        if (incoming is not null)
        {
            this.StartEncounter(e.NewLocation, incoming.Value);
            return;
        }

        if (this.ResolveCurrentKind(e.OldLocation) is not null)
            this.ResetRuntime(removeActors: true);
    }

    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!this.IsInArena || !e.Button.IsActionButton() || Game1.activeClickableMenu is not null || Game1.dialogueUp || Game1.eventUp)
            return;
        Point p = PlayerTile();
        if (Math.Abs(p.X - RetreatTile.X) > 1 || Math.Abs(p.Y - RetreatTile.Y) > 1)
            return;

        this.Helper.Input.Suppress(e.Button);
        this.ReturnToDeck();
    }

    public void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)
    {
        MilestoneBossKind? locationKind = this.ResolveCurrentKind(Game1.currentLocation);
        if (locationKind is null)
            return;
        if (this.CurrentKind != locationKind)
            this.StartEncounter(Game1.currentLocation!, locationKind.Value);

        long now = Environment.TickCount64;
        if (this.RouteConfirmUntilMs > 0 && now > this.RouteConfirmUntilMs)
        {
            this.RouteConfirmUntilMs = 0;
            this.RouteConfirmKind = null;
        }
        this.AnchorBossActors();
        this.UpdateCuratorVisualDamageState(now);

        if (this.State == MilestoneBossState.Victory)
        {
            if (this.VictoryReturnAtMs > 0 && now >= this.VictoryReturnAtMs)
                this.ReturnToDeck();
            return;
        }

        if (this.State == MilestoneBossState.Defeated)
        {
            if (now - this.StateStartedAtMs >= DefeatDurationMs)
                this.CompleteVictory(now);
            return;
        }

        if (this.CheckDefeatAndTransitions(now))
            return;

        switch (this.State)
        {
            case MilestoneBossState.Intro:
                if (now - this.StateStartedAtMs >= IntroDurationMs)
                    this.EnterDecision(now, 500);
                break;

            case MilestoneBossState.Decision:
                if (now >= this.NextDecisionAtMs)
                    this.SelectAttack(now);
                break;

            case MilestoneBossState.Telegraph:
                if (now - this.StateStartedAtMs >= this.CurrentAttackTelegraphMs())
                {
                    if (!this.AttackApplied)
                    {
                        this.AttackApplied = true;
                        this.ApplyCurrentAttack();
                    }
                    this.EnterDecision(now, this.CurrentDecisionGapMs());
                }
                break;

            case MilestoneBossState.PhaseTransition:
                if (now - this.StateStartedAtMs >= PhaseTransitionMs)
                {
                    this.Phase = Math.Max(1, this.PendingPhase);
                    this.PendingPhase = 0;
                    if (this.CurrentKind == MilestoneBossKind.TricolorResonance && this.Phase == 4)
                        this.SpawnTricolorUnified();
                    Game1.playSound("discoverMineral");
                    this.EnterDecision(now, 600);
                }
                break;
        }
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        MilestoneBossKind? kind = this.ResolveCurrentKind(Game1.currentLocation);
        if (kind is null)
            return;

        // 0678 depth contract: physical boss bodies and arena props are NOT drawn here.
        // Boss bodies are injected at Monster.draw; arena identity lives in TMX ground layers.
        this.DrawBossAuraVfx(e.SpriteBatch, kind.Value);
        this.DrawAttackTelegraph(e.SpriteBatch);
        this.DrawRetreatGlyph(e.SpriteBatch);
    }

    public void OnRenderedHud(object? sender, RenderedHudEventArgs e)
    {
        if (!this.IsInArena || this.CurrentKind is null)
            return;

        string title = this.CurrentKind switch
        {
            MilestoneBossKind.HollowCurator => "THE HOLLOW CURATOR",
            MilestoneBossKind.TricolorResonance => "THE TRICOLOR RESONANCE",
            MilestoneBossKind.Mimi => "MIMI • THE RESONANCE MASTER",
            _ => "CARDCHA BOSS",
        };
        string phase = this.DescribePhaseShort();
        (int hp, int max) = this.GetCombinedHealth();
        float ratio = max <= 0 ? 0f : Math.Clamp(hp / (float)max, 0f, 1f);

        int width = Math.Min(620, Game1.uiViewport.Width - 80);
        int x = (Game1.uiViewport.Width - width) / 2;
        int y = 26;
        e.SpriteBatch.Draw(Game1.staminaRect, new Rectangle(x, y, width, 50), Color.Black * 0.72f);
        e.SpriteBatch.Draw(Game1.staminaRect, new Rectangle(x + 8, y + 30, width - 16, 10), new Color(50, 43, 61) * 0.95f);
        e.SpriteBatch.Draw(Game1.staminaRect, new Rectangle(x + 8, y + 30, (int)((width - 16) * ratio), 10), this.KindColor(this.CurrentKind.Value) * 0.92f);
        Vector2 titleSize = Game1.smallFont.MeasureString(title);
        e.SpriteBatch.DrawString(Game1.smallFont, title, new Vector2(Game1.uiViewport.Width / 2f - titleSize.X / 2f, y + 4), Color.White);
        Vector2 phaseSize = Game1.smallFont.MeasureString(phase);
        e.SpriteBatch.DrawString(Game1.smallFont, phase, new Vector2(Game1.uiViewport.Width / 2f - phaseSize.X / 2f, y + 41), new Color(224, 219, 238));
    }

    public string DebugEnterBoss(int milestone)
    {
        if (!Context.IsWorldReady)
            return "Load a save first.";
        MilestoneBossKind? kind = milestone switch
        {
            2 => MilestoneBossKind.HollowCurator,
            3 => MilestoneBossKind.TricolorResonance,
            4 => MilestoneBossKind.Mimi,
            _ => null,
        };
        if (kind is null)
            return "Unknown milestone boss. Use 2, 3 or 4.";

        GameLocation? arena = this.EnsureLocation(kind.Value);
        if (arena is null)
            return $"Couldn't create Boss {milestone} arena.";
        Game1.warpFarmer(arena.NameOrUniqueName, ArrivalTile.X, ArrivalTile.Y, 0);
        return $"TEST: entered Boss {milestone} arena. Milestone gate bypassed; save progression unchanged until a real victory.";
    }

    public string EnterBoss2FromRegion2()
    {
        if (!Context.IsWorldReady)
            return ModEntry.T("airship.milestone.unavailable");
        if (!Region2RoguelikeRunService.IsRegion2(Game1.currentLocation))
            return ModEntry.T("airship.region2.boss_gate.location");
        if (!this.Save.Data.Region1BossDefeated)
            return ModEntry.T("airship.milestone.boss1_required");
        int owned = this.Save.Data.OwnedCards?.Count ?? 0;
        if (owned < 40)
            return ModEntry.T("airship.region2.boss_gate.cards", new { cards = owned });
        if (this.Save.Data.BossCardsUnlocked?.Contains(MirrorArchiveBossCardId) == true)
            return ModEntry.T("airship.region2.boss_gate.cleared");

        GameLocation? arena = this.EnsureLocation(MilestoneBossKind.HollowCurator);
        if (arena is null)
            return ModEntry.T("airship.milestone.unavailable");
        Game1.playSound("wand");
        Game1.warpFarmer(arena.NameOrUniqueName, ArrivalTile.X, ArrivalTile.Y, 0);
        return string.Empty;
    }

    public string UseAirshipMilestoneRoute()
    {
        if (!Context.IsWorldReady)
            return ModEntry.T("airship.milestone.unavailable");

        int owned = this.Save.Data.OwnedCards?.Count ?? 0;
        (MilestoneBossKind? kind, int required, string name) = this.ResolveNextMilestoneRoute();
        if (kind is null)
        {
            this.RouteConfirmUntilMs = 0;
            this.RouteConfirmKind = null;
            if (this.ExpeditionRouteAction is not null && this.Save.Data.AirshipHighestRegionUnlocked >= 3)
                return this.ExpeditionRouteAction(owned, 0, string.Empty);
            return ModEntry.T("airship.milestone.all_clear");
        }

        if (kind == MilestoneBossKind.HollowCurator && !this.Save.Data.Region1BossDefeated)
            return ModEntry.T("airship.milestone.boss1_required");

        int regionRequired = kind switch
        {
            MilestoneBossKind.TricolorResonance => 3,
            MilestoneBossKind.Mimi => 4,
            _ => 2,
        };
        if (this.Save.Data.AirshipHighestRegionUnlocked < regionRequired)
            return ModEntry.T("airship.milestone.route_sealed", new { region = regionRequired });

        if (owned < required)
        {
            this.RouteConfirmUntilMs = 0;
            this.RouteConfirmKind = null;
            if (this.ExpeditionRouteAction is not null)
                return this.ExpeditionRouteAction(owned, required, name);
            return ModEntry.T("airship.milestone.progress", new { name, cards = owned, required });
        }

        // 0679: the 40-card milestone no longer teleports straight into Boss II.
        // Hollow Curator belongs to Region II, so the Airship lands in the Forgotten Archive;
        // the physical north Archive Seal is the boss entrance.
        if (kind == MilestoneBossKind.HollowCurator && this.ExpeditionRouteAction is not null)
        {
            this.RouteConfirmUntilMs = 0;
            this.RouteConfirmKind = null;
            return this.ExpeditionRouteAction(owned, required, name);
        }

        long now = Environment.TickCount64;
        if (this.RouteConfirmKind != kind || this.RouteConfirmUntilMs <= now)
        {
            this.RouteConfirmKind = kind;
            this.RouteConfirmUntilMs = now + RouteConfirmWindowMs;
            Game1.playSound("smallSelect");
            return ModEntry.T("airship.milestone.confirm", new { name, required });
        }

        GameLocation? arena = this.EnsureLocation(kind.Value);
        if (arena is null)
        {
            this.RouteConfirmUntilMs = 0;
            this.RouteConfirmKind = null;
            return ModEntry.T("airship.milestone.unavailable");
        }

        this.RouteConfirmUntilMs = 0;
        this.RouteConfirmKind = null;
        Game1.playSound("wand");
        Game1.warpFarmer(arena.NameOrUniqueName, ArrivalTile.X, ArrivalTile.Y, 0);
        return string.Empty;
    }

    public string DescribeMilestoneRoute()
    {
        int owned = this.Save.Data.OwnedCards?.Count ?? 0;
        (MilestoneBossKind? kind, int required, string name) = this.ResolveNextMilestoneRoute();
        string next = kind is null ? "all-clear" : $"{kind}:{name}:{owned}/{required}";
        double confirm = this.RouteConfirmUntilMs > Environment.TickCount64
            ? (this.RouteConfirmUntilMs - Environment.TickCount64) / 1000d
            : 0d;
        return $"0679 MilestoneRoute | Next={next} | BossI={this.Save.Data.Region1BossDefeated} | HighestRegion={this.Save.Data.AirshipHighestRegionUnlocked} | Confirm={this.RouteConfirmKind?.ToString() ?? "none"}:{confirm:0.0}s";
    }

    private (MilestoneBossKind? Kind, int Required, string Name) ResolveNextMilestoneRoute()
    {
        HashSet<string>? unlocked = this.Save.Data.BossCardsUnlocked;
        if (unlocked?.Contains(MirrorArchiveBossCardId) != true)
            return (MilestoneBossKind.HollowCurator, 40, "The Hollow Curator");
        if (unlocked?.Contains(TricolorBossCardId) != true)
            return (MilestoneBossKind.TricolorResonance, 60, "The Tricolor Resonance");
        if (unlocked?.Contains(MimiBossCardId) != true)
            return (MilestoneBossKind.Mimi, 80, "MiMi • The Resonance Master");
        return (null, 0, string.Empty);
    }

    public string Describe()
    {
        string current = this.CurrentKind?.ToString() ?? "none";
        (int hp, int max) = this.GetCombinedHealth();
        return $"0681 MilestoneBoss | Current={current} | State={this.State} | Phase={this.Phase} | HP={hp}/{max} | " +
               $"CuratorAdapt={this.CuratorAdaptationStacks}/3 | CuratorRecord={this.ActiveCuratorRecord.Describe()} | ArchiveRule={this.ActiveCuratorArchiveRule} | CuratorVisual={this.CuratorAnimationClip(Environment.TickCount64).Name} | BossCards=[{string.Join(',', this.Save.Data.BossCardsUnlocked ?? new HashSet<string>())}] | " +
               $"HighestRegion={this.Save.Data.AirshipHighestRegionUnlocked}";
    }

    private void StartEncounter(GameLocation arena, MilestoneBossKind kind)
    {
        this.RemoveMarkedActors(arena);
        this.CurrentKind = kind;
        this.State = MilestoneBossState.Intro;
        this.Phase = 1;
        this.PendingPhase = 0;
        this.CurrentAttack = -1;
        this.StateStartedAtMs = Environment.TickCount64;
        this.NextDecisionAtMs = 0;
        this.VictoryReturnAtMs = 0;
        this.AttackApplied = false;
        this.VictoryHandled = false;
        this.CuratorAdaptationStacks = 0;
        if (kind == MilestoneBossKind.HollowCurator)
        {
            this.ActiveCuratorRecord = this.HasPendingCuratorRecord ? this.PendingCuratorRecord : CuratorRunRecord.Neutral;
            this.ActiveCuratorArchiveRule = this.HasPendingCuratorArchiveRule ? this.PendingCuratorArchiveRule : "none";
            this.PendingCuratorRecord = CuratorRunRecord.Neutral;
            this.HasPendingCuratorRecord = false;
            this.PendingCuratorArchiveRule = "none";
            this.HasPendingCuratorArchiveRule = false;
        }
        else
        {
            this.ActiveCuratorRecord = CuratorRunRecord.Neutral;
            this.ActiveCuratorArchiveRule = "none";
        }
        this.CuratorRecordRevealed = false;
        this.DecisionSerial = 0;
        this.RouteConfirmUntilMs = 0;
        this.RouteConfirmKind = null;
        this.AttackTargetTile = PlayerTile();
        this.AttackTargetTile2 = this.AttackTargetTile;
        this.EchoTargetTile = this.AttackTargetTile;
        this.EchoTargetTile2 = this.AttackTargetTile2;
        this.MimiCadenceIndex = 0;
        this.TricolorMotionSerial = 0;
        this.LastCuratorVisualHealth = kind == MilestoneBossKind.HollowCurator ? HollowCuratorMaxHealth : -1;
        this.CuratorHurtUntilMs = 0;

        switch (kind)
        {
            case MilestoneBossKind.HollowCurator:
                this.SpawnProxy(arena, "curator", PrimaryTile, HollowCuratorMaxHealth);
                break;
            case MilestoneBossKind.TricolorResonance:
                foreach ((string role, Point tile) in TricolorGuardianTiles)
                    this.SpawnProxy(arena, role, tile, TricolorGuardianMaxHealth);
                break;
            case MilestoneBossKind.Mimi:
                this.SpawnProxy(arena, "mimi", PrimaryTile, MimiMaxHealth);
                break;
        }

        Game1.playSound("wand");
        this.Monitor.Log($"0672 Boss encounter started: {kind}.", LogLevel.Info);
    }

    private bool CheckDefeatAndTransitions(long now)
    {
        if (this.CurrentKind is null)
            return false;

        if (this.CurrentKind == MilestoneBossKind.TricolorResonance)
        {
            if (this.Phase < 4)
            {
                if (!this.GetBossActors(includeDead: false).Any(a => this.Role(a) is "ignis" or "vita" or "aether"))
                {
                    this.BeginPhaseTransition(4, now);
                    return true;
                }
                return false;
            }

            Monster? unified = this.FindRole("unified", includeDead: true);
            if (unified is null || unified.Health <= 0)
            {
                this.BeginDefeat(now);
                return true;
            }
            return false;
        }

        Monster? primary = this.CurrentKind == MilestoneBossKind.HollowCurator
            ? this.FindRole("curator", includeDead: true)
            : this.FindRole("mimi", includeDead: true);
        if (primary is null || primary.Health <= 0)
        {
            this.BeginDefeat(now);
            return true;
        }

        float ratio = primary.MaxHealth <= 0 ? 0f : primary.Health / (float)primary.MaxHealth;
        if (this.CurrentKind == MilestoneBossKind.HollowCurator)
        {
            if (this.Phase == 1 && ratio <= 0.70f) { this.BeginPhaseTransition(2, now); return true; }
            if (this.Phase == 2 && ratio <= 0.35f) { this.BeginPhaseTransition(3, now); return true; }
        }
        else
        {
            if (this.Phase == 1 && ratio <= 0.75f) { this.BeginPhaseTransition(2, now); return true; }
            if (this.Phase == 2 && ratio <= 0.50f) { this.BeginPhaseTransition(3, now); return true; }
            if (this.Phase == 3 && ratio <= 0.25f) { this.BeginPhaseTransition(4, now); return true; }
        }
        return false;
    }

    private void SelectAttack(long now)
    {
        if (this.CurrentKind is null)
            return;

        this.DecisionSerial++;
        this.EchoTargetTile = this.AttackTargetTile;
        this.EchoTargetTile2 = this.AttackTargetTile2;
        this.AttackTargetTile = PlayerTile();
        this.AttackTargetTile2 = ClampArenaTile(new Point(
            this.AttackTargetTile.X + (this.DecisionSerial % 2 == 0 ? 2 : -2),
            this.AttackTargetTile.Y + (this.DecisionSerial % 3 == 0 ? 1 : 0)
        ));

        switch (this.CurrentKind.Value)
        {
            case MilestoneBossKind.HollowCurator:
            {
                int recordAttack = this.CuratorRecordAttackId();
                int[] pool = this.Phase switch
                {
                    1 => new[] { 0, 0, 1 },
                    2 => this.ApplyCuratorArchiveRuleAttackBias(new[] { 0, 1, 2, 4, recordAttack, recordAttack }),
                    _ => this.ApplyCuratorArchiveRuleAttackBias(new[] { 0, 2, 3, 4, recordAttack, recordAttack, recordAttack }),
                };
                this.CurrentAttack = pool[this.Rng.Next(pool.Length)];
                if (this.CurrentAttack == 5)
                {
                    this.AttackTargetTile2 = ClampArenaTile(new Point(
                        this.AttackTargetTile.X + (this.DecisionSerial % 2 == 0 ? 3 : -3),
                        this.AttackTargetTile.Y
                    ));
                }
                else if (this.CurrentAttack == 9)
                {
                    this.AttackTargetTile2 = ClampArenaTile(new Point(
                        this.AttackTargetTile.X + (this.DecisionSerial % 2 == 0 ? 2 : -2),
                        this.AttackTargetTile.Y + (this.DecisionSerial % 3 == 0 ? 2 : -1)
                    ));
                }
                if (this.Phase >= 2 && this.ActiveCuratorArchiveRule == "mirror_draft"
                    && this.DecisionSerial % 2 == 0 && this.CurrentAttack is 2 or 5 or 9)
                {
                    this.AttackTargetTile2 = MirrorCuratorTile(this.AttackTargetTile);
                }
                this.MaybeTeleportPrimary("curator");
                break;
            }

            case MilestoneBossKind.TricolorResonance:
            {
                if (this.Phase >= 4)
                {
                    this.CurrentAttack = this.DecisionSerial % 3 switch
                    {
                        0 => 13,
                        1 => 14,
                        _ => 15,
                    };
                }
                else
                {
                    string[] roles = this.GetBossActors(false)
                        .Select(this.Role)
                        .Where(r => r is "ignis" or "vita" or "aether")
                        .Distinct(StringComparer.OrdinalIgnoreCase)
                        .ToArray();
                    if (roles.Length == 0)
                    {
                        this.BeginPhaseTransition(4, now);
                        return;
                    }

                    string role = roles[this.Rng.Next(roles.Length)];
                    this.RepositionTricolorGuardian(role);
                    this.CurrentAttack = role == "ignis" ? 10 : role == "vita" ? 11 : 12;
                    if (role == "aether")
                    {
                        this.AttackTargetTile2 = ClampArenaTile(new Point(
                            this.AttackTargetTile.X,
                            this.AttackTargetTile.Y + (this.DecisionSerial % 2 == 0 ? 2 : -2)
                        ));
                    }
                }
                break;
            }

            case MilestoneBossKind.Mimi:
            {
                int[] pool = this.Phase switch
                {
                    1 => new[] { 20, 20, 21 },
                    2 => new[] { 20, 22, 26, 26 },
                    3 => new[] { 22, 23, 27, 27 },
                    _ => new[] { 24, 25, 26, 27, 28, 28 },
                };
                this.CurrentAttack = pool[this.Rng.Next(pool.Length)];
                if (this.CurrentAttack == 27)
                    this.MimiCadenceIndex = (this.MimiCadenceIndex + 1) % 3;
                this.MaybeTeleportPrimary("mimi");
                break;
            }
        }

        this.State = MilestoneBossState.Telegraph;
        this.StateStartedAtMs = now;
        this.AttackApplied = false;
        Game1.playSound(this.CurrentAttack is 10 or 24 or 25 or 28 ? "thudStep" : "Cowboy_gunload");
    }

    private void ApplyCurrentAttack()
    {
        int extra = this.CuratorAdaptationStacks * 2;
        switch (this.CurrentAttack)
        {
            case 0:
                if (PlayerWithin(this.AttackTargetTile, 1.4f))
                    DamagePlayer(12 + this.Phase * 2 + extra);
                break;
            case 1:
                this.CuratorAdaptationStacks = Math.Min(3, this.CuratorAdaptationStacks + 1);
                Game1.showGlobalMessage($"Hollow Curator adapts • {this.CuratorAdaptationStacks}/3");
                break;
            case 2:
                if (PlayerWithin(this.AttackTargetTile, 2.0f) || PlayerWithin(this.AttackTargetTile2, 1.35f))
                    DamagePlayer(15 + this.Phase * 2 + extra);
                break;
            case 3:
                if (PlayerWithin(this.AttackTargetTile, 2.55f))
                    DamagePlayer(23 + extra);
                break;
            case 4:
                if (PlayerWithin(this.EchoTargetTile, 1.8f) || PlayerWithin(this.EchoTargetTile2, 1.25f))
                    DamagePlayer(17 + this.Phase * 2 + extra);
                Game1.playSound("wand");
                break;
            case 5: // RISK: two collapsing archive zones, strong but clearly telegraphed.
                if (PlayerWithin(this.AttackTargetTile, 2.15f) || PlayerWithin(this.AttackTargetTile2, 1.25f))
                    DamagePlayer(20 + this.Phase + extra);
                Game1.playSound("thudStep");
                break;
            case 6: // PRECISION: narrow current + remembered strike.
                if (PlayerWithin(this.AttackTargetTile, 0.95f) || PlayerWithin(this.EchoTargetTile, 0.95f))
                    DamagePlayer(22 + extra);
                Game1.playSound("Cowboy_gunload");
                break;
            case 7: // PRESSURE: wider, lower-damage compression pulse.
                if (PlayerWithin(this.AttackTargetTile, 2.65f))
                    DamagePlayer(18 + this.Phase + extra);
                Game1.playSound("thudStep");
                break;
            case 8: // RECOVERY: Curator reflects restoration without disabling player healing.
            {
                Monster? curator = this.FindRole("curator", false);
                if (curator is not null)
                    curator.Health = Math.Min(curator.MaxHealth, curator.Health + 55 + this.CuratorAdaptationStacks * 10);
                if (PlayerWithin(this.AttackTargetTile, 1.35f))
                    DamagePlayer(10 + extra);
                Game1.playSound("healSound");
                break;
            }
            case 9: // MIRROR: current + secondary + previous position echo.
                if (PlayerWithin(this.AttackTargetTile, 1.55f)
                    || PlayerWithin(this.AttackTargetTile2, 1.25f)
                    || PlayerWithin(this.EchoTargetTile, 1.25f))
                    DamagePlayer(18 + this.Phase + extra);
                Game1.playSound("wand");
                break;

            case 10:
                if (PlayerWithin(this.AttackTargetTile, 2.05f))
                    DamagePlayer(20);
                break;
            case 11:
                foreach (Monster guardian in this.GetBossActors(false).Where(a => this.Role(a) is "ignis" or "vita" or "aether"))
                    guardian.Health = Math.Min(guardian.MaxHealth, guardian.Health + 70);
                if (PlayerWithin(this.AttackTargetTile, 1.5f))
                    DamagePlayer(8);
                Game1.playSound("leafrustle");
                break;
            case 12:
                if (PlayerWithin(this.AttackTargetTile, 1.35f) || PlayerWithin(this.AttackTargetTile2, 1.35f))
                    DamagePlayer(16);
                break;
            case 13:
                if (PlayerWithin(this.AttackTargetTile, 2.35f) || PlayerWithin(this.AttackTargetTile2, 1.6f))
                    DamagePlayer(25);
                break;
            case 14:
                if (PlayerWithin(this.AttackTargetTile, 1.55f) || PlayerWithin(this.EchoTargetTile, 1.55f))
                    DamagePlayer(21);
                break;
            case 15:
                if (PlayerWithin(this.AttackTargetTile, 2.0f)
                    || PlayerWithin(this.AttackTargetTile2, 1.35f)
                    || PlayerWithin(this.EchoTargetTile, 1.35f))
                    DamagePlayer(23);
                break;

            case 20:
                if (PlayerWithin(this.AttackTargetTile, 1.35f))
                    DamagePlayer(15 + this.Phase * 2);
                break;
            case 21:
                if (PlayerWithin(this.AttackTargetTile, 1.8f))
                    DamagePlayer(14);
                break;
            case 22:
                if (PlayerWithin(this.AttackTargetTile, 1.9f) || PlayerWithin(this.AttackTargetTile2, 1.35f))
                    DamagePlayer(17 + this.Phase * 2);
                break;
            case 23:
                if (PlayerWithin(this.AttackTargetTile, 2.3f))
                    DamagePlayer(20 + this.Phase);
                break;
            case 24:
                if (PlayerWithin(this.AttackTargetTile, 2.55f) || PlayerWithin(this.AttackTargetTile2, 1.8f))
                    DamagePlayer(22 + this.Phase * 2);
                break;
            case 25:
                if (PlayerWithin(this.AttackTargetTile, 3.0f))
                    DamagePlayer(30);
                Game1.playSound("explosion");
                break;
            case 26:
                if (PlayerWithin(this.EchoTargetTile, 1.7f) || PlayerWithin(this.EchoTargetTile2, 1.2f))
                    DamagePlayer(18 + this.Phase * 2);
                Game1.playSound("wand");
                break;
            case 27:
            {
                if (this.MimiCadenceIndex == 0)
                {
                    if (PlayerWithin(this.AttackTargetTile, 2.2f))
                        DamagePlayer(24);
                    Game1.playSound("explosion");
                }
                else if (this.MimiCadenceIndex == 1)
                {
                    Monster? mimi = this.FindRole("mimi", false);
                    if (mimi is not null)
                        mimi.Health = Math.Min(mimi.MaxHealth, mimi.Health + 100);
                    if (PlayerWithin(this.AttackTargetTile, 1.4f))
                        DamagePlayer(10);
                    Game1.playSound("leafrustle");
                }
                else
                {
                    if (PlayerWithin(this.AttackTargetTile, 1.45f) || PlayerWithin(this.AttackTargetTile2, 1.45f))
                        DamagePlayer(18);
                    Game1.playSound("wand");
                }
                break;
            }
            case 28:
                if (PlayerWithin(this.AttackTargetTile, 2.75f)
                    || PlayerWithin(this.AttackTargetTile2, 1.75f)
                    || PlayerWithin(this.EchoTargetTile, 1.5f))
                    DamagePlayer(32);
                Game1.playSound("explosion");
                break;
        }
    }

    private void BeginPhaseTransition(int nextPhase, long now)
    {
        if (this.State == MilestoneBossState.PhaseTransition || this.State == MilestoneBossState.Defeated || this.State == MilestoneBossState.Victory)
            return;
        this.PendingPhase = nextPhase;
        if (this.CurrentKind == MilestoneBossKind.HollowCurator && nextPhase == 2 && !this.CuratorRecordRevealed)
        {
            this.CuratorRecordRevealed = true;
            Game1.showGlobalMessage(ModEntry.T("boss.curator.record_rule.reveal", new { record = this.CuratorRecordShort(), rule = this.CuratorArchiveRuleShort() }));
        }
        this.State = MilestoneBossState.PhaseTransition;
        this.StateStartedAtMs = now;
        this.CurrentAttack = -1;
        this.AttackApplied = false;
        Game1.playSound("discoverMineral");
    }

    private void BeginDefeat(long now)
    {
        if (this.State is MilestoneBossState.Defeated or MilestoneBossState.Victory)
            return;
        this.State = MilestoneBossState.Defeated;
        this.StateStartedAtMs = now;
        this.CurrentAttack = -1;
        this.AttackApplied = false;
        Game1.playSound("thudStep");
    }

    private void CompleteVictory(long now)
    {
        if (this.VictoryHandled || this.CurrentKind is null)
            return;
        this.VictoryHandled = true;

        string reward = this.CurrentKind switch
        {
            MilestoneBossKind.HollowCurator => MirrorArchiveBossCardId,
            MilestoneBossKind.TricolorResonance => TricolorBossCardId,
            MilestoneBossKind.Mimi => MimiBossCardId,
            _ => string.Empty,
        };
        int unlockRegion = this.CurrentKind switch
        {
            MilestoneBossKind.HollowCurator => 3,
            MilestoneBossKind.TricolorResonance => 4,
            _ => this.Save.Data.AirshipHighestRegionUnlocked,
        };

        this.Save.Data.BossCardsUnlocked ??= new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        bool firstClear = this.Save.Data.BossCardsUnlocked.Add(reward);
        this.Save.Data.AirshipHighestRegionUnlocked = Math.Max(this.Save.Data.AirshipHighestRegionUnlocked, unlockRegion);
        this.Save.Save();

        Game1.playSound(firstClear ? "yoba" : "questcomplete");
        string name = this.CurrentKind switch
        {
            MilestoneBossKind.HollowCurator => "Mirror Archive",
            MilestoneBossKind.TricolorResonance => "Tricolor Resonance",
            MilestoneBossKind.Mimi => "MiMi's Resonance",
            _ => reward,
        };
        Game1.showGlobalMessage(firstClear ? $"Boss Card unlocked: {name}" : $"Rematch complete: {name}");
        this.State = MilestoneBossState.Victory;
        this.VictoryReturnAtMs = now + VictoryReturnMs;
        this.Monitor.Log($"0672 {this.CurrentKind} victory. firstClear={firstClear}, reward={reward}, highestRegion={this.Save.Data.AirshipHighestRegionUnlocked}.", LogLevel.Info);
    }

    private void SpawnTricolorUnified()
    {
        GameLocation? arena = Game1.currentLocation;
        if (arena is null)
            return;
        foreach (Monster actor in arena.characters.OfType<Monster>().Where(a => a.modData.ContainsKey(BossMarkerKey)).ToList())
            arena.characters.Remove(actor);
        this.SpawnProxy(arena, "unified", PrimaryTile, TricolorUnifiedMaxHealth);
    }

    private void SpawnProxy(GameLocation arena, string role, Point tile, int maxHealth)
    {
        GreenSlime proxy = new(new Vector2(tile.X * 64f, tile.Y * 64f), 0)
        {
            MaxHealth = maxHealth,
            Health = maxHealth,
            Speed = 0,
        };
        proxy.modData[BossMarkerKey] = ((int)(this.CurrentKind ?? MilestoneBossKind.HollowCurator)).ToString();
        proxy.modData[BossRoleKey] = role;
        proxy.isInvisible.Value = false;
        arena.characters.Add(proxy);
    }

    private void AnchorBossActors()
    {
        foreach (Monster actor in this.GetBossActors(false))
        {
            actor.Speed = 0;
            actor.Halt();
        }
    }

    private void RepositionTricolorGuardian(string role)
    {
        Monster? actor = this.FindRole(role, false);
        if (actor is null)
            return;

        this.TricolorMotionSerial++;
        Point target;
        Point player = PlayerTile();
        if (role == "ignis")
        {
            int sx = player.X < 14 ? 1 : -1;
            int sy = this.TricolorMotionSerial % 2 == 0 ? 1 : -1;
            target = ClampArenaTile(new Point(player.X + sx * 2, player.Y + sy));
        }
        else if (role == "vita")
        {
            Point[] pads = { new(11, 5), new(14, 5), new(17, 5), new(14, 8) };
            target = pads[this.TricolorMotionSerial % pads.Length];
        }
        else
        {
            Point[] pads = { new(5, 5), new(22, 5), new(5, 12), new(22, 12), new(14, 4) };
            target = pads[this.TricolorMotionSerial % pads.Length];
        }

        actor.Position = new Vector2(target.X * 64f, target.Y * 64f);
        Game1.playSound(role == "ignis" ? "thudStep" : "wand");
    }

    private void MaybeTeleportPrimary(string role)
    {
        if (this.DecisionSerial % 3 != 0)
            return;
        Monster? actor = this.FindRole(role, false);
        if (actor is null)
            return;
        Point[] pads = { new(9, 7), new(14, 6), new(19, 7), new(11, 10), new(17, 10) };
        Point p = pads[this.Rng.Next(pads.Length)];
        actor.Position = new Vector2(p.X * 64f, p.Y * 64f);
        Game1.playSound("wand");
    }

    private void EnterDecision(long now, int delayMs)
    {
        this.State = MilestoneBossState.Decision;
        this.StateStartedAtMs = now;
        this.NextDecisionAtMs = now + delayMs;
        this.CurrentAttack = -1;
        this.AttackApplied = false;
    }

    private int CurrentAttackTelegraphMs() => this.CurrentAttack switch
    {
        1 => 900,
        3 => 1050,
        4 => 880,
        5 => 980,
        6 => 1150,
        7 => 1050,
        8 => 1050,
        9 => 1000,
        10 => 720,
        11 => 820,
        12 => 760,
        13 => 980,
        14 => 900,
        15 => 960,
        24 => 900,
        25 => 1150,
        26 => 900,
        27 => 900,
        28 => 1180,
        _ => 760,
    };

    private int CurrentDecisionGapMs()
    {
        int gap = this.CurrentKind switch
        {
            MilestoneBossKind.HollowCurator => this.Phase switch { 1 => 780, 2 => 650, _ => 520 },
            MilestoneBossKind.TricolorResonance => this.Phase >= 4 ? 520 : 720,
            MilestoneBossKind.Mimi => this.Phase switch { 1 => 720, 2 => 620, 3 => 520, _ => 430 },
            _ => 650,
        };
        if (this.CurrentKind != MilestoneBossKind.HollowCurator || this.Phase < 2)
            return gap;
        return this.ActiveCuratorArchiveRule switch
        {
            "loose_folios" => Math.Max(360, gap - 100),
            "iron_bindings" => gap + 120,
            _ => gap,
        };
    }

    internal void DrawActorAtMonsterDepth(SpriteBatch batch, Monster actor)
    {
        if (!actor.modData.ContainsKey(BossMarkerKey))
            return;

        MilestoneBossKind kind = this.ResolveCurrentKind(actor.currentLocation ?? Game1.currentLocation)
            ?? this.CurrentKind
            ?? MilestoneBossKind.HollowCurator;
        string role = this.Role(actor);
        Vector2 feet = Game1.GlobalToLocal(Game1.viewport, actor.Position + new Vector2(32f, 58f));
        Texture2D texture;
        Rectangle source;
        float scale;
        Vector2 offset = Vector2.Zero;

        if (role == "curator")
        {
            long now = Environment.TickCount64;
            (string Name, string Path, int Frames, int FrameTicks, bool Loop) clip = this.CuratorAnimationClip(now);
            texture = this.Helper.ModContent.Load<Texture2D>(clip.Path);
            long clock = clip.Loop ? now : Math.Max(0L, now - this.StateStartedAtMs);
            int frame = clip.Loop
                ? (int)((clock / clip.FrameTicks + this.DecisionSerial) % clip.Frames)
                : Math.Min(clip.Frames - 1, (int)(clock / clip.FrameTicks));
            source = new Rectangle(frame * 48, 0, 48, 64);
            scale = 1.95f;
            float hover = this.State is MilestoneBossState.Intro or MilestoneBossState.Decision
                ? (float)Math.Sin(now / 240d) * 2f
                : 0f;
            offset = new Vector2(0f, 6f + hover);
        }
        else if (role is "ignis" or "vita" or "aether")
        {
            texture = this.Helper.ModContent.Load<Texture2D>(TricolorGuardiansTexturePath);
            int roleIndex = role == "ignis" ? 0 : role == "vita" ? 1 : 2;
            int active = (this.State == MilestoneBossState.Telegraph || this.State == MilestoneBossState.PhaseTransition) ? 1 : 0;
            source = new Rectangle((roleIndex * 2 + active) * 48, 0, 48, 48);
            scale = 1.85f;
        }
        else if (role == "unified")
        {
            texture = this.Helper.ModContent.Load<Texture2D>(TricolorUnifiedTexturePath);
            int frame = this.State == MilestoneBossState.PhaseTransition ? 2
                : this.State == MilestoneBossState.Telegraph ? 1 + (this.DecisionSerial & 1)
                : this.Phase >= 4 ? 3
                : 0;
            source = new Rectangle(frame * 64, 0, 64, 64);
            scale = 1.85f;
        }
        else
        {
            texture = this.Helper.ModContent.Load<Texture2D>(MimiTexturePath);
            int frame = this.Phase >= 4 ? 3 : this.Phase >= 3 ? 2 : this.Phase >= 2 ? 1 : 0;
            source = new Rectangle(frame * 64, 0, 64, 64);
            scale = 1.80f;
            offset = new Vector2(0f, 4f);
        }

        float pulse = this.State == MilestoneBossState.PhaseTransition
            ? 0.96f + 0.04f * (float)Math.Abs(Math.Sin(Environment.TickCount64 / 75d))
            : 1f;
        Color tint = this.State == MilestoneBossState.Defeated ? Color.White * 0.58f : Color.White;
        float actorLayer = Math.Clamp((actor.Position.Y + 64f) / 10000f, 0.0002f, 0.995f);
        float shadowLayer = Math.Max(0.0001f, actorLayer - 0.0001f);
        int shadowWidth = (int)(source.Width * scale * 0.58f);
        batch.Draw(Game1.staminaRect,
            new Rectangle((int)feet.X - shadowWidth / 2, (int)feet.Y - 6, shadowWidth, 8),
            null, Color.Black * 0.24f, 0f, Vector2.Zero, SpriteEffects.None, shadowLayer);
        batch.Draw(texture, feet + offset, source, tint, 0f,
            new Vector2(source.Width / 2f, source.Height), scale * pulse,
            SpriteEffects.None, actorLayer);
    }

    private int[] ApplyCuratorArchiveRuleAttackBias(int[] basePool)
    {
        if (this.Phase < 2 || this.ActiveCuratorArchiveRule == "none")
            return basePool;
        IEnumerable<int> extra = this.ActiveCuratorArchiveRule switch
        {
            "loose_folios" => new[] { 0, 2 },
            "iron_bindings" => new[] { 3 },
            "mirror_draft" => new[] { 9 },
            "redacted_ledger" => new[] { 4, 4 },
            _ => Array.Empty<int>(),
        };
        return basePool.Concat(extra).ToArray();
    }

    private static string NormalizeCuratorArchiveRule(string? archiveRule)
    {
        string key = (archiveRule ?? string.Empty).Trim().ToLowerInvariant();
        return key is "loose_folios" or "iron_bindings" or "mirror_draft" or "redacted_ledger" ? key : "none";
    }

    private string CuratorArchiveRuleShort()
        => ModEntry.T($"boss.curator.rule.short.{this.ActiveCuratorArchiveRule}");

    private static Point MirrorCuratorTile(Point tile)
        => ClampArenaTile(new Point(27 - tile.X, tile.Y));

    private int CuratorRecordAttackId()
        => this.ActiveCuratorRecord.Tag switch
        {
            "risk" => 5,
            "precision" => 6,
            "pressure" => 7,
            "recovery" => 8,
            "mirror" => 9,
            _ => 4,
        };

    private string CuratorRecordShort()
        => ModEntry.T($"boss.curator.record.short.{this.ActiveCuratorRecord.Tag}");

    private Color CuratorRecordColor()
        => this.ActiveCuratorRecord.Tag switch
        {
            "risk" => new Color(232, 146, 93),
            "precision" => new Color(166, 218, 246),
            "pressure" => new Color(210, 112, 154),
            "recovery" => new Color(112, 207, 151),
            "mirror" => new Color(171, 150, 242),
            _ => new Color(166, 190, 232),
        };

    private (string Name, string Path, int Frames, int FrameTicks, bool Loop) CuratorAnimationClip(long now)
    {
        if (this.State == MilestoneBossState.Defeated)
            return ("defeat", HollowCuratorDefeatTexturePath, 12, 145, false);
        if (this.State == MilestoneBossState.PhaseTransition)
            return ("transition", HollowCuratorTransitionTexturePath, 12, 90, false);
        if (this.CuratorHurtUntilMs > now)
            return ("hurt", HollowCuratorHurtTexturePath, 6, 60, true);
        if (this.State == MilestoneBossState.Intro)
            return ("observe", HollowCuratorObserveTexturePath, 10, 120, false);
        if (this.State == MilestoneBossState.Decision)
            return this.Phase >= 2
                ? ("drift", HollowCuratorDriftTexturePath, 8, 105, true)
                : ("idle", HollowCuratorIdleTexturePath, 8, 120, true);
        if (this.State != MilestoneBossState.Telegraph)
            return ("idle", HollowCuratorIdleTexturePath, 8, 120, true);
        return this.CurrentAttack switch
        {
            2 or 4 => ("page_volley", HollowCuratorPageVolleyTexturePath, 10, 82, true),
            3 or 9 => ("mirror", HollowCuratorMirrorTexturePath, 10, 90, true),
            5 or 6 => ("observe", HollowCuratorObserveTexturePath, 10, 95, true),
            8 => ("adapt", HollowCuratorAdaptTexturePath, 10, 90, true),
            _ => ("cast", HollowCuratorCastTexturePath, 10, 86, true),
        };
    }

    private void UpdateCuratorVisualDamageState(long now)
    {
        if (this.CurrentKind != MilestoneBossKind.HollowCurator)
        {
            this.LastCuratorVisualHealth = -1;
            this.CuratorHurtUntilMs = 0;
            return;
        }
        Monster? curator = this.FindRole("curator", includeDead: true);
        if (curator is null)
            return;
        if (this.LastCuratorVisualHealth >= 0 && curator.Health < this.LastCuratorVisualHealth && curator.Health > 0)
            this.CuratorHurtUntilMs = now + 360L;
        this.LastCuratorVisualHealth = curator.Health;
    }

    private void DrawBossAuraVfx(SpriteBatch batch, MilestoneBossKind kind)
    {
        // VFX only. Low-alpha accents may overlap actors but never pretend to be solid scenery.
        long now = Environment.TickCount64;
        foreach (Monster actor in this.GetBossActors(includeDead: false))
        {
            string role = this.Role(actor);
            Vector2 world = actor.Position + new Vector2(32f, 50f);
            Vector2 c = Game1.GlobalToLocal(Game1.viewport, world);
            Color accent = role switch
            {
                "ignis" => new Color(235, 105, 74),
                "vita" => new Color(105, 205, 124),
                "aether" => new Color(105, 174, 235),
                "unified" => new Color(212, 161, 232),
                "mimi" => new Color(199, 139, 218),
                "curator" => this.CuratorRecordColor(),
                _ => new Color(166, 190, 232),
            };
            float pulse = 0.16f + 0.07f * (float)Math.Sin(now / 180d + actor.GetHashCode() * 0.01d);
            for (int i = 0; i < 4; i++)
            {
                float a = (float)(now / 520d + i * MathHelper.PiOver2);
                Vector2 p = c + new Vector2(MathF.Cos(a) * 34f, MathF.Sin(a) * 14f - 22f);
                batch.Draw(Game1.staminaRect, new Rectangle((int)p.X, (int)p.Y, 3, 3), accent * pulse);
            }
        }
    }

    private void DrawAttackTelegraph(SpriteBatch batch)
    {
        if (this.State != MilestoneBossState.Telegraph || this.CurrentAttack < 0)
            return;

        Color c = this.CurrentKind is null ? Color.White : this.KindColor(this.CurrentKind.Value);
        float pulse = 0.28f + 0.16f * (float)Math.Abs(Math.Sin(Environment.TickCount64 / 90d));
        int radius = this.CurrentAttack switch
        {
            3 or 5 or 7 or 25 or 28 => 2,
            13 or 24 or 27 => 2,
            _ => 1,
        };

        if (this.CurrentAttack == 6)
        {
            Color precision = new Color(185, 224, 255) * (pulse + 0.08f);
            DrawTileZone(batch, this.AttackTargetTile, 0, precision);
            DrawTileZone(batch, this.EchoTargetTile, 0, precision * 0.78f);
            return;
        }

        if (this.CurrentAttack is 4 or 26)
        {
            Color mirror = new Color(190, 166, 255) * (pulse + 0.08f);
            DrawTileZone(batch, this.EchoTargetTile, 1, mirror);
            DrawTileZone(batch, this.EchoTargetTile2, 1, mirror * 0.72f);
            return;
        }

        if (this.CurrentAttack == 27)
            c = this.TricolorCycle(this.MimiCadenceIndex);
        else if (this.CurrentKind == MilestoneBossKind.HollowCurator && this.CurrentAttack is >= 5 and <= 9)
            c = this.CurrentAttack == 9 && this.ActiveCuratorArchiveRule == "mirror_draft"
                ? new Color(186, 164, 246)
                : this.CuratorRecordColor();

        DrawTileZone(batch, this.AttackTargetTile, radius, c * pulse);

        if (this.CurrentAttack is 2 or 5 or 9 or 12 or 13 or 15 or 22 or 24 or 27 or 28)
            DrawTileZone(batch, this.AttackTargetTile2, 1, new Color(238, 218, 255) * pulse);

        if (this.CurrentAttack is 9 or 14 or 28)
            DrawTileZone(batch, this.EchoTargetTile, 1, new Color(190, 166, 255) * pulse);

        if (this.CurrentAttack == 11)
            DrawTileZone(batch, this.AttackTargetTile, 1, new Color(102, 212, 118) * pulse);
    }

    private void DrawRetreatGlyph(SpriteBatch batch)
    {
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, new Vector2(RetreatTile.X * 64f + 32, RetreatTile.Y * 64f + 36));
        DrawRect(batch, new Rectangle((int)local.X - 26, (int)local.Y - 3, 52, 6), new Color(220, 194, 130) * 0.55f);
    }

    private string DescribePhaseShort()
    {
        if (this.CurrentKind is null)
            return string.Empty;
        return this.CurrentKind switch
        {
            MilestoneBossKind.HollowCurator => this.Phase switch
            {
                1 => $"Observation • {this.CuratorRecordShort()} • Adapt {this.CuratorAdaptationStacks}/3",
                2 => $"Reflection • {this.CuratorRecordShort()} • {this.CuratorArchiveRuleShort()} • Adapt {this.CuratorAdaptationStacks}/3",
                _ => $"Curator's Truth • {this.CuratorRecordShort()} • {this.CuratorArchiveRuleShort()} • Adapt {this.CuratorAdaptationStacks}/3",
            },
            MilestoneBossKind.TricolorResonance => this.Phase < 4
                ? $"Three Guardians • {this.GetTricolorLivingSummary()}"
                : "Unified Resonance",
            MilestoneBossKind.Mimi => this.Phase switch
            {
                1 => "Familiar Power",
                2 => "Refined Control",
                3 => "True Resonance",
                _ => "MiMi • Resonance Master",
            },
            _ => string.Empty,
        };
    }

    private string GetTricolorLivingSummary()
    {
        string[] roles = this.GetBossActors(false).Select(this.Role).Where(r => r is "ignis" or "vita" or "aether").ToArray();
        return $"Ignis:{(roles.Contains("ignis") ? "ON" : "X")} Vita:{(roles.Contains("vita") ? "ON" : "X")} Aether:{(roles.Contains("aether") ? "ON" : "X")}";
    }

    private (int Hp, int Max) GetCombinedHealth()
    {
        Monster[] actors = this.GetBossActors(includeDead: true);
        int hp = actors.Sum(a => Math.Max(0, a.Health));
        int max = actors.Sum(a => Math.Max(1, a.MaxHealth));
        return (hp, max);
    }

    private Monster[] GetBossActors(bool includeDead)
    {
        GameLocation? arena = Game1.currentLocation;
        if (arena is null)
            return Array.Empty<Monster>();
        IEnumerable<Monster> query = arena.characters.OfType<Monster>().Where(a => a.modData.ContainsKey(BossMarkerKey));
        if (!includeDead)
            query = query.Where(a => a.Health > 0);
        return query.ToArray();
    }

    private Monster? FindRole(string role, bool includeDead)
        => this.GetBossActors(includeDead).FirstOrDefault(a => this.Role(a).Equals(role, StringComparison.OrdinalIgnoreCase));

    private string Role(Monster actor)
        => actor.modData.TryGetValue(BossRoleKey, out string? role) ? role : "unknown";

    private MilestoneBossKind? ResolveCurrentKind(GameLocation? location)
    {
        string? name = location?.NameOrUniqueName;
        if (string.IsNullOrWhiteSpace(name)) return null;
        if (name.Equals(HollowCuratorLocationName, StringComparison.OrdinalIgnoreCase)) return MilestoneBossKind.HollowCurator;
        if (name.Equals(TricolorLocationName, StringComparison.OrdinalIgnoreCase)) return MilestoneBossKind.TricolorResonance;
        if (name.Equals(MimiLocationName, StringComparison.OrdinalIgnoreCase)) return MilestoneBossKind.Mimi;
        return null;
    }

    private void EnsureAllLocations()
    {
        this.EnsureLocation(MilestoneBossKind.HollowCurator);
        this.EnsureLocation(MilestoneBossKind.TricolorResonance);
        this.EnsureLocation(MilestoneBossKind.Mimi);
    }

    private GameLocation? EnsureLocation(MilestoneBossKind kind)
    {
        string locationName = kind switch
        {
            MilestoneBossKind.HollowCurator => HollowCuratorLocationName,
            MilestoneBossKind.TricolorResonance => TricolorLocationName,
            _ => MimiLocationName,
        };
        string mapAsset = kind switch
        {
            MilestoneBossKind.HollowCurator => HollowCuratorMapAssetName,
            MilestoneBossKind.TricolorResonance => TricolorMapAssetName,
            _ => MimiMapAssetName,
        };
        GameLocation? existing = Game1.getLocationFromName(locationName);
        if (existing is not null)
            return existing;
        try
        {
            GameLocation arena = new(mapAsset, locationName);
            Game1.locations.Add(arena);
            return arena;
        }
        catch (Exception ex)
        {
            this.Monitor.Log($"0670 couldn't create {locationName}: {ex.GetType().Name}: {ex.Message}", LogLevel.Error);
            return null;
        }
    }

    private void ReturnToDeck()
    {
        GameLocation? deck = Game1.getLocationFromName(AirshipFoundationService.DeckLocationName);
        if (deck is not null)
        {
            this.RemoveMarkedActors(Game1.currentLocation);
            this.State = MilestoneBossState.Dormant;
            this.CurrentKind = null;
            Game1.warpFarmer(AirshipFoundationService.DeckLocationName, 12, 10, 2);
            return;
        }

        GameLocation? region1 = Game1.getLocationFromName(AirshipFoundationService.Region1LocationName);
        if (region1 is not null)
            Game1.warpFarmer(AirshipFoundationService.Region1LocationName, 20, 4, 2);
    }

    private void ResetRuntime(bool removeActors)
    {
        if (removeActors)
        {
            foreach (string name in new[] { HollowCuratorLocationName, TricolorLocationName, MimiLocationName })
                this.RemoveMarkedActors(Game1.getLocationFromName(name));
        }
        this.CurrentKind = null;
        this.State = MilestoneBossState.Dormant;
        this.Phase = 1;
        this.PendingPhase = 0;
        this.CurrentAttack = -1;
        this.StateStartedAtMs = 0;
        this.NextDecisionAtMs = 0;
        this.VictoryReturnAtMs = 0;
        this.AttackApplied = false;
        this.VictoryHandled = false;
        this.EchoTargetTile = Point.Zero;
        this.EchoTargetTile2 = Point.Zero;
        this.MimiCadenceIndex = 0;
        this.TricolorMotionSerial = 0;
        this.LastCuratorVisualHealth = -1;
        this.CuratorHurtUntilMs = 0;
        this.CuratorAdaptationStacks = 0;
        this.ActiveCuratorRecord = CuratorRunRecord.Neutral;
        this.PendingCuratorRecord = CuratorRunRecord.Neutral;
        this.HasPendingCuratorRecord = false;
        this.PendingCuratorArchiveRule = "none";
        this.ActiveCuratorArchiveRule = "none";
        this.HasPendingCuratorArchiveRule = false;
        this.CuratorRecordRevealed = false;
        this.DecisionSerial = 0;
        this.RouteConfirmUntilMs = 0;
        this.RouteConfirmKind = null;
    }

    private void RemoveMarkedActors(GameLocation? arena)
    {
        if (arena is null) return;
        foreach (NPC actor in arena.characters.Where(a => a.modData.ContainsKey(BossMarkerKey)).ToList())
            arena.characters.Remove(actor);
    }

    private static Point PlayerTile() => new((int)(Game1.player.Position.X / 64f), (int)(Game1.player.Position.Y / 64f));

    private static Point ClampArenaTile(Point p)
        => new(Math.Clamp(p.X, 2, 25), Math.Clamp(p.Y, 2, 16));

    private static bool PlayerWithin(Point tile, float radiusTiles)
    {
        Vector2 center = new(tile.X * 64f + 32, tile.Y * 64f + 32);
        Vector2 player = Game1.player.Position + new Vector2(32f, 32f);
        return Vector2.Distance(center, player) / 64f <= radiusTiles;
    }

    private static void DamagePlayer(int damage)
    {
        if (Game1.player.health <= 0) return;
        Game1.player.takeDamage(Math.Max(1, damage), false, null);
    }

    private Color KindColor(MilestoneBossKind kind) => kind switch
    {
        MilestoneBossKind.HollowCurator => new Color(112, 132, 242),
        MilestoneBossKind.TricolorResonance => new Color(197, 210, 255),
        MilestoneBossKind.Mimi => new Color(220, 142, 244),
        _ => Color.White,
    };

    private Color RoleColor(string role, MilestoneBossKind kind) => role switch
    {
        "ignis" => new Color(238, 92, 78),
        "vita" => new Color(99, 210, 118),
        "aether" => new Color(89, 148, 241),
        "unified" => Color.White,
        "curator" => new Color(108, 133, 242),
        "mimi" => new Color(225, 145, 244),
        _ => this.KindColor(kind),
    };

    private Color TricolorCycle(int i) => (i % 3) switch
    {
        0 => new Color(238, 92, 78),
        1 => new Color(99, 210, 118),
        _ => new Color(89, 148, 241),
    };

    private static void DrawTileZone(SpriteBatch batch, Point center, int radius, Color color)
    {
        Rectangle world = new((center.X - radius) * 64, (center.Y - radius) * 64, (radius * 2 + 1) * 64, (radius * 2 + 1) * 64);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, new Vector2(world.X, world.Y));
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X, (int)local.Y, world.Width, world.Height), color);
    }

    private static void DrawRect(SpriteBatch batch, Rectangle rect, Color color)
        => batch.Draw(Game1.staminaRect, rect, color);

    private static void DrawDiamond(SpriteBatch batch, Vector2 center, int radius, Color color)
    {
        for (int y = -radius; y <= radius; y++)
        {
            int half = Math.Max(1, radius - Math.Abs(y));
            DrawRect(batch, new Rectangle((int)center.X - half, (int)center.Y + y, half * 2 + 1, 1), color);
        }
    }
}
