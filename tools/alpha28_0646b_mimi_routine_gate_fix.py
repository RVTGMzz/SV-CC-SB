from pathlib import Path

ROOT = Path('src/Cardcha')
OLD = '0.3.0-alpha.28.0.4.14.4.5.11.1'
NEW = '0.3.0-alpha.28.0.4.14.4.5.11.2'


def bump(path: Path):
    s = path.read_text(encoding='utf-8')
    if NEW not in s:
        if OLD not in s:
            raise RuntimeError(f'missing version in {path}')
        s = s.replace(OLD, NEW)
    path.write_text(s, encoding='utf-8')


def patch_home():
    p = ROOT/'Services/MimiHomeService.cs'
    s = p.read_text(encoding='utf-8')
    s = s.replace('/// Alpha28 .5.11.1 home/schedule hotfix: stable attic anchors + crisp portrait dialogue.',
                  '/// Alpha28 .5.11.2 home routine fix: fixed anchors, no home shop, direct routine TEST states.')
    s = s.replace('    private static readonly Point SecretTvWatchTile = new(6, 10);\n    private static readonly Point SecretLateHomeTile = new(13, 7);',
                  '    private static readonly Point DefaultHomeTile = new(10, 4);\n    private static readonly Point SecretTvWatchTile = new(5, 10);\n    private static readonly Point SecretLateHomeTile = new(13, 7);')
    s = s.replace('    private string? CachedAtticRoutineKey;\n    private Point? CachedAtticRoutineTile;\n',
                  '    private string? DebugRoutineOverride;\n')
    s = s.replace('        this.CachedAtticRoutineKey = null;\n        this.CachedAtticRoutineTile = null;\n', '', 3)
    s = s.replace('        this.LoggedAtticFailure = false;\n    }\n\n    public void OnButtonPressed',
                  '        this.LoggedAtticFailure = false;\n        this.DebugRoutineOverride = null;\n    }\n\n    public void OnButtonPressed', 1)

    old_guard = '''        if (!Context.IsWorldReady\n            || !this.Save.Data.MimiMeetupCompleted\n            || this.StoryOwnsMimiActor()\n            || this.MysteryOwnsMimiActor()\n            || Game1.eventUp)\n        {\n            return;\n        }\n\n        NPC? mimi = this.WorldActors.FindMimiActor() ?? this.WorldActors.EnsureMimiActor();\n        if (mimi is null)\n            return;\n'''
    new_guard = '''        if (!Context.IsWorldReady || Game1.eventUp)\n            return;\n\n        NPC? mimi = this.WorldActors.FindMimiActor() ?? this.WorldActors.EnsureMimiActor();\n        if (mimi is null)\n            return;\n\n        if (this.DebugRoutineOverride is not null)\n        {\n            GameLocation? debugAttic = this.EnsureAtticLocation();\n            if (debugAttic is null)\n                return;\n            this.ApplyFixedAtticState(mimi, debugAttic, this.DebugRoutineOverride);\n            return;\n        }\n\n        if (!this.Save.Data.MimiMeetupCompleted\n            || this.StoryOwnsMimiActor()\n            || this.MysteryOwnsMimiActor())\n        {\n            return;\n        }\n'''
    if old_guard not in s:
        raise RuntimeError('home guard anchor missing')
    s = s.replace(old_guard, new_guard, 1)

    s = s.replace('                Point tv = this.ResolveStableAtticRoutineTile(attic, "tv", SecretTvWatchTile);\n                PlaceMimi(mimi, attic, tv, 0);',
                  '                Point tv = ResolveFixedAtticAnchor(attic, SecretTvWatchTile);\n                PlaceMimi(mimi, attic, tv, 0);')
    s = s.replace('                Point lateHome = this.ResolveStableAtticRoutineTile(attic, "late", SecretLateHomeTile);\n                PlaceMimi(mimi, attic, lateHome, 1);',
                  '                Point lateHome = ResolveFixedAtticAnchor(attic, SecretLateHomeTile);\n                PlaceMimi(mimi, attic, lateHome, 1);')
    s = s.replace('            Point home = this.ResolveStableAtticRoutineTile(attic, "home");\n            PlaceMimi(mimi, attic, home, 2);',
                  '            Point home = ResolveFixedAtticAnchor(attic, DefaultHomeTile);\n            PlaceMimi(mimi, attic, home, 2);')

    start = s.find('    private Point ResolveStableAtticRoutineTile(')
    end = s.find('    internal bool OwnsSecretTvDialogueNow()', start)
    if start < 0 or end < 0:
        raise RuntimeError('stable resolver block missing')
    replacement = '''    private static Point ResolveFixedAtticAnchor(GameLocation attic, Point desired)\n    {\n        int width = attic.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 22;\n        int height = attic.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 14;\n        return new Point(\n            Math.Clamp(desired.X, 1, Math.Max(1, width - 2)),\n            Math.Clamp(desired.Y, 1, Math.Max(1, height - 2))\n        );\n    }\n\n    private void ApplyFixedAtticState(NPC mimi, GameLocation attic, string state)\n    {\n        switch (state)\n        {\n            case "tv":\n                PlaceMimi(mimi, attic, ResolveFixedAtticAnchor(attic, SecretTvWatchTile), 0);\n                break;\n            case "late":\n                PlaceMimi(mimi, attic, ResolveFixedAtticAnchor(attic, SecretLateHomeTile), 1);\n                break;\n            default:\n                PlaceMimi(mimi, attic, ResolveFixedAtticAnchor(attic, DefaultHomeTile), 2);\n                break;\n        }\n    }\n\n    public string DebugForceRoutine(string mode)\n    {\n        if (!Context.IsWorldReady)\n            return "MiMi routine TEST unavailable: load a save first.";\n\n        mode = (mode ?? "auto").Trim().ToLowerInvariant();\n        if (mode == "auto")\n        {\n            this.DebugRoutineOverride = null;\n            this.EnforceSchedule();\n            return "MiMi routine TEST: AUTO restored. Friendship/time rules own MiMi again.";\n        }\n        if (mode is not ("home" or "tv" or "late"))\n            return "Usage: cardcha_test_mimi_routine <home|tv|late|auto>";\n\n        GameLocation? attic = this.EnsureAtticLocation();\n        NPC? mimi = this.WorldActors.FindMimiActor() ?? this.WorldActors.EnsureMimiActor();\n        if (attic is null || mimi is null)\n            return "MiMi routine TEST couldn't resolve the attic/NPC.";\n\n        this.DebugRoutineOverride = mode;\n        this.ApplyFixedAtticState(mimi, attic, mode);\n        Point tile = new((int)(mimi.Position.X / 64f), (int)(mimi.Position.Y / 64f));\n        return $"MiMi routine TEST: forced {mode.ToUpperInvariant()} at ({tile.X},{tile.Y}). Runtime-only; use auto to release.";\n    }\n\n'''
    s = s[:start] + replacement + s[end:]
    s = s.replace('    internal bool OwnsSecretTvDialogueNow()\n        => this.IsSecretTvRoutineNow()',
                  '    internal bool OwnsSecretTvDialogueNow()\n        => (this.DebugRoutineOverride == "tv" || this.IsSecretTvRoutineNow())')
    s = s.replace('        string secretTv = this.IsSecretTvRoutineNow() ? "ACTIVE" : this.IsSecretTvRoutineUnlocked() ? "unlocked" : "locked";\n        return $"MiMiHome=Attic({attic is not null})',
                  '        string secretTv = this.IsSecretTvRoutineNow() ? "ACTIVE" : this.IsSecretTvRoutineUnlocked() ? "unlocked" : "locked";\n        NPC? actor = this.WorldActors.FindMimiActor();\n        string actorTile = actor is null ? "<missing>" : $"{(int)(actor.Position.X / 64f)},{(int)(actor.Position.Y / 64f)}@{actor.currentLocation?.NameOrUniqueName}";\n        return $"MiMiHome=Attic({attic is not null})')
    s = s.replace('| SecretTV={secretTv} 17:30-22:00";', '| SecretTV={secretTv} 17:30-22:00 | DebugRoutine={this.DebugRoutineOverride ?? "auto"} | Actor={actorTile}";')
    for t in ['DefaultHomeTile = new(10, 4)', 'SecretTvWatchTile = new(5, 10)', 'DebugForceRoutine(string mode)', 'ResolveFixedAtticAnchor', 'DebugRoutine={this.DebugRoutineOverride']:
        if t not in s: raise RuntimeError('home token '+t)
    p.write_text(s, encoding='utf-8')


