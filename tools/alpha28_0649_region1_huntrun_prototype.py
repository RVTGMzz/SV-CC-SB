from pathlib import Path

ROOT = Path("src/Cardcha")
SERVICE = ROOT / "Services/AirshipFoundationService.cs"
OLD_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.16"
NEW_VERSION = "0.3.0-alpha.28.0.4.14.4.5.12.17"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def patch_versions() -> None:
    for rel in ["manifest.json", "Cardcha.csproj", "Directory.Build.targets"]:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        if OLD_VERSION not in text:
            raise RuntimeError(f"{rel}: old version not found")
        path.write_text(text.replace(OLD_VERSION, NEW_VERSION), encoding="utf-8")


def add_i18n(path: Path, values: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8")
    if '"airship.region1.run.enter"' in text:
        return
    stripped = text.rstrip()
    if not stripped.endswith("}"):
        raise RuntimeError(f"{path}: expected JSON object")
    body = stripped[:-1].rstrip()
    lines = []
    for key, value in values.items():
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'  "{key}": "{escaped}"')
    path.write_text(body + ",\n" + ",\n".join(lines) + "\n}\n", encoding="utf-8")


def csv_layer(grid: list[list[int]]) -> str:
    return "\n".join(",".join(str(v) for v in row) + "," for row in grid)


