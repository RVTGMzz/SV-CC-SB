from pathlib import Path
import json

ROOT = Path('src/Cardcha')
OLD = '0.3.0-alpha.28.0.2.0'
NEW = '0.3.0-alpha.28.0.3.0'


def replace_required(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise RuntimeError(f'{label}: expected marker not found: {old[:120]!r}')
    return text.replace(old, new, 1)


# Version sync.
for rel in ['Cardcha.csproj', 'Directory.Build.targets', 'manifest.json', 'ModEntry.cs']:
    p = ROOT / rel
    text = p.read_text(encoding='utf-8')
    if OLD in text:
        text = text.replace(OLD, NEW)
    text = text.replace('SKY DOCK ACCESS TEST', 'SKY DOCK INTERIOR + FLIGHT TEST')
    p.write_text(text, encoding='utf-8')

# Save schema + Airship fare telemetry.
save_data = ROOT / 'Models/SaveData.cs'
text = save_data.read_text(encoding='utf-8')
text = text.replace('public int SchemaVersion { get; set; } = 15;', 'public int SchemaVersion { get; set; } = 16;')
if 'public int AirshipFlightsTaken' not in text:
    marker = '    public int AirshipHighestRegionUnlocked { get; set; }\n'
    addition = '''    public int AirshipFlightsTaken { get; set; }\n    public int AirshipTotalFarePaid { get; set; }\n'''
    if marker not in text:
        raise RuntimeError('SaveData Airship marker missing')
    text = text.replace(marker, marker + addition, 1)
save_data.write_text(text, encoding='utf-8')

save_service = ROOT / 'Services/SaveService.cs'
text = save_service.read_text(encoding='utf-8')
text = text.replace('private const int CurrentSchemaVersion = 15;', 'private const int CurrentSchemaVersion = 16;')

# Clean the accidental duplicate v15 migration if still present.
v15 = '''        // v15: Airship foundation. Existing saves that already completed the MiMi/Wizard\n        // handoff receive Region I access immediately instead of replaying onboarding.\n        if (loadedSchema < 15)\n        {\n            if (this.Data.MimiMeetupCompleted || this.Data.MachineDelivered || this.Data.BinderUnlocked)\n            {\n                this.Data.AirshipUnlocked = true;\n                this.Data.AirshipHighestRegionUnlocked = Math.Max(1, this.Data.AirshipHighestRegionUnlocked);\n                if (this.Data.AirshipUnlockedDay < 0)\n                    this.Data.AirshipUnlockedDay = Game1.Date.TotalDays;\n            }\n        }\n\n'''
if text.count(v15) > 1:
    text = text.replace(v15 + v15, v15, 1)

if '// v16: Sky Dock interior + MiMi fare telemetry.' not in text:
    marker = '        if (loadedSchema < CurrentSchemaVersion)\n'
    block = '''        // v16: Sky Dock interior + MiMi fare telemetry.\n        if (loadedSchema < 16)\n        {\n            this.Data.AirshipFlightsTaken = Math.Max(0, this.Data.AirshipFlightsTaken);\n            this.Data.AirshipTotalFarePaid = Math.Max(0, this.Data.AirshipTotalFarePaid);\n        }\n\n'''
    if marker not in text:
        raise RuntimeError('SaveService migration insertion marker missing')
    text = text.replace(marker, block + marker, 1)

if 'this.Data.AirshipFlightsTaken = Math.Max(0, this.Data.AirshipFlightsTaken);' not in text.split('private void Normalize()', 1)[1]:
    marker = '        this.Data.DuplicatePullStreak = Math.Max(0, this.Data.DuplicatePullStreak);\n\n'
    extra = '''        this.Data.AirshipHighestRegionUnlocked = Math.Clamp(this.Data.AirshipHighestRegionUnlocked, 0, 4);\n        this.Data.AirshipUnlockedDay = Math.Max(-1, this.Data.AirshipUnlockedDay);\n        this.Data.AirshipFlightsTaken = Math.Max(0, this.Data.AirshipFlightsTaken);\n        this.Data.AirshipTotalFarePaid = Math.Max(0, this.Data.AirshipTotalFarePaid);\n\n'''
    if marker not in text:
        raise RuntimeError('SaveService Normalize marker missing')
    # Remove the older misplaced Airship normalize block if present nearby, then insert canonical block.
    old_extra = '''        this.Data.AirshipHighestRegionUnlocked = Math.Clamp(this.Data.AirshipHighestRegionUnlocked, 0, 4);\n        this.Data.AirshipUnlockedDay = Math.Max(-1, this.Data.AirshipUnlockedDay);\n\n'''
    normalize_pos = text.index('private void Normalize()')
    before = text[:normalize_pos]
    after = text[normalize_pos:].replace(old_extra, '', 1)
    text = before + after
    text = text.replace(marker, marker + extra, 1)

if 'data.AirshipFlightsTaken' not in text:
    marker = '            data.AirshipHighestRegionUnlocked\n'
    repl = '''            data.AirshipHighestRegionUnlocked,\n            data.AirshipFlightsTaken,\n            data.AirshipTotalFarePaid\n'''
    if marker not in text:
        raise RuntimeError('SaveService fingerprint Airship marker missing')
    text = text.replace(marker, repl, 1)
save_service.write_text(text, encoding='utf-8')

# Sky Dock interior map: Cardcha-owned layout using the same vanilla interior tilesheet contract.
W, H = 30, 18
back = []
buildings = []
front = []
for y in range(H):
    br = []
    bu = []
    fr = []
    for x in range(W):
        # Back: warm wall top, wood floor below.
        if y == 0 or x == 0 or x == W - 1:
            b = 0
        elif y in (1, 2):
            b = 171
        elif y == 3:
            b = 113
        elif y == 4:
            b = 200
        else:
            b = 232 if (x + y) % 2 == 0 else 233
            if y % 2 == 0:
                b = 264 if x % 2 == 0 else 265
        br.append(b)

        # Buildings: outer room shell only. Interior remains open for player/NPC-safe future use.
        tile = 0
        if y == 1 and x == 1:
            tile = 155
        elif y == 1 and x == W - 2:
            tile = 156
        elif y == 2 and x == 1:
            tile = 187
        elif y == 2 and x == W - 2:
            tile = 188
        elif y == 2 and 1 < x < W - 2:
            tile = 81
        elif 4 <= y <= H - 3 and x == 1:
            tile = 68
        elif 4 <= y <= H - 3 and x == W - 2:
            tile = 69
        elif y == H - 2 and x not in (W // 2 - 1, W // 2, W // 2 + 1) and 0 < x < W - 1:
            tile = 1
        bu.append(tile)

        f = 0
        if y == H - 2 and x not in (W // 2 - 1, W // 2, W // 2 + 1) and 0 < x < W - 1:
            f = 166
        fr.append(f)
    back.append(br)
    buildings.append(bu)
    front.append(fr)


def csv(layer):
    return '\n'.join(','.join(str(v) for v in row) + ',' for row in layer)

map_text = f'''<?xml version='1.0' encoding='UTF-8'?>\n<map version="1.10" tiledversion="1.10.2" orientation="orthogonal" renderorder="right-down" width="{W}" height="{H}" tilewidth="16" tileheight="16" infinite="0" nextlayerid="4" nextobjectid="1">\n <properties>\n  <property name="CardchaSkyDockVersion" value="alpha.28.0.3.0" />\n  <property name="CardchaSkyDockRole" value="interior-hub|route-board|airship-bay|forest-return" />\n  <property name="CardchaAssetPolicy" value="cardcha-owned-map|vanilla-tiles-only|no-druid-assets" />\n  <property name="CardchaLayout" value="bottom-entry|left-route-board|right-airship-bay|future-utility-corner" />\n </properties>\n <tileset firstgid="1" name="townInterior" tilewidth="16" tileheight="16" tilecount="2176" columns="32">\n  <image source=".townInterior.png" width="512" height="1088" />\n </tileset>\n <layer id="1" name="Back" width="{W}" height="{H}">\n  <data encoding="csv">\n{csv(back)}\n</data>\n </layer>\n <layer id="2" name="Buildings" width="{W}" height="{H}">\n  <data encoding="csv">\n{csv(buildings)}\n</data>\n </layer>\n <layer id="3" name="Front" width="{W}" height="{H}">\n  <data encoding="csv">\n{csv(front)}\n</data>\n </layer>\n</map>\n'''
(ROOT / 'assets/sky_dock_interior.tmx').write_text(map_text, encoding='utf-8')

# Airship service: interior hub, deliberate fare confirmation, outbound/return cinematics.
service_path = ROOT / 'Services/AirshipFoundationService.cs'
s = service_path.read_text(encoding='utf-8')

if 'SkyDockInteriorLocationName' not in s:
    s = replace_required(
        s,
        '    public const string SkyDockLocationName = "Forest";\n',
        '''    public const string SkyDockLocationName = "Forest";\n    public const string SkyDockInteriorLocationName = "Cardcha_SkyDockInterior";\n    public const string SkyDockInteriorMapAssetName = "Maps/Cardcha_SkyDockInterior";\n''',
        'service constants'
    )

if 'SkyDockInteriorMapPath' not in s:
    s = replace_required(
        s,
        '    private const string DeckMapPath = "assets/airship_deck.tmx";\n',
        '''    private const string DeckMapPath = "assets/airship_deck.tmx";\n    private const string SkyDockInteriorMapPath = "assets/sky_dock_interior.tmx";\n    private const int Region1Fare = 100;\n    private const int Region2Fare = 250;\n    private const int Region3Fare = 500;\n    private const int Region4Fare = 1000;\n    private const long DepartureConfirmWindowMs = 5000L;\n    private const long FlightCutsceneDurationMs = 3200L;\n    private const long FlightWarpAtMs = 1650L;\n''',
        'service private constants'
    )

if 'SkyDockInteriorCreationFailed' not in s:
    s = replace_required(
        s,
        '    private bool LoggedDeckCreation;\n',
        '''    private bool LoggedDeckCreation;\n    private bool SkyDockInteriorCreationFailed;\n    private bool LoggedSkyDockInteriorFailure;\n    private bool LoggedSkyDockInteriorCreation;\n    private long PendingDepartureUntilMs;\n    private bool FlightCutsceneActive;\n    private bool FlightCutsceneReturning;\n    private bool FlightCutsceneWarped;\n    private long FlightCutsceneStartedAtMs;\n''',
        'service fields'
    )

old_asset = '''    public void OnAssetRequested(object? sender, AssetRequestedEventArgs e)\n    {\n        if (!e.NameWithoutLocale.IsEquivalentTo(DeckMapAssetName))\n            return;\n\n        e.LoadFromModFile<xTile.Map>(DeckMapPath, AssetLoadPriority.Exclusive);\n    }\n'''
new_asset = '''    public void OnAssetRequested(object? sender, AssetRequestedEventArgs e)\n    {\n        if (e.NameWithoutLocale.IsEquivalentTo(DeckMapAssetName))\n        {\n            e.LoadFromModFile<xTile.Map>(DeckMapPath, AssetLoadPriority.Exclusive);\n            return;\n        }\n\n        if (e.NameWithoutLocale.IsEquivalentTo(SkyDockInteriorMapAssetName))\n            e.LoadFromModFile<xTile.Map>(SkyDockInteriorMapPath, AssetLoadPriority.Exclusive);\n    }\n'''
if 'SkyDockInteriorMapAssetName' in s and old_asset in s:
    s = s.replace(old_asset, new_asset, 1)

if 'this.EnsureSkyDockInteriorLocation();' not in s:
    s = s.replace('        this.EnsureDeckLocation();\n        this.MigrateUnlockFromExistingStory();\n', '        this.EnsureDeckLocation();\n        this.EnsureSkyDockInteriorLocation();\n        this.MigrateUnlockFromExistingStory();\n', 1)
    day_marker = '        this.LoggedDeckFailure = false;\n        this.EnsureDeckLocation();\n'
    day_repl = '''        this.LoggedDeckFailure = false;\n        this.SkyDockInteriorCreationFailed = false;\n        this.LoggedSkyDockInteriorFailure = false;\n        this.EnsureDeckLocation();\n        this.EnsureSkyDockInteriorLocation();\n'''
    if day_marker not in s:
        raise RuntimeError('service day-start marker missing')
    s = s.replace(day_marker, day_repl, 1)

if 'this.LoggedSkyDockInteriorCreation = false;' not in s:
    s = s.replace('        this.LoggedDeckCreation = false;\n', '        this.LoggedDeckCreation = false;\n        this.LoggedSkyDockInteriorCreation = false;\n', 1)

# Update tick: travel cutscene takes priority, then normal flyby logic.
old_tick = '''        long now = Environment.TickCount64;\n        if (this.FlybyActive)\n'''
new_tick = '''        long now = Environment.TickCount64;\n\n        if (this.FlightCutsceneActive)\n        {\n            Game1.player.Halt();\n            this.UpdateFlightCutscene(now);\n            return;\n        }\n\n        if (this.PendingDepartureUntilMs > 0 && now > this.PendingDepartureUntilMs)\n            this.PendingDepartureUntilMs = 0;\n\n        if (this.FlybyActive)\n'''
if 'this.UpdateFlightCutscene(now);' not in s:
    s = replace_required(s, old_tick, new_tick, 'service update tick')

# Render interior markers/details and cinematic overlay.
render_marker = '''        if (location?.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase) == true)\n            this.DrawDeckMarkers(e.SpriteBatch, location);\n'''
render_repl = '''        if (location?.NameOrUniqueName.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase) == true)\n            this.DrawSkyDockInteriorDetails(e.SpriteBatch, location);\n\n        if (location?.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase) == true)\n            this.DrawDeckMarkers(e.SpriteBatch, location);\n\n        if (this.FlightCutsceneActive)\n            this.DrawFlightCutscene(e.SpriteBatch);\n'''
if 'this.DrawFlightCutscene(e.SpriteBatch);' not in s:
    s = replace_required(s, render_marker, render_repl, 'service render')

# Prevent action handling while cinematic is active.
s = s.replace('            || Game1.eventUp\n            || Environment.TickCount64 < this.WarpGraceUntilMs)', '            || Game1.eventUp\n            || this.FlightCutsceneActive\n            || Environment.TickCount64 < this.WarpGraceUntilMs)', 1)

# Exterior Sky Dock now enters the interior, never directly the deck.
old_exterior = '''            GameLocation? deck = this.EnsureDeckLocation();\n            if (deck is null)\n            {\n                this.Helper.Input.Suppress(e.Button);\n                Game1.drawObjectDialogue(ModEntry.T("airship.deck.unavailable"));\n                return;\n            }\n\n            this.Helper.Input.Suppress(e.Button);\n            Point arrival = ResolveDeckArrivalTile(deck);\n            this.WarpGraceUntilMs = Environment.TickCount64 + 850L;\n            Game1.warpFarmer(DeckLocationName, arrival.X, arrival.Y, 0);\n            return;\n'''
new_exterior = '''            GameLocation? interior = this.EnsureSkyDockInteriorLocation();\n            if (interior is null)\n            {\n                this.Helper.Input.Suppress(e.Button);\n                Game1.drawObjectDialogue(ModEntry.T("airship.skydock.interior.unavailable"));\n                return;\n            }\n\n            this.Helper.Input.Suppress(e.Button);\n            Point arrival = ResolveSkyDockInteriorArrivalTile(interior);\n            this.WarpGraceUntilMs = Environment.TickCount64 + 850L;\n            Game1.warpFarmer(SkyDockInteriorLocationName, arrival.X, arrival.Y, 0);\n            return;\n'''
if old_exterior in s:
    s = s.replace(old_exterior, new_exterior, 1)

# Add interior action block before the deck action block.
if 'HandleRegion1DepartureRequest' not in s.split('public void OnButtonPressed', 1)[1].split('/// <summary>', 1)[0]:
    marker = '''        if (!location.NameOrUniqueName.Equals(DeckLocationName, StringComparison.OrdinalIgnoreCase))\n            return;\n'''
    block = '''        if (location.NameOrUniqueName.Equals(SkyDockInteriorLocationName, StringComparison.OrdinalIgnoreCase))\n        {\n            Point action = GetActionTile();\n            Point route = ResolveSkyDockInteriorRouteTile(location);\n            Point exit = ResolveSkyDockInteriorExitTile(location);\n\n            if (Touches(action, route) || PlayerIsNear(route))\n            {\n                this.Helper.Input.Suppress(e.Button);\n                this.HandleRegion1DepartureRequest();\n                return;\n            }\n\n            if (Touches(action, exit) || PlayerIsNear(exit))\n            {\n                this.Helper.Input.Suppress(e.Button);\n                this.ReturnToSkyDockExterior();\n            }\n            return;\n        }\n\n'''
    if marker not in s:
        raise RuntimeError('service deck action marker missing')
    s = s.replace(marker, block + marker, 1)

# Normal deck exit = free return cinematic into interior.
s = s.replace('        this.ReturnToSkyDock();\n', '        this.StartFlightCutscene(returning: true);\n', 1)

# Debug deck return should remain instant/no progression side effects.
s = s.replace('            this.ReturnToSkyDock();\n            return "Airship TEST: returned to Sky Dock. Story/unlock state was not changed.";', '            this.WarpToSkyDockInterior();\n            return "Airship TEST: returned to Sky Dock interior. Story/unlock/fare state was not changed.";', 1)
s = s.replace('return "Airship TEST: warped to Cardcha_AirshipDeck. Run cardcha_test_airship again to return to Sky Dock. Story/unlock state was not changed.";', 'return "Airship TEST: warped to Cardcha_AirshipDeck. Run cardcha_test_airship again to return to Sky Dock interior. Story/unlock/fare state was not changed.";', 1)

# Status telemetry.
status_old = '''        bool deckExists = Game1.getLocationFromName(DeckLocationName) is not null;\n        return $"AirshipFlybySeen={this.Save.Data.AirshipFlybySeen} | " +\n'''
status_new = '''        bool deckExists = Game1.getLocationFromName(DeckLocationName) is not null;\n        bool interiorExists = Game1.getLocationFromName(SkyDockInteriorLocationName) is not null;\n        return $"AirshipFlybySeen={this.Save.Data.AirshipFlybySeen} | " +\n'''
if 'bool interiorExists' not in s:
    s = replace_required(s, status_old, status_new, 'service status header')
s = s.replace('$"DeckExists={deckExists} | SkyDock=', '$"DeckExists={deckExists} | InteriorExists={interiorExists} | Flights={this.Save.Data.AirshipFlightsTaken} | FarePaid={this.Save.Data.AirshipTotalFarePaid}g | SkyDock=', 1)

# Insert interior creation + travel helpers before exterior return helper.
helper_marker = '    private void ReturnToSkyDock()\n'
if 'private GameLocation? EnsureSkyDockInteriorLocation()' not in s:
    helpers = '''    private GameLocation? EnsureSkyDockInteriorLocation()\n    {\n        if (!Context.IsWorldReady || this.SkyDockInteriorCreationFailed)\n            return null;\n\n        GameLocation? existing = Game1.getLocationFromName(SkyDockInteriorLocationName);\n        if (existing is not null)\n            return existing;\n\n        try\n        {\n            GameLocation interior = new(SkyDockInteriorMapAssetName, SkyDockInteriorLocationName);\n            Game1.locations.Add(interior);\n            if (!this.LoggedSkyDockInteriorCreation)\n            {\n                this.LoggedSkyDockInteriorCreation = true;\n                this.Monitor.Log("Created Cardcha_SkyDockInterior from Cardcha-owned vanilla-tile layout.", LogLevel.Info);\n            }\n            return interior;\n        }\n        catch (Exception ex)\n        {\n            this.SkyDockInteriorCreationFailed = true;\n            if (!this.LoggedSkyDockInteriorFailure)\n            {\n                this.LoggedSkyDockInteriorFailure = true;\n                this.Monitor.Log($"Couldn't create Sky Dock interior; retries suppressed until next save/day. {ex.GetType().Name}: {ex.Message}", LogLevel.Error);\n            }\n            return null;\n        }\n    }\n\n    private void HandleRegion1DepartureRequest()\n    {\n        if (this.Save.Data.AirshipHighestRegionUnlocked < 1)\n        {\n            Game1.drawObjectDialogue(ModEntry.T("airship.route.locked"));\n            return;\n        }\n\n        // Validate the target before money is ever consumed.\n        if (this.EnsureDeckLocation() is null)\n        {\n            Game1.drawObjectDialogue(ModEntry.T("airship.deck.unavailable"));\n            return;\n        }\n\n        int fare = this.GetRegionFare(1);\n        long now = Environment.TickCount64;\n        if (this.PendingDepartureUntilMs <= now)\n        {\n            this.PendingDepartureUntilMs = now + DepartureConfirmWindowMs;\n            Game1.drawObjectDialogue(\n                fare <= 0\n                    ? ModEntry.T("airship.route.region1.first_free")\n                    : ModEntry.T("airship.route.region1.confirm", new { fare })\n            );\n            return;\n        }\n\n        this.PendingDepartureUntilMs = 0;\n        if (Game1.player.Money < fare)\n        {\n            Game1.drawObjectDialogue(ModEntry.T("airship.route.not_enough", new { fare, money = Game1.player.Money }));\n            return;\n        }\n\n        if (fare > 0)\n            Game1.player.Money -= fare;\n\n        this.Save.Data.AirshipFlightsTaken++;\n        this.Save.Data.AirshipTotalFarePaid += fare;\n        this.Save.Save();\n        this.StartFlightCutscene(returning: false);\n    }\n\n    private int GetRegionFare(int region)\n    {\n        if (this.Save.Data.AirshipFlightsTaken <= 0)\n            return 0; // MiMi's first flight is free; persisted so it can't be consumed twice accidentally.\n\n        return region switch\n        {\n            1 => Region1Fare,\n            2 => Region2Fare,\n            3 => Region3Fare,\n            4 => Region4Fare,\n            _ => Region1Fare\n        };\n    }\n\n    private void StartFlightCutscene(bool returning)\n    {\n        this.FlightCutsceneActive = true;\n        this.FlightCutsceneReturning = returning;\n        this.FlightCutsceneWarped = false;\n        this.FlightCutsceneStartedAtMs = Environment.TickCount64;\n        this.PendingDepartureUntilMs = 0;\n        Game1.player.Halt();\n        Game1.playSound("wand");\n    }\n\n    private void UpdateFlightCutscene(long now)\n    {\n        long elapsed = now - this.FlightCutsceneStartedAtMs;\n        if (!this.FlightCutsceneWarped && elapsed >= FlightWarpAtMs)\n        {\n            this.FlightCutsceneWarped = true;\n            if (this.FlightCutsceneReturning)\n            {\n                if (!this.WarpToSkyDockInterior())\n                    this.ReturnToSkyDockExterior();\n            }\n            else\n            {\n                GameLocation? deck = this.EnsureDeckLocation();\n                if (deck is null)\n                {\n                    // Target was validated before charging; this is a last-resort failure path.\n                    this.FlightCutsceneActive = false;\n                    this.ReturnToSkyDockExterior();\n                    Game1.drawObjectDialogue(ModEntry.T("airship.deck.unavailable"));\n                    return;\n                }\n\n                Point arrival = ResolveDeckArrivalTile(deck);\n                this.WarpGraceUntilMs = Environment.TickCount64 + 850L;\n                Game1.warpFarmer(DeckLocationName, arrival.X, arrival.Y, 0);\n            }\n        }\n\n        if (elapsed >= FlightCutsceneDurationMs)\n        {\n            this.FlightCutsceneActive = false;\n            this.FlightCutsceneReturning = false;\n            this.FlightCutsceneWarped = false;\n            this.FlightCutsceneStartedAtMs = 0;\n            this.WarpGraceUntilMs = Environment.TickCount64 + 500L;\n        }\n    }\n\n    private bool WarpToSkyDockInterior()\n    {\n        GameLocation? interior = this.EnsureSkyDockInteriorLocation();\n        if (interior is null)\n            return false;\n\n        Point arrival = ResolveSkyDockInteriorArrivalTile(interior);\n        this.WarpGraceUntilMs = Environment.TickCount64 + 850L;\n        Game1.warpFarmer(SkyDockInteriorLocationName, arrival.X, arrival.Y, 0);\n        return true;\n    }\n\n'''
    if helper_marker not in s:
        raise RuntimeError('service ReturnToSkyDock marker missing')
    s = s.replace(helper_marker, helpers + helper_marker, 1)

# Rename old helper to explicit exterior return.
s = s.replace('    private void ReturnToSkyDock()\n', '    private void ReturnToSkyDockExterior()\n', 1)

# Interior tile resolvers before deck resolvers.
resolver_marker = '    private static Point ResolveDeckArrivalTile(GameLocation deck)\n'
if 'ResolveSkyDockInteriorArrivalTile' not in s.split(resolver_marker, 1)[0]:
    resolver_block = '''    private static Point ResolveSkyDockInteriorArrivalTile(GameLocation interior)\n    {\n        int width = interior.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 30;\n        int height = interior.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 18;\n        return FindClearTileNear(interior, new Point(width / 2, Math.Max(2, height - 4)));\n    }\n\n    private static Point ResolveSkyDockInteriorExitTile(GameLocation interior)\n    {\n        int width = interior.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 30;\n        int height = interior.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 18;\n        return new Point(width / 2, Math.Max(1, height - 2));\n    }\n\n    private static Point ResolveSkyDockInteriorRouteTile(GameLocation interior)\n    {\n        int width = interior.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 30;\n        int height = interior.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 18;\n        return new Point(Math.Clamp(width / 3, 3, width - 4), Math.Clamp(7, 3, height - 5));\n    }\n\n    private static Point ResolveSkyDockInteriorBayTile(GameLocation interior)\n    {\n        int width = interior.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 30;\n        int height = interior.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 18;\n        return new Point(Math.Clamp(width - 6, 4, width - 3), Math.Clamp(7, 3, height - 5));\n    }\n\n'''
    if resolver_marker not in s:
        raise RuntimeError('service deck resolver marker missing')
    s = s.replace(resolver_marker, resolver_block + resolver_marker, 1)

# Draw the interior visual identity + flight cinematic before deck marker drawing.
draw_marker = '    private void DrawDeckMarkers(SpriteBatch batch, GameLocation deck)\n'
if 'private void DrawSkyDockInteriorDetails' not in s:
    draw_block = '''    private void DrawSkyDockInteriorDetails(SpriteBatch batch, GameLocation interior)\n    {\n        Point route = ResolveSkyDockInteriorRouteTile(interior);\n        Point exit = ResolveSkyDockInteriorExitTile(interior);\n        Point bay = ResolveSkyDockInteriorBayTile(interior);\n\n        // Route board: warm wood with a restrained MiMi cyan indicator.\n        Vector2 board = Game1.GlobalToLocal(Game1.viewport, new Vector2((route.X - 1) * 64f, (route.Y - 2) * 64f));\n        DrawRect(batch, new Rectangle((int)board.X, (int)board.Y, 150, 82), new Color(91, 58, 36) * 0.94f);\n        DrawRect(batch, new Rectangle((int)board.X + 7, (int)board.Y + 7, 136, 68), new Color(147, 100, 57) * 0.96f);\n        float pulse = 0.45f + 0.18f * (float)Math.Sin(Environment.TickCount64 / 270.0);\n        DrawRect(batch, new Rectangle((int)board.X + 22, (int)board.Y + 52, 92, 6), new Color(104, 220, 238) * pulse);\n\n        // Open-sky docking bay on the right wall. This is an overlay inside Cardcha's own location,\n        // so it cannot affect vanilla collision/pathing.\n        Vector2 sky = Game1.GlobalToLocal(Game1.viewport, new Vector2((bay.X - 2) * 64f, (bay.Y - 4) * 64f));\n        DrawRect(batch, new Rectangle((int)sky.X, (int)sky.Y, 250, 170), new Color(74, 128, 167) * 0.92f);\n        DrawRect(batch, new Rectangle((int)sky.X + 18, (int)sky.Y + 30, 72, 13), new Color(222, 237, 240) * 0.76f);\n        DrawRect(batch, new Rectangle((int)sky.X + 105, (int)sky.Y + 72, 95, 12), new Color(222, 237, 240) * 0.62f);\n        DrawRect(batch, new Rectangle((int)sky.X - 8, (int)sky.Y - 8, 266, 8), new Color(67, 45, 31) * 0.96f);\n        DrawRect(batch, new Rectangle((int)sky.X - 8, (int)sky.Y + 170, 266, 9), new Color(67, 45, 31) * 0.96f);\n        DrawRect(batch, new Rectangle((int)sky.X - 8, (int)sky.Y - 8, 8, 187), new Color(67, 45, 31) * 0.96f);\n        DrawRect(batch, new Rectangle((int)sky.X + 250, (int)sky.Y - 8, 8, 187), new Color(67, 45, 31) * 0.96f);\n\n        DrawWorldMarker(batch, route, new Color(255, 220, 120) * 0.58f);\n        DrawWorldMarker(batch, exit, new Color(120, 220, 255) * 0.52f);\n    }\n\n    private void DrawFlightCutscene(SpriteBatch batch)\n    {\n        float p = Math.Clamp((Environment.TickCount64 - this.FlightCutsceneStartedAtMs) / (float)FlightCutsceneDurationMs, 0f, 1f);\n        int w = Game1.viewport.Width;\n        int h = Game1.viewport.Height;\n\n        DrawRect(batch, new Rectangle(0, 0, w, h), new Color(21, 31, 51) * 0.94f);\n\n        // Dock frame.\n        Color woodDark = new Color(69, 46, 31) * 0.95f;\n        Color wood = new Color(132, 87, 50) * 0.96f;\n        DrawRect(batch, new Rectangle(0, h - 145, w, 145), woodDark);\n        for (int x = 0; x < w; x += 72)\n            DrawRect(batch, new Rectangle(x, h - 137, 66, 72), wood);\n        DrawRect(batch, new Rectangle(70, 0, 16, h - 80), woodDark);\n        DrawRect(batch, new Rectangle(w - 86, 0, 16, h - 80), woodDark);\n\n        // Clouds make the scene read as an elevated dock even before bespoke Cardcha art exists.\n        Color cloud = new Color(222, 236, 241) * 0.66f;\n        DrawRect(batch, new Rectangle(w / 8, h / 4, w / 5, 18), cloud);\n        DrawRect(batch, new Rectangle(w * 5 / 8, h / 3, w / 4, 20), cloud * 0.82f);\n\n        float travel = this.FlightCutsceneReturning ? 1f - p : p;\n        float shipX = MathHelper.Lerp(w * 0.28f, w * 0.78f, travel);\n        float shipY = h * 0.40f - (float)Math.Sin(p * Math.PI) * 24f;\n        this.DrawCinematicAirship(batch, new Vector2(shipX, shipY), 1.15f);\n\n        string title = ModEntry.T(this.FlightCutsceneReturning ? "airship.cutscene.return" : "airship.cutscene.departure");\n        Vector2 size = Game1.smallFont.MeasureString(title);\n        batch.DrawString(Game1.smallFont, title, new Vector2((w - size.X) / 2f, 26f), Color.White * 0.92f);\n    }\n\n    private void DrawCinematicAirship(SpriteBatch batch, Vector2 p, float scale)\n    {\n        int X(float n) => (int)(p.X + n * scale);\n        int Y(float n) => (int)(p.Y + n * scale);\n        int S(float n) => Math.Max(1, (int)(n * scale));\n\n        Color balloon = new Color(55, 44, 75) * 0.96f;\n        Color hull = new Color(101, 66, 43) * 0.98f;\n        Color trim = new Color(178, 125, 67) * 0.92f;\n        Color glow = new Color(116, 222, 241) * 0.72f;\n\n        DrawRect(batch, new Rectangle(X(-76), Y(-45), S(152), S(13)), balloon);\n        DrawRect(batch, new Rectangle(X(-92), Y(-31), S(184), S(21)), balloon);\n        DrawRect(batch, new Rectangle(X(-82), Y(-9), S(164), S(15)), balloon);\n        DrawRect(batch, new Rectangle(X(-45), Y(28), S(90), S(22)), hull);\n        DrawRect(batch, new Rectangle(X(-56), Y(50), S(112), S(8)), trim);\n        DrawRect(batch, new Rectangle(X(-31), Y(6), S(4), S(23)), trim);\n        DrawRect(batch, new Rectangle(X(27), Y(6), S(4), S(23)), trim);\n        DrawRect(batch, new Rectangle(X(7), Y(37), S(7), S(7)), glow);\n    }\n\n'''
    if draw_marker not in s:
        raise RuntimeError('service draw marker missing')
    s = s.replace(draw_marker, draw_block + draw_marker, 1)

# Reset all new runtime-only state.
reset_marker = '''        this.DeckCreationFailed = false;\n        this.LoggedDeckFailure = false;\n        this.CachedSkyDockTile = null;\n'''
reset_repl = '''        this.DeckCreationFailed = false;\n        this.LoggedDeckFailure = false;\n        this.SkyDockInteriorCreationFailed = false;\n        this.LoggedSkyDockInteriorFailure = false;\n        this.PendingDepartureUntilMs = 0;\n        this.FlightCutsceneActive = false;\n        this.FlightCutsceneReturning = false;\n        this.FlightCutsceneWarped = false;\n        this.FlightCutsceneStartedAtMs = 0;\n        this.CachedSkyDockTile = null;\n'''
if 'this.FlightCutsceneStartedAtMs = 0;' not in s.split('private void ResetRuntime()', 1)[1]:
    s = replace_required(s, reset_marker, reset_repl, 'service reset')

service_path.write_text(s, encoding='utf-8')

# Localization.
translations = {
    'default.json': {
        'airship.skydock.interior.unavailable': 'The Sky Dock hall is unstable right now. Try again after reloading the day.',
        'airship.route.region1.first_free': 'REGION I // MiMi: First flight is on the house. Yes, really. Interact again within a few seconds to depart.',
        'airship.route.region1.confirm': 'REGION I // MiMi fare: {{fare}}g. Fuel, docking, maintenance... friendship does not power an airship. Interact again within a few seconds to depart.',
        'airship.route.not_enough': 'MiMi: The fare is {{fare}}g, and you currently have {{money}}g. I run an airship, not a charity balloon.',
        'airship.cutscene.departure': 'Sky Dock — Departure',
        'airship.cutscene.return': 'Sky Dock — Arrival'
    },
    'vi.json': {
        'airship.skydock.interior.unavailable': 'Sảnh Sky Dock đang không ổn định. Hãy thử lại sau khi tải lại ngày.',
        'airship.route.region1.first_free': 'KHU VỰC I // MiMi: Chuyến đầu miễn phí. Ừ, thật đó. Tương tác lại trong vài giây để cất cánh.',
        'airship.route.region1.confirm': 'KHU VỰC I // Phí của MiMi: {{fare}}g. Nhiên liệu, phí bến, bảo trì... tàu bay không chạy bằng tình bạn đâu nha. Tương tác lại trong vài giây để cất cánh.',
        'airship.route.not_enough': 'MiMi: Vé là {{fare}}g, mà bạn đang có {{money}}g. Tui lái tàu bay chứ đâu lái khinh khí cầu từ thiện.',
        'airship.cutscene.departure': 'Sky Dock — Khởi hành',
        'airship.cutscene.return': 'Sky Dock — Cập bến'
    }
}
for filename, additions in translations.items():
    path = ROOT / 'i18n' / filename
    data = json.loads(path.read_text(encoding='utf-8'))
    data.update(additions)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print('alpha.28.0.3.0 Sky Dock interior + flight foundation patch applied')
