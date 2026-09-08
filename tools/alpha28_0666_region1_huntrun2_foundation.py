from pathlib import Path
import json, re

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.33'
PREV = '0.3.0-alpha.28.0.4.14.4.5.12.32'

# ---------------- version ----------------
manifest_path = ROOT / 'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['Version'] = VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

for rel in ['Cardcha.csproj', 'Directory.Build.targets']:
    p = ROOT / rel
    s = p.read_text(encoding='utf-8').replace(PREV, VERSION)
    p.write_text(s, encoding='utf-8')

# ---------------- Hunt Run 2.0 ----------------
p = ROOT / 'Services' / 'AirshipFoundationService.cs'
s = p.read_text(encoding='utf-8')

s = s.replace('    private const int Region1RunRoomCount = 4;\n', '''    // 0666 Hunt Run 2.0: a daily farming run is intentionally longer than the old 4-room prototype.
    private const int Region1RunMinNodes = 7;
    private const int Region1RunMaxNodes = 10;
    private const int Region1CheckpointNodeA = 3;
    private const int Region1CheckpointNodeB = 6;
    private const int Region1BossBranchMinNode = 7;
    private const string Region1EliteMarkerKey = "Ronvotri.Cardcha/Region1Elite";
    private const string Region1RootNestMarkerKey = "Ronvotri.Cardcha/Region1RootNest";

    private enum Region1RunEncounterType
    {
        Combat,
        Ambush,
        Elite,
        RootNest,
        Shrine
    }

    private enum Region1RunRouteKind
    {
        Moss,
        Briar,
        Ancient
    }
''', 1)

old_fields = '''    private int[] Region1RunRoute = Array.Empty<int>();
    private int Region1RunStep = -1;
    private int Region1RunSeed;
    private bool Region1RunActive;
    private bool Region1RunCompleted;
'''
new_fields = '''    private int[] Region1RunRoute = Array.Empty<int>();
    private Region1RunEncounterType[] Region1RunEncounters = Array.Empty<Region1RunEncounterType>();
    private Region1RunRouteKind[] Region1RunRouteKinds = Array.Empty<Region1RunRouteKind>();
    private int Region1RunStep = -1;
    private int Region1RunSeed;
    private int Region1RunTargetNodes;
    private bool Region1RunActive;
    private bool Region1RunCompleted;
    private bool Region1RunRouteChoicesPrepared;
    private int Region1RunLeftRoomIndex = -1;
    private int Region1RunRightRoomIndex = -1;
    private Region1RunRouteKind Region1RunLeftRouteKind = Region1RunRouteKind.Moss;
    private Region1RunRouteKind Region1RunRightRouteKind = Region1RunRouteKind.Briar;
    private bool Region1RunAwaitingBoon;
    private string[] Region1RunBoonChoices = Array.Empty<string>();
    private readonly HashSet<string> Region1RunBoons = new(StringComparer.OrdinalIgnoreCase);
    private readonly HashSet<int> Region1RunRewardedSteps = new();
    private int Region1RunUnbankedScrap;
    private int Region1RunUnbankedShiny;
'''
if old_fields not in s:
    raise RuntimeError('run fields anchor missing')
s = s.replace(old_fields, new_fields, 1)

# Update tick: detect a cleared node once and materialize checkpoint/boon/route state.
anchor = '''        if (this.PendingDepartureUntilMs > 0 && now > this.PendingDepartureUntilMs)
            this.PendingDepartureUntilMs = 0;
'''
insert = anchor + '''
        GameLocation? activeRunRoom = Game1.currentLocation;
        if (this.Region1RunActive
            && activeRunRoom is not null
            && TryGetRegion1RunRoomIndex(activeRunRoom, out _)
            && CountRegion1MarkedMonsters(activeRunRoom) == 0)
        {
            this.HandleRegion1RunNodeCleared(activeRunRoom);
        }
'''
if anchor not in s:
    raise RuntimeError('OnUpdateTicked anchor missing')
s = s.replace(anchor, insert, 1)

# Render portals, boon totems and root nests without changing TMX collision.
anchor = '''        if (location?.NameOrUniqueName.Equals(Region1LocationName, StringComparison.OrdinalIgnoreCase) == true)
            this.DrawRegion1Details(e.SpriteBatch, location);

        if (this.FlightCutsceneActive)
'''
insert = '''        if (location?.NameOrUniqueName.Equals(Region1LocationName, StringComparison.OrdinalIgnoreCase) == true)
            this.DrawRegion1Details(e.SpriteBatch, location);

        if (location is not null && TryGetRegion1RunRoomIndex(location, out _))
            this.DrawRegion1HuntRun2Overlay(e.SpriteBatch, location);

        if (this.FlightCutsceneActive)
'''
if anchor not in s:
    raise RuntimeError('OnRenderedWorld anchor missing')
s = s.replace(anchor, insert, 1)