def make_room_tmx(room_index: int, room_slug: str) -> str:
    width, height = 28, 20
    grass, accent, path = 381, 382, 457
    back = [[grass for _ in range(width)] for _ in range(height)]
    buildings = [[0 for _ in range(width)] for _ in range(height)]
    front = [[0 for _ in range(width)] for _ in range(height)]
    cx = width // 2

    # Stable authored border with two-tile north/south doorways.
    for x in range(width):
        if x not in (cx - 1, cx):
            buildings[0][x] = grass
            buildings[height - 1][x] = grass
    for y in range(height):
        buildings[y][0] = grass
        buildings[y][width - 1] = grass

    # Small grass variation so the six vanilla-tile rooms aren't carbon copies.
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if (x * 17 + y * 31 + room_index * 13) % 29 == 0:
                back[y][x] = accent

    def paint_path(cells):
        for x, y in cells:
            if 0 <= x < width and 0 <= y < height:
                back[y][x] = path

    def block(cells):
        for x, y in cells:
            if 1 <= x < width - 1 and 1 <= y < height - 1:
                buildings[y][x] = grass

    # Each room keeps a readable south -> north combat lane while using a different authored shape.
    if room_index == 0:  # Verdant Clearing
        paint_path((x, y) for y in range(4, 16) for x in range(6, 22) if ((x - cx) ** 2) / 80 + ((y - 10) ** 2) / 28 <= 1)
        block([(3, 4), (4, 4), (3, 5), (23, 4), (24, 4), (24, 5), (4, 15), (5, 15), (23, 15), (24, 15)])
    elif room_index == 1:  # Moss Creek
        for y in range(1, height - 1):
            bend = cx + (2 if (y // 4) % 2 == 0 else -2)
            paint_path((x, y) for x in range(bend - 2, bend + 3))
        block([(5, 6), (6, 6), (7, 6), (20, 6), (21, 6), (22, 6), (5, 13), (6, 13), (21, 13), (22, 13)])
    elif room_index == 2:  # Old Ruins
        paint_path((x, y) for y in range(3, 17) for x in range(9, 19))
        block([(5, 5), (6, 5), (5, 6), (21, 5), (22, 5), (22, 6), (5, 14), (6, 14), (21, 14), (22, 14),
               (9, 8), (10, 8), (17, 8), (18, 8), (9, 12), (10, 12), (17, 12), (18, 12)])
    elif room_index == 3:  # Briar Thicket
        for y in range(1, height - 1):
            lane = cx + ((y % 6) - 3)
            paint_path((x, y) for x in range(max(2, lane - 2), min(width - 2, lane + 3)))
        block([(4, y) for y in range(4, 9)] + [(23, y) for y in range(10, 15)] + [(8, 5), (19, 14), (7, 15), (20, 4)])
    elif room_index == 4:  # Hollow Grove
        paint_path((x, y) for y in range(3, 17) for x in range(7, 21) if abs(x - cx) + abs(y - 10) >= 4)
        block([(10, 7), (11, 7), (16, 7), (17, 7), (10, 13), (11, 13), (16, 13), (17, 13),
               (7, 9), (7, 10), (20, 9), (20, 10)])
    else:  # Card Shrine
        paint_path((x, y) for y in range(1, height - 1) for x in range(cx - 2, cx + 2))
        paint_path((x, y) for y in range(8, 12) for x in range(5, 23))
        block([(8, 7), (9, 7), (18, 7), (19, 7), (8, 12), (9, 12), (18, 12), (19, 12),
               (12, 9), (15, 9), (12, 10), (15, 10)])

    # Keep interaction approach tiles guaranteed clear.
    for y in (1, 2, height - 3, height - 2):
        for x in (cx - 1, cx):
            buildings[y][x] = 0
            back[y][x] = path

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" renderorder="right-down" width="{width}" height="{height}" tilewidth="16" tileheight="16" infinite="0" nextlayerid="4" nextobjectid="1">
 <properties>
  <property name="Outdoors" value="T" />
  <property name="CardchaRegionVersion" value="alpha.28.0.4.14.4.5.12.17" />
  <property name="CardchaRegionRole" value="region1-huntrun-room|room-{room_index + 1}|{room_slug}" />
  <property name="CardchaAssetPolicy" value="cardcha-owned-map|vanilla-tiles-only|no-third-party-assets" />
 </properties>
 <tileset firstgid="1" name="spring_outdoorsTileSheet" tilewidth="16" tileheight="16" tilecount="1975" columns="25">
  <image source=".spring_outdoorsTileSheet.png" width="400" height="1264" />
 </tileset>
 <layer id="1" name="Back" width="{width}" height="{height}">
  <data encoding="csv">
{csv_layer(back)}
</data>
 </layer>
 <layer id="2" name="Buildings" width="{width}" height="{height}">
  <data encoding="csv">
{csv_layer(buildings)}
</data>
 </layer>
 <layer id="3" name="Front" width="{width}" height="{height}">
  <data encoding="csv">
{csv_layer(front)}
</data>
 </layer>
</map>
'''


def generate_rooms() -> None:
    out = ROOT / "assets/region1_rooms"
    out.mkdir(parents=True, exist_ok=True)
    slugs = ["verdant-clearing", "moss-creek", "old-ruins", "briar-thicket", "hollow-grove", "card-shrine"]
    for i, slug in enumerate(slugs):
        (out / f"room_{i + 1}_{slug.replace('-', '_')}.tmx").write_text(make_room_tmx(i, slug), encoding="utf-8")


def patch_service() -> None:
    text = SERVICE.read_text(encoding="utf-8")

    text = replace_once(
        text,
        '    private const string Region1MapPath = "assets/region1_hunting.tmx";\n    private const string AirshipVisualPath = "assets/airship_visual.png";',
        '''    private const string Region1MapPath = "assets/region1_hunting.tmx";
    private const int Region1RunRoomCount = 4;
    private static readonly string[] Region1RunRoomLocationNames =
    {
        "Cardcha_R1_VerdantClearing",
        "Cardcha_R1_MossCreek",
        "Cardcha_R1_OldRuins",
        "Cardcha_R1_BriarThicket",
        "Cardcha_R1_HollowGrove",
        "Cardcha_R1_CardShrine",
    };
    private static readonly string[] Region1RunRoomMapAssetNames =
    {
        "Maps/Cardcha_R1_VerdantClearing",
        "Maps/Cardcha_R1_MossCreek",
        "Maps/Cardcha_R1_OldRuins",
        "Maps/Cardcha_R1_BriarThicket",
        "Maps/Cardcha_R1_HollowGrove",
        "Maps/Cardcha_R1_CardShrine",
    };
    private static readonly string[] Region1RunRoomMapPaths =
    {
        "assets/region1_rooms/room_1_verdant_clearing.tmx",
        "assets/region1_rooms/room_2_moss_creek.tmx",
        "assets/region1_rooms/room_3_old_ruins.tmx",
        "assets/region1_rooms/room_4_briar_thicket.tmx",
        "assets/region1_rooms/room_5_hollow_grove.tmx",
        "assets/region1_rooms/room_6_card_shrine.tmx",
    };
    private static readonly string[] Region1RunRoomNameKeys =
    {
        "airship.region1.run.room.0",
        "airship.region1.run.room.1",
        "airship.region1.run.room.2",
        "airship.region1.run.room.3",
        "airship.region1.run.room.4",
        "airship.region1.run.room.5",
    };
    private const string AirshipVisualPath = "assets/airship_visual.png";''',
        "room constants",
    )

    text = replace_once(
        text,
        '    private GameLocation? SkyDockDecorAppliedLocation;\n',
        '''    private GameLocation? SkyDockDecorAppliedLocation;
    private int[] Region1RunRoute = Array.Empty<int>();
    private int Region1RunStep = -1;
    private int Region1RunSeed;
    private bool Region1RunActive;
    private bool Region1RunCompleted;
''',
        "run fields",
    )

    text = replace_once(
        text,
        '''        if (e.NameWithoutLocale.IsEquivalentTo(Region1MapAssetName))
            e.LoadFromModFile<xTile.Map>(Region1MapPath, AssetLoadPriority.Exclusive);
''',
        '''        for (int i = 0; i < Region1RunRoomMapAssetNames.Length; i++)
        {
            if (!e.NameWithoutLocale.IsEquivalentTo(Region1RunRoomMapAssetNames[i]))
                continue;

            e.LoadFromModFile<xTile.Map>(Region1RunRoomMapPaths[i], AssetLoadPriority.Exclusive);
            return;
        }

        if (e.NameWithoutLocale.IsEquivalentTo(Region1MapAssetName))
            e.LoadFromModFile<xTile.Map>(Region1MapPath, AssetLoadPriority.Exclusive);
''',
        "asset request",
    )

    text = replace_once(
        text,
        '''        this.EnsureRegion1Location();
        this.MigrateUnlockFromExistingStory();
        this.FlybyArmAfterMs = Environment.TickCount64 + FlybyArmDelayMs;
''',
        '''        this.EnsureRegion1Location();
        this.EnsureRegion1RunRoomLocations();
        this.ResetRegion1RunState();
        this.MigrateUnlockFromExistingStory();
        this.FlybyArmAfterMs = Environment.TickCount64 + FlybyArmDelayMs;
''',
        "save loaded rooms",
    )

    text = replace_once(
        text,
        '''        this.EnsureRegion1Location();
        this.MigrateUnlockFromExistingStory();
        this.FlybyArmAfterMs = Environment.TickCount64 + 1500L;
''',
        '''        this.EnsureRegion1Location();
        this.EnsureRegion1RunRoomLocations();
        this.ResetRegion1RunState();
        this.MigrateUnlockFromExistingStory();
        this.FlybyArmAfterMs = Environment.TickCount64 + 1500L;
''',
        "day started rooms",
    )

    text = replace_once(
        text,
        '''        this.DeckDecorAppliedLocation = null;
        this.SkyDockDecorAppliedLocation = null;
    }
''',
        '''        this.DeckDecorAppliedLocation = null;
        this.SkyDockDecorAppliedLocation = null;
        this.ResetRegion1RunState();
    }
