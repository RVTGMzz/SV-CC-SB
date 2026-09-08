from pathlib import Path
import json, re

ROOT = Path('src/Cardcha')
VERSION = '0.3.0-alpha.28.0.4.14.4.5.12.34'
PREV = '0.3.0-alpha.28.0.4.14.4.5.12.33'

# ---------------- version ----------------
manifest_path = ROOT / 'manifest.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['Version'] = VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

for rel in ['Cardcha.csproj', 'Directory.Build.targets']:
    p = ROOT / rel
    s = p.read_text(encoding='utf-8').replace(PREV, VERSION)
    p.write_text(s, encoding='utf-8')

# ---------------- Hunt Run 2.0 advanced layer ----------------
p = ROOT / 'Services' / 'AirshipFoundationService.cs'
s = p.read_text(encoding='utf-8')

# Advanced enums + marker.
s = s.replace(
'''    private const string Region1EliteMarkerKey = "Ronvotri.Cardcha/Region1Elite";
    private const string Region1RootNestMarkerKey = "Ronvotri.Cardcha/Region1RootNest";
''',
'''    private const string Region1EliteMarkerKey = "Ronvotri.Cardcha/Region1Elite";
    private const string Region1EliteAffixMarkerKey = "Ronvotri.Cardcha/Region1EliteAffix";
    private const string Region1RootNestMarkerKey = "Ronvotri.Cardcha/Region1RootNest";
''', 1)

s = s.replace(
'''        Elite,
        RootNest,
        Shrine
    }

    private enum Region1RunRouteKind
''',
'''        Elite,
        RootNest,
        Shrine,
        LostCache,
        Moonwell,
        AncientEcho
    }

    private enum Region1EliteAffix
    {
        ThornAura,
        Swift,
        Regrowth,
        Bulwark,
        Infested,
        Resonant
    }

    private enum Region1DailyMutation
    {
        CalmGrove,
        BriarBloom,
        MoonlitGrove,
        Overgrown,
        ChaoticResonance
    }

    private enum Region1RunRouteKind
''', 1)

# Runtime fields.
field_anchor = '''    private int Region1RunUnbankedScrap;
    private int Region1RunUnbankedShiny;
'''
if field_anchor not in s:
    raise RuntimeError('0666 run field anchor missing')
s = s.replace(field_anchor, field_anchor + '''    private long Region1EliteAuraNextAtMs;
    private int Region1RunRareRoomsSeen;
''', 1)

# Update active elite affixes once per second.
update_anchor = '''        if (this.Region1RunActive
            && activeRunRoom is not null
            && TryGetRegion1RunRoomIndex(activeRunRoom, out _)
            && CountRegion1MarkedMonsters(activeRunRoom) == 0)
        {
            this.HandleRegion1RunNodeCleared(activeRunRoom);
        }
'''
if update_anchor not in s:
    raise RuntimeError('0666 active run update anchor missing')
s = s.replace(update_anchor, update_anchor + '''
        if (this.Region1RunActive
            && activeRunRoom is not null
            && TryGetRegion1RunRoomIndex(activeRunRoom, out _)
            && e.IsMultipleOf(60))
        {
            this.UpdateRegion1EliteAffixes(activeRunRoom, now);
        }
''', 1)

# Daily mutation banner on entry to first node.
warp_anchor = '''            this.PopulateRegion1RunRoom(e.NewLocation, roomIndex);
            string encounter = ModEntry.T($"airship.region1.run.encounter.{this.Region1RunEncounters[this.Region1RunStep].ToString().ToLowerInvariant()}");
'''
if warp_anchor not in s:
    raise RuntimeError('0666 OnWarped encounter anchor missing')
s = s.replace(warp_anchor, '''            this.PopulateRegion1RunRoom(e.NewLocation, roomIndex);
            if (this.Region1RunStep == 0)
            {
                Region1DailyMutation mutation = this.ResolveRegion1DailyMutation();
                Game1.showGlobalMessage(ModEntry.T("airship.region1.run.mutation.banner", new
                {
                    mutation = ModEntry.T($"airship.region1.run.mutation.{MutationKey(mutation)}.name")
                }));
            }
            string encounter = ModEntry.T($"airship.region1.run.encounter.{this.Region1RunEncounters[this.Region1RunStep].ToString().ToLowerInvariant()}");
''', 1)

# Reset advanced transient state.
reset_anchor = '''        this.Region1RunUnbankedScrap = 0;
        this.Region1RunUnbankedShiny = 0;
    }

    private GameLocation? BeginRegion1HuntRun()
'''
if reset_anchor not in s:
    raise RuntimeError('0666 reset anchor missing')