# OnWarped no longer infers step by Array.IndexOf because 7-10 nodes intentionally reuse the 6 handcrafted rooms.
old_warp = '''        if (TryGetRegion1RunRoomIndex(e.NewLocation, out int roomIndex))
        {
            int routeStep = Array.IndexOf(this.Region1RunRoute, roomIndex);
            if (routeStep >= 0)
                this.Region1RunStep = routeStep;

            this.PopulateRegion1RunRoom(e.NewLocation, roomIndex);
            Game1.showGlobalMessage(
                ModEntry.T(
                    "airship.region1.run.enter",
                    new
                    {
                        step = Math.Max(1, this.Region1RunStep + 1),
                        total = Region1RunRoomCount,
                        room = ModEntry.T(Region1RunRoomNameKeys[roomIndex])
                    }
                )
            );
            return;
        }

        if (!e.NewLocation.NameOrUniqueName.Equals(Region1LocationName, StringComparison.OrdinalIgnoreCase))
            return;

        if (e.OldLocation is not null && TryGetRegion1RunRoomIndex(e.OldLocation, out _))
        {
            this.ClearRegion1MarkedMonsters(e.NewLocation);
            this.Region1RunActive = false;
            this.Region1RunCompleted = true;
            this.Region1RunStep = Region1RunRoomCount;
            Game1.showGlobalMessage(ModEntry.T("airship.region1.run.complete"));
            return;
        }
'''
new_warp = '''        if (TryGetRegion1RunRoomIndex(e.NewLocation, out int roomIndex))
        {
            if (!this.Region1RunActive || this.Region1RunStep < 0 || this.Region1RunStep >= this.Region1RunTargetNodes)
            {
                Game1.showGlobalMessage(ModEntry.T("airship.region1.run.unstable"));
                return;
            }

            this.PopulateRegion1RunRoom(e.NewLocation, roomIndex);
            string encounter = ModEntry.T($"airship.region1.run.encounter.{this.Region1RunEncounters[this.Region1RunStep].ToString().ToLowerInvariant()}");
            Game1.showGlobalMessage(
                ModEntry.T(
                    "airship.region1.run.enter2",
                    new
                    {
                        step = this.Region1RunStep + 1,
                        total = this.Region1RunTargetNodes,
                        room = ModEntry.T(Region1RunRoomNameKeys[roomIndex]),
                        encounter
                    }
                )
            );
            return;
        }

        // Unexpected exit (death/emergency warp) drops only the current unbanked route bonus.
        // Checkpointed wallet rewards are already persisted and stay safe.
        if (this.Region1RunActive
            && e.OldLocation is not null
            && TryGetRegion1RunRoomIndex(e.OldLocation, out _)
            && !e.NewLocation.NameOrUniqueName.Equals(Region1LocationName, StringComparison.OrdinalIgnoreCase))
        {
            int lost = this.Region1RunUnbankedScrap;
            int lostShiny = this.Region1RunUnbankedShiny;
            this.ResetRegion1RunState();
            if (lost > 0 || lostShiny > 0)
                Game1.showGlobalMessage(ModEntry.T("airship.region1.run.unbanked-lost", new { scrap = lost, shiny = lostShiny }));
        }

        if (!e.NewLocation.NameOrUniqueName.Equals(Region1LocationName, StringComparison.OrdinalIgnoreCase))
            return;

        if (e.OldLocation is not null && TryGetRegion1RunRoomIndex(e.OldLocation, out _))
        {
            this.ClearRegion1MarkedMonsters(e.NewLocation);
            this.Region1RunActive = false;
            this.Region1RunCompleted = true;
            this.Region1RunStep = this.Region1RunTargetNodes;
            Game1.showGlobalMessage(ModEntry.T("airship.region1.run.complete"));
            return;
        }
'''
if old_warp not in s:
    raise RuntimeError('OnWarped run block missing')
s = s.replace(old_warp, new_warp, 1)