''',
        "returned title reset",
    )

    text = replace_once(
        text,
        '''        if (location.NameOrUniqueName.Equals(Region1LocationName, StringComparison.OrdinalIgnoreCase))
        {
            this.HandleRegion1Interaction(e, location);
            return;
        }

        if (!location.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase))
''',
        '''        if (location.NameOrUniqueName.Equals(Region1LocationName, StringComparison.OrdinalIgnoreCase))
        {
            this.HandleRegion1Interaction(e, location);
            return;
        }

        if (TryGetRegion1RunRoomIndex(location, out _))
        {
            this.HandleRegion1RunRoomInteraction(e, location);
            return;
        }

        if (!location.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase))
''',
        "room input routing",
    )

    old_warped = '''    public void OnWarped(object? sender, WarpedEventArgs e)
    {
        if (!Context.IsWorldReady
            || !Context.IsMainPlayer
            || !e.NewLocation.NameOrUniqueName.Equals(Region1LocationName, StringComparison.OrdinalIgnoreCase)
            || e.OldLocation?.NameOrUniqueName.Equals(Region1LocationName, StringComparison.OrdinalIgnoreCase) == true)
        {
            return;
        }

        this.PopulateRegion1(e.NewLocation);
    }
'''
    new_warped = '''    public void OnWarped(object? sender, WarpedEventArgs e)
    {
        if (!Context.IsWorldReady || !Context.IsMainPlayer)
            return;

        if (TryGetRegion1RunRoomIndex(e.NewLocation, out int roomIndex))
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

        if (e.OldLocation?.NameOrUniqueName.Equals(Region1LocationName, StringComparison.OrdinalIgnoreCase) == true)
            return;

        this.PopulateRegion1(e.NewLocation);
    }