def patch_social():
    p = ROOT/'Services/MimiSocialService.cs'
    s = p.read_text(encoding='utf-8')
    anchor = '''        // Once today's normal greeting is complete, the same simple action button becomes the\n        // merchant interaction. This keeps controller UX one-button and doesn't steal gifting.\n        this.OpenMimiShop();\n'''
    repl = '''        // MiMi's attic is her home, never a shop. After today's greeting, empty-hand\n        // interactions at home simply stop here; gifting above still uses Stardew normally.\n        if (Game1.currentLocation?.NameOrUniqueName.Equals(MimiHomeService.AtticLocationName, StringComparison.OrdinalIgnoreCase) == true)\n            return;\n\n        // Outside the attic, retain the established post-greeting merchant interaction.\n        this.OpenMimiShop();\n'''
    if anchor not in s: raise RuntimeError('social shop anchor missing')
    s = s.replace(anchor, repl, 1)
    p.write_text(s, encoding='utf-8')


def patch_modentry():
    p = ROOT/'ModEntry.cs'
    s = p.read_text(encoding='utf-8')
    reg = '        helper.ConsoleCommands.Add("cardcha_test_attic", "TEST ONLY: toggle direct MiMi attic access without changing friendship/story progression.", this.CommandTestAttic);\n'
    if 'cardcha_test_mimi_routine' not in s:
        s = s.replace(reg, reg + '        helper.ConsoleCommands.Add("cardcha_test_mimi_routine", "TEST ONLY: force MiMi attic state: home|tv|late|auto.", this.CommandTestMimiRoutine);\n', 1)
    handler_anchor = '    private void CommandAirshipStatus(string command, string[] args)\n'
    handler = '''    private void CommandTestMimiRoutine(string command, string[] args)\n    {\n        string mode = args.FirstOrDefault() ?? "auto";\n        this.Monitor.Log(this.Home.DebugForceRoutine(mode), LogLevel.Alert);\n    }\n\n'''
    if 'private void CommandTestMimiRoutine' not in s:
        s = s.replace(handler_anchor, handler + handler_anchor, 1)
    old_version = '''    private void CommandVersion(string command, string[] args)\n    {\n        this.Monitor.Log(\n            "Cardcha! v0.3.0-alpha.28.0.4.14.4.5.1 CHACHA SUPPORT CAST RUNTIME TEST",\n            LogLevel.Alert\n        );\n    }\n'''
    new_version = '''    private void CommandVersion(string command, string[] args)\n    {\n        this.Monitor.Log($"Cardcha! v{this.ModManifest.Version}", LogLevel.Alert);\n    }\n'''
    if old_version in s:
        s = s.replace(old_version, new_version, 1)
    p.write_text(s, encoding='utf-8')


