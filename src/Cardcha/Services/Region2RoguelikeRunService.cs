using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Monsters;
using StardewValley.Objects;

namespace Cardcha.Services;

internal enum Region2RoomKind
{
    Vestibule,
    InkboundStacks,
    MirrorGallery,
    WardenVault,
}

internal enum Region2NodeKind
{
    Combat,
    Ambush,
    Elite,
    MirrorChoice,
    ArchiveEvent,
    Cache,
    Restoration,
    CursedArchive,
    BossGate,
    FinalCache,
}

internal enum Region2RunModifier
{
    LooseFolios,
    IronBindings,
    MirrorDraft,
    RedactedLedger,
}

/// <summary>
/// 0680 Region II roguelike route foundation.
///
/// The Forgotten Archive is no longer a fixed three-wave room. A run targets 6-9 nodes and
/// branches between combat, risk, recovery, event and reward nodes. Hollow Curator can be
/// challenged from node 6 onward once the real 40-card gate is satisfied, while the player may
/// choose to go deeper for more reward before committing to the boss.
///
/// This service owns Region II runtime only. Region III/IV remain on RegionExpeditionService.
/// Physical art stays in TMX/native actors; this service does not paint physical props from
/// RenderedWorld.
/// </summary>
internal sealed class Region2RoguelikeRunService
{
    private const string NodeMarkerKey = "Ronvotri.Cardcha/0680Region2Node";
    private const string InteractionMarkerKey = "Ronvotri.Cardcha/0683Region2Interaction";
    private const string RoomMechanicMarkerKey = "Ronvotri.Cardcha/0684RoomMechanic";
    private const long ExtractConfirmWindowMs = 5000L;
    private const long MirrorTelegraphMs = 1050L;
    private const long InkTelegraphMs = 900L;
    private const long VaultTelegraphMs = 950L;
    private static readonly Point BossGateTile = new(20, 5);
    public const string InkboundStacksLocationName = "Cardcha_Region2_InkboundStacks";
    public const string InkboundStacksMapAssetName = "Maps/Cardcha_Region2_InkboundStacks";
    public const string MirrorGalleryLocationName = "Cardcha_Region2_MirrorGallery";
    public const string MirrorGalleryMapAssetName = "Maps/Cardcha_Region2_MirrorGallery";
    public const string WardenVaultLocationName = "Cardcha_Region2_WardenVault";
    public const string WardenVaultMapAssetName = "Maps/Cardcha_Region2_WardenVault";
    private const string InkboundStacksMapPath = "assets/region2_inkbound_stacks.tmx";
    private const string MirrorGalleryMapPath = "assets/region2_mirror_gallery.tmx";
    private const string WardenVaultMapPath = "assets/region2_warden_vault.tmx";

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;
    private readonly AirshipFoundationService Airship;
    private readonly RegionExpeditionService LegacyExpeditions;

    private Func<string>? BossGateAction;
    private Func<string>? BossGateDebugAction;
    private Action<CuratorRunRecord>? CuratorRecordSink;
    private Action<string>? CuratorArchiveRuleSink;

    private bool Active;
    private bool LeavingForBoss;
    private bool RouteComplete;
    private bool BossGateReady;
    private bool ChoicePending;
    private bool ChoiceDeferred;
    private bool DebugBossGateEntry;
    private bool NodeSpawned;
    private bool AwaitingRoomInteraction;
    private Point ActiveInteractionTile;
    private bool PendingInternalRoomWarp;
    private Region2NodeKind PendingNodeKind;
    private Region2RoomKind CurrentRoom = Region2RoomKind.Vestibule;
    private int CurrentNode;
    private int TargetNodes;
    private int RunSeed;
    private int UnbankedScrap;
    private int UnbankedShiny;
    private int TotalBankedScrap;
    private int TotalBankedShiny;
    private int NodeStartHealth;
    private int RiskRecord;
    private int PrecisionRecord;
    private int PressureRecord;
    private int RecoveryRecord;
    private int MirrorRecord;
    private long ExtractConfirmUntilMs;
    private Region2NodeKind CurrentKind;
    private Region2NodeKind ChoiceA;
    private Region2NodeKind ChoiceB;
    private string LastCuratorRecord = "none";
    private Region2RunModifier ActiveRunModifier = Region2RunModifier.MirrorDraft;
    private string LastEncounterMix = "none";
    private string ActiveRoomMechanic = "none";
    private long RoomMechanicNextAtMs;
    private long RoomMechanicResolveAtMs;
    private Point[] RoomMechanicTiles = Array.Empty<Point>();
    private int RoomMechanicCycles;
    private int RoomMechanicHits;

    public bool IsActive => this.Active;

    public Region2RoguelikeRunService(
        IModHelper helper,
        IMonitor monitor,
        SaveService save,
        AirshipFoundationService airship,
        RegionExpeditionService legacyExpeditions)
    {
        this.Helper = helper;
        this.Monitor = monitor;
        this.Save = save;
        this.Airship = airship;
        this.LegacyExpeditions = legacyExpeditions;
    }

    public void BindBossGateHandlers(Func<string> realHandler, Func<string> debugHandler)
    {
        this.BossGateAction = realHandler;
        this.BossGateDebugAction = debugHandler;
    }

    public void BindCuratorRecordSink(Action<CuratorRunRecord> sink)
        => this.CuratorRecordSink = sink;

    public void BindCuratorArchiveRuleSink(Action<string> sink)
        => this.CuratorArchiveRuleSink = sink;

    public void OnAssetRequested(object? sender, AssetRequestedEventArgs e)
    {
        if (e.NameWithoutLocale.IsEquivalentTo(InkboundStacksMapAssetName))
            e.LoadFromModFile<xTile.Map>(InkboundStacksMapPath, AssetLoadPriority.Exclusive);
        else if (e.NameWithoutLocale.IsEquivalentTo(MirrorGalleryMapAssetName))
            e.LoadFromModFile<xTile.Map>(MirrorGalleryMapPath, AssetLoadPriority.Exclusive);
        else if (e.NameWithoutLocale.IsEquivalentTo(WardenVaultMapAssetName))
            e.LoadFromModFile<xTile.Map>(WardenVaultMapPath, AssetLoadPriority.Exclusive);
    }

    public void OnSaveLoaded(object? sender, SaveLoadedEventArgs e)
    {
        this.ResetRuntime(clearEnemies: true);
        this.EnsureRoomLocations();
    }
    public void OnDayStarted(object? sender, DayStartedEventArgs e)
    {
        this.ResetRuntime(clearEnemies: true);
        this.EnsureRoomLocations();
    }
    public void OnReturnedToTitle(object? sender, ReturnedToTitleEventArgs e) => this.ResetRuntime(clearEnemies: false);

    public void PrepareNormalDebugEntry()
    {
        this.DebugBossGateEntry = false;
    }

    public void PrepareBossGateDebugEntry()
    {
        this.DebugBossGateEntry = true;
    }

    public void OnWarped(object? sender, WarpedEventArgs e)
    {
        bool incoming = IsRegion2(e.NewLocation);
        bool outgoing = IsRegion2(e.OldLocation);

        if (incoming && outgoing)
        {
            this.ClearInteractionObject(e.OldLocation);
            this.CurrentRoom = ResolveRoom(e.NewLocation);
            this.ClearRunEnemies(e.OldLocation);
            if (this.PendingInternalRoomWarp)
            {
                this.PendingInternalRoomWarp = false;
                Region2NodeKind kind = this.PendingNodeKind;
                this.BeginNodeHere(e.NewLocation, kind);
            }
            return;
        }

        if (incoming)
        {
            this.LegacyExpeditions.SuspendLegacyRegion2RuntimeForRoguelike();
            this.CurrentRoom = ResolveRoom(e.NewLocation);
            this.StartRun(e.NewLocation, this.DebugBossGateEntry);
            this.DebugBossGateEntry = false;
            return;
        }

        if (outgoing && this.Active)
        {
            if (!this.LeavingForBoss)
            {
                int lostScrap = this.UnbankedScrap;
                int lostShiny = this.UnbankedShiny;
                if (lostScrap > 0 || lostShiny > 0)
                    Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.lost", new { scrap = lostScrap, shiny = lostShiny }));
            }
            this.ResetRuntime(clearEnemies: false);
        }
    }