s = s.replace(reset_anchor, '''        this.Region1RunUnbankedScrap = 0;
        this.Region1RunUnbankedShiny = 0;
        this.Region1EliteAuraNextAtMs = 0;
        this.Region1RunRareRoomsSeen = 0;
    }

    private GameLocation? BeginRegion1HuntRun()
''', 1)

# Node rewards: rare-room payouts + mutation economy.
reward_anchor = '''        Region1RunRouteKind routeKind = this.Region1RunRouteKinds[this.Region1RunStep];
        Region1RunEncounterType encounter = this.Region1RunEncounters[this.Region1RunStep];

        if (routeKind is Region1RunRouteKind.Briar or Region1RunRouteKind.Ancient)
'''
if reward_anchor not in s:
    raise RuntimeError('0666 node reward anchor missing')
s = s.replace(reward_anchor, '''        Region1RunRouteKind routeKind = this.Region1RunRouteKinds[this.Region1RunStep];
        Region1RunEncounterType encounter = this.Region1RunEncounters[this.Region1RunStep];
        Region1DailyMutation mutation = this.ResolveRegion1DailyMutation();

        if (encounter is Region1RunEncounterType.LostCache or Region1RunEncounterType.Moonwell or Region1RunEncounterType.AncientEcho)
            this.Region1RunRareRoomsSeen++;

        switch (encounter)
        {
            case Region1RunEncounterType.LostCache:
                this.Region1RunUnbankedScrap += 4;
                this.Region1RunUnbankedShiny += 1;
                break;
            case Region1RunEncounterType.Moonwell:
                Game1.player.health = Math.Min(Game1.player.maxHealth, Game1.player.health + Math.Max(12, (int)Math.Round(Game1.player.maxHealth * 0.30d)));
                this.BankRegion1RunRewards("moonwell");
                break;
            case Region1RunEncounterType.AncientEcho:
                this.Region1RunUnbankedScrap += 3;
                this.Region1RunUnbankedShiny += 1;
                break;
        }

        switch (mutation)
        {
            case Region1DailyMutation.Overgrown:
                this.Region1RunUnbankedScrap++;
                break;
            case Region1DailyMutation.BriarBloom:
                if (encounter is Region1RunEncounterType.Elite or Region1RunEncounterType.RootNest or Region1RunEncounterType.AncientEcho)
                    this.Region1RunUnbankedScrap++;
                break;
            case Region1DailyMutation.MoonlitGrove:
                Random moonlit = new(unchecked(this.Region1RunSeed + nodeNumber * 2147483 + Game1.Date.TotalDays));
                if (moonlit.NextDouble() < 0.25d)
                    this.Region1RunUnbankedShiny++;
                break;
            case Region1DailyMutation.ChaoticResonance:
                if (encounter is Region1RunEncounterType.Elite or Region1RunEncounterType.AncientEcho)
                    this.Region1RunUnbankedScrap++;
                break;
        }

        if (routeKind is Region1RunRouteKind.Briar or Region1RunRouteKind.Ancient)
''', 1)

boon_anchor = '''        bool boonMilestone = nodeNumber == 2 || nodeNumber == 5 || nodeNumber == 8;
        if (boonMilestone || encounter == Region1RunEncounterType.Shrine)
'''
if boon_anchor not in s:
    raise RuntimeError('0666 boon milestone anchor missing')
s = s.replace(boon_anchor, '''        bool boonMilestone = nodeNumber == 2 || nodeNumber == 5 || nodeNumber == 8
            || (mutation == Region1DailyMutation.ChaoticResonance && (nodeNumber == 4 || nodeNumber == 7));
        if (boonMilestone || encounter == Region1RunEncounterType.Shrine)
''', 1)

# Rare-room roll layers over route encounters from node 4 onward.
roll_start = s.index('    private Region1RunEncounterType RollRegion1Encounter(Region1RunRouteKind route, int nodeIndex)\n')
roll_end = s.index('    private void AdvanceRegion1HuntRun(', roll_start)
new_roll = r'''    private Region1RunEncounterType RollRegion1Encounter(Region1RunRouteKind route, int nodeIndex)
    {
        Region1DailyMutation mutation = this.ResolveRegion1DailyMutation();
        Random random = new(unchecked(this.Region1RunSeed + (nodeIndex + 1) * 32452843 + (int)route * 49999));

        if (nodeIndex >= 3)
        {
            int rareChance = mutation switch
            {
                Region1DailyMutation.ChaoticResonance => 18,
                Region1DailyMutation.MoonlitGrove => 16,
                _ => 11
            };
            if (random.Next(100) < rareChance)
            {
                int rare = random.Next(100);
                return route switch
                {
                    Region1RunRouteKind.Ancient => rare < 45 ? Region1RunEncounterType.LostCache
                        : rare < 76 ? Region1RunEncounterType.Moonwell
                        : Region1RunEncounterType.AncientEcho,
                    Region1RunRouteKind.Briar => rare < 32 ? Region1RunEncounterType.LostCache
                        : rare < 50 ? Region1RunEncounterType.Moonwell
                        : Region1RunEncounterType.AncientEcho,
                    _ => rare < 44 ? Region1RunEncounterType.Moonwell
                        : rare < 82 ? Region1RunEncounterType.LostCache
                        : Region1RunEncounterType.AncientEcho,
                };
            }
        }

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

'''
s = s[:roll_start] + new_roll + s[roll_end:]