# Replace old 4-room run core through monster factory with Hunt Run 2.0.
start = s.index('    private void ResetRegion1RunState()\n')
end = s.index('    private void ClearRegion1MarkedMonsters(GameLocation location)\n', start)
new_core = r'''    private void ResetRegion1RunState()
    {
        this.Region1RunRoute = Array.Empty<int>();
        this.Region1RunEncounters = Array.Empty<Region1RunEncounterType>();
        this.Region1RunRouteKinds = Array.Empty<Region1RunRouteKind>();
        this.Region1RunStep = -1;
        this.Region1RunSeed = 0;
        this.Region1RunTargetNodes = 0;
        this.Region1RunActive = false;
        this.Region1RunCompleted = false;
        this.Region1RunRouteChoicesPrepared = false;
        this.Region1RunLeftRoomIndex = -1;
        this.Region1RunRightRoomIndex = -1;
        this.Region1RunAwaitingBoon = false;
        this.Region1RunBoonChoices = Array.Empty<string>();
        this.Region1RunBoons.Clear();
        this.Region1RunRewardedSteps.Clear();
        this.Region1RunUnbankedScrap = 0;
        this.Region1RunUnbankedShiny = 0;
    }

    private GameLocation? BeginRegion1HuntRun()
    {
        if (!this.EnsureRegion1RunRoomLocations())
            return null;

        this.Region1RunSeed = unchecked(
            (int)Game1.uniqueIDForThisGame
            + Game1.Date.TotalDays * 397
            + this.Save.Data.AirshipFlightsTaken * 7919
        );
        Random random = new(this.Region1RunSeed);
        this.Region1RunTargetNodes = random.Next(Region1RunMinNodes, Region1RunMaxNodes + 1);
        this.Region1RunRoute = Enumerable.Repeat(-1, this.Region1RunTargetNodes).ToArray();
        this.Region1RunEncounters = Enumerable.Repeat(Region1RunEncounterType.Combat, this.Region1RunTargetNodes).ToArray();
        this.Region1RunRouteKinds = Enumerable.Repeat(Region1RunRouteKind.Moss, this.Region1RunTargetNodes).ToArray();
        this.Region1RunRoute[0] = random.Next(Region1RunRoomLocationNames.Length);
        this.Region1RunEncounters[0] = Region1RunEncounterType.Combat;
        this.Region1RunStep = 0;
        this.Region1RunActive = true;
        this.Region1RunCompleted = false;
        this.Region1RunRouteChoicesPrepared = false;
        this.Region1RunRewardedSteps.Clear();
        this.Region1RunBoons.Clear();
        this.Region1RunUnbankedScrap = 0;
        this.Region1RunUnbankedShiny = 0;

        this.Monitor.Log(
            $"Region I Hunt Run 2.0 seed={this.Region1RunSeed}; targetNodes={this.Region1RunTargetNodes}; firstRoom={ModEntry.T(Region1RunRoomNameKeys[this.Region1RunRoute[0]])}. Branches generate after each clear.",
            LogLevel.Info
        );

        return Game1.getLocationFromName(Region1RunRoomLocationNames[this.Region1RunRoute[0]]);
    }

    private static bool TryGetRegion1RunRoomIndex(GameLocation location, out int index)
    {
        string name = location.NameOrUniqueName;
        for (int i = 0; i < Region1RunRoomLocationNames.Length; i++)
        {
            if (!name.Equals(Region1RunRoomLocationNames[i], StringComparison.OrdinalIgnoreCase))
                continue;

            index = i;
            return true;
        }

        index = -1;
        return false;
    }

    private void HandleRegion1RunRoomInteraction(ButtonPressedEventArgs e, GameLocation location)
    {
        Point action = GetActionTile();
        Point retreat = ResolveRegion1RunReturnTile(location);

        if (Touches(action, retreat) || PlayerIsNear(retreat))
        {
            this.Helper.Input.Suppress(e.Button);
            this.BankRegion1RunRewards("extract");
            this.ResetRegion1RunState();
            this.StartFlightCutscene(returning: true);
            return;
        }

        int remaining = CountRegion1MarkedMonsters(location);
        if (remaining > 0)
        {
            Point[] blockedTargets = ResolveRegion1RunChoiceTiles(location);
            if (blockedTargets.Any(tile => Touches(action, tile)) || Touches(action, ResolveRegion1RunBossTile(location)))
            {
                this.Helper.Input.Suppress(e.Button);
                Game1.drawObjectDialogue(ModEntry.T("airship.region1.run.blocked", new { count = remaining }));
            }
            return;
        }

        this.HandleRegion1RunNodeCleared(location);

        if (this.Region1RunAwaitingBoon)
        {
            Point[] boonTiles = ResolveRegion1RunBoonTiles(location);
            for (int i = 0; i < boonTiles.Length && i < this.Region1RunBoonChoices.Length; i++)
            {
                if (!Touches(action, boonTiles[i]))
                    continue;
                this.Helper.Input.Suppress(e.Button);
                this.ChooseRegion1RunBoon(this.Region1RunBoonChoices[i]);
                return;
            }

            if (ResolveRegion1RunChoiceTiles(location).Any(tile => Touches(action, tile)))
            {
                this.Helper.Input.Suppress(e.Button);
                Game1.drawObjectDialogue(ModEntry.T("airship.region1.run.boon.choose-first"));
            }
            return;
        }

        int nodeNumber = this.Region1RunStep + 1;
        Point bossTile = ResolveRegion1RunBossTile(location);
        int owned = this.Save.Data.OwnedCards?.Count ?? 0;
        bool bossBranchVisible = nodeNumber >= Region1BossBranchMinNode;
        if (bossBranchVisible && Touches(action, bossTile))
        {
            this.Helper.Input.Suppress(e.Button);
            if (owned < Region1GateCardRequirement)
            {
                Game1.drawObjectDialogue(ModEntry.T("airship.region1.run.boss-locked", new { cards = owned, required = Region1GateCardRequirement }));
                return;
            }

            this.BankRegion1RunRewards("boss-branch");
            this.WarpRegion1RunToHub();
            return;
        }

        if (this.Region1RunStep >= this.Region1RunTargetNodes - 1)
        {
            if (Touches(action, bossTile))
            {
                this.Helper.Input.Suppress(e.Button);
                this.BankRegion1RunRewards("run-complete");
                this.WarpRegion1RunToHub();
            }
            return;
        }

        if (!this.Region1RunRouteChoicesPrepared)
            this.PrepareRegion1RunRouteChoices();

        Point[] routeTiles = ResolveRegion1RunChoiceTiles(location);
        if (routeTiles.Length >= 2 && Touches(action, routeTiles[0]))
        {
            this.Helper.Input.Suppress(e.Button);
            this.AdvanceRegion1HuntRun(this.Region1RunLeftRouteKind, this.Region1RunLeftRoomIndex);
            return;
        }
        if (routeTiles.Length >= 2 && Touches(action, routeTiles[1]))
        {
            this.Helper.Input.Suppress(e.Button);
            this.AdvanceRegion1HuntRun(this.Region1RunRightRouteKind, this.Region1RunRightRoomIndex);
        }
    }

    private void HandleRegion1RunNodeCleared(GameLocation location)
    {
        if (!this.Region1RunActive || this.Region1RunStep < 0 || this.Region1RunStep >= this.Region1RunTargetNodes)
            return;
        if (!this.Region1RunRewardedSteps.Add(this.Region1RunStep))
            return;

        int nodeNumber = this.Region1RunStep + 1;
        Region1RunRouteKind routeKind = this.Region1RunRouteKinds[this.Region1RunStep];
        Region1RunEncounterType encounter = this.Region1RunEncounters[this.Region1RunStep];

        if (routeKind is Region1RunRouteKind.Briar or Region1RunRouteKind.Ancient)
            this.Region1RunUnbankedScrap++;
        if (this.Region1RunBoons.Contains("scrap_compass"))
            this.Region1RunUnbankedScrap++;
        if (this.Region1RunBoons.Contains("hunters_edge") && encounter is Region1RunEncounterType.Elite or Region1RunEncounterType.RootNest)
            this.Region1RunUnbankedScrap++;
        if (this.Region1RunBoons.Contains("verdant_recovery"))
            Game1.player.health = Math.Min(Game1.player.maxHealth, Game1.player.health + 6);
        if (this.Region1RunBoons.Contains("moss_ward") && encounter is Region1RunEncounterType.Elite or Region1RunEncounterType.RootNest)
            Game1.player.health = Math.Min(Game1.player.maxHealth, Game1.player.health + 12);
        if (this.Region1RunBoons.Contains("fortune_bud"))
        {
            Random fortune = new(unchecked(this.Region1RunSeed + nodeNumber * 982451653));
            if (fortune.NextDouble() < 0.20d)
                this.Region1RunUnbankedShiny++;
        }

        if (nodeNumber == Region1CheckpointNodeA || nodeNumber == Region1CheckpointNodeB)
        {
            if (this.Region1RunBoons.Contains("deep_roots"))
                Game1.player.health = Math.Min(Game1.player.maxHealth, Game1.player.health + 20);
            this.BankRegion1RunRewards($"checkpoint-{nodeNumber}");
            Game1.playSound("questcomplete");
            Game1.showGlobalMessage(ModEntry.T("airship.region1.run.checkpoint", new { node = nodeNumber }));
        }

        bool boonMilestone = nodeNumber == 2 || nodeNumber == 5 || nodeNumber == 8;
        if (boonMilestone || encounter == Region1RunEncounterType.Shrine)
            this.PrepareRegion1RunBoonChoices();

        if (!this.Region1RunAwaitingBoon && this.Region1RunStep < this.Region1RunTargetNodes - 1)
            this.PrepareRegion1RunRouteChoices();

        Game1.playSound("discoverMineral");
    }

    private void PrepareRegion1RunBoonChoices()
    {
        string[] pool =
        {
            "verdant_recovery",
            "scrap_compass",
            "deep_roots",
            "fortune_bud",
            "hunters_edge",
            "moss_ward"
        };
        string[] available = pool.Where(id => !this.Region1RunBoons.Contains(id)).ToArray();
        if (available.Length < 3)
        {
            this.Region1RunUnbankedScrap += 2;
            this.Region1RunAwaitingBoon = false;
            this.Region1RunBoonChoices = Array.Empty<string>();
            return;
        }

        Random random = new(unchecked(this.Region1RunSeed + (this.Region1RunStep + 1) * 65537 + this.Region1RunBoons.Count * 31337));
        this.Region1RunBoonChoices = available.OrderBy(_ => random.Next()).Take(3).ToArray();
        this.Region1RunAwaitingBoon = true;
        this.Region1RunRouteChoicesPrepared = false;
        Game1.showGlobalMessage(ModEntry.T("airship.region1.run.boon.ready"));
    }

    private void ChooseRegion1RunBoon(string boonId)
    {
        if (!this.Region1RunAwaitingBoon || !this.Region1RunBoonChoices.Contains(boonId, StringComparer.OrdinalIgnoreCase))
            return;
        this.Region1RunBoons.Add(boonId);
        this.Region1RunAwaitingBoon = false;
        this.Region1RunBoonChoices = Array.Empty<string>();
        Game1.playSound("yoba");
        Game1.showGlobalMessage(ModEntry.T("airship.region1.run.boon.chosen", new { boon = ModEntry.T($"airship.region1.run.boon.{boonId}.name") }));
        if (this.Region1RunStep < this.Region1RunTargetNodes - 1)
            this.PrepareRegion1RunRouteChoices();
    }

    private void PrepareRegion1RunRouteChoices()
    {
        if (!this.Region1RunActive || this.Region1RunStep >= this.Region1RunTargetNodes - 1)
        {
            this.Region1RunRouteChoicesPrepared = false;
            return;
        }

        Random random = new(unchecked(this.Region1RunSeed + (this.Region1RunStep + 1) * 104729));
        Region1RunRouteKind[] kinds = Enum.GetValues<Region1RunRouteKind>().OrderBy(_ => random.Next()).Take(2).ToArray();
        this.Region1RunLeftRouteKind = kinds[0];
        this.Region1RunRightRouteKind = kinds[1];
        int currentRoom = this.Region1RunRoute[this.Region1RunStep];
        this.Region1RunLeftRoomIndex = PickNextRegion1Room(random, currentRoom, -1);
        this.Region1RunRightRoomIndex = PickNextRegion1Room(random, currentRoom, this.Region1RunLeftRoomIndex);
        this.Region1RunRouteChoicesPrepared = true;
    }

    private static int PickNextRegion1Room(Random random, int currentRoom, int excludedRoom)
    {
        int[] candidates = Enumerable.Range(0, Region1RunRoomLocationNames.Length)
            .Where(i => i != currentRoom && i != excludedRoom)
            .OrderBy(_ => random.Next())
            .ToArray();
        return candidates.Length == 0 ? Math.Max(0, (currentRoom + 1) % Region1RunRoomLocationNames.Length) : candidates[0];
    }

    private Region1RunEncounterType RollRegion1Encounter(Region1RunRouteKind route, int nodeIndex)
    {
        Random random = new(unchecked(this.Region1RunSeed + (nodeIndex + 1) * 32452843 + (int)route * 49999));
        int roll = random.Next(100);
        return route switch
        {
            Region1RunRouteKind.Moss => roll < 55 ? Region1RunEncounterType.Combat
                : roll < 78 ? Region1RunEncounterType.Ambush
                : roll < 90 ? Region1RunEncounterType.RootNest
                : Region1RunEncounterType.Shrine,
            Region1RunRouteKind.Briar => roll < 38 ? Region1RunEncounterType.Elite
                : roll < 68 ? Region1RunEncounterType.RootNest
                : Region1RunEncounterType.Ambush,
            _ => roll < 34 ? Region1RunEncounterType.Shrine
                : roll < 58 ? Region1RunEncounterType.RootNest
                : roll < 78 ? Region1RunEncounterType.Elite
                : Region1RunEncounterType.Combat,
        };
    }

    private void AdvanceRegion1HuntRun(Region1RunRouteKind routeKind, int roomIndex)
    {
        if (!this.Region1RunActive || this.Region1RunStep < 0 || this.Region1RunStep >= this.Region1RunTargetNodes - 1)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.region1.run.unstable"));
            return;
        }

        int nextStep = this.Region1RunStep + 1;
        this.Region1RunRoute[nextStep] = Math.Clamp(roomIndex, 0, Region1RunRoomLocationNames.Length - 1);
        this.Region1RunRouteKinds[nextStep] = routeKind;
        this.Region1RunEncounters[nextStep] = this.RollRegion1Encounter(routeKind, nextStep);
        this.Region1RunStep = nextStep;
        this.Region1RunRouteChoicesPrepared = false;
        this.Region1RunAwaitingBoon = false;
        this.Region1RunBoonChoices = Array.Empty<string>();

        GameLocation? next = Game1.getLocationFromName(Region1RunRoomLocationNames[this.Region1RunRoute[nextStep]]);
        if (next is null)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.region1.run.unstable"));
            return;
        }

        Point nextArrival = ResolveRegion1RunArrivalTile(next);
        this.WarpGraceUntilMs = Environment.TickCount64 + 650L;
        Game1.playSound("wand");
        Game1.warpFarmer(next.NameOrUniqueName, nextArrival.X, nextArrival.Y, 0);
    }

    private void WarpRegion1RunToHub()
    {
        GameLocation? hub = this.EnsureRegion1Location();
        if (hub is null)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.region1.unavailable"));
            return;
        }

        Point arrival = ResolveRegion1ArrivalTile(hub);
        this.WarpGraceUntilMs = Environment.TickCount64 + 650L;
        Game1.playSound("discoverMineral");
        Game1.warpFarmer(Region1LocationName, arrival.X, arrival.Y, 0);
    }

    private void PopulateRegion1RunRoom(GameLocation location, int roomIndex)
    {
        this.ClearRegion1MarkedMonsters(location);
        if (!this.Region1RunActive || this.Region1RunStep < 0 || this.Region1RunStep >= this.Region1RunEncounters.Length)
            return;

        Region1RunEncounterType encounter = this.Region1RunEncounters[this.Region1RunStep];
        if (encounter == Region1RunEncounterType.Shrine)
        {
            this.Monitor.Log($"Region I Hunt Run node {this.Region1RunStep + 1}: Ancient Shrine, no combat spawn.", LogLevel.Trace);
            return;
        }

        Point[][] roomCandidates =
        {
            new[] { new Point(5,5), new Point(9,5), new Point(18,5), new Point(22,5), new Point(6,9), new Point(11,9), new Point(17,9), new Point(22,9), new Point(5,13), new Point(10,13), new Point(18,13), new Point(23,13), new Point(8,16), new Point(19,16) },
            new[] { new Point(5,4), new Point(10,5), new Point(17,4), new Point(22,5), new Point(7,9), new Point(11,10), new Point(18,9), new Point(23,10), new Point(5,15), new Point(10,14), new Point(18,15), new Point(22,14) },
            new[] { new Point(4,4), new Point(9,5), new Point(18,5), new Point(23,4), new Point(6,10), new Point(11,10), new Point(17,10), new Point(22,10), new Point(4,15), new Point(9,14), new Point(18,14), new Point(23,15) },
            new[] { new Point(5,4), new Point(10,4), new Point(18,5), new Point(22,5), new Point(6,9), new Point(12,9), new Point(17,10), new Point(22,10), new Point(5,14), new Point(10,15), new Point(18,14), new Point(23,15) },
            new[] { new Point(5,5), new Point(9,6), new Point(18,6), new Point(22,5), new Point(5,10), new Point(11,9), new Point(17,11), new Point(22,10), new Point(6,15), new Point(10,14), new Point(18,14), new Point(22,15) },
            new[] { new Point(5,5), new Point(10,5), new Point(18,5), new Point(23,5), new Point(6,9), new Point(10,11), new Point(18,9), new Point(22,11), new Point(5,15), new Point(10,15), new Point(18,15), new Point(23,15) },
        };

        int encounterSeed = unchecked(this.Region1RunSeed + roomIndex * 104729 + Math.Max(0, this.Region1RunStep) * 8191);
        Random random = new(encounterSeed);
        Point[] shuffled = roomCandidates[roomIndex].OrderBy(_ => random.Next()).ToArray();
        int targetCount = encounter switch
        {
            Region1RunEncounterType.Combat => random.Next(5, 8),
            Region1RunEncounterType.Ambush => random.Next(8, 11),
            Region1RunEncounterType.Elite => 4,
            Region1RunEncounterType.RootNest => 6,
            _ => 0
        };
        int spawned = 0;

        foreach (Point tile in shuffled)
        {
            if (spawned >= targetCount)
                break;

            Vector2 tileVector = new(tile.X, tile.Y);
            try
            {
                if (location.IsTileBlockedBy(tileVector) || location.Objects.ContainsKey(tileVector))
                    continue;
            }
            catch
            {
                continue;
            }

            Monster monster;
            if (encounter == Region1RunEncounterType.Elite && spawned == 0)
            {
                GreenSlime elite = new(tileVector * 64f, 0) { MaxHealth = 210 + this.Region1RunStep * 16, Speed = 3 };
                elite.Health = elite.MaxHealth;
                elite.modData[Region1EliteMarkerKey] = "1";
                monster = elite;
            }
            else if (encounter == Region1RunEncounterType.RootNest && spawned < 3)
            {
                GreenSlime nest = new(tileVector * 64f, 0) { MaxHealth = 60 + this.Region1RunStep * 8, Speed = 0 };
                nest.Health = nest.MaxHealth;
                nest.modData[Region1RootNestMarkerKey] = "1";
                monster = nest;
            }
            else
            {
                monster = CreateRegion1RunMonster(roomIndex, random.Next(100), tileVector * 64f);
            }

            monster.modData[Region1MonsterMarkerKey] = "huntrun2";
            location.characters.Add(monster);
            spawned++;
        }

        this.Monitor.Log(
            $"Region I Hunt Run 2.0 node {this.Region1RunStep + 1}/{this.Region1RunTargetNodes}: room={roomIndex + 1}, encounter={encounter}, spawned={spawned}.",
            LogLevel.Trace
        );
    }

    private static Monster CreateRegion1RunMonster(int roomIndex, int roll, Vector2 position)
        => roomIndex switch
        {
            0 => roll < 72 ? (Monster)new GreenSlime(position, 0) : new Bug(position, 0),
            1 => roll < 55 ? (Monster)new GreenSlime(position, 0) : new Bat(position),
            2 => roll < 52 ? (Monster)new Bug(position, 0) : new Bat(position),
            3 => roll < 45 ? (Monster)new GreenSlime(position, 0) : roll < 78 ? new Bug(position, 0) : new Bat(position),
            4 => roll < 68 ? (Monster)new Bat(position) : new GreenSlime(position, 0),
            _ => roll < 34 ? (Monster)new GreenSlime(position, 0) : roll < 67 ? new Bat(position) : new Bug(position, 0),
        };

    private void BankRegion1RunRewards(string reason)
    {
        int scrap = Math.Max(0, this.Region1RunUnbankedScrap);
        int shiny = Math.Max(0, this.Region1RunUnbankedShiny);
        if (scrap <= 0 && shiny <= 0)
            return;

        this.Save.Data.CardboardScraps += scrap;
        this.Save.Data.ShinyScraps += shiny;
        this.Region1RunUnbankedScrap = 0;
        this.Region1RunUnbankedShiny = 0;
        this.Save.Save();
        Game1.showGlobalMessage(ModEntry.T("airship.region1.run.bank", new { scrap, shiny, reason }));
    }

    public string DescribeHuntRun2()
    {
        if (!Context.IsWorldReady)
            return "HuntRun2=<no save>";
        string encounter = this.Region1RunStep >= 0 && this.Region1RunStep < this.Region1RunEncounters.Length
            ? this.Region1RunEncounters[this.Region1RunStep].ToString()
            : "none";
        string route = this.Region1RunStep >= 0 && this.Region1RunStep < this.Region1RunRouteKinds.Length
            ? this.Region1RunRouteKinds[this.Region1RunStep].ToString()
            : "none";
        return $"HuntRun2 Active={this.Region1RunActive} | Node={Math.Max(0, this.Region1RunStep + 1)}/{this.Region1RunTargetNodes} | " +
               $"Encounter={encounter} | Route={route} | Boons=[{string.Join(',', this.Region1RunBoons)}] | " +
               $"AwaitingBoon={this.Region1RunAwaitingBoon} | Unbanked={this.Region1RunUnbankedScrap} Scrap + {this.Region1RunUnbankedShiny} Shiny | " +
               $"BossBranch={(this.Region1RunStep + 1 >= Region1BossBranchMinNode)} | Seed={this.Region1RunSeed}";
    }

    public string DebugClearHuntRunNode()
    {
        if (!Context.IsWorldReady || !this.Region1RunActive || Game1.currentLocation is null || !TryGetRegion1RunRoomIndex(Game1.currentLocation, out _))
            return "Hunt Run 2.0 TEST: enter a Region I run room first.";
        this.ClearRegion1MarkedMonsters(Game1.currentLocation);
        this.HandleRegion1RunNodeCleared(Game1.currentLocation);
        return $"TEST: cleared node {this.Region1RunStep + 1}/{this.Region1RunTargetNodes}. {this.DescribeHuntRun2()}";
    }

    private void DrawRegion1HuntRun2Overlay(SpriteBatch batch, GameLocation room)
    {
        if (!this.Region1RunActive || this.Region1RunStep < 0 || this.Region1RunStep >= this.Region1RunTargetNodes)
            return;

        foreach (Monster nest in room.characters.OfType<Monster>().Where(m => m.Health > 0 && m.modData.ContainsKey(Region1RootNestMarkerKey)))
        {
            Vector2 center = Game1.GlobalToLocal(Game1.viewport, nest.Position + new Vector2(32f, 32f));
            int pulse = 34 + (int)(5f * Math.Sin(Environment.TickCount64 / 170d));
            batch.Draw(Game1.staminaRect, new Rectangle((int)center.X - pulse, (int)center.Y - 3, pulse * 2, 6), new Color(111, 199, 83) * 0.55f);
            batch.Draw(Game1.staminaRect, new Rectangle((int)center.X - 3, (int)center.Y - pulse, 6, pulse * 2), new Color(111, 199, 83) * 0.55f);
        }

        if (CountRegion1MarkedMonsters(room) > 0)
            return;

        if (this.Region1RunAwaitingBoon)
        {
            Point[] boonTiles = ResolveRegion1RunBoonTiles(room);
            for (int i = 0; i < boonTiles.Length && i < this.Region1RunBoonChoices.Length; i++)
                DrawRunChoiceMarker(batch, boonTiles[i], new Color(154, 228, 124), ModEntry.T($"airship.region1.run.boon.{this.Region1RunBoonChoices[i]}.name"));
            return;
        }

        int nodeNumber = this.Region1RunStep + 1;
        if (this.Region1RunStep < this.Region1RunTargetNodes - 1)
        {
            if (!this.Region1RunRouteChoicesPrepared)
                this.PrepareRegion1RunRouteChoices();
            Point[] routes = ResolveRegion1RunChoiceTiles(room);
            DrawRunChoiceMarker(batch, routes[0], RouteColor(this.Region1RunLeftRouteKind), ModEntry.T($"airship.region1.run.route.{this.Region1RunLeftRouteKind.ToString().ToLowerInvariant()}"));
            DrawRunChoiceMarker(batch, routes[1], RouteColor(this.Region1RunRightRouteKind), ModEntry.T($"airship.region1.run.route.{this.Region1RunRightRouteKind.ToString().ToLowerInvariant()}"));
        }

        Point boss = ResolveRegion1RunBossTile(room);
        if (nodeNumber >= Region1BossBranchMinNode)
        {
            int owned = this.Save.Data.OwnedCards?.Count ?? 0;
            string label = owned >= Region1GateCardRequirement
                ? ModEntry.T("airship.region1.run.route.boss")
                : ModEntry.T("airship.region1.run.route.boss-locked-short", new { cards = owned, required = Region1GateCardRequirement });
            DrawRunChoiceMarker(batch, boss, new Color(214, 194, 92), label);
        }
        else if (this.Region1RunStep >= this.Region1RunTargetNodes - 1)
        {
            DrawRunChoiceMarker(batch, boss, new Color(158, 211, 178), ModEntry.T("airship.region1.run.route.finish"));
        }
    }

    private static Color RouteColor(Region1RunRouteKind route) => route switch
    {
        Region1RunRouteKind.Moss => new Color(113, 198, 118),
        Region1RunRouteKind.Briar => new Color(202, 117, 104),
        _ => new Color(139, 177, 224)
    };

    private static void DrawRunChoiceMarker(SpriteBatch batch, Point tile, Color color, string label)
    {
        Vector2 world = new(tile.X * 64f + 32f, tile.Y * 64f + 32f);
        Vector2 local = Game1.GlobalToLocal(Game1.viewport, world);
        float pulse = 0.82f + 0.12f * (float)Math.Sin(Environment.TickCount64 / 180d + tile.X);
        int size = (int)(24f * pulse);
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - size, (int)local.Y - 3, size * 2, 6), color * 0.72f);
        batch.Draw(Game1.staminaRect, new Rectangle((int)local.X - 3, (int)local.Y - size, 6, size * 2), color * 0.72f);
        Vector2 textSize = Game1.smallFont.MeasureString(label);
        batch.DrawString(Game1.smallFont, label, new Vector2(local.X - textSize.X / 2f, local.Y + 30f), Color.White);
    }

    private static Point[] ResolveRegion1RunChoiceTiles(GameLocation room)
    {
        int width = room.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 28;
        int center = width / 2;
        return new[] { new Point(Math.Max(2, center - 5), 2), new Point(Math.Min(width - 3, center + 5), 2) };
    }

    private static Point[] ResolveRegion1RunBoonTiles(GameLocation room)
    {
        int width = room.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 28;
        int center = width / 2;
        return new[] { new Point(Math.Max(3, center - 7), 5), new Point(center, 5), new Point(Math.Min(width - 4, center + 7), 5) };
    }

    private static Point ResolveRegion1RunBossTile(GameLocation room)
    {
        int width = room.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 28;
        return new Point(width / 2, 2);
    }

'''
s = s[:start] + new_core + s[end:]