    public void OnUpdateTicked(object? sender, UpdateTickedEventArgs e)
    {
        if (!Context.IsWorldReady || !this.Active || !IsRegion2(Game1.currentLocation) || Game1.currentLocation is null)
            return;
        if (this.ChoiceDeferred && !Game1.dialogueUp && Game1.activeClickableMenu is null)
        {
            this.ChoiceDeferred = false;
            this.PrepareRouteChoice(Game1.currentLocation);
            return;
        }
        if (this.RouteComplete || this.BossGateReady || this.ChoicePending || this.ChoiceDeferred)
            return;
        if (!IsCombatKind(this.CurrentKind) || !this.NodeSpawned)
        {
            this.ClearRoomMechanicTelegraph();
            return;
        }

        this.UpdateRoomMechanic(Game1.currentLocation);
        if (CountRunEnemies(Game1.currentLocation) > 0)
            return;

        this.ResetRoomMechanicState();
        this.NodeSpawned = false;
        this.CompleteCurrentNode(Game1.currentLocation);
    }

    public void OnRenderedWorld(object? sender, RenderedWorldEventArgs e)
    {
        if (!Context.IsWorldReady || !this.Active || !IsRegion2(Game1.currentLocation)
            || this.RoomMechanicResolveAtMs <= Environment.TickCount64 || this.RoomMechanicTiles.Length == 0)
            return;

        Color color = this.ActiveRoomMechanic switch
        {
            "mirror_trace" => new Color(151, 191, 232),
            "ink_sweep" => new Color(136, 82, 142),
            "warden_seal" => new Color(222, 181, 86),
            _ => new Color(210, 210, 210),
        };
        long left = Math.Max(0L, this.RoomMechanicResolveAtMs - Environment.TickCount64);
        float pulse = 0.32f + 0.22f * (1f - Math.Min(1f, left / 1100f));
        foreach (Point tile in this.RoomMechanicTiles)
            DrawHazardOutline(e.SpriteBatch, tile, color * pulse);
    }

    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady || !this.Active || !e.Button.IsActionButton()
            || Game1.currentLocation is null || !IsRegion2(Game1.currentLocation)
            || Game1.activeClickableMenu is not null || Game1.dialogueUp || Game1.eventUp)
            return;

        Point player = PlayerTile();
        Point action = Game1.player.GetGrabTile().ToPoint();

        if (this.AwaitingRoomInteraction && this.TryHandleRoomInteraction(e, Game1.currentLocation, action))
        {
            this.Helper.Input.Suppress(e.Button);
            return;
        }

        bool gateClose = Math.Abs(player.X - BossGateTile.X) <= 2 && Math.Abs(player.Y - BossGateTile.Y) <= 2;
        bool gateFacing = Math.Abs(action.X - BossGateTile.X) <= 1 && Math.Abs(action.Y - BossGateTile.Y) <= 1;
        if (this.CurrentRoom == Region2RoomKind.WardenVault && (gateClose || gateFacing))
        {
            this.Helper.Input.Suppress(e.Button);
            this.TryUseBossGate();
            return;
        }

        Point extract = ResolveExtractionTile(Game1.currentLocation);
        bool extractClose = Math.Abs(player.X - extract.X) <= 2 && Math.Abs(player.Y - extract.Y) <= 2;
        bool extractFacing = Math.Abs(action.X - extract.X) <= 1 && Math.Abs(action.Y - extract.Y) <= 1;
        if (!extractClose && !extractFacing)
            return;

        this.Helper.Input.Suppress(e.Button);
        this.TryExtract();
    }

    public string DebugClearCurrentNode()
    {
        if (!Context.IsWorldReady || !this.Active || !IsRegion2(Game1.currentLocation) || Game1.currentLocation is null)
            return "No active Region II roguelike node.";
        if (this.AwaitingRoomInteraction)
            return this.DebugResolveRoomInteraction();
        if (!IsCombatKind(this.CurrentKind))
            return $"Region II node {this.CurrentNode}/{this.TargetNodes} is {this.CurrentKind}; there are no combat enemies to clear.";

        int removed = 0;
        for (int i = Game1.currentLocation.characters.Count - 1; i >= 0; i--)
        {
            if (Game1.currentLocation.characters[i] is Monster monster && monster.modData.ContainsKey(NodeMarkerKey))
            {
                monster.Health = 0;
                Game1.currentLocation.characters.RemoveAt(i);
                removed++;
            }
        }
        return $"TEST: cleared {removed} Region II node enemy/enemies. Node completion will resolve on the next update tick.";
    }

    public string Describe()
    {
        return $"0685 Region II Rogue: modifier={this.ActiveRunModifier}, mix={this.LastEncounterMix}, active={this.Active}, room={this.CurrentRoom}, node={this.CurrentNode}/{this.TargetNodes}, kind={this.CurrentKind}, interaction={this.AwaitingRoomInteraction}, mechanic={this.ActiveRoomMechanic}[{this.RoomMechanicCycles} cycles/{this.RoomMechanicHits} hits], "
            + $"choicePending={this.ChoicePending}, bossGate={this.BossGateReady}, complete={this.RouteComplete}, "
            + $"unbanked={this.UnbankedScrap}S/{this.UnbankedShiny}Sh, banked={this.TotalBankedScrap}S/{this.TotalBankedShiny}Sh, "
            + $"record={this.CurrentRecordTag()} [risk={this.RiskRecord}, precision={this.PrecisionRecord}, pressure={this.PressureRecord}, recovery={this.RecoveryRecord}, mirror={this.MirrorRecord}], "
            + "runLength=6-9 nodes; Boss Gate eligible from node 6 when Boss I + 40 cards are satisfied.";
    }


    public string DescribeRoomMechanic()
    {
        long now = Environment.TickCount64;
        long telegraphMs = this.RoomMechanicResolveAtMs > now ? this.RoomMechanicResolveAtMs - now : 0L;
        long nextMs = this.RoomMechanicNextAtMs > now ? this.RoomMechanicNextAtMs - now : 0L;
        return $"0684 RoomMechanic: active={this.Active}, room={this.CurrentRoom}, kind={this.CurrentKind}, tag={this.ActiveRoomMechanic}, "
            + $"telegraph={telegraphMs}ms, next={nextMs}ms, tiles={this.RoomMechanicTiles.Length}, cycles={this.RoomMechanicCycles}, hits={this.RoomMechanicHits}.";
    }

    private void StartRun(GameLocation location, bool debugBossGate)
    {
        this.ClearRunEnemies(location);
        this.Active = true;
        this.LeavingForBoss = false;
        this.RouteComplete = false;
        this.BossGateReady = false;
        this.ChoicePending = false;
        this.ChoiceDeferred = false;
        this.NodeSpawned = false;
        this.AwaitingRoomInteraction = false;
        this.ActiveInteractionTile = Point.Zero;
        this.CurrentNode = 1;
        this.UnbankedScrap = 0;
        this.UnbankedShiny = 0;
        this.TotalBankedScrap = 0;
        this.TotalBankedShiny = 0;
        this.RiskRecord = 0;
        this.PrecisionRecord = 0;
        this.PressureRecord = 0;
        this.RecoveryRecord = 0;
        this.MirrorRecord = 0;
        this.LastCuratorRecord = "none";
        this.LastEncounterMix = "none";
        this.ExtractConfirmUntilMs = 0;

        int flights = Math.Max(0, this.Save.Data.AirshipFlightsTaken);
        this.RunSeed = unchecked((int)Game1.uniqueIDForThisGame + Game1.Date.TotalDays * 1009 + flights * 7919 + 0x2A80);
        Random random = new(this.RunSeed);
        this.TargetNodes = 6 + random.Next(4); // 6-9, aligned with Region I run length without copying its route logic.
        this.ActiveRunModifier = PickRunModifier(random);

        if (debugBossGate)
        {
            this.CurrentNode = 6;
            this.TargetNodes = Math.Max(6, this.TargetNodes);
            this.LastCuratorRecord = "debug";
            Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.debug_bossgate"));
            this.BeginNode(location, Region2NodeKind.BossGate);
            return;
        }

        Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.start", new
        {
            total = this.TargetNodes,
            modifier = this.RunModifierDisplayName(),
            effect = this.RunModifierEffectText()
        }));
        this.BeginNode(location, Region2NodeKind.Combat);
    }

    private void BeginNode(GameLocation location, Region2NodeKind kind)
    {
        Region2RoomKind targetRoom = this.ResolveRoomForNode(kind);
        string targetName = RoomLocationName(targetRoom);
        if (!location.NameOrUniqueName.Equals(targetName, StringComparison.OrdinalIgnoreCase))
        {
            GameLocation? target = this.EnsureRoomLocation(targetRoom);
            if (target is not null)
            {
                this.PendingInternalRoomWarp = true;
                this.PendingNodeKind = kind;
                this.ClearRunEnemies(location);
                Point arrival = RoomArrivalTile(targetRoom);
                Game1.warpFarmer(target.NameOrUniqueName, arrival.X, arrival.Y, 0);
                return;
            }
        }
        this.CurrentRoom = targetRoom;
        this.BeginNodeHere(location, kind);
    }

    private void BeginNodeHere(GameLocation location, Region2NodeKind kind)
    {
        this.CurrentKind = kind;
        this.ChoicePending = false;
        this.BossGateReady = false;
        this.NodeSpawned = false;
        this.ResetRoomMechanicState();
        this.AwaitingRoomInteraction = false;
        this.ActiveInteractionTile = Point.Zero;
        this.ClearInteractionObject(location);
        this.ExtractConfirmUntilMs = 0;
        this.NodeStartHealth = Math.Max(1, Game1.player.health);

        if (kind == Region2NodeKind.BossGate)
        {
            this.BossGateReady = true;
            this.LastCuratorRecord = this.CurrentRecordTag();
            Game1.playSound("discoverMineral");
            Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.bossgate_ready", new { record = this.RecordDisplayName(this.LastCuratorRecord) }));
            return;
        }

        if (kind == Region2NodeKind.FinalCache || IsManualInteractionKind(kind))
        {
            this.PrepareRoomInteraction(location, kind);
            return;
        }

        if (kind == Region2NodeKind.CursedArchive)
        {
            this.PrepareRoomInteraction(location, kind);
            return;
        }

        if (IsCombatKind(kind))
        {
            this.SpawnNodeEnemies(location, kind);
            this.NodeSpawned = true;
            this.ArmRoomMechanicForCombat(location);
            Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.node", new
            {
                node = this.CurrentNode,
                total = this.TargetNodes,
                kind = this.NodeDisplayName(kind)
            }));
            return;
        }
    }

    private void CompleteCurrentNode(GameLocation location)
    {
        this.ResetRoomMechanicState();
        if (IsCombatKind(this.CurrentKind))
        {
            this.UpdateCombatRecord();
            this.AwardNode(this.CurrentKind);
        }

        if (this.CurrentNode == 3 || this.CurrentNode == 6)
            this.BankCheckpoint();

        if (this.CurrentNode >= this.TargetNodes)
        {
            if (this.CanChallengeBoss())
            {
                this.CurrentKind = Region2NodeKind.BossGate;
                this.BossGateReady = true;
                this.LastCuratorRecord = this.CurrentRecordTag();
                Game1.playSound("discoverMineral");
                Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.bossgate_ready", new { record = this.RecordDisplayName(this.LastCuratorRecord) }));
            }
            else
            {
                // 0684 audit correction: route-end Final Cache must remain the physical 0683 Chest interaction.
                // Never auto-award it from the node-completion path.
                this.BeginNode(location, Region2NodeKind.FinalCache);
            }
            return;
        }

        if (Game1.dialogueUp || Game1.activeClickableMenu is not null)
        {
            this.ChoiceDeferred = true;
            return;
        }
        this.PrepareRouteChoice(location);
    }

    private void PrepareRouteChoice(GameLocation location)
    {
        int nextNode = this.CurrentNode + 1;
        Random random = new(unchecked(this.RunSeed + nextNode * 104729 + this.RiskRecord * 97 + this.MirrorRecord * 193));

        if (this.CanChallengeBoss() && nextNode >= 6)
        {
            this.ChoiceA = Region2NodeKind.BossGate;
            this.ChoiceB = PickDeepRoute(random);
        }
        else if (nextNode >= this.TargetNodes)
        {
            this.ChoiceA = this.CanChallengeBoss() ? Region2NodeKind.BossGate : Region2NodeKind.FinalCache;
            this.ChoiceB = this.ChoiceA;
        }
        else
        {
            this.ChoiceA = PickRoute(random, previous: this.CurrentKind, exclude: null);
            this.ChoiceB = PickRoute(random, previous: this.CurrentKind, exclude: this.ChoiceA);
        }

        if (this.ChoiceA == this.ChoiceB)
        {
            this.CurrentNode = nextNode;
            this.BeginNode(location, this.ChoiceA);
            return;
        }

        this.ChoicePending = true;
        string prompt = ModEntry.T("airship.region2.rogue.choose", new { node = nextNode, total = this.TargetNodes });
        Response[] responses =
        {
            new("cardcha_r2_a", this.RouteChoiceLabel(this.ChoiceA)),
            new("cardcha_r2_b", this.RouteChoiceLabel(this.ChoiceB)),
        };
        location.createQuestionDialogue(prompt, responses, (Farmer _, string answer) =>
        {
            if (!this.Active || !IsRegion2(Game1.currentLocation))
                return;
            Region2NodeKind selected = answer == "cardcha_r2_b" ? this.ChoiceB : this.ChoiceA;
            this.ChoicePending = false;
            this.CurrentNode = nextNode;
            if (selected is Region2NodeKind.Elite or Region2NodeKind.CursedArchive)
                this.RiskRecord++;
            this.BeginNode(Game1.currentLocation!, selected);
        });
    }

    private Region2NodeKind PickDeepRoute(Random random)
    {
        Region2NodeKind[] deep =
        {
            Region2NodeKind.Elite,
            Region2NodeKind.CursedArchive,
            Region2NodeKind.MirrorChoice,
            Region2NodeKind.Cache,
            Region2NodeKind.Ambush,
        };
        return this.PickWeightedRoute(random, deep);
    }

    private Region2NodeKind PickRoute(Random random, Region2NodeKind previous, Region2NodeKind? exclude)
    {
        Region2NodeKind[] pool =
        {
            Region2NodeKind.Combat,
            Region2NodeKind.Ambush,
            Region2NodeKind.Elite,
            Region2NodeKind.MirrorChoice,
            Region2NodeKind.ArchiveEvent,
            Region2NodeKind.Cache,
            Region2NodeKind.Restoration,
            Region2NodeKind.CursedArchive,
        };
        List<Region2NodeKind> candidates = pool
            .Where(k => k != previous && (!exclude.HasValue || k != exclude.Value))
            .ToList();
        return this.PickWeightedRoute(random, candidates);
    }

    private Region2NodeKind PickWeightedRoute(Random random, IEnumerable<Region2NodeKind> candidates)
    {
        List<(Region2NodeKind Kind, int Weight)> weighted = candidates
            .Select(kind => (kind, Math.Max(1, RunModifierRouteWeight(this.ActiveRunModifier, kind))))
            .ToList();
        if (weighted.Count == 0)
            return Region2NodeKind.Combat;

        int total = weighted.Sum(p => p.Weight);
        int roll = random.Next(total);
        foreach ((Region2NodeKind kind, int weight) in weighted)
        {
            if (roll < weight)
                return kind;
            roll -= weight;
        }
        return weighted[^1].Kind;
    }

    private static int RunModifierRouteWeight(Region2RunModifier modifier, Region2NodeKind kind)
        => modifier switch
        {
            Region2RunModifier.LooseFolios => kind switch
            {
                Region2NodeKind.Combat => 22,
                Region2NodeKind.Ambush => 28,
                Region2NodeKind.Elite => 10,
                Region2NodeKind.MirrorChoice => 8,
                Region2NodeKind.ArchiveEvent => 8,
                Region2NodeKind.Cache => 7,
                Region2NodeKind.Restoration => 6,
                Region2NodeKind.CursedArchive => 11,
                _ => 10,
            },
            Region2RunModifier.IronBindings => kind switch
            {
                Region2NodeKind.Combat => 12,
                Region2NodeKind.Ambush => 6,
                Region2NodeKind.Elite => 26,
                Region2NodeKind.MirrorChoice => 7,
                Region2NodeKind.ArchiveEvent => 8,
                Region2NodeKind.Cache => 18,
                Region2NodeKind.Restoration => 12,
                Region2NodeKind.CursedArchive => 11,
                _ => 10,
            },
            Region2RunModifier.MirrorDraft => kind switch
            {
                Region2NodeKind.Combat => 12,
                Region2NodeKind.Ambush => 10,
                Region2NodeKind.Elite => 9,
                Region2NodeKind.MirrorChoice => 28,
                Region2NodeKind.ArchiveEvent => 20,
                Region2NodeKind.Cache => 8,
                Region2NodeKind.Restoration => 10,
                Region2NodeKind.CursedArchive => 8,
                _ => 10,
            },
            Region2RunModifier.RedactedLedger => kind switch
            {
                Region2NodeKind.Combat => 8,
                Region2NodeKind.Ambush => 10,
                Region2NodeKind.Elite => 12,
                Region2NodeKind.MirrorChoice => 8,
                Region2NodeKind.ArchiveEvent => 12,
                Region2NodeKind.Cache => 18,
                Region2NodeKind.Restoration => 18,
                Region2NodeKind.CursedArchive => 28,
                _ => 10,
            },
            _ => 10,
        };

    private void ResolveNonCombatNode(Region2NodeKind kind)
    {
        switch (kind)
        {
            case Region2NodeKind.MirrorChoice:
                this.MirrorRecord++;
                this.UnbankedScrap += 3;
                if ((this.RunSeed + this.CurrentNode) % 3 == 0)
                    this.UnbankedShiny++;
                Game1.playSound("wand");
                Game1.drawObjectDialogue(ModEntry.T("airship.region2.rogue.event.mirror"));
                break;

            case Region2NodeKind.ArchiveEvent:
                this.UnbankedScrap += 2;
                if (Game1.player.health < Game1.player.maxHealth / 2)
                {
                    int heal = Math.Min(8, Game1.player.maxHealth - Game1.player.health);
                    Game1.player.health += Math.Max(0, heal);
                    if (heal > 0) this.RecoveryRecord++;
                }
                Game1.playSound("pageTurn");
                Game1.drawObjectDialogue(ModEntry.T("airship.region2.rogue.event.archive"));
                break;

            case Region2NodeKind.Cache:
                this.UnbankedScrap += 4;
                if (unchecked(this.RunSeed + this.CurrentNode * 17) % 4 == 0)
                    this.UnbankedShiny++;
                Game1.playSound("openChest");
                Game1.drawObjectDialogue(ModEntry.T("airship.region2.rogue.event.cache"));
                break;

            case Region2NodeKind.Restoration:
                int before = Game1.player.health;
                Game1.player.health = Math.Min(Game1.player.maxHealth, Game1.player.health + 18);
                if (Game1.player.health > before)
                    this.RecoveryRecord++;
                this.UnbankedScrap += 1;
                Game1.playSound("healSound");
                Game1.drawObjectDialogue(ModEntry.T("airship.region2.rogue.event.restoration"));
                break;
        }
    }

    private void PrepareRoomInteraction(GameLocation location, Region2NodeKind kind)
    {
        this.AwaitingRoomInteraction = true;
        this.ActiveInteractionTile = ResolveInteractionTile(kind, this.CurrentRoom);
        if (kind is Region2NodeKind.Cache or Region2NodeKind.FinalCache)
            this.EnsureInteractionChest(location, this.ActiveInteractionTile);

        Game1.showGlobalMessage(ModEntry.T("airship.region2.interaction.ready", new
        {
            node = this.CurrentNode,
            total = this.TargetNodes,
            target = this.InteractionDisplayName(kind)
        }));
    }

    private bool TryHandleRoomInteraction(ButtonPressedEventArgs e, GameLocation location, Point actionTile)
    {
        if (!this.AwaitingRoomInteraction)
            return false;

        Point cursorTile = new((int)e.Cursor.GrabTile.X, (int)e.Cursor.GrabTile.Y);
        bool mouseDirect = e.Button == SButton.MouseRight && Touches(cursorTile, this.ActiveInteractionTile);
        if (!Touches(actionTile, this.ActiveInteractionTile) && !mouseDirect)
            return false;

        this.ResolveRoomInteraction(location, debug: false);
        return true;
    }

    private void ResolveRoomInteraction(GameLocation location, bool debug)
    {
        if (!this.AwaitingRoomInteraction)
            return;

        Region2NodeKind kind = this.CurrentKind;
        this.AwaitingRoomInteraction = false;

        if (kind is Region2NodeKind.Cache or Region2NodeKind.FinalCache)
        {
            this.ClearInteractionObject(location);
            Game1.playSound("openBox");
        }

        if (kind == Region2NodeKind.CursedArchive)
        {
            Game1.playSound("wand");
            this.SpawnNodeEnemies(location, kind);
            this.NodeSpawned = true;
            this.ArmRoomMechanicForCombat(location);
            Game1.drawObjectDialogue(ModEntry.T("airship.region2.interaction.cursed_awakened"));
            return;
        }

        if (kind == Region2NodeKind.FinalCache)
        {
            this.AwardNode(kind);
            this.RouteComplete = true;
            Game1.playSound("discoverMineral");
            Game1.drawObjectDialogue(ModEntry.T("airship.region2.interaction.final_opened", new
            {
                scrap = this.UnbankedScrap,
                shiny = this.UnbankedShiny
            }));
            return;
        }

        this.ResolveNonCombatNode(kind);
        this.CompleteCurrentNode(location);
    }

    private string DebugResolveRoomInteraction()
    {
        if (!Context.IsWorldReady || !this.AwaitingRoomInteraction || Game1.currentLocation is null)
            return "No pending Region II room interaction.";

        Region2NodeKind kind = this.CurrentKind;
        this.ResolveRoomInteraction(Game1.currentLocation, debug: true);
        if (kind == Region2NodeKind.CursedArchive && this.NodeSpawned)
        {
            int removed = 0;
            for (int i = Game1.currentLocation.characters.Count - 1; i >= 0; i--)
            {
                if (Game1.currentLocation.characters[i] is Monster monster && monster.modData.ContainsKey(NodeMarkerKey))
                {
                    monster.Health = 0;
                    Game1.currentLocation.characters.RemoveAt(i);
                    removed++;
                }
            }
            return $"TEST: activated Cursed Archive and cleared {removed} awakened enemy/enemies; completion resolves next tick.";
        }
        return $"TEST: resolved Region II interaction node {this.CurrentNode}/{this.TargetNodes} ({kind}).";
    }

    private void EnsureInteractionChest(GameLocation room, Point tile)
    {
        Vector2 key = new(tile.X, tile.Y);
        if (room.Objects.TryGetValue(key, out StardewValley.Object? existing))
        {
            if (existing is Chest && existing.modData.ContainsKey(InteractionMarkerKey))
                return;
            this.Monitor.Log($"0683 Region II interaction chest tile {tile} is occupied; node remains interactable by tile.", LogLevel.Warn);
            return;
        }

        Chest chest = new(true);
        chest.modData[InteractionMarkerKey] = $"0683:{this.CurrentNode}:{this.CurrentKind}";
        room.setObject(key, chest);
    }

    private void ClearInteractionObject(GameLocation? room)
    {
        if (room is null)
            return;
        Point tile = ResolveCacheTile(ResolveRoom(room));
        Vector2 key = new(tile.X, tile.Y);
        if (room.Objects.TryGetValue(key, out StardewValley.Object? existing)
            && existing.modData.ContainsKey(InteractionMarkerKey))
            room.Objects.Remove(key);
    }

    private static bool IsManualInteractionKind(Region2NodeKind kind)
        => kind is Region2NodeKind.MirrorChoice or Region2NodeKind.ArchiveEvent or Region2NodeKind.Cache or Region2NodeKind.Restoration;

    private static Point ResolveInteractionTile(Region2NodeKind kind, Region2RoomKind room)
    {
        if (kind is Region2NodeKind.Cache or Region2NodeKind.FinalCache)
            return ResolveCacheTile(room);
        if (kind == Region2NodeKind.CursedArchive)
            return new Point(20, 12);
        if (kind == Region2NodeKind.MirrorChoice)
            return new Point(20, 11);
        if (kind == Region2NodeKind.Restoration)
            return room == Region2RoomKind.MirrorGallery ? new Point(9, 18) : new Point(30, 18);
        if (kind == Region2NodeKind.ArchiveEvent)
            return room == Region2RoomKind.MirrorGallery ? new Point(30, 18) : new Point(9, 11);
        return new Point(20, 14);
    }

    private static Point ResolveCacheTile(Region2RoomKind room) => room switch
    {
        Region2RoomKind.WardenVault => new Point(20, 16),
        Region2RoomKind.MirrorGallery => new Point(20, 17),
        Region2RoomKind.InkboundStacks => new Point(20, 17),
        _ => new Point(20, 16),
    };

    private string InteractionDisplayName(Region2NodeKind kind)
        => ModEntry.T($"airship.region2.interaction.object.{InteractionKey(kind)}");

    private static string InteractionKey(Region2NodeKind kind) => kind switch
    {
        Region2NodeKind.MirrorChoice => "mirror",
        Region2NodeKind.ArchiveEvent => "lectern",
        Region2NodeKind.Cache => "cache",
        Region2NodeKind.Restoration => "restoration",
        Region2NodeKind.CursedArchive => "cursed",
        Region2NodeKind.FinalCache => "finalcache",
        _ => "archive",
    };

    private static bool Touches(Point a, Point b)
        => Math.Abs(a.X - b.X) <= 1 && Math.Abs(a.Y - b.Y) <= 1;

    private void SpawnNodeEnemies(GameLocation location, Region2NodeKind kind)
    {
        this.ClearRunEnemies(location);
        Point[] candidates = SpawnCandidatesForRoom(this.CurrentRoom);
        Random random = new(unchecked(this.RunSeed + this.CurrentNode * 65537 + (int)kind * 7919));
        Point[] shuffled = candidates.OrderBy(_ => random.Next()).ToArray();

        int targetCount = kind switch
        {
            Region2NodeKind.Ambush => 6 + this.CurrentNode / 3,
            Region2NodeKind.Elite => 4 + this.CurrentNode / 4,
            Region2NodeKind.CursedArchive => 6 + this.CurrentNode / 2,
            _ => 4 + this.CurrentNode / 3,
        };

        int spawned = 0;
        foreach (Point tile in shuffled)
        {
            if (spawned >= targetCount)
                break;
            Vector2 tv = new(tile.X, tile.Y);
            try
            {
                if (location.IsTileBlockedBy(tv) || location.Objects.ContainsKey(tv))
                    continue;
            }
            catch
            {
                continue;
            }

            bool forceElite = kind == Region2NodeKind.Elite && spawned == 0;
            Monster enemy = this.CreateEnemy(kind, spawned, tv * 64f, forceElite);
            enemy.modData[RegionExpeditionService.EnemyMarkerKey] = $"0680:2:{this.CurrentNode}:{kind}";
            enemy.modData[NodeMarkerKey] = this.CurrentNode.ToString();
            location.characters.Add(enemy);
            spawned++;
        }

        this.LastEncounterMix = DescribeEncounterMix(location);
        Game1.playSound(kind == Region2NodeKind.Ambush ? "batScreech" : "wand");
        this.Monitor.Log($"0685 Region II node {this.CurrentNode}/{this.TargetNodes} {kind}: modifier={this.ActiveRunModifier}, spawned={spawned}, mix={this.LastEncounterMix}.", LogLevel.Trace);
    }

    private Monster CreateEnemy(Region2NodeKind kind, int index, Vector2 position, bool forceElite)
    {
        int depth = Math.Max(1, this.CurrentNode);
        float hpScale = 1f + (depth - 1) * 0.055f + this.RiskRecord * 0.025f;
        Monster monster;
        string role;
        int baseHp;
        int speed;

        if (forceElite)
        {
            monster = new GreenSlime(position, 0);
            role = "archive_warden";
            baseHp = 390 + depth * 24;
            speed = 3;
        }
        else
        {
            int archetype = this.ResolveEncounterArchetype(kind, index, depth);
            if (archetype == 0)
            {
                monster = new Bat(position);
                role = "ink_moth";
                baseHp = 105 + depth * 9;
                speed = kind == Region2NodeKind.Ambush ? 5 : 4;
            }
            else if (archetype == 1)
            {
                monster = new Bug(position, 0);
                role = "paper_scarab";
                baseHp = 145 + depth * 12;
                speed = 3;
            }
            else
            {
                monster = new GreenSlime(position, 0);
                role = "dust_slime";
                baseHp = 190 + depth * 15;
                speed = 2;
            }
        }

        if (kind == Region2NodeKind.CursedArchive)
        {
            hpScale += 0.18f;
            speed += 1;
        }

        this.ApplyRunModifierEnemyStats(ref hpScale, ref speed);

        int hp = Math.Max(1, (int)Math.Round(baseHp * hpScale));
        monster.MaxHealth = hp;
        monster.Health = hp;
        monster.Speed = speed;
        monster.modData[RegionExpeditionService.EnemyRoleKey] = role;
        return monster;
    }

    private static Region2RunModifier PickRunModifier(Random random)
        => (Region2RunModifier)random.Next(Enum.GetValues<Region2RunModifier>().Length);

    private int ResolveEncounterArchetype(Region2NodeKind kind, int index, int depth)
    {
        int salt = unchecked(this.RunSeed + depth * 4099 + index * 8191 + (int)kind * 131);
        int roll = (int)((uint)salt % 100u);
        return this.ActiveRunModifier switch
        {
            Region2RunModifier.LooseFolios => roll < 58 ? 0 : roll < 84 ? 1 : 2,
            Region2RunModifier.IronBindings => roll < 15 ? 0 : roll < 45 ? 1 : 2,
            Region2RunModifier.MirrorDraft => roll % 3,
            Region2RunModifier.RedactedLedger => roll < 25 ? 0 : roll < 75 ? 1 : 2,
            _ => roll % 3,
        };
    }

    private void ApplyRunModifierEnemyStats(ref float hpScale, ref int speed)
    {
        switch (this.ActiveRunModifier)
        {
            case Region2RunModifier.LooseFolios:
                hpScale *= 0.88f;
                speed += 1;
                break;
            case Region2RunModifier.IronBindings:
                hpScale *= 1.18f;
                speed = Math.Max(1, speed - 1);
                break;
            case Region2RunModifier.RedactedLedger:
                hpScale *= 1.05f;
                break;
        }
    }

    private string RunModifierDisplayName()
        => ModEntry.T($"airship.region2.modifier.{RunModifierKey(this.ActiveRunModifier)}.name");

    private string RunModifierEffectText()
        => ModEntry.T($"airship.region2.modifier.{RunModifierKey(this.ActiveRunModifier)}.effect");

    private static string RunModifierKey(Region2RunModifier modifier) => modifier switch
    {
        Region2RunModifier.LooseFolios => "loose_folios",
        Region2RunModifier.IronBindings => "iron_bindings",
        Region2RunModifier.MirrorDraft => "mirror_draft",
        Region2RunModifier.RedactedLedger => "redacted_ledger",
        _ => "mirror_draft",
    };

    private static string DescribeEncounterMix(GameLocation location)
    {
        string[] roles = { "ink_moth", "paper_scarab", "dust_slime", "archive_warden" };
        List<string> parts = new();
        foreach (string role in roles)
        {
            int count = location.characters.OfType<Monster>().Count(m =>
                m.Health > 0
                && m.modData.ContainsKey(NodeMarkerKey)
                && m.modData.TryGetValue(RegionExpeditionService.EnemyRoleKey, out string? value)
                && value.Equals(role, StringComparison.OrdinalIgnoreCase));
            if (count > 0)
                parts.Add($"{role}:{count}");
        }
        return parts.Count == 0 ? "none" : string.Join(",", parts);
    }

    private void ArmRoomMechanicForCombat(GameLocation location)
    {
        this.ResetRoomMechanicState();
        this.ActiveRoomMechanic = this.CurrentRoom switch
        {
            Region2RoomKind.MirrorGallery => "mirror_trace",
            Region2RoomKind.InkboundStacks => "ink_sweep",
            Region2RoomKind.WardenVault when this.CurrentKind == Region2NodeKind.Elite => "warden_seal",
            _ => "none",
        };
        if (this.ActiveRoomMechanic == "none")
            return;

        this.RoomMechanicNextAtMs = Environment.TickCount64 + 2200L;
        Game1.showGlobalMessage(ModEntry.T("airship.region2.mechanic.active", new
        {
            mechanic = ModEntry.T($"airship.region2.mechanic.{this.ActiveRoomMechanic}.name")
        }));
    }

    private void UpdateRoomMechanic(GameLocation location)
    {
        if (this.ActiveRoomMechanic == "none")
            return;
        if (CountRunEnemies(location) <= 0)
        {
            this.ClearRoomMechanicTelegraph();
            return;
        }

        long now = Environment.TickCount64;
        if (this.RoomMechanicResolveAtMs > 0)
        {
            if (now < this.RoomMechanicResolveAtMs)
                return;
            this.ResolveRoomMechanicHit();
            this.ClearRoomMechanicTelegraph();
            this.RoomMechanicNextAtMs = now + RoomMechanicCooldownMs(this.ActiveRoomMechanic, this.CurrentNode);
            return;
        }

        if (now < this.RoomMechanicNextAtMs)
            return;
        if (!this.TryArmRoomMechanicTelegraph(location, now))
            this.RoomMechanicNextAtMs = now + 700L;
    }

    private bool TryArmRoomMechanicTelegraph(GameLocation location, long now)
    {
        Point player = PlayerTile();
        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 40;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 28;

        switch (this.ActiveRoomMechanic)
        {
            case "mirror_trace":
                Point origin = ClampArenaTile(player, width, height);
                Point reflected = ClampArenaTile(new Point(width - 1 - origin.X, origin.Y), width, height);
                this.RoomMechanicTiles = BuildSquareZone(origin, 1, width, height)
                    .Concat(BuildSquareZone(reflected, 1, width, height))
                    .Distinct()
                    .ToArray();
                this.RoomMechanicResolveAtMs = now + MirrorTelegraphMs;
                Game1.playSound("wand");
                break;

            case "ink_sweep":
                int row = Math.Clamp(player.Y, 4, Math.Max(4, height - 5));
                this.RoomMechanicTiles = Enumerable.Range(4, Math.Max(1, width - 8))
                    .Select(x => new Point(x, row))
                    .ToArray();
                this.RoomMechanicResolveAtMs = now + InkTelegraphMs;
                Game1.playSound("batScreech");
                break;

            case "warden_seal":
                Monster? warden = location.characters.OfType<Monster>().FirstOrDefault(m =>
                    m.Health > 0
                    && m.modData.TryGetValue(RegionExpeditionService.EnemyRoleKey, out string? role)
                    && role.Equals("archive_warden", StringComparison.OrdinalIgnoreCase));
                if (warden is null)
                    return false;
                Point center = ClampArenaTile(new Point((int)(warden.Position.X / 64f), (int)(warden.Position.Y / 64f)), width, height);
                this.RoomMechanicTiles = BuildSquareZone(center, 2, width, height)
                    .Where(p => p != center)
                    .ToArray();
                this.RoomMechanicResolveAtMs = now + VaultTelegraphMs;
                Game1.playSound("discoverMineral");
                break;

            default:
                return false;
        }

        this.RoomMechanicCycles++;
        return this.RoomMechanicTiles.Length > 0;
    }

    private void ResolveRoomMechanicHit()
    {
        if (this.RoomMechanicTiles.Length == 0)
            return;
        Point player = PlayerTile();
        if (!this.RoomMechanicTiles.Contains(player))
            return;

        int damage = this.ActiveRoomMechanic switch
        {
            "mirror_trace" => 8 + this.CurrentNode / 4,
            "ink_sweep" => 7 + this.CurrentNode / 4,
            "warden_seal" => 10 + this.CurrentNode / 3,
            _ => 0,
        };
        if (damage <= 0)
            return;

        this.RoomMechanicHits++;
        // Use the native Farmer damage pipeline so Cardcha defensive/revive effects remain authoritative.
        Game1.player.takeDamage(damage, false, null);
    }

    private void ResetRoomMechanicState()
    {
        this.ActiveRoomMechanic = "none";
        this.RoomMechanicNextAtMs = 0L;
        this.RoomMechanicResolveAtMs = 0L;
        this.RoomMechanicTiles = Array.Empty<Point>();
        this.RoomMechanicCycles = 0;
        this.RoomMechanicHits = 0;
    }

    private void ClearRoomMechanicTelegraph()
    {
        this.RoomMechanicResolveAtMs = 0L;
        this.RoomMechanicTiles = Array.Empty<Point>();
    }

    private static long RoomMechanicCooldownMs(string tag, int node)
    {
        int depthCut = Math.Min(900, Math.Max(0, node - 1) * 90);
        int baseline = tag switch
        {
            "mirror_trace" => 4500,
            "ink_sweep" => 4800,
            "warden_seal" => 4200,
            _ => 5000,
        };
        return Math.Max(3000, baseline - depthCut);
    }

    private static Point ClampArenaTile(Point tile, int width, int height)
        => new(Math.Clamp(tile.X, 2, Math.Max(2, width - 3)), Math.Clamp(tile.Y, 3, Math.Max(3, height - 4)));

    private static IEnumerable<Point> BuildSquareZone(Point center, int radius, int width, int height)
    {
        for (int y = center.Y - radius; y <= center.Y + radius; y++)
        for (int x = center.X - radius; x <= center.X + radius; x++)
        {
            if (x >= 1 && x < width - 1 && y >= 2 && y < height - 2)
                yield return new Point(x, y);
        }
    }

    private static void DrawHazardOutline(SpriteBatch batch, Point tile, Color color)
    {
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, new Vector2(tile.X * 64f, tile.Y * 64f));
        Rectangle r = new((int)local.X + 7, (int)local.Y + 7, 50, 50);
        const int edge = 4;
        batch.Draw(Game1.staminaRect, new Rectangle(r.X, r.Y, r.Width, edge), color);
        batch.Draw(Game1.staminaRect, new Rectangle(r.X, r.Bottom - edge, r.Width, edge), color);
        batch.Draw(Game1.staminaRect, new Rectangle(r.X, r.Y, edge, r.Height), color);
        batch.Draw(Game1.staminaRect, new Rectangle(r.Right - edge, r.Y, edge, r.Height), color);
    }

    private void UpdateCombatRecord()
    {
        int endHealth = Math.Max(0, Game1.player.health);
        int maxHealth = Math.Max(1, Game1.player.maxHealth);
        if (endHealth >= this.NodeStartHealth)
            this.PrecisionRecord++;
        if (this.NodeStartHealth - endHealth >= Math.Max(8, maxHealth / 5))
            this.PressureRecord++;
    }

    private void AwardNode(Region2NodeKind kind)
    {
        int scrap = kind switch
        {
            Region2NodeKind.Combat => 4,
            Region2NodeKind.Ambush => 5,
            Region2NodeKind.Elite => 7,
            Region2NodeKind.CursedArchive => 8,
            Region2NodeKind.FinalCache => 5,
            _ => 0,
        };
        int shiny = kind switch
        {
            Region2NodeKind.Elite => unchecked(this.RunSeed + this.CurrentNode * 31) % 3 == 0 ? 1 : 0,
            Region2NodeKind.CursedArchive => unchecked(this.RunSeed + this.CurrentNode * 43) % 2 == 0 ? 1 : 0,
            Region2NodeKind.FinalCache => 1,
            _ => 0,
        };
        this.UnbankedScrap += scrap;
        this.UnbankedShiny += shiny;
    }

    private void BankCheckpoint()
    {
        if (this.UnbankedScrap <= 0 && this.UnbankedShiny <= 0)
            return;
        int scrap = Math.Max(0, this.UnbankedScrap);
        int shiny = Math.Max(0, this.UnbankedShiny);
        this.Save.Data.CardboardScraps += scrap;
        this.Save.Data.ShinyScraps += shiny;
        this.Save.Save();
        this.TotalBankedScrap += scrap;
        this.TotalBankedShiny += shiny;
        this.UnbankedScrap = 0;
        this.UnbankedShiny = 0;
        Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.checkpoint", new { node = this.CurrentNode, scrap, shiny }));
    }

    private void BankAllRemaining()
    {
        if (this.UnbankedScrap <= 0 && this.UnbankedShiny <= 0)
            return;
        int scrap = Math.Max(0, this.UnbankedScrap);
        int shiny = Math.Max(0, this.UnbankedShiny);
        this.Save.Data.CardboardScraps += scrap;
        this.Save.Data.ShinyScraps += shiny;
        this.Save.Save();
        this.TotalBankedScrap += scrap;
        this.TotalBankedShiny += shiny;
        this.UnbankedScrap = 0;
        this.UnbankedShiny = 0;
    }

    private void TryUseBossGate()
    {
        if (!this.BossGateReady)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.region2.rogue.bossgate_not_ready", new { node = this.CurrentNode }));
            return;
        }

        bool debug = this.LastCuratorRecord == "debug";
        if (!debug)
        {
            if (!this.Save.Data.Region1BossDefeated)
            {
                Game1.drawObjectDialogue(ModEntry.T("airship.region2.boss_gate.boss1"));
                return;
            }
            int owned = this.Save.Data.OwnedCards?.Count ?? 0;
            if (owned < 40)
            {
                Game1.drawObjectDialogue(ModEntry.T("airship.region2.boss_gate.cards", new { cards = owned }));
                return;
            }
            if (this.Save.Data.BossCardsUnlocked?.Contains(MilestoneBossService.MirrorArchiveBossCardId) == true)
            {
                Game1.drawObjectDialogue(ModEntry.T("airship.region2.boss_gate.cleared"));
                return;
            }
        }

        Func<string>? handler = debug ? this.BossGateDebugAction : this.BossGateAction;
        if (handler is null)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.expedition.unavailable"));
            return;
        }

        CuratorRunRecord record = this.BuildCuratorRunRecord(debug);
        this.CuratorArchiveRuleSink?.Invoke(RunModifierKey(this.ActiveRunModifier));
        this.CuratorRecordSink?.Invoke(record);
        this.BankAllRemaining();
        this.LeavingForBoss = true;
        string result = handler();
        if (!string.IsNullOrWhiteSpace(result))
        {
            this.LeavingForBoss = false;
            Game1.drawObjectDialogue(result);
            return;
        }
        this.LastCuratorRecord = record.Tag;
        this.Active = false;
        this.Monitor.Log($"0686 Region II -> Hollow Curator. Transferred {record.Describe()} + ArchiveRule={RunModifierKey(this.ActiveRunModifier)}.", LogLevel.Info);
    }

    private void TryExtract()
    {
        long now = Environment.TickCount64;
        if (this.ExtractConfirmUntilMs <= now)
        {
            this.ExtractConfirmUntilMs = now + ExtractConfirmWindowMs;
            if (this.RouteComplete)
            {
                Game1.drawObjectDialogue(ModEntry.T("airship.region2.rogue.extract_complete", new
                {
                    scrap = this.UnbankedScrap,
                    shiny = this.UnbankedShiny
                }));
            }
            else
            {
                Game1.drawObjectDialogue(ModEntry.T("airship.region2.rogue.extract_early", new
                {
                    node = this.CurrentNode,
                    total = this.TargetNodes,
                    scrap = this.UnbankedScrap,
                    shiny = this.UnbankedShiny
                }));
            }
            return;
        }

        this.ExtractConfirmUntilMs = 0;
        if (this.RouteComplete)
            this.BankAllRemaining();
        else
        {
            this.UnbankedScrap = 0;
            this.UnbankedShiny = 0;
        }
        this.ClearRunEnemies(Game1.currentLocation!);
        this.Active = false;
        this.Airship.StartExternalRegionReturnFlight();
    }

    private bool CanChallengeBoss()
    {
        if (!this.Save.Data.Region1BossDefeated)
            return false;
        if ((this.Save.Data.OwnedCards?.Count ?? 0) < 40)
            return false;
        return this.Save.Data.BossCardsUnlocked?.Contains(MilestoneBossService.MirrorArchiveBossCardId) != true;
    }

    private CuratorRunRecord BuildCuratorRunRecord(bool debug)
    {
        if (debug)
            return CuratorRunRecord.Debug("neutral");
        return new CuratorRunRecord(
            this.CurrentRecordTag(),
            this.RiskRecord,
            this.PrecisionRecord,
            this.PressureRecord,
            this.RecoveryRecord,
            this.MirrorRecord,
            this.CurrentNode
        );
    }

    private string CurrentRecordTag()
    {
        (string tag, int value)[] records =
        {
            ("risk", this.RiskRecord),
            ("precision", this.PrecisionRecord),
            ("pressure", this.PressureRecord),
            ("recovery", this.RecoveryRecord),
            ("mirror", this.MirrorRecord),
        };
        int max = records.Max(p => p.value);
        if (max <= 0)
            return "neutral";
        return records.First(p => p.value == max).tag;
    }

    private string RecordDisplayName(string tag)
        => ModEntry.T($"airship.region2.rogue.record.{tag}");

    private string NodeDisplayName(Region2NodeKind kind)
        => ModEntry.T($"airship.region2.rogue.kind.{KindKey(kind)}");

    private string RouteChoiceLabel(Region2NodeKind kind)
        => ModEntry.T("airship.region2.rogue.route_label", new
        {
            kind = this.NodeDisplayName(kind),
            risk = IsRiskKind(kind) ? ModEntry.T("airship.region2.rogue.risk_high") : ModEntry.T("airship.region2.rogue.risk_normal")
        });

    private static string KindKey(Region2NodeKind kind)
        => kind switch
        {
            Region2NodeKind.Combat => "combat",
            Region2NodeKind.Ambush => "ambush",
            Region2NodeKind.Elite => "elite",
            Region2NodeKind.MirrorChoice => "mirror",
            Region2NodeKind.ArchiveEvent => "event",
            Region2NodeKind.Cache => "cache",
            Region2NodeKind.Restoration => "restoration",
            Region2NodeKind.CursedArchive => "cursed",
            Region2NodeKind.BossGate => "bossgate",
            _ => "finalcache",
        };

    private static bool IsCombatKind(Region2NodeKind kind)
        => kind is Region2NodeKind.Combat or Region2NodeKind.Ambush or Region2NodeKind.Elite or Region2NodeKind.CursedArchive;

    private static bool IsRiskKind(Region2NodeKind kind)
        => kind is Region2NodeKind.Elite or Region2NodeKind.CursedArchive or Region2NodeKind.BossGate;

    internal static bool IsRegion2(GameLocation? location)
        => location is not null && IsRegion2Name(location.NameOrUniqueName);

    internal static bool IsRegion2Name(string? name)
        => !string.IsNullOrWhiteSpace(name) && (
            name.Equals(RegionExpeditionService.Region2LocationName, StringComparison.OrdinalIgnoreCase)
            || name.Equals(InkboundStacksLocationName, StringComparison.OrdinalIgnoreCase)
            || name.Equals(MirrorGalleryLocationName, StringComparison.OrdinalIgnoreCase)
            || name.Equals(WardenVaultLocationName, StringComparison.OrdinalIgnoreCase));

    private Region2RoomKind ResolveRoomForNode(Region2NodeKind kind)
    {
        if (kind is Region2NodeKind.BossGate or Region2NodeKind.Elite or Region2NodeKind.FinalCache)
            return Region2RoomKind.WardenVault;
        if (kind == Region2NodeKind.MirrorChoice)
            return Region2RoomKind.MirrorGallery;
        if (kind is Region2NodeKind.Ambush or Region2NodeKind.CursedArchive)
            return Region2RoomKind.InkboundStacks;
        if (kind == Region2NodeKind.Restoration)
            return this.CurrentNode >= 5 ? Region2RoomKind.MirrorGallery : Region2RoomKind.Vestibule;
        if (kind == Region2NodeKind.Cache)
            return ((this.RunSeed + this.CurrentNode) & 1) == 0 ? Region2RoomKind.MirrorGallery : Region2RoomKind.InkboundStacks;
        if (kind == Region2NodeKind.ArchiveEvent)
            return this.CurrentNode <= 3 ? Region2RoomKind.Vestibule : Region2RoomKind.MirrorGallery;
        return (this.CurrentNode % 3) switch
        {
            0 => Region2RoomKind.MirrorGallery,
            1 => Region2RoomKind.Vestibule,
            _ => Region2RoomKind.InkboundStacks,
        };
    }

    private static string RoomLocationName(Region2RoomKind room) => room switch
    {
        Region2RoomKind.InkboundStacks => InkboundStacksLocationName,
        Region2RoomKind.MirrorGallery => MirrorGalleryLocationName,
        Region2RoomKind.WardenVault => WardenVaultLocationName,
        _ => RegionExpeditionService.Region2LocationName,
    };

    private static string RoomMapAssetName(Region2RoomKind room) => room switch
    {
        Region2RoomKind.InkboundStacks => InkboundStacksMapAssetName,
        Region2RoomKind.MirrorGallery => MirrorGalleryMapAssetName,
        Region2RoomKind.WardenVault => WardenVaultMapAssetName,
        _ => RegionExpeditionService.Region2MapAssetName,
    };

    private static Point RoomArrivalTile(Region2RoomKind room)
        => room == Region2RoomKind.WardenVault ? new Point(20, 23) : new Point(20, 24);

    private static string[] Region2RoomNames()
        => new[] { RegionExpeditionService.Region2LocationName, InkboundStacksLocationName, MirrorGalleryLocationName, WardenVaultLocationName };

    private void EnsureRoomLocations()
    {
        foreach (Region2RoomKind room in Enum.GetValues<Region2RoomKind>())
            this.EnsureRoomLocation(room);
    }

    private GameLocation? EnsureRoomLocation(Region2RoomKind room)
    {
        string name = RoomLocationName(room);
        GameLocation? existing = Game1.getLocationFromName(name);
        if (existing is not null) return existing;
        try
        {
            GameLocation created = new(RoomMapAssetName(room), name);
            Game1.locations.Add(created);
            return created;
        }
        catch (Exception ex)
        {
            this.Monitor.Log($"0683 couldn't create Region II room {room}: {ex.GetType().Name}: {ex.Message}", LogLevel.Error);
            return null;
        }
    }

    private static Region2RoomKind ResolveRoom(GameLocation? location)
    {
        string? name = location?.NameOrUniqueName;
        if (name?.Equals(InkboundStacksLocationName, StringComparison.OrdinalIgnoreCase) == true) return Region2RoomKind.InkboundStacks;
        if (name?.Equals(MirrorGalleryLocationName, StringComparison.OrdinalIgnoreCase) == true) return Region2RoomKind.MirrorGallery;
        if (name?.Equals(WardenVaultLocationName, StringComparison.OrdinalIgnoreCase) == true) return Region2RoomKind.WardenVault;
        return Region2RoomKind.Vestibule;
    }

    private static Point[] SpawnCandidatesForRoom(Region2RoomKind room) => room switch
    {
        Region2RoomKind.InkboundStacks => new[]
        {
            new Point(5,5), new Point(13,5), new Point(27,5), new Point(35,5), new Point(7,10), new Point(16,10),
            new Point(24,10), new Point(33,10), new Point(6,15), new Point(14,15), new Point(26,15), new Point(34,15),
            new Point(9,20), new Point(17,20), new Point(23,20), new Point(31,20)
        },
        Region2RoomKind.MirrorGallery => new[]
        {
            new Point(8,6), new Point(14,6), new Point(20,7), new Point(26,6), new Point(32,6), new Point(10,11),
            new Point(16,12), new Point(24,12), new Point(30,11), new Point(8,17), new Point(14,18), new Point(20,17),
            new Point(26,18), new Point(32,17), new Point(12,22), new Point(28,22)
        },
        Region2RoomKind.WardenVault => new[]
        {
            new Point(10,8), new Point(15,8), new Point(25,8), new Point(30,8), new Point(9,13), new Point(15,13),
            new Point(25,13), new Point(31,13), new Point(10,18), new Point(16,18), new Point(24,18), new Point(30,18)
        },
        _ => new[]
        {
            new Point(6,5), new Point(11,5), new Point(18,5), new Point(22,5), new Point(29,5), new Point(34,5),
            new Point(7,10), new Point(13,10), new Point(20,9), new Point(27,10), new Point(33,10),
            new Point(6,16), new Point(12,17), new Point(18,15), new Point(22,15), new Point(28,17), new Point(34,16),
            new Point(9,22), new Point(15,21), new Point(25,21), new Point(31,22)
        }
    };

    private static Point PlayerTile()
        => new((int)(Game1.player.Position.X / 64f), (int)(Game1.player.Position.Y / 64f));

    private static Point ResolveExtractionTile(GameLocation location)
    {
        int width = location.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 40;
        int height = location.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 28;
        return new Point(width / 2, Math.Max(3, height - 3));
    }

    private static int CountRunEnemies(GameLocation location)
        => location.characters.OfType<Monster>().Count(m => m.Health > 0 && m.modData.ContainsKey(NodeMarkerKey));

    private void ClearRunEnemies(GameLocation location)
    {
        for (int i = location.characters.Count - 1; i >= 0; i--)
        {
            if (location.characters[i] is Monster monster
                && (monster.modData.ContainsKey(NodeMarkerKey)
                    || monster.modData.TryGetValue(RegionExpeditionService.EnemyMarkerKey, out string? marker)
                    && marker.StartsWith("0679:", StringComparison.OrdinalIgnoreCase)))
            {
                location.characters.RemoveAt(i);
            }
        }
    }

    private void ResetRuntime(bool clearEnemies)
    {
        if (clearEnemies && Context.IsWorldReady)
        {
            foreach (string name in Region2RoomNames())
            {
                GameLocation? room = Game1.getLocationFromName(name);
                if (room is not null)
                {
                    this.ClearRunEnemies(room);
                    this.ClearInteractionObject(room);
                }
            }
        }
        this.Active = false;
        this.LeavingForBoss = false;
        this.RouteComplete = false;
        this.BossGateReady = false;
        this.ChoicePending = false;
        this.ChoiceDeferred = false;
        this.NodeSpawned = false;
        this.ResetRoomMechanicState();
        this.AwaitingRoomInteraction = false;
        this.ActiveInteractionTile = Point.Zero;
        this.PendingInternalRoomWarp = false;
        this.CurrentRoom = Region2RoomKind.Vestibule;
        this.CurrentNode = 0;
        this.TargetNodes = 0;
        this.ActiveRunModifier = Region2RunModifier.MirrorDraft;
        this.LastEncounterMix = "none";
        this.UnbankedScrap = 0;
        this.UnbankedShiny = 0;
        this.ExtractConfirmUntilMs = 0;
    }
}