'''
    text = replace_once(text, old_warped, new_warped, "warped hunt routing")

    text = replace_once(
        text,
        '''        if (this.EnsureRegion1Location() is null)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.region1.unavailable"));
            return;
        }
''',
        '''        if (this.EnsureRegion1Location() is null || !this.EnsureRegion1RunRoomLocations())
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.region1.unavailable"));
            return;
        }
''',
        "departure validation",
    )

    old_flight = '''                GameLocation? region = this.EnsureRegion1Location();
                if (region is null)
                {
                    // Target was validated before charging; this is a last-resort failure path.
                    this.FlightCutsceneActive = false;
                    this.ReturnToSkyDockExterior();
                    Game1.drawObjectDialogue(ModEntry.T("airship.region1.unavailable"));
                    return;
                }

                Point arrival = ResolveRegion1ArrivalTile(region);
                this.WarpGraceUntilMs = Environment.TickCount64 + 850L;
                Game1.warpFarmer(Region1LocationName, arrival.X, arrival.Y, 0);
'''
    new_flight = '''                GameLocation? firstRoom = this.BeginRegion1HuntRun();
                if (firstRoom is null)
                {
                    // Target was validated before charging; this is a last-resort failure path.
                    this.FlightCutsceneActive = false;
                    this.ReturnToSkyDockExterior();
                    Game1.drawObjectDialogue(ModEntry.T("airship.region1.unavailable"));
                    return;
                }

                Point arrival = ResolveRegion1RunArrivalTile(firstRoom);
                this.WarpGraceUntilMs = Environment.TickCount64 + 850L;
                Game1.warpFarmer(firstRoom.NameOrUniqueName, arrival.X, arrival.Y, 0);