# Replace room population with elite affix + mutation-aware version while keeping 0666 candidate maps.
pop_start = s.index('    private void PopulateRegion1RunRoom(GameLocation location, int roomIndex)\n')
pop_end = s.index('    private static Monster CreateRegion1RunMonster(', pop_start)
old_pop = s[pop_start:pop_end]
# Reuse exact candidate table from current method to avoid map-coordinate drift.
table_start = old_pop.index('        Point[][] roomCandidates =\n')
table_end = old_pop.index('        int encounterSeed =', table_start)
candidate_table = old_pop[table_start:table_end]
new_pop = r'''    private void PopulateRegion1RunRoom(GameLocation location, int roomIndex)
    {
        this.ClearRegion1MarkedMonsters(location);
        this.Region1EliteAuraNextAtMs = 0;
        if (!this.Region1RunActive || this.Region1RunStep < 0 || this.Region1RunStep >= this.Region1RunEncounters.Length)
            return;

        Region1RunEncounterType encounter = this.Region1RunEncounters[this.Region1RunStep];
        if (encounter is Region1RunEncounterType.Shrine or Region1RunEncounterType.LostCache or Region1RunEncounterType.Moonwell)
        {
            this.Monitor.Log($"Region I Hunt Run node {this.Region1RunStep + 1}: {encounter}, no combat spawn.", LogLevel.Trace);
            return;
        }

''' + candidate_table + r'''        int encounterSeed = unchecked(this.Region1RunSeed + roomIndex * 104729 + Math.Max(0, this.Region1RunStep) * 8191);
        Random random = new(encounterSeed);
        Point[] shuffled = roomCandidates[roomIndex].OrderBy(_ => random.Next()).ToArray();
        bool eliteEncounter = encounter is Region1RunEncounterType.Elite or Region1RunEncounterType.AncientEcho;
        Region1EliteAffix eliteAffix = eliteEncounter ? this.RollRegion1EliteAffix(this.Region1RunStep) : Region1EliteAffix.ThornAura;
        int targetCount = encounter switch
        {
            Region1RunEncounterType.Combat => random.Next(5, 8),
            Region1RunEncounterType.Ambush => random.Next(8, 11),
            Region1RunEncounterType.Elite => 4,
            Region1RunEncounterType.RootNest => 6,
            Region1RunEncounterType.AncientEcho => 3,
            _ => 0
        };
        if (eliteEncounter && eliteAffix == Region1EliteAffix.Infested)
            targetCount += 2;
        if (this.ResolveRegion1DailyMutation() == Region1DailyMutation.CalmGrove && targetCount > 3)
            targetCount--;

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
            if (eliteEncounter && spawned == 0)
            {
                int baseHp = 210 + this.Region1RunStep * 16;
                if (encounter == Region1RunEncounterType.AncientEcho)
                    baseHp = (int)Math.Round(baseHp * 1.20d);
                GreenSlime elite = new(tileVector * 64f, 0) { MaxHealth = baseHp, Speed = 3 };
                elite.Health = elite.MaxHealth;
                elite.modData[Region1EliteMarkerKey] = "1";
                elite.modData[Region1EliteAffixMarkerKey] = eliteAffix.ToString();
                this.ApplyRegion1EliteAffix(elite, eliteAffix);
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
                if (eliteEncounter && eliteAffix == Region1EliteAffix.Resonant)
                {
                    monster.Speed += 1;
                    monster.MaxHealth = Math.Max(1, (int)Math.Round(monster.MaxHealth * 1.15d));
                    monster.Health = monster.MaxHealth;
                }
            }

            monster.modData[Region1MonsterMarkerKey] = "huntrun2";
            this.ApplyRegion1DailyMutationToMonster(monster);
            location.characters.Add(monster);
            spawned++;
        }

        this.Monitor.Log(
            $"Region I Hunt Run 2.0 node {this.Region1RunStep + 1}/{this.Region1RunTargetNodes}: room={roomIndex + 1}, encounter={encounter}, eliteAffix={(eliteEncounter ? eliteAffix : "none")}, mutation={this.ResolveRegion1DailyMutation()}, spawned={spawned}.",
            LogLevel.Trace
        );
    }

    private Region1EliteAffix RollRegion1EliteAffix(int nodeIndex)
    {
        Region1EliteAffix[] pool = Enum.GetValues<Region1EliteAffix>();
        int seed = unchecked(this.Region1RunSeed + (nodeIndex + 1) * 67867967 + Game1.Date.TotalDays * 97);
        return pool[new Random(seed).Next(pool.Length)];
    }

    private void ApplyRegion1EliteAffix(Monster elite, Region1EliteAffix affix)
    {
        switch (affix)
        {
            case Region1EliteAffix.ThornAura:
                elite.MaxHealth = Math.Max(1, (int)Math.Round(elite.MaxHealth * 1.10d));
                break;
            case Region1EliteAffix.Swift:
                elite.Speed += 2;
                break;
            case Region1EliteAffix.Regrowth:
                elite.MaxHealth = Math.Max(1, (int)Math.Round(elite.MaxHealth * 1.15d));
                break;
            case Region1EliteAffix.Bulwark:
                elite.MaxHealth = Math.Max(1, (int)Math.Round(elite.MaxHealth * 1.60d));
                elite.Speed = Math.Max(1, elite.Speed - 1);
                break;
            case Region1EliteAffix.Infested:
                elite.MaxHealth = Math.Max(1, (int)Math.Round(elite.MaxHealth * 1.15d));
                break;
            case Region1EliteAffix.Resonant:
                elite.MaxHealth = Math.Max(1, (int)Math.Round(elite.MaxHealth * 1.25d));
                break;
        }
        elite.Health = elite.MaxHealth;
    }

    private void ApplyRegion1DailyMutationToMonster(Monster monster)
    {
        Region1DailyMutation mutation = this.ResolveRegion1DailyMutation();
        bool rootNest = monster.modData.ContainsKey(Region1RootNestMarkerKey);
        bool elite = monster.modData.ContainsKey(Region1EliteMarkerKey);
        double hpScale = mutation switch
        {
            Region1DailyMutation.CalmGrove => 0.90d,
            Region1DailyMutation.BriarBloom when elite || rootNest => 1.20d,
            Region1DailyMutation.Overgrown => 1.15d,
            Region1DailyMutation.ChaoticResonance => 1.10d,
            _ => 1.00d
        };
        monster.MaxHealth = Math.Max(1, (int)Math.Round(monster.MaxHealth * hpScale));
        monster.Health = monster.MaxHealth;

        if (!rootNest && mutation == Region1DailyMutation.MoonlitGrove && monster is Bat)
            monster.Speed += 1;
        if (!rootNest && mutation == Region1DailyMutation.ChaoticResonance)
            monster.Speed += 1;
    }

    private void UpdateRegion1EliteAffixes(GameLocation room, long now)
    {
        foreach (Monster elite in room.characters.OfType<Monster>().Where(m => m.Health > 0 && m.modData.ContainsKey(Region1EliteMarkerKey)))
        {
            if (!elite.modData.TryGetValue(Region1EliteAffixMarkerKey, out string? raw)
                || !Enum.TryParse(raw, ignoreCase: true, out Region1EliteAffix affix))
            {
                continue;
            }

            if (affix == Region1EliteAffix.Regrowth && elite.Health < elite.MaxHealth)
            {
                int heal = Math.Max(2, elite.MaxHealth / 40);
                elite.Health = Math.Min(elite.MaxHealth, elite.Health + heal);
            }

            if (affix == Region1EliteAffix.ThornAura && now >= this.Region1EliteAuraNextAtMs)
            {
                Vector2 eliteCenter = elite.Position + new Vector2(32f, 32f);
                Vector2 playerCenter = Game1.player.Position + new Vector2(32f, 32f);
                if (Vector2.Distance(eliteCenter, playerCenter) <= 112f)
                {
                    this.Region1EliteAuraNextAtMs = now + 1200L;
                    Game1.player.takeDamage(3, false, elite);
                    Game1.playSound("leafrustle");
                }
            }
        }
    }

    private Region1DailyMutation ResolveRegion1DailyMutation()
    {
        Region1DailyMutation[] values = Enum.GetValues<Region1DailyMutation>();
        int seed = unchecked((int)Game1.uniqueIDForThisGame + Game1.Date.TotalDays * 1009 + 17041);
        int index = (int)((uint)seed % (uint)values.Length);
        return values[index];
    }

    private static string MutationKey(Region1DailyMutation mutation) => mutation switch
    {
        Region1DailyMutation.CalmGrove => "calm_grove",
        Region1DailyMutation.BriarBloom => "briar_bloom",
        Region1DailyMutation.MoonlitGrove => "moonlit_grove",
        Region1DailyMutation.Overgrown => "overgrown",
        _ => "chaotic_resonance"
    };

    private static string EliteAffixKey(Region1EliteAffix affix) => affix switch
    {
        Region1EliteAffix.ThornAura => "thorn_aura",
        Region1EliteAffix.Swift => "swift",
        Region1EliteAffix.Regrowth => "regrowth",
        Region1EliteAffix.Bulwark => "bulwark",
        Region1EliteAffix.Infested => "infested",
        _ => "resonant"
    };

'''
s = s[:pop_start] + new_pop + s[pop_end:]