# Remove obsolete single-next resolver if still present to avoid dead-contract confusion.
s = re.sub(r'    private static Point ResolveRegion1RunNextTile\(GameLocation room\)\n    \{.*?\n    \}\n\n', '', s, flags=re.S)

p.write_text(s, encoding='utf-8')

# ---------------- i18n ----------------
def update_json(path: Path, changes: dict):
    data = json.loads(path.read_text(encoding='utf-8'))
    data.update(changes)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

common_en = {
    'airship.region1.run.enter2': 'HUNT {{step}}/{{total}} • {{room}} • {{encounter}}',
    'airship.region1.run.encounter.combat': 'HUNT',
    'airship.region1.run.encounter.ambush': 'AMBUSH',
    'airship.region1.run.encounter.elite': 'ELITE HUNT',
    'airship.region1.run.encounter.rootnest': 'ROOT NEST',
    'airship.region1.run.encounter.shrine': 'ANCIENT SHRINE',
    'airship.region1.run.route.moss': 'MOSS PATH',
    'airship.region1.run.route.briar': 'BRIAR PATH',
    'airship.region1.run.route.ancient': 'ANCIENT PATH',
    'airship.region1.run.route.boss': 'BOSS GATE',
    'airship.region1.run.route.finish': 'FINISH HUNT',
    'airship.region1.run.route.boss-locked-short': 'GATE {{cards}}/{{required}}',
    'airship.region1.run.boss-locked': 'The Boss Gate resonates, but you only have {{cards}}/{{required}} unique cards. Keep hunting or extract.',
    'airship.region1.run.checkpoint': 'CHECKPOINT • Node {{node}} banked your route rewards. You can extract safely or keep going deeper.',
    'airship.region1.run.bank': 'RUN REWARD BANKED • +{{scrap}} Cardboard Scrap • +{{shiny}} Shiny Scrap',
    'airship.region1.run.unbanked-lost': 'The emergency exit scattered the unbanked route bonus: {{scrap}} Scrap, {{shiny}} Shiny.',
    'airship.region1.run.boon.ready': 'A Verdant boon awakened. Choose 1 of 3 before continuing.',
    'airship.region1.run.boon.choose-first': 'Choose one Verdant boon first.',
    'airship.region1.run.boon.chosen': 'RUN BOON • {{boon}} joined this Hunt Run.',
    'airship.region1.run.boon.verdant_recovery.name': 'Verdant Recovery',
    'airship.region1.run.boon.verdant_recovery.desc': 'After each cleared node, recover 6 HP.',
    'airship.region1.run.boon.scrap_compass.name': 'Scrap Compass',
    'airship.region1.run.boon.scrap_compass.desc': 'Each cleared node adds +1 unbanked Cardboard Scrap to the run.',
    'airship.region1.run.boon.deep_roots.name': 'Deep Roots',
    'airship.region1.run.boon.deep_roots.desc': 'Checkpoints restore 20 HP.',
    'airship.region1.run.boon.fortune_bud.name': 'Fortune Bud',
    'airship.region1.run.boon.fortune_bud.desc': 'Each cleared node has a 20% chance to add +1 unbanked Shiny Scrap.',
    'airship.region1.run.boon.hunters_edge.name': "Hunter's Edge",
    'airship.region1.run.boon.hunters_edge.desc': 'Elite Hunt and Root Nest clears add +1 unbanked Cardboard Scrap.',
    'airship.region1.run.boon.moss_ward.name': 'Moss Ward',
    'airship.region1.run.boon.moss_ward.desc': 'Clearing Elite Hunt or Root Nest restores 12 HP.'
}
common_vi = {
    'airship.region1.run.enter2': 'HUNT {{step}}/{{total}} • {{room}} • {{encounter}}',
    'airship.region1.run.encounter.combat': 'SĂN QUÁI',
    'airship.region1.run.encounter.ambush': 'PHỤC KÍCH',
    'airship.region1.run.encounter.elite': 'SĂN ELITE',
    'airship.region1.run.encounter.rootnest': 'Ổ RỄ',
    'airship.region1.run.encounter.shrine': 'ĐIỆN THỜ CỔ',
    'airship.region1.run.route.moss': 'LỐI RÊU',
    'airship.region1.run.route.briar': 'LỐI GAI',
    'airship.region1.run.route.ancient': 'LỐI CỔ',
    'airship.region1.run.route.boss': 'BOSS GATE',
    'airship.region1.run.route.finish': 'KẾT THÚC CHUYẾN SĂN',
    'airship.region1.run.route.boss-locked-short': 'CỔNG {{cards}}/{{required}}',
    'airship.region1.run.boss-locked': 'Boss Gate đã cộng hưởng, nhưng bạn mới có {{cards}}/{{required}} lá bài khác nhau. Có thể săn tiếp hoặc rút lui.',
    'airship.region1.run.checkpoint': 'CHECKPOINT • Node {{node}} đã cất an toàn phần thưởng đường đi. Có thể rút lui hoặc tiếp tục xuống sâu hơn.',
    'airship.region1.run.bank': 'ĐÃ CẤT PHẦN THƯỞNG • +{{scrap}} Cardboard Scrap • +{{shiny}} Shiny Scrap',
    'airship.region1.run.unbanked-lost': 'Lối thoát khẩn cấp làm rơi phần thưởng chưa cất: {{scrap}} Scrap, {{shiny}} Shiny.',
    'airship.region1.run.boon.ready': 'Một Verdant Boon vừa thức tỉnh. Chọn 1 trong 3 trước khi đi tiếp.',
    'airship.region1.run.boon.choose-first': 'Hãy chọn một Verdant Boon trước.',
    'airship.region1.run.boon.chosen': 'RUN BOON • {{boon}} đã theo bạn trong chuyến săn này.',
    'airship.region1.run.boon.verdant_recovery.name': 'Verdant Recovery',
    'airship.region1.run.boon.verdant_recovery.desc': 'Mỗi khi dọn xong một node, hồi 6 HP.',
    'airship.region1.run.boon.scrap_compass.name': 'Scrap Compass',
    'airship.region1.run.boon.scrap_compass.desc': 'Mỗi node hoàn thành cộng +1 Cardboard Scrap chưa cất.',
    'airship.region1.run.boon.deep_roots.name': 'Deep Roots',
    'airship.region1.run.boon.deep_roots.desc': 'Checkpoint hồi 20 HP.',
    'airship.region1.run.boon.fortune_bud.name': 'Fortune Bud',
    'airship.region1.run.boon.fortune_bud.desc': 'Mỗi node hoàn thành có 20% cơ hội cộng +1 Shiny Scrap chưa cất.',
    'airship.region1.run.boon.hunters_edge.name': "Hunter's Edge",
    'airship.region1.run.boon.hunters_edge.desc': 'Dọn Elite Hunt hoặc Root Nest cộng +1 Cardboard Scrap chưa cất.',
    'airship.region1.run.boon.moss_ward.name': 'Moss Ward',
    'airship.region1.run.boon.moss_ward.desc': 'Dọn Elite Hunt hoặc Root Nest hồi 12 HP.'
}
update_json(ROOT/'i18n/default.json', common_en)
update_json(ROOT/'i18n/vi.json', common_vi)

