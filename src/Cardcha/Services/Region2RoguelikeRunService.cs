using Microsoft.Xna.Framework;
using StardewModdingAPI;
using StardewModdingAPI.Events;
using StardewValley;
using StardewValley.Monsters;

namespace Cardcha.Services;

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
    private const long ExtractConfirmWindowMs = 5000L;
    private static readonly Point BossGateTile = new(20, 4);

    private readonly IModHelper Helper;
    private readonly IMonitor Monitor;
    private readonly SaveService Save;
    private readonly AirshipFoundationService Airship;
    private readonly RegionExpeditionService LegacyExpeditions;

    private Func<string>? BossGateAction;
    private Func<string>? BossGateDebugAction;

    private bool Active;
    private bool LeavingForBoss;
    private bool RouteComplete;
    private bool BossGateReady;
    private bool ChoicePending;
    private bool DebugBossGateEntry;
    private bool NodeSpawned;
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

    public void OnSaveLoaded(object? sender, SaveLoadedEventArgs e) => this.ResetRuntime(clearEnemies: true);
    public void OnDayStarted(object? sender, DayStartedEventArgs e) => this.ResetRuntime(clearEnemies: true);
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

        if (incoming)
        {
            // The legacy service still owns the Airship route and permission gate. Once that warp
            // succeeds, 0680 takes runtime ownership and cancels the old three-wave state.
            this.LegacyExpeditions.SuspendLegacyRegion2RuntimeForRoguelike();
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
        if (this.RouteComplete || this.BossGateReady || this.ChoicePending)
            return;
        if (!IsCombatKind(this.CurrentKind) || !this.NodeSpawned)
            return;
        if (CountRunEnemies(Game1.currentLocation) > 0)
            return;

        this.NodeSpawned = false;
        this.CompleteCurrentNode(Game1.currentLocation);
    }

    public void OnButtonPressed(object? sender, ButtonPressedEventArgs e)
    {
        if (!Context.IsWorldReady || !this.Active || !e.Button.IsActionButton()
            || Game1.currentLocation is null || !IsRegion2(Game1.currentLocation)
            || Game1.activeClickableMenu is not null || Game1.dialogueUp || Game1.eventUp)
            return;

        Point player = PlayerTile();
        Point action = Game1.player.GetGrabTile().ToPoint();

        bool gateClose = Math.Abs(player.X - BossGateTile.X) <= 2 && Math.Abs(player.Y - BossGateTile.Y) <= 2;
        bool gateFacing = Math.Abs(action.X - BossGateTile.X) <= 1 && Math.Abs(action.Y - BossGateTile.Y) <= 1;
        if (gateClose || gateFacing)
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
        return $"0680 Region II Rogue: active={this.Active}, node={this.CurrentNode}/{this.TargetNodes}, kind={this.CurrentKind}, "
            + $"choicePending={this.ChoicePending}, bossGate={this.BossGateReady}, complete={this.RouteComplete}, "
            + $"unbanked={this.UnbankedScrap}S/{this.UnbankedShiny}Sh, banked={this.TotalBankedScrap}S/{this.TotalBankedShiny}Sh, "
            + $"record={this.CurrentRecordTag()} [risk={this.RiskRecord}, precision={this.PrecisionRecord}, pressure={this.PressureRecord}, recovery={this.RecoveryRecord}, mirror={this.MirrorRecord}], "
            + "runLength=6-9 nodes; Boss Gate eligible from node 6 when Boss I + 40 cards are satisfied.";
    }

    private void StartRun(GameLocation location, bool debugBossGate)
    {
        this.ClearRunEnemies(location);
        this.Active = true;
        this.LeavingForBoss = false;
        this.RouteComplete = false;
        this.BossGateReady = false;
        this.ChoicePending = false;
        this.NodeSpawned = false;
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
        this.ExtractConfirmUntilMs = 0;

        int flights = Math.Max(0, this.Save.Data.AirshipFlightsTaken);
        this.RunSeed = unchecked((int)Game1.uniqueIDForThisGame + Game1.Date.TotalDays * 1009 + flights * 7919 + 0x2A80);
        Random random = new(this.RunSeed);
        this.TargetNodes = 6 + random.Next(4); // 6-9, aligned with Region I run length without copying its route logic.

        if (debugBossGate)
        {
            this.CurrentNode = 6;
            this.TargetNodes = Math.Max(6, this.TargetNodes);
            this.CurrentKind = Region2NodeKind.BossGate;
            this.BossGateReady = true;
            this.LastCuratorRecord = "debug";
            Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.debug_bossgate"));
            return;
        }

        Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.start", new { total = this.TargetNodes }));
        this.BeginNode(location, Region2NodeKind.Combat);
    }

    private void BeginNode(GameLocation location, Region2NodeKind kind)
    {
        this.CurrentKind = kind;
        this.ChoicePending = false;
        this.BossGateReady = false;
        this.NodeSpawned = false;
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

        if (kind == Region2NodeKind.FinalCache)
        {
            this.AwardNode(kind);
            this.RouteComplete = true;
            Game1.playSound("discoverMineral");
            Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.complete", new { scrap = this.UnbankedScrap, shiny = this.UnbankedShiny }));
            return;
        }

        if (IsCombatKind(kind))
        {
            this.SpawnNodeEnemies(location, kind);
            this.NodeSpawned = true;
            Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.node", new
            {
                node = this.CurrentNode,
                total = this.TargetNodes,
                kind = this.NodeDisplayName(kind)
            }));
            return;
        }

        this.ResolveNonCombatNode(kind);
        this.CompleteCurrentNode(location);
    }

    private void CompleteCurrentNode(GameLocation location)
    {
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
                this.CurrentKind = Region2NodeKind.FinalCache;
                this.AwardNode(Region2NodeKind.FinalCache);
                this.RouteComplete = true;
                Game1.playSound("discoverMineral");
                Game1.showGlobalMessage(ModEntry.T("airship.region2.rogue.complete", new { scrap = this.UnbankedScrap, shiny = this.UnbankedShiny }));
            }
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

    private static Region2NodeKind PickDeepRoute(Random random)
    {
        Region2NodeKind[] deep =
        {
            Region2NodeKind.Elite,
            Region2NodeKind.CursedArchive,
            Region2NodeKind.MirrorChoice,
            Region2NodeKind.Cache,
            Region2NodeKind.Ambush,
        };
        return deep[random.Next(deep.Length)];
    }

    private static Region2NodeKind PickRoute(Random random, Region2NodeKind previous, Region2NodeKind? exclude)
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
        return candidates[random.Next(candidates.Count)];
    }

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

    private void SpawnNodeEnemies(GameLocation location, Region2NodeKind kind)
    {
        this.ClearRunEnemies(location);
        Point[] candidates =
        {
            new(6,5), new(11,5), new(18,5), new(22,5), new(29,5), new(34,5),
            new(7,10), new(13,10), new(20,9), new(27,10), new(33,10),
            new(6,16), new(12,17), new(18,15), new(22,15), new(28,17), new(34,16),
            new(9,22), new(15,21), new(25,21), new(31,22)
        };
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

        Game1.playSound(kind == Region2NodeKind.Ambush ? "batScreech" : "wand");
        this.Monitor.Log($"0680 Region II node {this.CurrentNode}/{this.TargetNodes} {kind}: spawned={spawned}.", LogLevel.Trace);
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
            int archetype = kind == Region2NodeKind.Ambush ? 0 : (index + depth) % 3;
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

        int hp = Math.Max(1, (int)Math.Round(baseHp * hpScale));
        monster.MaxHealth = hp;
        monster.Health = hp;
        monster.Speed = speed;
        monster.modData[RegionExpeditionService.EnemyRoleKey] = role;
        return monster;
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

        this.LastCuratorRecord = debug ? "debug" : this.CurrentRecordTag();
        this.BankAllRemaining();
        this.LeavingForBoss = true;
        string result = handler();
        if (!string.IsNullOrWhiteSpace(result))
        {
            this.LeavingForBoss = false;
            Game1.drawObjectDialogue(result);
            return;
        }
        this.Active = false;
        this.Monitor.Log($"0680 Region II -> Hollow Curator. Curator record={this.LastCuratorRecord}.", LogLevel.Info);
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

    private static bool IsRegion2(GameLocation? location)
        => location?.NameOrUniqueName.Equals(RegionExpeditionService.Region2LocationName, StringComparison.OrdinalIgnoreCase) == true;

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
        if (clearEnemies && Context.IsWorldReady && IsRegion2(Game1.currentLocation) && Game1.currentLocation is not null)
            this.ClearRunEnemies(Game1.currentLocation);
        this.Active = false;
        this.LeavingForBoss = false;
        this.RouteComplete = false;
        this.BossGateReady = false;
        this.ChoicePending = false;
        this.NodeSpawned = false;
        this.CurrentNode = 0;
        this.TargetNodes = 0;
        this.UnbankedScrap = 0;
        this.UnbankedShiny = 0;
        this.ExtractConfirmUntilMs = 0;
    }
}