# Debug/status includes today's mutation, rare count and current elite affix.
desc_anchor = '''        return $"HuntRun2 Active={this.Region1RunActive} | Node={Math.Max(0, this.Region1RunStep + 1)}/{this.Region1RunTargetNodes} | " +
               $"Encounter={encounter} | Route={route} | Boons=[{string.Join(',', this.Region1RunBoons)}] | " +
               $"AwaitingBoon={this.Region1RunAwaitingBoon} | Unbanked={this.Region1RunUnbankedScrap} Scrap + {this.Region1RunUnbankedShiny} Shiny | " +
               $"BossBranch={(this.Region1RunStep + 1 >= Region1BossBranchMinNode)} | Seed={this.Region1RunSeed}";
    }
'''
if desc_anchor not in s:
    raise RuntimeError('0666 hunt status anchor missing')
s = s.replace(desc_anchor, '''        string affix = "none";
        Monster? elite = Game1.currentLocation?.characters.OfType<Monster>().FirstOrDefault(m => m.Health > 0 && m.modData.ContainsKey(Region1EliteMarkerKey));
        if (elite is not null && elite.modData.TryGetValue(Region1EliteAffixMarkerKey, out string? currentAffix))
            affix = currentAffix;
        Region1DailyMutation mutation = this.ResolveRegion1DailyMutation();
        return $"HuntRun2 Active={this.Region1RunActive} | Node={Math.Max(0, this.Region1RunStep + 1)}/{this.Region1RunTargetNodes} | " +
               $"Encounter={encounter} | Route={route} | Mutation={mutation} | EliteAffix={affix} | RareSeen={this.Region1RunRareRoomsSeen} | " +
               $"Boons=[{string.Join(',', this.Region1RunBoons)}] | AwaitingBoon={this.Region1RunAwaitingBoon} | " +
               $"Unbanked={this.Region1RunUnbankedScrap} Scrap + {this.Region1RunUnbankedShiny} Shiny | " +
               $"BossBranch={(this.Region1RunStep + 1 >= Region1BossBranchMinNode)} | Seed={this.Region1RunSeed}";
    }

    public string DescribeHuntAdvanced()
    {
        if (!Context.IsWorldReady)
            return "HuntRunAdvanced=<no save>";
        Region1DailyMutation mutation = this.ResolveRegion1DailyMutation();
        return $"DailyMutation={mutation} | Name={ModEntry.T($"airship.region1.run.mutation.{MutationKey(mutation)}.name")} | " +
               $"RareRoomsSeen={this.Region1RunRareRoomsSeen} | Run={this.DescribeHuntRun2()}";
    }
''', 1)