# ---------------- ModEntry commands/version ----------------
mod_path = ROOT/'ModEntry.cs'
mod = mod_path.read_text(encoding='utf-8')
anchor = '        helper.ConsoleCommands.Add("cardcha_airship_status", "Show alpha.28 Airship foundation state.", this.CommandAirshipStatus);\n'
if anchor not in mod:
    raise RuntimeError('airship status command anchor missing')
mod = mod.replace(anchor, anchor + '''        helper.ConsoleCommands.Add("cardcha_huntrun_status", "Show Region I Hunt Run 2.0 route/boon/checkpoint state.", (_, _) => this.Monitor.Log(this.Airship.DescribeHuntRun2(), LogLevel.Alert));
        helper.ConsoleCommands.Add("cardcha_huntrun_clear", "TEST ONLY: clear the current Hunt Run 2.0 encounter.", (_, _) => this.Monitor.Log(this.Airship.DebugClearHuntRunNode(), LogLevel.Alert));
''', 1)
mod = mod.replace('0.3.0-alpha.28.0.4.14.4.5.12.32 VERDANT REGION I BALANCE PASS TEST',
                  '0.3.0-alpha.28.0.4.14.4.5.12.33 REGION I HUNT RUN 2.0 FOUNDATION TEST', 1)
mod_path.write_text(mod, encoding='utf-8')