'''
    text = replace_once(text, old_flight, new_flight, "flight enters hunt run")

    insertion_point = '    private void HandleRegion1DepartureRequest()\n'
    hunt_methods = '''    private bool EnsureRegion1RunRoomLocations()
    {
        if (!Context.IsWorldReady)
            return false;

        for (int i = 0; i < Region1RunRoomLocationNames.Length; i++)
        {
            if (Game1.getLocationFromName(Region1RunRoomLocationNames[i]) is not null)
                continue;

            try
            {
                Game1.locations.Add(new GameLocation(Region1RunRoomMapAssetNames[i], Region1RunRoomLocationNames[i]));
            }
            catch (Exception ex)
            {
                this.Monitor.Log(
                    $"Couldn't create Region I Hunt Run room {i + 1}; run generation aborted safely. {ex.GetType().Name}: {ex.Message}",
                    LogLevel.Error
                );
                return false;
            }
        }

        return true;
    }

    private void ResetRegion1RunState()
    {
        this.Region1RunRoute = Array.Empty<int>();
        this.Region1RunStep = -1;
        this.Region1RunSeed = 0;
        this.Region1RunActive = false;
        this.Region1RunCompleted = false;
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
        this.Region1RunRoute = Enumerable.Range(0, Region1RunRoomLocationNames.Length)
            .OrderBy(_ => random.Next())
            .Take(Region1RunRoomCount)
            .ToArray();
        this.Region1RunStep = 0;
        this.Region1RunActive = true;
        this.Region1RunCompleted = false;

        string route = string.Join(
            " -> ",
            this.Region1RunRoute.Select(index => ModEntry.T(Region1RunRoomNameKeys[index]))
        );
        this.Monitor.Log(
            $"Region I Hunt Run seed={this.Region1RunSeed}; route={route}. Exactly {Region1RunRoomCount} unique room(s) selected from {Region1RunRoomLocationNames.Length}.",
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
        Point next = ResolveRegion1RunNextTile(location);
        Point retreat = ResolveRegion1RunReturnTile(location);

        if (Touches(action, retreat) || PlayerIsNear(retreat))
        {
            this.Helper.Input.Suppress(e.Button);
            this.ResetRegion1RunState();
            this.StartFlightCutscene(returning: true);
            return;
        }

        if (!Touches(action, next) && !PlayerIsNear(next))
            return;

        this.Helper.Input.Suppress(e.Button);
        int remaining = CountRegion1MarkedMonsters(location);
        if (remaining > 0)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.region1.run.blocked", new { count = remaining }));
            return;
        }

        this.AdvanceRegion1HuntRun();
    }

    private void AdvanceRegion1HuntRun()
    {
        if (!this.Region1RunActive || this.Region1RunRoute.Length != Region1RunRoomCount)
        {
            Game1.drawObjectDialogue(ModEntry.T("airship.region1.run.unstable"));
            return;
        }

        this.Region1RunStep++;
        if (this.Region1RunStep >= Region1RunRoomCount)
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
            return;
        }

        int roomIndex = this.Region1RunRoute[this.Region1RunStep];
        GameLocation? next = Game1.getLocationFromName(Region1RunRoomLocationNames[roomIndex]);
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

    private void PopulateRegion1RunRoom(GameLocation location, int roomIndex)
    {
        this.ClearRegion1MarkedMonsters(location);

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
        int targetCount = random.Next(5, 9);
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

            Monster monster = CreateRegion1RunMonster(roomIndex, random.Next(100), tileVector * 64f);
            monster.modData[Region1MonsterMarkerKey] = "huntrun";
            location.characters.Add(monster);
            spawned++;
        }

        this.Monitor.Log(
            $"Region I Hunt Run room {roomIndex + 1} populated with {spawned} controlled monster(s); existing Scrap drop pipeline remains authoritative.",
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

    private void ClearRegion1MarkedMonsters(GameLocation location)
    {
        foreach (NPC actor in location.characters
                     .Where(actor => actor is Monster && actor.modData.ContainsKey(Region1MonsterMarkerKey))
                     .ToList())
        {
            location.characters.Remove(actor);
        }
    }

    private static int CountRegion1MarkedMonsters(GameLocation location)
        => location.characters
            .OfType<Monster>()
            .Count(monster => monster.Health > 0 && monster.modData.ContainsKey(Region1MonsterMarkerKey));

    private static Point ResolveRegion1RunArrivalTile(GameLocation room)
    {
        int width = room.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 28;
        int height = room.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 20;
        return FindClearTileNear(room, new Point(width / 2, Math.Max(3, height - 3)));
    }

    private static Point ResolveRegion1RunNextTile(GameLocation room)
    {
        int width = room.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 28;
        return new Point(width / 2, 1);
    }

    private static Point ResolveRegion1RunReturnTile(GameLocation room)
    {
        int width = room.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 28;
        int height = room.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 20;
        return new Point(width / 2, Math.Max(2, height - 2));
    }

'''
    text = replace_once(text, insertion_point, hunt_methods + insertion_point, "hunt methods insertion")

    SERVICE.write_text(text, encoding="utf-8")


def write_handoff() -> None:
    detail = Path("handoff/ALPHA28_0649_REGION1_HUNTRUN_PROTOTYPE.md")
    detail.write_text('''# Alpha.28 0649 — Region I Hunt Run prototype\n\nStatus: implementation candidate; in-game acceptance pending.\n\n## Locked purpose\nRegion I now uses a Rune Factory / roguelite-inspired authored-room run instead of one static farming field. Exactly **4 unique rooms are selected from a pool of 6** per paid/free Airship trip.\n\n## Runtime flow\n`Airship -> random 4-of-6 Region I rooms -> existing Region I Boss Gate hub -> Boss Gate 20 -> return / future Boss I`\n\nThe six prototype rooms are Cardcha-owned TMX maps made only from vanilla Stardew outdoor tilesheet references:\n1. Verdant Clearing\n2. Moss Creek\n3. Old Ruins\n4. Briar Thicket\n5. Hollow Grove\n6. Card Shrine\n\nA run route never repeats a room. The seed includes save ID, in-game day, and Airship flight count, so later farming trips can roll a different route.\n\n## Combat rules\n- Each room rolls a controlled 5–8 monster encounter from Green Slime / Bat / Bug pools.\n- Existing Cardcha monster-death -> Scrap economy remains authoritative. No direct normal-card drops were added.\n- The north route only advances after all Cardcha-marked monsters in that room are defeated.\n- The south route aborts/extracts back toward the Airship.\n- After room 4, the player reaches the existing Region I Boss Gate hub.\n- Existing 20 unique-card Boss Gate requirement is unchanged.\n\n## Non-regression\nNo SaveData schema change. No progression milestone change. No Boss Card/Boss Form tuning change. No MiMi/stair changes. No changes to the Forest Arcane Gate, Airship visual, Airship deck, Sky Dock interior, or existing Region I Boss Gate TMX.\n\n## Pending acceptance\nVisual/layout quality and controller feel need in-game testing. This is the first functional 4-of-6 Hunt Run vertical slice, not final Region I art.\n''', encoding="utf-8")

    latest = Path("handoff/LATEST_CARDCHA_HANDOFF.md")
    latest.write_text(f'''# Latest Cardcha handoff\n\nCurrent development branch:\n`cardcha-alpha28-0649-region1-huntrun-prototype`\n\nCurrent build:\n`{NEW_VERSION}`\n\nRead this FIRST when resuming from another chat:\n`handoff/ALPHA28_0649_REGION1_HUNTRUN_PROTOTYPE.md`\n\n## Session status — 2026-09-07\n- Region I Hunt Run prototype implemented as 6 authored vanilla-tile rooms; each Airship farming run chooses exactly 4 unique rooms.\n- Existing Region I Boss Gate hub and 20-card requirement are preserved at the end of the run.\n- 0648J MiMi Gift/Profile scale and WizardHouse stair acceptance remains pending because the user is away from the test machine; do not silently treat those two items as accepted.\n- Save schema 19, Boss Form duration 10s, Boss Energy gain 1/3, 76/76 active-card audit, Airship route/visual, Forest gate collision contract, and card canon remain protected.\n\n## Test focus when available\n1. Fly Region I repeatedly and confirm the route selects 4 non-repeating rooms from the 6-room pool.\n2. Confirm north progression is blocked until the room encounter is cleared.\n3. Confirm room 4 exits to the existing Region I Boss Gate hub.\n4. Confirm Boss Gate still reports Card Resonance and requires 20 unique cards.\n5. Confirm monsters still feed the normal Scrap pipeline.\n''', encoding="utf-8")


def main() -> None:
    patch_versions()
    generate_rooms()
    patch_service()
    add_i18n(ROOT / "i18n/default.json", {
        "airship.region1.run.enter": "HUNT {{step}}/{{total}} // {{room}}",
        "airship.region1.run.blocked": "The north route is still unstable. Defeat the remaining {{count}} monster(s) first.",
        "airship.region1.run.complete": "REGION I HUNT COMPLETE // The Boss Gate route is ahead.",
        "airship.region1.run.unstable": "This Hunt Run lost its route state. Extract and begin a new Region I flight.",
        "airship.region1.run.room.0": "Verdant Clearing",
        "airship.region1.run.room.1": "Moss Creek",
        "airship.region1.run.room.2": "Old Ruins",
        "airship.region1.run.room.3": "Briar Thicket",
        "airship.region1.run.room.4": "Hollow Grove",
        "airship.region1.run.room.5": "Card Shrine",
    })
    add_i18n(ROOT / "i18n/vi.json", {
        "airship.region1.run.enter": "CHUYẾN SĂN {{step}}/{{total}} // {{room}}",
        "airship.region1.run.blocked": "Lối phía bắc vẫn chưa ổn định. Hãy hạ {{count}} quái còn lại trước.",
        "airship.region1.run.complete": "HOÀN TẤT CHUYẾN SĂN KHU VỰC I // Tuyến tới Cổng Boss đã mở ra phía trước.",
        "airship.region1.run.unstable": "Chuyến săn đã mất trạng thái tuyến đường. Hãy rút về và bắt đầu một chuyến bay Khu Vực I mới.",
        "airship.region1.run.room.0": "Khoảng Rừng Xanh",
        "airship.region1.run.room.1": "Suối Rêu",
        "airship.region1.run.room.2": "Tàn Tích Cổ",
        "airship.region1.run.room.3": "Bụi Gai",
        "airship.region1.run.room.4": "Lùm Cây Trũng",
        "airship.region1.run.room.5": "Điện Thờ Cardcha",
    })
    write_handoff()
    print("0649 Region I Hunt Run prototype generated: 6 rooms, exactly 4 unique rooms per run.")


if __name__ == "__main__":
    main()