# Overlay: mutation badge, elite affix marker, rare-room identity.
draw_anchor = '''        if (!this.Region1RunActive || this.Region1RunStep < 0 || this.Region1RunStep >= this.Region1RunTargetNodes)
            return;

        foreach (Monster nest in room.characters.OfType<Monster>().Where(m => m.Health > 0 && m.modData.ContainsKey(Region1RootNestMarkerKey)))
'''
if draw_anchor not in s:
    raise RuntimeError('0666 draw overlay anchor missing')
s = s.replace(draw_anchor, '''        if (!this.Region1RunActive || this.Region1RunStep < 0 || this.Region1RunStep >= this.Region1RunTargetNodes)
            return;

        Region1DailyMutation mutation = this.ResolveRegion1DailyMutation();
        string mutationLabel = "MUTATION • " + ModEntry.T($"airship.region1.run.mutation.{MutationKey(mutation)}.name");
        batch.DrawString(Game1.smallFont, mutationLabel, new Vector2(24f, 78f), new Color(208, 235, 184));

        foreach (Monster elite in room.characters.OfType<Monster>().Where(m => m.Health > 0 && m.modData.ContainsKey(Region1EliteMarkerKey)))
        {
            if (!elite.modData.TryGetValue(Region1EliteAffixMarkerKey, out string? raw)
                || !Enum.TryParse(raw, ignoreCase: true, out Region1EliteAffix affix))
            {
                continue;
            }
            Point tile = new((int)(elite.Position.X / 64f), (int)(elite.Position.Y / 64f));
            DrawRunChoiceMarker(batch, tile, EliteAffixColor(affix), ModEntry.T($"airship.region1.run.affix.{EliteAffixKey(affix)}.name"));
        }

        Region1RunEncounterType currentEncounter = this.Region1RunEncounters[this.Region1RunStep];
        if (currentEncounter is Region1RunEncounterType.LostCache or Region1RunEncounterType.Moonwell or Region1RunEncounterType.AncientEcho)
        {
            int width = room.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 28;
            int height = room.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 20;
            Point rareTile = new(width / 2, Math.Max(5, height / 2));
            DrawRunChoiceMarker(batch, rareTile, RareEncounterColor(currentEncounter), ModEntry.T($"airship.region1.run.rare.{currentEncounter.ToString().ToLowerInvariant()}.name"));
        }

        foreach (Monster nest in room.characters.OfType<Monster>().Where(m => m.Health > 0 && m.modData.ContainsKey(Region1RootNestMarkerKey)))
''', 1)