def patch_gate():
    p = ROOT/'Patches/AirshipGateRelocationPatch.cs'
    s = p.read_text(encoding='utf-8')
    s = s.replace('/// .5.6.1.3 hard relocation pass for the Forest Arcane Gate.', '/// .5.11.2 reachable relocation pass for the Forest Arcane Gate.')
    s = s.replace('    // User-accepted screenshot target: about 11 tiles left and 4 tiles down from the old portal.\n    private const int GateShiftX = -11;\n    private const int GateShiftY = 4;',
                  '    // Move from the previous fenced placement toward the open meadow immediately right of the pink blossom tree.\n    private const int GateShiftX = -16;\n    private const int GateShiftY = 8;')
    start = s.find('    private static void AfterResolveSkyDockTile(ref Point __result)')
    if start < 0: raise RuntimeError('gate postfix missing')
    end = s.find('\n    }\n}', start)
    if end < 0: raise RuntimeError('gate end missing')
    method = '''    private static void AfterResolveSkyDockTile(ref Point __result)\n    {\n        GameLocation? forest = Game1.getLocationFromName(AirshipFoundationService.SkyDockLocationName);\n        if (forest is null)\n            return;\n\n        int width = forest.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 120;\n        int height = forest.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 120;\n        Point original = __result;\n        Point desired = new(\n            Math.Clamp(original.X + GateShiftX, 2, Math.Max(2, width - 3)),\n            Math.Clamp(original.Y + GateShiftY, 2, Math.Max(2, height - 4))\n        );\n\n        Point seed = FindFarmSideSeed(forest, original);\n        HashSet<Point> reachable = FloodWalkable(forest, seed);\n        Point final = FindReachableGateAnchor(forest, desired, reachable) ?? original;\n        __result = final;\n\n        if (!LoggedPlacement)\n        {\n            LoggedPlacement = true;\n            ModEntry.StaticMonitor?.Log(\n                $"Arcane Gate reachable relocation: base=({original.X},{original.Y}) desired=({desired.X},{desired.Y}) final=({final.X},{final.Y}); interaction=160px; CollisionEdits=NONE.",\n                LogLevel.Alert\n            );\n        }\n    }\n\n    private static Point FindFarmSideSeed(GameLocation forest, Point fallback)\n    {\n        try\n        {\n            foreach (Warp warp in forest.warps)\n            {\n                if (!string.IsNullOrWhiteSpace(warp.TargetName) && warp.TargetName.Contains("Farm", StringComparison.OrdinalIgnoreCase))\n                {\n                    for (int r = 0; r <= 5; r++)\n                        for (int y = warp.Y - r; y <= warp.Y + r; y++)\n                            for (int x = warp.X - r; x <= warp.X + r; x++)\n                            {\n                                Point p = new(x, y);\n                                if (IsWalkable(forest, p))\n                                    return p;\n                            }\n                }\n            }\n        }\n        catch { }\n        return IsWalkable(forest, fallback) ? fallback : new Point(Math.Max(2, fallback.X), Math.Max(2, fallback.Y));\n    }\n\n    private static HashSet<Point> FloodWalkable(GameLocation forest, Point seed)\n    {\n        HashSet<Point> seen = new();\n        if (!IsWalkable(forest, seed))\n            return seen;\n        Queue<Point> q = new();\n        q.Enqueue(seed); seen.Add(seed);\n        Point[] dirs = { new(1,0), new(-1,0), new(0,1), new(0,-1) };\n        while (q.Count > 0)\n        {\n            Point p = q.Dequeue();\n            foreach (Point d in dirs)\n            {\n                Point n = new(p.X + d.X, p.Y + d.Y);\n                if (seen.Contains(n) || !IsWalkable(forest, n))\n                    continue;\n                seen.Add(n); q.Enqueue(n);\n            }\n        }\n        return seen;\n    }\n\n    private static Point? FindReachableGateAnchor(GameLocation forest, Point desired, HashSet<Point> reachable)\n    {\n        for (int r = 0; r <= 14; r++)\n        {\n            for (int y = desired.Y - r; y <= desired.Y + r; y++)\n            for (int x = desired.X - r; x <= desired.X + r; x++)\n            {\n                if (Math.Abs(x - desired.X) != r && Math.Abs(y - desired.Y) != r)\n                    continue;\n                Point a = new(x, y);\n                if (!GateFootprintClear(forest, a))\n                    continue;\n                Point[] action = { new(a.X, a.Y + 2), new(a.X - 1, a.Y + 2), new(a.X + 1, a.Y + 2), new(a.X, a.Y + 3) };\n                if (action.Any(reachable.Contains))\n                    return a;\n            }\n        }\n        return null;\n    }\n\n    private static bool GateFootprintClear(GameLocation forest, Point a)\n    {\n        for (int y = a.Y; y <= a.Y + 2; y++)\n            for (int x = a.X - 1; x <= a.X + 1; x++)\n                if (!IsWalkable(forest, new Point(x, y)))\n                    return false;\n        return true;\n    }\n\n    private static bool IsWalkable(GameLocation forest, Point p)\n    {\n        int w = forest.Map?.Layers.FirstOrDefault()?.LayerWidth ?? 120;\n        int h = forest.Map?.Layers.FirstOrDefault()?.LayerHeight ?? 120;\n        if (p.X < 1 || p.Y < 1 || p.X >= w - 1 || p.Y >= h - 1)\n            return false;\n        try\n        {\n            Vector2 v = new(p.X, p.Y);\n            if (forest.Map?.GetLayer("Buildings")?.Tiles[p.X, p.Y] is not null || forest.Map?.GetLayer("Front")?.Tiles[p.X, p.Y] is not null)\n                return false;\n            if (forest.IsTileBlockedBy(v) || forest.Objects.ContainsKey(v) || forest.terrainFeatures.ContainsKey(v))\n                return false;\n            Rectangle box = new(p.X * 64, p.Y * 64, 64, 64);\n            foreach (var f in forest.largeTerrainFeatures)\n                if (f.getBoundingBox().Intersects(box))\n                    return false;\n            return true;\n        }\n        catch { return false; }\n    }\n'''
    s = s[:start] + method + '\n}' + s[end+7:]
    for t in ['GateShiftX = -16', 'GateShiftY = 8', 'FloodWalkable', 'FindReachableGateAnchor', 'CollisionEdits=NONE']:
        if t not in s: raise RuntimeError('gate token '+t)
    p.write_text(s, encoding='utf-8')


def patch_airship():
    p = ROOT/'Services/AirshipFoundationService.cs'
    s = p.read_text(encoding='utf-8')
    s = s.replace('Point landing = FindClearTileNear(forest, new Point(dock.X, dock.Y + 2));\n        this.WarpGraceUntilMs',
                  'Point landing = FindClearTileNear(forest, new Point(dock.X, dock.Y + 3));\n        this.WarpGraceUntilMs', 1)
    p.write_text(s, encoding='utf-8')


for f in [ROOT/'manifest.json', ROOT/'Cardcha.csproj', ROOT/'Directory.Build.targets']:
    bump(f)
patch_home()
patch_social()
patch_modentry()
patch_gate()
patch_airship()
print('alpha28 0646B patch applied')