# ---------------- handoff ----------------
handoff = Path('handoff/ALPHA28_0666_REGION1_HUNTRUN2_FOUNDATION.md')
handoff.write_text(f'''# Alpha28 0666 - Region I Hunt Run 2.0 Foundation\n\nBuild: `{VERSION}`\nBranch: `cardcha-alpha28-0666-region1-huntrun2-foundation`\nStatus: implementation candidate; in-game acceptance pending.\n\n## Run length\n- Each Region I flight now rolls 7-10 nodes.\n- Six handcrafted room maps remain the visual pool; rooms may recur later in a run, but the next node never immediately repeats the current room and the two visible branch choices point to different rooms.\n\n## Branching routes\nAfter a node is cleared, two world-space route markers appear:\n- Moss Path: safer weighting, mostly Combat/Ambush.\n- Briar Path: high-pressure weighting, Elite/Root Nest/Ambush, +1 unbanked Scrap on clear.\n- Ancient Path: Shrine/Root/Elite mix, +1 unbanked Scrap on clear.\nTwo of the three are offered each node.\n\n## Encounter foundation\n- Combat: 5-7 controlled monsters.\n- Ambush: 8-10 monsters.\n- Elite Hunt: one high-HP elite proxy plus three adds.\n- Root Nest: three stationary root-node proxies plus guards; root nodes receive a Cardcha world marker.\n- Ancient Shrine: no combat; it immediately feeds the boon-choice flow.\nAll monster deaths still use the existing Scrap drop pipeline. No finished cards drop from rooms.\n\n## Run Boons\nAt nodes 2, 5 and 8, plus Ancient Shrine encounters, the run offers 3 temporary boons as three in-world totems. Choose one by interacting with it. Current pool: Verdant Recovery, Scrap Compass, Deep Roots, Fortune Bud, Hunter's Edge, Moss Ward. Boons reset when the run ends.\n\n## Checkpoints / extract risk\n- Checkpoints at nodes 3 and 6 bank route bonuses into the existing virtual Scrap wallets.\n- South exit remains a safe voluntary extract and banks current unbanked bonuses.\n- An unexpected exit/death discards only the unbanked route bonus; previously checkpointed rewards remain safe.\n\n## Boss branch\n- From node 7 onward, a center Boss Gate branch appears.\n- If the player has 20 unique cards, it banks current run rewards and routes to the existing Region I Boss Gate hub.\n- If below 20, the marker shows progress and the player can keep hunting or extract.\n- Boss remains optional for repeat farming.\n\n## Debug\n- `cardcha_huntrun_status`\n- `cardcha_huntrun_clear`\n\n## Preserved locks\nSave schema 19, 76 active normal cards / 80 base IDs, Monster -> Scrap -> Gacha canon, Region I Boss package 0660-0665, Verdant Core, Guardian Rabbit 10 sec, Boss Energy x1/3, Airship visual/upgrade progression, Forest gate, MiMi profile/CC/stair fixes and TMX strict CSV safety remain unchanged.\n''', encoding='utf-8')
Path('handoff/LATEST_CARDCHA_HANDOFF.md').write_text(f'''# Latest Cardcha handoff\n\nCurrent branch: `cardcha-alpha28-0666-region1-huntrun2-foundation`\nCurrent build: `{VERSION}`\n\nContinue from:\n`handoff/ALPHA28_0666_REGION1_HUNTRUN2_FOUNDATION.md`\n\n0660-0666 in-game acceptance remains pending. Do not resume from stale `main`.\n''', encoding='utf-8')

print(json.dumps({
    'version': VERSION,
    'runNodes': '7-10',
    'routes': ['Moss', 'Briar', 'Ancient'],
    'encounters': ['Combat', 'Ambush', 'Elite', 'RootNest', 'Shrine'],
    'boonChoice': '1-of-3',
    'checkpoints': [3, 6],
    'bossBranchFromNode': 7,
    'schema': 19
}, indent=2))