route_color_anchor = '''    private static Color RouteColor(Region1RunRouteKind route) => route switch
    {
        Region1RunRouteKind.Moss => new Color(113, 198, 118),
        Region1RunRouteKind.Briar => new Color(202, 117, 104),
        _ => new Color(139, 177, 224)
    };
'''
if route_color_anchor not in s:
    raise RuntimeError('route color anchor missing')
s = s.replace(route_color_anchor, route_color_anchor + '''

    private static Color EliteAffixColor(Region1EliteAffix affix) => affix switch
    {
        Region1EliteAffix.ThornAura => new Color(211, 104, 112),
        Region1EliteAffix.Swift => new Color(235, 218, 108),
        Region1EliteAffix.Regrowth => new Color(107, 220, 129),
        Region1EliteAffix.Bulwark => new Color(145, 169, 184),
        Region1EliteAffix.Infested => new Color(191, 131, 215),
        _ => new Color(95, 210, 202)
    };

    private static Color RareEncounterColor(Region1RunEncounterType encounter) => encounter switch
    {
        Region1RunEncounterType.LostCache => new Color(232, 199, 94),
        Region1RunEncounterType.Moonwell => new Color(116, 181, 236),
        _ => new Color(184, 125, 229)
    };
''', 1)

p.write_text(s, encoding='utf-8')

# ---------------- i18n ----------------
def update_json(path: Path, values: dict):
    data = json.loads(path.read_text(encoding='utf-8'))
    data.update(values)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

