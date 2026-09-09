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
/// 0672 encounter-depth pass for the 40/60/80-card milestone bosses.
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
    private const string HollowCuratorTexturePath = "assets/bosses/milestone/hollow_curator.png";
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
    private int DecisionSerial;
    private Point EchoTargetTile;
    private Point EchoTargetTile2;
    private int MimiCadenceIndex;
    private int TricolorMotionSerial;

    public MilestoneBossService(IModHelper helper, IMonitor monitor, SaveService save)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
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
        this.AnchorBossActors();

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

        this.DrawArenaIdentity(e.SpriteBatch, kind.Value);
        foreach (Monster actor in this.GetBossActors(includeDead: true))
            this.DrawActor(e.SpriteBatch, actor, kind.Value);
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

    public string Describe()
    {
        string current = this.CurrentKind?.ToString() ?? "none";
        (int hp, int max) = this.GetCombinedHealth();
        return $"0672 MilestoneBoss | Current={current} | State={this.State} | Phase={this.Phase} | HP={hp}/{max} | " +
               $"CuratorAdapt={this.CuratorAdaptationStacks}/3 | BossCards=[{string.Join(',', this.Save.Data.BossCardsUnlocked ?? new HashSet<string>())}] | " +
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
        this.DecisionSerial = 0;
        this.AttackTargetTile = PlayerTile();
        this.AttackTargetTile2 = this.AttackTargetTile;
        this.EchoTargetTile = this.AttackTargetTile;
        this.EchoTargetTile2 = this.AttackTargetTile2;
        this.MimiCadenceIndex = 0;
        this.TricolorMotionSerial = 0;

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
                int[] pool = this.Phase switch
                {
                    1 => new[] { 0, 0, 1 },
                    2 => new[] { 0, 1, 2, 4, 4 },
                    _ => new[] { 0, 2, 3, 4, 4 },
                };
                this.CurrentAttack = pool[this.Rng.Next(pool.Length)];
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

    private int CurrentDecisionGapMs() => this.CurrentKind switch
    {
        MilestoneBossKind.HollowCurator => this.Phase switch { 1 => 780, 2 => 650, _ => 520 },
        MilestoneBossKind.TricolorResonance => this.Phase >= 4 ? 520 : 720,
        MilestoneBossKind.Mimi => this.Phase switch { 1 => 720, 2 => 620, 3 => 520, _ => 430 },
        _ => 650,
    };

    private void DrawActor(SpriteBatch batch, Monster actor, MilestoneBossKind kind)
    {
        string role = this.Role(actor);
        Vector2 feet = Game1.GlobalToLocal(Game1.viewport, actor.Position + new Vector2(32f, 58f));
        Texture2D texture;
        Rectangle source;
        float scale;
        Vector2 offset = Vector2.Zero;
        if (role == "curator")
        {
            texture = this.Helper.ModContent.Load<Texture2D>(HollowCuratorTexturePath);
            int frame = this.State == MilestoneBossState.Telegraph || this.Phase >= 3 ? 1 : 0;
            source = new Rectangle(frame * 48, 0, 48, 64);
            scale = 2.35f;
            offset = new Vector2(0f, 10f);
        }
        else if (role is "ignis" or "vita" or "aether")
        {
            texture = this.Helper.ModContent.Load<Texture2D>(TricolorGuardiansTexturePath);
            int frame = role == "ignis" ? 0 : role == "vita" ? 1 : 2;
            source = new Rectangle(frame * 48, 0, 48, 48);
            scale = 2.3f;
        }
        else if (role == "unified")
        {
            texture = this.Helper.ModContent.Load<Texture2D>(TricolorUnifiedTexturePath);
            int frame = this.State == MilestoneBossState.Telegraph ? 1 : 0;
            source = new Rectangle(frame * 64, 0, 64, 64);
            scale = 2.2f;
        }
        else
        {
            texture = this.Helper.ModContent.Load<Texture2D>(MimiTexturePath);
            int frame = this.Phase >= 4 ? 2 : this.Phase >= 3 ? 1 : 0;
            source = new Rectangle(frame * 64, 0, 64, 64);
            scale = 2.18f;
            offset = new Vector2(0f, 6f);
        }
        float pulse = this.State == MilestoneBossState.PhaseTransition ? 0.88f + 0.12f * (float)Math.Abs(Math.Sin(Environment.TickCount64 / 75d)) : 1f;
        Color tint = this.State == MilestoneBossState.Defeated ? Color.White * 0.58f : Color.White;
        int shadowWidth = (int)(source.Width * scale * 0.62f);
        batch.Draw(Game1.staminaRect, new Rectangle((int)feet.X - shadowWidth / 2, (int)feet.Y - 7, shadowWidth, 9), Color.Black * 0.28f);
        batch.Draw(texture, feet + offset, source, tint, 0f, new Vector2(source.Width / 2f, source.Height), scale * pulse, SpriteEffects.None, 0.99f);
    }

    private void DrawAttackTelegraph(SpriteBatch batch)
    {
        if (this.State != MilestoneBossState.Telegraph || this.CurrentAttack < 0)
            return;

        Color c = this.CurrentKind is null ? Color.White : this.KindColor(this.CurrentKind.Value);
        float pulse = 0.28f + 0.16f * (float)Math.Abs(Math.Sin(Environment.TickCount64 / 90d));
        int radius = this.CurrentAttack switch
        {
            3 or 25 or 28 => 2,
            13 or 24 or 27 => 2,
            _ => 1,
        };

        if (this.CurrentAttack is 4 or 26)
        {
            Color mirror = new Color(190, 166, 255) * (pulse + 0.08f);
            DrawTileZone(batch, this.EchoTargetTile, 1, mirror);
            DrawTileZone(batch, this.EchoTargetTile2, 1, mirror * 0.72f);
            return;
        }

        if (this.CurrentAttack == 27)
            c = this.TricolorCycle(this.MimiCadenceIndex);

        DrawTileZone(batch, this.AttackTargetTile, radius, c * pulse);

        if (this.CurrentAttack is 2 or 12 or 13 or 15 or 22 or 24 or 27 or 28)
            DrawTileZone(batch, this.AttackTargetTile2, 1, new Color(238, 218, 255) * pulse);

        if (this.CurrentAttack is 14 or 28)
            DrawTileZone(batch, this.EchoTargetTile, 1, new Color(190, 166, 255) * pulse);

        if (this.CurrentAttack == 11)
            DrawTileZone(batch, this.AttackTargetTile, 1, new Color(102, 212, 118) * pulse);
    }

    private void DrawArenaIdentity(SpriteBatch batch, MilestoneBossKind kind)
    {
        string path = kind switch
        {
            MilestoneBossKind.HollowCurator => HollowArenaTexturePath,
            MilestoneBossKind.TricolorResonance => TricolorArenaTexturePath,
            _ => MimiArenaTexturePath,
        };
        Texture2D texture = this.Helper.ModContent.Load<Texture2D>(path);
        Point[] placements = kind switch
        {
            MilestoneBossKind.HollowCurator => new[] { new Point(6,5), new Point(21,5), new Point(6,13), new Point(21,13), new Point(10,4), new Point(17,4), new Point(10,15), new Point(17,15) },
            MilestoneBossKind.TricolorResonance => new[] { new Point(8,5), new Point(14,3), new Point(20,5), new Point(5,11), new Point(23,11), new Point(9,14), new Point(14,15), new Point(19,14) },
            _ => new[] { new Point(7,5), new Point(11,4), new Point(16,4), new Point(20,5), new Point(6,12), new Point(21,12), new Point(10,15), new Point(17,15) },
        };
        for (int i = 0; i < placements.Length; i++)
        {
            Point p = placements[i];
            Vector2 local = Game1.GlobalToLocal(Game1.viewport, new Vector2(p.X * 64f + 32, p.Y * 64f + 48));
            Rectangle src = new((i % 4) * 32, ((i / 4) % 2) * 32, 32, 32);
            float scale = kind == MilestoneBossKind.Mimi ? 1.75f : 1.9f;
            batch.Draw(texture, local, src, Color.White * 0.92f, 0f, new Vector2(16f, 32f), scale, SpriteEffects.None, 0.985f);
        }
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
                1 => $"Observation • Adapt {this.CuratorAdaptationStacks}/3",
                2 => $"Reflection • Adapt {this.CuratorAdaptationStacks}/3",
                _ => $"Curator's Truth • Adapt {this.CuratorAdaptationStacks}/3",
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
        this.CuratorAdaptationStacks = 0;
        this.DecisionSerial = 0;
        this.EchoTargetTile = Point.Zero;
        this.EchoTargetTile2 = Point.Zero;
        this.MimiCadenceIndex = 0;
        this.TricolorMotionSerial = 0;
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