update_json(ROOT/'i18n/default.json', {
    'airship.region1.run.mutation.banner': 'DAILY MUTATION • {{mutation}}',
    'airship.region1.run.mutation.calm_grove.name': 'Calm Grove',
    'airship.region1.run.mutation.calm_grove.desc': 'Enemies have 10% less HP and encounters contain slightly fewer monsters.',
    'airship.region1.run.mutation.briar_bloom.name': 'Briar Bloom',
    'airship.region1.run.mutation.briar_bloom.desc': 'Elite and Root Nest targets gain 20% HP, but dangerous nodes grant +1 route Scrap.',
    'airship.region1.run.mutation.moonlit_grove.name': 'Moonlit Grove',
    'airship.region1.run.mutation.moonlit_grove.desc': 'Bats move faster, rare rooms appear more often, and each cleared node has a 25% Shiny Scrap chance.',
    'airship.region1.run.mutation.overgrown.name': 'Overgrown Day',
    'airship.region1.run.mutation.overgrown.desc': 'Enemies gain 15% HP, but every cleared node grants +1 route Scrap.',
    'airship.region1.run.mutation.chaotic_resonance.name': 'Chaotic Resonance',
    'airship.region1.run.mutation.chaotic_resonance.desc': 'Enemies gain 10% HP and speed, rare rooms are more common, and extra boon milestones appear at nodes 4 and 7.',
    'airship.region1.run.affix.thorn_aura.name': 'THORN AURA',
    'airship.region1.run.affix.thorn_aura.desc': 'Deals 3 damage to farmers who remain too close; 1.2s pulse cooldown.',
    'airship.region1.run.affix.swift.name': 'SWIFT',
    'airship.region1.run.affix.swift.desc': 'The Elite moves much faster.',
    'airship.region1.run.affix.regrowth.name': 'REGROWTH',
    'airship.region1.run.affix.regrowth.desc': 'The Elite regenerates a small amount of HP every second.',
    'airship.region1.run.affix.bulwark.name': 'BULWARK',
    'airship.region1.run.affix.bulwark.desc': 'The Elite has 60% more HP but moves slightly slower.',
    'airship.region1.run.affix.infested.name': 'INFESTED',
    'airship.region1.run.affix.infested.desc': 'The Elite arrives with two additional monsters.',
    'airship.region1.run.affix.resonant.name': 'RESONANT',
    'airship.region1.run.affix.resonant.desc': 'The Elite is tougher and strengthens the HP and speed of its escort.',
    'airship.region1.run.encounter.lostcache': 'RARE • Lost Cache',
    'airship.region1.run.encounter.moonwell': 'RARE • Moonwell',
    'airship.region1.run.encounter.ancientecho': 'RARE • Ancient Echo',
    'airship.region1.run.rare.lostcache.name': 'LOST CACHE',
    'airship.region1.run.rare.lostcache.desc': 'A forgotten supply cache. Clear reward: +4 Scrap and +1 Shiny Scrap.',
    'airship.region1.run.rare.moonwell.name': 'MOONWELL',
    'airship.region1.run.rare.moonwell.desc': 'A quiet Verdant spring. Restores 30% Max HP and immediately banks current route rewards.',
    'airship.region1.run.rare.ancientecho.name': 'ANCIENT ECHO',
    'airship.region1.run.rare.ancientecho.desc': 'A stronger affixed Elite encounter. Clear reward: +3 Scrap and +1 Shiny Scrap.'
})
update_json(ROOT/'i18n/vi.json', {
    'airship.region1.run.mutation.banner': 'BIẾN DỊ HÔM NAY • {{mutation}}',
    'airship.region1.run.mutation.calm_grove.name': 'Khu Rừng Yên Ả',
    'airship.region1.run.mutation.calm_grove.desc': 'Quái có ít hơn 10% HP và mỗi encounter có ít quái hơn một chút.',
    'airship.region1.run.mutation.briar_bloom.name': 'Gai Nở Rộ',
    'airship.region1.run.mutation.briar_bloom.desc': 'Elite và Root Nest có thêm 20% HP, nhưng node nguy hiểm thưởng thêm 1 Scrap trong run.',
    'airship.region1.run.mutation.moonlit_grove.name': 'Rừng Dưới Trăng',
    'airship.region1.run.mutation.moonlit_grove.desc': 'Bat nhanh hơn, rare room xuất hiện nhiều hơn và mỗi node đã clear có 25% cơ hội nhận Shiny Scrap.',
    'airship.region1.run.mutation.overgrown.name': 'Rừng Mọc Tràn',
    'airship.region1.run.mutation.overgrown.desc': 'Quái có thêm 15% HP, nhưng mỗi node đã clear thưởng thêm 1 Scrap trong run.',
    'airship.region1.run.mutation.chaotic_resonance.name': 'Cộng Hưởng Hỗn Loạn',
    'airship.region1.run.mutation.chaotic_resonance.desc': 'Quái có thêm 10% HP và tốc độ, rare room thường gặp hơn, đồng thời có thêm mốc boon ở node 4 và 7.',
    'airship.region1.run.affix.thorn_aura.name': 'HÀO QUANG GAI',
    'airship.region1.run.affix.thorn_aura.desc': 'Gây 3 sát thương nếu farmer đứng quá gần; mỗi 1,2 giây mới phát xung một lần.',
    'airship.region1.run.affix.swift.name': 'NHANH NHẸN',
    'airship.region1.run.affix.swift.desc': 'Elite di chuyển nhanh hơn đáng kể.',
    'airship.region1.run.affix.regrowth.name': 'TÁI SINH',
    'airship.region1.run.affix.regrowth.desc': 'Elite hồi một lượng HP nhỏ mỗi giây.',
    'airship.region1.run.affix.bulwark.name': 'THÀNH LŨY',
    'airship.region1.run.affix.bulwark.desc': 'Elite có thêm 60% HP nhưng di chuyển chậm hơn một chút.',
    'airship.region1.run.affix.infested.name': 'NHIỄM ĐÀN',
    'airship.region1.run.affix.infested.desc': 'Elite xuất hiện cùng thêm hai quái hộ tống.',
    'airship.region1.run.affix.resonant.name': 'CỘNG HƯỞNG',
    'airship.region1.run.affix.resonant.desc': 'Elite cứng cáp hơn và tăng HP lẫn tốc độ cho quái hộ tống.',
    'airship.region1.run.encounter.lostcache': 'HIẾM • Kho Đồ Thất Lạc',
    'airship.region1.run.encounter.moonwell': 'HIẾM • Giếng Trăng',
    'airship.region1.run.encounter.ancientecho': 'HIẾM • Vọng Âm Cổ Đại',
    'airship.region1.run.rare.lostcache.name': 'KHO ĐỒ THẤT LẠC',
    'airship.region1.run.rare.lostcache.desc': 'Một kho tiếp tế bị bỏ quên. Thưởng khi clear: +4 Scrap và +1 Shiny Scrap.',
    'airship.region1.run.rare.moonwell.name': 'GIẾNG TRĂNG',
    'airship.region1.run.rare.moonwell.desc': 'Một mạch nước Verdant yên tĩnh. Hồi 30% Max HP và bank ngay phần thưởng route hiện tại.',
    'airship.region1.run.rare.ancientecho.name': 'VỌNG ÂM CỔ ĐẠI',
    'airship.region1.run.rare.ancientecho.desc': 'Một Elite có affix mạnh hơn. Thưởng khi clear: +3 Scrap và +1 Shiny Scrap.'
})

# ---------------- ModEntry ----------------
mod_path = ROOT/'ModEntry.cs'
mod = mod_path.read_text(encoding='utf-8')
cmd_anchor = '        helper.ConsoleCommands.Add("cardcha_huntrun_status", "Show Region I Hunt Run 2.0 route/boon/checkpoint state.", (_, _) => this.Monitor.Log(this.Airship.DescribeHuntRun2(), LogLevel.Alert));\n'
if cmd_anchor not in mod:
    raise RuntimeError('huntrun status command anchor missing')
mod = mod.replace(cmd_anchor, cmd_anchor + '        helper.ConsoleCommands.Add("cardcha_huntrun_daily", "Show today\'s Region I mutation, Elite affix and rare-room state.", (_, _) => this.Monitor.Log(this.Airship.DescribeHuntAdvanced(), LogLevel.Alert));\n', 1)
mod = mod.replace('0.3.0-alpha.28.0.4.14.4.5.12.33 REGION I HUNT RUN 2.0 FOUNDATION TEST',
                  '0.3.0-alpha.28.0.4.14.4.5.12.34 HUNT RUN 2.0 ADVANCED LAYER TEST', 1)
mod_path.write_text(mod, encoding='utf-8')

# ---------------- handoff ----------------
Path('handoff/ALPHA28_0667_HUNTRUN2_ADVANCED_LAYER.md').write_text(f'''# Alpha28 0667 - Hunt Run 2.0 Advanced Layer\n\nBuild: `{VERSION}`\nBranch: `cardcha-alpha28-0667-huntrun2-advanced-layer`\nStatus: implementation candidate; in-game acceptance pending for 0660-0667.\n\n## Elite Affixes\n- Thorn Aura: proximity pulse, 3 damage, 1.2s cooldown.\n- Swift: +2 Speed.\n- Regrowth: heals every second.\n- Bulwark: +60% HP, slightly slower.\n- Infested: +2 escorts.\n- Resonant: tougher Elite; escorts gain +15% HP and +1 Speed.\n- Affixes are deterministic per run seed/node and are shown above the Elite.\n\n## Daily Mutation\nOne deterministic Region I mutation per save-day, shared by every run that day:\n- Calm Grove: -10% enemy HP, slightly fewer enemies.\n- Briar Bloom: Elite/Root Nest +20% HP, dangerous nodes +1 route Scrap.\n- Moonlit Grove: faster Bats, 25% Shiny chance per clear, more rare rooms.\n- Overgrown Day: +15% enemy HP, +1 route Scrap per clear.\n- Chaotic Resonance: +10% HP/+1 Speed, more rare rooms, extra boon milestones at nodes 4 and 7.\n\n## Advanced Rare Rooms\nStarting from node 4, route rolls can create:\n- Lost Cache: no combat; +4 Scrap +1 Shiny.\n- Moonwell: no combat; heal 30% Max HP and bank current route rewards.\n- Ancient Echo: affixed Elite; +3 Scrap +1 Shiny.\nBase rare chance is 11%, Moonlit 16%, Chaotic 18%. Route type weights which rare room appears.\n\n## Preserved\n- Hunt Run remains 7-10 nodes with checkpoints 3/6, Boss branch from node 7, Extract, 1-of-3 boons.\n- Monsters still feed Scrap pipeline; no finished-card drops.\n- Save schema 19 unchanged.\n- Boss I 0660-0665, Verdant Core, Guardian Rabbit, Airship, MiMi/stair/profile/CC, 76 active-card audit unchanged.\n''', encoding='utf-8')
Path('handoff/LATEST_CARDCHA_HANDOFF.md').write_text(f'''# Latest Cardcha handoff\n\nCurrent branch: `cardcha-alpha28-0667-huntrun2-advanced-layer`\nCurrent build: `{VERSION}`\n\nContinue from:\n`handoff/ALPHA28_0667_HUNTRUN2_ADVANCED_LAYER.md`\n\nDo not resume from stale `main`. In-game acceptance remains pending for 0660-0667.\n''', encoding='utf-8')

print(json.dumps({
    'version': VERSION,
    'eliteAffixes': 6,
    'dailyMutations': 5,
    'advancedRareRooms': 3,
    'runNodes': '7-10',
    'schema': 19
}, indent=2))
